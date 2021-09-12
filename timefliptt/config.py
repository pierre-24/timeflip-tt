import yaml

from pytimefliplib.async_client import DEFAULT_PASSWORD


class ConfigError(Exception):
    pass


class Config:
    """Custom app config
    """

    # TimeFlip
    TIMEFLIP = {
        'address': '',
        'password': DEFAULT_PASSWORD
    }

    # App info
    APP_INFO = {
        'app_name': 'TimeFlip TimeTracker'
    }

    def __init__(self):
        pass

    def from_file(self, fp):
        """Read config from a YAML file
        """

        data = yaml.load(fp, yaml.CLoader)

        for key, val in data.items():
            if hasattr(self, key):
                if type(val) is dict:
                    getattr(self, key).update(**val)
                else:
                    setattr(self, key, val)
            elif key == key.upper():  # all uppercase keys are also accepted
                setattr(self, key, val)

    @staticmethod
    def _is_valid_mac(addr: str) -> bool:
        """Check if input is a valid MAC address
        """

        seq = addr.split(':')
        if len(seq) != 6:
            return False

        try:
            data = [int(x, base=16) for x in seq]
        except ValueError:
            return False

        return all(0 <= x < 256 for x in data)

    def _check(self):
        """Check data consistency
        """

        # TimeFlip
        if self.TIMEFLIP['address']:
            raise ConfigError('you forgot to set TimeFlip address!')

        if not self._is_valid_mac(self.TIMEFLIP['address']):
            raise ConfigError('{} is not a valid MAC address'.format(self.TIMEFLIP['address']))

        if len(self.TIMEFLIP['password']) != 6:
            raise ConfigError('Password must be 6 character long!')
