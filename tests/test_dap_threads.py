import asyncio

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import to_formatted_text

from tests.stubs import DAPServerMixin
from vidb.client import stack_trace
from vidb.ui import ThreadsWidget, GroupableRadioList


THREADS_RESPONSE = {
    'seq': 1,
    'type': 'response',
    'request_seq': 1,
    'success': True,
    'command': 'threads',
    'body': {
        'threads': [
            {'id': 1, 'name': 'MainThread'},
            {'id': 2, 'name': 'Worker 2'},
            {'id': 3, 'name': 'Worker 3'},
        ],
    },
}

class TestThreads(DAPServerMixin):
    async def test_render_thread_to_radiolist_text(self, client):
        widget = ThreadsWidget()
        self.assert_formatted_text(
            widget._render_thread_to_radiolist_text({'id': 1, 'name': 'MainThread'}),
            '1 - MainThread',
        )

    async def test_attach_threads_widget(self, client):
        async def server_threads():
            async with self.assert_request_response(
                "threads",
                response=THREADS_RESPONSE,
            ) as threads_request:
                assert threads_request == {
                    "seq": 1,
                    "type": "request",
                    "command": "threads",
                    "arguments": None,
                }

        widget = ThreadsWidget()
        widget_task = asyncio.create_task(widget.update_threads(client))
        await asyncio.gather(
            server_threads(),
            widget_task,
            return_exceptions=True,
        )
