#!/usr/bin/env python3

import time
import os
import sys
sys.path.append('../lib')
from configparser import RawConfigParser
from modbusRegister import ModbusRegister
from sdm230 import Sdm230
from metricsRecorder import MetricsRecorder

# snoops on a RS485 interface connected to a network with an active controller talking to a SDM230




if __name__ == '__main__':


    settings = RawConfigParser()
    settings.read(os.path.dirname(os.path.realpath(__file__)) + '/gateway.cfg')

    error_interval = settings.getint('gateway', 'error_interval', fallback=60)
    debug = settings.getint('gateway', 'debug', fallback=0)




    recorder = MetricsRecorder(settings)


    modbus = ModbusRegister(settings)
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
        interval = settings.getint(section, 'interval', fallback=1)
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
            'nextUpdate': now + interval
        })

    print('Done!')


    now = time.time()
     # main loop
    while True:
        modbus.read();
        now = time.time()
        tosend = False
        for device in devices:
            if now > device['nextUpdate']:
                device['nextUpdate'] = now + interval
                info = device['deviceProcessor'].read()
                recorder.add(now, device['measurement'], info, interval,[])
                tosend = True

        if tosend:
            recorder.send()
            if debug == '1':
                print(points)



    modbus.close()
