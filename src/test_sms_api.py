from flask import Flask
import unittest
from base64 import b64encode
import json

from sms_api import app, db, Account, PhoneNumber

class SmsApiTests(unittest.TestCase):


    # def setUp(self):
    #     self.app = app.test_client()

    def setUp(self):
        """
        Creates a new database for the unit test to use
        """
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.commit()
        self.client = app.test_client()


    def tearDown(self):
        """
        Ensures that the database is emptied for next unit test
        """
        pass

    def basic_auth(self, username, password):
        headers = {
        'Authorization': 'Basic ' + b64encode("{0}:{1}".format(username, password)),
    }
        return headers

    def test_index(self):
        response = self.client.get("/")
        msg = "Welcome to sms api"
        self.assertEquals(response.data, msg)

    def check_output(self, i, e):
        self.assertEquals(i['error'], e['error'])
        self.assertEquals(i['message'], e['message'])

    #@unittest.skip('test')
    def test_inbound(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': 'inbound sms ok', 'error': ''}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_inbound_to_invalid(self):
        params = { "from" : "4924195509198",
                   "to" : "9198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'to is invalid'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_inbound_from_invalid(self):
        params = { "from" : "9198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'from is invalid'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_inbound_from_missing(self):
        params = {
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'from is missing'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_inbound_text_missing(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198"
                }
        expected = {'message': '', 'error': 'text is missing'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    @unittest.skip('test')
    def test_inbound_unknown(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'unknown failure'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers)
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_inbound_to_not_found(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'to parameter not found'}
        headers = self.basic_auth('plivo5','6DLH8A25XZ')
        response = self.client.post("/inbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound(self):
        params = { "from" : "4924195509012",
                   "to" : "3253280312",
                   "text" : "hello from plivo"
                }
        expected = {'message': 'outbound sms ok', 'error': ''}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_stop_request(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'sms from '+params['from']+' to '+params['to']+' blocked by STOP reqeust'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_to_invalid(self):
        params = { "from" : "4924195509198",
                   "to" : "9198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'to is invalid'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_from_invalid(self):
        params = { "from" : "9198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'from is invalid'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_from_missing(self):
        params = {
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'from is missing'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_text_missing(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198"
                }
        expected = {'message': '', 'error': 'text is missing'}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_from_not_found(self):
        params = { "from" : "4924195509198",
                   "to" : "4924195509198",
                   "text" : "STOP, Hello World"
                }
        expected = {'message': '', 'error': 'from parameter not found'}
        headers = self.basic_auth('plivo5','6DLH8A25XZ')
        response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
        if response.status_code == 200:
            output = json.loads(response.get_data())
            self.check_output(expected, output)

    #@unittest.skip('test')
    def test_outbound_51_reqeust(self):
        params = { "from" : "3253280312",
                   "to" : "3253280312",
                   "text" : "hello from plivo"
                }
        expected = {'message': 'outbound sms ok', 'error': ''}
        headers = self.basic_auth('plivo1','20S0KPNOIM')
        for i in xrange(0,51):
            response = self.client.post("/outbound/sms/", data=json.dumps(params), headers=headers, content_type='application/json')
            if response.status_code == 200:
                output = json.loads(response.get_data())
                if i != 51:
                    expected = {'message': '', 'error' : 'limit reached for from 3253280312'}
                    self.check_output(expected, output)


if __name__ == '__main__':
    unittest.main()
