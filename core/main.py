import asyncio
from .source import Server
from .cli import Console


async def main():
    server = Server()
    cli = Console(server.filters_manager)

    cli_task = asyncio.create_task(cli.on_command())
    server_task = asyncio.create_task(server.start_server())
    await server_task
    await cli_task

if __name__ == '__main__':
    asyncio.run(main())
