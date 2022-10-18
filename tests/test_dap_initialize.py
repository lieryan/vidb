from vidb.client import DAPClient
from vidb.connection import DAPConnection


class TestInitialize:
    async def test_initialize(self, pipe_connection_factory):
        reader, writer = await pipe_connection_factory()

        debugger = DAPConnection(None, None)
        content = b'{"type": "response", "seq": 1, "command": "test"}'
        writer.write(f"Content-Length: {len(content)}".encode("ascii") + b"\r\n\r\n" + content)

        client = DAPClient(connection=DAPConnection(reader, writer))
        await client.initialize()
