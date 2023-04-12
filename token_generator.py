import jwt
import datetime
import string
import random

def generate_token():
    exp_time = datetime.datetime.now() + datetime.timedelta(days = 3650)
    payload = { 'app_name':'TESIS-UNIR', 'valid_until': str(exp_time) }
    secret = ''.join(random.choices(string.ascii_uppercase + string.digits, k=20))
    print(secret + '\n')
    return jwt.encode(payload, secret, algorithm='HS256')

print(generate_token())