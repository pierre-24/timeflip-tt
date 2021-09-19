import tempfile
from unittest import TestCase
import os

import flask
from sqlalchemy.orm import Session

from timefliptt.config import Config
from timefliptt.app import create_app, db
from timefliptt.blueprints.base_models import User


class FlaskTestCase(TestCase):

    def setUp(self):
        # config
        _, self.db_file = tempfile.mkstemp(suffix='.sqlite')

        config = Config()
        config.DB_FILE = self.db_file

        self.app = create_app(config)
        self.app.config['SERVER_NAME'] = '127.0.0.1:5000'
        self.app.config['DEBUG'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.app.config['WITH_TIMEFLIP'] = False

        # push context
        self.app_context = self.app.app_context()
        self.app_context.push()

        db.create_all()
        self.db_session: Session = db.session

        # create admin
        self.admin_name = 'admin'
        self.admin_address = ':'.join(['00'] * 6)
        self.admin_password = '0' * 6

        self.admin = User.create(self.admin_name, self.admin_address, self.admin_password)
        self.db_session.add(self.admin)
        self.db_session.commit()

        # create client
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        os.remove(self.db_file)
        self.app_context.pop()

    def login(self, address, password):
        """Login client."""

        self.client.post(flask.url_for('visitor.login'), data={
            'address': address,
            'password': password
        }, follow_redirects=False)

        response = self.client.get(flask.url_for('user.graphs'), follow_redirects=False)
        self.assertEqual(response.status_code, 200)

    def logout(self):
        """Logout client"""
        self.client.get(flask.url_for('visitor.logout'), follow_redirects=False)

        response = self.client.get(flask.url_for('user.graphs'), follow_redirects=False)
        self.assertEqual(response.status_code, 302)
