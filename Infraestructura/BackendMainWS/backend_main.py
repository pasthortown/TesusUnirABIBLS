# Importación las bibliotecas de Python necesarias para realizar tareas, entre las que podemos mencionar:
#  - Conexión con MongoDB
#  - Levantamiento de API web

import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
from pymongo import MongoClient
from datetime import datetime
from datetime import date
from bson import json_util
import json
import jwt
from dateutil import parser
import logging
from collections import defaultdict

# Función para escribir en el archivo de log
def write_log(content):
    logging.info(content)

# Se obtienen las credenciales para conectarse a la base de datos de MongoDB y a la API de Twitter desde variables de entorno
mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

# Configuración del logger
logging.basicConfig(filename='logs.txt', level=logging.DEBUG)

# Conexión a la base de datos de MongoDB
database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

# Levantamiento del API URL "/" HTTP: GET
class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio de Inteligencia Artificial Operativo', 'status':200})

# Levantamiento del API HTTP: POST
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
        if (action == 'get_all_tweets'):
            respuesta = get_all_tweets()
        if (action == 'upload_tweets_backup'):
            respuesta = upload_tweets_backup(content['tweets'])
        if (action == 'upload_hashtags_backup'):
            respuesta = upload_hashtags_backup(content['hashtags'])
        if (action == 'update_tweet'):
            respuesta = update_tweet(content)
        self.write(respuesta)
        return

# Función para cargar a la base de datos Mongo el backup de Hashtags
def upload_hashtags_backup(hashtags):
    collection_t = db['hashtags']
    collection_t.drop()
    collection = db['hashtags']
    toInsert = [{'hashtag': h['text'], 'count': h['weight']} for i, h in enumerate(hashtags)]
    for hashtag in toInsert:
        collection.insert_one(hashtag)
    return {'response':'success', 'status':200}

# Función para cargar a la base de datos Mongo el backup de Tweets
def upload_tweets_backup(tweets):
    collection_t = db['tweets']
    collection_t.drop()
    collection = db['tweets']
    for tweet in tweets:
        collection.insert_one(tweet)
    return {'response':'success', 'status':200}

# Función que devuelve los hashtags almacenados en la base de datos
def hashtags():
    collection = db['hashtags']
    hashtags_on_db = collection.find({})
    toReturn = [{'text': h['hashtag'], 'weight': h['count'], 'rotate': i % 2 * 90} for i, h in enumerate(hashtags_on_db)]
    return {'response':toReturn, 'status':200}

# Función que devuelve todos los tweets almacenados
def get_all_tweets():
    collection = db['tweets']
    tweets = json.loads(json_util.dumps(collection.find({})))
    return {'response':tweets, 'status':200}

# Función que devuelve los tweets almacenados en la base de datos y clasificados como Xenofóbicos
def get_tweets_from_db():
    collection = db['tweets']
    meses = [ "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre" ]
    pipeline = [
        { "$match": { "clasificado": "Xenofóbico" } },
        { "$project": { 
            "_id": 0, 
            "user_gender": 1,
            "pais": 1,
            "text": 1,
            "clasificado": 1,
            "created_at": 1, 
            "month": { "$month": "$created_at" },
            "month_name": { 
                "$arrayElemAt": [
                    meses,
                    { "$subtract": [ { "$month": "$created_at" }, 1 ] }
                ]
            },
            "year": { "$year": "$created_at" }
        }}
    ]
    return json.loads(json_util.dumps(collection.aggregate(pipeline)))

# Función para construir el gráfico de líneas correspondiente a los tweets clasificados omo Xenofóbico por mes
def build_tweets_by_month(list_tweets):
    lineChartDatasets = []
    tweet_counts = defaultdict(lambda: [0] * 12)
    for tweet in list_tweets:
        year = tweet["year"]
        month = tweet["month"] - 1 
        tweet_counts[year][month] += 1
    for year in sorted(tweet_counts.keys()):
        data = tweet_counts[year]
        dataset = {'data': data, 'label': str(year), 'fill': True, 'tension': 0.5}
        lineChartDatasets.append(dataset)
    return lineChartDatasets

# Función para construir el gráfico de barras correspondiente a los tweets clasificados omo Xenofóbico por país
def build_tweets_by_country(list_tweets):
    barChartDatasets = []
    paises = list(set([str(tweet["pais"]).upper() for tweet in list_tweets]))
    years = list(set([tweet["year"] for tweet in list_tweets]))
    for year in years:
        data = []
        for pais in paises:
            cuenta_tweets = sum(1 for tweet in list_tweets if str(tweet["pais"]).upper() == str(pais).upper() and tweet["year"] == year)
            data.append(cuenta_tweets)
        dataset = {'data': data, 'label': str(year)}
        barChartDatasets.append(dataset)
    return barChartDatasets

# Función para construir el gráfico de radar correspondiente a los tweets clasificados omo Xenofóbico por género y país
def build_tweets_by_gender(list_tweets):
    radarChartDatasets = []
    genders = list(set([str(tweet["user_gender"]).upper() for tweet in list_tweets]))
    paises = list(set([str(tweet["pais"]).upper() for tweet in list_tweets]))
    for gender in genders:
        data = []
        for pais in paises:
            cuenta_tweets = sum(1 for tweet in list_tweets if str(tweet["pais"]).upper() == str(pais).upper() and str(tweet["user_gender"]).upper() == str(gender).upper())
            data.append(cuenta_tweets)
        dataset = {'data': data, 'label': str(gender)}
        radarChartDatasets.append(dataset)
    return radarChartDatasets

# Función para obtener los tweets clasificados como Xenofóbico en el mes
def get_current_month_tweets(list_tweets):
    current_month = date.today().month
    current_year = date.today().year
    current_month_tweets = []
    for tweet in list_tweets:
        if tweet["month"] == current_month and tweet["year"] == current_year:
            current_month_tweets.append(tweet)
    return current_month_tweets

# Función para devolver la información para las gráficas
def tweets():
    meses = [ "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre" ]
    list_tweets = get_tweets_from_db()
    lineChartLabels = meses
    lineChartDatasets = build_tweets_by_month(list_tweets)
    barChartDatasets = build_tweets_by_country(list_tweets)
    paises = list(set([str(tweet["pais"]).upper() for tweet in list_tweets]))
    barChartLabels = paises
    radarChartLabels = paises
    radarChartDatasets = build_tweets_by_gender(list_tweets)
    response = { 
                    'tweets': get_current_month_tweets(list_tweets),
                    'lineChartLabels': lineChartLabels,
                    'lineChartDatasets': lineChartDatasets,
                    'barChartLabels': barChartLabels,
                    'barChartDatasets': barChartDatasets,
                    'radarChartLabels': radarChartLabels,
                    'radarChartDatasets': radarChartDatasets,
               }
    return {'response':response, 'status':200}

# Función para actualizar un tweet desde la interfaz DataView para entrenamiento y corrección de clasificación del modelo
def update_tweet(data):
    collection = db['tweets']
    collection.update_one( {'tweet_id': data['tweet_id']}, {'$set': {'clasificado': data['clasificado']}} )
    return {'response':'done', 'status':200}

# Validación del token JWT para autorizar la comunicación con el API
def validate_token(token):
    try:
        response = jwt.decode(token, app_secret, algorithms=['HS256'])
        exp_time = parser.parse(response['valid_until'])
        app_name = response['app_name']
        if (app_name == allowed_app_name and datetime.now() < exp_time):
            return True
        else:
            return False
    except:
        return False

# Función para inicializar el API
def make_app():
    urls = [
        ("/", DefaultHandler),
        ("/([^/]+)", ActionHandler)
    ]
    return Application(urls, debug=True)
    
# Este código pone en marcha el servicio del API en el puerto 5050
if __name__ == '__main__':
    app = make_app()
    app.listen(5050)
    IOLoop.instance().start()