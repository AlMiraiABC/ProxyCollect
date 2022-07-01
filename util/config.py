from typing import Dict, TypedDict

from util.config_util import ConfigUtil
from util.ip import PublicIP
from al_utils.async_util import run_async


class RDBConfig:
    """
    Configs for :class:`db.rdb.rdb_dbutil.RDBUtil`

    Ref
    --------------
    https://docs.sqlalchemy.org/en/14/core/engines.html?highlight=create_engine#
    """
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'db.rdb.{k}', f'_DB_RDB_{k.upper()}', d)

    ENGINE: str = get('engine', 'mysql+pymysql')
    """RDB database driver"""
    USERNAME: str = get('username', 'root')
    """RDB login username."""
    PASSWORD: str = get('password', '')
    """RDB login password."""
    HOST: str = get('host', 'localhost')
    """RDB host ip address."""
    PORT: str = str(get('port', '3306'))
    """RDB connect port."""
    DB: str = get('db', 'proxy_ip')
    """Database name."""
    CHARSET: str = get('charset', 'utf8mb4')
    """Charset in connect."""
    URL: str = get(
        'url',
        f'{ENGINE}://{USERNAME}:{PASSWORD}@{HOST}:{PORT}/{DB}?charset={CHARSET}'
    )
    """Connect url."""
    EXTRA: Dict[str, any] = ConfigUtil().get_key(f'db.rdb.extra', default={})
    """
    Other parameters.

    NOTE:
    --------
    Environment variables are not supported.

    See:
    ---------
    https://docs.sqlalchemy.org/en/14/core/engines.html?highlight=create_engine#sqlalchemy.create_engine.params
    """


class DBConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'db.{k}', f'_DB_{k.upper()}', d)

    TYPE: str = get('type', 'rdb')
    """Database type."""
    RDB = RDBConfig


class ValidConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'valid.{k}', f'_VALID_{k.upper()}', d)

    PUBLIC_IP: str = get('pubip', run_async(PublicIP.public_ip()))
    """Public ip address of host."""
    TIMEOUT: float = float(get('timeout', 5))
    """Time seconds to wait for connection."""
    SEMAPHORE: int = int(get('semaphore', 50))
    """The maximum number of concurrent."""
    PATCH: int = int(get('patch', 500))
    """Number of each epoch."""


class ScoreConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'score.{k}', f'_SCORE_{k.upper()}', d)
    INIT: int = int(get('init', 20))
    """Default score."""
    INCREASE: int = int(get('increase', 1))
    """Increase step if valid successfully."""
    DECREASE: int = int(get('decrease', 1))
    """Decrease step if valid failed."""
    THRESHOLD: int = int(get('threshold', 0))
    """Set proxy unavailable if under threshold."""
    DELETE: bool = False if get('delete', False) in [
        'false', 'False', 'f', 'F', '0', 0, False, None] else True
    """Whether delete it if score under the `THRESHOLD`"""
    CEILING: int = int(get('ceiling', 50))
    """The maximum score value."""
    NADIR: int = int(get('nadir', -20))
    """The minimum score value."""


class CrawlsCrawlerConfig(TypedDict):
    """Config of crawls.crawlers"""
    callable: str
    args: list
    kwargs: dict[str, any]


class CrawlsConfig:
    """
    Crawls configs.

    NOTE:
    Environment variables are not supported.
    """
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'crawl.{k}', None, d)

    CRAWLERS: list[CrawlsCrawlerConfig] = get('crawlers', [])
    """
    Configured crawlers.
    """
    SEMAPHORE: int = int(get('semaphore', 10))
    """The maximum number of concurrent."""


class QueryConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'query.{k}', f'_QUERY_{k.upper()}', d)

    MAX_PS: int = int(get('max_limit', 100))
    """Maximum total number of queried proxies in one page."""
    BACKFILL: bool = bool(get('backfill', False))
    """
    Whether update proxy when check in query.

    If True, the dbuser must have update privilege.
    """
    DEFAULT_PS:int = int(get('default_ps',20))
    """Default page size. The default count number of proxies in one page."""
