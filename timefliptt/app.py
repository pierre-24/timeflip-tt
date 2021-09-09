import argparse
import yaml

from flask import Flask, make_response, Response
from flask.views import MethodView

from pytimefliplib.async_client import DEFAULT_PASSWORD, AsyncClient, TimeFlipRuntimeError

import timefliptt
from timefliptt.timeflip import run_coroutine_on_timeflip, CoroutineError


class ConfigError(Exception):
    pass


class Config:
    """Custom Flask config
    """

    # TimeFlip
    TIMEFLIP = {
        'address': '',
        'password': DEFAULT_PASSWORD
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


class Index(MethodView):
    @staticmethod
    async def get_facet(client: AsyncClient):
        return client.current_facet_value

    async def get(self) -> Response:
        try:
            facet = await run_coroutine_on_timeflip(self.get_facet)
            return make_response('current facet is {}'.format(facet), 200)
        except (CoroutineError, TimeFlipRuntimeError) as e:
            return make_response('Error while getting facet: {}'.format(e), 200)


def create_app(args: argparse.Namespace) -> Flask:
    app = Flask(__name__)

    # config
    config = Config()
    config.from_file(args.settings)
    app.config.from_object(config)

    # urls
    app.add_url_rule('/', view_func=Index.as_view('index'))

    return app


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=timefliptt.__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + timefliptt.__version__)

    parser.add_argument('-i', '--settings', help='Settings', default='config.yml', type=argparse.FileType('r'))

    return parser


def main():
    # get args
    args = get_arguments_parser().parse_args()

    # run webserver
    app = create_app(args)
    app.run()


if __name__ == '__main__':
    main()
