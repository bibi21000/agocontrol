#! /usr/bin/python
"""
     Copyright (C) 2013 Sebastien GALLET <bibi21000@gmail.com>

     This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License.
     This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty
     of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.

     See the GNU General Public License for more details.


     Weather devices

"""

import sys,os
try :
    sys.path.insert(0, os.path.abspath('/opt/agocontrol/bin/'))
    sys.path.insert(0, os.path.abspath('../../../agocontrol/shared'))
except:
    pass
import agoclient
import time
import threading
import string
import traceback
import urllib2
import json
import syslog

ex_rain = "%s-rain-%s"
ex_temp = "%s-temperature-%s"
ex_humidity = "%s-humidity-%s"
ex_pressure = "%s-pressure-%s"
ex_windspeed = "%s-windspeed-%s"
ex_windangle = "%s-windangle-%s"
ex_rain3h = "%s-rain3h-%s"
ex_cloud = "%s-cloud-%s"
ex_snow3h = "%s-snow3h-%s"

def log_exception(exc):
    for line in exc.split('\n'):
        if len(line):
            syslog.syslog(syslog.LOG_ERR, line)

client = agoclient.AgoConnection("Weather")

weatherconfig = agoclient.getConfigOption("weather","locations","Dijon,France")
locations=[]
fails={}
try:
    locations = map(str, weatherconfig.split(','))
except:
    syslog.syslog(syslog.LOG_ERR, 'Error when reading weather locations')
else:
    if '' in locations :
        locations.remove('')
    for loc in locations:
        try :
            client.addDevice(ex_rain%(loc,0), "binarysensor")
            client.addDevice(ex_temp%(loc,0), "temperaturesensor")
            client.addDevice(ex_humidity%(loc,0), "multilevelsensor")
            client.addDevice(ex_pressure%(loc,0), "multilevelsensor")
            client.addDevice(ex_windspeed%(loc,0), "multilevelsensor")
            client.addDevice(ex_windangle%(loc,0), "multilevelsensor")
            client.addDevice(ex_rain3h%(loc,0), "multilevelsensor")
            client.addDevice(ex_cloud%(loc,0), "multilevelsensor")
            client.addDevice(ex_snow3h%(loc,0), "multilevelsensor")
        except :
            error = traceback.format_exc()
            syslog.syslog(syslog.LOG_ERR, 'Error when adding location %s' % loc)
            log_exception(error)

weatherconfig=None
readMetric = agoclient.getConfigOption("weather","metric","metric")
#readTempUnits = agoclient.getConfigOption("weather","temp_units","c")
#Never use value <600
readWaitTime = int(agoclient.getConfigOption("weather","wait_time","900"))
readApiKey = agoclient.getConfigOption("weather","api_key","")
if readWaitTime<600 :
    readWaitTime=900

syslog.syslog(syslog.LOG_DEBUG, 'Found %s locations' % len(locations))
syslog.syslog(syslog.LOG_DEBUG, 'Locations founds %s' % locations)

class testEvent(threading.Thread):
        def __init__(self,):
                threading.Thread.__init__(self)
        def run(self):
                while (True):
                    for loc in locations:
                        try :
                            if loc in fails and fails[loc]>5 :
                                syslog.syslog(syslog.LOG_WARNING, '%s disabled after %s fails.' % (loc,5))
                            else :
                                syslog.syslog(syslog.LOG_DEBUG, 'Try to get weather data for %s' % loc)
                                response=None
                                if readApiKey=="" :
                                    response = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=%s'%(loc))
                                else :
                                    response = urllib2.urlopen('http://api.openweathermap.org/data/2.5/weather?q=%s&APPID=%s'%(loc,readApiKey))
                                weather_result = json.load(response)
                                syslog.syslog(syslog.LOG_DEBUG, "%s"%weather_result)
                                conditions = weather_result['weather'][0]['main']
                                humidity = float(weather_result['main']['humidity'])
                                temp = float(weather_result['main']['temp'])
                                pressure = float(weather_result['main']['pressure'])
                                windspeed = float(weather_result['wind']['speed'])
                                windangle = float(weather_result['wind']['deg'])
                                if (readMetric == 'metric'):
                                        client.emitEvent(ex_temp%(loc,0), "event.environment.temperaturechanged", "%.2f"%(temp-273.15) , "degC")
                                        client.emitEvent(ex_windspeed%(loc,0), "event.environment.windspeedchanged", "%.2f"%(windspeed*3600/1000), "km/h")
                                else:
                                        client.emitEvent(ex_temp%(loc,0), "event.environment.temperaturechanged",  "%.2f"%(temp*1.8 - 459.67), "degF")
                                        client.emitEvent(ex_windspeed%(loc,0), "event.environment.windspeedchanged", "%.2f"%((windspeed/1.609344)*3600/1000), "mph")
                                client.emitEvent(ex_humidity%(loc,0), "event.environment.humiditychanged", "%.0f"%humidity, "%")
                                client.emitEvent(ex_pressure%(loc,0), "event.environment.pressurechanged", "%.0f"%pressure, "hPa")
                                client.emitEvent(ex_windangle%(loc,0), "event.environment.anglechanged", "%.0f"%windangle, "deg")
                                search_Rain = string.find(conditions, "Rain")
                                search_Drizzle = string.find(conditions, "Drizzle")
                                if (search_Rain >= 0) or (search_Drizzle >=0):
                                        client.emitEvent(ex_rain%(loc,0),"event.device.statechanged", "255", "")
                                else :
                                        client.emitEvent(ex_rain%(loc,0),"event.device.statechanged", "0", "")
                                if 'rain' in weather_result and '3h' in weather_result['rain'] :
                                    client.emitEvent(ex_rain3h%(loc,0), "event.environment.rain3hchanged", "%.0f"%weather_result['rain']['3h'], "mm")
                                else :
                                    client.emitEvent(ex_rain3h%(loc,0), "event.environment.rain3hchanged", "%.0f"%0, "mm")
                                if 'snow' in weather_result and '3h' in weather_result['snow'] :
                                    client.emitEvent(ex_snow3h%(loc,0), "event.environment.snow3hchanged", "%.0f"%weather_result['snow']['3h'], "mm")
                                else :
                                    client.emitEvent(ex_snow3h%(loc,0), "event.environment.snow3hchanged", "%.0f"%0, "mm")
                                if 'clouds' in weather_result and 'all' in weather_result['clouds'] :
                                    client.emitEvent(ex_cloud%(loc,0), "event.environment.cloudchanged", "%.0f"%weather_result['clouds']['all'], "%")
                                else :
                                    client.emitEvent(ex_cloud%(loc,0), "event.environment.cloudchanged", "%.0f"%0, "%")
                                if loc in fails :
                                    if (fails[loc]>1) :
                                        fails[loc] -= 1
                                    else :
                                        del(fails[loc])
                        except :
                            error = traceback.format_exc()
                            syslog.syslog(syslog.LOG_ERR, 'Error when getting weather data for "%s"'%loc)
                            log_exception(error)
                        finally :
                            time.sleep (readWaitTime)

background = testEvent()
background.setDaemon(True)
background.start()

client.run()

