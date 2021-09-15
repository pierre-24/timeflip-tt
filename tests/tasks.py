import flask

from tests import TestFlask

from timefliptt.blueprints.base_models import Category


class TestCategory(TestFlask):
    def setUp(self):
        super().setUp()

        self.category = Category.create('test1')
        self.db_session.add(self.category)
        self.db_session.commit()

        self.num_category = Category.query.count()

        self.login(self.admin_address, self.admin_password)

    def test_create_category(self):
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.post(flask.url_for('user.category-edit'), data={
            'category_id': -1,
            'category_name': name
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_category + 1, Category.query.count())

        c = Category.query.order_by(Category.id.desc()).first()
        self.assertEqual(c.name, name)
