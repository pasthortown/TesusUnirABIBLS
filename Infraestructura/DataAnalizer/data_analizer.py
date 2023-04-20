import os
from pymongo import MongoClient
from datetime import datetime
from bson import json_util
import json
from dateutil import parser
import random
import spacy
import nltk
import re
import logging
from collections import Counter

def write_log(content):
    logging.info(content)

mongo_bdd = os.getenv('mongo_bdd')
mongo_bdd_server = os.getenv('mongo_bdd_server')
mongo_user = os.getenv('mongo_user')
mongo_password = os.getenv('mongo_password')
app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

logging.basicConfig(filename='logs.txt', level=logging.DEBUG)

database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('spanish') + ['rt']
nlp = spacy.load('es_core_news_sm')

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
    for tweet in tweets_to_process:
        clasificacion = random.choice(['Xenofabia', 'Normal'])
        collection.update_one( {'_id': tweet['_id']}, {'$set': {'clasificado': clasificacion}} )

search_hashtags_from_tweets()
clasify_tweets()