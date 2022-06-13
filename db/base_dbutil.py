from abc import ABC, abstractmethod
from typing import List, Tuple

from db.model import Anonymous, Protocol, Proxy, StoredProxy, Verify


class BaseDbUtil(ABC):
    @abstractmethod
    async def try_insert(self, proxy: Proxy) -> StoredProxy | None:
        """
        Try to insert a :param:`proxy` into the database.

        :param proxy: Proxy
        :returns: Inserted proxy if not exists, otherwise None.
        """
        pass

    @abstractmethod
    async def increase_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        """
        Increase the score of :param:`proxy`.

        :param proxy: Proxy stored in database.
        :param step: Step to increment the score.
        :returns: Updated proxy if successfully, otherwise None.
        """
        pass

    @abstractmethod
    async def decrease_score(self, proxy: StoredProxy, step=1) -> StoredProxy | None:
        """
        Decrease the score of :param:`proxy`.

        :param proxy: Proxy stored in database.
        :param step: Step to decrement the score.
        :returns: Updated proxy if successfully, otherwise None.
        """
        pass

    @abstractmethod
    async def update_speed(self, proxy: StoredProxy, new_speed: float) -> StoredProxy | None:
        """
        Update the speed of :param:`proxy` to :param:`new_speed`.

        :param proxy: Proxy stored in the database.
        :param new_speed: New speed value.
        :returns: Updated proxy if successfully, otherwise None.
        """
        pass

    @abstractmethod
    async def gets(self, protocol: Protocol = None, ip: str = None, port: int = None, verify: Verify = None, anonymous: Anonymous = None, domestic: bool = None,
                   limit: int = 100, offset: int = 0) -> List[StoredProxy]:
        """
        Get proxies by given conditions.
        """
        pass
