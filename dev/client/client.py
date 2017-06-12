from tornado import ioloop
import subprocess
import socket
import struct
import os

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
        self._tested = False
        return s

    def onMessage(self, fd, evt):
        print 'new Message'
        tmp = ''
        while True:
            try:
                s = self._sock.recv(1024)
            except socket.error as e:
               if e.errno == 10035:
                   continue
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
                self._isFirst = False
        else:
            print len(self._buff)
            if len(self._buff) < 4:
                return
            if self._frameSize < 0:
                self._frameSize = struct.unpack('<I', self._buff[0:4])[0]
            if len(self._buff) < self._frameSize+4:
                return
            else:
                self.onMessageComplete(self._buff[4:4+self._frameSize])
                self._buff = self._buff[4+self._frameSize:]
                self._frameSize = -1
                self._headerSize = -1


    def onMessageComplete(self, msg):
        print 'messge length:', len(msg)
        if not self._tested:
            fd = os.open('result.jpg', os.O_CREAT|os.O_WRONLY)
            os.write(fd, msg)
            os.close(fd)
            self._tested = True

class Uploader():
    pass

if __name__ == '__main__':
    cap = Minicap()
    touch = Minitouch()
    p = subprocess.Popen("adb forward tcp:13130 localabstract:minicap")
    p.wait()
    ioloop.IOLoop.current().add_handler(cap.start().fileno(),
                                        cap.onMessage, ioloop.IOLoop.READ+ioloop.IOLoop.ERROR)
    ioloop.IOLoop.current().start()