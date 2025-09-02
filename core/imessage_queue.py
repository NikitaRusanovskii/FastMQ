from abc import ABC, abstractmethod
from .units import Consumer


class IMessageQueue(ABC):
    @abstractmethod
    async def publish(self, message: str, consumer_ids: list[int]):
        pass

    '''@abstractmethod
    async def wait_pong(self, websocket: ClientConnection) -> bool:
        pass'''

    @abstractmethod
    async def send_to(self, message: str, consumer: Consumer) -> bool:
        pass

    @abstractmethod
    async def loop(self):
        pass
