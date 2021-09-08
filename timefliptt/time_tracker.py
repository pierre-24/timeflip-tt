import yaml
import os

from pytimefliplib.async_client import DEFAULT_PASSWORD
from pytimefliplib.scripts import is_valid_addr


class SettingsError(Exception):
    pass


class Settings:

    DEFAULT_SETTINGS = {
        # database
        'database_path': 'timeflip-tt.sqlite3',

        # device
        'tf_address': '',
        'tf_password': DEFAULT_PASSWORD
    }

    def __init__(self):
        self.current_settings = self.DEFAULT_SETTINGS.copy()

    def from_file(self, fp):
        """Load settings

        :param fp: file in read mode
        """
        settings = yaml.load(fp, yaml.CLoader)

        for key, val in settings.items():
            if key in self.current_settings:
                self.current_settings[key] = val

        self._check()

    def _check(self):
        """Check consistency of the data. Raises `SettingsError` if anything is wrong.
        """

        # Database
        if not os.path.exists(self['database_path']):
            raise SettingsError('invalid `database_path`, {} does not exists'.format(self['database_path']))

        # TimeFlip
        if not is_valid_addr(self['tf_address']):
            raise SettingsError('`tf_address: {}` is not a valid address'.format(self['tf_address']))

        if len(self['tf_password']) != 6:
            raise SettingsError('`tf_password` must be 6 letter long')

    def dump(self, fp):
        """Dump settings

        :param fp: file in write mode
        """
        yaml.dump(self.current_settings, fp, yaml.CDumper)

    def __getitem__(self, item):
        return self.current_settings[item]


class TimeTrackerError(Exception):
    pass


class TimeTracker:
    def __init__(self, settings: Settings):
        self.settings = settings
