import json
from itertools import count
from typing import cast

from vidb.dap import (
    Capabilities,
    InitializeRequest,
    InitializeResponse,
    _Request,
    _Response,
)


class DAPConnection:
    sequence = count()

    def __init__(self, reader, writer):
        self.reader = reader
        self.writer = writer

    def _validate_initialize(self, parsed_request: _Request) -> InitializeRequest:
        return cast(InitializeRequest, parsed_request)

    async def _send(self, request: bytes):
        self.writer.write(f"Content-Length: {len(request)}".encode("ascii") + b"\r\n\r\n")
        self.writer.write(request)

    async def read_headers(self, reader) -> dict[str, str]:
        headers: dict[str, str] = {}
        while (header := await reader.readline()) != b"\r\n":
            header_name, header_value = header.decode("ascii").split(":")
            header_value = header_value.strip()
            headers[header_name] = header_value
        return headers

    def _handle_initialize(self, request: InitializeRequest) -> InitializeResponse:
        capabilities = Capabilities()
        return InitializeResponse(
            seq=next(self.sequence),
            type="response",
            request_seq=request["seq"],
            success=True,
            command=request["command"],
            message="",
            body=capabilities,
        )
