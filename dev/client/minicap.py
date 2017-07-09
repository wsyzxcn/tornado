# -*-encoding:utf-8 -*-
from tornado import ioloop
import subprocess
import socket
import struct
import os
import time
import re

_width = 0
_height = 0
_deviceId = None
_minicapProc = None
_rotation = 0
_cap = None
_loop = None
_server_addr = "www.staky.xin"

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
        self._fd = None

    def start(self):
        global _server_addr
        self._deviceConn = self._connectDevice()
        fd = self._deviceConn.fileno()
        self._fd = fd
        self._serverConn = socket.socket()
        self._serverConn.connect(("www.staky.xin", 8889))
        print 'connected'
        print fd
        return fd

    def _connectDevice(self):
        print "connect"
        con = socket.socket()
        retry = 0
        while True:
            try:
                con.connect(('127.0.0.1', 13130))
            except:
                retry += 1
                time.sleep(1)
                if retry > 5:
                    raise Exception("unable to connect service")
                    break
                else:
                    continue
            break
        return con

    def reConnectDevice(self):
        """"重新连接设备
        """
        global _loop
        self._deviceConn.shutdown(socket.SHUT_RDWR)
        _loop.remove_handler(self._fd)
        try:
            self._deviceConn = self._connectDevice()
            self._deviceConn.setblocking(False)
            fd = self._deviceConn.fileno()
            self._fd = fd
            self._assembler.clear()
            _loop.add_handler(fd, self.onMessage, ioloop.IOLoop.READ + ioloop.IOLoop.ERROR)
        except:
            pass

    def onMessage(self, fd, evt):
        global _loop
        if evt == ioloop.IOLoop.READ:
            tmp = ''
            while True:
                try:
                    s = self._deviceConn.recv(4096)
                    tmp += s
                    if len(s) < 4096:
                        break
                    if len(tmp) > 1024 * 50:
                        print 'exeed max:%s' % len(tmp)
                        break
                except socket.error as e:
                    if e.errno == 10035:
                        break
                    else:
                        self.reConnectDevice()
            self._assembler.feed(tmp)
        elif evt == ioloop.IOLoop.ERROR:
            _loop.remove_handler(self._fd)
            print "error"

    def onFrameReady(self, frm):
        # print 'messge length:', len(msg)
        self._serverConn.send('2\n')
        self._serverConn.send('data-length:%s\n' % len(frm))
        self._serverConn.send('deviceId:e5ae5af4\n')
        self._serverConn.send(frm)


class Assembler(object):
    '''将从设备上读取的字节解析成图片桢'''

    def __init__(self):
        self._buff = ''
        self._frameReadyListenner = []
        self._isFirst = True
        self._frameSize = -1
        self._state = 'header'
        self._isFirstFrame = True

    def feed(self, buf):
        self._buff += buf
        self._assemble()

    def clear(self):
        self._buff = ''
        self._isFirst = True
        self._state = 'header'
        self._frameSize = -1

    def _assemble(self):
        if self._isFirst:
            if len(self._buff) < 24:
                return
            else:
                self._buff = self._buff[24:]
                self._isFirst = False
        else:
            if len(self._buff) < 4:
                return
            if self._frameSize < 0:
                self._frameSize = struct.unpack('<I', self._buff[:4])[0]
            if len(self._buff) < self._frameSize + 4:
                return
            else:
                self._onFrameReady(self._buff[4:4 + self._frameSize])
                self._buff = self._buff[4 + self._frameSize:]
                self._frameSize = -1
                self._headerSize = -1

    def _onFrameReady(self, frame):
        if self._isFirstFrame:
            with open("result.jpg", "w+b") as fp:
                fp.write(frame)
                self._isFirstFrame = False
        for l in self._frameReadyListenner:
            l(frame)

    def registFrameListener(self, func):
        self._frameReadyListenner.append(func)


def onRotationChanged(rotation):
    global _deviceId, _minicapProc, _rotation, _loop
    if _rotation != rotation:
        _rotation = rotation
        _loop.add_callback(onRestart)


def killOldMinicap():
    _minicapProc, _deviceId
    if _minicapProc is not None:
        _minicapProc.kill()
    ret = subprocess.check_output("adb -s %s shell ps" % _deviceId)
    if ret:
        mobject = re.search("^[^\s]*\s*(\d+).*minicap\s*$", ret, re.M)
        if mobject:
            pid = int(mobject.groups()[0])
            subprocess.Popen("adb -s %s shell kill -s 9 %s" % (_deviceId, pid))


def onRestart():
    global _deviceId, _minicapProc, _rotation, _cap, _loop
    if _deviceId is None:
        raise ValueError("device id is not set")
    killOldMinicap()
    print "restart ", _rotation
    _minicapProc = subprocess.Popen(
        "adb -s %s shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P 1080x1920@450x800/%s"
        % (_deviceId, _rotation)
        , shell=True
    )
    _loop.call_later(1, _cap.reConnectDevice)


def start(deviceId, rotation):
    global _deviceId, _minicapProc, _cap, _loop, _rotation
    _deviceId = deviceId

    p = subprocess.Popen("adb -s %s forward tcp:13130 localabstract:minicap" % deviceId, shell=True)
    p.wait()
    output = subprocess.check_output(
        "adb -s %s shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P 1080x1920@450x800/0 -t" % deviceId)
    if output.find("OK") == -1:
        import sys
        print output
        print "device do not support by minicap"
        sys.exit(0)
    startCmd = "adb -s %s shell LD_LIBRARY_PATH=/data/local/tmp /data/local/tmp/minicap -P 1080x1920@450x800/%s" \
               % (deviceId, rotation)
    print startCmd
    print rotation
    _minicapProc = subprocess.Popen(
        startCmd, shell=True
    )
    cap = Minicap()
    _cap = cap
    _rotation = rotation
    time.sleep(1)
    ioloop.IOLoop.current().add_handler(cap.start(),
                                        cap.onMessage, ioloop.IOLoop.READ + ioloop.IOLoop.ERROR)
    _loop = ioloop.IOLoop.current()


def setResolution(width, height):
    global _width, _height
    _width = width
    _height = height
