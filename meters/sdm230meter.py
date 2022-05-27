
import datetime
from pymodbus.exceptions import ModbusIOException


#
#Input registers
SDM230Registers = {
    'LineToNeutral':            0x000,  #30001,Line to neutral volts.,Volts,0x0000
    'Current':                  0x0006, #30007,Current.,Amps,0x0006
    'ActivePower':              0x000C, #30013,Active power.,Watts,0x000C
    'ApparentPower':            0x0012, #30019,Apparent power,VoltAmps,0x0012
    'ReactivePower':            0x0018, #30025.Reactive power,VAr,0x0018
    'PowerFactor':              0x001E, #30031, #Power factor,None,0x001E
    'PhaseAngle':               0x0024, #30037,Phase angle.,Degree,0x0024
    'Frequency':                0x0046, #30071,Frequency,Hz,0x0046
    'ImportActiveEnergy':       0x0048, #30073,Import active energy,kwh,0x0048
    'ExportActiveEnergy':       0x004A, #30075,Export active energy,kwh,0x004A
    'ImportReactiveEnergy':     0x004C, #30077,Import reactive energy,kvarh,0x004C
    'ExportReactiveEnergy':     0x004E, #30079,Export reactive energy,kvarh,0x004E
    'TotalW':                   0x0054, #30085,Total system power demand,W,0x0054
    'MaximumTotalW':            0x0056, #30087,Maximum total system power demand,W,0x0056
    'ImportW':                  0x0058, #30089,Current system positive power demand,W,0x0058
    'MaximimImportW':           0x005A, #30091,Maximum system positive power demand,W,0x005A
    'ExportW':                  0x005C, #30093,Current system reverse power demand,W,0x005C
    'MaximumExportW':           0x005E, #30095,Maximum system reverse power demand,W,0x005E
    'CurrentA':                 0x0102, #30259,Current demand.,Amps,0x0102
    'MaximumCurrentA':          0x0108, #30265,Maximum current demand.,Amps,0x0108
    'TotalActiveEnergy':        0x0156, #30343,Total active energy,kwh,0x0156
    'TotalReactiveEnergy':      0x0158, #30345,Total reactive energy,kvarh,0x0158
    'ResetableActiveEnergy':    0x0180, #30385,Current resettable total active energy,kwh,0x0180
    'ResettableReactiveEnergy': 0x0182, #30387,Current resettable total reactive energy,kvarh,0x0182
}


import struct

def merge(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result


class SDM230Meter:
    def __init__(self, client, name, unit):
        self.client = client
        self.name = name
        self.unit = unit


    def read_info(self):
        return


    def print_info(self):
        return

    def read_float(self, payload, register):
        return struct.unpack("!f", payload[register*2:register*2+4])[0]


    def read(self):
        #'LineToNeutral':            0x000,  #30001,Line to neutral volts.,Volts,0x0000
        #'Current':                  0x0006, #30007,Current.,Amps,0x0006
        #'ActivePower':              0x000C, #30013,Active power.,Watts,0x000C
        #'ApparentPower':            0x0012, #30019,Apparent power,VoltAmps,0x0012
        #'ReactivePower':            0x0018, #30025.Reactive power,VAr,0x0018
        row = self.client.read_input_registers(0, 30, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = {                                    # ==================================================================
            'LineToNeutral': self.read_float(payload, 0),
            'Current': self.read_float(payload, 6),
            'ActivePower': self.read_float(payload, 12),
            'ApparentPower': self.read_float(payload,18),
            'ReactivePower': self.read_float(payload,24)
        }

        # 'PowerFactor':              0x001E, #30031, #Power factor,None,0x001E
        # 'PhaseAngle':               0x0024, #30037,Phase angle.,Degree,0x0024

        row = self.client.read_input_registers(30, 10, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = merge(info, {                                    # ==================================================================
            'PowerFactor': self.read_float(payload, 30-30),
            'PhaseAngle': self.read_float(payload, 36-30),
        })
        
        # 'Frequency':                0x0046, #30071,Frequency,Hz,0x0046
        # 'ImportActiveEnergy':       0x0048, #30073,Import active energy,kwh,0x0048
        # 'ExportActiveEnergy':       0x004A, #30075,Export active energy,kwh,0x004A
        # 'ImportReactiveEnergy':     0x004C, #30077,Import reactive energy,kvarh,0x004C
        # 'ExportReactiveEnergy':     0x004E, #30079,Export reactive energy,kvarh,0x004E
        # 'TotalW':                   0x0054, #30085,Total system power demand,W,0x0054
        # 'MaximumTotalW':            0x0056, #30087,Maximum total system power demand,W,0x0056
        # 'ImportW':                  0x0058, #30089,Current system positive power demand,W,0x0058
        # 'MaximimImportW':           0x005A, #30091,Maximum system positive power demand,W,0x005A
        # 'ExportW':                  0x005C, #30093,Current system reverse power demand,W,0x005C
        # 'MaximumExportW':           0x005E, #30095,Maximum system reverse power demand,W,0x005E


        row = self.client.read_input_registers(70, 30, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = merge(info, {                                    # ==================================================================
            'Frequency': self.read_float(payload, 70-70),
            'ImportActiveEnergy': self.read_float(payload, 72-70),
            'ExportActiveEnergy': self.read_float(payload, 74-70),
            'ImportReactiveEnergy': self.read_float(payload, 76-70),
            'ExportReactiveEnergy': self.read_float(payload, 78-70),
            'TotalW': self.read_float(payload, 84-70),
            'MaximumTotalW': self.read_float(payload, 86-70),
            'ImportW': self.read_float(payload, 88-70),
            'MaximimImportW': self.read_float(payload, 90-70),
            'ExportW': self.read_float(payload, 92-70),
            'MaximumExportW': self.read_float(payload, 94-70),
        })

        # 'CurrentA':                 0x0102, #30259,Current demand.,Amps,0x0102
        # 'MaximumCurrentA':          0x0108, #30265,Maximum current demand.,Amps,0x0108
        row = self.client.read_input_registers(258, 8, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = merge(info, {                                    # ==================================================================
            'CurrentA': self.read_float(payload, 258-258),
            'MaximumCurrentA': self.read_float(payload, 264-264),
        })

        # 'TotalActiveEnergy':        0x0156, #30343,Total active energy,kwh,0x0156
        # 'TotalReactiveEnergy':      0x0158, #30345,Total reactive energy,kvarh,0x0158
        row = self.client.read_input_registers(342, 4, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = merge(info, {                                    # ==================================================================
            'TotalActiveEnergy': self.read_float(payload, 342-342),
            'TotalReactiveEnergy': self.read_float(payload, 344-342),
        })

        # 'ResetableActiveEnergy':    0x0180, #30385,Current resettable total active energy,kwh,0x0180
        # 'ResettableReactiveEnergy': 0x0182, #30387,Current resettable total reactive energy,kvarh,0x0182
        row = self.client.read_input_registers(384, 4, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # believed to be bigendian words, little endian bytes
        payload = b"".join(struct.pack("!H", x) for x in row.registers)
 
        info = merge(info, {                                    # ==================================================================
            'ResetableActiveEnergy': self.read_float(payload, 384-384),
            'ResettableReactiveEnergy': self.read_float(payload, 386-384),
        })


        return info
        