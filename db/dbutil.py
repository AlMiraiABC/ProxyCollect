from typing import Callable

from al_utils.logger import Logger
from al_utils.meta import merge_meta
from al_utils.singleton import Singleton
from util.config import DBConfig, RDBConfig
from util.score import Score

from db.base_dbutil import BaseDbUtil
from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from db.rdb.rdb_dbutil import RDBDbUtil

logger = Logger(__file__).logger


def default_update_cb(speed: float, anonymous: Anonymous):
    def cb(i: StoredProxy):
        i.anonymous = anonymous
        i.speed = speed
        i.score = Score.calc(i.speed, i.score)
        return i
    return cb


class DbUtil(merge_meta(BaseDbUtil, Singleton)):
    def __init__(self):
        self.db: BaseDbUtil
        match DBConfig.TYPE:
            case 'rdb':
                self.db = RDBDbUtil(RDBConfig.URL, **RDBConfig.EXTRA)
            case _:
                raise ValueError(f'Unsupported db type, got {DBConfig.TYPE}')

    def _any_falsy(*args: str) -> bool:
        """
        Determine whether at least one of :param:`args` is falsy.

        :returns: False if all :param:`args` are truthy."""
        for arg in args:
            if not arg:
                return True
        return False

    async def try_insert(self, proxy: Proxy) -> StoredProxy | None:
        if self._any_falsy(proxy.protocol, proxy.ip, proxy.port):
            raise ValueError(f"protocol, ip and port must be set, "
                             f"but got {proxy}")
        if not proxy.verify:
            match proxy.protocol:
                case Protocol.HTTP:
                    verify = Verify.HTTP
                case Protocol.HTTPS:
                    verify = Verify.HTTPS
                case Protocol.SOCKS4:
                    verify = Verify.TCP
                case Protocol.SOCKS5:
                    verify = Verify.UDP
            proxy.verify = verify
            logger.debug(f"set verify to {verify}")
        if not proxy.anonymous:
            proxy.anonymous = Anonymous.TRANSPARENT
            logger.debug(f"set anonymous to {proxy.anonymous}")
        return await self.db.try_insert(proxy)

    async def _update(self, proxy: StoredProxy, cb: Callable[[StoredProxy], StoredProxy]) -> StoredProxy | None:
        if not proxy.id:
            raise ValueError(f"id must be set, "
                             f"but got {proxy}")
        return await self.db._update(proxy, cb)

    async def increase_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        if not proxy.id:
            raise ValueError(f"id must be set, "
                             f"but got {proxy}")
        if step < 1:
            raise ValueError(f"step must ≥ 1.")
        return await self.db.increase_score(proxy, step)

    async def decrease_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        if not proxy.id:
            raise ValueError(f"id must be set, "
                             f"but got {proxy}")
        if step < 1:
            raise ValueError(f"step must ≥ 1.")
        return await self.db.decrease_score(proxy, step)

    async def update_speed(self, proxy: StoredProxy, new_speed: float) -> StoredProxy | None:
        if not proxy.id:
            raise ValueError(f"id must be set, "
                             f"but got {proxy}")
        if new_speed <= 0 and new_speed != -1:
            raise ValueError(f"speed must > 0, or -1(timeout).")
        return await self.db.update_speed(proxy, new_speed)

    async def gets(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None,
                   limit: int = 100, offset: int = 0,  min_score: int = None, max_score: int = None, min_speed: float = None, max_speed: float = None) -> list[StoredProxy]:
        if not limit or limit <= 0:
            limit = 100
            logger.debug(f"set limit to {limit}")
        if not offset or offset < 0:
            offset = 0
            logger.debug(f"set offset to {offset}")
        if not self._check_min_max(min_score, max_score):
            logger.debug(f'score min {min_score} > max {max_score}.')
            return []
        if not self._check_min_max(min_speed, max_speed):
            logger.debug(f'speed min {min_score} > max {max_score}.')
            return []
        return await self.db.gets(protocol, ip, port, verify, anonymous, domestic, limit, offset, min_score, max_score, min_speed, max_speed)

    async def count(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None,
                    min_score: int = None, max_score: int = None, min_speed: float = None, max_speed: float = None) -> int:
        if not self._check_min_max(min_score, max_score):
            logger.debug(f'score min {min_score} > max {max_score}.')
            return []
        if not self._check_min_max(min_speed, max_speed):
            logger.debug(f'speed min {min_score} > max {max_score}.')
            return []
        return await self.db.count(protocol, ip, port, verify, anonymous, domestic, min_score, max_score, min_speed, max_speed)

    async def gets_random(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None,
                          limit: int = 100, min_score: int = None, max_score: int = None, min_speed: float = None, max_speed: float = None) -> list[StoredProxy]:
        if not limit or limit < 0:
            limit = 100
            logger.debug(f"set limit to {limit}")
        if not self._check_min_max(min_score, max_score):
            logger.debug(f'score min {min_score} > max {max_score}.')
            return []
        if not self._check_min_max(min_speed, max_speed):
            logger.debug(f'speed min {min_score} > max {max_score}.')
            return []
        return await self.db.gets_random(protocol, ip, port, verify, anonymous, domestic, limit, min_score, max_score, min_speed, max_speed)

    async def delete(self, proxy: StoredProxy):
        if not proxy:
            return
        return await self.db.delete(proxy)
