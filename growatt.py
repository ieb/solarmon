import datetime
from pymodbus.exceptions import ModbusIOException

# Updated for v130 whcih seems to be close to a 2022 Growatt 4200 TL XE 1 phase, 2 PV model

# Codes
StateCodes = {
    0: 'Waiting',
    1: 'Normal',
    3: 'Fault'
}

# No change in v120
ErrorCodes = {
    0: 'None',
    24: 'Auto Test Failed',
    25: 'No AC Connection',
    26: 'PV Isolation Low',
    27: 'Residual Current High',
    28: 'DC Current High',
    29: 'PV Voltage High',
    30: 'AC Voltage Outrange',
    31: 'AC Freq Outrange',
    32: 'Module Hot'
}



for i in range(1, 24):
    ErrorCodes[i] = "Error Code: %s" % str(99 + i)

DeratingMode = {
    0: 'No Deratring',
    1: 'PV',
    2: '',
    3: 'Vac',
    4: 'Fac',
    5: 'Tboost',
    6: 'Tinv',
    7: 'Control',
    8: '*LoadSpeed',
    9: '*OverBackByTime',
    10: 'cInternalTemprDerate',
    11: 'cOutTemprDerate',
    12: 'cLineImpeCalcDerate',
    13: 'cParallelAntiBackflowDerate',
    14: 'cLocalAntiBackflowDerate',
    15: 'cBdcLoadPriDerate',
    16: 'cChkCTErrDerate',
}

FaultCode = {
    0x1: '?',
   0x2: 'Communication error',
   0x4: '?',
   0x8: 'StrReverse or StrShort fault',
   0x10: 'Model Init fault',
   0x20: 'Grid Volt Sample diffirent',
   0x40: 'ISO Sample diffirent',
   0x80: 'GFCI Sample diffirent',
   0x100: '?',
   0x200: '?',
   0x400: '?',
   0x800: '?',
   0x1000: 'AFCI Fault',
   0x2000: '?',
   0x4000: 'AFCI Module fault',
   0x8000: '?',
   0x10000: '?',
   0x20000: 'Relay check fault',
   0x40000: '?',
   0x80000: '?',
   0x100000: '?',
   0x200000: 'Communication error',
   0x400000: 'Bus Voltage error',
   0x800000: 'AutoTest fail',
   0x1000000: 'No Utility',
   0x2000000: 'PV Isolation Low',
   0x4000000: 'Residual I High',
   0x8000000: 'Output High DCI',
   0x10000000: 'PV Voltage high',
   0x20000000: 'AC V Outrange',
   0x40000000: 'AC F Outrange',
   0x80000000: 'TempratureHigh',

}
WarnCode = {
        0x1: 'Fan warning',
   0x2: 'String communication abnormal',
   0x4: 'StrPIDconfig Warning',
   0x8: '?',
   0x10: 'DSP and COM firmware unmatch',
   0x20: '?',
   0x40: 'SPD abnormal',
   0x80: 'GND and N connect abnormal',
   0x100:  'PV1 or PV2 circuit short',
   0x200: 'PV1 or PV2 boost driver broken',
   0x400: '?',
   0x800: '?',
   0x1000: '?',
   0x2000: '?',
   0x4000: '?',
   0x8000: '?',

}


def read_single(row, index, unit=10):
    return float(row.registers[index]) / unit

def read_double(row, index, unit=10):
    return float((row.registers[index] << 16) + row.registers[index + 1]) / unit

def read_lookup(row, index, lookup):
    value = row.registers[index]
    if ( value in lookup ):
        return lookup[value]
    return "none"

def read_hex(row, index):
    value = ((row.registers[index] << 16) + row.registers[index + 1])
    return hex(value)

def read_bitCode(row, index , codes=FaultCode):
    value = ((row.registers[index] << 16) + row.registers[index + 1])
    list = []
    for k,v in codes.items():
        if ( value&k == k):
            list.append(v)
    if len(list) == 0:
        return "none"
    return ','.join(list)


def merge(*dict_args):
    result = {}
    for dictionary in dict_args:
        result.update(dictionary)
    return result

class Growatt:
    def __init__(self, client, name, unit):
        self.client = client
        self.name = name
        self.unit = unit

        self.read_info()

    def read_info(self):
        row = self.client.read_holding_registers(88, unit=self.unit)
        if type(row) is ModbusIOException:
            self.modbusVersion = -1
            self.exportControlEnabled = -1
            self.exportLimitPowerRate = -1
            return


        self.modbusVersion = row.registers[0]
        # export enabled ?
        row = self.client.read_holding_registers(122, unit=self.unit)
        if type(row) is ModbusIOException:
            self.exportControlEnabled = -1
            self.exportLimitPowerRate = -1
            return
        self.exportControlEnabled = row.registers[0]
        row = self.client.read_holding_registers(123, unit=self.unit)
        if type(row) is ModbusIOException:
            self.exportLimitPowerRate = -1
            return
        self.exportLimitPowerRate = row.registers[0]*0.1

    def print_info(self):
        print('Growatt:')
        print('\tName: ' + str(self.name))
        print('\tUnit: ' + str(self.unit))
        print('\tModbus Version: ' + str(self.modbusVersion))
        print('\tExport Limit Enabled: ' + str(self.exportControlEnabled))
        print('\tExport Limit        : ' + str(self.exportLimitPowerRate)+ '%')

    def read(self):
        row = self.client.read_input_registers(0, 12, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None

        # doc v120 registers
        #                                           # Unit,     Variable Name,      Description
        info = {                                    # ==================================================================
            'StatusCode': row.registers[0],         # N/A,      Inverter Status,    Inverter run state
            'Status': StateCodes[row.registers[0]],
            'Ppv': read_double(row, 1),             # 0.1W,     Ppv H,              Input power (high)
                                                    # 0.1W,     Ppv L,              Input power (low)
            'Vpv1': read_single(row, 3),            # 0.1V,     Vpv1,               PV1 voltage
            'PV1Curr': read_single(row, 4),         # 0.1A,     PV1Curr,            PV1 input current
            'PV1Watt': read_double(row, 5),         # 0.1W,     PV1Watt H,          PV1 input watt (high)
                                                    # 0.1W,     PV1Watt L,          PV1 input watt (low)
            'Vpv2': read_single(row, 7),            # 0.1V,     Vpv2,               PV2 voltage
            'PV2Curr': read_single(row, 8),         # 0.1A,     PV2Curr,            PV2 input current
            'PV2Watt': read_double(row, 9),         # 0.1W,     PV2Watt H,          PV2 input watt (high)
                                                    # 0.1W,     PV2Watt L,          PV2 input watt (low)
        }

        row = self.client.read_input_registers(35, 7, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None
        info = merge( info, {
            'Pac': read_double(row, 35-35),            # 0.1W,     Pac H,              Output power (high)
                                                       # 0.1W,     Pac L,              Output power (low)
            'Fac': read_single(row, 37-35, 100),       # 0.01Hz,   Fac,                Grid frequency
            'Vac1': read_single(row, 38-35),           # 0.1V,     Vac1,               Three/single phase grid voltage
            'Iac1': read_single(row, 39-35),           # 0.1A,     Iac1,               Three/single phase grid output current
            'Pac1': read_double(row, 40-35),           # 0.1VA,    Pac1 H,             Three/single phase grid output watt (high)
                                                    # 0.1VA,    Pac1 L,             Three/single phase grid output watt (low)
        })

        row = self.client.read_input_registers(53, 14, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None
        info = merge( info, {
            'EnergyToday': read_double(row, 53-53),    # 0.1kWh,   Energy today H,     Today generate energy (high)
                                                    # 0.1kWh,   Energy today L,     Today generate energy today (low)
            'EnergyTotal': read_double(row, 55-53),    # 0.1kWh,   Energy total H,     Total generate energy (high)
                                                    # 0.1kWh,   Energy total L,     Total generate energy (low)
            'TimeTotal': read_double(row, 57-53, 2),   # 0.5S,     Time total H,       Work time total (high)
                                                    # 0.5S,     Time total L,       Work time total (low)
            'Epv1_today': read_double(row, 59-53),  # 0.1kWh,   Energy today H,     pv1 generate energy (high)
                                                    # 0.1kWh,   Energy today L,     pv1 generate energy today (low)
            'Epv1_total': read_double(row, 61-53),    # 0.1kWh,   Energy total H,     pv2 generate energy (high)
                                                    # 0.1kWh,   Energy total L,     pv2 generate energy (low)
            'Epv2_today': read_double(row, 63-53),  # 0.1kWh,   Energy today H,     pv1 generate energy (high)
                                                    # 0.1kWh,   Energy today L,     pv1 generate energy today (low)
            'Epv2_total': read_double(row, 65-53),    # 0.1kWh,   Energy total H,     pv2 generate energy (high)
                                                    # 0.1kWh,   Energy total L,     pv2 generate energy (low)

        })

        row = self.client.read_input_registers(93, 3, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None
        info = merge( info, {
            'TempInverter': read_single(row, 93-93),           # 0.1C,     Inverter Temperature
            'TempIpm': read_single(row, 94-93),           # 0.1C,     Imp Temperature
            'TempBoost': read_single(row, 95-93),           # 0.1C,     Boost Temperature
        })

        row = self.client.read_input_registers(100, 12, unit=self.unit)
        if type(row) is ModbusIOException:
            print(row)
            return None
        info = merge( info, {
            'IPF': read_single(row, 100-100, 1),           # 0.1C,     Inverter output PF now
            'RealOPPercent': read_single(row, 101-100, 100),      # percent,     Real Output power Percent
            'OPFullwatt': read_double(row, 102-100),           # 0.1C,     Boost Temperature
            'DeratingMode': read_lookup(row, 104-100, DeratingMode),
            'DeratingModeCode': row.registers[104-100],
            'Fault': read_bitCode(row, 106-100, FaultCode),
            'FaultBitCode': read_hex(row, 106-100),
            'Warn': read_bitCode(row, 110-100, WarnCode),
            'WarnBitCode': read_hex(row, 110-100),
        })

 
            


        #row = self.client.read_input_registers(33, 8, unit=self.unit)
        #info = merge(info, {
        #    'ISOFault': read_single(row, 0),        # 0.1V,     ISO fault Value,    ISO Fault value
        #    'GFCIFault': read_single(row, 1, 1),    # 1mA,      GFCI fault Value,   GFCI fault Value
        #    'DCIFault': read_single(row, 2, 100),   # 0.01A,    DCI fault Value,    DCI fault Value
        #    'VpvFault': read_single(row, 3),        # 0.1V,     Vpv fault Value,    PV voltage fault value
        #    'VavFault': read_single(row, 4),        # 0.1V,     Vac fault Value,    AC voltage fault value
        #    'FacFault': read_single(row, 5, 100),   # 0.01 Hz,  Fac fault Value,    AC frequency fault value
        #    'TempFault': read_single(row, 6),       # 0.1C,     Temp fault Value,   Temperature fault value
        #    'FaultCode': row.registers[7],          #           Fault code,         Inverter fault bit
        #    'Fault': ErrorCodes[row.registers[7]]
        #})

        # row = self.client.read_input_registers(41, 1, unit=self.unit)
        # info = merge_dicts(info, {
        #    'IPMTemp': read_single(row, 0),         # 0.1C,     IPM Temperature,    The inside IPM in inverter Temperature
        # })

        #row = self.client.read_input_registers(42, 2, unit=self.unit)
        #info = merge(info, {
        #    'PBusV': read_single(row, 0),           # 0.1V,     P Bus Voltage,      P Bus inside Voltage
        #    'NBusV': read_single(row, 1),           # 0.1V,     N Bus Voltage,      N Bus inside Voltage
        #})

        # row = self.client.read_input_registers(44, 3, unit=self.unit)
        # info = merge_dicts(info, {
        #                                            #           Check Step,         Product check step
        #                                            #           IPF,                Inverter output PF now
        #                                            #           ResetCHK,           Reset check data
        # })
        #
        # row = self.client.read_input_registers(47, 1, unit=self.unit)
        # info = merge_dicts(info, {
        #    'DeratingMode': row.registers[6],       #           DeratingMode,       DeratingMode
        #    'Derating': DeratingMode[row.registers[6]]
        # })

        #row = self.client.read_input_registers(48, 16, unit=self.unit)
        #info = merge(info, {
        #    'Epv1_today': read_double(row, 0),      # 0.1kWh,   Epv1_today H,       PV Energy today
        #                                            # 0.1kWh,   Epv1_today L,       PV Energy today
        #    'Epv1_total': read_double(row, 2),      # 0.1kWh,   Epv1_total H,       PV Energy total
        #                                            # 0.1kWh,   Epv1_total L,       PV Energy total
        #    'Epv2_today': read_double(row, 4),      # 0.1kWh,   Epv2_today H,       PV Energy today
        #                                            # 0.1kWh,   Epv2_today L,       PV Energy today
        #    'Epv2_total': read_double(row, 6),      # 0.1kWh,   Epv2_total H,       PV Energy total
        #                                            # 0.1kWh,   Epv2_total L,       PV Energy total
        #    'Epv_total': read_double(row, 8),       # 0.1kWh,   Epv_total H,        PV Energy total
        #                                            # 0.1kWh,   Epv_total L,        PV Energy total
        #    'Rac': read_double(row, 10),            # 0.1Var,   Rac H,              AC Reactive power
        #                                            # 0.1Var,   Rac L,              AC Reactive power
        #    'E_rac_today': read_double(row, 12),    # 0.1kVarh, E_rac_today H,      AC Reactive energy
        #                                            # 0.1kVarh, E_rac_today L,      AC Reactive energy
        #    'E_rac_total': read_double(row, 14),    # 0.1kVarh, E_rac_total H,      AC Reactive energy
        #                                            # 0.1kVarh, E_rac_total L,      AC Reactive energy
        #})

        # row = self.client.read_input_registers(64, 2, unit=self.unit)
        # info = merge_dicts(info, {
        #    'WarningCode': row.registers[0],        #           WarningCode,        Warning Code
        #    'WarningValue': row.registers[1],       #           WarningValue,       Warning Value
        # })
        #
        # info = merge_dicts(info, self.read_fault_table('GridFault', 90, 5))

        return info

    # def read_fault_table(self, name, base_index, count):
    #     fault_table = {}
    #     for i in range(0, count):
    #         fault_table[name + '_' + str(i)] = self.read_fault_record(base_index + i * 5)
    #     return fault_table
    #
    # def read_fault_record(self, index):
    #     row = self.client.read_input_registers(index, 5, unit=self.unit)
    #     # TODO: Figure out how to read the date for these records?
    #     print(row.registers[0],
    #             ErrorCodes[row.registers[0]],
    #             '\n',
    #             row.registers[1],
    #             row.registers[2],
    #             row.registers[3],
    #             '\n',
    #             2000 + (row.registers[1] >> 8),
    #             row.registers[1] & 0xFF,
    #             row.registers[2] >> 8,
    #             row.registers[2] & 0xFF,
    #             row.registers[3] >> 8,
    #             row.registers[3] & 0xFF,
    #             row.registers[4],
    #             '\n',
    #             2000 + (row.registers[1] >> 4),
    #             row.registers[1] & 0xF,
    #             row.registers[2] >> 4,
    #             row.registers[2] & 0xF,
    #             row.registers[3] >> 4,
    #             row.registers[3] & 0xF,
    #             row.registers[4]
    #           )
    #     return {
    #         'FaultCode': row.registers[0],
    #         'Fault': ErrorCodes[row.registers[0]],
    #         #'Time': int(datetime.datetime(
    #         #    2000 + (row.registers[1] >> 8),
    #         #    row.registers[1] & 0xFF,
    #         #    row.registers[2] >> 8,
    #         #    row.registers[2] & 0xFF,
    #         #    row.registers[3] >> 8,
    #         #    row.registers[3] & 0xFF
    #         #).timestamp()),
    #         'Value': row.registers[4]
    #     }

