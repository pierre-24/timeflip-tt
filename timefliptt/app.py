import argparse
import atexit

import flask
from flask_sqlalchemy import SQLAlchemy

import timefliptt
from timefliptt.config import Config
from timefliptt.timeflip import daemon_start, daemon_stop, soft_connect


db = SQLAlchemy()


def create_app(config: Config) -> flask.Flask:
    app = flask.Flask(__name__)
    app.config.from_object(config)

    # modules
    db.init_app(app)

    # urls
    from timefliptt.blueprints.visitors.views import blueprint
    app.register_blueprint(blueprint)

    from timefliptt.blueprints.api.views import blueprint
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

    db.create_all()


def stop_app():
    daemon_stop()


def main():
    # get args
    args = get_arguments_parser().parse_args()

    # configure
    config = Config()
    if args.settings:
        config.from_file(args.settings)

    # create app
    app = create_app(config)

    @app.before_first_request
    def setup_thread():
        atexit.register(stop_app)
        daemon_start()

        if 'address' in flask.session:
            soft_connect(flask.session['address'], flask.session.get('password', ''))

    if not args.init:  # run webserver
        app.run()
    else:  # init app
        with app.app_context():
            init_app()


if __name__ == '__main__':
    main()
