#!/usr/bin/env python3

import time
import os
import sys
sys.path.append('../lib')
from configparser import RawConfigParser
from modbusRegister import ModbusRegister
from modbusMetrics import ModbusMetrics
from sdm230 import Sdm230
from metricsRecorder import MetricsRecorder

# snoops on a RS485 interface connected to a network with an active controller talking to a SDM230




if __name__ == '__main__':


    settings = RawConfigParser()
    settings.read(os.path.dirname(os.path.realpath(__file__)) + '/gateway.cfg')

    error_interval = settings.getint('gateway', 'error_interval', fallback=60)
    debug = settings.getint('gateway', 'debug', fallback=0)



    metrics = ModbusMetrics(settings)
    recorder = MetricsRecorder(settings, metrics)


    modbus = ModbusRegister(settings, metrics)
    modbus.connect()


    print('Loading devices... ')
    devices = []
    now = time.time()
    for section in settings.sections():
        if not section.startswith('gateway.'):
            continue

        name = section[8:]
        device = int(settings.get(section, 'device'))
        measurement = settings.get(section, 'measurement')
        deviceType = settings.get(section, 'deviceType')
        logFields = settings.get(section, 'logFields', fallback='').split(',')
        sampleInterval = settings.getint(section, 'sampleInterval', fallback=5)
        updateInterval = settings.getint(section, 'updateInterval', fallback=60)
        if deviceType == 'sdm230':
            deviceProcessor = Sdm230(modbus, device, logFields)
        else:
            continue

        devices.append({
            'error_sleep': 0,
            'device': device,
            'name': name,
            'deviceProcessor': deviceProcessor,
            'measurement': measurement,
            'nextUpdate': now + updateInterval,
            'nextSample': now + sampleInterval,
            'updateInterval': updateInterval,
            'sampleInterval': sampleInterval
         })

    print('Done!')


     # main loop
    lastRead = time.time()
    while True:
        now = time.time()
        if modbus.read():
            lastRead = now
        if now > lastRead + 30:
            # nothing read for 60s, inverter is in deep sleep
            # Trigger getting the data.
            for device in devices:
                device['deviceProcessor'].request()
            now = time.time()
            lastRead = now


        tosend = False
        for device in devices:
            if now > device['nextSample']:
                device['nextSample'] = now + device['sampleInterval']
                device['deviceProcessor'].update()
            if now > device['nextUpdate']:
                device['nextUpdate'] = now + device['updateInterval']
                info = device['deviceProcessor'].read()
                recorder.add(now, device['measurement'], info, device['updateInterval'],[])
                tosend = True

        if tosend:
            recorder.send()
            if debug == '1':
                print(points)

        metrics.report(recorder)



    modbus.close()
