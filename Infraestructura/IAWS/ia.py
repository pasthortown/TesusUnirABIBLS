import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from pymongo import MongoClient
import datetime
from bson import json_util
import json
import uuid
import jwt
from dateutil import parser
import random

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio de Inteligencia Artificial Operativo', 'status':200})


class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, action):
        pass
    
    def post(self, action):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (action == 'hashtags'):
            respuesta = hashtags()
        if (action == 'tweets'):
            respuesta = tweets()
        self.write(respuesta)
        return

def hashtags():
    collection = db['hashtags']
    response = []
    for w in range(100):
        word = { 'text': 'palabra' + str(w), 'weight': random.randint(1, 10), 'rotate': random.randint(-90, 90)}
        response.append(word)
    return {'response':response, 'status':200}

def tweets():
    collection = db['tweets']
    lineChartLabels = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio']
    lineChartDatasets = [
        { 'data': [ 65, 59, 80, 81, 56, 55, 40 ], 'label': '2021', 'fill': True, 'tension': 0.5 },
        { 'data': [ 40, 55, 56, 81, 80, 59, 65 ], 'label': '2022', 'fill': True, 'tension': 0.5 }
    ]
    barChartLabels = ['España', 'Ecuador', 'Estados Unidos', 'Alemania', 'Francia', 'Colombia', 'Brasil']
    barChartDatasets = [
        { 'data': [ 65, 59, 80, 81, 56, 55, 40 ], 'label': '2021' },
        { 'data': [ 28, 48, 40, 19, 86, 27, 90 ], 'label': '2022' }
    ]
    radarChartLabels = ['España', 'Ecuador', 'Estados Unidos', 'Alemania', 'Francia', 'Colombia', 'Brasil']
    radarChartDatasets = [
        { 'data': [65, 59, 90, 81, 56, 55, 40], 'label': 'Hombres' },
        { 'data': [28, 48, 40, 19, 96, 27, 100], 'label': 'Mujeres' }
    ]
    response = { 
                    'lineChartLabels': lineChartLabels,
                    'lineChartDatasets': lineChartDatasets,
                    'barChartLabels': barChartLabels,
                    'barChartDatasets': barChartDatasets,
                    'radarChartLabels': radarChartLabels,
                    'radarChartDatasets': radarChartDatasets,
               }
    return {'response':response, 'status':200}

def validate_token(token):
    try:
        response = jwt.decode(token, app_secret, algorithms=['HS256'])
        exp_time = parser.parse(response['valid_until'])
        app_name = response['app_name']
        if (app_name == allowed_app_name and datetime.datetime.now() < exp_time):
            return True
        else:
            return False
    except:
        return False

def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)
    
if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()