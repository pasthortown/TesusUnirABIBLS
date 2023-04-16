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
import tweepy
import spacy
import nltk
import gender_guesser.detector as gender
from country_list import countries_for_language
import re
import logging

def write_log(content):
    logging.info(content)

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

api_key = os.getenv('twitter_api_key')
api_key_secret = os.getenv('twitter_api_key_secret')
access_token = os.getenv('twitter_access_token')
access_token_secret = os.getenv('twitter_access_token_secret')

logging.basicConfig(filename='logs.txt', level=logging.DEBUG)
countries = dict(countries_for_language('es'))

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('spanish')
nlp = spacy.load('es_core_news_sm')

auth = tweepy.OAuth1UserHandler(api_key, api_key_secret, access_token, access_token_secret)
try:
    api = tweepy.API(auth)
    api.verify_credentials()
    write_log('Conexión a Twitter Exitosa')
except:
    write_log('Conexión a Twitter Fallida')

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
        if (action == 'search_tweets_and_store_on_db'):
            respuesta = search_tweets_and_store_on_db(content)
        self.write(respuesta)
        return

def get_tweets_by_hashtag(hashtag, since_date, until_date, items=100):
    numero_consultas_excedido = False
    try:
        tweets = tweepy.Cursor(api.search_tweets, q=hashtag, lang="es", since_id=since_date, until=until_date).items(int(items))
    except tweepy.TooManyRequests:
        write_log("Se excedió el límite de la tasa. Por favor espere 5 minutos antes de continuar.")
        numero_consultas_excedido = True
    output = []
    if (not numero_consultas_excedido):
        detector = gender.Detector()
        for tweet in tweets:
            caracteres_especiales = "@#$%^&*()_+=.,:"
            user_name=str(tweet.user.name)
            ubicacion = str(tweet.user.location)
            for caracter in caracteres_especiales:
                user_name = user_name.replace(caracter, "")
                ubicacion = ubicacion.replace(caracter, "")
            regex = r'\b{}\b'.format('|'.join(countries.values()))
            match = re.search(regex, ubicacion, re.IGNORECASE)
            twitter_pais = match.group(0) if match else None
            nombres = user_name.split()
            gender_detected = None
            for nombre in nombres:
                gender_detected = detector.get_gender(nombre)
                if gender_detected != 'unknown' and gender_detected != None:
                    break
            genero = 'female' if 'female' in str(gender_detected) else 'male' if 'male' in str(gender_detected) else 'unknown'
            output.append({
                'created_at': tweet.created_at,
                'user_gender': genero,
                'pais': twitter_pais,
                'text': tweet.text,
                'clasificado': 'Pendiente'
            })
    return output

def search_keywords_in_text(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if not token.is_stop and token.is_alpha]
    keywords = [keyword for keyword in keywords if keyword.lower() not in stop_words]
    return keywords

def save_hashtags(hashtags):
    collection = db['hashtags']
    hashtags_on_db =  select_hasgtags_on_db()
    for hashtag_to_add in hashtags:
        found: False
        for hashtag_on_db in hashtags_on_db:
            if (hashtag_to_add == hashtag_on_db['hashtag']):
                collection.update_one({'hashtag':hashtag_to_add}, { "$set": { 'count': int(hashtag_on_db['count']) + 1 } })
                found = True
        if (not found):
            item = {
                'item_id': str(uuid.uuid4()),
                'hashtag': hashtag_to_add,
                'count': 1,
                'tweets': []
            }
            collection.insert_one(item)

def select_hasgtags_on_db():
    collection = db['hashtags']
    output_model = {}
    output_model['_id'] = False
    output_model['item_id'] = True
    output_model['hashtag'] = True
    output_model['count'] = True
    items = collection.find({}, output_model)
    return json.loads(json_util.dumps(items))

def search_tweets_and_store_on_db(content):
    hashtags = content['hashtags']
    since_date = content['since_date']
    until_date = content['until_date']
    collection = db['hashtags']
    docs = collection.find({'tweets.0': {'$exists': True}})
    fechas_distintas = set()
    for doc in docs:
        for tweet in doc['tweets']:
            fecha = tweet['created_at']
            fecha_fmt = fecha.strftime('%Y-%m-%d')
            fechas_distintas.add(fecha_fmt)
    fechas_distintas = sorted(list(fechas_distintas))
    fecha_inicial_valida = True
    fecha_final_valida = True
    if (since_date in fechas_distintas):
        fecha_inicial_valida = False
    if (until_date in fechas_distintas):
        fecha_final_valida = False
    if (fecha_inicial_valida and fecha_final_valida):
        for hashtag in hashtags:
            tweets = get_tweets_by_hashtag(hashtag, since_date, until_date)
            # q="#hashtag1 OR #hashtag2" es posible buscar varios hashtag a la vez y luego podemos clasificarlos
            collection.update_one({'hashtag':hashtag}, { "$push": { 'tweets': {'$each': tweets} } })
        return {'response':'success', 'status':200}
    else:
        write_log('Las fechas requeridas ya fueron analizadas anteriormente')
        return {'response':'Las fechas requeridas ya fueron analizadas anteriormente', 'status':400}

def hashtags():
    hashtags_on_db =  select_hasgtags_on_db()
    toReturn = []
    for item in hashtags_on_db:
        hashtag = {
            'text': item['hashtag'],
            'weight': item['count'],
            'rotate': random.randint(0,1) * 90
        }
        toReturn.append(hashtag)
    return {'response':toReturn, 'status':200}

def tweets():
    collection = db['hashtags']
    output_model = {}
    output_model['_id'] = False
    output_model['tweets'] = True
    hashtags = json.loads(json_util.dumps(collection.find({}, output_model)))
    tweets = []
    for hashtag in hashtags:
        tweets = tweets + hashtag['tweets']
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
                    'tweets': tweets,
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