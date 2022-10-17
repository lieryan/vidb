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


class DAPDebugger:
    sequence = count()

    def _validate_initialize(self, parsed_request: _Request) -> InitializeRequest:
        return cast(InitializeRequest, parsed_request)

    async def _send(self, request: bytes) -> bytes:
        parsed_request: _Request = json.loads(request.decode("utf-8"))
        response: _Response = self._handle_initialize(
            self._validate_initialize(parsed_request),
        )
        prepared_response: bytes = json.dumps(response).encode("utf-8")
        return prepared_response

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
