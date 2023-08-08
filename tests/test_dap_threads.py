import asyncio

from prompt_toolkit import HTML
from prompt_toolkit.formatted_text import to_formatted_text

from tests.stubs import DAPServerMixin
from vidb.client import stack_trace
from vidb.ui import ThreadsWidget, GroupableRadioList


class TestThreads(DAPServerMixin):
    async def test_render_thread_to_radiolist_text(self, client):
        widget = ThreadsWidget()
        self.assert_formatted_text(
            widget._render_thread_to_radiolist_text({'id': 1, 'name': 'MainThread'}),
            '1 - MainThread',
        )
