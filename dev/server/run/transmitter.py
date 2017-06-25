# -*-encoding:utf8-*-
import socket
import tornado.ioloop as ioloop
import traceback
import re
import json


class Transmitter(object):
    """transmit message between web page and local client connected to the phone"""

    def __init__(self):
        self._server = None
        self._deviceSideConnections = {}
        self._chunks = {}
        self.webSocketHandlers = {}

    def createSocketServer(self):
        serversocket = socket.socket()
        serversocket.bind(("", 8889))
        serversocket.listen(10)
        self._server = serversocket
        return serversocket.fileno()

    def _onDeviceSideReadable(self, fd, evt):
        if evt == ioloop.IOLoop.READ:
            sock = self._deviceSideConnections[fd]
            LENGTH = 1024
            L = 1024
            buf = ''
            s = ''
            while LENGTH == L:
                try:
                    s = sock.recv(LENGTH)
                except socket.error as e:
                    if e.errno == 10035:
                        break
                    else:
                        self._deviceSideDisconnect(fd)
                        break
                L = len(s)
                buf = buf+s
            if buf:
                if not self._chunks. has_key(fd):
                    self._chunks[fd] = MessageAssembler()
                    self._chunks[fd].registMessageReadyListenner(self.msgListenner)
                try:
                    self._chunks[fd].add(buf)
                except ValueError:
                    print 'Unexpected Message content!!'
                    self._deviceSideDisconnect(fd)
            else:
                self.onError(fd, evt)
        else:
            self.onError(fd, evt)

    def _deviceSideDisconnect(self, fd):
        ioloop.IOLoop.current().remove_handler(fd)
        if fd in self._chunks:
            del self._chunks[fd]
        try:
            del self._deviceSideConnections[fd]
            self._deviceSideConnections[fd].close()
        except:
            traceback.print_stack()

    def onError(self, fd, *args):
        print 'error'
        self._deviceSideDisconnect(fd)

    def _onDeviceSideConnection(self, fd, evt):
        sock, add = self._server.accept()
        self._deviceSideConnections[sock.fileno()] = sock
        sock.setblocking(False)
        ioloop.IOLoop.current().add_handler(sock.fileno(), self._onDeviceSideReadable, ioloop.IOLoop.READ + ioloop.IOLoop.ERROR)

    def addWebSocketClient(self, deviceId, client):
        if deviceId not in self.webSocketHandlers:
            self.webSocketHandlers[deviceId] = []
        self.webSocketHandlers[deviceId].append(client)
        print 'add client %s' % deviceId


    def removeClient(self, client):
        self.webSocketHandlers.remove(client)

    def msgListenner(self, deviceId, msg):
        if deviceId in self.webSocketHandlers:
            for client in self.webSocketHandlers[deviceId]:
                client.write_message(msg, binary=True)

    def onwebHandlerMessage(self,webHandler, message):
        try:
            obj = json.loads(message)
            cmd = obj['cmd']
            deviceId = obj['deviceId']
            if cmd == 'init':
                self.addWebSocketClient(deviceId, webHandler)
        except:
            traceback.print_stack()

    def onWebHandlerDisconnect(self, webHandler):
        for deviceId in self.webSocketHandlers:
            for wh in self.webSocketHandlers[deviceId]:
                if wh == webHandler:
                    self.webSocketHandlers[deviceId].remove(wh)


class NotEnoughtData(Exception):
    pass


class MessageAssembler(object):
    """
    从客户端发送过来的截图桢信息可能一次性读不完， 每次socket可读的时候将数据独取出来， 并把数据交给本类的一个实例。
    本类每次接收到新的数据时将会检测是否有一次完整的数据包， 如果存在的话就除法一个消息接受完成的事件。
    """

    def __init__(self):
        self._data = ''
        self._state = 'new'
        self._index = 0
        self._header = {}
        self._headerCount = 0
        self._msgListenner = []
        self._deviceId = ''
        self.times = 0

    def _data(self):
        return self._data

    def _getNextLine(self):
        i = self._index
        while True:
            if i >= len(self._data):
                raise NotEnoughtData()
            if self._data[i] == '\n':
                break
            i += 1
        while True:
            i += 1
            if i >= len(self._data):
                raise NotEnoughtData()
            if self._data[i] != '\n':
                break
        old_index = self._index
        self._index = i
        return self._data[old_index:i-1]

    def _onMessageComplete(self, frm):
        self.times += 1
        for l in self._msgListenner:
            l(self._deviceId, frm)

    def registMessageReadyListenner(self, func):
        self._msgListenner.append(func)

    def unregistMessageListenner(self, func):
        self._msgListenner.remove(func)

    def add(self, chunk):
        self._data = self._data+chunk
        try:
            while True:
                if self._state == 'new':
                    s = self._getNextLine()
                    if not s.strip():
                        continue
                    self._headerCount = int(s)
                    self._state = 'header'
                elif self._state == 'header':
                    s = self._getNextLine()
                    if not s.strip():
                        continue
                    m = re.match("^([^:]*):([^:]*)$", s)
                    key = m.groups()[0]
                    value = m.groups()[1]
                    self._header[key] = value
                    if len(self._header.keys()) == self._headerCount:
                        if 'deviceId' in self._header:
                            self._deviceId = self._header['deviceId']
                        self._state = 'data'
                elif self._state == 'data':
                    if len(self._data)-self._index < int(self._header['data-length']):
                        break
                    else:
                        self._onMessageComplete(self._data[self._index:self._index + int(self._header['data-length'])])
                        self._data = self._data[self._index+int(self._header['data-length']):]
                        self._state = 'new'
                        self._headerCount = 0
                        self._header = {}
                        self._index = 0


        except NotEnoughtData:
            pass
        except ValueError:
            raise
        except:
            traceback.print_stack()

