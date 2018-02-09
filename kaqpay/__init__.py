from flask import Flask, request
from ..ibisclient import *

app = Flask(__name__)

@app.route('/')
@app.route('/index.html')
def index():
    crsid = request.headers.get('X-Aaprincipal').split(' ')[1]
    conn = createConnection()
    methods = PersonMethods(conn)
    person = methods.getPerson("crsid", crsid, fetch="all_inst")
    instid_list = list()
    for i in person.institutions:
        instid_list.append(i.instid)
    return "{crsid} at {inst}".format(crsid=crsid, inst=str(instid_list))

