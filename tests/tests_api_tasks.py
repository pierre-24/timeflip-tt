import flask

from tests import FlaskTestCase

from timefliptt.blueprints.base_models import Category, Task


class CategoryTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.category_1 = Category.create('test1')
        self.db_session.add(self.category_1)
        self.category_2 = Category.create('test2')
        self.db_session.add(self.category_2)
        self.db_session.commit()

        self.task_1_1 = Task.create('test1', self.category_1, '#ffffff')
        self.db_session.add(self.task_1_1)
        self.task_2_1 = Task.create('test2', self.category_2, '#ffffff')
        self.db_session.add(self.task_2_1)
        self.db_session.commit()

        self.num_category = Category.query.count()
        self.num_task = Task.query.count()

    def test_get_categories_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        response = self.client.get(flask.url_for('api.categories'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('categories', data)
        self.assertEqual(len(data['categories']), self.num_category)

    def test_create_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.post(flask.url_for('api.categories'), json={
            'name': name
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data['name'], name)

        self.assertEqual(self.num_category + 1, Category.query.count())

        c = Category.query.get(data['id'])
        self.assertEqual(c.name, name)
