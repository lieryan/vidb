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
    await client.initialize()

    await app.threads_widget.attach(client)

    use_asyncio_event_loop()
    await app.run()


asyncio.run(main())
