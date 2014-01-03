#! /usr/bin/env python
"""
     Copyright (C) 2013 Sebastien GALLET <bibi21000@gmail.com>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.


     Bluetooth Scanner device

     You must pair your phone, ...
     use :
     #hciconfig hci0 piscan
     #bluetooth-agent <pincode>
     Look for your computer on your phone and use the previous pincode
     #hciconfig hci0 noscan

"""

import sys,os
try :
    sys.path.insert(0, os.path.abspath('/opt/agocontrol/bin/'))
    sys.path.insert(0, os.path.abspath('../../../agocontrol/shared'))
except:
    pass
import agoclient
import time
import traceback
import bluetooth
import threading
from threading import Timer
import syslog

client = agoclient.AgoConnection("Bluescan")

def log_exception(exc):
    for line in exc.split('\n'):
        if len(line):
            syslog.syslog(syslog.LOG_ERR, line)

method = agoclient.getConfigOption("bluescan","method","lookup")
scan_delay = int(agoclient.getConfigOption("bluescan","delay-scan","30"))
error_delay = int(agoclient.getConfigOption("bluescan","delay-error","450"))
hysteresis = int(agoclient.getConfigOption("bluescan","hysteresis","3"))
phoneconfig = agoclient.getConfigOption("bluescan","phones","D0:B3:3F:BC:0E:21")
sphones=[]
phones={}
ex_bluescan="bluescan-%s"

try:
    sphones = map(str, phoneconfig.split(','))
except:
    syslog.syslog(syslog.LOG_NOTICE, 'no phone defined')
else:
    for phon in sphones:
        try :
            phones[phon]={'mac': phon, 'status':0, 'count':0}
            syslog.syslog(syslog.LOG_INFO, 'Add bluetooth device %s' % phon)
            client.addDevice(ex_bluescan%phon, "binarysensor")
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when adding bluetooth device %s' % phon)
            log_exception(error)
phoneconfig=None
sphones=None
syslog.syslog(syslog.LOG_DEBUG, 'Found %s bluetooth devices' % len(phones))

def listen_discovery():
    """
    Listen to bluetooth adaptator. This method use the
    bluetooth.discover_devices(). It takes approcimatively 10 seconds
    to proceed. Phones must be "visible" in bluetooth.
    """
    try:
        nearby_devices = bluetooth.discover_devices()
        syslog.syslog(syslog.LOG_DEBUG, 'listen_discovery devices discovered %s' % nearby_devices)
        for phon in phones.keys():
            if phones[phon]["status"] == 1 :
                if phone not in nearby_devices:
                    phones[phon]["count"] =  phones[phon]["count"] + 1
                    if phones[phon]["count"] >= hysteresis:
                        client.emitEvent(ex_bluescan%phon,"event.device.statechanged", "0", "")
                        phones[phon]["status"] = 0
                        syslog.syslog(syslog.LOG_DEBUG, "%s has gone"%phon)
        for phon in nearby_devices:
            if phon in phones.keys():
                if 'name' not in phones[phon] :
                    phones[phon]['name'] = bluetooth.lookup_name(phon)
                phones[phon]["count"] = 0
                if phones[phon]["status"] == 0:
                    phones[phon]["status"] = 1
                    client.emitEvent(ex_bluescan%phon,"event.device.statechanged", "255", "")
                    syslog.syslog(syslog.LOG_DEBUG, "%s is here"%phon)
        return True
    except :
        error = traceback.format_exc()
        syslog.syslog(syslog.LOG_ERR, 'Error when discovering devices in listen_discovery')
        log_exception(error)
        return False

def listen_lookup():
    """
    Listen to bluetooth adaptator. This method use the
    bluetooth.lookup_name(). It takes approcimatively 3 seconds
    to proceed.
    """
    try:
        for phon in phones:
            target_name = bluetooth.lookup_name( phon )
            if target_name == None:
                if phones[phon]["status"] == 1 :
                    phones[phon]["count"] = phones[phon]["count"] + 1
                    if phones[phon]["count"] >= hysteresis:
                        phones[phon]["status"] = 0
                        client.emitEvent(ex_bluescan%phon,"event.device.statechanged", "0", "")
                        syslog.syslog(syslog.LOG_DEBUG, "%s has gone"%phon)
            else:
                phones[phon]["count"] = 0
                if phones[phon]["status"] == 0:
                    phones[phon]["status"] = 1
                    client.emitEvent(ex_bluescan%phon,"event.device.statechanged", "255", "")
                    syslog.syslog(syslog.LOG_DEBUG, "%s is here"%phon)
        return True
    except :
        error = traceback.format_exc()
        syslog.syslog(syslog.LOG_ERR, 'Error when discovering devices in listen_lookup')
        log_exception(error)

class testEvent(threading.Thread):
        def __init__(self,):
                threading.Thread.__init__(self)
        def run(self):
                while (True):
                    if method=="lookup" :
                        if listen_lookup() == True :
                            time.sleep(scan_delay)
                        else :
                            time.sleep(error_delay)
                    else:
                        if listen_discovery() == True :
                            time.sleep(scan_delay)
                        else :
                            time.sleep(error_delay)

background = testEvent()
background.setDaemon(True)
background.start()

client.run()

