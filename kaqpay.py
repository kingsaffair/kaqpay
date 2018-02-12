from flask import Flask, request, g, current_app, redirect, jsonify
from werkzeug.local import LocalProxy
from ibisclient import *
from functools import reduce
from urllib import parse
import jwt

import sys
import logging
from logging.handlers import SMTPHandler

class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level

    def filter(self, record):
        return record.levelno < self.level


app = Flask(__name__)
app.config.from_object('config')

stdout = logging.StreamHandler(stream=sys.stdout)
stdout.setLevel(logging.INFO)
stdout.addFilter(MaxLevelFilter(logging.WARNING))
stderr = logging.StreamHandler(stream=sys.stderr)
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
    person = methods.getPerson("crsid", crsid, fetch="all_insts")
    instids = list(map(lambda i: i.instid, person.institutions))
    is_kings = reduce(lambda x, y: x or y, [(i in instids) for i in app.config.get('KINGS')])
    payload = {'email': "{}@cam.ac.uk".format(crsid), 'kings': is_kings}
    app.logger.info("%s logged in successfully. (kings: %s)", crsid, is_kings)
    encoded = jwt.encode(payload, app.config.get('JWT_KEY'), algorithm=app.config.get('JWT_ALGORITHM')) 
    return redirect("{qpay}?{enc}".format(qpay=app.config.get('QPAY_URL'), 
                                          enc=parse.urlencode({'jwt': encoded})))


@app.route('/test_response')
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
        return jsonify({'error': 'Pass in a JWT.'})
    

