#!/usr/bin/env python3

import os
import sys
import struct
from configparser import RawConfigParser
from pymodbus.client.sync import ModbusSerialClient as ModbusClient
from pymodbus.exceptions import ModbusIOException

settings = RawConfigParser()
settings.read(os.path.dirname(os.path.realpath(__file__)) + '/solarmon.cfg')

port = settings.get('query', 'port', fallback='/dev/ttyUSB1')
unit = settings.get('inverter.main', 'unit', fallback=1)

print('Setup Serial Connection... ', end='')
client = ModbusClient(method='rtu', port=port, baudrate=9600, stopbits=1, parity='N', bytesize=8, timeout=1)
client.connect()
print('Done!')

def toAscii(registers):
    b = bytearray(len(registers)*2)
    ashex = list()
    i = 0
    for x in registers:
        ashex.append('{:02x}'.format(x))
        struct.pack_into("!H",b,i,x)
        i+=2
    #print(ashex)
    #print(len(registers), b)
    return b.decode('ascii')

def dumpAsHex(registers):
    ashex = list()
    for x in registers:
        ashex.append('{:02x}'.format(x))
    print(ashex)

def packAscii(value):
    registers = list()
    abytes = value.encode('ascii')
    print(abytes)
    i = 0
    v = 0
    for b in abytes:
        v = v*256
        v = v+b
        if i == 1:
            registers.append(v)
            i = 0
            v = 0
        else:
            i += 1
    if i == 1:
        v = v*256
        registers.append(v)
    return registers
        

def dumpAsAscii(registers):
    b = bytearray(len(registers)*2)
    i = 0
    for x in registers:
        struct.pack_into("!H",b,i,x)
        i+=2
    print(len(registers), b)
    print(b.decode('ascii'))


# get the serial number
row = client.read_holding_registers(23, count=5, unit=unit)
print("Old style serial number:", toAscii(row.registers))
row = client.read_holding_registers(209, count=15, unit=unit)
print("Serial Number:", toAscii(row.registers))
row = client.read_holding_registers(3001, count=15, unit=unit)
print("New Serial Number:", toAscii(row.registers))

row = client.read_holding_registers(125, count=8, unit=unit)
print("Inverter Type", toAscii(row.registers))

row = client.read_holding_registers(88, unit=unit)
modbusVersion = row.registers[0]/100
print("ModbusVersion:", modbusVersion)

row = client.read_holding_registers(9, count=3, unit=unit)
print("Firmware Version:", toAscii(row.registers))

row = client.read_holding_registers(12, count=3, unit=unit)
print("Control Firmware Version:", toAscii(row.registers))

row = client.read_holding_registers(133, count=4 ,unit=unit)
print("Bootloader Version:", toAscii(row.registers))

row = client.read_holding_registers(45, count=6, unit=unit)
print("Localtime {day:02d}/{month:02d}/{year:04d} {hour:02d}:{min:02d}:{sec:02d}".format(
    year=row.registers[0],
    month=row.registers[1],
    day=row.registers[2], 
    hour=row.registers[3],
    min=row.registers[4],
    sec=row.registers[5]))

#print("Control Firmware Version:", toAscii(row.registers))

# export enabled ?
row = client.read_holding_registers(122, count=2, unit=unit)
exportControlEnabled = row.registers[0]
exportLimitPowerRate = row.registers[1]*0.1
if exportControlEnabled == 0:
    print("Export Control Disabled") 
if exportControlEnabled == 1:
    print("Export Control RS485 Meter")
if exportControlEnabled == 2:
    print("Export Control RS232 Meter") 
if exportControlEnabled == 3:
    print("Export Control Current Transformer") 
print("Export Power Limit:", exportLimitPowerRate)

row = client.read_holding_registers(42, count=2, unit=unit)
g100FailSafe  = row.registers[0]
if g100FailSafe == 0:
    print("G100 Fail safe Disabled") 
if g100FailSafe == 1:
    print("G100 Fail safe Enabled") 
row = client.read_holding_registers(3000, count=1, unit=unit)
g100FailSafeRate  = row.registers[0]*0.1
print("Export Power Failsafe Limit:", g100FailSafeRate)

row = client.read_holding_registers(3016, count=1, unit=unit)
dryContactEnable  = row.registers[0]
if dryContactEnable == 0:
    print("DryContact Disabled")
if dryContactEnable == 1:
    print("DryContact Enabled")
row = client.read_holding_registers(3017, count=3, unit=unit)
dryContactOnRate  = row.registers[0]*0.1
dryContactOffRate  = row.registers[2]*0.1
print("DryContact On:", dryContactOnRate)
print("DryContact Off:", dryContactOffRate)


# seems to be read by monitors to control external access at the remote
# end. Doesnt appear to be needed when setting values over modbus
row = client.read_holding_registers(3125, count=4, unit=unit)
print("Key:", toAscii(row.registers))


row = client.read_holding_registers(8, count=1, unit=unit)
print("Normal Work PV Voltage:", row.registers[0]*0.1)
row = client.read_holding_registers(17, count=1, unit=unit)
print("PV Start Voltage:", row.registers[0]*0.1)
row = client.read_holding_registers(81, count=1, unit=unit)
print("PV Voltage High Fault:", row.registers[0]*0.1)
row = client.read_holding_registers(124, count=1, unit=unit)
if row.registers[0] == 0:
    print("Independent tracker model")
if row.registers[0] == 1:
    print("DC Source tracker model")
if row.registers[0] == 2:
    print("Paralleltracker model")
row = client.read_holding_registers(238, count=1, unit=unit)
print("Fast MPPT Enable:", row.registers[0])


row = client.read_holding_registers(241, count=2, unit=unit)
print("Latitude:", row.registers[0])
print("Longitude:", row.registers[0])


if (len(sys.argv) > 1) and (sys.argv[1] == 'set'):
    print("Set Export Power Limit")
    row = client.write_register(123, value=876, unit=unit)
    print("Response", row)
    row = client.read_holding_registers(123, count=2, unit=unit)
    exportLimitPowerRate = row.registers[0]*0.1
    print("Export Power Limit:", exportLimitPowerRate)
    row = client.write_register(123, value=875, unit=unit)
    print("Response", row)
    row = client.read_holding_registers(123, count=2, unit=unit)
    exportLimitPowerRate = row.registers[0]*0.1
    print("Export Power Limit:", exportLimitPowerRate)


    row = client.write_register(3000, value=876, unit=unit)
    row = client.read_holding_registers(3000, count=1, unit=unit)
    g100FailSafeRate  = row.registers[0]*0.1
    print("Export Power Failsafe Limit:", g100FailSafeRate)
else:
    print("Dry run, use ./setExportLimit.py set to update export limits  ")




