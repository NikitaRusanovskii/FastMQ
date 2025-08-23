import asyncio
import websockets
import logging
from abc import ABC, abstractmethod
from itertools import count
from .units import Producer, Consumer, Unit
from .configurator import instance_config


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('managers-logger')
config = instance_config()


START_CONSUMER_ID = int(config.get_element('UNIT_INFO', 'start_consumer_id'))
START_PRODUCER_ID = int(config.get_element('UNIT_INFO', 'start_producer_id'))


class IRegistry(ABC):
    @abstractmethod
    async def add_consumer(self, consumer: Consumer):
        pass

    @abstractmethod
    async def add_producer(self, producer: Producer):
        pass


class IClientFabric(ABC):
    @abstractmethod
    async def create(self,
                     websocket: websockets.ClientConnection,
                     path: str) -> Unit:
        pass


class Registry(IRegistry):
    def __init__(self, prod_ids: dict[int, Producer],
                 cons_ids: dict[int, Consumer]):
        self.prod_ids = prod_ids
        self.cons_ids = cons_ids
        self.cons_id = count(START_CONSUMER_ID)
        self.prod_id = count(START_PRODUCER_ID)
        self.lock = asyncio.Lock()

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


class ClientFabric(IClientFabric):
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
