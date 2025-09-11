from abc import ABC, abstractmethod

from websockets import ClientConnection

from .units import Consumer, Producer, Unit


class IFiltersManager(ABC):
    @abstractmethod
    async def get_cons_ids_by_filter(self, filter: str):
        pass

    # commands:
    @abstractmethod
    async def add(self, name: str):
        pass

    @abstractmethod
    async def remove(self, name: str):
        pass

    @abstractmethod
    async def subscribe_on(self, name: str, websocket_id: int):
        pass


class IRegistry(ABC):
    @abstractmethod
    async def get_consumer_by_id(self, id: int):
        pass

    @abstractmethod
    async def add_consumer(self, consumer: Consumer):
        pass

    @abstractmethod
    async def add_producer(self, producer: Producer):
        pass

    @abstractmethod
    async def cleanup(self, unit: Unit):
        pass

    @abstractmethod
    async def get_id_by_websocket(self,
                                  websocket: ClientConnection) -> int | None:
        pass


class IClientFabric(ABC):
    @abstractmethod
    async def create(self, websocket: ClientConnection, path: str) -> Unit:
        pass
