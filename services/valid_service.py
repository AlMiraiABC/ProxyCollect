import asyncio
import time
from asyncio import AbstractEventLoop, Queue, Semaphore
from multiprocessing import Event

from aiohttp import ClientSession
from al_utils.logger import Logger
from db.dbutil import DbUtil
from db.model import StoredProxy
from util.valid import Valid

logger = Logger(__file__).logger


class ValidService:
    def __init__(self, patch: int = 500, semaphore: int = 50, loop: AbstractEventLoop = None):
        self.patch = patch if patch > 50 else 500
        self.semaphore = semaphore if semaphore > 10 else 50
        self._cursor: int = 0
        """
        Row number.
        `-1`: finished.
        """
        self._db = DbUtil()
        self._valid = Valid()
        self._stop = Event()
        self._queue: Queue[StoredProxy] = Queue(patch*1.2, loop=loop)

    async def get_patch(self) -> list[StoredProxy]:
        """Get next patch proxies."""
        proxies = await self._db.gets(limit=self.patch, offset=self._cursor)
        if not proxies:
            self._cursor = -1
        self._cursor += self.patch
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

    async def valid_proxies(self, proxies: list[StoredProxy]):
        ret: list[StoredProxy] = []
        async with ClientSession() as session:
            async with asyncio.Semaphore(self.semaphore):
                for proxy in proxies:
                    ret.append(await self.update(session, proxy))
        return ret

    async def run_patch(self) -> list[StoredProxy]:
        """
        Run one patch.

        :return: Updated proxies. The item will be None if update it failed.
        """
        proxies = await self.get_patch()
        for proxy in proxies:
            await self._queue.put(proxy)
        ret = []
        async with ClientSession() as session:
            async with Semaphore(self.semaphore):
                while not self._queue.empty() and not self._stop.is_set():
                    proxy = await self._queue.get()
                    ret.append(self.update(session, proxy))
        return ret

    async def run(self):
        """
        Start or continue to run valid service.

        Valid all proxies in one ioloop. This is IO bound tasks and multiprocessing will not
        imporve efficiency.
        """
        if self._cursor < 0:
            raise RuntimeError('Service already stopped.')
        logger.info(f"Running valid service with {self.max_workers} workers.")
        self._stop.clear()
        while self._cursor >= 0 and not self._stop.is_set():
            logger.info(f"Get patch from {self._cursor}.")
            start_time = time.time()
            results = await self.run_patch()
            logger.info(f"The patch {self._cursor}-{self._cursor+self.patch} finished "
                        f"in {time.time()-start_time} seconds.")
            count = len(results)
            fails = [result for result in results if not result]
            timeouts = [result for result in results
                        if result and result.speed == -1]
            logger.info(f"The The patch {self._cursor}-{self._cursor+self.patch} valid {count} proxies, "
                        f"{len(fails)} failed and"
                        f"{len(timeouts)} timed out.")

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
