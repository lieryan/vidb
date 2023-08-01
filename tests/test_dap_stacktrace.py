import asyncio

from tests.stubs import DAPServerMixin
from vidb.client import stack_trace

STACK_TRACE_RESPONSE = {
    "seq": 1,
    "type": "response",
    "request_seq": 1,
    "success": True,
    "command": "stackTrace",
    "body": {
        "stackFrames": [
            {
                "id": 3,
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
