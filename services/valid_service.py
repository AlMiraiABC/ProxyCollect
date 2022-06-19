import asyncio
import time
from asyncio import Queue
from multiprocessing import Event
from typing import Callable

from aiohttp import ClientSession
from al_utils.logger import Logger
from db.dbutil import DbUtil
from db.model import StoredProxy
from util.valid import Valid

logger = Logger(__file__).logger


class ValidService:
    def __init__(self, patch: int = 500, semaphore: int = 50):
        self.patch = patch if patch >= 50 else 500
        self.semaphore = semaphore if semaphore > 10 else 50
        self._cursor: int = 0
        """
        Row number.
        `-1`: finished.
        """
        self._db = DbUtil()
        self._valid = Valid()
        self._stop = Event()
        self._queue: Queue[StoredProxy] = Queue(patch*1.2)

    async def get_patch(self) -> list[StoredProxy]:
        """Get next patch proxies."""
        proxies = await self._db.gets(limit=self.patch, offset=self._cursor)
        if not proxies:
            self._cursor = -1
            logger.debug(f'No more proxies.')
        else:
            self._cursor += len(proxies)
            logger.debug(f'Get {len(proxies)} proxies from {self._cursor}.')
        return proxies

    async def update(self, session: ClientSession, proxy: StoredProxy):
        """Valid and update :param:`proxy`"""
        speed, anonymous = await self._valid.async_req(proxy, session=session)

        def cb(i: StoredProxy):
            i.anonymous = anonymous
            i.speed = speed
            return i
        ret = await self._db._update(proxy, cb)
        if not ret:
            logger.warning(f'Update proxy failed from {proxy} to '
                           f'{{anonymous: {anonymous}, speed: {speed}}}')
        return ret

    async def valid_proxies(self):
        """
        Get proxies from queue and valid it.

        Updated proxy will put in `rqueue`.
        """
        logger.debug("Start valid proxies.")
        updated: list[StoredProxy] = []
        async with ClientSession() as session:
            async with asyncio.Semaphore(self.semaphore):
                while not self._queue.empty() and not self._stop.is_set():
                    proxy = await self._queue.get()
                    updated.append(await self.update(session, proxy))
        logger.debug(f"Valid proxies finished. "
                     f"Updated {len(updated)} proxies.")
        return updated

    async def run_patch(self):
        """
        Run one patch.

        :return: Updated proxies. The item will be None if update it failed.
        """
        proxies = await self.get_patch()
        b = self._queue.qsize()
        for proxy in proxies:
            await self._queue.put(proxy)
        logger.debug(
            f'Put {len(proxies)} proxies from {b} to {self._queue.qsize()}.')
        return self.valid_proxies()

    async def run(self, patch_cb: Callable[[list[StoredProxy]], None] = None):
        """
        Start or continue to run valid service.

        Valid all proxies in one ioloop. This is IO bound tasks and multiprocessing will not
        imporve efficiency.
        """
        patch_cb = patch_cb or (lambda *_: None)
        if self._cursor < 0:
            raise RuntimeError('Service already stopped.')
        logger.info(f"Running valid service with {self.max_workers} workers.")
        count, fails, timeouts = 0, 0, 0
        self._stop.clear()
        while self._cursor >= 0 and not self._stop.is_set():
            logger.info(f"Get patch from {self._cursor}.")
            start_time = time.time()
            results = await self.run_patch()
            logger.info(f"The patch {self._cursor}-{self._cursor+self.patch} finished "
                        f"in {time.time()-start_time} seconds.")
            c, f, t = self._count(results)
            logger.info(f"The The patch {self._cursor}-{self._cursor+self.patch} valid {c} proxies, "
                        f"{f} failed and"
                        f"{t} timed out.")
            count += c
            fails += f
            timeouts += t
        self._stop.set()
        return count, fails, timeouts

    def _count(self, proxies: list[StoredProxy]):
        """
        Reduce updated proxies.

        :param updated: Updated proxies.
        :returns: len(proxies), len(proxy is None), len(proxy.speed is -1)
        """
        c = len(proxies)
        f = len([proxy for proxy in proxies if not proxy])
        t = len([proxy for proxy in proxies
                 if proxy and proxy.speed == -1])
        return c, f, t

    async def pause(self):
        """
        Pause runing. Exec :meth:`run` to continue.
        """
        self._stop.set()

    async def stop(self):
        """
        Stop running.
        """
        self._cursor = -1
        self._stop.set()
        while not self._queue.empty():
            await self._queue.get()
