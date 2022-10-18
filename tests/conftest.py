import asyncio
import json
import os

import pytest


async def create_pipe_connection():
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
    return (reader, reader_transport), (writer, writer_transport)


@pytest.fixture
def pipe_connection_factory():
    async def _factory():
        (reader, reader_transport), (writer, writer_transport) = await create_pipe_connection()

        transports.append(reader_transport)
        transports.append(writer_transport)

        return reader, writer

    transports = []

    try:
        yield _factory
    finally:
        for t in transports:
            t.close()


@pytest.fixture
def create_reader_pipe(pipe_connection_factory):
    async def _factory(data):
        reader, writer = await pipe_connection_factory()

        writer.write(data)
        writer.close()

        return reader

    return _factory


@pytest.fixture
def create_reader_message_pipe(create_reader_pipe):
    def _factory(*messages):
        chunks = []
        for message in messages:
            raw_message = json.dumps(message).encode("utf-8")
            chunks.append(f"Content-Length: {len(raw_message)}\r\n".encode("utf-8"))
            chunks.append(b"\r\n")
            chunks.append(raw_message)

        return create_reader_pipe(b"".join(chunks))

    return _factory
