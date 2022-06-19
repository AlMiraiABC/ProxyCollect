from typing import Callable
from unittest import TestCase

from db.model import Anonymous, Protocol, Verify
from db.rdb.model import TBProxy
from db.rdb.rdb_dbutil import _RDBDAO
from sqlalchemy import create_engine
from sqlalchemy.orm import Session as S
from sqlalchemy.orm import sessionmaker
from util.config import RDBConfig

engine = create_engine(RDBConfig.URL, pool_size=5, max_overflow=3,
                       echo=True, echo_pool=True)
Session: Callable[[], S] = sessionmaker(engine)


class Test_RDBDAO(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dao = _RDBDAO()

    def trunct(self):
        with Session() as session:
            session.execute(f'truncate table {TBProxy.__tablename__}')
            session.commit()

    def setUp(self) -> None:
        self.trunct()

    def tearDown(self) -> None:
        self.trunct()

    def _insert(self, session: S, instance: TBProxy):
        session.add(instance)
        session.commit()
        return instance

    def test_get_by_id_exist(self):
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            instance = self._insert(session, instance)
            inserted = self.dao.get_by_id(session, instance.id)
            self.assertIsNotNone(inserted)

    def test_get_by_id_unexist(self):
        with Session() as session:
            inserted = self.dao.get_by_id(session, -1)
            self.assertIsNone(inserted)

    def test_try_insert_unexist(self):
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            inserted = self.dao.try_insert(session, instance)
            session.commit()
            self.assertIsNotNone(inserted)

    def test_try_insert_exist(self):
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            instance = self._insert(session, instance)
            inserted = self.dao.try_insert(session, instance)
            self.assertIsNone(inserted)

    def test_get_exist(self):
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            inserted = self._insert(session, instance)
            got = self.dao.get(session, instance)
            self.assertIsNotNone(got)

    def test_get_unexist(self):
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            got = self.dao.get(session, instance)
            self.assertIsNone(got)

    def test_update_exist(self):
        NV = Verify.HTTPS
        instance = TBProxy(protocol=Protocol.HTTP, ip='127.0.0.1', port=3336,
                           verify=Verify.HTTP, anonymous=Anonymous.HIGH)
        with Session() as session:
            inserted = self._insert(session, instance)
            inserted.verify = NV
            self.dao.update(session, instance)
            session.commit()
            updated = session.get(TBProxy, inserted.id)
            self.assertIsNotNone(updated)
