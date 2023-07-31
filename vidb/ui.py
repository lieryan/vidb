from __future__ import annotations

from typing import Optional

from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
from prompt_toolkit.enums import EditingMode
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import VSplit, HSplit, Window
from prompt_toolkit.layout.controls import BufferControl, FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.layout.margins import NumberedMargin
from prompt_toolkit.lexers.pygments import PygmentsLexer
from prompt_toolkit.widgets import RadioList
from ptterm import Terminal
from pygments.lexers.python import PythonLexer


border_style = "fg:lightblue bg:darkred bold"


def TitledWindow(
    title,
    window,
    *,
    title_style: str=border_style,
):
    return HSplit([
        Window(
            content=FormattedTextControl(
                text=title,
            ),
            height=1,
            style=title_style,
        ),
        window,
    ])



def HSeparator():
    return Window(
        height=1,
        char=' ',
        style=border_style,
    )


def VSeparator():
    return Window(
        width=1,
        char=' ',
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
        real_forward_property =  forward_property(attr_name=self.attr_name)
        real_forward_property.name = name
        setattr(cls, name, real_forward_property)


class GroupableRadioList:
    group: Optional[RadioListGroup]

    values = _selected_index = current_value = forward_property("radio")

    def __init__(self, values, *args, **kwargs):
        self.radio = RadioList(values=values, *args, **kwargs)
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



class VariablesWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(
            values=[
                (None, "No variables"),
                *[
                    (x, f"Var {x}")
                    for x in range(10)
                ]
            ],
        )
        self.key_bindings = self.radio.control.key_bindings

    def __pt_container__(self):
        return TitledWindow(
            "Variables:",
            self.radio,
        )


class StacktraceWidget(GroupableRadioList):
    def __init__(self):
        super().__init__(
            values=[
                (None, "No stacktrace"),
                *[
                    (x, f"Frame {x}")
                    for x in range(10)
                ]
            ],
        )
        self.key_bindings = self.radio.control.key_bindings

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
                *[
                    (x, f"Breakpoint {x}")
                    for x in range(10)
                ]
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
        self.variables_widget = VariablesWidget()
        self.stacktrace_widget = StacktraceWidget()
        self.breakpoint_widget = BreakpointWidget()
        self.right_sidebar = RadioListGroup(
            HSplit,
            [
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
        )

        self.source_widget.source_file = open("vidb/ui.py")

    def run(self):
        self._ptk.run()

    def _create_layout(self):
        root_container = TitledWindow(
            "ViDB 0.1.0 - ?:help  n:next  s:step into  b:breakpoint  !:python command line",
            self._create_main_container(),
        )

        return Layout(root_container)

    def _create_main_container(self):
        return VSplit([
            HSplit([
                # Source code buffer
                self.source_widget,

                HSeparator(),

                # Shell buffer
                self.terminal_widget,
            ]),

            VSeparator(),

            self.right_sidebar,
        ])

    def _create_keybinds(self):
        kb = self.global_bindings
        source_kb = self.source_widget.key_bindings
        stacktrace_kb = self.stacktrace_widget.key_bindings
        variables_kb = self.variables_widget.key_bindings
        breakpoint_kb = self.breakpoint_widget.key_bindings

        @kb.add("q")
        def exit_(event):
            event.app.exit()
            self.terminal_widget.process.kill()

        def focus_source_widget(event):
            event.app.layout.focus(self.source_widget)

        @kb.add("V")
        @source_kb.add("right")
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

        variables_kb.add("left")(focus_source_widget)
        stacktrace_kb.add("left")(focus_source_widget)
        breakpoint_kb.add("left")(focus_source_widget)
