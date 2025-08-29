import asyncio
import logging
from .logger import instance_logger
from .imessage_queue import IMessageQueue
from .ibuffer import IBuffer
from .units import Consumer
from .imanagers import IRegistry


# logging
logger = logging.getLogger(__name__)
logger = instance_logger(logger, __name__)


class MessageQueue(IMessageQueue):
    def __init__(self,
                 buffer: IBuffer,
                 registry: IRegistry,
                 attempts_count: int,
                 time_sleep: int,
                 queue_pause: int):
        self.registry = registry
        self.buffer = buffer
        self.attempts_count = attempts_count
        self.time_sleep = time_sleep
        self.queue_pause = queue_pause

    async def publish(self, message: str, consumer_ids: list[int]):
        try:
            await self.buffer.add(message=message, consumer_ids=consumer_ids)
            logger.info('Public succesful.')
        except Exception as ex:
            logger.error(f'Error {ex}.')

    '''async def wait_pong(self, websocket: ClientConnection) -> bool:
        await asyncio.sleep(0.1)
        try:
            return True if await websocket.recv() == 'pong' else False
        except Exception as ex:
            logger.error(f'Error {ex}')'''

    '''async def send_to(self, message: str, websocket: ClientConnection) -> bool:
        for attempt in range(self.attempts_count):
            try:
                await websocket.send(message)
                if await self.wait_pong(websocket):
                    logger.info('Message sended.')
                    return True
                await asyncio.sleep(attempt * self.time_sleep)
            except Exception as ex:
                logger.error(f'Error {ex}')
                continue
        return False'''

    async def send_to(self, message: str, consumer: Consumer) -> bool:
        for attempt in range(self.attempts_count):
            try:
                await consumer.websocket.send(message)
                logger.info('Message sended.')
                return True
            except Exception as ex:
                logger.error(f'Error {ex}')
                continue
        return False

    async def loop(self):
        while True:
            tasks = []
            element = await self.buffer.pop_oldest()
            if not element:
                await asyncio.sleep(self.queue_pause)
                continue
            msg = element[1]
            consumer_ids = element[0]
            if (not msg) or (not consumer_ids):
                await asyncio.sleep(self.queue_pause)
                continue
            try:
                for id in consumer_ids:
                    ws = await self.registry.get_consumer_by_id(id)
                    tasks.append(self.send_to(msg,
                                              ws))
                await asyncio.gather(*tasks)
            except Exception as ex:
                logger.error(f'Error {ex}')
