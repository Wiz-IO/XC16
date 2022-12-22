# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )
#   Based of Reverse Engineering of Pickit4 protocol
#   Version: 
#       1.0 ( PlatformIO mod )
#
#   Depend: 
#       intelhex, 
#       pyusb ( libusb-1.0.dll ) 
#           https://github.com/libusb/libusb/releases
#

import sys, json, struct, time, click
from os.path import join, normpath, dirname
from platformio import proc

PYTHON_EXE = proc.get_pythonexe_path()
THIS_DIR = normpath( dirname(__file__) )

try: # install python requirements
    import usb.core  
    import usb.util
    from intelhex import IntelHex
except ImportError:
    print('\nInstalling Python requirements...')
    args = [ PYTHON_EXE, '-m', 'pip', '-q', 'install', '-r', 'requirements.txt' ]
    result = proc.exec_command( args, stdout=sys.stdout, stderr=sys.stderr, stdin=sys.stdin, cwd=THIS_DIR )
    print(result)
    print('Requirements DONE')
    print('Download and Put "libusb-1.0.dll" in PIO Python folder:', dirname(PYTHON_EXE), '\n')      
    print('https://github.com/libusb/libusb/releases') 
    print('and click [ Upload ] again\n') 
    exit(0)

###############################################################################
###############################################################################

RESULT                      = 13
GET_FIRMWARE_INFO           = 0xE1
GET_FW_INFO_TYPE_APP        = 0xAF
SCRIPT_NO_DATA              = 0x0100
SCRIPT_WITH_DOWNLOAD        = 0xC0000101
SCRIPT_WITH_UPLOAD          = 0x80000102
SCRDONE                     = 259
COMMAND_GET_STATUS_FROM_KEY = 261
KEY_COMMANDS_GET_ERROR_STATUS = "ERROR_STATUS_KEY"

PTG_MODE_CONTROL_COMMAND    = 94 # disable ToGO mode

ICSP_WIRE_2 = 0 
ICSP_WIRE_4 = 1
ICSP_SWD    = 2

PULL_NONE   = 0
PULL_UP     = 1
PULL_DOWN   = 2

TIMEOUT_DEFAULT = 1000

PICS = { # local PIC info ... loaded from board.json
    'PIC24FJ256GB206': { 
        'DeviceID'          : 0x4104FFFF,   # family, pic, rev
        'EraseSize'         : 2048,         # in bytes
        'FlashEnd'          : 0x00015800, 
        'ConfigEnd'         : 0x0002AC00,
        'RIPE'              : 'RIPE_01c_000032.hex' # not used
    },
}

###############################################################################

def INFO(txt): 
    click.secho( '   %s' % (txt), fg='blue') # BUG: Windows: 4 same chars

def ERROR(txt):
    click.secho( '[ERROR] %s \n' % txt, fg='red') 
    time.sleep(.1)
    sys.exit(-1)

def PRINT_HEX(TXT, ar, maxSize=0x600):
    return
    if None == ar:
        print('HEX NONE')
        return
    size = len(ar)
    if size > maxSize: 
        size = maxSize
    if ar[0] == GET_FIRMWARE_INFO: 
        size = 48
    ar = ar[0:size]
    txt = ''
    for a in ar:
        txt += '%02X ' % a
    print(TXT, txt)

###############################################################################

def pack_array(arr): # [8] --> [6]
    a = []
    i = 0
    while True:
        b = arr[ i : i + 8 ]
        if len(b) == 0: 
            break
        b[3] = b[6]
        for j in range(6): 
            a.append( b[j] )
        i += 8
    return a

def get_flash(H, pic_end_address, rowSizeInBytes=0x800):
    pic_end_address *= 2 # hex address

    a = [0xFF for i in range(pic_end_address)] # fill mem

    end_address = 0
    for s in H.segments():           
        if s[0] >= pic_end_address: # skip config bits
            break
        end_address = s[1]            
        data = H.tobinarray(start = s[0], end = s[1] - 1)  
        for i in range( s[1] - s[0] ):
            a[ s[0] + i ] = data[ i ] # replace data

    nonAligned = end_address % rowSizeInBytes
    if nonAligned != 0: 
        end_address += rowSizeInBytes - nonAligned
    a = a[ 0 : end_address] # cut end aligned
 
    a = pack_array(a) 
    #print('Application size:', len(a), 'bytes')
    return a
              
def get_config(H):
    rowSizeInBytes = 0x100
    a = [0xFF for i in range(rowSizeInBytes)] # fill mem
    s = None
    for s in H.segments(): pass # get last segment
    data = H.tobinarray(start = s[0], end = s[1] - 1)
    i = rowSizeInBytes - len(data) # set to end
    for d in data:
        if d == 0: d = 0xFF 
        a[i] = d
        i += 1  
    a = pack_array(a)  
    #print('SIZE', len(a))
    #PRINT_HEX('Configuration  :', a, len(a))
    return a

###############################################################################

class PK4_PIC:
    rx = b''
    timeout = TIMEOUT_DEFAULT

    def __init__(self, USB, hex_file, device = 'PIC24FJ256GB206', device_info = None, tool_info = None):
        self.USB = USB   
        self.hex_file = hex_file   

        self.tool_info = {}
        self.tool_info['power'] = True
        self.tool_info['release_power'] = False
        self.tool_info['release_reset'] = True
        self.tool_info['speed'] = 400
        #self.tool_info['pullup'] = TODO, not need by default
        if tool_info: 
            self.tool_info = tool_info
            

        if device_info:
            self.device_info = device_info
        else:
            if device not in PICS: 
                ERROR("Not supported device: " + device)
            self.device_info = PICS[device] 

        self.SCR = {} # load device scripts
        with open( join(THIS_DIR, device + '.json')) as json_file: 
            self.SCR = json.load(json_file)

        # not used
        # HEX = IntelHex()
        # HEX.fromfile( join(THIS_DIR,self.device_info['RIPE']), format='hex' )
        # self.ARR_PE = get array, align, pack
        
        HEX = IntelHex()
        HEX.fromfile(hex_file, format='hex') 
        # HEX.tobinfile('APPLICATION.bin')

        self.BIN_FLASH  = get_flash(HEX, self.device_info['FlashEnd'], self.device_info['EraseSize'])
        self.BIN_CONFIG = get_config(HEX)
        
    def hid_write(self, buffer, ep = 0x02):
        PRINT_HEX('W[%d]:\t' %len(buffer), buffer)
        try:
            self.USB.write(ep, buffer, self.timeout)
        except: 
            ERROR('HID WRITE TIMEOUT')

    def hid_read(self, size = 0x200, ep = 0x81):
        self.rx = b''
        try:
            self.rx = self.USB.read(ep, size + 1, self.timeout)
        except: 
            ERROR('HID READ TIMEOUT')
        if size != len(self.rx): 
            ERROR('HID READ SIZE')       
        if size < 12:
            PRINT_HEX('R<--:\t', self.rx, size)
        else:     
            PRINT_HEX('R<--:\t', self.rx, struct.unpack('<I', self.rx[8:12])[0])    

    def receive(self, size = 0x200, ep = 0x81):
        self.hid_read(size, ep)
        if RESULT != self.rx[0]: 
            ERROR('RECEIVE ANSWER')
        return struct.unpack('<I', self.rx[8:12])[0] # payload size        

    def transmit(self, cmd, transferSize = 0, payload = None, ep = 0x02):
        a = struct.pack('<I', cmd)              # COMMAND
        a += struct.pack('<I', 0)               # SEQUENSE
        size = 16
        if payload: 
            size += len(payload)
        a += struct.pack('<I', size)            # PACKET SIZE
        a += struct.pack('<I', transferSize)    # TRANSFER SIZE
        if payload: 
            a += bytearray(payload)             # PAYLOAD
        self.hid_write(a, ep)

    def write(self, cmd = SCRIPT_NO_DATA, transferSize = 0, prm = None, scr = None):
        payload = b''
        if prm:
            payload += struct.pack('<I', len(prm))
        else: 
            payload += struct.pack('<I', 0)
        if scr:
            payload += struct.pack('<I', len(scr))
        else: 
            payload += struct.pack('<I', 0)   
        if prm:
            payload += bytearray(prm) 
        if scr:
            payload += bytearray(scr)
        self.transmit(cmd, transferSize, payload)
        self.receive()

## CMD PROGRAMER ##############################################################

    def enablePTG(self, enable):
        res = -1
        self.write(
            cmd = SCRIPT_WITH_UPLOAD,
            scr = struct.pack('<BI', 0x5E, int(enable)),  
            transferSize = 4
        )
        self.hid_read(size = 4, ep = 0x83)
        if len(self.rx) == 4:
            res = struct.unpack('<I', self.rx[:4])[0]
        self.sendScriptDone()
        self.getStatusValueFromKey(KEY_COMMANDS_GET_ERROR_STATUS)
        return res

    def sendScriptDone(self):
        self.write(SCRDONE)

    def getStatusValueFromKey(self, key):
        self.transmit(COMMAND_GET_STATUS_FROM_KEY, 0, bytearray(key, 'ascii') + b'\x00')
        size = self.receive()
        s = str( self.rx[ 16 : size ], 'ascii' ).replace('\0','') 
        #print( 'Status:', s) # NONE
        return s # string

    def boot(self):     
        self.hid_write( [ GET_FIRMWARE_INFO ] )
        self.hid_read()
        if 0x200 != len(self.rx): 
            ERROR('BOOT ANSWER SIZE')
        if GET_FIRMWARE_INFO != self.rx[0] or GET_FW_INFO_TYPE_APP != self.rx[1]: 
            ERROR('BOOT APP')
        serial = str( self.rx[32:47], 'utf-8').replace('\0','' )
        #self.enablePTG(0) # disable ToGO
        return serial

    def shutDownPowerSystem(self):
        self.write(scr = [0x44])

    def selectPowerSource(self, fromTool):
        self.write(scr = [0x46, fromTool & 1, 0, 0, 0 ]) 

    def setPowerInfo(self, Vdd, VppOperation, Vpp_op):
        self.write(scr = [ 64, 
                (Vdd & 0xFF), (Vdd >> 8 & 0xFF), 0, 0, 
                (VppOperation & 0xFF), (VppOperation >> 8 & 0xFF), 0, 0, 
                (Vpp_op & 0xFF), (Vpp_op >> 8 & 0xFF), 0, 0, 
                66, 67 ] )

    def getVoltagesInfo(self):
        self.write(scr = [71]) 
        return struct.unpack('<IIIIIIII', self.rx[24:24+32]) 

    def applyLedIntensity(self, level):
        self.write(self.SCRIPT_NO_DATA, scr = [0xCF, level & 0xFF])

    def applySelICSP(self, mode=1): 
        # BootFlash=0, FlashData=1
        self.write(self.SCRIPT_NO_DATA, scr = [39, mode & 1])

    def setSpeed(self, speed): 
        # 100, 400
        self.write(scr = [0xEC, (speed & 0xFF), (speed >> 8 & 0xFF), 0, 0 ]) 

    def getSpeed(self):
        self.write(scr = [0xED]) 
        return struct.unpack('<I', self.rx[24:28])[0] 

    def applySelJTAGSpeed(self, speed_level = 1):
        self.write(scr = [0xD4, (speed_level & 0xFF), (speed_level >> 8 & 0xFF), 0, 0 ]) 

    def releaseFromReset(self):
        self.write(scr = [0x42, 0xB0]) 
        time.sleep(.1)

    def holdInReset(self):
        self.write(scr = [0xB1]) 
        time.sleep(.1)

    def closeRelay(self, closeIt):
        self.write(scr = [0xEF, closeIt & 1])

    def applySelPullUpDown(self, dir, pullChannel, pullState, resistance):
        # pullChannel [0..1]
        # pullDirCmd = 205, 206
        # resistance = 4700 [0..50000]
        # pullState [0..1]
        pullDirCmd = 205 if dir == 0 else 206
        self.write(scr = [ pullDirCmd, pullChannel, (resistance & 0xFF), (resistance >> 8 & 0xFF), 0, 0, pullState ])

## CMD SCRIPT #################################################################

    def runScript(self, name):
        self.write(scr = self.SCR[name])

    def CalcCRC_PE(self):
        # after: SEND FLASH DATA, getStatusValueFromKey('ERROR_STATUS_KEY'), SCRDONE()
        # return U32 len[20:+4] = 2, U16 crc[24:+2]
        pass

    def TestPEConnect(self):
        # after: enterTMOD_PE()
        pass

    def enterTMOD_PE(self):
        self.runScript('enterTMOD_PE')     

    def EnterTMOD_LV(self):
        self.runScript('EnterTMOD_LV')

    def ExitTMOD(self):
        self.runScript('ExitTMOD')

    def GetDeviceID(self):
        self.runScript('GetDeviceID')
        self.id = struct.unpack('<I', self.rx[24:28])[0] 
        return self.id # family, pic, revision

    def EraseTestmemRange(self, address, size):
        # address = 0x80000
        # size    = 0xBEE
        pass

    def EraseChip(self, codeGuardOption = 0):
        params = struct.pack('<I', codeGuardOption)
        self.write(scr = self.SCR['EraseChip'], prm = params)

    def WriteProgmem(self, address, size):
        # min size = 192 bytes
        params  = struct.pack('<I', address)
        params += struct.pack('<I', size)
        self.timeout = 3000 # need ?
        self.write(
            cmd = SCRIPT_WITH_DOWNLOAD,
            scr = self.SCR['WriteProgmem'], 
            prm = params, 
            transferSize = size
        )
        self.timeout = TIMEOUT_DEFAULT

    def WriteProgmemPE(self):
        # as WriteProgmem
        pass

    def ReadProgmem(self, address, size):
        # SCRIPT_WITH_UPLOAD
        pass

    def ReadProgmemWords(self):
        # SCRIPT_WITH_UPLOAD
        pass

## COMMON #####################################################################

    def get_device_id(self, test_start = True, test_end = True):
        if test_start:
            self.EnterTMOD_LV() 
        res = self.GetDeviceID()
        if test_end: 
            self.ExitTMOD()        
        return res

    def erase_chip(self, codeGuardOption = 0, test_start = True, test_end = False):
        if test_start:
            self.EnterTMOD_LV() 
        self.timeout = 3000 # need ?
        self.EraseChip(codeGuardOption) # codeGuardOption: no info
        self.timeout = TIMEOUT_DEFAULT
        if test_end: 
            self.ExitTMOD()  

    def program(self, buffer, address, test_start = False, test_end = False):
        if test_start:
            self.EnterTMOD_LV()   

        EP_SIZE = 4096
        size = len(buffer)
        self.WriteProgmem(address, size)
        i = 0
        while True:
            if i >= size: break
            self.hid_write(buffer[ i : i + EP_SIZE ], ep = 0x04)
            i += EP_SIZE
        self.getStatusValueFromKey(KEY_COMMANDS_GET_ERROR_STATUS)

        if test_end: 
            self.ExitTMOD()  

###############################################################################
# PlatformIO Uploader
###############################################################################

def dev_uploader(target, source, env):
    hex_file = join(env.get("BUILD_DIR"), env.get("PROGNAME"))+'.hex'
    device = env.BoardConfig().get('upload.device', None)
    INFO('Device : %s' % device)
    info = env.BoardConfig().get('upload.info', None)
    prog = env.BoardConfig().get('upload.programer', None)

    try:
        USB = usb.core.find(idVendor=0x04D8, idProduct=0x9012) # PicKit4 ( power 50mA )
    except:
        print('\n[ERROR] "libusb-1.0.dll" not found')
        print('Please, Download and Put "libusb-1.0.dll" in PIO Python folder:', dirname(PYTHON_EXE), '\n')        
        print('https://github.com/libusb/libusb/releases')        
        exit(0)
    if None == USB:
        USB = usb.core.find(idVendor=0x04D8, idProduct=0x9018) # SNAP ( not support power )
        if USB: 
            INFO('Programer : SNAP')
    else:
        INFO('Programer : PICKIT4')
    if None == USB: 
        ERROR("USB Programer not found")  
    #print(USB)  

    INFO('Driver : %s' % usb.util.get_string(USB, USB.iSerialNumber) )
    USB.set_configuration()
    USB.reset() 

    d = PK4_PIC(USB, hex_file, device, info, prog)
    INFO('Serial Number : %s' %  d.boot())

    d.selectPowerSource( d.tool_info['power'] )
    d.shutDownPowerSystem()
    d.setPowerInfo(3250, 3250, 3250)
    INFO('Voltages : %s' % str(d.getVoltagesInfo()))

    d.setSpeed(d.tool_info['speed']) 
    INFO('ICSP Speed : %s' % d.getSpeed())

    d.applySelJTAGSpeed(1) # speed level ... no info ... lo/hi ?
    # set PullUp, PullDown, 4.7k ... TODO

    INFO('Device ID : 0x%04X' % d.get_device_id())

    print('Erasing Chip...')
    d.erase_chip()

    print('Program Application...')
    d.program(d.BIN_FLASH, 0)

    if len(d.BIN_CONFIG) > 0:
        print('Program Configiguration bits...')    
        d.program(d.BIN_CONFIG, d.device_info['ConfigEnd'] - ((len(d.BIN_CONFIG) // 3) * 2) )

    d.holdInReset()
    if d.tool_info['release_reset']:
        d.releaseFromReset()

    if d.tool_info['release_power']:
        d.shutDownPowerSystem() # Power OFF    

    INFO('DONE')
 
