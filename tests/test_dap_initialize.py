import asyncio
import os
from contextlib import asynccontextmanager

from vidb.client import DAPClient
from vidb.connection import DAPConnection


class TestInitialize:
    @asynccontextmanager
    async def _open_pipe_connection(self):
        loop = asyncio.get_event_loop()
        r, w = os.pipe()

        reader = asyncio.StreamReader()
        reader_transport, _ = await loop.connect_read_pipe(
            lambda: asyncio.StreamReaderProtocol(reader),
            os.fdopen(r, mode="r"),
        )

        writer_transport, writer_protocol = await loop.connect_write_pipe(
            asyncio.BaseProtocol,
            os.fdopen(w, mode="w"),
        )
        writer = asyncio.StreamWriter(
            writer_transport,
            writer_protocol,
            reader,
            loop,
        )

        try:
            yield reader, writer
        finally:
            reader_transport.close()
            writer_transport.close()

    async def test_open_pipe_connection(self):
        async with self._open_pipe_connection() as (reader, writer):
            writer.write(b"Content-Length: 10\r\n\r\n" + (b"a" * 10))
            assert await reader.readline() == b"Content-Length: 10\r\n"
            assert await reader.readline() == b"\r\n"
            assert await reader.read(10) == b"a" * 10

            writer.close()
            assert await reader.read() == b""
