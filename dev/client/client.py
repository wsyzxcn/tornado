# -*-encoding:utf-8 -*-
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
        self._serverConn = None
        self._assembler = Assembler()
        self._deviceConn = None
        self._assembler.registFrameListener(self.onFrameReady)

    def start(self):
        self._deviceConn = socket.socket()
        self._deviceConn.connect(('127.0.0.1', 13130))
        self._deviceConn.setblocking(False)
        fd = self._deviceConn.fileno()
        self._serverConn = socket.socket()
        self._serverConn.connect(('127.0.0.1', 8889))
        return fd

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
                    print 'exeed max:%s' % len(tmp)
                    break
            except socket.error as e:
               if e.errno == 10035:
                   break
        self._assembler.feed(tmp)


    def onFrameReady(self, frm):
        # print 'messge length:', len(msg)
        self._serverConn.send('1\n')
        self._serverConn.send('data-length:%s\n' % len(frm))
        self._serverConn.send(frm)



class Assembler(object):
    '''将从设备上读取的字节解析成图片桢'''
    def __init__(self):
        self._buff = ''
        self._frameReadyListenner = []
        self._isFirst = True
        self._frameSize = -1
        self._state = 'header'

    def feed(self, buf):
        self._buff += buf
        self._assemble()

    def _assemble(self):
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
                self._onFrameReady(self._buff[4:4+self._frameSize])
                self._buff = self._buff[4+self._frameSize:]
                self._frameSize = -1
                self._headerSize = -1

    def _onFrameReady(self, frame):
        for l in self._frameReadyListenner:
            l(frame)

    def registFrameListener(self, func):
        self._frameReadyListenner.append(func)




class Uploader():
    pass

if __name__ == '__main__':
    cap = Minicap()
    touch = Minitouch()
    p = subprocess.Popen("adb forward tcp:13130 localabstract:minicap", shell=True)
    p.wait()
    ioloop.IOLoop.current().add_handler(cap.start(),
                                        cap.onMessage, ioloop.IOLoop.READ+ioloop.IOLoop.ERROR)
    ioloop.IOLoop.current().start()