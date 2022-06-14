from unittest import IsolatedAsyncioTestCase
from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from sqlalchemy import delete
from sqlalchemy.orm import Session
from db.rdb.model import TBProxy
from db.rdb.rdb_dbutil import RDBDbUtil


class TestRDBDbUtil(IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.util = RDBDbUtil()
        return await super().asyncSetUp()

    def _delete(self, id: int):
        try:
            with self.util.Session() as session:
                session.execute(delete(TBProxy).where(TBProxy.id == id))
                session.commit()
        except:
            return

    def _insert(self, session: Session, instance: TBProxy):
        session.add(instance)
        session.commit()
        return instance

    async def test_try_insert(self):
        try:
            proxy = Proxy(Protocol.HTTP, '127.0.0.1', '3336',
                          Verify.HTTP, Anonymous.HIGH)
            inserted = await self.util.try_insert(proxy)
            self.assertIsNotNone(inserted)
        finally:
            self._delete(inserted.id)

    async def test_try_insert_exist(self):
        ks = {"protocol": Protocol.HTTP, "ip": '127.0.0.1', "port": 3336,
              "verify": Verify.HTTP, "anonymous": Anonymous.HIGH}
        proxy = Proxy(**ks)
        session = self.util.Session()
        try:
            inserted = self._insert(session, TBProxy(**ks))
            existed = await self.util.try_insert(proxy)
            self.assertIsNone(existed)
        finally:
            self._delete(inserted.id)
            session.close()

    async def test__update(self):
        NS = 0.85
        ks = {"protocol": Protocol.HTTP, "ip": '127.0.0.1', "port": 3336,
              "verify": Verify.HTTP, "anonymous": Anonymous.HIGH}

        def cb(i: TBProxy):
            i.speed = NS
            return i
        instance = TBProxy(**ks)
        try:
            with self.util.Session() as session:
                inserted = self._insert(session, instance)
                proxy = StoredProxy(inserted.id, **ks, score=100)  # {id, ...}
            proxy = self.util._update(proxy, cb)
            self.assertEqual(proxy.speed, NS)
        finally:
            self._delete(inserted.id)

    async def test_gets(self):
        session = self.util.Session()
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH)
        ]
        try:
            session.add_all(ins)
            session.commit()
            # SELECT...
            # FROM proxy
            # WHERE proxy.protocol = %(protocol_1)s AND proxy.verify = %(verify_1)s
            # LIMIT %(param_1)s, %(param_2)s
            gets = await self.util.gets(protocol=Protocol.HTTPS, verify=Verify.HTTPS)
            self.assertSetEqual(
                set([ins[0].id, ins[1].id]), set([p.id for p in gets]))
        finally:
            [session.delete(i) for i in ins]
            session.commit()
            session.close()

    async def test_count(self):
        session = self.util.Session()
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH)
        ]
        try:
            session.add_all(ins)
            session.commit()
            # SELECT count(*) AS count_1
            # FROM
            #   (SELECT...
            #       FROM proxy
            #       WHERE proxy.protocol = %(protocol_1)s AND proxy.verify = %(verify_1)s
            #   )AS anon_1
            count = await self.util.count(protocol=Protocol.HTTPS, verify=Verify.HTTPS)
            self.assertEqual(count, 2)
        finally:
            [session.delete(i) for i in ins]
            session.commit()
            session.close()
