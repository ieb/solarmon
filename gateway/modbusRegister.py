
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

EMPTY = bytearray()

class ModbusRegister:
    def __init__(self, settings ):
        self.request_frame = {}
        self.registers = {}
        self.baudrate = settings.get('gateway', 'baudrate', fallback=9600)
        self.parity = PARITY[settings.get('gateway', 'parity', fallback='N')]
        self.stopbits = STOP[settings.get('gateway', 'stopbits', fallback='1')]
        self.device = settings.get('gateway', 'port', fallback='/dev/ttyUSB1')
        self.debug = settings.getint('gateway', 'debug', fallback=0)

        # modbus end of frame is a tx silent of [3.5 * byte tx time * 30% margin] seconds
        self.timeout = (1.0 / self.baudrate) * 10.0 * 3.5 * 1.2
        self.timeout = settings.get('gateway', 'timeout', fallback=self.timeout)
        self.request_timeout = settings.get('gateway', 'request_timeout', fallback=self.timeout*64)
        self.hasRequestFrame = False 


    def connect(self):

        # init serial object
        print("Connecting to ", self.device)
        self.ser = serial.Serial(self.device, self.baudrate, parity=self.parity, stopbits=self.stopbits,
                            timeout=self.timeout)

        # wait serial start and flush all
        time.sleep(.5)
        self.ser.read(self.ser.inWaiting())

    def close(self):
        self.ser.close()




    def read(self):
        dataRead = self.ser.read(2048)
        if not dataRead:
            return
        frame = bytes(dataRead)


        # skip null frame
        # init vars
        err_str = "OK"
        device_id = 0
        f_code = 0
        e_code = 0
        # add date and time
        now = datetime.now()
        date = now.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
        # format modbus frame as txt string
        txt_frame = ''
        txt_crc_expected = ''
        for item in bytearray(frame):
            if txt_frame:
                txt_frame += "-"
            txt_frame += "%02x" % item
        # check short frame
        if len(frame) >= 5:
            # check CRC
            if not self.checkCrc(frame):
                err_str = "BAD_CRC  "
                # process anyway in case it is a follow on packet or partial packet
            else:
                # except code
                if f_code > 0x80:
                    err_str = "EXCEPT_FRAME"
                    e_code = struct.unpack("B", frame[2:3])[0]
            while len(frame) > 0:
                frame = self.processRegisters(frame)
                #if len(frame) > 0:
                #    print("Remainder :",self.frameAsText(frame))

        else:
            err_str = "SHORT_FRAME"
        # send result to stdout
        if self.debug == 1:
            items = ['DATE=%s' % date, 'ERR=%s' % err_str,  "CRC_CALC=%s " % txt_crc_expected, 'FRAME=%s' % txt_frame, 'device=%s' % device_id]
            csv_line = SEP.join(items)
            print(csv_line)
            sys.stdout.flush()

    def checkCrc(self, frame):
        r_crc = struct.unpack("<H", frame[-2:])[0]
        c_crc = self.frame2crc(frame[:-2])
        txt_crc_expected = "%04x %04x" % (c_crc,r_crc) 

        return (r_crc == c_crc)

    def frameAsText(self, frame):
        txt_frame = ""
        for item in frame:
            if txt_frame:
                txt_frame += "-"
            txt_frame += "%02x" % item
        return txt_frame

    def processRegisters(self, frame):

        if self.hasRequestFrame:
            self.response_frame.extend(frame)
            frame = bytearray()
            if len(self.response_frame) > 4:
                dataBytes = struct.unpack('B',self.response_frame[2:3])[0]
                device_id = struct.unpack('B',self.response_frame[0:1])[0]
                if ( len(self.response_frame) >= dataBytes + 5 ):  # device, function, lenght ... crc,crc
                    # full response found
                    frame = self.response_frame[dataBytes+5:]
                    self.response_frame = self.response_frame[0:dataBytes+5]
                    if self.debug == 1:
                        print("Response", self.frameAsText(self.response_frame))
                    if not self.checkCrc(self.response_frame):
                        date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                        print(date,"Warning Response CRC Fail", self.frameAsText(self.response_frame))

                    if dataBytes != self.request_count_registers*2:
                        print("Warning, not enough bytes returned got "+str(dataBytes)+" expected "+str(self.request_count_registers*2), self.frameAsText(self.response_frame))

                    self.extendRegisters(device_id,self.request_start_register+dataBytes+1)

                    storeStart = self.request_start_register*2
                    storeEnd = storeStart + dataBytes
                    frameDataStart = 3
                    frameDataEnd = 3+dataBytes

                    if ( (storeEnd-storeStart) != (frameDataEnd - frameDataStart) ):
                        print("Length calc mismatch ",storeStart, storeEnd, frameDataStart, frameDataEnd)

                    # store the registers against the device
                    if self.debug == 1:
                        print("Frame Data  ",frameDataStart, frameDataEnd)
                        print("Saving At   ",device_id, storeStart, storeEnd)
                    self.registers[device_id][storeStart:storeEnd] = self.response_frame[frameDataStart:frameDataEnd]
                    if self.debug == 1:
                        print("Saved  Range ",self.frameAsText(self.registers[device_id][storeStart:storeEnd]))
                    self.hasRequestFrame = False
                    return frame

            if ((datetime.now() - self.request_recieved).total_seconds()) > self.request_timeout:
                self.hasRequestFrame = False
            return frame

        f_code = struct.unpack("B", frame[1:2])[0]
        if f_code > 0x80 and len(frame) >= 5:
            print("Exception ",self.frameAsText(frame))
            self.hasRequestFrame = False
            return frame[5:]


        # check for timeout
        if f_code == 4  and (len(frame) >= 8) :
            # request from master to device
            if self.debug == 1:
                print("Request", self.frameAsText(frame))
            if not self.checkCrc(frame[0:8]):
                date = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                print(date, "Warning Request CRC Fail")

            self.request_frame = frame[0:8]
            self.request_device_id = struct.unpack("B", frame[0:1])[0]
            self.request_start_register = struct.unpack('!H',frame[2:4])[0]
            self.request_count_registers = struct.unpack('!H', frame[4:6])[0]
            self.request_recieved = datetime.now()
            self.response_frame = bytearray()
            self.hasRequestFrame = True

            if self.debug == 1:
                print("Request device=",self.request_device_id,"start_register=",self.request_start_register,"count=",self.request_count_registers)
            return frame[8:]
        return EMPTY

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

    def dump(self, device_id):
        print("Device",device_id)
        if device_id in self.registers:
            print(self.frameAsText(self.registers[device_id]))



    def getFloat(self, device_id, reg):
        if device_id in self.registers:
            if len(self.registers[device_id]) > reg+2:
                return struct.unpack("!f", self.registers[device_id][reg*2:reg*2+4])[0]
        return 0

    def getInt16(self, device_id, reg):
        if device_id in self.registers:
            if len(self.registers[device_id]) > reg+2:
                return struct.unpack("<h", self.registers[device_id][reg*2:reg*2+2])[0]
        return 0

    def getUInt16(self, device_id, reg):
        if device_id in self.registers:
            if len(self.registers[device_id]) > reg+2:
                return struct.unpack("<H", self.registers[device_id][reg*2:reg*2+2])[0]
        return 0

    def getInt32(self, device_id, reg):
        if device_id in self.registers:
            if len(self.registers[device_id]) > reg+2:
                return struct.unpack("<i", self.registers[device_id][reg*2:reg*2+2])[0]
        return 0

    def getUInt32(self, device_id, reg):
        if device_id in self.registers:
            if len(self.registers[device_id]) > reg+2:
                return struct.unpack("<I", self.registers[device_id][reg*2:reg*2+2])[0]
        return 0



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


