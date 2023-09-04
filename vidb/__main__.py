import asyncio
import sys

from prompt_toolkit.eventloop import use_asyncio_event_loop

from vidb.client import DAPClient
from vidb.connection import DAPConnection
from vidb.ui import UI


async def main():
    app = UI()

    portnum = sys.argv[1]
    connection = await DAPConnection.from_tcp("localhost", portnum)
    client = DAPClient(connection=connection)
    initial_load_task = asyncio.create_task(initial_load(client, app))

    use_asyncio_event_loop()
    await app.run()
    for msg in client.connection.dispatcher._messages:
        print(msg)


async def initial_load(client, app):
    await client.initialize()

    await app.threads_widget.attach(client)

    await app.variables_widget.attach(client, app.stacktrace_widget)
    await app.stacktrace_widget.attach(client, app.threads_widget)
    await app.source_widget.attach(client, app.stacktrace_widget)

    app.threads_widget.current_value = app.threads_widget.current_value


asyncio.run(main())
