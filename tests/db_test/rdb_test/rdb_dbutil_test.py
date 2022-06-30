from unittest import IsolatedAsyncioTestCase

from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from db.rdb.model import TBProxy
from db.rdb.rdb_dbutil import RDBDbUtil
from sqlalchemy.orm import Session
from util.config import RDBConfig


class TestRDBDbUtil(IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        cls.util = RDBDbUtil(RDBConfig.URL, echo=True)

    async def asyncSetUp(self) -> None:
        self.truncate()

    async def asyncTearDown(self) -> None:
        self.truncate()

    def truncate(self):
        with self.util.Session() as session:
            session.execute(f'TRUNCATE TABLE {TBProxy.__tablename__};')
            session.commit()

    def _insert(self, session: Session, instance: TBProxy):
        session.add(instance)
        session.commit()
        return instance

    async def test_try_insert(self):
        proxy = Proxy(Protocol.HTTP, '127.0.0.1', '3336',
                      Verify.HTTP, Anonymous.HIGH)
        inserted = await self.util.try_insert(proxy)
        self.assertIsNotNone(inserted)

    async def test_try_insert_exist(self):
        ks = {"protocol": Protocol.HTTP, "ip": '127.0.0.1', "port": 3336,
              "verify": Verify.HTTP, "anonymous": Anonymous.HIGH}
        proxy = Proxy(**ks)
        with self.util.Session() as session:
            self._insert(session, TBProxy(**ks))
            existed = await self.util.try_insert(proxy)
            self.assertIsNone(existed)

    async def test__update(self):
        NS = 0.85
        ks = {"protocol": Protocol.HTTP, "ip": '127.0.0.1', "port": 3336,
              "verify": Verify.HTTP, "anonymous": Anonymous.HIGH}

        def cb(i: TBProxy):
            i.speed = NS
            return i
        instance = TBProxy(**ks)
        with self.util.Session() as session:
            inserted = self._insert(session, instance)
            proxy = StoredProxy(inserted.id, **ks, score=100)  # {id, ...}
        proxy = await self.util._update(proxy, cb)
        self.assertEqual(proxy.speed, NS)

    async def test_gets(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH)
        ]
        with self.util.Session() as session:
            session.add_all(ins)
            session.commit()
            # SELECT...
            # FROM proxy
            # WHERE proxy.protocol = %(protocol_1)s AND proxy.verify = %(verify_1)s
            # LIMIT %(param_1)s, %(param_2)s
            gets = await self.util.gets(protocol=Protocol.HTTPS, verify=Verify.HTTPS)
            self.assertSetEqual(
                set([ins[0].id, ins[1].id]), set([p.id for p in gets]))

    async def test_count(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH)
        ]
        with self.util.Session() as session:
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

    async def test_gets_random(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH)
        ]
        with self.util.Session() as session:
            session.add_all(ins)
            session.commit()
            # SELECT...
            # FROM proxy
            # WHERE proxy.protocol = %(protocol_1)s AND proxy.verify = %(verify_1)s
            # ORDER BY rand()
            # LIMIT 2
            proxies = await self.util.gets_random(protocol=Protocol.HTTPS, verify=Verify.HTTPS, limit=2)
            self.assertTrue(set([p.id for p in ins]) >
                            set([p.id for p in proxies]))

    async def test_delete(self):
        ins = TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                      verify=Verify.HTTPS, anonymous=Anonymous.HIGH)
        with self.util.Session() as session:
            inserted = self._insert(session, ins)
            await self.util.delete(inserted)
        with self.util.Session() as session:  # creat enew session
            q = session.get(TBProxy, inserted.id)
            self.assertIsNone(q)

    async def test_delete_unexist(self):
        ins = TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                      verify=Verify.HTTPS, anonymous=Anonymous.HIGH)

        with self.util.Session() as session:
            inserted = self._insert(session, ins)
            session.delete(inserted)
            session.commit()
            self.util.delete(inserted)

    async def test_gets_score(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, score=30),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, score=10),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH, score=10)
        ]
        with self.util.Session() as session:
            session.add_all(ins)
            session.commit()
            gets = await self.util.gets(protocol=Protocol.HTTPS, verify=Verify.HTTPS, min_score=15)
            self.assertSetEqual(
                set([ins[0].id]), set([p.id for p in gets]))

    async def test_gets_score_empty(self):
        gets = await self.util.gets(protocol=Protocol.HTTPS, verify=Verify.HTTPS, min_score=15, max_score=10)
        self.assertListEqual(gets, [])

    async def test_gets_speed(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, speed=-1),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, speed=-1),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH, speed=2.0)
        ]
        with self.util.Session() as session:
            session.add_all(ins)
            session.commit()
            """
            WHERE ... proxy.speed >= %(speed_1)s ...
            """
            gets = await self.util.gets(min_speed=0)
            self.assertSetEqual(
                set([ins[2].id]), set([p.id for p in gets]))

    async def test_gets_speed_eq(self):
        ins = [
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.1', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, speed=-1),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.2', port=3306,
                    verify=Verify.HTTPS, anonymous=Anonymous.HIGH, speed=-1),
            TBProxy(protocol=Protocol.HTTPS, ip='127.0.0.3', port=3306,
                    verify=Verify.UDP, anonymous=Anonymous.HIGH, score=2.0)
        ]
        with self.util.Session() as session:
            session.add_all(ins)
            session.commit()
            """
            WHERE ... proxy.speed = %(speed_1)s...
            """
            gets = await self.util.gets(protocol=Protocol.HTTPS, verify=Verify.HTTPS, min_speed=-1, max_speed=-1)
            self.assertSetEqual(
                set([ins[0].id, ins[1].id]), set([p.id for p in gets]))
