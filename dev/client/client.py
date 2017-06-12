from tornado import ioloop
import subprocess
import socket
import struct

class Minitouch():
    pass

class Minicap():

    def __init__(self):
        self._buff = ''
        self._state = 'header'
        self._headerSize = -1
        self._frameSize = -1
        self._isFirst = True
        pass

    def start(self):
        s = socket.socket()
        s.connect(('127.0.0.1', 13130))
        s.setblocking(False)
        self._sock = s
        return s

    def onMessage(self, fd, evt):
        tmp = ''
        while True:
            s = self._sock.recv(1024)
            tmp += s
            if len(s)<1024:
                break
        self._buff += tmp
        self.handleMessage()
        pass

    def handleMessage(self):
        if self._isFirst:
            if len(self._buff) < 24:
                return
            else:
                self._buff = self._buff[24:]
        else:
            if len(self._buff) < 4:
                return
            if self._frameSize < 0:
                self._frameSize = struct.unpack('<I', self._buff[0:4])
            if len(self._buff) < self._frameSize+4:
                return
            else:
                self.onMessageComplete(self._buff[4:4+self._frameSize])
                self._buff = self._buff[4+self._frameSize:]
                self._frameSize = -1
                self._headerSize = -1


    def onMessageComplete(self, msg):
        print 'messge length:', len(msg)

class Uploader():
    pass

if __name__ == '__main__':
    cap = Minicap()
    touch = Minitouch()
    p = subprocess.Popen("./libs/adb/adb forward tcp:13130 localabstract:minicap")
    p.wait()
    ioloop.IOLoop.current().add_handler(cap.start(),
                                        cap.onMessage, ioloop.IOLoop.READ+ioloop.IOLoop.ERROR)
