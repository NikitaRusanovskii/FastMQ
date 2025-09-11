import pytest
import pytest_asyncio
import aiosqlite
from core.buffer import ROMBuffer


@pytest_asyncio.fixture
async def db_con():
    # создание базы данных в оперативной памяти
    connection = await aiosqlite.connect(':memory:')
    yield connection
    await connection.close()


@pytest_asyncio.fixture
async def buffer(db_con):
    buffer = ROMBuffer(db_con)
    await buffer.initialize()
    return buffer


@pytest.mark.asyncio
async def test_buffer_initialization(buffer):
    async with buffer.connection.execute(
        """SELECT name FROM sqlite_master
        WHERE type='table' AND name='messages'"""
    ) as cursor:
        result = await cursor.fetchone()
        assert result is not None


@pytest.mark.asyncio
async def test_buffer_add_and_get(buffer):
    await buffer.add([0, 1, 13, 5], 'hello to 0 1 13 5')
    result = await buffer.get_old_element()
    assert result == (1, [0, 1, 13, 5], 'hello to 0 1 13 5')


@pytest.mark.asyncio
async def test_buffer_get_old_element(buffer):
    await buffer.add([1, 2, 3], 'hello one')
    await buffer.add([1, 2, 3], 'hello two')
    await buffer.add([1, 2, 3], 'hello three')

    result = await buffer.get_old_element()
    assert result[2] == 'hello one'


@pytest.mark.asyncio
async def test_buffer_pop_old_element(buffer):
    await buffer.add([1, 2, 3], 'hello one')
    await buffer.add([1, 2, 3], 'hello two')
    await buffer.add([1, 2, 3], 'hello three')

    result = await buffer.pop_oldest()
    assert result[2] == 'hello one'

    result = await buffer.pop_oldest()
    assert result[2] == 'hello two'

    result = await buffer.pop_oldest()
    assert result[2] == 'hello three'


@pytest.mark.asyncio
async def test_buffer_delete_old(buffer):
    await buffer.add([1, 2, 3], 'hello one')
    await buffer.add([1, 2, 3], 'hello two')
    await buffer.add([1, 2, 3], 'hello three')

    await buffer.delete_old()
    result = await buffer.get_old_element()
    assert result[2] == 'hello two'


# Тесты выше работают корректно
