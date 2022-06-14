import json

import aiohttp
from al_utils.alru import alru_cache


class PublicIP:
    """Utils to get public IP addresses of current host."""
    @staticmethod
    @alru_cache(maxsize=1)
    async def public_ip():
        """
        Get the public IP address.

        This method will try all ways until get response.

        :raise ConnectionError: All ways are failed.
        """
        fns = [
            PublicIP.public_ip_from_aws,
            PublicIP.public_ip_from_ifconfig,
            PublicIP.public_ip_from_httpbin,
            PublicIP.public_ip_from_16yun,
            PublicIP.public_ip_from_ipcn,
        ]
        for fn in fns:
            try:
                ip = await fn()
                if ip:
                    return ip
            except:
                continue
        raise ConnectionError('Cannot get public IP address.')

    @staticmethod
    async def public_ip_from_aws():
        url = "http://checkip.amazonaws.com/"
        return await PublicIP._get_content(url)

    @staticmethod
    async def public_ip_from_ifconfig():
        url = "https://ifconfig.me/ip"
        return await PublicIP._get_content(url)

    @staticmethod
    async def public_ip_from_httpbin():
        url = "https://httpbin.org/ip"
        text = await PublicIP._get_content(url)
        if text:
            data: dict[str, str] = json.loads(text)
            if data:
                return data.get('origin')

    @staticmethod
    async def public_ip_from_16yun():
        url = "http://current.ip.16yun.cn:802/"
        return await PublicIP._get_content(url)

    @staticmethod
    async def public_ip_from_ipcn():
        url = 'https://ip.cn/api/index?type=0'
        text = await PublicIP._get_content(url)
        if text:
            data: dict[str, str] = json.loads(text)
            if data:
                return data.get("ip")

    @staticmethod
    async def _get_content(url) -> str | None:
        """
        Send get request to :param:`url`.

        :return: Resposne text if status code is 200. Otherwise None
        """
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    # response.json() will check content type
                    # may return a json but content-type in header is html/text.
                    return (await response.text()).strip()
