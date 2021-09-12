import argparse

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy

import timefliptt
from timefliptt.config import Config

db = SQLAlchemy()


def create_app(args: argparse.Namespace) -> Flask:
    app = Flask(__name__)

    # config
    config = Config()

    if args.settings:
        config.from_file(args.settings)

    app.config.from_object(config)

    # module
    Bootstrap().init_app(app)
    db.init_app(app)

    # urls
    from timefliptt.views.visitor import blueprint
    app.register_blueprint(blueprint)

    from timefliptt.views.api import blueprint
    app.register_blueprint(blueprint)

    return app


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=timefliptt.__doc__)
    parser.add_argument('-v', '--version', action='version', version='%(prog)s ' + timefliptt.__version__)

    parser.add_argument('-i', '--settings', help='Settings', type=argparse.FileType('r'))

    parser.add_argument('-I', '--init', action='store_true', help='Initialize the application')

    return parser


def init_app():
    """Initialize the app
    """

    from timefliptt.models import Category

    db.create_all()

    dummy_cat = Category.create('Dummy')
    db.session.add(dummy_cat)
    db.session.commit()


def main():
    # get args
    args = get_arguments_parser().parse_args()

    app = create_app(args)

    if not args.init:  # run webserver
        app.run()
    else:  # init app
        with app.app_context():
            init_app()


if __name__ == '__main__':
    main()
