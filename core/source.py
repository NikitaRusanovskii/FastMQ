import websockets
import asyncio
import json
import logging
from abc import ABC, abstractmethod
from .managers import ClientFabric, Registry, FiltersManager
from .units import Producer, Consumer


SERVER_ADDR = ('0.0.0.0', 25565)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("source-logger")


class IServer(ABC):
    @abstractmethod
    async def handler(self, websocket: websockets.ClientConnection):
        """Processes each client's connections separately.

        Args:
            websocket: websockets.ClientConnection."""
        pass

    @abstractmethod
    async def start_server(self):
        """Starts asynchronous connection handlers."""
        pass


class IMessangeHandler(ABC):
    @abstractmethod
    async def handle(self, message: str):
        """Processes incoming message from producer."""
        pass


class MessageHandler:
    def __init__(self,
                 prod_ids: dict[int, Producer],
                 cons_ids: dict[int, Consumer],
                 filters: dict[str, list[int]]):
        self.prod_ids = prod_ids
        self.cons_ids = cons_ids
        self.filters = filters

    async def send_on(self, message: str, ids: list[int]):
        for id in ids:
            if not (id in self.cons_ids):
                err = ValueError(f'ID {id} not found.')
                logger.info(f'Error {err}.')
                raise err
            await self.cons_ids[id].websocket.send(message)

    async def handle(self, message: str):
        unpacked = json.loads(message)
        msg = unpacked['message']
        filts = unpacked['filters']
        for filter in filts:
            await self.send_on(msg, self.filters[filter])


class Server(IServer):
    def __init__(self):
        self.prod_ids = {}
        self.cons_ids = {}
        self.filters = {'test': [0]}
        self.filters_manager = FiltersManager(self.filters)
        self.registry = Registry(self.prod_ids,
                                 self.cons_ids)
        self.client_fabric = ClientFabric(self.registry)
        self.message_handler = MessageHandler(self.prod_ids,
                                              self.cons_ids,
                                              self.filters)

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
