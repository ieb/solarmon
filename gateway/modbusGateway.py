#!/usr/bin/env python3

import time
import os

from configparser import RawConfigParser
from influxdb import InfluxDBClient
from modbusRegister import ModbusRegister
from sdm230 import SDM230

# snoops on a RS485 interface connected to a network with an active controller talking to a SDM230





if __name__ == '__main__':


    settings = RawConfigParser()
    settings.read(os.path.dirname(os.path.realpath(__file__)) + '/gateway.cfg')

    error_interval = settings.getint('gateway', 'error_interval', fallback=60)


    print('Setup InfluxDB Client... ', end='')
    db_name = settings.get('influx', 'db_name', fallback='inverter')

    influx = InfluxDBClient(host=settings.get('influx', 'host', fallback='localhost'),
                    port=settings.getint('influx', 'port', fallback=8086),
                    username=settings.get('influx', 'username', fallback=None),
                    password=settings.get('influx', 'password', fallback=None),
                    database=db_name)
    influx.create_database(db_name)
    print('Done!')


    modbus = ModbusRegister(settings);
    modbus.connect();


    print('Loading devices... ')
    devices = []
    now = time.time()
    for section in settings.sections():
        if not section.startswith('gateway.'):
            continue

        name = section[6:]
        device = int(settings.get(section, 'device'))
        measurement = settings.get(section, 'measurement')
        deviceType = settings.get(section, 'deviceType')
        interval = settings.getint(section, 'interval', fallback=1)
        if deviceType == 'sdm230':
            deviceProcessor = SDM230(modbus, device)
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
        points = []
        now = time.time()
        for device in devices:
            if now > device.nextUpdate:
                device.nextUpdate = device.nextUpdate + interval
                info = device.deviceProcessor.read()
                points.append({
                    'time': int(now),
                    'measurement': device.measurement,
                    "fields": info,
                    })

        if len(points) > 0:
            if debug == 1:
                print(point)
            if not influx.write_points(points, time_precision='s'):
                print("Failed to write to DB!")



    modbus.close()
