import tornado.ioloop
import tornado.web
import tornado.websocket
import tornado.httpserver
import jsonpickle
import cv2
import base64
import settings as s


cl = []

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.write("Hello, world")


class WebSocketHandler(tornado.websocket.WebSocketHandler):
    def open(self):
        s.logAppend("Connection opened")
        if self not in cl:
            cl.append(self)

    def on_close(self):
        s.logAppend("Connection closed")
        if self in cl:
            cl.remove(self)

    def on_message(self, message):
        # byte decode
        try:
            message = message.decode("utf-8")
        except:
            if(s.DEBUG):
                print("Decode failed")

        # request raw image
        if message == "imgraw":
            imgjpg = cv2.imencode('.jpg', s.OUT_IMGRAW)[1].tostring()
            imgb64 = base64.b64encode(imgjpg).decode('ascii')
            response = {"type": "imgraw", "data": imgb64}
            try:
                self.write_message(jsonpickle.encode(response))
            except tornado.websocket.WebSocketClosedError:
                print("websocket coding error")

        # request preprocessed / cropped image
        elif message == "imgproc":
            imgjpg = cv2.imencode('.jpg', s.OUT_IMGPROC)[1].tostring()
            imgb64 = base64.b64encode(imgjpg).decode('ascii')
            response = {"type": "imgproc", "data": imgb64}
            try:
                self.write_message(jsonpickle.encode(response))
            except tornado.websocket.WebSocketClosedError:
                print("Websocket encoding error")

        # request tracking data
        elif message == "track":
            response = {"type": "track", "data": s.OUT_TRACKDATA}
            try:
                self.write_message(jsonpickle.encode(response))
            except tornado.websocket.WebSocketClosedError:
                print("Websocket encoding error")

        # request all settings
        elif message == "settings":
            response = {"type": "settings", "data": s.SETTINGS}
            try:
                self.write_message(jsonpickle.encode(response))
            except tornado.websocket.WebSocketClosedError:
                print("Websocket encoding error")

        elif message == "log":
            response = {"type": "log", "data": s.LOGS}
            try:
                self.write_message(jsonpickle.encode(response))
                s.LOGS = {} #reset log lines
            except tornado.websocket.WebSocketClosedError:
                print("Websocket encoding error")

        elif message == "writeloop":
            try:
                s.FRMPROV.loopToFile()
            except:
                print("File writing error!")

        else:
            print("Unsupported function: " + str(message))


class IndexHandler(tornado.web.RequestHandler):
    def get(self):
        self.render("../web/eyevr_debug.html", port=8082)


class PostSettingHandler(tornado.web.RequestHandler):
    def post(self):
        s.logAppend("POST request!")
        s.logAppend("Currently "+str(len(s.SETTINGS))+" settings known")

        for item1 in s.SETTINGS:
            s.logAppend("Known Setting: " + item1 + ", current value: " + str(s.SETTINGS[item1]) + ", current type: " + str(type(s.SETTINGS[item1])))

        try:
            dataSettings = {}
            tempDict = []
            data = tornado.escape.json_decode(self.request.body)

            for item in data:
                tempDict = item
                s.logAppend("Conversion of value " + str(tempDict["value"]) + " for " + str(tempDict["name"]) + " to type " + repr(type(s.SETTINGS[str(tempDict["name"])])))
                try:
                    newVal = convert(str(tempDict["value"]), type(s.SETTINGS[str(tempDict["name"])]))
                    s.logAppend("Successfully converted, writing...")
                    if(str(tempDict["name"]) != "mode"):
                        s.SETTINGS[str(tempDict["name"])] = newVal
                    else:
                        if(newVal != s.SETTINGS["mode"]):
                            s.FRMPROV.switchMode(newVal)
                    s.logAppend("Successfully written")
                except Exception as e:
                    s.logAppend("Settings type conversion or write failed: "+str(e))

        except Exception as e:
            s.logAppend("Settings decoding error: "+str(e))


def make_app():
    print("Serving static files from: "+s.ROOT)
    return tornado.web.Application([
            (r"/", IndexHandler),
            (r"/websocket", WebSocketHandler),
            (r"/setting", PostSettingHandler),
            (r'/static/(.*)', tornado.web.StaticFileHandler, {'path': s.ROOT+'/web'})
    ], compiled_template_cache=False)


def convert(value, type_):
    import importlib
    s.logAppend("Got type str("+repr(type_)+")")

    # Special case - bool
    if(str(type_.__name__) == "bool"):
        if(value == "True" or value == "true"):
            return True
        else:
            return False

    # All other datatypes
    try:
        # Check if it's a builtin type
        module = importlib.import_module('builtins')
        cls = getattr(module, str(type_.__name__))
    except AttributeError as e:
        s.logAppend("AttError: "+str(e))
        # if not, separate module and class
        module, type_ = type_.rsplit(".", 1)
        module = importlib.import_module(module)
        cls = getattr(module, str(type_.__name__))
    return cls(value)