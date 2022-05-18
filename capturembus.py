#!/usr/bin/env python3
from pymodbus.client.sync import ModbusSerialClient as ModbusClient


client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()

While True:
    