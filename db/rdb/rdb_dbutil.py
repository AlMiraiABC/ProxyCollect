from typing import Callable

from al_utils.logger import Logger
from db.base_dbutil import BaseDbUtil
from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from db.rdb.model import TBProxy
from sqlalchemy import create_engine, func
from sqlalchemy.orm import Session, sessionmaker

logger = Logger(__file__).logger


class RDBDbUtil(BaseDbUtil):
    def __init__(self, url: str = '', **kwargs):
        self.engine = create_engine(url, **kwargs)
        self.Session: Callable[[], Session] = sessionmaker(self.engine)
        self.dao = _RDBDAO()

    async def try_insert(self, proxy: Proxy) -> StoredProxy | None:
        if proxy is None:
            return
        with self.Session() as session:
            instance = self.to_tbproxy(proxy)
            inserted = self.dao.try_insert(session, instance)
            if not inserted:
                return None
            session.commit()
            logger.debug(f'inserted {inserted.id}.')
            return self.to_storedproxy(inserted)

    async def _update(self, proxy: StoredProxy, cb: Callable[[TBProxy], TBProxy]) -> StoredProxy | None:
        with self.Session() as session:
            instance = self.dao.get_by_id(session, proxy.id)
            if not instance:
                return None
            logger.debug(f'updating {instance.id} {instance}.')
            instance = cb(instance)
            updated = self.dao.insert_or_update(
                session, instance)  # cannot be none
            logger.debug(f'updated {updated.id} to {updated}.')
            session.commit()
            return self.to_storedproxy(updated)

    async def increase_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        def set_socre(i: TBProxy):
            i.score += step
            return i
        return await self._update(proxy, set_socre)

    async def decrease_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        def set_socre(i: TBProxy):
            i.score -= step
            return i
        return await self._update(proxy, set_socre)

    async def update_speed(self, proxy: StoredProxy, new_speed: float) -> StoredProxy | None:
        def set_socre(i: TBProxy):
            i.speed = new_speed
            return i
        return await self._update(proxy, set_socre)

    async def gets(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None,
                   limit: int = 100, offset: int = 0) -> list[StoredProxy]:
        if not limit or limit <= 0:
            logger.debug(f'set limit from {limit} to {100}.')
            limit = 100
        if not offset or offset < 0:
            logger.debug(f'set offset from {offset} to {0}.')
            offset = 0
        with self.Session() as session:
            query = self._gen_query(session, protocol, ip, port,
                                    verify, anonymous, domestic)
            results: list[TBProxy] = query.offset(offset).limit(limit).all()
            return [self.to_storedproxy(r) for r in results]

    async def count(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None) -> int:
        with self.Session() as session:
            query = self._gen_query(session, protocol, ip, port,
                                    verify, anonymous, domestic)
            result: int = query.count()
            return result

    async def gets_random(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None, limit: int = 100) -> list[StoredProxy]:
        with self.Session() as session:
            query = self._gen_query(session, protocol, ip, port,
                                    verify, anonymous, domestic)
            # https://docs.sqlalchemy.org/en/14/core/functions.html#sqlalchemy.sql.functions.random
            # https://stackoverflow.com/a/33583008
            results: list[TBProxy] = query.order_by(
                func.random()).limit(limit).all()
            return [self.to_storedproxy(r) for r in results]

    def _gen_query(self, session: Session, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None):
        query = session.query(TBProxy)
        if protocol:
            query = query.filter(TBProxy.protocol == protocol)
        if ip:
            query = query.filter(TBProxy.ip == ip)
        if port:
            query = query.filter(TBProxy.port == port)
        if verify:
            query = query.filter(TBProxy.verify == verify)
        if anonymous:
            query = query.filter(TBProxy.anonymous == anonymous)
        if domestic:
            query = query.filter(TBProxy.domestic == domestic)
        return query

    def to_storedproxy(self, proxy: TBProxy) -> StoredProxy | None:
        """Convert :class:`TBProxy` :param:`proxy` to :class:`StoredProxy`"""
        if proxy is None:
            return None
        return StoredProxy(proxy.id, proxy.protocol, proxy.ip, proxy.port,
                           proxy.verify, proxy.score, proxy.anonymous,
                           proxy.domestic, proxy.address, proxy.speed)

    def to_tbproxy(self, proxy: Proxy) -> TBProxy | None:
        """Convert :class:`Proxy` :param:`proxy` to :class:`TBProxy`"""
        if proxy is None:
            return None
        return TBProxy(protocol=proxy.protocol, ip=proxy.ip, port=proxy.port,
                       verify=proxy.verify, anonymous=proxy.anonymous,
                       domestic=proxy.domestic, address=proxy.address, speed=0)


class _RDBDAO:
    def get_by_id(self, session: Session, id: int) -> TBProxy | None:
        """Get proxy by id."""
        if id < 0:
            return None
        instance = session.get(TBProxy, id)
        return instance

    def try_insert(self, session: Session, instance: TBProxy) -> TBProxy | None:
        """
        Try to insert a proxy if not exist.

        :return: Inserted instance. Or None if already exists.
        NOTE: Need commit.
        """
        inserted = self.get(session, instance)
        if inserted:
            logger.debug(f'Proxy already exists {inserted.id}.')
            return None
        session.add(instance)
        logger.debug(f'Insert proxy {instance}.')
        return instance

    def get(self, session: Session, instance: TBProxy) -> TBProxy | None:
        """Get proxy by unique columns."""
        if not instance:
            return None
        uniq = ['protocol', 'ip', 'port', 'verify']
        query = session.query(TBProxy)
        for col in uniq:
            query = query.filter(getattr(TBProxy, col) ==
                                 getattr(instance, col))
        return query.first()

    def update(self, session: Session, instance: TBProxy) -> TBProxy | None:
        """Update proxy if exists."""
        if not self.get(session, instance):
            logger.debug(f'Proxy not exists {instance}.')
            return None
        logger.debug(f'Update proxy {instance}.')
        session.add(instance)
        logger.debug(f'Update proxy to {instance}.')
        return instance

    def insert_or_update(self, session: Session, instance: TBProxy) -> TBProxy | None:
        """
        Insert or update this instance.

        NOTE: Need commit.
        """
        if not instance:
            return None
        session.add(instance)
        return instance

    def delete(self, session: Session, instance: TBProxy):
        if not instance:
            return None
        session.delete(instance)
        logger.debug(f'Delete proxy {instance}.')

    def delete_by_id(self, session: Session, id: int):
        if id < 0:
            return
        inserted = session.get(id)
        if inserted:
            session.delete(inserted)
            logger.debug(f'Delete proxy {inserted}.')
            return
        logger.debug(f'Proxy not exists {id}.')
