import asyncio
import json
from collections import deque
from typing import cast

from vidb.dap import Event, ProtocolMessage, Request, Response


class Dispatcher:
    def __init__(self):
        self.futures = {}
        self.events = {}
        self._messages = deque(maxlen=100)

    def handle_request(self, message: Request) -> asyncio.Future:
        self._messages.append(message)
        assert message["seq"] not in self.futures

        future_response: asyncio.Future = asyncio.Future()
        self.futures[message["seq"]] = future_response
        return future_response

    def handle_response(self, message: Response):
        self._messages.append(message)
        assert message["request_seq"] in self.futures

        future_response = self.futures.pop(message["request_seq"])
        future_response.set_result(message)

        return future_response

    def handle_event(self, message: Event):
        self._messages.append(message)
        listeners = self.events.get(message["event"], {})
        for listener in listeners:
            listener(message)


class BaseDAPConnection:
    def __init__(self, reader, writer):
        super().__init__()
        self.reader = reader
        self.writer = writer

    @classmethod
    def write_message(cls, writer, msg: ProtocolMessage) -> None:
        prepared_msg: bytes = json.dumps(msg).encode("utf-8")
        writer.write(f"Content-Length: {len(prepared_msg)}".encode("ascii") + b"\r\n")
        writer.write(b"\r\n")
        writer.write(prepared_msg)

    async def read_headers(self) -> dict[str, str]:
        headers: dict[str, str] = {}
        while (header := await self.reader.readline()) != b"\r\n":
            header_name, header_value = header.decode("ascii").split(":")
            header_value = header_value.strip()
            headers[header_name] = header_value
        return headers

    async def recv_message(self) -> ProtocolMessage:
        headers = await self.read_headers()
        body = await self.reader.readexactly(int(headers["Content-Length"]))

        return json.loads(body.decode("utf-8"))


class DAPConnection(BaseDAPConnection):
    dispatcher: Dispatcher

    def __init__(self, reader, writer, dispatcher=None):
        super().__init__(reader, writer)
        self.dispatcher = dispatcher or Dispatcher()

    @classmethod
    async def from_tcp(cls, host, address):
        reader, writer = await asyncio.open_connection(host, address)
        conn = cls(reader, writer)
        conn.start_listening()
        return conn

    def start_listening(self):
        self.__listener = asyncio.create_task(self.handle_messages())

    async def request(self, request: Request) -> Response:
        future_response: asyncio.Future = self.send_message(request)
        response: Response = await future_response
        return response

    def send_message(self, request: Request) -> asyncio.Future:
        assert request["type"] == "request"
        future_response = self.dispatch_message(request)

        self.write_message(self.writer, request)

        return future_response

    async def recv_message(self) -> Response | Event:
        message = await super().recv_message()
        assert message["type"] == "response" or message["type"] == "event"
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
