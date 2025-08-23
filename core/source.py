import websockets
import asyncio
import json
import logging
from .logger import instance_logger
from .managers import ClientFabric, Registry, FiltersManager
from .configurator import instance_config


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)

# configs
config = instance_config()

SERVER_ADDR = (
    config.get_element('SERVER_INFO', 'server_ip'),
    int(config.get_element('SERVER_INFO', 'server_port'))
)


class MessageHandler:
    def __init__(self,
                 registry: Registry,
                 filters_manager: FiltersManager):
        self.registry = registry
        self.filters_manager = filters_manager

    async def send_on(self, message: str, ids: list[int]):
        for id in ids:
            consumer = await self.registry.get_consumer_by_id(id)
            if consumer is None:
                logger.warning('Unknown consumer')
                return
            await consumer.websocket.send(message)

    async def handle(self, message: str):
        unpacked = json.loads(message)
        msg = unpacked['message']
        filts = unpacked['filters']
        for f in filts:
            ids = await self.filters_manager.get_cons_ids_by_filter(f)
            await self.send_on(msg, ids)


class Server:
    def __init__(self):
        self.prod_ids = {}
        self.cons_ids = {}
        self.filters = {'test': [0]}
        self.filters_manager = FiltersManager(self.filters)
        self.registry = Registry(self.prod_ids,
                                 self.cons_ids)
        self.client_fabric = ClientFabric(self.registry)
        self.message_handler = MessageHandler(self.registry,
                                              self.filters_manager)

    async def handler(self, websocket: websockets.ClientConnection):
        path = websocket.request.path
        client_addr = websocket.remote_address
        unit = await self.client_fabric.create(websocket, path)
        logger.info(f'Client created like {path}!')
        try:
            async for message in websocket:
                await self.message_handler.handle(message)
        except websockets.ConnectionClosed:
            logger.info(f'Connection with {client_addr} closed')
            self.registry.cleanup(unit)

    async def start_server(self):
        async with websockets.serve(self.handler, SERVER_ADDR[0],
                                    SERVER_ADDR[1]):
            logger.info('Server started.')
            await asyncio.Future()
