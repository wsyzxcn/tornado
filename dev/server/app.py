import tornado
import tornado.ioloop as ioloop
import tornado.web as web
import tornado.websocket as websocket
from run import sockethandler

sockHandler = sockethandler.SocketHandler()

class MainHandler(web.RequestHandler):
    buff={}

    def get(self):
        if True:
            with open('./public/index.html', 'rb') as fd:
                s = fd.read(2048)
                MainHandler.buff['index'] = s
        self.write(MainHandler.buff['index'])


class WebSocketHandler(websocket.WebSocketHandler):

    def open(self, *args, **kwargs):
        print 'a new connection'
        global sockHandler
        sockHandler.addClient(self)

    def close(self, *args, **kwargs):
        global sockethandler
        sockHandler.removeClient(self)
    # def get(self):
    #     self.write("this is websocket handler")

    def on_message(self, message):
        print 'new message', message



def makeApp():
    return tornado.web.Application([(r"/", MainHandler), (r"/index.html", MainHandler),
                                    (r"/connection", WebSocketHandler),])
if __name__ == '__main__':
    app = makeApp()
    app.listen(8888)

    loop = ioloop.IOLoop.current()
    loop.add_handler(sockHandler.createSocketServer(), sockHandler.onConnection, ioloop.IOLoop.READ)
    ioloop.IOLoop.current().start()
