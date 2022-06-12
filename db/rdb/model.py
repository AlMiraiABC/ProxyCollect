from enum import Enum
from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify
from sqlalchemy import (TIMESTAMP, Boolean, Column, DateTime, Float, Integer, SmallInteger, String,
                        TypeDecorator, func, text)
from sqlalchemy.ext.declarative import declarative_base


class IntEnum(TypeDecorator):
    """
    SQLAlchemy Enum type based on Integer indices.

    Ref
    ----------------
    [How to model enums backed by integers with sqlachemy?]
    (https://stackoverflow.com/questions/33612625/how-to-model-enums-backed-by-integers-with-sqlachemy#answer-41634765)

    E.g.
    --------------
    >>> class MyEnum(Enum):
    >>>     one = 1
    >>>     two = 2
    >>>     three = 3
    >>> from sqlalchemy import Column
    >>> column_name = Column('column_name', IntEnum(MyEnum))
    """
    impl = Integer

    def __init__(self, enum_type: Enum, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._enum_type = enum_type

    def process_bind_param(self, value: Enum, dialect):
        return value.value

    def process_result_value(self, value, dialect):
        return self._enum_type(value)


Base = declarative_base()


class _TBBaseClass():
    id = Column(Integer, primary_key=True, autoincrement=True, nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, server_default=func.now())
    updated_at = Column(TIMESTAMP, nullable=False,
                        server_default=func.now(), server_onupdate=func.now())


class TBProxy(_TBBaseClass, Base, StoredProxy):
    __tablename__ = 'proxy'
    protocol = Column("protocol", IntEnum(Protocol), nullable=False)
    ip = Column("ip", String, nullable=False)
    port = Column("port", SmallInteger, nullable=False)
    verify = Column("verify", IntEnum(Verify), nullable=False)
    anonymous = Column("anonymous", IntEnum(Anonymous), nullable=False)
    domestic = Column("domestic", Boolean,
                      server_default=text('1'), nullable=False)
    address = Column("address", String, nullable=True)
    speed = Column("speed", Float, server_default=text('0'), nullable=False)
    verify_time = Column("verify_time", DateTime,
                         server_default=func.now(), onupdate=func.now())
    score = Column("score", Integer, server_default=text('20'), nullable=False)


class _TBIdName(_TBBaseClass):
    name = Column("name", String, nullable=False, unique=True)
