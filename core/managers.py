import asyncio
import websockets
import logging
from .logger import instance_logger
from itertools import count
from .units import Producer, Consumer, Unit


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger)


START_CONSUMER_ID = 0
START_PRODUCER_ID = 100


class FiltersManager:
    def __init__(self, filters: dict[str, list[int]]):
        self.filters = filters
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
                raise ValueError(f'Filter with name {name} not found!')
            self.filters.pop(name)
        logger.info(f'Filter {name} removed.')

    async def subscribe_on(self, name: str, websocket_id: int):
        async with self.lock:
            # Consumer не может создать свой фильтр и слушать его
            if not (name in self.filters.keys()):
                raise ValueError(f'Filter with name {name} not found!')
            self.filters[name].append(websocket_id)
        logger.info((f'Client with ID {websocket_id} '
                    f'subscribed on filter {name}.'))


class Registry:
    def __init__(self, prod_ids: dict[int, Producer],
                 cons_ids: dict[int, Consumer]):
        self.prod_ids = prod_ids
        self.cons_ids = cons_ids
        self.cons_id = count(START_CONSUMER_ID)
        self.prod_id = count(START_PRODUCER_ID)
        self.lock = asyncio.Lock()

    async def get_consumer_by_id(self, id: int):
        async with self.lock:
            try:
                return self.cons_ids[id]
            except KeyError as ex:
                logger.error(f'Unknown key: {ex}')
        return None

    async def add_consumer(self, consumer: Consumer):
        async with self.lock:
            cur_id = next(self.cons_id)
            self.cons_ids[cur_id] = consumer
            consumer.id = cur_id
        logger.info(f'Consumer added. ID {cur_id}')

    async def add_producer(self, producer: Producer):
        async with self.lock:
            cur_id = next(self.prod_id)
            self.prod_ids[cur_id] = producer
            producer.id = cur_id
        logger.info(f'Producer added.ID {cur_id}')

    async def cleanup(self, unit: Unit):
        async with self.lock:
            if isinstance(unit, Producer):
                self.prod_ids.pop(unit.id)
            elif isinstance(unit, Consumer):
                self.cons_ids.pop(unit.id)
        logger.info('Unit has been removed from storage!')


class ClientFabric:
    def __init__(self, registry: Registry):
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
