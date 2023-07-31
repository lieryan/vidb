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


class VariablesWidget:
    def __init__(self):
        self.key_bindings = KeyBindings()
        self.content = Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.key_bindings,
            ),
        )

    def __pt_container__(self):
        return TitledWindow(
            "Variables:",
            self.content,
        )


class StacktraceWidget:
    def __init__(self):
        self.key_bindings = KeyBindings()
        self.content = Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.key_bindings,
            ),
        )

    def __pt_container__(self):
        return TitledWindow(
            "Stack:",
            self.content,
        )


class BreakpointWidget:
    def __init__(self):
        self.key_bindings = KeyBindings()
        self.content = Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.key_bindings,
            ),
        )

    def __pt_container__(self):
        return TitledWindow(
            "Breakpoints:",
            self.content,
        )


class UI:
    _ptk: Application

    def __init__(self):
        self.source_widget = SourceWidget()
        self.terminal_widget = TerminalWidget()
        self.variables_widget = VariablesWidget()
        self.stacktrace_widget = StacktraceWidget()
        self.breakpoint_widget = BreakpointWidget()

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

            HSplit(
                [
                    # Variables
                    self.variables_widget,

                    # Stack
                    self.stacktrace_widget,

                    # Breakpoint
                    self.breakpoint_widget,
                ],
                width=40,
            ),
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
        variables_kb.add("down")(focus_stacktrace_widget)
        variables_kb.add("up")(focus_breakpoint_widget)

        stacktrace_kb.add("left")(focus_source_widget)
        stacktrace_kb.add("up")(focus_variable_widget)
        stacktrace_kb.add("down")(focus_breakpoint_widget)

        breakpoint_kb.add("left")(focus_source_widget)
        breakpoint_kb.add("down")(focus_variable_widget)
        breakpoint_kb.add("up")(focus_stacktrace_widget)
