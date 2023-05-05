# Importación las bibliotecas de Python necesarias para realizar tareas, entre las que podemos mencionar:
#  - Conexión con MongoDB
#  - Manipulación de fechas y horas
#  - Procesamiento de lenguaje natural
#  - La clasificación de texto
#  - Conexión al API de twitter 

import os
from pymongo import MongoClient
import datetime
from datetime import timedelta
import spacy
import nltk
import re
import logging
import tensorflow as tf
import tweepy
import gender_guesser.detector as gender
from country_list import countries_for_language
import re
import time
import numpy as np

class lossAlcanzadoCallback(tf.keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        if(logs.get('accuracy')> 0.90):
              logging.info("Alcanzado el 90% de precisión, se detiene el entrenamiento.")
              self.model.stop_training = True

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

api_key = os.getenv('twitter_api_key')
api_key_secret = os.getenv('twitter_api_key_secret')
access_token = os.getenv('twitter_access_token')
access_token_secret = os.getenv('twitter_access_token_secret')

# Configuración del logger
logging.basicConfig(filename='logs.txt', level=logging.DEBUG)

# Prueba de autenticación con Twitter
auth = tweepy.OAuth1UserHandler(api_key, api_key_secret, access_token, access_token_secret)
try:
    api = tweepy.API(auth)
    api.verify_credentials()
    write_log('Conexión a Twitter Exitosa')
except:
    write_log('Conexión a Twitter Fallida')

# Diccionario de países
countries = dict(countries_for_language('es'))

# Conexión a la base de datos de MongoDB
database_uri='mongodb://'+mongo_user+':'+mongo_password+'@'+ mongo_bdd_server +'/'
client = MongoClient(database_uri)
db = client[mongo_bdd]

# Descarga de paquetes y modelos de lenguaje
nltk.download('stopwords')
stop_words = nltk.corpus.stopwords.words('spanish') + ['rt', 'u']
nlp = spacy.load('es_core_news_sm')

# Función para verificar si la hora actual se encuentra entre un rango dado de horas
def hora_actual_entre_rango(inicio, fin):
    hora_actual = datetime.datetime.now().time()
    hora_inicio = datetime.time.fromisoformat(inicio)
    hora_fin = datetime.time.fromisoformat(fin)
    if hora_actual >= hora_inicio and hora_actual <= hora_fin:
        return True
    else:
        return False
    
# Función para obtener los hashtags de la base de datos de tweets clasificados como "Xenofóbico"
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

# Función para obtener tweets a partir de una consulta y almacenarlos en la base de datos
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

# Función encargada de actualizar los hashtags en la base de datos
def update_hashtags_on_db():
    hashtags_on_db = select_hasgtags_on_db()
    collection_h = db['hashtags']
    collection_h.drop()
    collection_h.insert_many(hashtags_on_db)
    
# Función encargada de buscar tweets por fecha y almacenarlos en la base de datos
def search_tweets_and_store_on_db(since_date, until_date):
    collection_h = db['hashtags']
    hashtags_on_db = collection_h.find({}).sort({'count': -1}).limit(20)
    hashtags = [h['hashtag'] for h in hashtags_on_db]
    collection = db['tweets']
    query = " OR #".join(["#" + hashtag for hashtag in hashtags])
    tweets = get_tweets_by_query(query, since_date, until_date)
    if len(tweets) > 0:
        result_mongo = collection.insert_many(tweets)

# Función encargada de buscar las palabras principales en un texto
def search_keywords_in_text(text):
    doc = nlp(text)
    keywords = [token.text for token in doc if not token.is_stop and token.is_alpha]
    keywords = [keyword.lower() for keyword in keywords if keyword.lower() not in stop_words]
    return keywords

# Función encargada de buscar hashtags en el texto de los tweets y almacenarlos en la base de datos
def search_hashtags_from_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({'hashtags': []})
    for tweet in tweets_to_process:
        hashtags = search_keywords_in_text(tweet['text'])
        collection.update_one( {'_id': tweet['_id']}, {'$set': {'hashtags': hashtags}} )

# Función encargada de clasificar los tweets según su contenido
def clasify_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({'clasificado': 'Pendiente'})
    if tweets_to_process.count() > 0:
        tweets_to_train = collection.find({'clasificado': {'$ne': 'Pendiente'}})
        prediction_result = do_predictions(tweets_to_train, tweets_to_process)
        for result in prediction_result:
            collection.update_one({'tweet_id': result['tweet_id']}, {'$set': {'clasificado': result['clasificado']}})
    else:
        write_log("No hay tweets pendientes para procesar")
        
# Función encargada de realizar predicciones sobre los tweets a clasificar
def do_predictions(tweets_to_train, tweets_to_process):
    # El arreglo textos_nuevos contendrá el texto de cada tweet a clasificar
    textos_nuevos = []
    # El arreglo to_return contendrá los indices de cada tweet y la clasificación realizada por la red neuronal.
    to_return = []
    for tweet in tweets_to_process:
        textos_nuevos.append(tweet["text"])
        to_return.append({'tweet_id': tweet["tweet_id"], 'clasificado': ''})
    # El arreglo textos_entrenamiento contendrá el texto de cada tweet de entrenamiento
    textos_entrenamiento = []
    # El arreglo etiquetas contendrá la etiqueta de cada tweet de entrenamiento clasificada como Xenofóbico = 1 o Normal = 0
    etiquetas = []
    for tweet in tweets_to_train:
        textos_entrenamiento.append(tweet["text"])
        if tweet["clasificado"] == "Xenofóbico":
            etiquetas.append(1)
        else:
            etiquetas.append(0)
    # Creamos un objeto Tokenizer de Keras que se utilizará para convertir los textos en secuencias de números enteros.
    tokenizer = tf.keras.preprocessing.text.Tokenizer(num_words=10000, oov_token="<OOV>")
    # Entrenamos el tokenizador en los textos de entrenamiento para construir un índice de vocabulario y asignar un número entero a cada palabra.
    tokenizer.fit_on_texts(textos_entrenamiento)
    # Convertimos los textos de entrenamiento en secuencias de números enteros utilizando el índice de vocabulario construido por el tokenizador.
    secuencias_texto = tokenizer.texts_to_sequences(textos_entrenamiento)
    # Ajustamos las secuencias de texto a una longitud máxima de 60 y rellena las secuencias más cortas con ceros.
    secuencias_texto = tf.keras.preprocessing.sequence.pad_sequences(secuencias_texto, padding="post", maxlen=60)
    # Convertimos secuencias_texto y etiquetas a un numpy_array para su utilización con tensorflow
    secuencias_texto = np.array(secuencias_texto)
    etiquetas = np.array(etiquetas)
    # Creamos un modelo secuencial de Keras con una capa de embedding, una capa LSTM y una capa densa con activación sigmoidal.
    modelo = tf.keras.Sequential([
        tf.keras.layers.Embedding(input_dim=10000, output_dim=16, input_length=60),
        tf.keras.layers.LSTM(16),
        tf.keras.layers.Dense(1, activation="sigmoid")
    ])
    # Compilamos el modelo con una función de pérdida de entropía cruzada binaria, un optimizador Adam y la métrica de precisión.
    modelo.compile(loss="binary_crossentropy", optimizer="adam", metrics=["accuracy"])
    # Entrenamos el modelo utilizando el 80% de los datos para su preparación y el 20% para la validación. Si la precisión obtenida es igual o superior al 90%, se detiene el entrenamiento con el fin de optimizar el proceso y prevenir el sobreentrenamiento.
    historial = modelo.fit(secuencias_texto, etiquetas, epochs=10, validation_split=0.2, callbacks=[lossAlcanzadoCallback()])
    # Guardamos el log correspondiente al resultado del entrenamiento.
    history_string = "Epoch\tLoss\tAccuracy\n"
    for epoch, loss, accuracy in zip(historial.epoch, historial.history['loss'], historial.history['accuracy']):
        history_string += f"{epoch}\t{loss:.4f}\t{accuracy:.4f}\n"
    write_log(history_string)
    # Entrenamos el tokenizador utilizando los textos nuevos para construir un índice de vocabulario y asignar un número entero a cada palabra.
    secuencias_texto_nuevos = tokenizer.texts_to_sequences(textos_nuevos)
    # Ajustamos las secuencias de textos nuevos a una longitud máxima de 60 y se rellenan las secuencias más cortas con ceros.
    secuencias_texto_nuevos = tf.keras.preprocessing.sequence.pad_sequences(secuencias_texto_nuevos, padding="post", maxlen=60)
    # Procedemos a clasificar los textos_nuevos mediante la red neuronal previamente entrenada. La predicción para cada texto será una probabilidad y si esta es alta (cerca de 1), se considerará que el tweet es xenofóbico.
    predicciones = modelo.predict(secuencias_texto_nuevos)
    # Asociamos la etiqueta Xenofóbico si la predicción es superior a 0.5 caso contrario la etiqueta asociada sera Normal
    etiquetas_predichas_binarias = (predicciones > 0.5).astype(int)
    etiquetas_predichas = ['Xenofóbico' if x == 1 else 'Normal' for x in etiquetas_predichas_binarias]
    # Agregamos una columna denominada prediccion al listado de tweets a procesar que contiene la clasificación realizada
    index = 0
    for tweet in to_return:
        tweet['clasificado'] = etiquetas_predichas[index]
        index = index + 1
        write_log(str(tweet['tweet_id']) + ' ' + tweet['clasificado'])
    return to_return

# Función para enumerar los tweets presentes en la base de datos
def ennumerate_tweets():
    collection = db['tweets']
    tweets_to_process = collection.find({})
    count = 0
    for tweet in tweets_to_process:
        count = count + 1
        collection.update_one( {'_id': tweet['_id']}, {'$set': {'tweet_id': count}} )

# Función para iniciar la búsqueda de los tweets que han sido generados en el día cuando se cumple la condición de horario
def search_new_tweets():
    if hora_actual_entre_rango('22:50:00', '22:52:00'):
        fecha_actual = datetime.today().strftime('%Y-%m-%d')
        fecha_siguiente = (datetime.today() + timedelta(days=1)).strftime('%Y-%m-%d')
        search_tweets_and_store_on_db(fecha_actual, fecha_siguiente)
        update_hashtags_on_db()
        time.sleep(3*60)

def log_hashtags():
    collection_h = db['hashtags']
    hashtags_on_db = collection_h.find({}).sort([('count', -1)]).limit(20)
    hashtags = [h['hashtag'] for h in hashtags_on_db]
    hashtag_list = "\"".join([", \"" + hashtag for hashtag in hashtags])
    write_log('Hashtags:')
    write_log(hashtag_list)

clasify_tweets()
search_hashtags_from_tweets()
update_hashtags_on_db()
log_hashtags()
ennumerate_tweets()
#search_new_tweets()