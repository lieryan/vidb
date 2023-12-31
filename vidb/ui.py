from __future__ import annotations
from uuid import uuid4

import asyncio
import io
from pathlib import Path
from asyncio.locks import Condition
from typing import Optional
from contextlib import asynccontextmanager

from prompt_toolkit import HTML, Application
from prompt_toolkit.application import get_app
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.filters.base import Never
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import NumberedMargin
from prompt_toolkit.lexers.pygments import PygmentsLexer
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import RadioList
from ptterm import Terminal
from pygments.lexers.python import PythonLexer

from vidb.client import stack_trace, threads


border_style = "fg:lightblue bg:darkred bold"

background_tasks = set()

def create_background_task(coro):
    """ create a reliable background task by keeping strong reference to the task """
    task = asyncio.create_task(coro)
    background_tasks.add(task)
    task.add_done_callback(background_tasks.discard)


def TitledWindow(
    title,
    window,
    *,
    title_style: str = border_style,
):
    return HSplit(
        [
            Window(
                content=FormattedTextControl(
                    text=title,
                ),
                height=1,
                style=title_style,
            ),
            window,
        ]
    )


def HSeparator():
    return Window(
        height=1,
        char=" ",
        style=border_style,
    )


def VSeparator():
    return Window(
        width=1,
        char=" ",
        style=border_style,
    )


class SourceWidget(Window):
    def __init__(self):
        self.key_bindings = KeyBindings()
        super().__init__(
            content=BufferControl(
                lexer=PygmentsLexer(PythonLexer),
                key_bindings=self.key_bindings,
            ),
            left_margins=[
                NumberedMargin(),
            ],
            cursorline=True,
        )

    async def attach(self, client, stacktrace_widget):
        create_background_task(self.run(client, stacktrace_widget))

    async def run(self, client, stacktrace_widget):
        async with stacktrace_widget.watch() as on_current_stackframe_changed:
            while True:
                frame_id = await on_current_stackframe_changed()

                frame = next(frame for frame in stacktrace_widget.frames if frame["id"] == frame_id)
                if frame["source"]["sourceReference"] == 0:
                    self.source_file = open(frame["source"]["path"])
                else:
                    arguments = {"source": frame["source"], "sourceReference": frame["source"]["sourceReference"]}
                    src = await client.remote_call(dict, "source", arguments=arguments)

                    self.source_file = io.StringIO(src["content"])
                self.content.buffer.cursor_position = self.content.buffer.document.translate_row_col_to_index(
                    frame["line"] - 1,
                    frame["column"] - 1,
                )

                self._center_cursor(
                    self.content.buffer,
                )

                get_app().invalidate()

    def _center_cursor(self, buffer):
        """
        Center Window vertically around cursor.

        """
        # adapted from prompt_toolkit/key_binding/bindings/vi.py

        w = self
        b = buffer

        if w and w.render_info:
            info = w.render_info

            # Calculate the offset that we need in order to position the row
            # containing the cursor in the center.
            scroll_height = info.window_height // 2

            y = max(0, b.document.cursor_position_row - 1)
            height = 0
            while y > 0:
                line_height = info.get_height_for_line(y)

                if height + line_height < scroll_height:
                    height += line_height
                    y -= 1
                else:
                    break

            w.vertical_scroll = y

    @property
    def source_file(self):
        return self.content.buffer

    @source_file.setter
    def source_file(self, file):
        self.content.buffer = Buffer(
            document=Document(
                file.read(),
            ),
            read_only=True,
        )


class TerminalWidget(Terminal):
    def __init__(self):
        self.key_bindings = KeyBindings()
        super().__init__(
            ["ipython"],
            height=10,
        )


class forward_property:
    def __init__(self, attr_name):
        self.attr_name = attr_name

    def __get__(self, instance, cls):
        return getattr(getattr(instance, self.attr_name), self.name)

    def __set__(self, instance, value):
        setattr(getattr(instance, self.attr_name), self.name, value)

    def __set_name__(self, cls, name):
        real_forward_property = forward_property(attr_name=self.attr_name)
        real_forward_property.name = name
        setattr(cls, name, real_forward_property)


class RadioListWithWatchableCurrentValue(RadioList):
    def __init__(self, values, *args, **kwargs):
        self._watch_current_value = Condition()
        super().__init__(values, *args, **kwargs)

    @property
    def current_value(self):
        return self._current_value

    @current_value.setter
    def current_value(self, new_value):
        async def update():
            async with self._watch_current_value:
                self._current_value = new_value
                self._watch_current_value.notify_all()
        create_background_task(update())

    @asynccontextmanager
    async def watch(self):
        """ watch current value """
        async def _waiter():
            await self._watch_current_value.wait()
            return self.current_value

        async with self._watch_current_value:
            yield _waiter


class GroupableRadioList:
    group: Optional[RadioListGroup]

    values = _selected_index = current_value = watch = forward_property("radio")

    def __init__(self, values, *args, **kwargs):
        self.radio = RadioListWithWatchableCurrentValue(values=values, *args, **kwargs)
        self.radio.window.dont_extend_height = Never()
        self.group = None

        kb = self.radio.control.key_bindings

        @kb.add("up")
        def _(event):
            if self._selected_index - 1 >= 0:
                self._selected_index -= 1
            else:
                self.on_hit_top(event)

        @kb.add("down")
        def _(event):
            if self._selected_index + 1 < len(self.values):
                self._selected_index += 1
            else:
                self.on_hit_bottom(event)

    def on_hit_top(self, event):
        if self.group and self.group.first_window is not event.app.layout.current_window:
            event.app.layout.focus_previous()

    def on_hit_bottom(self, event):
        if self.group and self.group.last_window is not event.app.layout.current_window:
            event.app.layout.focus_next()


class ThreadsWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(values=[(None, "No threads")])
        self.threads = []

    async def attach(self, client):
        await self.update_threads(client)
        for thread in self.threads:
            await client.remote_call(dict, "pause", arguments={"threadId": thread["id"]})
        # create_background_task(self.run(client))

    async def update_threads(self, client):
        thread_list = await threads(client)
        self.threads = thread_list["threads"]
        self.values = [(t["id"], self._render_thread_to_radiolist_text(t)) for t in self.threads]
        self.current_value = self.values[0][0]

    def _render_thread_to_radiolist_text(self, thread):
        return f"{thread['id']} - {thread['name']}"

    def __pt_container__(self):
        return TitledWindow(
            "Threads:",
            self.radio,
        )


class VariablesWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(
            values=[(None, "No variables")],
        )
        self.key_bindings = self.radio.control.key_bindings

    async def attach(self, client, stacktrace_widget):
        create_background_task(self.run(client, stacktrace_widget))

    async def run(self, client, stacktrace_widget):
        from vidb.client import scopes, variables
        async with stacktrace_widget.watch() as on_current_stackframe_changed:
            while True:
                frame_id = await on_current_stackframe_changed()

                scope_list = await scopes(client, frame_id=frame_id)
                values = []
                for scope in scope_list["scopes"]:
                    values.append((("scope", scope["name"]), scope["name"]))
                    if True:
                    # if scope.get("presentationHint") in ["locals", "globals"]:
                        variable_list = await variables(client, variables_reference=scope["variablesReference"])
                        for variable in variable_list["variables"]:
                            var_uuid = uuid4()
                            values.append((
                                variable["variablesReference"] or var_uuid,
                                HTML("{expand_marker} <variables-name>{name}</variables-name>: <variables-type>{type}</variables-type> = <variables-value>{value}</variables-value>").format(
                                    **variable,
                                    expand_marker="+" if variable["variablesReference"] else "-",
                                ),
                            ))
                            misc = variable.copy()
                            if misc["evaluateName"] == misc["name"]: del misc["evaluateName"]
                            del misc["name"]
                            del misc["type"]
                            del misc["value"]
                            del misc["variablesReference"]
                            if misc.get("presentationHint") == {"attributes": ["rawString"]}:
                                del misc["presentationHint"]
                            for k, v in misc.items():
                                k = str(k)[:5]
                                values.append((variable["variablesReference"] or var_uuid, f"-- {k}={v}"))
                self.values = values
                self.current_value = self.values[0][0]
                get_app().invalidate()

    def __pt_container__(self):
        return TitledWindow(
            "Variables:",
            self.radio,
        )


class StacktraceWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(values=[(None, "No stacktrace")])
        self.key_bindings = self.radio.control.key_bindings

    async def attach(self, client, threads_widget):
        create_background_task(self.run(client, threads_widget))

    async def run(self, client, threads_widget):
        async with threads_widget.watch() as on_current_thread_changed:
            while True:
                thread_id = await on_current_thread_changed()

                stack_trace_list = await stack_trace(client, thread_id=thread_id)
                self.frames = stack_trace_list["stackFrames"]
                self.values = [
                    (frame["id"], self._render_frame_to_radiolist_text(frame)) for frame in self.frames
                ]
                self.current_value = self.values[0][0]
                get_app().invalidate()

    def _render_frame_to_radiolist_text(self, frame):
        def short_path(path: str):
            return Path(path).name

        return HTML("<frame-name>{name}</frame-name> <frame-filepath>{file_name}:{line}:{column}</frame-filepath>").format(
            **frame,
            file_name=short_path(frame['source']['path']),
        )

    def __pt_container__(self):
        return TitledWindow(
            "Stack:",
            self.radio,
        )


class BreakpointWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(
            values=[
                (None, "No breakpoints"),
                *[(x, f"Breakpoint {x}") for x in range(10)],
            ],
        )
        self.key_bindings = self.radio.control.key_bindings

    def __pt_container__(self):
        return TitledWindow(
            "Breakpoints:",
            self.radio,
        )


class RadioListGroup:
    def __init__(self, split_cls, children, *args, **kwargs):
        assert all(isinstance(c, GroupableRadioList) for c in children)
        for c in children:
            c.group = self
        self.content = split_cls(children, *args, **kwargs)
        self.children = children

    @property
    def first_window(self):
        return self.children and self.children[0].radio.window

    @property
    def last_window(self):
        return self.children and self.children[-1].radio.window

    def __pt_container__(self):
        return self.content


class UI:
    _ptk: Application

    def __init__(self):
        self.source_widget = SourceWidget()
        self.terminal_widget = TerminalWidget()
        self.threads_widget = ThreadsWidget()
        self.variables_widget = VariablesWidget()
        self.stacktrace_widget = StacktraceWidget()
        self.breakpoint_widget = BreakpointWidget()
        self.right_sidebar = RadioListGroup(
            HSplit,
            [
                self.threads_widget,
                self.variables_widget,
                self.stacktrace_widget,
                self.breakpoint_widget,
            ],
            width=40,
        )

        self.global_bindings = KeyBindings()
        self._create_keybinds()
        self._ptk = Application(
            layout=self._create_layout(),
            key_bindings=self.global_bindings,
            full_screen=True,
            mouse_support=True,
            editing_mode=EditingMode.VI,
            style=Style.from_dict(
                {
                    "frame-name": "fg:lightblue",
                    "frame-filepath": "fg:red",
                    "variables-name": "fg:green",
                    "variables-type": "fg:lightblue",
                    "variables-value": "fg:red",
                },
            ),
        )

        self.source_widget.source_file = open("vidb/ui.py")

    def run(self, *args, **kwargs):
        return self._ptk.run_async(*args, **kwargs)

    def _create_layout(self):
        root_container = TitledWindow(
            "ViDB 0.1.0 - ?:help  n:next  s:step into  b:breakpoint  !:python command line",
            self._create_main_container(),
        )

        return Layout(root_container)

    def _create_main_container(self):
        return VSplit(
            [
                HSplit(
                    [
                        # Source code buffer
                        self.source_widget,
                        HSeparator(),
                        # Shell buffer
                        self.terminal_widget,
                    ]
                ),
                VSeparator(),
                self.right_sidebar,
            ]
        )

    def _create_keybinds(self):
        kb = self.global_bindings
        source_kb = self.source_widget.key_bindings
        stacktrace_kb = self.stacktrace_widget.key_bindings
        variables_kb = self.variables_widget.key_bindings
        breakpoint_kb = self.breakpoint_widget.key_bindings
        threads_kb = self.threads_widget.radio.control.key_bindings

        @kb.add("q")
        def exit_(event):
            event.app.exit()
            self.terminal_widget.process.kill()

        def focus_source_widget(event):
            event.app.layout.focus(self.source_widget)

        @kb.add("T")
        @source_kb.add("right")
        def focus_threads_widget(event):
            event.app.layout.focus(self.threads_widget)

        @kb.add("V")
        def focus_variable_widget(event):
            event.app.layout.focus(self.variables_widget)

        @kb.add("S")
        def focus_stacktrace_widget(event):
            event.app.layout.focus(self.stacktrace_widget)

        @kb.add("B")
        def focus_breakpoint_widget(event):
            event.app.layout.focus(self.breakpoint_widget)

        @kb.add("X")
        @kb.add("!")
        def focus_terminal_widget(event):
            event.app.layout.focus(self.terminal_widget)

        threads_kb.add("left")(focus_source_widget)
        variables_kb.add("left")(focus_source_widget)
        stacktrace_kb.add("left")(focus_source_widget)
        breakpoint_kb.add("left")(focus_source_widget)
