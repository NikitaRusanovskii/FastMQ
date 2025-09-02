import asyncio
import websockets
import logging
from .logger import instance_logger
from itertools import count
from .units import Producer, Consumer, Unit
from .imanagers import IFiltersManager, IClientFabric, IRegistry
from websockets import ClientConnection


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class FiltersManager(IFiltersManager):
    def __init__(self):
        self.filters = {}
        self.lock = asyncio.Lock()

    async def get_cons_ids_by_filter(self, filter: str):
        async with self.lock:
            try:
                return self.filters[filter]
            except KeyError as ex:
                logger.error(f'Unknown filter: {ex}')
        return None

    # commands:
    async def add(self, name: str):
        async with self.lock:
            self.filters[name] = []
        logger.info(f'Filter {name} added.')

    async def remove(self, name: str):
        async with self.lock:
            if not (name in self.filters.keys()):
                logger.error(f'Filter with name {name} not found!')
                return
            self.filters.pop(name)
        logger.info(f'Filter {name} removed.')

    async def subscribe_on(self, name: str, websocket_id: int):
        async with self.lock:
            # Consumer не может создать свой фильтр и слушать его
            if not (name in self.filters.keys()):
                logger.error(f'Filter with name {name} not found!')
                return
            self.filters[name].append(websocket_id)
        logger.info((f'Client with ID {websocket_id} '
                    f'subscribed on filter {name}.'))


class Registry(IRegistry):
    def __init__(self,
                 start_consumer_id,
                 start_producer_id):
        self.prod_ids = {}
        self.cons_ids = {}
        self.sock_ids = {}
        self.cons_id = count(start_consumer_id)
        self.prod_id = count(start_producer_id)
        self.lock = asyncio.Lock()

    async def get_consumer_by_id(self, id: int):
        async with self.lock:
            try:
                return self.cons_ids[id]
            except KeyError as ex:
                logger.error(f'Unknown key: {ex}')
        return None

    async def get_id_by_websocket(self,
                                  websocket: ClientConnection) -> int | None:
        async with self.lock:
            try:
                return self.sock_ids[websocket]
            except Exception as ex:
                logger.error(f'Error {ex}')
        return None

    async def add_consumer(self, consumer: Consumer):
        async with self.lock:
            cur_id = next(self.cons_id)
            self.cons_ids[cur_id] = consumer
            consumer.id = cur_id
            self.sock_ids[consumer.websocket] = cur_id
        logger.info(f'Consumer added. ID {cur_id}')

    async def add_producer(self, producer: Producer):
        async with self.lock:
            cur_id = next(self.prod_id)
            self.prod_ids[cur_id] = producer
            producer.id = cur_id
            self.sock_ids[producer.websocket] = cur_id
        logger.info(f'Producer added.ID {cur_id}')

    async def cleanup(self, unit: Unit):
        # мне не нравится реализация
        async with self.lock:
            if isinstance(unit, Producer):
                if self.prod_ids.get(unit.id):
                    self.prod_ids.pop(unit.id)
                    self.sock_ids.pop(unit.websocket)
            elif isinstance(unit, Consumer):
                if self.cons_ids.get(unit.id):
                    self.cons_ids.pop(unit.id)
                    self.sock_ids.pop(unit.websocket)
        logger.info('Unit has been removed from storage!')


class ClientFabric(IClientFabric):
    def __init__(self, registry: IRegistry):
        self.registry = registry
        self.roles = {
            'consumer': Consumer,
            'producer': Producer
        }
        self.regs = {
            'consumer': self.registry.add_consumer,
            'producer': self.registry.add_producer
        }

    async def create(self,
                     websocket: websockets.ClientConnection,
                     path: str) -> Unit:
        role = path.strip('/')
        if not (role in self.roles):
            err = ValueError(f'Not found role: {role}')
            logger.error(f'Error {err} raised.')
            raise err
        unit = self.roles[role](websocket)
        await self.regs[role](unit)
        return unit
