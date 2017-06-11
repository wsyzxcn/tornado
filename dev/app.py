import tornado
import tornado.ioloop as ioloop
import tornado.web as web
import tornado.websocket as websocket
import os

class MainHandler(web.RequestHandler):
    buff={}

    def get(self):
        if MainHandler.buff.get('index', None) is None:
            with open('./public/index.html', 'rb') as fd:
                s = fd.read(2048)
                MainHandler.buff['index'] = s
        self.write(MainHandler.buff['index'])


class WebSocketHandler(websocket.WebSocketHandler):
    def on_message(self, message):
        pass



def makeApp():
    return tornado.web.Application([(r"/", MainHandler),(r"/index.html", MainHandler)])
if __name__ == '__main__':
    app = makeApp()
    app.listen(8888)
    ioloop.IOLoop.current().start()
