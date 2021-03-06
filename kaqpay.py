from flask import Flask, request, g, current_app, redirect, jsonify, render_template
from werkzeug.local import LocalProxy
from ibisclient import *
from functools import reduce
from urllib import parse
from datetime import datetime, timedelta
import jwt

import sys
import logging
from logging.handlers import SMTPHandler

class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno <= self.level


app = Flask(__name__)
app.config.from_object('config')

app.logger.setLevel(logging.INFO)

stdout = logging.StreamHandler(stream=sys.stdout)
stderr = logging.StreamHandler(stream=sys.stderr)

stdout.addFilter(MaxLevelFilter(logging.WARNING))
stdout.setLevel(logging.INFO)
stderr.setLevel(logging.ERROR)

fmt = logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s')
stdout.setFormatter(fmt)
stderr.setFormatter(fmt)

app.logger.addHandler(stdout)
app.logger.addHandler(stderr)

if app.config.get('SMTP'):
    mail = SMTPHandler(
            mailhost=app.config.get('SMTP_HOST'),
            fromaddr=app.config.get('SMTP_ADDR'),
            toaddrs=app.config.get('ADMIN_EMAIL'),
            credentials=app.config.get('SMTP_CREDENTIALS'),
            subject='KA x Qpay Sign In Error')
    mail.setFormatter(fmt)
    mail.setLevel(logging.CRITICAL)
    app.logger.addHandler(mail)

def getIbis():
    if getattr(g, 'conn', None) is None:
        g.conn = createConnection()
    if getattr(g, 'methods', None) is None:
        g.methods = PersonMethods(g.conn)
    return g.methods

methods = LocalProxy(getIbis)

@app.route('/')
@app.route('/index.html')
def index():
    crsid = request.headers.get('X-Aaprincipal').split(' ')[1]
    person = methods.getPerson("crsid", crsid, fetch="all_attrs")
    instids = list(map(lambda attr: attr.value, person.attributes))
    is_kings = reduce(lambda x, y: x or y, [(i in instids) for i in app.config.get('KINGS')])
    now = datetime.utcnow()
    payload = {'email': "{}@cam.ac.uk".format(crsid), 
               'kings': is_kings, 
               'exp': now + timedelta(minutes = 15)}
    app.logger.info("%s logged in successfully. (kings: %s)", crsid, is_kings)
    encoded = jwt.encode(payload, app.config.get('JWT_KEY'), algorithm=app.config.get('JWT_ALGORITHM')) 
    if is_kings and now < datetime(2018,3,6,0,0):
        url = app.config.get('QPAY_KINGS_URL')
        app.logger.info("sending %s to King's URL", crsid)
    else:
        url = app.config.get('QPAY_UNI_URL')
        app.logger.info("sending %s to General Release URL", crsid)
    return redirect("{qpay}?{enc}".format(qpay=url, 
                                          enc=parse.urlencode({'jwt': encoded})))

if app.config.get('DEBUG'):
    @app.route('/test')
    def test():
        app.logger.info("Access to test site")
        return render_template('test.html')

    @app.route('/test/kings')
    def test_kings():
        payload = {'email': "test01@cam.ac.uk", 
                   'kings': True, 
                   'exp': datetime.utcnow() + timedelta(minutes = 15)}
        app.logger.info("Testing King's Member URL.")
        encoded = jwt.encode(payload, app.config.get('JWT_KEY'), algorithm=app.config.get('JWT_ALGORITHM')) 
        return redirect("{qpay}?{enc}".format(qpay=app.config.get('QPAY_KINGS_URL'), 
                                              enc=parse.urlencode({'jwt': encoded})))

    @app.route('/test/non_kings')
    def test_non_kings():
        payload = {'email': "test02@cam.ac.uk", 
                   'kings': False, 
                   'exp': datetime.utcnow() + timedelta(minutes = 15)}
        app.logger.info("Testing Non-King's University Member URL.")
        encoded = jwt.encode(payload, app.config.get('JWT_KEY'), algorithm=app.config.get('JWT_ALGORITHM')) 
        return redirect("{qpay}?{enc}".format(qpay=app.config.get('QPAY_UNI_URL'), 
                                              enc=parse.urlencode({'jwt': encoded})))

    @app.route('/test/response')
    def test_response():
        param = request.args.get('jwt')
        if param is not None:
            enc = parse.unquote(param)
            algo = app.config.get('JWT_ALGORITHM')
            if algo.startswith('RS'):
                key = app.config.get('JWT_PUBLIC_KEY')
            else:
                key = app.config.get('JWT_KEY')
            result = jwt.decode(enc, key=key, algorithms=[algo])
            return jsonify(result)
        else:
            res = jsonify({'error': 'Pass in a JWT.'})
            res.status_code = 400
            return res
    
@app.errorhandler(jwt.exceptions.InvalidTokenError)
def handle_invalid_tokens(error):
    app.logger.error("Invalid Token Error.")
    return jsonify({'error': 'Invalid Key.'}), 400
    
@app.errorhandler(jwt.exceptions.InvalidKeyError)
def handle_invalid_keys(error):
    app.logger.error("Invalid Key Error.")
    return jsonify({'error': 'Invalid Key.'}), 400

@app.errorhandler(AttributeError)
def handle_attribute_error(error):
    app.logger.error("AttributeError.")
    return "Wrong way In!", 400
