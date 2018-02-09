from flask import Flask, request, g, current_app
from werkzeug.local import LocalProxy
from ibisclient import *

app = Flask(__name__)

def getIbis():
    if getattr(g, 'conn', None) is None:
        g.conn = createTestConnection()
    if getattr(g, 'methods', None) is None:
        g.methods = PersonMethods(g.conn)
    return g.methods

methods = LocalProxy(getIbis)

@app.route('/')
@app.route('/index.html')
def index():
    crsid = request.headers.get('X-Aaprincipal').split(' ')[1]
    person = methods.getPerson("crsid", crsid, fetch="all_insts")
    instid_list = list()
    for i in person.institutions:
        instid_list.append(i.instid)
    if 'KINGSUG' in instid_list or 'KINGSPG' in instid_list:
        return "King's Member!"
    else:
        return "Not a King's Member."
        


