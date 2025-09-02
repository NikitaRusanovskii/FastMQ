import asyncio
from pathlib import Path
from .source import Server
from .managers import FiltersManager, Registry, ClientFabric
from .message_queue import MessageQueue
from .buffer import ROMBuffer
from .configurator import Config
from .cli import Console
import aiosqlite


async def main():
    cfg = Config(Path('config.ini'))

    start_consumer_id = cfg.get_int_element('UNIT_INFO', 'start_consumer_id')
    start_producer_id = cfg.get_int_element('UNIT_INFO', 'start_producer_id')
    attempts_count = cfg.get_int_element('QUEUE_INFO', 'attempts_count')
    time_sleep = cfg.get_int_element('QUEUE_INFO', 'time_sleep')
    queue_pause = cfg.get_int_element('QUEUE_INFO', 'queue_pause')
    timeout = cfg.get_float_element('QUEUE_INFO', 'timeout')

    fm = FiltersManager()
    rg = Registry(start_consumer_id=start_consumer_id,
                  start_producer_id=start_producer_id)
    cf = ClientFabric(rg)

    connection = await aiosqlite.connect('buffer.db')
    rb = ROMBuffer(connection)
    await rb.initialize()
    mq = MessageQueue(rb, rg, attempts_count, time_sleep,
                      queue_pause, timeout)
    server = Server(fm, rg, cf, mq)
    server_addr = (
        cfg.get_element('SERVER_INFO', 'server_ip'),
        cfg.get_int_element('SERVER_INFO', 'server_port')
    )
    cli = Console(server.filters_manager)
    message_queue_tast = asyncio.create_task(mq.loop())
    cli_task = asyncio.create_task(cli.on_command())
    server_task = asyncio.create_task(server.start_server(server_addr))
    try:
        await asyncio.gather(
            server_task,
            cli_task,
            message_queue_tast
        )
    finally:
        await connection.close()

if __name__ == '__main__':
    asyncio.run(main())
