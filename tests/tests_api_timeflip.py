import flask

from tests import FlaskTestCase

from timefliptt.blueprints.base_models import TimeFlipDevice, Task, Category, FacetToTask


class TimeFlipTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000')
        self.db_session.add(self.device)
        self.db_session.commit()

        self.num_devices = TimeFlipDevice.query.count()

    def test_view_devices(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.get(flask.url_for('api.timeflips'))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('timeflip_devices', data)
        self.assertEqual(len(data['timeflip_devices']), self.num_devices)

    def test_add_device_ok(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'password': password
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIsNone(data['name'])
        self.assertEqual(password, data['password'])
        self.assertEqual(address, data['address'])

        self.assertEqual(self.num_devices + 1, TimeFlipDevice.query.count())

        d = TimeFlipDevice.query.get(data['id'])
        self.assertIsNone(d.name)
        self.assertEqual(password, d.password)
        self.assertEqual(address, d.address)

    def test_add_device_already_exists_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': self.device.address,
            'password': self.device.password
        })

        self.assertEqual(response.status_code, 403)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

    def test_add_device_wrong_address_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address + 'x',
            'password': password
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

    def test_add_device_wrong_password_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        # too long
        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'password': password + 'x'
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        # too short
        password = '0' * 2

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'password': password
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

    def test_view_device_ok(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.get(flask.url_for('api.timeflip', id=self.device.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(self.device.name, data['name'])
        self.assertEqual(self.device.address, data['address'])
        self.assertEqual(self.device.password, data['password'])

    def test_view_unknown_device_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.get(flask.url_for('api.timeflip', id=-1))
        self.assertEqual(response.status_code, 404)

    def test_delete_device_ok(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.delete(flask.url_for('api.timeflip', id=self.device.id))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_devices - 1, TimeFlipDevice.query.count())
        self.assertIsNone(TimeFlipDevice.query.get(self.device.id))

    def test_delete_unknown_device_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        response = self.client.delete(flask.url_for('api.timeflip', id=-1))
        self.assertEqual(response.status_code, 404)

        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())


class FacetToTaskTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.category = Category.create('test1')
        self.db_session.add(self.category)

        self.device = TimeFlipDevice.create('00:00:00:00:00:00', '000000', 'TF')
        self.db_session.add(self.device)
        self.db_session.commit()

        self.num_devices = TimeFlipDevice.query.count()

        self.task_1 = Task.create('test1', self.category, '#ffffff')
        self.db_session.add(self.task_1)
        self.task_2 = Task.create('test2', self.category, '#ffffff')
        self.db_session.add(self.task_2)
        self.db_session.commit()

        self.ftt = FacetToTask.create(self.device, 0, self.task_1)
        self.db_session.add(self.ftt)
        self.db_session.commit()

        self.num_ftt = FacetToTask.query.count()

    def test_view_facets_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())

        response = self.client.get(flask.url_for('api.timeflip-facets', id=self.device.id))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertIn('facet_to_task', data)
        self.assertEqual(len(data['facet_to_task']), self.num_ftt)

    def test_add_tasks_new_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = 1
        self.assertNotEqual(facet, self.ftt.facet)

        response = self.client.put(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet), json={
            'task': self.task_2.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(facet, data['facet'])
        self.assertEqual(self.task_2.id, data['task']['id'])

        self.assertEqual(self.num_ftt + 1, FacetToTask.query.count())

        ftt = FacetToTask.query.order_by(FacetToTask.id.desc()).first()
        self.assertEqual(facet, ftt.facet)
        self.assertEqual(self.device.id, ftt.timeflip_device_id)
        self.assertEqual(self.task_2.id, ftt.task_id)

    def test_add_tasks_existing_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = self.ftt.facet
        self.assertEqual(self.ftt.task_id, self.task_1.id)

        response = self.client.put(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet), json={
            'task': self.task_2.id
        })
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(facet, data['facet'])
        self.assertEqual(self.task_2.id, data['task']['id'])

        self.assertEqual(self.num_ftt, FacetToTask.query.count())

        ftt = FacetToTask.query.get(self.ftt.id)  # existing line is modified!
        self.assertEqual(facet, ftt.facet)
        self.assertEqual(self.device.id, ftt.timeflip_device_id)
        self.assertEqual(self.task_2.id, ftt.task_id)

    def test_add_tasks_too_large_facet_ko(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = 200
        self.assertNotEqual(facet, self.ftt.facet)

        response = self.client.put(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet), json={
            'task': self.task_2.id
        })
        self.assertEqual(response.status_code, 422)

        self.assertEqual(self.num_ftt, FacetToTask.query.count())

    def test_view_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = self.ftt.facet

        response = self.client.get(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet))
        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(facet, data['facet'])
        self.assertEqual(self.task_1.id, data['task']['id'])

    def test_view_unknown_facet_ko(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = 1
        self.assertNotEqual(facet, self.ftt.facet)

        response = self.client.get(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet))
        self.assertEqual(response.status_code, 404)

    def test_delete_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())

        response = self.client.delete(flask.url_for('api.timeflip-facet', id=self.device.id, facet=self.ftt.facet))
        self.assertEqual(response.status_code, 200)

        self.assertEqual(self.num_ftt - 1, FacetToTask.query.count())
        self.assertIsNone(FacetToTask.query.get(self.ftt.id))

    def test_delete_unknown_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())
        facet = 1
        self.assertNotEqual(facet, self.ftt.facet)

        response = self.client.delete(flask.url_for('api.timeflip-facet', id=self.device.id, facet=facet))
        self.assertEqual(response.status_code, 404)

    def test_delete_task_also_delete_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())

        self.db_session.delete(self.task_1)
        self.db_session.commit()

        self.assertEqual(self.num_ftt - 1, FacetToTask.query.count())
        self.assertIsNone(FacetToTask.query.get(self.ftt.id))

    def test_delete_device_also_delete_facet_ok(self):
        self.assertEqual(self.num_ftt, FacetToTask.query.count())

        self.db_session.delete(self.device)
        self.db_session.commit()

        self.assertEqual(self.num_ftt - 1, FacetToTask.query.count())
        self.assertIsNone(FacetToTask.query.get(self.ftt.id))
