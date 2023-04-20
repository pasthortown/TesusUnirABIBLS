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
import random
import tweepy
import gender_guesser.detector as gender
from country_list import countries_for_language
import re
import logging
from collections import defaultdict

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

def get_tweets_by_query(query, since_date, until_date, items_count=100):
    tweets = tweepy.Cursor(api.search_tweets, q=query, lang="es", since_id=since_date, until=until_date).items(int(items_count))
    output = []
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
            'hashtags': [],
            'clasificado': 'Pendiente'
        })
    return output

def search_tweets_and_store_on_db(content):
    hashtags = content['hashtags']
    collection = db['tweets']
    since_date = content['since_date']
    until_date = content['until_date']
    query = " OR #".join(["#" + hashtag for hashtag in hashtags])
    tweets = get_tweets_by_query(query, since_date, until_date)
    if len(tweets) > 0:
        result_mongo = collection.insert_many(tweets)
    return {'response':'success', 'status':200}

def select_hasgtags_on_db():
    collection = db['tweets']
    pipeline = [
        { "$match": { "hashtags": { "$not": { "$size": 0 } }, "clasificado": "Xenofabia" } },
        { "$project": { "_id": 0, "hashtags": 1 } },
        { "$unwind": "$hashtags" },
        { "$group": { "_id": "$hashtags", "count": { "$sum": 1 } } },
        { "$project": { "_id": 0, "hashtag": "$_id", "count": 1 } }
    ]
    hashtags = collection.aggregate(pipeline)
    return hashtags

def hashtags():
    hashtags_on_db =  select_hasgtags_on_db()
    toReturn = [{'text': h['hashtag'], 'weight': h['count'], 'rotate': i % 2 * 90} for i, h in enumerate(hashtags_on_db)]
    return {'response':toReturn, 'status':200}

def get_tweets_from_db():
    collection = db['tweets']
    meses = [ "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre" ]
    pipeline = [
        { "$match": { "clasificado": "Xenofabia" } },
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

def build_tweets_by_gender(list_tweets):
    radarChartDatasets = []
    genders = list(set([str(tweet["user_gender"]).upper() for tweet in list_tweets]))
    paises = list(set([str(tweet["pais"]).upper() for tweet in list_tweets]))
    for gender in genders:
        data = []
        for pais in paises:
            cuenta_tweets = sum(1 for tweet in list_tweets if str(tweet["pais"]).upper() == str(pais).upper() and tweet["user_gender"] == gender)
            data.append(cuenta_tweets)
        dataset = {'data': data, 'label': str(gender)}
        radarChartDatasets.append(dataset)
    return radarChartDatasets

def get_current_month_tweets(list_tweets):
    current_month = date.today().month
    current_year = date.today().year
    current_month_tweets = []
    for tweet in list_tweets:
        if tweet["month"] == current_month and tweet["year"] == current_year:
            current_month_tweets.append(tweet)
    return current_month_tweets

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