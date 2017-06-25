import subprocess
import threading
import re
import time

class _Observer(threading.Thread):

    def __init__(self):
        self._started = False
        self._curRotation = 0
        self._rotationListener = []
        super(_Observer, self).__init__()

    def start(self):
        self._started = True
        super(_Observer, self).start()

    def run(self):
        while self._started:
            time.sleep(1)
            self._observeRotation()

    def stop(self):
        self._started = False

    def _observeRotation(self):
        """
        get display rotation, rotation is represented as 0,90,180,270, while 0 is original display orientation
        :return:rotation of device
        """
        rotation = self._curRotation
        output = subprocess.check_output("adb -d shell dumpsys display")
        if output:
            m = re.search("^\s*mCurrentOrientation\s*=\s*(\d+)", output, re.M)
            if m:
                rotation = int(m.groups()[0])*90
        if rotation!=self._curRotation:
            self._updateRotation(rotation)

    def _updateRotation(self, rotation):
        for l in self._rotationListener:
            l(rotation)
        self._curRotation = rotation

    def registRotLstnr(self, l):
        self._rotationListener.append(l)

    def unregistRotLstnr(self, l):
        self._rotationListener.remove(l)

_observerInstance = _Observer()

def registRotLstnr(listener):
    global _observerInstance
    _observerInstance.registRotLstnr(listener)

def unregistRotLstnr(listener):
    global _observerInstance
    _observerInstance.unregistRotLstnr(listener)

def start(deviceId):
    global  _observerInstance
    if not _observerInstance:
        _observerInstance = _Observer()
    _observerInstance.start()

def stop():
    global _observerInstance
    _observerInstance.stop()

if __name__ == '__main__':
    o = _Observer()
    o._getRotation()