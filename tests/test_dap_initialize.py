import asyncio
from contextlib import asynccontextmanager
from copy import deepcopy
from itertools import count

from vidb.client import DAPClient
from vidb.connection import DAPConnection, BaseDAPConnection
from vidb.dap import Response, Event, Request


INITIALIZE_RESPONSE = {
    "seq": 1,
    "type": "response",
    "request_seq": 1,
    "success": True,
    "command": "initialize",
    "body": {
        "supportsCompletionsRequest": True,
        "supportsConditionalBreakpoints": True,
        "supportsConfigurationDoneRequest": True,
        "supportsDebuggerProperties": True,
        "supportsDelayedStackTraceLoading": True,
        "supportsEvaluateForHovers": True,
        "supportsExceptionInfoRequest": True,
        "supportsExceptionOptions": True,
        "supportsFunctionBreakpoints": True,
        "supportsHitConditionalBreakpoints": True,
        "supportsLogPoints": True,
        "supportsModulesRequest": True,
        "supportsSetExpression": True,
        "supportsSetVariable": True,
        "supportsValueFormattingOptions": True,
        "supportsTerminateRequest": True,
        "supportsGotoTargetsRequest": True,
        "supportsClipboardContext": True,
        "exceptionBreakpointFilters": [
            {
                "filter": "raised",
                "label": "Raised Exceptions",
                "default": False,
                "description": "Break whenever any exception is raised.",
            },
            {
                "filter": "uncaught",
                "label": "Uncaught Exceptions",
                "default": True,
                "description": "Break when the process is exiting due to unhandled exception.",
            },
            {
                "filter": "userUnhandled",
                "label": "User Uncaught Exceptions",
                "default": False,
                "description": "Break when exception escapes into library code.",
            },
        ],
        "supportsStepInTargetsRequest": True,
    },
}

INITIALIZED_EVENT = {
    "seq": 2,
    "type": "event",
    "event": "initialized",
}

CONFIGURATION_DONE_RESPONSE = {
    "seq": 3,
    "type": "response",
    "request_seq": 3,
    "success": True,
    "command": "configurationDone",
}

ATTACH_RESPONSE = {
    "seq": 4,
    "type": "response",
    "request_seq": 2,
    "success": True,
    "command": "attach",
}


class DAPServerConnection(BaseDAPConnection):
    def send_message(self, msg: Response | Event):
        assert msg["type"] in ["response", "event"]
        self.write_message(self.writer, msg)

    async def recv_message(self) -> Request:
        message = await super().recv_message()
        assert message["type"] == "request"
        return message


class TestInitialize:
    @asynccontextmanager
    async def assert_request_response(
        self,
        command: str,
        response,
    ):
        response = deepcopy(response)

        request: Request = await self.server_connection.recv_message()
        assert request["type"] == "request"
        assert request["command"] == command
        assert response["command"] == command
        yield request
        assert response["request_seq"] == request["seq"] or response["request_seq"] is None
        response["request_seq"] = request["seq"]
        self.send_message(response)

    def send_message(self, msg: Response | Event):
        seq = next(self.server_sequence)
        assert msg["seq"] == seq or msg["seq"] is None
        msg["seq"] = seq
        self.server_connection.send_message(msg)

    async def test_attach_initialize_sequence(self, pipe_connection_factory):
        async def server_initialize():
            async with self.assert_request_response(
                "initialize", response=INITIALIZE_RESPONSE
            ) as initialize_request:
                pass

            async with self.assert_request_response(
                "attach", response=ATTACH_RESPONSE
            ) as attach_request:
                self.send_message(INITIALIZED_EVENT)

                async with self.assert_request_response(
                    "configurationDone", response=CONFIGURATION_DONE_RESPONSE
                ) as configuration_done_request:
                    pass

        self.server_sequence = count(1)

        reader, server_writer = await pipe_connection_factory()
        server_reader, writer = await pipe_connection_factory()

        self.server_connection = DAPServerConnection(server_reader, server_writer)
        connection = DAPConnection(reader, writer)
        client = DAPClient(connection=connection)
        connection.start_listening()
        await asyncio.gather(
            server_initialize(),
            client.initialize(),
        )
