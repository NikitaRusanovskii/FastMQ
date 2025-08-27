import websockets
import asyncio
import json
import logging
from .logger import instance_logger
from .imanagers import IClientFabric, IRegistry, IFiltersManager
from abc import ABC, abstractmethod


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class IMessageHandler(ABC):
    @abstractmethod
    async def handle(self, message: str):
        pass


class MessageHandler(IMessageHandler):
    def __init__(self,
                 registry: IRegistry,
                 filters_manager: IFiltersManager):
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
    def __init__(self,
                 filters_manager: IFiltersManager,
                 registry: IRegistry,
                 client_fabric: IClientFabric):
        self.filters_manager = filters_manager
        self.registry = registry
        self.client_fabric = client_fabric
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

    async def start_server(self, server_addr: tuple[str, int]):
        async with websockets.serve(self.handler, server_addr[0],
                                    server_addr[1]):
            logger.info('Server started.')
            await asyncio.Future()
