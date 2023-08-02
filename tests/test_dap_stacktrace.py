import asyncio

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import to_formatted_text

from tests.stubs import DAPServerMixin
from vidb.client import stack_trace
from vidb.ui import StacktraceWidget, GroupableRadioList


BOTTOM_MOST_FRAME_ID = 3
STACK_TRACE_RESPONSE = {
    "seq": 1,
    "type": "response",
    "request_seq": 1,
    "success": True,
    "command": "stackTrace",
    "body": {
        "stackFrames": [
            {
                "id": BOTTOM_MOST_FRAME_ID,
                "name": "select",
                "line": 469,
                "column": 1,
                "source": {
                    "path": "/usr/local/lib/python3.10/selectors.py",
                    "sourceReference": 0,
                },
                "presentationHint": "subtle",
            },
            {
                "id": 2,
                "name": "<module>",
                "line": 29,
                "column": 1,
                "source": {
                    "path": "/opt/app/app/bin/testscript.py",
                    "sourceReference": 0,
                },
            },
        ],
        "totalFrames": 2,
    },
}


class TestStacktrace(DAPServerMixin):
    async def test_stack_trace_request(self, client):
        async def server_stack_trace():
            async with self.assert_request_response(
                "stackTrace",
                response=STACK_TRACE_RESPONSE,
            ) as stack_trace_request:
                assert stack_trace_request == {
                    "seq": 1,
                    "type": "request",
                    "command": "stackTrace",
                    "arguments": {
                        "threadId": 1,
                    },
                }

        await asyncio.gather(
            server_stack_trace(),
            stack_trace(client, thread_id=1),
        )

    async def test_render_frame_to_radiolist_text(self, client):
        widget = StacktraceWidget()

        self.assert_formatted_text(
            widget._render_frame_to_radiolist_text(STACK_TRACE_RESPONSE["body"]["stackFrames"][0]),
            '<frame-name>select</frame-name> <frame-filepath>selectors.py:469:1</frame-filepath>',
        )

        self.assert_formatted_text(
            widget._render_frame_to_radiolist_text(STACK_TRACE_RESPONSE["body"]["stackFrames"][1]),
            '<frame-name>&lt;module&gt;</frame-name> <frame-filepath>testscript.py:29:1</frame-filepath>',
        )

    async def test_attach_stacktrace_widget(self, client):
        async def server_stack_trace():
            async with self.assert_request_response(
                "stackTrace",
                response=STACK_TRACE_RESPONSE,
            ) as stack_trace_request:
                assert stack_trace_request == {
                    "seq": 1,
                    "type": "request",
                    "command": "stackTrace",
                    "arguments": {
                        "threadId": 2,
                    },
                }

        async def change_current_thread():
            await widget.attached.wait()
            threads_widget.current_value = 2
            async with self.assert_request_response(
                "stackTrace",
                response=STACK_TRACE_RESPONSE,
            ) as stack_trace_request:
                assert stack_trace_request == {
                    "seq": 1,
                    "type": "request",
                    "command": "stackTrace",
                    "arguments": {
                        "threadId": 2,
                    },
                }
            async with threads_widget.radio._watch_current_value:
                widget_attach_task.cancel()

        class DummyApp:
            def invalidate(self):
                pass
        app = DummyApp()

        widget = StacktraceWidget()
        threads_widget = GroupableRadioList(
            values=[
                (1, "Thread 1"),
                (2, "Thread 2"),
            ],
        )
        widget_attach_task = asyncio.create_task(widget.attach(client, app, threads_widget))
        await asyncio.gather(
            change_current_thread(),
            widget_attach_task,
            return_exceptions=True,
        )

        assert widget.current_value == 3
        assert widget.frames == STACK_TRACE_RESPONSE["body"]["stackFrames"]

        assert widget.values[0][0] == 3
        self.assert_formatted_text(
            widget.values[0][1],
            '<frame-name>select</frame-name> <frame-filepath>selectors.py:469:1</frame-filepath>',
        )

        assert widget.values[1][0] == 2
        self.assert_formatted_text(
            widget.values[1][1],
            '<frame-name>&lt;module&gt;</frame-name> <frame-filepath>testscript.py:29:1</frame-filepath>',
        )

    def assert_formatted_text(self, formatted0, expected):
        assert to_formatted_text(formatted0) == to_formatted_text(HTML(expected))
