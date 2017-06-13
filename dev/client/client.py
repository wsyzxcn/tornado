from tornado import ioloop
import subprocess
import socket
import struct
import os
import numpy as np
import cv2

class Minitouch():
    pass

class Minicap():

    def __init__(self):
        self._buff = ''
        self._state = 'header'
        self._headerSize = -1
        self._frameSize = -1
        self._isFirst = True
        self._toserversocket = None
        pass

    def start(self):
        s = socket.socket()
        s.connect(('127.0.0.1', 13130))
        s.setblocking(False)
        self._sock = s
        self._tested = False

        self._toserversocket = socket.socket()
        self._toserversocket.connect(('127.0.0.1', 8889))

        return s

    def onMessage(self, fd, evt):
        print 'new Message'
        tmp = ''
        while True:
            try:
                s = self._sock.recv(4096)
                tmp += s
                if len(s) < 4096:
                    break
                if len(tmp) > 1024 * 50:
                    print 'exeed max:%s'%len(tmp)
                    break
            except socket.error as e:
               if e.errno == 10035:
                   break


        self._buff += tmp
        self.handleMessage()

    def handleMessage(self):
        if self._isFirst:
            if len(self._buff) < 24:
                return
            else:
                print 'first time buf len:', len(self._buff)
                self._buff = self._buff[24:]
                print self._buff
                self._isFirst = False
        else:
            print len(self._buff)
            if len(self._buff) < 4:
                return
            if self._frameSize < 0:
                self._frameSize = struct.unpack('<I', self._buff[:4])[0]
                print('frame size: %s'%self._frameSize)
            if len(self._buff) < self._frameSize+4:
                return
            else:
                self.onMessageComplete(self._buff[4:4+self._frameSize])
                self._buff = self._buff[4+self._frameSize:]
                self._frameSize = -1
                self._headerSize = -1


    def onMessageComplete(self, msg):
        # print 'messge length:', len(msg)
        self._toserversocket.send('1')
        self._toserversocket('data-length:%s' % len(msg))
        self._toserversocket(msg)


        # if not self._tested:
        #     fd = os.open('result.jpg', os.O_CREAT|os.O_WRONLY)
        #     os.write(fd, msg)
        #     os.close(fd)
        #     self._tested = True
class Uploader():
    pass

if __name__ == '__main__':
    cap = Minicap()
    touch = Minitouch()
    p = subprocess.Popen("adb forward tcp:13130 localabstract:minicap", shell=True)
    p.wait()
    ioloop.IOLoop.current().add_handler(cap.start().fileno(),
                                        cap.onMessage, ioloop.IOLoop.READ+ioloop.IOLoop.ERROR)
    ioloop.IOLoop.current().start()