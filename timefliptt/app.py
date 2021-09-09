import argparse

from flask import Flask

import timefliptt
from timefliptt.config import Config


def create_app(args: argparse.Namespace) -> Flask:
    app = Flask(__name__)

    # config
    config = Config()
    config.from_file(args.settings)
    app.config.from_object(config)

    # urls
    from views_visitor import blueprint
    app.register_blueprint(blueprint)

    from views_api import blueprint
    app.register_blueprint(blueprint)

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
