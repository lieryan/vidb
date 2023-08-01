from contextlib import asynccontextmanager
from copy import deepcopy

from pytest import fixture

from vidb.connection import BaseDAPConnection
from vidb.dap import Response, Event, Request


class DAPServerMixin:
    @fixture(autouse=True)
    def setup_method(self, server_sequence, server_connection):
        self.__server_sequence = server_sequence
        self.__server_connection = server_connection

    @asynccontextmanager
    async def assert_request_response(
        self,
        command: str,
        response,
    ):
        response = deepcopy(response)

        request: Request = await self.__server_connection.recv_message()
        assert request["type"] == "request"
        assert request["command"] == command
        assert response["command"] == command

        yield request

        assert response["request_seq"] == request["seq"] or response["request_seq"] is None
        response["request_seq"] = request["seq"]
        self.send_message(response)

    def send_message(self, msg: Response | Event):
        seq = next(self.__server_sequence)
        assert msg["seq"] == seq or msg["seq"] is None
        msg["seq"] = seq
        self.__server_connection.send_message(msg)


class DAPServerConnection(BaseDAPConnection):
    def send_message(self, msg: Response | Event):
        assert msg["type"] in ["response", "event"]
        self.write_message(self.writer, msg)

    async def recv_message(self) -> Request:
        message = await super().recv_message()
        assert message["type"] == "request"
        return message
