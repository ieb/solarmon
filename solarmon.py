#!/usr/bin/env python3

import time
import os

from configparser import RawConfigParser
from influxdb import InfluxDBClient
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from os.path import exists

from growatt import Growatt

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

interval = settings.getint('query', 'interval', fallback=1)
offline_interval = settings.getint('query', 'offline_interval', fallback=60)
error_interval = settings.getint('query', 'error_interval', fallback=60)
debug = settings.get('query', 'debug', fallback=0)
port = settings.get('query', 'port', fallback='/dev/ttyUSB0')

while not exists(port):
    print("Waiting for ", port);
    time.sleep(5)


db_name = settings.get('influx', 'db_name', fallback='inverter')

# Clients
influxPending = True
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

print('Loading inverters... ')
inverters = []
for section in settings.sections():
    if not section.startswith('inverters.'):
        continue

    name = section[10:]
    unit = int(settings.get(section, 'unit'))
    measurement = settings.get(section, 'measurement')
    growatt = Growatt(client, name, unit)
    growatt.print_info()
    inverters.append({
        'error_sleep': 0,
        'growatt': growatt,
        'measurement': measurement
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

            points = [{
                'time': int(now),
                'measurement': inverter['measurement'],
                "fields": info
            }]
            if debug == 1:
                print(growatt.name)
                print(points)

            if not influx.write_points(points, time_precision='s'):
                print("Failed to write to DB!")
        except Exception as err:
            print(growatt.name)
            print(err)
            inverter['error_sleep'] = error_interval

    if online:
        time.sleep(interval)
    else:
        # If all the inverters are not online because no power is being generated then we sleep for 1 min
        time.sleep(offline_interval)
