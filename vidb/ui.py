from prompt_toolkit import Application
from prompt_toolkit.buffer import Buffer
from prompt_toolkit.document import Document
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


class UI:
    _ptk: Application

    def __init__(self):
        self._create_keybinds()
        self._ptk = Application(
            layout=self._create_layout(),
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
        )

    def run(self):
        self._ptk.run()

    def _create_layout(self):
        root_container = TitledWindow(
            "ViDB 0.1.0 - ?:help  n:next  s:step into  b:breakpoint  !:python command line",
            self._create_main_container(),
        )

        return Layout(root_container)

    def _create_main_container(self):
        self.source_window = self._create_source_window()
        self.terminal_window = self._create_terminal_window()
        self.variables_window = self._create_variables_window()
        self.stacktrace_window = self._create_stacktrace_window()
        self.breakpoint_window = self._create_breakpoint_window()
        return VSplit([
            HSplit([
                # Source code buffer
                self.source_window,

                HSeparator(),

                # Shell buffer
                self.terminal_window,
            ]),

            # A vertical line in the middle
            VSeparator(),

            HSplit(
                [
                    # Variables
                    TitledWindow(
                        "Variables:",
                        self.variables_window,
                    ),

                    # Stack
                    TitledWindow(
                        "Stack:",
                        self.stacktrace_window,
                    ),

                    # Breakpoint
                    TitledWindow(
                        "Breakpoints:",
                        self.breakpoint_window,
                    ),
                ],
                width=40,
            ),
        ])

    def _create_source_window(self):
        return Window(
            content=BufferControl(
                buffer=self._create_source_code_buffer(),
                lexer=PygmentsLexer(PythonLexer),
                key_bindings=self.source_kb,
            ),
            left_margins=[
                NumberedMargin(),
            ],
            cursorline=True,
        )

    def _create_source_code_buffer(self):
        return Buffer(
            document=Document(
                open("vidb/ui.py").read(),
            ),
            read_only=True,
        )

    def _create_terminal_window(self):
        return Terminal(
            ["ipython"],
            height=10,
        )

    def _create_variables_window(self):
        return Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.variables_kb,
            ),
        )

    def _create_stacktrace_window(self):
        return Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.stacktrace_kb,
            ),
        )

    def _create_breakpoint_window(self):
        return Window(
            content=FormattedTextControl(
                text="Hello world",
                focusable=True,
                key_bindings=self.breakpoint_kb,
            ),
        )

    def _create_keybinds(self):
        self.kb = kb = KeyBindings()
        self.source_kb = source_kb = KeyBindings()
        self.breakpoint_kb = breakpoint_kb = KeyBindings()
        self.stacktrace_kb = stacktrace_kb = KeyBindings()
        self.variables_kb = variables_kb = KeyBindings()

        @kb.add("q")
        def exit_(event):
            event.app.exit()
            self.terminal_window.process.kill()

        def focus_source_window(event):
            event.app.layout.focus(self.source_window)

        @kb.add("V")
        @source_kb.add("right")
        def focus_variable_window(event):
            event.app.layout.focus(self.variables_window)

        @kb.add("S")
        def focus_stacktrace_window(event):
            event.app.layout.focus(self.stacktrace_window)

        @kb.add("B")
        def focus_breakpoint_window(event):
            event.app.layout.focus(self.breakpoint_window)

        @kb.add("X")
        @kb.add("!")
        def focus_terminal_window(event):
            event.app.layout.focus(self.terminal_window)

        variables_kb.add("left")(focus_source_window)
        variables_kb.add("down")(focus_stacktrace_window)
        variables_kb.add("up")(focus_breakpoint_window)

        stacktrace_kb.add("left")(focus_source_window)
        stacktrace_kb.add("up")(focus_variable_window)
        stacktrace_kb.add("down")(focus_breakpoint_window)

        breakpoint_kb.add("left")(focus_source_window)
        breakpoint_kb.add("down")(focus_variable_window)
        breakpoint_kb.add("up")(focus_stacktrace_window)
