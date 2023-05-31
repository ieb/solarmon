#!/usr/bin/env python3

import time
import os
sys.path.append('../lib')

from os.path import exists

from configparser import RawConfigParser
from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient

from sdm230meter import SDM230Meter

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/metermon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)
debug = settings.get('query', 'debug', fallback=0)
port = settings.get('query', 'port', fallback='/dev/ttyUSB0')

db_name = settings.get('influx', 'db_name', fallback='none')

while not exists(port):
    print("Waiting for ", port);
    time.sleep(5)

# Clients
influxPending = True
if db_name != 'none':
    while influxPending:
        try:
            print('Setup InfluxDB Client... ', end='')
            influx = InfluxDBClient(host=settings.get('influx', 'host', fallback='localhost'),
                                    port=settings.getint('influx', 'port', fallback=8086),
                                    username=settings.get('influx', 'username', fallback=None),
                                    password=settings.get('influx', 'password', fallback=None),
                                    database=db_name)
            influx.create_database(db_name)
            print('Done!')
            influxPending = False
        except:
            print('Failed to connect to Influx')
            time.sleep(10)

print('Setup Serial Connection... ', end='')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
print('Dome!')

print('Loading meters... ')
print(settings.sections())
meters = []
for section in settings.sections():
    print(section)
    if not section.startswith('meters.'):
        continue

    print("Adding")
    name = section[7:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    meter = SDM230Meter(client=client, name=name, unit=unit)
    meter.print_info()
    meters.append({
        'error_sleep': 0,
        'meter': meter,
        'measurement': measurement
    })
print('Done!')
print(meters)

while True:
    online = False
    for meter in meters:
        # If this inverter errored then we wait a bit before trying again
        if meter['error_sleep'] > 0:
            meter['error_sleep'] -= interval
            continue

        sdm230 = meter['meter']
        try:
            now = time.time()
            info = sdm230.read()

            if info is None:
                continue

            # Mark that at least one inverter is online so we should continue collecting data
            online = True

            points = [{
                'time': int(now),
                'measurement': meter['measurement'],
                "fields": info
            }]
            if debug == '1':
                print(sdm230.name)
                print(points)

            if not influxPending:
                if not influx.write_points(points, time_precision='s'):
                    print("Failed to write to DB!")
        except Exception as err:
            print(sdm230.name)
            print(err)
            meter['error_sleep'] = error_interval

    if online:
        time.sleep(interval)
    else:
        # If all the inverters are not online because no power is being generated then we sleep for 1 min
        time.sleep(offline_interval)
