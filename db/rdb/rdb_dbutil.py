from config import RDBConfig
from db.base_dbutil import BaseDbUtil
from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from db.rdb.model import TBProxy
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker


class RDBDbUtil(BaseDbUtil):
    def __init__(self, url: str = '', **kwargs):
        self.engine = create_engine(url or RDBConfig.URL, pool_size=5, max_overflow=3,
                                    echo=True, echo_pool=True, **(kwargs or RDBConfig.EXTRA))
        self.Session = sessionmaker(self.engine)

    async def try_insert(self, proxy: Proxy) -> StoredProxy | None:
        if proxy is None:
            return
        instance = self.to_tbproxy(proxy)
        with self.Session() as session:
            stored: TBProxy | None = session.execute(
                select(TBProxy)
                .where(TBProxy.protocol == proxy.protocol)
                .where(TBProxy.ip == proxy.ip)
                .where(TBProxy.port == proxy.port)
                .where(TBProxy.verify == proxy.verify)
            ).first()
            if stored:
                return None
            session.add(instance)
            session.commit()
            return self.to_storedproxy(instance)

    async def increase_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        pass

    async def decrease_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        pass

    async def update_speed(self, proxy: StoredProxy, new_speed: float) -> StoredProxy | None:
        pass

    async def gets(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None) -> list[StoredProxy]:
        pass

    def to_storedproxy(self, proxy: TBProxy) -> StoredProxy | None:
        if proxy is None:
            return None
        return StoredProxy(proxy.id, proxy.protocol, proxy.ip, proxy.port,
                           proxy.verify, proxy.score, proxy.anonymous,
                           proxy.domestic, proxy.address, proxy.speed)

    def to_tbproxy(self, proxy: Proxy) -> TBProxy | None:
        if proxy is None:
            return None
        return TBProxy(protocol=proxy.protocol, ip=proxy.ip, port=proxy.port,
                       verify=proxy.verify, anonymous=proxy.anonymous,
                       domestic=proxy.domestic, address=proxy.address, speed=0)
