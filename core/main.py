import asyncio
from pathlib import Path
from .source import Server
from .managers import FiltersManager, Registry, ClientFabric
from .configurator import Config
from .cli import Console


async def main():
    cfg = Config(Path('config.ini'))

    start_consumer_id = cfg.get_int_element('UNIT_INFO', 'start_consumer_id')
    start_producer_id = cfg.get_int_element('UNIT_INFO', 'start_producer_id')

    fm = FiltersManager()
    rg = Registry(start_consumer_id=start_consumer_id,
                  start_producer_id=start_producer_id)
    cf = ClientFabric(rg)
    server = Server(fm, rg, cf)

    server_addr = (
        cfg.get_element('SERVER_INFO', 'server_ip'),
        cfg.get_int_element('SERVER_INFO', 'server_port')
    )

    cli = Console(server.filters_manager)

    cli_task = asyncio.create_task(cli.on_command())
    server_task = asyncio.create_task(server.start_server(server_addr))
    await server_task
    await cli_task

if __name__ == '__main__':
    asyncio.run(main())
