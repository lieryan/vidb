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

        connection = DAPConnection(reader, None)
        headers = await connection.read_headers()
        assert headers == {"Content-Length": "10"}

    async def test_recv_message(self, create_reader_message_pipe):
        reader = await create_reader_message_pipe(
            {
                "type": "response",
                "seq": 123,
            },
        )

        connection = DAPConnection(reader, None)
        message = await connection.recv_message()
        assert message == {
            "type": "response",
            "seq": 123,
        }

    def test_dispatch_request_message_returns_future(self):
        message = {
            "type": "request",
            "seq": 123,
        }
        connection = DAPConnection(None, None)

        assert 123 not in connection.dispatcher.futures
        future_response = connection.dispatch_message(message)
        assert 123 in connection.dispatcher.futures
        assert isinstance(future_response, asyncio.Future)
        assert connection.dispatcher.futures[123] is future_response

    def test_dispatch_response_message_sets_future(self):
        message = {
            "type": "response",
            "request_seq": 123,
        }
        connection = DAPConnection(None, None)

        future_response = asyncio.Future()
        connection.dispatcher.futures[123] = future_response

        assert not future_response.done()
        assert 123 in connection.dispatcher.futures

        future_response = connection.dispatch_message(message)

        assert future_response.done()
        assert 123 not in connection.dispatcher.futures

    async def test_send_message(self, pipe_connection_factory):
        reader, writer = await pipe_connection_factory()

        connection = DAPConnection(None, writer)

        message = {
            "type": "request",
            "seq": 123,
        }

        future_response = connection.send_message(message)

        assert isinstance(future_response, asyncio.Future)

        writer.close()
        data = await reader.read()
        assert data == b'Content-Length: 31\r\n\r\n{"type": "request", "seq": 123}'

    async def test_request_response(self, pipe_connection_factory, create_reader_message_pipe):
        response_message = {
            "type": "response",
            "request_seq": 123,
        }
        reader, reader_writer = await pipe_connection_factory()
        _, writer = await pipe_connection_factory()

        connection = DAPConnection(reader, writer)

        request_message = {
            "type": "request",
            "seq": 123,
        }

        DAPConnection.write_message(reader_writer, response_message)

        asyncio.create_task(connection.handle_messages())
        response = await connection.request(request_message)
        assert response == response_message
