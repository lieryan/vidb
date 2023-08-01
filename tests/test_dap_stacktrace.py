import asyncio

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import to_formatted_text

from tests.stubs import DAPServerMixin
from vidb.client import stack_trace
from vidb.ui import StacktraceWidget


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

        _, stack_frames = await asyncio.gather(
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

    def assert_formatted_text(self, formatted0, expected):
        assert to_formatted_text(formatted0) == to_formatted_text(HTML(expected))
