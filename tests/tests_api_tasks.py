import flask

from tests import FlaskTestCase

from timefliptt.blueprints.base_models import Category, Task


class CategoriesTestCase(FlaskTestCase):
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

    def test_view_categories_ok(self):
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

    def test_view_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        response = self.client.get(flask.url_for('api.category', id=self.category_1.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data['id'], self.category_1.id)
        self.assertEqual(data['name'], self.category_1.name)

    def test_view_unknown_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        response = self.client.get(flask.url_for('api.category', id=-1))
        self.assertEqual(response.status_code, 404)

    def test_modify_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.put(flask.url_for('api.category', id=self.category_1.id), json={
            'name': name
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data['id'], self.category_1.id)
        self.assertEqual(data['name'], name)

        c = Category.query.get(data['id'])
        self.assertEqual(c.name, name)

    def test_modify_unknown_category_ko(self):
        self.assertEqual(self.num_category, Category.query.count())

        name = 'whatever'

        response = self.client.put(flask.url_for('api.category', id=-1), json={
            'name': name
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_category_ok(self):
        self.assertEqual(self.num_category, Category.query.count())

        response = self.client.delete(flask.url_for('api.category', id=self.category_1.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_category - 1, Category.query.count())
        self.assertIsNone(Category.query.get(self.category_1.id))

    def test_delete_unknown_category_ko(self):
        self.assertEqual(self.num_category, Category.query.count())

        response = self.client.delete(flask.url_for('api.category', id=-1))
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_category, Category.query.count())


class TasksTestCase(FlaskTestCase):
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

    def test_view_tasks_ok(self):
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.get(flask.url_for('api.tasks'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('tasks', data)
        self.assertEqual(len(data['tasks']), self.num_task)

    def test_create_task_ok(self):
        self.assertEqual(self.num_task, Task.query.count())

        name = 'whatever'
        color = '#ff0000'

        response = self.client.post(flask.url_for('api.category', id=self.category_1.id), json={
            'name': name,
            'color': color
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(name, data['name'])
        self.assertEqual(color, data['color'])

        self.assertEqual(self.num_task + 1, Task.query.count())

        t = Task.query.get(data['id'])
        self.assertEqual(name, t.name)
        self.assertEqual(color, t.color)
        self.assertEqual(self.category_1.id, t.category_id)

    def test_create_task_unknown_cat_ko(self):
        self.assertEqual(self.num_task, Task.query.count())

        name = 'whatever'
        color = '#ff0000'

        response = self.client.post(flask.url_for('api.category', id=-1), json={
            'name': name,
            'color': color
        })
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_task, Task.query.count())

    def test_view_task_ok(self):
        self.assertEqual(self.num_task, Task.query.count())
        t = self.task_1_1

        response = self.client.get(flask.url_for('api.task', id=t.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(data['id'], t.id)
        self.assertEqual(data['name'], t.name)
        self.assertEqual(data['color'], t.color)
        self.assertEqual(data['category'], t.category_id)

    def test_view_unknown_task_ok(self):
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.get(flask.url_for('api.task', id=-1))
        self.assertEqual(response.status_code, 404)

    def test_modify_task_ok(self):
        self.assertEqual(self.num_task, Task.query.count())

        name = 'whatever'
        color = '#000000'

        response = self.client.put(flask.url_for('api.task', id=self.task_1_1.id), json={
            'name': name,
            'color': color,
            'category': self.category_2.id
        })
        self.assertEqual(response.status_code, 200)

        data = response.get_json()
        self.assertEqual(data['id'], self.task_1_1.id)
        self.assertEqual(data['name'], name)
        self.assertEqual(data['color'], color)
        self.assertEqual(data['category'], self.category_2.id)

        t = Task.query.get(data['id'])
        self.assertEqual(name, t.name)
        self.assertEqual(color, t.color)
        self.assertEqual(self.category_2.id, t.category_id)

    def test_modify_unknown_task_ko(self):
        self.assertEqual(self.num_task, Task.query.count())

        name = 'whatever'
        color = '#000000'

        response = self.client.put(flask.url_for('api.task', id=-1), json={
            'name': name,
            'color': color,
            'category': self.category_2.id
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_task_ok(self):
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.delete(flask.url_for('api.task', id=self.task_1_1.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_task - 1, Task.query.count())
        self.assertIsNone(Task.query.get(self.task_1_1.id))

    def test_delete_unknown_task_ko(self):
        self.assertEqual(self.num_task, Task.query.count())

        response = self.client.delete(flask.url_for('api.task', id=-1))
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_task, Task.query.count())
