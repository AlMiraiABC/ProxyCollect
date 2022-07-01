from db.dbutil import DbUtil, default_update_cb
from db.model import Anonymous, Protocol, Proxy, Verify
from util.ip import is_formed_ipv4
from util.valid import Valid
from al_utils.logger import Logger

logger = Logger(__file__).logger


class QueryService:
    def __init__(self, valid: Valid, max_page_size: int = 100, backfill: bool = False):
        """
        :param valid: Valid instance.
        :param max_page_size: Maximum count number of one page when query.
        :param backfill: Whether to update proxies when check.
        """
        self._db = DbUtil()
        self._valid = valid
        self._max_ps = max_page_size
        self._backfill = backfill

    async def get(self,
                  protocol: Protocol | str = None,
                  ip: str = None,
                  port: int = None,
                  verify: Verify | str = None,
                  anonymous: Anonymous | str = None,
                  domestic: bool = None,
                  limit: int = 1,
                  skip: int = 0,
                  min_score: int = 20,
                  max_score: int = None,
                  min_speed: int = 0,
                  max_speed: int = None) -> list[Proxy]:
        """
        Get proxies.
        """
        protocol, ip, port, verify, anonymous, domestic = self._verify_query_params(
            protocol, ip, port, verify, anonymous, domestic)
        if not limit or limit > self._max_ps:
            limit = self._max_ps
            logger.debug(f'limit is too large, set to {limit}.')
        if not limit or limit < 1:
            limit = 1
            logger.debug(f'limit is too small, set to {limit}.')
        if not skip or skip < 0:
            skip = 0
            logger.debug(f'set skip to {skip}')
        return await self._db.gets(protocol, ip, port, verify, anonymous, domestic, limit, skip,
                                   min_score, max_score, min_speed, max_speed)

    async def get_count(self,
                        protocol: Protocol | str = None,
                        ip: str = None,
                        port: int = None,
                        verify: Verify | str = None,
                        anonymous: Anonymous | str = None,
                        domestic: bool = None,
                        min_score: int = 20,
                        max_score: int = None,
                        min_speed: int = 0,
                        max_speed: int = None) -> int:
        """
        Get count of proxies.
        """
        protocol, ip, port, verify, anonymous, domestic = self._verify_query_params(
            protocol, ip, port, verify, anonymous, domestic)
        return await self._db.count(protocol, ip, port, verify, anonymous, domestic,
                                    min_score, max_score, min_speed, max_speed)

    async def get_random(self,
                         protocol: Protocol | str = None,
                         ip: str = None,
                         port: int = None,
                         verify: Verify | str = None,
                         anonymous: Anonymous | str = None,
                         domestic: bool = None,
                         count: int = 1,
                         min_score: int = 20,
                         max_score: int = None,
                         min_speed: int = 0,
                         max_speed: int = None) -> list[Proxy]:
        protocol, ip, port, verify, anonymous, domestic = self._verify_query_params(
            protocol, ip, port, verify, anonymous, domestic)
        if not count or count < 1:
            count = 1
            logger.debug(f'set count to {count}.')
        return await self._db.gets_random(
            protocol, ip, port, verify, anonymous, domestic, count,
            min_score, max_score, min_speed, max_speed)

    async def get_check(self,
                        protocol: Protocol | str = None,
                        ip: str = None,
                        port: int = None,
                        verify: Verify | str = None,
                        anonymous: Anonymous | str = None,
                        domestic: bool = None,
                        check_count: int = 1,
                        min_score: int = 20,
                        max_score: int = None,
                        min_speed: int = 0,
                        max_speed: int = None) -> Proxy | None:
        """
        Get a checked proxy.

        It will get :param:`check_count` proxies and return checked one.

        :param check_count: Maximum check times.
        :return: Checked proxy. None if all :param:`check_count` proxies are unavailable.
        """
        if not check_count or check_count < 1:
            check_count = 1
            logger.debug(f'set check_count to {check_count}.')
        proxies = await self.get_random(protocol, ip, port, verify, anonymous, domestic,
                                        check_count, min_score, max_score, min_speed, max_speed)
        for proxy in proxies:
            # TODO: 2022-06-19 support different check methods.
            speed, anon = await self._valid.async_valid(proxy)
            logger.debug(f'Proxy {proxy.id} speed: {speed} anonymous: {anon}')
            if self._backfill:
                await self._db._update(proxy, default_update_cb(speed, anon))
                logger.debug(
                    f'backfill {{id:{proxy.id}, speed: {speed}, anonymous: {anonymous.name}}}.')
            if speed > 0:
                if not anonymous:
                    return proxy
                if anon == anonymous:
                    return proxy

    def _verify_query_params(self, protocol: Protocol | str, ip: str, port: int, verify: Verify | str, anonymous: Anonymous | str, domestic: bool):
        """
        Verify query params.

        :raise KeyError: :param:`protocol`, :param:`verify` or :param:`anonymous` wrong value.
        :raise ValueError: :param:`ip` or :param:`port` is malformed.
        """
        if isinstance(protocol, str):
            protocol = Protocol[protocol]
        if isinstance(verify, str):
            verify = Verify[verify]
        if isinstance(anonymous, str):
            anonymous = Anonymous[anonymous]
        if port and (port < 0 or port > 65535):
            raise ValueError(
                f'port must be a positive integer, bug got {port}.')
        if ip and not is_formed_ipv4(ip):
            raise ValueError(f'Malformed IP address {ip}.')
        return protocol, ip, port, verify, anonymous, domestic
