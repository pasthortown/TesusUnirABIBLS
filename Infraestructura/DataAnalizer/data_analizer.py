import os
from pymongo import MongoClient
import datetime
from datetime import timedelta
from bson import json_util
import json
from dateutil import parser
import random
import spacy
import nltk
import re
import logging
from collections import Counter
import tensorflow as tf
import pandas as pd
import tweepy
import gender_guesser.detector as gender
from country_list import countries_for_language
import re
import time

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

logging.basicConfig(filename='logs.txt', level=logging.DEBUG)

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('spanish') + ['rt']
nlp = spacy.load('es_core_news_sm')

def hora_actual_entre_rango(inicio, fin):
    hora_actual = datetime.datetime.now().time()
    hora_inicio = datetime.time.fromisoformat(inicio)
    hora_fin = datetime.time.fromisoformat(fin)
    if hora_actual >= hora_inicio and hora_actual <= hora_fin:
        return True
    else:
        return False

def select_hasgtags_on_db():
    collection = db['tweets']
    pipeline = [
        { "$match": { "hashtags": { "$not": { "$size": 0 } }, "clasificado": "Xenofóbico" } },
        { "$project": { "_id": 0, "hashtags": 1 } },
        { "$unwind": "$hashtags" },
        { "$group": { "_id": "$hashtags", "count": { "$sum": 1 } } },
        { "$project": { "_id": 0, "hashtag": "$_id", "count": 1 } }
    ]
    hashtags = collection.aggregate(pipeline)
    return hashtags

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

def search_tweets_and_store_on_db(since_date, until_date):
    hashtags_on_db = select_hasgtags_on_db()
    hashtags = [h['hashtag'] for h in hashtags_on_db]
    collection = db['tweets']
    query = " OR #".join(["#" + hashtag for hashtag in hashtags])
    tweets = get_tweets_by_query(query, since_date, until_date)
    if len(tweets) > 0:
        result_mongo = collection.insert_many(tweets)

def search_keywords_in_text(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if not token.is_stop and token.is_alpha]
    keywords = [keyword.lower() for keyword in keywords if keyword.lower() not in stop_words]
    return keywords

def search_hashtags_from_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({'hashtags': []})
    for tweet in tweets_to_process:
        hashtags = search_keywords_in_text(tweet['text'])
        collection.update_one( {'_id': tweet['_id']}, {'$set': {'hashtags': hashtags}} )

def clasify_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({'clasificado': 'Pendiente'})
    tweets_to_train = collection.find({'clasificado': {'$ne': 'Pendiente'}})
    prediction_result = do_predictions(tweets_to_train, tweets_to_process)
    for result in prediction_result:
        collection.update_one({'_id': result['_id']}, {'$set': {'clasificado': result['clasificado']}})

def do_predictions(tweets_to_train, tweets_to_process):
    textos_nuevos = [tweet["text"] for tweet in tweets_to_process]
    textos = [tweet["text"] for tweet in tweets_to_train]
    etiquetas = [tweet["clasificado"] for tweet in tweets_to_train]
    tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=10000, oov_token="<OOV>")
    tokenizer.fit_on_texts(textos)
    secuencias_texto = tokenizer.texts_to_sequences(textos)
    secuencias_texto = tf.keras.preprocessing.sequence.pad_sequences(secuencias_texto, padding="post", maxlen=60)
    modelo = tf.keras.Sequential([
        tf.keras.layers.Embedding(input_dim=10000, output_dim=16, input_length=60),
        tf.keras.layers.LSTM(16),
        tf.keras.layers.Dense(1, activation="sigmoid")
    ])
    modelo.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
    historial = modelo.fit(secuencias_texto, etiquetas, epochs=10, validation_split=0.2)
    secuencias_texto_nuevos = tokenizer.texts_to_sequences(textos_nuevos)
    secuencias_texto_nuevos = tf.keras.preprocessing.sequence.pad_sequences(secuencias_texto_nuevos, padding="post", maxlen=50)
    predicciones = modelo.predict(secuencias_texto_nuevos)
    etiquetas_predichas_binarias = (predicciones > 0.5).astype(int)
    etiquetas_predichas_binarias = ['Xenofóbico' if x == 1 else 'Normal' for x in etiquetas_predichas_binarias]
    tweets_to_process['prediccion'] = etiquetas_predichas_binarias
    return tweets_to_process

def ennumerate_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({})
    count = 0
    for tweet in tweets_to_process:
        count = count + 1
        collection.update_one( {'_id': tweet['_id']}, {'$set': {'tweet_id': count}} )

def search_new_tweets():
    if hora_actual_entre_rango('22:00:00', '22:02:00'):
        fecha_actual = datetime.today().strftime('%Y-%m-%d')
        fecha_siguiente = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        search_tweets_and_store_on_db(fecha_actual, fecha_siguiente)
        time.sleep(3*60)

search_hashtags_from_tweets()
# clasify_tweets()
# ennumerate_tweets()