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


source_kb = KeyBindings()
breakpoint_kb = KeyBindings()
stacktrace_kb = KeyBindings()
variables_kb = KeyBindings()
kb = KeyBindings()

source_code_buffer = Buffer(
    document=Document(
        open("vidb/ui.py").read(),
    ),
    read_only=True,
)

source_window = Window(
    content=BufferControl(
        buffer=source_code_buffer,
        lexer=PygmentsLexer(PythonLexer),
        key_bindings=source_kb,
    ),
    left_margins=[
        NumberedMargin(),
    ],
    cursorline=True,
)

terminal_window = Terminal(
    ["ipython"],
    height=10,
)

variables_window = Window(
    content=FormattedTextControl(
        text="Hello world",
        focusable=True,
        key_bindings=variables_kb,
    ),
)

stacktrace_window = Window(
    content=FormattedTextControl(
        text="Hello world",
        focusable=True,
        key_bindings=stacktrace_kb,
    ),
)

breakpoint_window = Window(
    content=FormattedTextControl(
        text="Hello world",
        focusable=True,
        key_bindings=breakpoint_kb,
    ),
)


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


main_container = VSplit([
    HSplit([
        # Source code buffer
        source_window,

        HSeparator(),

        # Shell buffer
        terminal_window,
    ]),

    # A vertical line in the middle
    VSeparator(),

    HSplit(
        [
            # Variables
            TitledWindow(
                "Variables:",
                variables_window,
            ),

            # Stack
            TitledWindow(
                "Stack:",
                stacktrace_window,
            ),

            # Breakpoint
            TitledWindow(
                "Breakpoints:",
                breakpoint_window,
            ),
        ],
        width=40,
    ),
])

root_container = TitledWindow(
    "ViDB 0.1.0 - ?:help  n:next  s:step into  b:breakpoint  !:python command line",
    main_container,
    title_style=border_style,
)

layout = Layout(root_container)

@kb.add("q")
def exit_(event):
    event.app.exit()
    terminal_window.process.kill()


def focus_source_window(event):
    event.app.layout.focus(source_window)


@kb.add("V")
@source_kb.add("right")
def focus_variable_window(event):
    event.app.layout.focus(variables_window)


@kb.add("S")
def focus_stacktrace_window(event):
    event.app.layout.focus(stacktrace_window)


@kb.add("B")
def focus_breakpoint_window(event):
    event.app.layout.focus(breakpoint_window)


@kb.add("X")
@kb.add("!")
def focus_terminal_window(event):
    event.app.layout.focus(terminal_window)


variables_kb.add("left")(focus_source_window)
variables_kb.add("down")(focus_stacktrace_window)
variables_kb.add("up")(focus_breakpoint_window)

stacktrace_kb.add("left")(focus_source_window)
stacktrace_kb.add("up")(focus_variable_window)
stacktrace_kb.add("down")(focus_breakpoint_window)

breakpoint_kb.add("left")(focus_source_window)
breakpoint_kb.add("down")(focus_variable_window)
breakpoint_kb.add("up")(focus_stacktrace_window)


class UI:
    _ptk: Application

    def __init__(self):
        self._ptk = Application(
            layout=layout,
            key_bindings=kb,
            full_screen=True,
            mouse_support=True,
        )

    def run(self):
        self._ptk.run()
