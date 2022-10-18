import asyncio
import os
from contextlib import asynccontextmanager

from vidb.client import DAPClient
from vidb.connection import DAPConnection


class TestConnection:
    async def _open_connection(self):
        if getattr(self, "_reader", None) is None or getattr(self, "_writer", None) is None:
            self._reader, self._writer = await asyncio.open_connection(host="localhost", port=8833)
        return self._reader, self._writer

    async def test_open_pipe_connection(self, create_reader_pipe):
        reader = await create_reader_pipe(b"Content-Length: 10\r\n\r\n" + (b"a" * 10))

        assert await reader.readline() == b"Content-Length: 10\r\n"
        assert await reader.readline() == b"\r\n"
        assert await reader.read(10) == b"a" * 10

        assert await reader.read() == b""

    async def test_read_headers(self, create_reader_pipe):
        reader = await create_reader_pipe(b"Content-Length: 10\r\n\r\n" + (b"a" * 10))

        connection = DAPConnection(None, None)
        headers = await connection.read_headers(reader)
        assert headers == {"Content-Length": "10"}
