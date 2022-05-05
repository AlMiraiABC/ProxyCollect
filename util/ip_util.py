import re

class IpUtil:
    @staticmethod
    def is_formed_ipv4(ip:str, pattern: str = None):
        """
        Verify :param:`ip` whether formed.

        :param ip: Ipv4 address.
        :param pattern: Specified regex pattern.
        :return: True if formed, otherwise False.

        Ref
        --------------
        https://ihateregex.io/expr/ip/
        """
        if not ip:
            return False
        p = re.compile(
            pattern or r'^(\b25[0-5]|\b2[0-4][0-9]|\b[01]?[0-9][0-9]?)(\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}$')
        return p.match(ip.strip()) is not None
