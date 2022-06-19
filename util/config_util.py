import json
import os

from al_utils.singleton import Singleton


class ConfigUtil(Singleton):
    _PREFIX = 'PC'

    def __init__(self, config_path: str = None) -> None:
        self.config_path = config_path or \
            os.getenv(f'{self._PREFIX}_CONFIG_FILE') or \
            './config.json'
        if not os.path.exists(self.config_path):
            self.config = {}
        else:
            with open(self.config_path, 'r') as config_file:
                self.config: dict = json.load(config_file)

    def get_key(self, key: str, env_key: str = None, default=None):
        """
        Get value from config.

        :param key: The key. Format as a.b.c.d
        :param env_key: The system environment key.
        :param default: The default value.
        :return: env > config > default
        """
        env_var = os.getenv(f"{self._PREFIX}{env_key}") if env_key else None
        return env_var or self._get(self.config, key.split('.')) or default

    def _get(self, d: dict, keys: list[str]):
        if len(keys) == 1:
            return d.get(keys[0])
        v = d.get(keys[0])
        if isinstance(v, dict):
            return self._get(v, keys[1:])
