import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop
 
 
class EyeSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        pass
 
    def on_message(self, message):
        self.write_message(u"Your message was: " + message)
 
    def on_close(self):
        pass
 
 
class IndexPageHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("index.html")
 
 
class EyeApplication(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', IndexPageHandler),
            (r'/websocket', EyeSocketHandler)
        ]
 
        settings = {
            'template_path': 'templates'
        }
        tornado.web.Application.__init__(self, handlers, **settings)