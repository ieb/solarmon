#!/usr/bin/env python3

import os
import struct
from configparser import RawConfigParser
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusIOException

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '../solarmon.cfg')

port = settings.get('query', 'port', fallback='/dev/ttyUSB1')

print('Setup Serial Connection... ', end='')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
print('Dome!')


registerfile = open("holdingregisters.bin", "wb")

for rnum in range(0,4000,20):
    row = client.read_holding_registers(rnum, count=20, unit=1)
    try:
        print(rnum)
        print(row.registers)
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
        registerfile.write(payload)
    except:
        print(row)
        payload = bytearray(40)
        registerfile.write(payload)


registerfile.close()

registerfile = open("inputregisters.bin", "wb")

for rnum in range(0,4000,20):
    row = client.read_input_registers(rnum, count=20, unit=1)
    try:
        print(rnum)
        print(row.registers)
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
        registerfile.write(payload)
    except:
        print(row)
        payload = bytearray(40)
        registerfile.write(payload)


registerfile.close()


