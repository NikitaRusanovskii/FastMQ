import asyncio
import json
import logging
from abc import ABC, abstractmethod

import websockets

from .imanagers import IClientFabric, IFiltersManager, IRegistry
from .imessage_queue import IMessageQueue
from .logger import instance_logger

# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class IHandler(ABC):
    @abstractmethod
    async def handle(self, message: str):
        pass


class MessageHandler(IHandler):
    def __init__(self, filters_manager: IFiltersManager,
                 message_queue: IMessageQueue):
        self.filters_manager = filters_manager
        self.message_queue = message_queue

    async def handle(self, message: str):
        dm = json.loads(message)
        filters = dm.get("filters")
        msg = dm.get("message")
        all_ids = set()
        for filt in filters:
            ids = await self.filters_manager.get_cons_ids_by_filter(filt)
            if ids:
                [all_ids.add(id) for id in ids]
            else:
                continue
        id_list = list(all_ids)
        logger.info(f"message: {msg}, ids: {id_list}")
        await self.message_queue.publish(msg, id_list)


class CommandHandler:
    def __init__(self, filters_manager: IFiltersManager, registry: IRegistry):
        self.filters_manager = filters_manager
        self.registry = registry

    async def handle(self, message: str,
                     ws: websockets.ClientConnection) -> bool:
        if message.startswith("/subscribe_on"):
            sm = message.split()
            await self.filters_manager.subscribe_on(
                sm[1], await self.registry.get_id_by_websocket(ws)
            )
            return True
        else:
            return False


class Server:
    def __init__(
        self,
        filters_manager: IFiltersManager,
        registry: IRegistry,
        client_fabric: IClientFabric,
        message_queue: IMessageQueue,
    ):
        self.filters_manager = filters_manager
        self.registry = registry
        self.client_fabric = client_fabric
        self.message_queue = message_queue
        self.message_handler = MessageHandler(self.filters_manager,
                                              self.message_queue)
        self.command_handler = CommandHandler(self.filters_manager,
                                              self.registry)

    async def handler(self, websocket: websockets.ClientConnection):
        path = websocket.request.path
        client_addr = websocket.remote_address
        unit = await self.client_fabric.create(websocket, path)
        logger.info(f"Client created like {path}!")
        try:
            async for message in websocket:
                if not await self.command_handler.handle(message, websocket):
                    await self.message_handler.handle(message)
        except websockets.ConnectionClosed:
            logger.info(f"Connection with {client_addr} closed")
            await self.registry.cleanup(unit)

    async def start_server(self, server_addr: tuple[str, int]):
        async with websockets.serve(self.handler,
                                    server_addr[0], server_addr[1]):
            logger.info("Server started.")
            await asyncio.Future()
