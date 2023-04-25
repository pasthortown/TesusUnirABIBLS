import tornado.ioloop
import tornado.web
from tornado_swagger.setup import setup_swagger
from tornado_swagger.swagger import SwaggerUIHandler

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")

class HelloWorldHandler(tornado.web.RequestHandler):
    def get(self):
        self.write({'hello': 'world'})

def make_app():
    app = tornado.web.Application([
        (r"/", MainHandler),
        (r"/hello", HelloWorldHandler),
        (r'/swagger/(.*)', SwaggerUIHandler),
    ])
    setup_swagger(app)
    return app

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()