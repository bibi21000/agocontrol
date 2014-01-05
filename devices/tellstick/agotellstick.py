#! /usr/bin/env python
# -*- coding: utf-8 -*-
"""
     Copyright (C) 2013 Sebastien GALLET <bibi21000@gmail.com>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

     Install telldus-core : http://developer.telldus.com/wiki/TellStickInstallationUbuntu

"""
import sys,os
try :
    sys.path.insert(0, os.path.abspath('/opt/agocontrol/bin/'))
    sys.path.insert(0, os.path.abspath('../../../agocontrol/shared'))
except:
    pass
import syslog
import time
from datetime import datetime
import threading
from threading import Timer
import agoclient
from ctypes import c_int, c_ubyte, c_void_p, POINTER, string_at, c_char_p
from ctypes.util import find_library
from ctypes import cdll, CFUNCTYPE
import traceback

def log_exception(exc):
    for line in exc.split('\n'):
        if len(line):
            syslog.syslog(syslog.LOG_ERR, line)

# Device methods
TELLSTICK_TURNON = 1
TELLSTICK_TURNOFF = 2
TELLSTICK_BELL = 4
TELLSTICK_TOGGLE = 8
TELLSTICK_DIM = 16
TELLSTICK_LEARN = 32
TELLSTICK_EXECUTE = 64
TELLSTICK_UP = 128
TELLSTICK_DOWN = 256
TELLSTICK_STOP = 512
#Sensor value types
TELLSTICK_TEMPERATURE = 1
TELLSTICK_HUMIDITY = 2
TELLSTICK_RAINRATE = 4
TELLSTICK_RAINTOTAL = 8
TELLSTICK_WINDDIRECTION = 16
TELLSTICK_WINDAVERAGE = 32
TELLSTICK_WINDGUST = 64
#Error codes
TELLSTICK_SUCCESS = 0
TELLSTICK_ERROR_NOT_FOUND = -1
TELLSTICK_ERROR_PERMISSION_DENIED = -2
TELLSTICK_ERROR_DEVICE_NOT_FOUND = -3
TELLSTICK_ERROR_METHOD_NOT_SUPPORTED = -4
TELLSTICK_ERROR_COMMUNICATION = -5
TELLSTICK_ERROR_CONNECTING_SERVICE = -6
TELLSTICK_ERROR_UNKNOWN_RESPONSE = -7
TELLSTICK_ERROR_SYNTAX = -8
TELLSTICK_ERROR_BROKEN_PIPE = -9
TELLSTICK_ERROR_COMMUNICATING_SERVICE = -10
TELLSTICK_ERROR_UNKNOWN = -99
#Device typedef
TELLSTICK_TYPE_DEVICE = 1
TELLSTICK_TYPE_GROUP = 2
TELLSTICK_TYPE_SCENE = 3
#Device changes
TELLSTICK_DEVICE_ADDED = 1
TELLSTICK_DEVICE_CHANGED = 2
TELLSTICK_DEVICE_REMOVED = 3
TELLSTICK_DEVICE_STATE_CHANGED = 4
#Change types
TELLSTICK_CHANGE_NAME = 1
TELLSTICK_CHANGE_PROTOCOL = 2
TELLSTICK_CHANGE_MODEL = 3
TELLSTICK_CHANGE_METHOD = 4
TELLSTICK_CHANGE_AVAILABLE = 5
TELLSTICK_CHANGE_FIRMWARE = 6
#Controller typedef
TELLSTICK_CONTROLLER_TELLSTICK = 1
TELLSTICK_CONTROLLER_TELLSTICK_DUO = 2
TELLSTICK_CONTROLLER_TELLSTICK_NET = 3
#From http://developer.telldus.se/wiki/TellStick_conf
TELLDUS_MODELS = {
    'arctech' : {
        'codeswitch' : ['house','unit'],
        'bell': ['house'],
        'selflearning-switch': ['house','unit'],
        'selflearning-dimmer': ['house','unit'],
    },
    'brateck' : {
        'brateck' : ['house'],
    },
    'everflourish' : {
        'everflourish' : ['house','unit'],
    },
    'fuhaote' : {
        'fuhaote' : ['code'],
    },
    'hasta' : {
        'hasta' : ['house','unit'],
    },
    'brateck' : {
        'brateck' : ['house'],
    },
    'ikea' : {
        'ikea' : ['system','units','fade'],
    },
    'risingsun' : {
        'codeswitch' : ['house','unit'],
        'selflearning': ['house','unit'],
    },
    'sartano' : {
        'sartano' : ['code'],
    },
    'silvanchip' : {
        'ecosavers' : ['house','unit'],
        'kp100': ['house'],
    },
    'upm' : {
        'upm' : ['house','unit'],
    },
    'waveman' : {
        'waveman' : ['house','unit'],
    },
    'x10' : {
        'x10' : ['house','unit'],
    },
    'yidong' : {
        'yidong' : ['unit'],
    },
}
timers = {} #timerlist

def sensor_callback(protocol, model, id, dataType, value, timestamp, callbackId, context):
    print "Sensor:", string_at(protocol), string_at(model), "id:", id
    if(dataType == TELLSTICK_TEMPERATURE):
            print "Temperature:", string_at(value), "C,", datetime.fromtimestamp(timestamp)
    elif(dataType == TELLSTICK_HUMIDITY):
            print "Humidity:", string_at(value), "%,", datetime.fromtimestamp(timestamp)
    print ""

def nothing() :
    print "nothing called"

def device_callback(deviceId, method, value, callbackId, context):
    global timers
    print "callback!"
    print method
    if (deviceId == 1):
            # is turning on deviceId 1 here, so just return if events for that device are picked up
            return

    t = 0
    print "Received event for device %d" % (deviceId,)
    if (deviceId in timers):
            # a timer already exists for this device, it might be running so interrupt it
            # Many devices (for example motion detectors) resends their messages many times to ensure that they
            # are received correctly. In this example, we don't want to run the turnOn/turnOff methods every time, instead we
            # start a timer, and run the method when the timer is finished. For every incoming event on this device, the timer
            # is restarted.
            t = timers[deviceId]
            t.cancel()
    if (method == TELLSTICK_DIM):
        print int(float(string_at(value))/2.55)+1
        t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", int(float(string_at(value))/2.55)+1, ""])
    elif (method == TELLSTICK_TURNON):
        t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", "255", ""])
    elif (method == TELLSTICK_TURNOFF):
        t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", "0", ""])
    else :
        syslog.syslog(syslog.LOG_ERR, 'Unknown command received for %s:' % deviceId)
        syslog.syslog(syslog.LOG_ERR, 'method = %s' % method)
        syslog.syslog(syslog.LOG_ERR, 'value = %s' % value)
        syslog.syslog(syslog.LOG_ERR, 'callbackId = %s' % callbackId)
        syslog.syslog(syslog.LOG_ERR, 'context = %s' % context)
    t.start()
    timers[deviceId] = t #put timer in list, to allow later cancellation

def device_change_callback(deviceId, change_event, change_type, callbackId, context):
    global timers
    print "device change callback!"
    print method
    if (deviceId == 1):
            # is turning on deviceId 1 here, so just return if events for that device are picked up
            return

    t = 0
    print "Received event for device %d" % (deviceId,)
    if (deviceId in timers):
            # a timer already exists for this device, it might be running so interrupt it
            # Many devices (for example motion detectors) resends their messages many times to ensure that they
            # are received correctly. In this example, we don't want to run the turnOn/turnOff methods every time, instead we
            # start a timer, and run the method when the timer is finished. For every incoming event on this device, the timer
            # is restarted.
            t = timers[deviceId]
            t.cancel()
    if (change_event == TELLSTICK_DIM):
        print int(float(string_at(value))/2.55)+1
        #t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", int(float(string_at(value))/2.55)+1, ""])
    elif (change_event == TELLSTICK_TURNON):
        pass
        #t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", "255", ""])
    elif (change_event == TELLSTICK_TURNOFF):
        pass
        #t = Timer(delay_rf/1000.0, client.emitEvent,[lib.make_device_id(deviceId), "event.device.statechanged", "0", ""])
    else :
        syslog.syslog(syslog.LOG_ERR, 'Unknown command received for %s:' % deviceId)
        syslog.syslog(syslog.LOG_ERR, 'method = %s' % method)
        syslog.syslog(syslog.LOG_ERR, 'value = %s' % value)
        syslog.syslog(syslog.LOG_ERR, 'callbackId = %s' % callbackId)
        syslog.syslog(syslog.LOG_ERR, 'context = %s' % context)
    t.start()
    timers[deviceId] = t #put timer in list, to allow later cancellation

#function to be called when device event occurs, even for unregistered devices
def raw_callback(data, controllerId, callbackId, context):
    print string_at(data)

    print "callback!"

SENSORFUNC = CFUNCTYPE(None, POINTER(c_ubyte), POINTER(c_ubyte), c_int, c_int, POINTER(c_ubyte), c_int, c_int, c_void_p)
DEVICEFUNC = CFUNCTYPE(None, c_int, c_int, POINTER(c_ubyte), c_int, c_void_p)
DEVICECHANGEFUNC = CFUNCTYPE(None, c_int, c_int, c_int, c_int, c_void_p)
RAWFUNC = CFUNCTYPE(None, POINTER(c_ubyte), c_int, c_int, c_void_p)

class TelldusException(Exception):
    """
    telldus exception
    """
    def __init__(self, value):
        '''
        '''
        Exception.__init__(self)
        self.value = value

    def __str__(self):
        '''
        '''
        return repr(self.value)


class Telldusd:
    """
    Interface to the telldusd daemon. It encapsulates ALL the calls to
    the telldus daemon.
    """
    def __init__(self):
        '''
        Init the class
        '''
        self._tdlib = None
        self._device_event_cb = None
        self._device_event_cb_id = None
        self._sensor_event_cb = None
        self._sensor_event_cb_id = None
        self._device_change_event_cb = None
        self._device_change_event_cb_id = None
        ret = find_library("telldus-core")
        if ret != None:
            try:
                self._tdlib = cdll.LoadLibrary(ret)
            except:
                raise TelldusException("Could not load the telldus-core library : %s" % (traceback.format_exc()))
        else:
            raise TelldusException("Could not find the telldus-core library. Check if it is installed properly : %s" % (traceback.format_exc()))
        try:
            self._tdlib.tdInit()
        except:
            raise TelldusException("Could not initialize telldus-core library : %s" % (traceback.format_exc()))

    def close(self):
        '''
        Close the lib
        '''
        self.unregister_device_event()
        self.unregister_device_change_event()
        self.unregister_sensor_event()
        self._tdlib.tdClose()

    def register_device_event(self, callback):
        '''
        Register the device event callback to telldusd
        '''
        try:
            self._device_event_cb_id = \
                self._tdlib.tdRegisterDeviceEvent(callback, 0)
            return self._device_event_cb_id
        except:
            raise TelldusException("Could not register the device event callback : %s" % (traceback.format_exc()))

    def unregister_device_event(self):
        '''
        Unregister the device event callback to telldusd
        '''
        try:
            self._tdlib.tdUnregisterCallback(self._device_event_cb_id)
        except:
            raise TelldusException("Could not unregister the device event callback : %s" % (traceback.format_exc()))

    def register_device_change_event(self, callback):
        '''
        Register the device change event callback to telldusd
        '''
        try:
            self._device_change_event_cb_id = \
                self._tdlib.tdRegisterDeviceChangeEvent(callback,0)
            return self._device_change_event_cb_id
        except:
            raise TelldusException("Could not register the device change event callback : %s" % (traceback.format_exc()))

    def unregister_device_change_event(self):
        '''
        Unregister the device change event callback to telldusd
        '''
        try:
            self._tdlib.tdUnregisterCallback(self._device_change_event_cb_id)
        except:
            raise TelldusException("Could not unregister the device event change callback : %s" % (traceback.format_exc()))

    def register_sensor_event(self, callback):
        '''
        Register the sensor event callback to telldusd
        '''
        try:
            self._sensor_event_cb_id = \
                self._tdlib.tdRegisterSensorEvent(callback, 0)
            return self._sensor_event_cb_id
        except:
            raise TelldusException("Could not register the sensor event callback : %s" % (traceback.format_exc()))

    def unregister_sensor_event(self):
        '''
        Unregister the sensor event callback to telldusd
        '''
        try:
            self._tdlib.tdUnregisterCallback(self._sensor_event_cb_id)
        except:
            raise TelldusException("Could not unregister the sensor event callback : %s" % (traceback.format_exc()))

    def get_devices(self):
        '''
        Return a list of devices registered in telldus daemon
        '''
        ret = {}
        for i in range(self._tdlib.tdGetNumberOfDevices()):
            iid = self._tdlib.tdGetDeviceId(c_int(i))
            ret[iid] = { "name" : c_char_p(self._tdlib.tdGetName(c_int(iid))).value,
                       "house" : c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("house"), "")).value,
                       "unit" : c_char_p(self._tdlib.tdGetDeviceParameter(c_int(iid), c_char_p("unit"), "")).value,
                       "model" : "%s" % c_char_p(self._tdlib.tdGetModel(c_int(iid))).value,
                       "protocol" : c_char_p(self._tdlib.tdGetProtocol(c_int(iid))).value
            }
        return ret

    def is_dimmer(self, deviceid):
        '''
        Get the info on the device
        @param deviceid : id of the module
        '''
        if self.methods(deviceid, TELLSTICK_DIM) == TELLSTICK_DIM:
            return True
        return False

    def is_switch(self, deviceid):
        '''
        Get the info on the device
        @param deviceid : id of the module
        '''
        if self.methods(deviceid, TELLSTICK_TURNON) == TELLSTICK_TURNON and \
           self.methods(deviceid, TELLSTICK_TURNOFF) == TELLSTICK_TURNOFF and \
           self.methods(deviceid, TELLSTICK_DIM) != TELLSTICK_DIM:
                return True
        return False

    def get_info(self, deviceid):
        '''
        Get the info on the device
        @param deviceid : id of the module
        '''
        sst = []
        sst.append("%s : %s" % \
            (deviceid, c_char_p(self._tdlib.tdGetName(c_int(deviceid))).value))
        sst.append("model : %s" % \
            (c_char_p(self._tdlib.tdGetModel(c_int(deviceid))).value))
        sst.append("protocol : %s" % \
            (c_char_p(self._tdlib.tdGetProtocol(c_int(deviceid))).value))
        sst.append("house : %s / unit: %s" % (c_char_p(self._tdlib.tdGetDeviceParameter(c_int(deviceid), c_char_p("house"), "")).value, \
            c_char_p(self._tdlib.tdGetDeviceParameter(c_int(deviceid), c_char_p("unit"), "")).value))
        sst.append("Methods :")
        ss1, ss2, ss3 = "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_TURNON) \
            == TELLSTICK_TURNON:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_TURNOFF) \
            == TELLSTICK_TURNOFF:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_DIM) \
            == TELLSTICK_DIM:
            ss3 = "Yes"
        sst.append("ON : %s / OFF: %s / DIM: %s" % (ss1, ss2, ss3))
        ss1, ss2, ss3, ss4 = "No", "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_BELL) \
            == TELLSTICK_BELL:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_TOGGLE) \
            == TELLSTICK_TOGGLE:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_LEARN) \
            == TELLSTICK_LEARN:
            ss3 = "Yes"
        if self.methods(deviceid, TELLSTICK_EXECUTE) \
            == TELLSTICK_EXECUTE:
            ss4 = "Yes"
        sst.append("BELL : %s / TOGGLE: %s / LEARN: %s / EXECUTE: %s" % \
            (ss1, ss2, ss3, ss4))
        ss1, ss2, ss3 = "No", "No", "No"
        if self.methods(deviceid, TELLSTICK_UP) \
            == TELLSTICK_UP:
            ss1 = "Yes"
        if self.methods(deviceid, TELLSTICK_DOWN) \
            == TELLSTICK_DOWN:
            ss2 = "Yes"
        if self.methods(deviceid, TELLSTICK_STOP) \
            == TELLSTICK_STOP:
            ss3 = "Yes"
        sst.append("UP : %s / DOWN: %s / STOP: %s" % (ss1, ss2, ss3))
        return sst

    def check_device(self, device):
        '''

        Check that the device exist in telldusd
        @param device : address of the device. Maybe malformed.
        '''
        try:
            deviceid = int(device[2:])
            name = c_char_p(self._tdlib.tdGetName(c_int(deviceid))).value
            #print "found name = %s" % name
            if name == None or name == "" :
                #print "bad device %s" % device
                return False
            else:
                #print "good device %s" % device
                return True
        except :
            #print "bad device %s" % device
            return False

    def get_device_id(self, devicestr):
        '''
        Retrieve an id from HU address
        @param device : address of the module (ie TS14)
        @return : Id of the device (14)
        '''
        return int(devicestr[2:])

    def make_device_id(self, deviceint):
        '''
        Retrieve an id from HU address
        @param device : address of the module (ie TS14)
        @return : Id of the device (14)
        '''
        return "TS%s"%deviceint

    def get_device(self, deviceid):
        '''
        Retrieve an address device from deviceid
        @param deviceid : id of the device (ie 14)
        @return : address of the device (ie TS14)
        '''
        return 'TS'+str(deviceid)

    def turn_on(self, deviceid):
        '''
        Turns the internal device On
        @param deviceid : id of the module
        '''
        self._tdlib.tdTurnOn(c_int(deviceid))

    def turn_off(self, deviceid):
        '''
        Turns the internal device Off
        @param deviceid : id of the module
        '''
        self._tdlib.tdTurnOff(c_int(deviceid))

    def bell(self, deviceid):
        '''
        Bells the device
        @param deviceid : id of the module
        '''
        self._tdlib.tdBell(c_int(deviceid))

    def learn(self, deviceid):
        '''
        Sends a special Learn command to the device
        @param deviceid : id of the module
        '''
        self._tdlib.tdLearn(c_int(deviceid))

    def add_device(self):
        '''
        Add a device to telldus
        @return the id of the new device
        '''
        return self._tdlib.tdAddDevice()

    def remove_device(self, deviceid):
        '''
        Remove a device from telldus
        @param deviceid : id of the module
        @return True if success, false otherwise
        '''
        return self._tdlib.tdRemoveDevice(c_int(deviceid))

    def dim(self, deviceid, level):
        '''
        Dims the device level should be between 0 and 100
        tdlib use a level from 0 to 255. So we translate it.
        @param deviceid : id of the module
        @param level : level of light
        '''
        self._tdlib.tdDim(c_int(deviceid), c_ubyte(int(int(level)*2.55)))

    def up(self, deviceid):
        '''
        Move the shutter up.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdUp(c_int(deviceid))

    def down(self, deviceid):
        '''
        Move the shutter down.
        Test if the device support the up command
        If not try to send an on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdDown(c_int(deviceid))

    def stop(self, deviceid):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        self._tdlib.tdStop(c_int(deviceid))

    def methods(self, deviceid, methods):
        '''
        Stop the shutter.
        Test if the device support the up command
        If not try to manage it supporting the on command
        @param deviceid : id of the module
        '''
        #int methods = tdMethods(id, TELLSTICK_TURNON | \
        #    TELLSTICK_TURNOFF | TELLSTICK_BELL);
        return self._tdlib.tdMethods(c_int(deviceid), methods)

client = agoclient.AgoConnection("tellstick")
device = agoclient.getConfigOption("tellstick", "device", "/dev/tellstick")
delay_rf = float(agoclient.getConfigOption("tellstick", "delay_rf", "400"))

lib = Telldusd()
sensor_func = SENSORFUNC(sensor_callback)
device_func = DEVICEFUNC(device_callback)
raw_func = RAWFUNC(raw_callback)

lib.register_sensor_event(sensor_func)
lib.register_device_event(device_func)
lib.register_device_change_event(raw_func)

devices=lib.get_devices()
for dev in devices.keys() :
    if lib.is_dimmer(dev) :
        client.addDevice(lib.make_device_id(dev), "dimmer")
    elif lib.is_switch(dev) :
        client.addDevice(lib.make_device_id(dev), "switch")
    else :
        syslog.syslog(syslog.LOG_ERR, 'Unknown device type for %s' % dev)
        log_exception(lib.get_info(dev))

print devices

tellsticklock = threading.Lock()

class command_send(threading.Thread):

    def __init__(self, id, command, level):
        threading.Thread.__init__(self)
        self.id = id
        self.command = command
        self.level = level

    def run(self):
        try :
            tellsticklock.acquire()
            if self.command == "on":
                if lib.is_dimmer(lib.get_device_id(self.id)) :
                    lib.dim(lib.get_device_id(self.id), 255)
                else :
                    lib.turn_on(lib.get_device_id(self.id))
            elif self.command == "off":
                if lib.is_dimmer(lib.get_device_id(self.id)) :
                    lib.dim(lib.get_device_id(self.id), 0)
                else :
                    lib.turn_off(lib.get_device_id(self.id))
            elif self.command == "setlevel":
                lib.dim(lib.get_device_id(self.id), self.level)
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when calling telldus command %s for device  %s' % (self.command, self.id))
            log_exception(error)
            self.error=1
        finally :
            tellsticklock.release()

def messageHandler(internalid, content):
    print content
    if "command" in content:
        if "level" in content:
            background = command_send(internalid, content["command"], content["level"])
        else:
            background = command_send(internalid, content["command"], "")
        background.setDaemon(True)
        background.start()

# specify our message handler method
client.addHandler(messageHandler)

client.run()

lib.close()
