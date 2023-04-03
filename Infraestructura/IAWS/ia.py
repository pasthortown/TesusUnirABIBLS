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
        self.write({'response':'Administrador de Catálogos Operativo', 'status':200})


class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, catalog, action):
        pass
    
    def post(self, catalog, action):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (action == 'upload_items'):
            items = content['items']
            respuesta = upload_items(catalog, items)
        if (action == 'get_item'):
            item_id = content['item_id']
            output_model = content['output_model']
            respuesta = get_item(catalog, item_id, output_model)
        if (action == 'get_items'):
            output_model = content['output_model']
            respuesta = get_items(catalog, output_model)
        if (action == 'update_item'):
            item_id = content['item_id']
            item = content['item']
            respuesta = update_item(catalog, item_id, item)
        if (action == 'search_items'):
            attribute = content['attribute']
            value = content['value']
            output_model = content['output_model']
            respuesta = search_items(catalog, attribute, value, output_model)
        if (action == 'count'):
            respuesta = count_items(catalog)
        if (action == 'delete_item'):
            item_id = content['item_id']
            deleted = delete_item(catalog, item_id)
            respuesta = {'response':'Elemento no encontrado', 'status':500}
            if (deleted == True):
                respuesta = {'response':'Elemento eliminado', 'status':200}
        self.write(respuesta)
        return

def count_items(catalog):
    collection = db[catalog]
    documents_count = collection.count_documents({})
    return {'response':documents_count, 'status':200}

def upload_items(catalog, items):
    collection = db[catalog]
    log = []
    for item in items:
        item_id = str(uuid.uuid4())
        item['item_id'] = item_id
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.insert_one(item)
        log.append(item)
    toReturn = json.loads(json_util.dumps(log))
    return {'response':toReturn, 'status':200}

def search_items(catalog, attribute, value, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    filter = {}
    filter[attribute] = value
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return
        status = 200
    else:
        toReturn = 'Elemento no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_item(catalog, item_id, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    filter = {"item_id":item_id}
    items = collection.find(filter, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        toReturn = items_to_return[0]
        status = 200
    else:
        toReturn = 'Elemento no encontrado'
        status = 500
    return {'response':toReturn, 'status':status}

def get_items(catalog, output_model):
    collection = db[catalog]
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['timestamp'] = True
    items = collection.find({}, output_model)
    items_to_return = json.loads(json_util.dumps(items))
    return {'response':items_to_return, 'status':200}

def update_item(catalog, item_id, item):
    collection = db[catalog]
    filter = {"item_id":item_id}
    prev_items = collection.find(filter)
    previous_items = json.loads(json_util.dumps(prev_items))
    if (len(previous_items) == 0):
        return {'response': 'Elemento no encontrado', 'status':500}
    else:
        item['timestamp'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        collection.update_one(filter, {'$set':item})
        log = []
        log.append(item)
        toReturn = json.loads(json_util.dumps(log))
        return {'response':toReturn, 'status':200}

def delete_item(catalog, item_id):
    collection = db[catalog]
    filter = {"item_id":item_id}
    items = collection.find(filter, {
        "item_id": True, 
        "_id": False
    })
    items_to_return = json.loads(json_util.dumps(items))
    if (len(items_to_return)>0):
        collection.delete_one(filter)
        toReturn = True
    else:
        toReturn = False
    return toReturn

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
        ("/([^/]+)/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)
    
if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()