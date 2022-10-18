from itertools import count
from typing import TypeVar, Type

from vidb.connection import DAPConnection
from vidb.dap import Request, InitializeRequest, InitializeRequestArguments


T = TypeVar("T", bound=Request)


class DAPClient:
    sequence = count()
    connection: DAPConnection

    def __init__(self, connection):
        self.connection = connection

    async def initialize(self) -> None:
        request = self._create_initialize_request()
        response = await self.connection.send_message(request)
        print("response", response)

    def _create_initialize_request(self) -> InitializeRequest:
        arguments = InitializeRequestArguments(
            clientID="vidb",
            clientName="vidb",
            adapterID="vidb",
            locale="en-US",
        )
        return self.make_request(InitializeRequest, arguments)

    def make_request(self, request_cls: type[T], arguments) -> T:
        return request_cls(
            seq=next(self.sequence),
            type="request",
            command="initialize",
            arguments=arguments,
        )
