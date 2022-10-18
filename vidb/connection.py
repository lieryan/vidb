import asyncio
import json
from itertools import count
from typing import cast

from vidb.dap import (
    Capabilities,
    Event,
    InitializeRequest,
    InitializeResponse,
    ProtocolMessage,
    Request,
    Response,
)


class Dispatcher:
    def __init__(self):
        self.futures = {}

    def handle_request(self, message: Request) -> asyncio.Future:
        assert message["seq"] not in self.futures

        future_response: asyncio.Future = asyncio.Future()
        self.futures[message["seq"]] = future_response
        return future_response

    def handle_response(self, message: Response):
        assert message["request_seq"] in self.futures

        future_response = self.futures.pop(message["request_seq"])
        future_response.set_result(message)

        return future_response

    def handle_event(self, message: Event):
        pass


class DAPConnection:
    dispatcher: Dispatcher

    def __init__(self, reader, writer, dispatcher=None):
        self.reader = reader
        self.writer = writer
        self.dispatcher = dispatcher or Dispatcher()

    @classmethod
    async def from_tcp(cls, host, address):
        reader, writer = await asyncio.open_connection(host, address)
        conn = cls(reader, writer)
        asyncio.create_task(conn.handle_messages())
        return conn

    async def request(self, request: Request) -> Response:
        future_response: asyncio.Future = self.send_message(request)
        response: Response = await future_response
        return response

    @classmethod
    def write_message(cls, writer, request: Request) -> None:
        prepared_request: bytes = json.dumps(request).encode("utf-8")
        writer.write(f"Content-Length: {len(prepared_request)}".encode("ascii") + b"\r\n")
        writer.write(b"\r\n")
        writer.write(prepared_request)

    def send_message(self, request: Request) -> asyncio.Future:
        assert request["type"] == "request"
        future_response = self.dispatch_message(request)

        self.write_message(self.writer, request)

        return future_response

    async def read_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        while (header := await self.reader.readline()) != b"\r\n":
            header_name, header_value = header.decode("ascii").split(":")
            header_value = header_value.strip()
            headers[header_name] = header_value
        return headers

    async def recv_message(self) -> Response | Event:
        headers = await self.read_headers()
        body = await self.reader.readexactly(int(headers["Content-Length"]))

        message = json.loads(body.decode("utf-8"))
        assert message["type"] in ["response", "event"]
        return message

    async def handle_messages(self) -> None:
        while True:
            message: Response | Event = await self.recv_message()
            self.dispatch_message(message)

    def dispatch_message(self, message: ProtocolMessage) -> asyncio.Future:
        match message["type"]:
            case "request":
                return self.dispatcher.handle_request(
                    cast(Request, message),
                )

            case "response":
                return self.dispatcher.handle_response(
                    cast(Response, message),
                )

            case "event":
                return self.dispatcher.handle_event(
                    cast(Event, message),
                )

            case _:
                raise ValueError()
