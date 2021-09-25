import flask

from tests import FlaskTestCase

from timefliptt.blueprints.base_models import TimeFlipDevice


class CategoriesTestCase(FlaskTestCase):
    def setUp(self):
        super().setUp()

        self.device = TimeFlipDevice.create('TF', '00:00:00:00:00:00', '000000')
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

        name = 'whatever'
        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'name': name,
            'password': password
        })

        self.assertEqual(response.status_code, 200)
        data = response.get_json()

        self.assertEqual(name, data['name'])
        self.assertEqual(password, data['password'])
        self.assertEqual(address, data['address'])

        self.assertEqual(self.num_devices + 1, TimeFlipDevice.query.count())

        d = TimeFlipDevice.query.get(data['id'])
        self.assertEqual(name, d.name)
        self.assertEqual(password, d.password)
        self.assertEqual(name, d.name)

    def test_add_device_wrong_address_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        name = 'whatever'
        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address + 'x',
            'name': name,
            'password': password
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

    def test_add_device_wrong_name_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        name = 'x' * 19
        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'name': name + 'x',
            'password': password
        })

        self.assertEqual(response.status_code, 422)
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

    def test_add_device_wrong_password_ko(self):
        self.assertEqual(self.num_devices, TimeFlipDevice.query.count())

        name = 'whatever'
        address = '12:34:56:78:9a:bc'
        password = '0' * 6

        response = self.client.post(flask.url_for('api.timeflips'), json={
            'address': address,
            'name': name,
            'password': password + 'x'
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
