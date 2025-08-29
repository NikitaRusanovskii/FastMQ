from abc import ABC, abstractmethod


class IBuffer(ABC):
    @abstractmethod
    async def get_old_element(self) -> tuple[list, str] | None:
        pass

    @abstractmethod
    async def add(self, consumer_ids: list, message: str) -> None:
        pass

    @abstractmethod
    async def delete_old(self):
        pass

    @abstractmethod
    async def pop_oldest(self) -> tuple[list, str] | None:
        pass
