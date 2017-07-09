# -*-encoding:utf8-*-
import subprocess
import re
import sys
import devicestateobserver
import os
import minicap
from tornado import ioloop


def _checkDeviceConnected():
    output = subprocess.check_output("adb devices")
    if output:
        resultList = re.findall("^\s*(.*)\s*device\s*$", output, re.M)
        print type(resultList[0])
        if resultList:
            if len(resultList) > 1:
                print "more than one device detected, use the first one list by cmd adb devices"
            return resultList[0]
        else:
            print "no device detected"
            sys.exit(0)


def _prepareEnvirion(deviceId):
    """
    将对应的minicap版本推送到手机上
    :return:
    """
    abiresult = subprocess.check_output("adb -s %s shell getprop ro.product.cpu.abi"%deviceId)
    abi = abiresult.strip()
    sdkresult = subprocess.check_output("adb -s %s shell getprop ro.build.version.sdk"%deviceId)
    sdk = sdkresult.strip()
    binaryPath = os.path.join(".", "libs", "minicaplib", abi, "minicap")
    p = subprocess.Popen("adb -s %s push %s /data/local/tmp"%(deviceId, binaryPath))
    p.wait()
    soPath = os.path.join(".", "libs", "minicaplib", "android-%s"%sdk, abi, "minicap.so")
    p = subprocess.Popen("adb -s %s push %s /data/local/tmp"%(deviceId, soPath))
    p.wait()
    p = subprocess.Popen("adb -s %s shell chmod 777 /data/local/tmp/minicap"%deviceId)
    p.wait()


def _getResolution(deviceId):
    width, height = 0, 0
    result = subprocess.check_output("adb -s %s shell wm size"%deviceId)
    m = re.search("(\d+)x(\d+)", result)
    if m:
        width = int(m.groups()[0])
        height = int(m.groups()[1])
    return width, height


def _getRotation():
    rotation = 0
    output = subprocess.check_output("adb -d shell dumpsys display")
    if output:
        m = re.search("^\s*mCurrentOrientation\s*=\s*(\d+)", output, re.M)
        if m:
            rotation = int(m.groups()[0]) * 90
    return rotation


def initiate():
    deviceId = _checkDeviceConnected()
    print deviceId
    _prepareEnvirion(deviceId)
    devicestateobserver.start(deviceId)
    devicestateobserver.registRotLstnr(minicap.onRotationChanged)
    width, height = _getResolution(deviceId)
    minicap.setResolution(width, height)
    rotation = _getRotation()
    minicap.start(deviceId, rotation)
    print 'init finished'
    ioloop.IOLoop.current().start()

if __name__ == '__main__':
    initiate()