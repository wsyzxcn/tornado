from tornado import ioloop

def func():
    print 'executed'

if __name__ == '__main__':
    l = ioloop.IOLoop.current()
    l.add_callback(func)
    print type(l)
    l.start()
