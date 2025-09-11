import pytest

from core.managers import FiltersManager


@pytest.mark.asyncio
class TestFiltersManager:
    @pytest.fixture(autouse=True)
    def setup(self):
        self.filters = {}
        self.fm = FiltersManager(self.filters)

    @pytest.mark.parametrize("input, expected", [("a", {"a": []}), ("b", {"b": []})])
    async def test_add(self, input, expected):
        await self.fm.add(input)
        result = self.fm.filters
        assert result == expected

    @pytest.mark.parametrize(
        "input, expected", [("a", {"b": [], "c": []}), ("b", {"a": [], "c": []})]
    )
    async def test_remove(self, input, expected):
        await self.fm.add("a")
        await self.fm.add("b")
        await self.fm.add("c")

        await self.fm.remove(input)
        result = self.fm.filters
        assert result == expected

    @pytest.mark.parametrize(
        "fname, cid, expected",
        [
            ("a", 3, {"a": [3], "b": []}),
            ("b", 2, {"a": [], "b": [2]}),
        ],
    )
    async def test_subscribe_on(self, fname, cid, expected):
        await self.fm.add("a")
        await self.fm.add("b")
        await self.fm.subscribe_on(fname, cid)
        result = self.fm.filters
        assert result == expected

    @pytest.mark.parametrize("input, expected", [("a", [0]), ("b", None)])
    async def test_get_cons_ids_by_filter(self, input, expected):
        await self.fm.add("a")
        await self.fm.subscribe_on("a", 0)
        result = await self.fm.get_cons_ids_by_filter(input)
        assert result == expected
