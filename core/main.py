import asyncio
from pathlib import Path
from .source import Server
from .managers import FiltersManager, Registry, ClientFabric
from .message_queue import MessageQueue
from .buffer import ROMBuffer
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
    rb = ROMBuffer()
    await rb.initialize()
    attempts_count = cfg.get_int_element('QUEUE INFO', 'attempts_count')
    time_sleep = cfg.get_int_element('QUEUE INFO', 'time_sleep')
    queue_pause = cfg.get_int_element('QUEUE INFO', 'queue_pause')
    mq = MessageQueue(rb, rg, attempts_count, time_sleep, queue_pause)
    server = Server(fm, rg, cf, mq)

    server_addr = (
        cfg.get_element('SERVER_INFO', 'server_ip'),
        cfg.get_int_element('SERVER_INFO', 'server_port')
    )

    cli = Console(server.filters_manager)
    message_queue_tast = asyncio.create_task(mq.loop())
    cli_task = asyncio.create_task(cli.on_command())
    server_task = asyncio.create_task(server.start_server(server_addr))
    await asyncio.gather(
        server_task,
        cli_task,
        message_queue_tast
    )

if __name__ == '__main__':
    asyncio.run(main())
