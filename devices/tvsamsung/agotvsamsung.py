#!/usr/bin/python
"""
     Copyright (C) 2013 Sebastien GALLET <bibi21000@gmail.com>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.

     Samsung TV devices

"""


import sys,os
try :
    sys.path.insert(0, os.path.abspath('/opt/agocontrol/bin/'))
    sys.path.insert(0, os.path.abspath('../../../agocontrol/shared'))
except:
    pass
import agoclient
import threading
import time
import base64
import logging
from subprocess import Popen, PIPE
import re
import socket
import traceback
import syslog

remote  = 'python remote'
app     = 'agocontrol'
tvmodel = "LE32C650"

client = agoclient.AgoConnection("TvSamsung")

def log_exception(exc):
    for line in exc.split('\n'):
        if len(line):
            syslog.syslog(syslog.LOG_ERR, line)

hostsconfig = agoclient.getConfigOption("tvsamsung", "hosts", "192.168.14.50")
tvs={}
hosts=[]
try:
    hosts = map(str, hostsconfig.split(','))
except:
    syslog.syslog(syslog.LOG_ERR, 'Error when reading hosts TVs')
else:
    for host in hosts:
        try :
            if os.system('ping -c 2 ' + host):
                syslog.syslog(syslog.LOG_WARNING, 'No response to ping from %s'%host)
            else :
                pid = Popen(["/usr/sbin/arp", "-n", host], stdout=PIPE)
                s = pid.communicate()[0]
                macaddress = re.search(r"(([a-f\d]{1,2}\:){5}[a-f\d]{1,2})", s).groups()[0]
                tvs[host]={'host':host, 'mac':macaddress}
                syslog.syslog(syslog.LOG_INFO, 'Add TV device at %s' % host)
                client.addDevice(host, "tv")
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when adding bluetooth device %s' % host)
            log_exception(error)

if len(tvs)==0 :
    exit(1)
hostconfig=None
hosts=None
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
s.connect((tvs[tvs.keys()[0]]['host'], 55000))
ipsource = s.getsockname()[0]
s.close()
s=None
syslog.syslog(syslog.LOG_DEBUG, 'Found %s TVs devices' % len(tvs))
syslog.syslog(syslog.LOG_DEBUG, 'Use local IP %s' % ipsource)
syslog.syslog(syslog.LOG_DEBUG, 'TVs founds %s' % tvs)

tvlock = threading.Lock()

class command_send(threading.Thread):

    def __init__(self, id, functioncommand, option):
        threading.Thread.__init__(self)
        self.id = id
        self.functioncommand = functioncommand
        self.option = option
        self.error=0

    def notify_sms(self, rtime=None, receiver=None, receiver_no="0000000000", sender=None, sender_no="0000000000", message="Hello world") :
        syslog.syslog(syslog.LOG_DEBUG, 'notify_sms from  %s' % sender_no)
        if rtime==None :
            rtime=time.mktime(time.localtime())
        if receiver==None :
            receiver=receiver_no
        if sender==None :
            sender=sender_no
        body = "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + \
                "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">" + \
                "<s:Body>" + "      <u:AddMessage xmlns:u=\"urn:samsung.com:service:MessageBoxService:1\">" + \
                "         <MessageType>text/xml</MessageType>" + "         <MessageID>MessageId</MessageID>" + \
                "<Message>" + "&lt;Category&gt;SMS&lt;/Category&gt;" + "&lt;DisplayType&gt;Maximum&lt;/DisplayType&gt;" + \
                "&lt;ReceiveTime&gt;" + "&lt;Date&gt;" + time.strftime('%Y-%m-%d', time.localtime(rtime)) + \
                "&lt;/Date&gt;" + "&lt;Time&gt;" + time.strftime('%H:%M:%S', time.localtime(rtime)) + \
                "&lt;/Time&gt;" + "&lt;/ReceiveTime&gt;" + "&lt;Receiver&gt;" + "&lt;Number&gt;" + \
                receiver_no + "&lt;/Number&gt;" + "&lt;Name&gt;" + receiver + \
                "&lt;/Name&gt;" + "&lt;/Receiver&gt;" + "&lt;Sender&gt;" + "&lt;Number&gt;" + \
                sender_no + "&lt;/Number&gt;" + "&lt;Name&gt;" + sender + "&lt;/Name&gt;" + \
                "&lt;/Sender&gt;" + "&lt;Body&gt;" + message + "&lt;/Body&gt;" + "</Message>" + \
                "      </u:AddMessage>" + "   </s:Body>" + "</s:Envelope>";
        self._notify(body)

    def notify_incoming_call(self, rtime=None, receiver=None, receiver_no="0000000000", sender=None, sender_no="0000000000", message="Hello world") :
        syslog.syslog(syslog.LOG_DEBUG, 'notify_incoming_call from  %s' % sender_no)
        if rtime==None :
            rtime=time.mktime(time.localtime())
        if receiver==None :
            receiver=receiver_no
        if sender==None :
            sender=sender_no
        body = "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + \
                "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">" + \
                "<s:Body>" + "      <u:AddMessage xmlns:u=\"urn:samsung.com:service:MessageBoxService:1\">" + \
                "         <MessageType>text/xml</MessageType>" + "         <MessageID>MessageId</MessageID>" + \
                "<Message>" + "&lt;Category&gt;Incoming Call&lt;/Category&gt;" + "&lt;DisplayType&gt;Maximum&lt;/DisplayType&gt;" + \
                "&lt;CallTime&gt;" + "&lt;Date&gt;" + time.strftime('%Y-%m-%d', time.localtime(rtime)) + \
                "&lt;/Date&gt;" + "&lt;Time&gt;" + time.strftime('%H:%M:%S', time.localtime(rtime)) + \
                "&lt;/Time&gt;" + "&lt;/CallTime&gt;" + "&lt;Callee&gt;" + "&lt;Number&gt;" + \
                receiver_no + "&lt;/Number&gt;" + "&lt;Name&gt;" + receiver + \
                "&lt;/Name&gt;" + "&lt;/Callee&gt;" + "&lt;Caller&gt;" + "&lt;Number&gt;" + \
                sender_no + "&lt;/Number&gt;" + "&lt;Name&gt;" + sender + "&lt;/Name&gt;" + \
                "&lt;/Caller&gt;" + "&lt;Body&gt;" + message + "&lt;/Body&gt;" + "</Message>" + \
                "      </u:AddMessage>" + "   </s:Body>" + "</s:Envelope>";
        self._notify(body)

    def notify_schedule_reminder(self, starttime=None, endtime=None, owner=None, owner_no="0000000000", message="Hello world") :
        syslog.syslog(syslog.LOG_DEBUG, 'notify_schedule_reminder for  %s' % owner_no)
        if starttime==None :
            starttime=time.mktime(time.localtime())
        if endtime==None :
            endtime=time.mktime(time.localtime())
        if owner==None :
            owner=owner_no
        body = "<?xml version=\"1.0\" encoding=\"utf-8\"?>" + \
                "<s:Envelope xmlns:s=\"http://schemas.xmlsoap.org/soap/envelope/\" s:encodingStyle=\"http://schemas.xmlsoap.org/soap/encoding/\">" + \
                "<s:Body>" + "      <u:AddMessage xmlns:u=\"urn:samsung.com:service:MessageBoxService:1\">" + \
                "         <MessageType>text/xml</MessageType>" + "         <MessageID>MessageId</MessageID>" + \
                "<Message>" + "&lt;Category&gt;Schedule Reminder&lt;/Category&gt;" + "&lt;DisplayType&gt;Maximum&lt;/DisplayType&gt;" + \
                "&lt;StartTime&gt;" + "&lt;Date&gt;" + time.strftime('%Y-%m-%d', time.localtime(starttime)) + \
                "&lt;/Date&gt;" + "&lt;Time&gt;" + time.strftime('%H:%M:%S', time.localtime(starttime)) + \
                "&lt;/Time&gt;" + "&lt;/StartTime&gt;" + \
                "&lt;EndTime&gt;" + "&lt;Date&gt;" + time.strftime('%Y-%m-%d', time.localtime(endtime)) + \
                "&lt;/Date&gt;" + "&lt;Time&gt;" + time.strftime('%H:%M:%S', time.localtime(endtime)) + \
                "&lt;/Time&gt;" + "&lt;/EndTime&gt;" + \
                "&lt;Owner&gt;" + "&lt;Number&gt;" + \
                owner_no + "&lt;/Number&gt;" + "&lt;Name&gt;" + owner + \
                "&lt;/Name&gt;" + "&lt;/Owner&gt;" + \
                "&lt;Body&gt;" + message + "&lt;/Body&gt;" + "</Message>" + \
                "      </u:AddMessage>" + "   </s:Body>" + "</s:Envelope>";
        self._notify(body)

    def _notify(self,message):
        length = len(message)
        header = "POST /PMR/control/MessageBoxService HTTP/1.0\r\n" + "Content-Type: text/xml; charset=\"utf-8\"\r\n" + \
                "HOST: " + ipsource + \
                "\r\n" + "Content-Length: " + str(length) + "\r\n" + \
                "SOAPACTION: \"uuid:samsung.com:service:MessageBoxService:1#AddMessage\"\r\n" + "Connection: close\r\n" + "\r\n"
        message = header + message
        try :
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
            s.connect((self.id, 52235))
            sent = s.send(message)
            if (sent <= 0):
                syslog.syslog(syslog.LOG_ERR, 'Error when notify message. No response from %s'%self.id)
                s.close()
                return
            recv = s.recv(100000)
            s.close()
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when notifying %s' % self.id)
            log_exception(error)


    def push(self,key):
        # keys : http://wiki.samygo.tv/index.php5/D-Series_Key_Codes
        try :
            tvlock.acquire()
            self.error=0
            new = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            new.connect((self.id, 55000))
            msg = chr(0x64) + chr(0x00) +\
                chr(len(base64.b64encode(ipsource)))    + chr(0x00) + base64.b64encode(ipsource) +\
                chr(len(base64.b64encode(macaddress)))    + chr(0x00) + base64.b64encode(macaddress) +\
                chr(len(base64.b64encode(remote))) + chr(0x00) + base64.b64encode(remote)
            pkt = chr(0x00) +\
                chr(len(app)) + chr(0x00) + app +\
                chr(len(msg)) + chr(0x00) + msg
            new.send(pkt)
            msg = chr(0x00) + chr(0x00) + chr(0x00) +\
                chr(len(base64.b64encode(key))) + chr(0x00) + base64.b64encode(key)
            pkt = chr(0x00) +\
                chr(len(tvmodel))  + chr(0x00) + tvmodel +\
                chr(len(msg)) + chr(0x00) + msg
            new.send(pkt)
            new.close()
            time.sleep(0.1)
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when pushing command to TV %s' % self.id)
            log_exception(error)
            self.error=1
        finally :
            tvlock.release()

    def run(self):
        self.error=0
        syslog.syslog(syslog.LOG_DEBUG, 'command %s to %s' % (self.functioncommand, self.id))
        if self.functioncommand == "chan+":
            self.push("KEY_CHUP")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "255", "")
        elif self.functioncommand == "chan-":
            self.push("KEY_CHDOWN")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "vol+":
            self.push("KEY_VOLUP")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "255", "")
        elif self.functioncommand == "vol-":
            self.push("KEY_VOLDOWN")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "on":
            self.push("KEY_POWERON")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "off":
            self.push("KEY_POWEROFF")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "mute":
            self.push("KEY_MUTE")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "unmute":
            self.push("KEY_MUTE")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "getepg":
            self.push("KEY_GUIDE")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "setinput":
            self.push("KEY_HDMI")
            #self.push("KEY_HDMI1")
            #self.push("KEY_EXT2")
            #self.push("KEY_PCMODE")
            #self.push("KEY_AV1")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "notifysms":
            self.notify_message(rtime=None, sender=None, sender_no="bibi", owner=None, owner_no="bibi", message="coucou")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "notifyincomingcall":
            self.notify_incoming_call(rtime=None, caller=None, caller_no="bibi", callee=None, callee_no="bibi", message="coucou")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")
        elif self.functioncommand == "notifyschedulereminder":
            self.notify_schedule_reminder(rtime=None, sender=None, sender_no="bibi", owner=None, owner_no="bibi", message="coucou")
            if self.error==0:
                client.emitEvent(self.id, "event.device.statechanged", "0", "")

def messageHandler(internalid, content):
    print content
    if "command" in content:
        if "option" in content:
            background = command_send(internalid, content["command"], content["option"])
        else:
            background = command_send(internalid, content["command"], "")
        background.setDaemon(True)
        background.start()

# specify our message handler method
client.addHandler(messageHandler)

client.run()
