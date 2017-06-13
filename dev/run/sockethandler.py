import socket
import tornado.ioloop as ioloop
import traceback
import re

class SocketHandler():

    def __init__(self):
        self._server = None
        self._socks = {}
        self._chunks = {}
        self.client = []

    def createSocketServer(self):
        serversocket = socket.socket()
        serversocket.bind(("", 8889))
        serversocket.listen(10)
        self._server = serversocket
        return serversocket.fileno()

    def onMessage(self, fd, evt):
        if evt == ioloop.IOLoop.READ:
            sock = self._socks[fd]
            LENGTH = 1024
            L = 1024
            buf = ''
            while LENGTH == L:
                s = sock.recv(LENGTH)
                L = len(s)
                buf = buf+s
            if buf:
                if not self._chunks.has_key(fd):
                    self._chunks[fd] = Chunk(self.client)
                self._chunks[fd].add(buf)
            else:
                self.onError(fd, evt)
        else:
            self.onError(fd, evt)

    def onError(self, fd, evt):
        sock = self._socks[fd]
        print 'an error accursed'
        try:
            ioloop.IOLoop.current().remove_handler(fd)
            sock.close()
            del self._socks[fd]
        except:
            print traceback.format_exc()

    def onConnection(self, fd, evt):
        sock, add = self._server.accept()
        self._socks[sock.fileno()] = sock
        sock.setblocking(False)
        ioloop.IOLoop.current().add_handler(sock.fileno(), self.onMessage, ioloop.IOLoop.READ+ioloop.IOLoop.ERROR)
        # ioloop.IOLoop.current().add_handler(sock.fileno(), self.onError, ioloop.IOLoop.ERROR)

    def addClient(self, client):
        self.client.append(client)

    def removeClient(self, client):
        self.client.remove(client)

class NotEnoughtData(Exception):
    pass

class Chunk():

    def __init__(self,clients):
        self._data = ''
        self._state = 'new'
        self._index = 0
        self._header = {}
        self._headerCount = 0
        self.clients = clients

    def data(self):
        return self._data

    def getNextLine(self):
        i = self._index
        print 'get line'
        while True:
            if i >= len(self._data):
                print 'should raise'
                raise NotEnoughtData()
            # print 'i:', i, len(self._data)
            if self._data[i] == '\n':
                print 'get line succeed'
                break
            i += 1
        while True:
            i += 1
            if i >= len(self._data):
                print 'should raise'
                raise NotEnoughtData()
            if self._data[i] != '\n':
                break
        old_index = self._index
        self._index = i
        return self._data[old_index:i-1]

    def onMessageComplete(self, message):
        print 'i got a message', len(message)
        for client in self.clients:
            client.write_message(message.encode('utf8'))

    def add(self, chunk):
        self._data = self._data+chunk
        try:
            while True:
                if self._state == 'new':
                    print 'status: new'
                    s = self.getNextLine()
                    print 's:', s
                    if not s.strip():
                        continue
                    self._headerCount = int(s)
                    self._state = 'header'
                elif self._state == 'header':
                    s = self.getNextLine()
                    if not s.strip():
                        continue
                    m = re.match("^([^:]*):([^:]*)$", s)
                    key = m.groups()[0]
                    value = m.groups()[1]
                    self._header[key] = value
                    if len(self._header.keys()) == self._headerCount:
                        self._state = 'data'
                elif self._state == 'data':
                    print self._index, len(self._data), self._header['data-length']
                    if len(self._data)-self._index < int(self._header['data-length']):
                        break
                    else:
                        print 'complete'
                        self.onMessageComplete(self._data[self._index:self._index+int(self._header['data-length'])])
                        self._data = self._data[self._index+int(self._header['data-length']):]
                        self._state = 'new'
                        self._headerCount = 0
                        self._header = {}
                        self._index = 0


        except NotEnoughtData:
            print 'not enough data'
        except:
            print traceback.format_exc()

