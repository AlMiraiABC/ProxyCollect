from typing import Any, Dict

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
    USERNAME: str = get('username', 'root')
    PASSWORD: str = get('password', '')
    HOST: str = get('host', 'localhost')
    PORT: str = str(get('port', '3306'))
    DB: str = get('db', 'proxy_ip')  # database name
    CHARSET: str = get('charset', 'utf8mb4')
    URL: str = get('url', f'{ENGINE}://{USERNAME}:{PASSWORD}@'
                   f'{HOST}:{PORT}/{DB}?charset={CHARSET}')
    # other parameters
    # see more: https://docs.sqlalchemy.org/en/14/core/engines.html?highlight=create_engine#sqlalchemy.create_engine.params
    EXTRA: Dict[str, Any] = get('extra', {})


class DBConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'db.{k}', f'_DB_{k.upper()}', d)

    TYPE: str = get('type', 'rdb')
    RDB = RDBConfig


class ValidConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'valid.{k}', f'_VALID_{k.upper()}', d)

    PUBLIC_IP: str = get('pubip', PublicIP.public_ip())
    TIMEOUT: float = get('timeout', 5)
