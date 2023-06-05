import os
from tornado.ioloop import IOLoop
from tornado.web import Application, RequestHandler
from tornado.escape import json_decode
import datetime
import jwt
from dateutil import parser
import pdfkit
import jinja2
import base64
import qrcode
from io import BytesIO

app_secret = os.getenv('app_secret')
allowed_app_name = os.getenv('allowed_app_name')

# Levantamiento del API URL "/" HTTP: GET
class DefaultHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')

    def get(self):
        self.write({'response':'Servicio de Exportación de Documentos Operativo','status':200})

# Levantamiento del API HTTP: POST
class ActionHandler(RequestHandler):
    def set_default_headers(self):
        self.set_header('Access-Control-Allow-Origin', '*')
        self.set_header('Access-Control-Allow-Headers', '*')
        self.set_header('Access-Control-Allow-Methods', '*')
    
    def options(self, type):
        pass

    def post(self, type):
        content = json_decode(self.request.body)
        headers = self.request.headers
        token = headers['token']
        auth = validate_token(token)
        if auth == False:
            self.write({'response':'Acceso Denegado', 'status':'500'})
            return
        if (type == 'pdf'):
            params = content['params']
            template_name = content['template_name']
            respuesta = generate_pdf(template_name, params)
        if (type == 'qr'):
            toEncode = content['toEncode']
            respuesta = generate_qr(toEncode)
        self.write(respuesta)
        return

# Función que devuelve en Base64 el la imágen con el código QR generada a partir del texto recibido
def generate_qr(toEncode):
    buffered = BytesIO()
    img = qrcode.make(toEncode)
    img.save(buffered, format="JPEG")
    img_str = base64.b64encode(buffered.getvalue())
    return {'response': img_str.decode('utf-8'), 'status':200}

# Función que devuelve en Base64 un PDF generado a partir de los parámetros recibidos
def generate_pdf(template_name, params_in):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader('Templates'))
    params = params_in
    params['app_name']=allowed_app_name
    template = env.get_template(template_name)
    html_processed = template.render(params)
    toReturn = pdfkit.from_string(html_processed,False)
    return {'response': base64.b64encode(toReturn).decode('utf-8'), 'status':200}

# Validación del token JWT para autorizar la comunicación con el API
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