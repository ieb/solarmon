


#
#Input registers,
# each register is a 2 byte so multiply the register number by 2 to get the offset
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




class SDM230:
    def __init__(self, modbusRegister, unit):
        self.modbusRegister = modbusRegister
        self.unit = unit


    def read(self):
        return {
            'LineToNeutral': self.modbusRegister.getFloat( self.unit, SDM230Registers['LineToNeutral']),
            'Current': self.modbusRegister.getFloat( self.unit, SDM230Registers['Current']),
            'ActivePower': self.modbusRegister.getFloat( self.unit, SDM230Registers['ActivePower']),
            'ApparentPower': self.modbusRegister.getFloat( self.unit, SDM230Registers['ApparentPower']),
            'ReactivePower': self.modbusRegister.getFloat( self.unit, SDM230Registers['ReactivePower']),
            'PowerFactor': self.modbusRegister.getFloat( self.unit, SDM230Registers['PowerFactor']),
            'PhaseAngle': self.modbusRegister.getFloat( self.unit, SDM230Registers['PhaseAngle']),
            'Frequency': self.modbusRegister.getFloat( self.unit, SDM230Registers['Frequency']),
            'ImportActiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ImportActiveEnergy']),
            'ExportActiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ExportActiveEnergy']),
            'ImportReactiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ImportReactiveEnergy']),
            'ExportReactiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ExportReactiveEnergy']),
            'TotalW': self.modbusRegister.getFloat( self.unit, SDM230Registers['TotalW']),
            'MaximumTotalW': self.modbusRegister.getFloat( self.unit, SDM230Registers['MaximumTotalW']),
            'ImportW': self.modbusRegister.getFloat( self.unit, SDM230Registers['ImportW']),
            'MaximimImportW': self.modbusRegister.getFloat( self.unit, SDM230Registers['MaximimImportW']),
            'ExportW': self.modbusRegister.getFloat( self.unit, SDM230Registers['ExportW']),
            'MaximumExportW': self.modbusRegister.getFloat( self.unit, SDM230Registers['MaximumExportW']),
            'CurrentA': self.modbusRegister.getFloat( self.unit, SDM230Registers['CurrentA']),
            'MaximumCurrentA': self.modbusRegister.getFloat( self.unit, SDM230Registers['MaximumCurrentA']),
            'TotalActiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['TotalActiveEnergy']),
            'TotalReactiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['TotalReactiveEnergy']),
            'ResetableActiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ResetableActiveEnergy']),
            'ResettableReactiveEnergy': self.modbusRegister.getFloat( self.unit, SDM230Registers['ResetableActiveEnergy']),
        }



        