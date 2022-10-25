from __future__ import annotations

import asyncio
from itertools import count
from typing import TypeVar

from vidb.connection import DAPConnection
from vidb.dap import (
    InitializeRequest,
    InitializeRequestArguments,
    InitializeResponse,
    Request,
)


T = TypeVar("T", bound=Request)


class SupportFlags:
    pass


async def initialize(client: DAPClient):
    arguments: InitializeRequestArguments = InitializeRequestArguments(
        clientID="vidb",
        clientName="vidb",
        adapterID="vidb",
        locale="en-US",

        linesStartAt1=True,
        columnsStartAt1=True,
        pathFormat="path",
        supportsVariableType=True,
    )

    response = await client.remote_call(
        InitializeRequest,
        "initialize",
        arguments,
    )

    client.server_support.configuration_done_request = \
        response["body"]["supportsConfigurationDoneRequest"]

    return response


def attach(client: DAPClient):
    arguments = dict(arguments=[])
    return client.remote_call(
        dict,
        "attach",
        arguments,
    )


def configuration_done(client: DAPClient):
    arguments = dict()
    return client.remote_call(
        dict,
        "configurationDone",
        arguments,
    )


def set_breakpoints(client: DAPClient, path, breakpoints):
    arguments = dict(
        source=dict(
            path=path,
        ),
        breakpoints=[{"line": bp} for bp in breakpoints],
    )
    return client.remote_call(
        dict,
        "setBreakpoints",
        arguments,
    )



class DAPClient:
    sequence = count()
    connection: DAPConnection

    def __init__(self, connection):
        self.connection = connection
        self.server_support = SupportFlags()

    def wait_for_event(self, event_name):
        event = asyncio.Event()
        self.add_event_listener(event_name, event.set)
        async def _waiter():
            await event.wait()
            self.remove_event_listener(event_name, event.set)
        return _waiter()

    def add_event_listener(self, event_name, listener):
        listeners = self.connection.dispatcher.events.setdefault(event_name, set())
        listeners.add(listener)

    def remove_event_listener(self, event_name, listener):
        listeners = self.connection.dispatcher.events.setdefault(event_name, set())
        listeners.remove(listener)

    async def initialize(self) -> None:
        # Initialization sequence:
        #
        #     https://github.com/microsoft/vscode/issues/4902#issuecomment-368583522
        #

        initialized_event = self.wait_for_event("initialized")

        await initialize(self)
        attach_response = attach(self)
        await initialized_event
        # await set_breakpoints(self, path="myscript.py", breakpoints=[2,9])
        if self.server_support.configuration_done_request:
            await configuration_done(self)
        await attach_response

    def remote_call(self, request_cls, command, arguments):
        request = self.prepare_request(
            request_cls,
            command,
            arguments,
        )
        return self.connection.send_message(request)

    def prepare_request(
        self,
        request_cls: type[T],
        command: str,
        arguments,
    ) -> T:
        return request_cls(
            seq=next(self.sequence),
            type="request",
            command=command,
            arguments=arguments,
        )
