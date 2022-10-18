import json
from itertools import count

from vidb.dap import (
    InitializeRequest,
    InitializeRequestArguments,
    _Request,
    _Response,
)
from vidb.connection import DAPConnection


class DAPClient:
    sequence = count()
    connection: DAPConnection

    def __init__(self, connection):
        self.connection = connection

    async def send(self, request: _Request) -> _Response:
        prepared_request: bytes = json.dumps(request).encode("utf-8")
        raw_response: bytes = await self.connection._send(prepared_request)
        response: _Response = json.loads(raw_response.decode("utf-8"))
        return response

    async def initialize(self) -> None:
        request = self._create_initialize_request()
        response = await self.send(request)
        print("response", response)

    def _create_initialize_request(self) -> InitializeRequest:
        arguments = InitializeRequestArguments(
            clientID="vidb",
            clientName="vidb",
            adapterID="vidb",
            locale="en-US",
        )
        return InitializeRequest(
            seq=next(self.sequence),
            type="request",
            command="initialize",
            arguments=arguments,
        )
