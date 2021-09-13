import yaml
import os

import timefliptt


class ConfigError(Exception):
    pass


class Config:
    """Custom app config
    """

    # App config
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_FILE = 'timeflip-tt.sqlite'

    # App info
    APP_INFO = {
        'app_name': 'TimeFlip TimeTracker',
        'app_author': timefliptt.__author__,
        'app_author_url': 'https://pierrebeaujean.net',
        'app_version': timefliptt.__version__,
        'app_repo_url': 'https://github.com/pierre-24/timeflip-tt/'
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

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return 'sqlite:///{}'.format(os.path.join(os.path.abspath(self.DB_FILE)))
