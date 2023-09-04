from __future__ import annotations

import asyncio
from itertools import count
from typing import TypeVar

from vidb.connection import DAPConnection
from vidb.dap import (
    AttachRequest,
    AttachRequestArguments,
    ConfigurationDoneRequest,
    ConfigurationDoneArguments,
    InitializeRequest,
    InitializeRequestArguments,
    InitializeResponse,
    ThreadsRequest,
    Request,
    StackTraceArguments,
    StackTraceRequest,
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
        # supportsVariableType=True,
    )

    response: InitializeResponse = await client.remote_call(
        InitializeRequest,
        "initialize",
        arguments,
    )

    client.server_support.configuration_done_request = response[
        "supportsConfigurationDoneRequest"
    ]

    return response


def attach(client: DAPClient):
    arguments: AttachRequestArguments = dict(
        justMyCode=False,
        pathMappings=[
            # {
            #     "localRoot": "/home/lieryan/.virtualenvs/smc-console-api-d8bry_A7-py3.10/lib/python3.10/site-packages/",
            #     "remoteRoot": "/opt/app/venv/lib/python3.10/site-packages"
            # },
            {
                "localRoot": "/home/lieryan/Projects/SP-258/",
                "remoteRoot": "/opt/app/app/"
            },
        ],
        request="attach",
        # stopOnEntry=True, # launch only
        # "name": "test",
    )
    return client.remote_call(
        AttachRequest,
        "attach",
        arguments,
    )


def configuration_done(client: DAPClient):
    arguments: ConfigurationDoneArguments = dict()
    return client.remote_call(
        ConfigurationDoneRequest,
        "configurationDone",
        arguments,
    )


# def set_breakpoints(client: DAPClient, path, breakpoints):
#     arguments = dict(
#         source=dict(
#             path=path,
#         ),
#         breakpoints=[{"line": bp} for bp in breakpoints],
#     )
#     return client.remote_call(
#         dict,
#         "setBreakpoints",
#         arguments,
#     )


def threads(client: DAPClient):
    return client.remote_call(
        ThreadsRequest,
        "threads",
        arguments=None,
    )


def stack_trace(client: DAPClient, *, thread_id: int):
    arguments: StackTraceArguments = dict(
        threadId=thread_id,
    )
    return client.remote_call(
        StackTraceRequest,
        "stackTrace",
        arguments=arguments,
    )


def scopes(client: DAPClient, *, frame_id):
    arguments: ... = dict(
        frameId=frame_id,
    )
    return client.remote_call(
        dict,
        "scopes",
        arguments=arguments,
    )


def variables(client: DAPClient, *, variables_reference):
    arguments: ... = dict(
        variablesReference=variables_reference,
    )
    return client.remote_call(
        dict,
        "variables",
        arguments=arguments,
    )


class DAPClient:
    sequence: count
    connection: DAPConnection

    def __init__(self, connection):
        self.connection = connection
        self.server_support = SupportFlags()
        self.sequence = count(1)

    def wait_for_event(self, event_name):
        event = asyncio.Event()
        listener = lambda e: event.set()
        self.add_event_listener(event_name, listener)

        async def _waiter():
            await event.wait()
            self.remove_event_listener(event_name, listener)

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
        # thread_stopped_event = self.wait_for_event("thread")
        attach_response = attach(self)
        await initialized_event
        # resp = await set_breakpoints(self, path="myscript.py", breakpoints=[2,9])
        if self.server_support.configuration_done_request:
            await configuration_done(self)
        await attach_response

    def remote_call(self, request_cls: type[Request], command: str, arguments):
        async def _return_or_raise(future_response):
            response = await future_response
            assert response["type"] == "response"
            assert response["command"] == command
            assert request["seq"] == response["request_seq"]
            if response["success"]:
                return response.get("body", None)
            else:
                response = dict(response)
                del response["seq"]
                del response["type"]
                del response["request_seq"]
                del response["success"]
                del response["command"]
                message = response.pop("message")
                raise Exception(message + (str(response) if response else ""))

        request = self.prepare_request(
            request_cls,
            command,
            arguments,
        )
        return _return_or_raise(self.connection.send_message(request))

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
