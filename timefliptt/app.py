import argparse

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager

import timefliptt
from timefliptt.config import Config

db = SQLAlchemy()
login_manager = LoginManager()


@login_manager.user_loader
def load_user(user_id):
    from timefliptt.blueprints.base_models import User
    return User.query.get(user_id)


def create_app(config: Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config)

    # module
    Bootstrap().init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'visitor.login'

    # urls
    from timefliptt.blueprints.visitor.views import blueprint
    app.register_blueprint(blueprint)

    from timefliptt.blueprints.user.views import blueprint
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


def main():
    # get args
    args = get_arguments_parser().parse_args()

    # configure
    config = Config()
    if args.settings:
        config.from_file(args.settings)

    # create app
    app = create_app(config)

    if not args.init:  # run webserver
        app.run()
    else:  # init app
        with app.app_context():
            init_app()


if __name__ == '__main__':
    main()
