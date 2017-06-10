from tornado.gen import coroutine
from tornado import httpclient
from tornado.ioloop import IOLoop
from time import sleep
from tornado.gen import Future

@coroutine
def get():
    print 'get'
    response = yield httpclient.AsyncHTTPClient().fetch(r'http://www.baidu.com')
    # yield delaytask()
    print 'recv response'

def delaytask():
    sleep(2)
    return Future()

def test():
    print 'test'
if __name__ == '__main__':
    l = IOLoop.current()
    l.add_callback(get)
    l.add_callback(test)
    l.start()