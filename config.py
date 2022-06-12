from typing import Any, Dict

from util.config_util import ConfigUtil


class RDBConfig:
    """
    Configs for :class:`db.rdb.rdb_dbutil.RDBUtil`

    Ref
    --------------
    https://docs.sqlalchemy.org/en/14/core/engines.html?highlight=create_engine#
    """
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'db.rdb.{k}', f'_DB_RDB_{k.upper()}', d)

    ENGINE = get('engine', 'mysql+pymysql')
    USERNAME = get('username', 'root')
    PASSWORD = get('password', '')
    HOST = get('host', 'localhost')
    PORT = str(get('port', '3306'))
    DB = get('db', 'proxy_ip')
    CHARSET = get('charset', 'utf8mb4')
    URL = get('url', f'{ENGINE}://{USERNAME}:{PASSWORD}@'
              f'{HOST}:{PORT}/{DB}?charset={CHARSET}')
    # other parameters
    # see more: https://docs.sqlalchemy.org/en/14/core/engines.html?highlight=create_engine#sqlalchemy.create_engine.params
    EXTRA: Dict[str, Any] = get('extra', {})


class DBConfig:
    def get(k: str, d: any):
        return ConfigUtil().get_key(f'db.{k}', f'_DB_{k.upper()}', d)

    TYPE = get('type', 'rdb')
    RDB = RDBConfig
