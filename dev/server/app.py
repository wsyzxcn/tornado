import tornado
import tornado.ioloop as ioloop
import tornado.web as web
import tornado.websocket as websocket
from run import transmitter
import traceback
import json

msgTransmitter = transmitter.Transmitter()

class MainHandler(web.RequestHandler):
    buff = {}

    def get(self):
        if True:
            with open('./public/index.html', 'rb') as fd:
                s = fd.read(2048)
                MainHandler.buff['index'] = s
        self.write(MainHandler.buff['index'])


class WebSocketHandler(websocket.WebSocketHandler):

    def open(self, *args, **kwargs):
        print 'a new connection'

    def on_close(self, *args, **kwargs):
        global msgTransmitter
        print 'disconnect ws'
        msgTransmitter.onWebHandlerDisconnect(self)

    def on_message(self, message):
        global msgTransmitter
        msgTransmitter.onwebHandlerMessage(self, message)



def makeApp():
    return tornado.web.Application([(r"/", MainHandler), (r"/index.html", MainHandler),
                                    (r"/connection", WebSocketHandler), ])
if __name__ == '__main__':
    app = makeApp()
    app.listen(8888)
    loop = ioloop.IOLoop.current()
    loop.add_handler(msgTransmitter.createSocketServer(), msgTransmitter._onDeviceSideConnection, ioloop.IOLoop.READ)
    ioloop.IOLoop.current().start()
