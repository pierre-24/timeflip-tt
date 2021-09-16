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

        self.login(self.admin_address, self.admin_password)

    def test_create_category_ok(self):
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

    def test_create_category_not_logged_ko(self):
        self.logout()
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.post(flask.url_for('user.category-edit'), data={
            'category_id': -1,
            'category_name': name
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_category, Category.query.count())

    def test_modify_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.post(flask.url_for('user.category-edit'), data={
            'category_id': self.category_1.id,
            'category_name': name
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_category, Category.query.count())

        c = Category.query.get(self.category_1.id)
        self.assertEqual(c.name, name)

    def test_modify_category_not_logged_ko(self):
        self.logout()
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.post(flask.url_for('user.category-edit'), data={
            'category_id': self.category_1.id,
            'category_name': name
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        self.assertEqual(self.num_category, Category.query.count())

        c = Category.query.get(self.category_1.id)
        self.assertNotEqual(c.name, name)

    def test_delete_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.post(flask.url_for('user.category-delete'), data={
            'category_delete_id': self.category_1.id,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # delete category and its task
        self.assertEqual(self.num_category - 1, Category.query.count())
        self.assertIsNone(Category.query.get(self.category_1.id))
        self.assertEqual(self.num_task - 1, Task.query.count())
        self.assertIsNone(Task.query.get(self.task_1_1.id))

    def test_delete_category_not_logged_ko(self):
        self.logout()

        self.assertEqual(self.num_category, Category.query.count())
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.post(flask.url_for('user.category-delete'), data={
            'category_delete_id': self.category_1.id,
        }, follow_redirects=False)
        self.assertEqual(response.status_code, 302)

        # nothing deleted
        self.assertEqual(self.num_category, Category.query.count())
        self.assertIsNotNone(Category.query.get(self.category_1.id))

        self.assertEqual(self.num_task, Task.query.count())
        self.assertIsNotNone(Task.query.get(self.task_1_1.id))
