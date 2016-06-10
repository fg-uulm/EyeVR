import tornado.web
import tornado.websocket
import tornado.httpserver
import tornado.ioloop 
 
wss = []

class EyeSocketHandler(tornado.websocket.WebSocketHandler):
	def open(self):
		print('WS Opened')
		if self not in wss:
			wss.append(self)
		pass
 
	def on_message(self, message):
		self.write_message(u"Your message was: " + message)
 
	def check_origin(self, origin):
		return True

	def on_close(self):
		print('WS Closed')
		if self in wss:
			wss.remove(self)
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
 
		settings = {}

		tornado.web.Application.__init__(self, handlers, **settings)

	def wsSend(self, message):
		for ws in wss:
			if not ws.ws_connection.stream.socket:
				print("Web socket does not exist anymore!!!")
				wss.remove(ws)
			else:
				ws.write_message(message)