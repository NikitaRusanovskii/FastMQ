import websockets
import asyncio
import json
import logging
from .managers import ClientFabric, Registry
from .units import Producer, Consumer


SERVER_ADDR = ('0.0.0.0', 25565)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("source-logger")


class MessageHandler:
    def __init__(self,
                 prod_ids: dict[int, Producer],
                 cons_ids: dict[int, Consumer]):
        self.prod_ids = prod_ids
        self.cons_ids = cons_ids

    async def send_to(self, message: str, id: int):
        if not (id in self.cons_ids.keys()):
            err = ValueError(f'ID not found: {id}')
            logger.error(f'Error {err} is raised.')
            raise err
        socket = self.cons_ids[id]
        await socket.websocket.send(message)

    async def handle(self, message: str):
        msg_dict = json.loads(message)
        ids = msg_dict['IDs']
        msg = msg_dict['message']
        for id in ids:
            await self.send_to(msg, id)
        logger.info(f'Message {message} handled.')


class Server:
    def __init__(self):
        self.prod_ids = {}
        self.cons_ids = {}
        self.registry = Registry(self.prod_ids,
                                 self.cons_ids)
        self.client_fabric = ClientFabric(self.registry)
        self.message_handler = MessageHandler(self.prod_ids,
                                              self.cons_ids)

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
