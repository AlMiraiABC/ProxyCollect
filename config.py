from typing import Dict, TypedDict

from util.config_util import ConfigUtil
from util.ip import PublicIP


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
    EXTRA: Dict[str, any] = get('extra', {})
    """
    Other parameters

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

    PUBLIC_IP: str = get('pubip', PublicIP.public_ip())
    """Public ip address of host."""
    TIMEOUT: float = float(get('timeout', 5))
    """Time seconds to wait for connection."""


class CrawlDetailConfig(TypedDict):
    """The detail config of each type of crawl."""
    headers: dict[str, str]
    """Request headers."""
    semaphore: int
    """The maximum number of concurrent."""
    timeout: int
    """Time seconds to wait for connection."""


class CrawlConfig:
    """Crawls common configs. Priority lower than :class:`CrawlDetailConfig`"""
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'valid.{k}', f'_CRAWL_{k.upper()}', d)

    def DETAIL(k: CrawlDetailConfig, d: CrawlDetailConfig):
        """Get type of :param:`k`'s detail config."""
        return CrawlConfig.get(k, d)
    HEADERS: dict[str, str] = get('headers', {})
    """Common headers."""
    SEMAPHORE: int = int(get('semaphore', 10))
    """The maximum number of concurrent."""
    TIMEOUT: int = int(get('timeout', 10))
    """Time seconds to wait for connection."""
