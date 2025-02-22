#!/usr/bin/env python3

import time
import os
import sys
import traceback
import json

sys.path.append('./lib')

from configparser import RawConfigParser
from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from os.path import exists

from growatt import Growatt
from metricsRecorder import MetricsRecorder
from modbusMetrics import ModbusMetrics
from calcExportLimit import ExportLimitCalc



settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)
debug = settings.get('query', 'debug', fallback=0)
if not os.environ.get('DEBUG') == None:
    debug = os.environ.get('DEBUG')
port = settings.get('query', 'port', fallback='/dev/ttyUSB0')

while not exists(port):
    print("Waiting for ", port);
    time.sleep(5)

metrics = ModbusMetrics(settings)
recorder = MetricsRecorder(settings, metrics)
exportCalc = ExportLimitCalc(settings)



print('Setup Serial Connection... ', end='')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
print('Done!')

print('Loading inverters... ')
inverters = []
for section in settings.sections():
    if not section.startswith('inverters.'):
        continue

    name = section[10:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    limits = json.loads(settings.get(section, 'limits', fallback="[[4,500],[4.5,1000],[5,2000]]"))
    exportEvaluatePeriod = int(settings.get(section, 'exportEvaluatePeriod', fallback=900))
    growatt = Growatt(client, name, unit)
    growatt.print_info()
    inverters.append({
        'error_sleep': 0,
        'growatt': growatt,
        'measurement': measurement,
        'limits': limits,
        'exportEvaluatePeriod': exportEvaluatePeriod,
        'lastExportEvaluate': 0
    })
print('Done!')

while True:
    online = False
    for inverter in inverters:
        # If this inverter errored then we wait a bit before trying again
        if inverter['error_sleep'] > 0:
            inverter['error_sleep'] -= interval
            continue

        growatt = inverter['growatt']
        try:
            now = time.time()
            info = growatt.read()

            if info is None:
                continue

            # Mark that at least one inverter is online so we should continue collecting data
            online = True
            recorder.add(now, inverter['measurement'], info, interval,[])
            tosend = True

            if tosend:
                recorder.send()
                if debug == 1:
                    print(growatt.name)
                    print(info)

            metrics.report(recorder)

            if now > inverter['lastExportEvaluate'] + inverter['exportEvaluatePeriod']:     
                inverter['lastExportEvaluate'] = now
                exportCalc.load("gateway", 'gatewayData')
                endOfPeriod = (time.time())
                startOfPeriod = (endOfPeriod - (7*24*3600))
                exportCalculations = exportCalc.analyse(startOfPeriod, endOfPeriod)
                print(f'export calcs {json.dumps(exportCalculations)}')
                limitSet = False
                for limit in inverter['limits']:                
                    if exportCalculations['kwh'] < limit[0]:
                        growatt.setExportLimit(limit[1])
                        limitSet = True
                        break;
                if not limitSet:
                    growatt.setExportLimit(4200)



        except Exception as err:
            metrics.inc('main.exceptions')
            traceback.print_exc()
            print(growatt.name)
            print(err)
            inverter['error_sleep'] = error_interval

    if online:
        time.sleep(interval)
    else:
        # If all the inverters are not online because no power is being generated then we sleep for 1 min
        time.sleep(offline_interval)
