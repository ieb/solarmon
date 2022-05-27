
import argparse
import sys
import serial
import struct
import time
from datetime import datetime

# heavilly based on https://github.com/sourceperl/modbus-serial-monitor/blob/master/scripts/modbus-scan-serial
# because python is not my native language.

SEP = ";"
PARITY = {'N': serial.PARITY_NONE, 'E': serial.PARITY_EVEN, 'O': serial.PARITY_ODD,
          'M': serial.PARITY_MARK, 'S': serial.PARITY_SPACE}
STOP = {'1': serial.STOPBITS_ONE, '1.5': serial.STOPBITS_ONE_POINT_FIVE, '2': serial.STOPBITS_TWO}


class ModbusRegister:
    def __init__(self, settings ):
        self.request_frame = {}
        self.registers = {}
        self.baudrate = settings.get('gateway', 'baudrate', fallback=9600)
        self.parity = PARITY[settings.get('gateway', 'parity', fallback='N')]
        self.stopbits = STOP[settings.get('gateway', 'stopbits', fallback='1')]
        self.device = settings.get('gateway', 'device', fallback='/dev/ttyUSB1')
        self.debug = settings.get('gateway', 'debug', fallback=0)

        # modbus end of frame is a tx silent of [3.5 * byte tx time * 30% margin] seconds
        self.timeout = (1.0 / self.baudrate) * 11.0 * 3.5 * 1.3
        self.timeout = settings.get('gateway', 'timeout', fallback=self.timeout)
        self.request_timeout = settings.get('gateway', 'request_timeout', fallback=self.timeout*64)


    def connect(self):

        # init serial object
        self.ser = serial.Serial(self.device, self.baudrate, parity=self.parity, stopbits=self.stopbits,
                            timeout=self.timeout)

        # wait serial start and flush all
        time.sleep(.5)
        self.ser.read(self.ser.inWaiting())

    def close(self):
        self.ser.close()




    def read(self):
        frame = bytes(self.ser.read(256))
        # skip null frame
        if not frame:
            return
        # init vars
        err_str = "NO"
        device_id = 0
        f_code = 0
        e_code = 0
        # add date and time
        now = datetime.now()
        date = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        # format modbus frame as txt string
        txt_frame = ''
        for item in bytearray(frame):
            if txt_frame:
                txt_frame += "-"
            txt_frame += "%02x" % item
        # check short frame
        if len(frame) >= 5:
            # check CRC
            r_crc = struct.unpack("<H", frame[-2:])[0]
            c_crc = self.frame2crc(frame[:-2])
            crc_ok = (r_crc == c_crc)
            if not crc_ok:
                err_str = "BAD_CRC"
            else:
                # device ID
                device_id = struct.unpack("B", frame[0:1])[0]
                # function code
                f_code = struct.unpack("B", frame[1:2])[0]
                # except code
                if f_code > 0x80:
                    err_str = "EXCEPT_FRAME"
                    e_code = struct.unpack("B", frame[2:3])[0]
                self.processRegisters(f_code, device_id, frame);

        else:
            err_str = "SHORT_FRAME"
        # send result to stdout
        if self.debug == 1:
            items = ['DATE=%s' % date, 'ERR=%s' % err_str, 'FRAME=%s' % txt_frame, 'device=%s' % device_id]
            csv_line = SEP.join(items)
            print(csv_line)
            sys.stdout.flush()

    def processRegisters(self, f_code, device_id, frame):
        if f_code == 4: # input registers
            dataBytes = struct.unpack('B',frame[2:3])[0]
            if (len(frame) == 8) and (len(frame) != dataBytes+3):
                # request from master to device
                self.request_frame[device_id] = {
                    'frame': frame,
                    'start': struct.unpack('<H',frame[2:4]),
                    'count': struct.unpack('<H', frame[4:6]),
                    'recieved': datetime.now()
                }
                print(self.request_frame[device_id])
            elif device_id in self.request_frame:
                # have a request outstanding
                if ((datetime.now() - self.request_frame[device_id]['recieved']).total_seconds()) < self.request_timeout:
                    # frame timeout not reached, process
                    startRegister = self.request_frame[device_id]['start']
                    nRegisters = self.request_frame[device_id]['count']
                    if dataBytes != nRegisters*2:
                        print("Warning, not enough bytes returned got "+str(dataBytes)+" expected "+str(nRegisters*2))

                    self.extendRegisters(device_id,startRegister+dataBytes+1)


                    # store the registers against the device
                    self.registers[device_id][startRegister:startRegister+dataBytes] = frame[4:4+dataBytes]


                del self.request_frame[device_id]


    def extendRegisters(self, device_id, newSize):
        if not (device_id in self.registers):
            regsize = 0
            newregsize = 4096
        else:
            regsize = len(self.registers[device_id])
            newregsize = regsize

        # need to extend the registers in 4K chunks
        while newSize > newregsize and newregsize < 0xffff:
            newregsize = newregsize + 4096 

        if newregsize > regsize:
            print("Extending "+str(device_id)+" registers to "+str(newregsize))
            newregisters = bytearray(newregsize)
            if regsize > 0:
                newregisters[0:regsize] = self.registers[device_id][0:regsize]
            self.registers[device_id] = newregisters


    def getFloat(self, device_id, reg):
        return struct.unpack("<f", self.registers[device_id][reg:reg+4])

    def getInt16(self, device_id, reg):
        return struct.unpack("<h", self.registers[device_id][reg:reg+2])

    def getUInt16(self, device_id, reg):
        return struct.unpack("<H", self.registers[device_id][reg:reg+2])
    def getInt32(self, device_id, reg):
        return struct.unpack("<i", self.registers[device_id][reg:reg+2])

    def getUInt32(self, device_id, reg):
        return struct.unpack("<I", self.registers[device_id][reg:reg+2])



    def frame2crc(self, frame):
        """Compute modbus CRC16 (for RTU mode)
        :param label: modbus frame
        :type label: str (Python2) or class bytes (Python3)
        :returns: CRC16
        :rtype: int
        """
        crc = 0xFFFF
        for index, item in enumerate(bytearray(frame)):
            next_byte = item
            crc ^= next_byte
            for i in range(8):
                lsb = crc & 1
                crc >>= 1
                if lsb:
                    crc ^= 0xA001
        return crc


