import asyncio
from vidb.client import DAPClient
from vidb.debugger import DAPDebugger


class TestInitialize:
    async def test_initialize(self):
        client = DAPClient(server=DAPDebugger())
        await client.initialize()
