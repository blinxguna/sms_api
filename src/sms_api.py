

import os
import re
import json
import redis

from flask import Flask
from functools import wraps
from flask import request, Response, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask.views import MethodView

import logging
file_handler = logging.FileHandler('app.log')

app = Flask(__name__)
app.config.from_object(os.environ['APP_SETTINGS'])
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)
db = SQLAlchemy(app)
r_server = redis.Redis('localhost')

#from src.models import PhoneNumber

"""
   Model Implemented to Access the Postgresql Data
"""

class Account(db.Model):

    __tablename__ = 'account'

    id = db.Column(db.Integer, db.Sequence('account_id_seq'), primary_key=True)
    auth_id = db.Column(db.String(30))
    username = db.Column(db.String(40))

    def __repr__(self):
        return( 'Account( ' + str( self.auth_id ) + ', ' + self.username + ')' )

class PhoneNumber(db.Model):

    __tablename__ = 'phone_number'

    id = db.Column(db.Integer, primary_key=True)
    number = db.Column(db.String(40))
    account_id = db.Column(db.Integer,  db.ForeignKey('account.id'))

    def __repr__(self):
        return( 'Account( ' + str( self.auth_id ) + ', ' + self.username + ')' )


def check_auth(auth):
    """This function is called  Account Model and check /
    password combination is valid.
    """
    account_obj = Account.query.filter_by(username=auth.username, auth_id=auth.password)
    if account_obj.count() > 0:
        return True, account_obj
    return False, account_obj

def authenticate():
    """Sends a 403 response that enables basic auth"""
    return Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 403,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})


def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        status, user_obj  = check_auth(auth)
        if not auth or not status:
            return authenticate()
        return f(*args, **kwargs)
    return decorated

def api_root():
    """
        Sample API url Welcome msg
    """
    return 'Welcome to sms api'

"""
    Cache Layer
"""

class RedisCache(object):
    """
        Class to implement redis and custom sms api methods
    """
    MAX_API_OUTBOUND =2
    COUNTER_EXIPRE_VALUE = 24 * 60 * 60
    SMS_EXPIRE_VALUE = 4 * 60 * 60

    def __init__(self, ip_data, s_handle):
        self.redis = s_handle
        self.d_json = ip_data
        self.from_string = self.d_json['from']
        self.to_string = self.d_json['to']
        self.text_string = self.d_json['text']
        self.from_to_string = self.from_string+'_'+self.to_string
        self.from_str_cnt = self.from_string+'_counter'
        self.error = ''

    def _store_cache(self, p, w):
        return self.redis.set(p, w)

    def _get_cache(self, v):
        return self.redis.get(v)

    def store_sms_cache(self):
        """The 'from' and 'to' pair must be stored in Redis as a unique
        entry and should expire after 4 hours."""
        app.logger.info(("Store method key = {} and value {} ").format(self.from_to_string, self.text_string))
        if self._store_cache(self.from_to_string, self.text_string):
            return self._set_expires(self.from_to_string, self.SMS_EXPIRE_VALUE)

    def check_sms_cache(self):
        if self._get_cache(self.from_to_string):
            app.logger.info('check method already exist stop msg')
            self.error = 'sms from {} to {} blocked by STOP reqeust'.format(self.from_string, self.to_string)
            return False

        out_value = self._get_cache(self.from_str_cnt)
        if out_value == None:
            out_value = self._counter_increment(self.from_str_cnt)
            if int(out_value) == 1:
                #First Time found 'From' set expire to 24 hours
                app.logger.info('first time from msg save 24hours cache')
                self._set_expires(self.from_str_cnt, self.COUNTER_EXIPRE_VALUE)
        else:
            if int(out_value) >= self.MAX_API_OUTBOUND:
                app.logger.info(('limit {} reached outbound {} msg').format(self.MAX_API_OUTBOUND, self.from_string))
                self.error = 'limit reached for from {}'.format(self.from_string)
                return False
            out_value = self._counter_increment(self.from_str_cnt)

        return True

    def _counter_increment(self, k):
        return self.redis.incr(k)

    def _set_expires(self, v, s):
        return self.redis.expire(v,int(s))

    def error_out(self):
        return jsonify({"message": "", "error": self.error})

"""
    Business Layer
"""

class SmsValidator(object):
    """
        Class to implement custom sms api validation methods
    """
    def __init__(self, ip_data , msg_string='inbound'):
        self.msg = msg_string
        self.d_json = ip_data
        self.to_from_length  = re.compile('^[0-9]{6,16}$')
        self.text_length  = re.compile('^[a-zA-Z, 0-9]{1,120}$')
        self.stop_msg = re.compile('STOP|STOP\n|STOP\r|STOP\r\n')
        self.error = None
        self.in_list = ['to', 'from', 'text']

    def _field_validation(self):
        for i in self.in_list:
            if not i in self.d_json.keys():
                self.error = i + ' is missing'
                return False
        return True

    def _to_from_string_valid(self, d):
        if self.to_from_length.match(d):
            return True
        return False

    def _text_string_valid(self, d):
        if self.text_length.match(d):
            return True
        return False

    def is_valid(self):
        app.logger.info('sms valid method')
        if self._field_validation():
            for j in self.in_list[:2]:
                if not self._to_from_string_valid(self.d_json[j]):
                    self.error = j + ' is invalid'
                    return False
            if not self._text_string_valid(self.d_json['text']):
                self.error = 'text is invalid'
                return False
        else:
            return False
        return True

    def detect_stop(self):
        if self.stop_msg.match(self.d_json['text']):
            return True
        return False

    def output_json(self):
        if self.error:
            return jsonify({"message": "", "error": self.error})
        else:
            return jsonify({"message": self.msg+" sms ok", "error": ""})

"""
    API Layer
"""

class InboundSmsApi(MethodView):

    @requires_auth
    def post(self):
        try :
            app.logger.info(('Post msg Inbound msg {}').format(request.json))
            valid_obj = SmsValidator(request.json, 'inbound' )
            status, user_obj = check_auth(request.authorization)
            if valid_obj.is_valid():
                app.logger.info(('check to number Inbound PhoneNumber {}').format(valid_obj.d_json['to']))
                account_id = user_obj[0].id
                data = PhoneNumber.query.filter_by(number=valid_obj.d_json['to'], account_id=account_id)
                if data.count() == 0:
                    valid_obj.error = 'to parameter not found'
                    return valid_obj.output_json()
                if valid_obj.detect_stop():
                    redis_obj = RedisCache(request.json, r_server)
                    redis_obj.store_sms_cache()
            app.logger.info(('End Post inbound msg {}').format(valid_obj.output_json()))
            return valid_obj.output_json()
        except Exception as err:
            app.logger.error(('Exception in inbound {}').format(err))
            return jsonify({"message": "", "error": "unknown failure"})

class OutboundSmsApi(MethodView):

    @requires_auth
    def post(self):
        try :
            app.logger.info(('Start Post msg outbound msg {}').format(request.json))
            valid_obj = SmsValidator(request.json, 'outbound')
            status, user_obj = check_auth(request.authorization)
            if valid_obj.is_valid():
                app.logger.info(('check from number Inbound PhoneNumber {}').format(valid_obj.d_json['from']))
                account_id = user_obj[0].id
                data = PhoneNumber.query.filter_by(number=valid_obj.d_json['from'], account_id=account_id)
                if data.count() == 0:
                    valid_obj.error = 'from parameter not found'
                    return valid_obj.output_json()
                redis_obj = RedisCache(request.json, r_server)
                if not redis_obj.check_sms_cache():
                    return redis_obj.error_out()
            app.logger.info(('End Post outbound msg {}').format(valid_obj.output_json()))
            return valid_obj.output_json()
        except Exception as err:
            app.logger.error(('Exception in outbound {}').format(err))
            return jsonify({"message": "", "error": "unknown failure"})


# urls for User API
inbound_api_view = InboundSmsApi.as_view('inbound_api')
outbound_api_view = OutboundSmsApi.as_view('outbound_api')

app.add_url_rule('/inbound/sms/', view_func = inbound_api_view, methods=["POST",])
app.add_url_rule('/outbound/sms/', view_func = outbound_api_view, methods=["POST",])
app.add_url_rule('/', 'index', api_root)

if __name__ == '__main__':
    app.run()
