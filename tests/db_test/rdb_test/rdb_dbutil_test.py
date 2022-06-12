from unittest import IsolatedAsyncioTestCase
from db.model import Anonymous, Protocol, Proxy, Verify
from sqlalchemy import delete
from db.rdb.model import TBProxy
from db.rdb.rdb_dbutil import RDBDbUtil


class TestRDBDbUtil(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.util = RDBDbUtil()
        return await super().asyncSetUp()

    def _delete(self, id) -> None:
        try:
            with self.util.Session() as session:
                session.execute(delete(TBProxy).where(TBProxy.id == id))
                session.commit()
        except:
            return

    async def test_try_insert(self):
        proxy = Proxy(Protocol.HTTP, '127.0.0.1', '3336',
                      Verify.HTTP, Anonymous.HIGH)
        inserted = await self.util.try_insert(proxy)
        self.assertIsNotNone(inserted)
        self._delete(inserted.id)

    async def test_try_insert_exist(self):
        proxy = Proxy(Protocol.HTTP, '127.0.0.1', '3336',
                      Verify.HTTP, Anonymous.HIGH)
        inserted = await self.util.try_insert(proxy)
        existed = await self.util.try_insert(proxy)
        self.assertIsNone(existed)
        self._delete(inserted.id)
