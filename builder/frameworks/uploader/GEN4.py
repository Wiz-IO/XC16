# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )
#   Based of Reverse Engineering of Pickit4 protocol ( GEN4 )
#   Version: 
#       1.0.0 ( PlatformIO mod )
#   Python depend: 
#       intelhex, 
#       pyusb ( libusb-1.0.dll ) https://github.com/libusb/libusb/releases
#
#   NOTES: 
#       Tool must be in PIC mode
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
    print('Download and Put libusb-1.0.dll in PIO Python folder:', dirname(PYTHON_EXE), '\n') # TODO add libs      
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
KEY_COMMANDS_GET_ERROR_STATUS = 'ERROR_STATUS_KEY'

PTG_MODE_CONTROL_COMMAND    = 94 # disable ToGO mode

# ICSPSel
ICSP_WIRE_2 = 0 
ICSP_WIRE_4 = 1
ICSP_SWD    = 2

# PGCPGDConfig 
PULL_NONE   = 0
PULL_UP     = 1
PULL_DOWN   = 2

TIMEOUT_DEFAULT = 3000

PICS = { # local PIC info ... loaded from board.json
    'PIC24FJ256GB206': {
        'DeviceID'          : 0x4104FFFF,       
        'FlashEnd'          : 0x00015800, 
        'FlashConfigEnd'    : 0x0002AC00
    },
    'PIC24F16KA301': {
        'DeviceID'          : 0x4508FFFF,
        'FlashEnd'          : 0x00002C00, 
        'Eeprom'            : 0x007FFE00,
        'EepromSize'        : 256,        
        'Config'            : 0x00F80000,
        'ConfigSize'        : 18          
    },    
}

###############################################################################

def INFO(txt): 
    click.secho( '   %s' % (txt), fg='blue') # BUG: Windows: 4 same chars

def ERROR(txt):
    print()
    click.secho( '[ERROR] %s' % txt, fg='red') 
    print()
    time.sleep(.1)
    sys.exit(-1)

def PRINT_HEX(TXT, ar, maxSize=0x200):
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

def get_data_24(H, address_start, address_end, rowSizeInBytes, cutEnd = False):
    address_start *= 2
    address_end   *= 2
    end = 0
    if cutEnd:
        for s in H.segments():
            if s[1] > address_end: 
                continue
            end = s[1]
    if end > 0:
        address_end = end
        nonAligned = address_end % rowSizeInBytes   
        if nonAligned != 0: 
            address_end += rowSizeInBytes - nonAligned    
    d = H.tobinarray(start = address_start, end = address_end - 1) 
    return pack_array(d)

def get_data_16(H, address, size): 
    a = []    
    if address < 0 or size == 0:
        return [] 
    data = H.tobinarray(start = (address * 2), end = (address * 2) + (size * 2) - 1)
    i = 0
    for d in data: 
        if i > 1: # remove zeroes
            if i > 2: 
                i = -1
        else:
            a.append(d)
        i += 1
    for b in a: # skip if blank
        if b != 0xFF: 
            return a
    return []

###############################################################################

class GEN4:
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
        if tool_info: 
            self.tool_info = tool_info
            
        if device_info:
            self.device_info = device_info
        else:
            if device not in PICS: 
                ERROR('Not supported device: ' + device)
            self.device_info = PICS[device] 

        self.SCR = {} # load device scripts
        with open( join(THIS_DIR, device + '.json')) as json_file: 
            self.SCR = json.load(json_file)
        
        self.BIN_FLASH          = []
        self.BIN_FLASH_CONFIG   = []        
        self.BIN_EEPROM         = []
        self.BIN_CONFIG         = []

        HEX = IntelHex()
        HEX.fromfile(hex_file, format='hex') 
        # HEX.tobinfile('APPLICATION.bin')        

        self.BIN_FLASH = get_data_24(HEX, 0, self.device_info['FlashEnd'], 0x800, True)

        if 'WriteDataEEmem' in self.SCR:        
            self.BIN_EEPROM = get_data_16(HEX, device_info['Eeprom'], device_info['EepromSize'])
        else:
            pass # TODO

        if 'WriteConfigmem' in self.SCR:
            self.BIN_CONFIG = get_data_16(HEX, device_info['Config'], device_info['ConfigSize'])    
        else:
            self.BIN_FLASH_CONFIG = get_data_24(HEX, self.device_info['FlashConfigEnd'] - 128, self.device_info['FlashConfigEnd'], 256)

        #exit(0)
        
        
    def hid_write(self, buffer, ep = 0x02):
        PRINT_HEX('W[%d](%d) ' % (len(buffer),ep), buffer)         
        try:
            self.USB.write(ep, buffer, self.timeout)
        except: 
            ERROR('HID WRITE TIMEOUT')  

        if ep == 4 and len(buffer) == 0x1000:
            try: self.USB.clear_halt(4) # ???
            except: 
                pass               

    def hid_read(self, size = 0x200, ep = 0x81):
        self.rx = b''
        try:
            self.rx = self.USB.read(ep, size + 1, self.timeout)
        except: 
            ERROR('HID READ TIMEOUT')
        if size != len(self.rx): 
            ERROR('HID READ SIZE')       
        if size < 12:
            PRINT_HEX('R[%d]\t'%size, self.rx, size)
        else:     
            PRINT_HEX('R[]\t', self.rx, struct.unpack('<I', self.rx[8:12])[0]) 

    def receive(self, size = 0x200, ep = 0x81):
        self.hid_read(size, ep)
        if RESULT != self.rx[0]: 
            ERROR('RECEIVE ANSWER 13')
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
        return res # 0

    def sendScriptDone(self):
        self.write(SCRDONE)

    def getStatusValueFromKey(self, key):
        self.transmit(COMMAND_GET_STATUS_FROM_KEY, 0, bytearray(key, 'ascii') + b'\x00')
        size = self.receive()
        s = str( self.rx[ 16 : size ], 'ascii' ).replace('\0','') 
        #print( 'Status:', s) # NONE
        return s

    def boot(self):     
        self.hid_write( [ GET_FIRMWARE_INFO ] )
        self.hid_read()
        if 0x200 != len(self.rx): 
            ERROR('BOOT ANSWER SIZE')
        if GET_FIRMWARE_INFO != self.rx[0] or GET_FW_INFO_TYPE_APP != self.rx[1]: 
            ERROR('BOOT APP')
        serial = str( self.rx[32:47], 'utf-8').replace('\0','' )
        # self.enablePTG(0) # disable ProgramerToGO
        return serial # BURxxx

    def shutDownPowerSystem(self):
        self.write(scr = [0x44])
        time.sleep(.1)

    def selectPowerSource(self, fromTool):
        self.write(scr = [0x46, fromTool & 1, 0, 0, 0 ]) 
        time.sleep(.1)

    def setPowerInfo(self, Vdd, VppOperation, Vpp_op):
        self.write(scr = [ 64, 
                (Vdd & 0xFF), (Vdd >> 8 & 0xFF), 0, 0, 
                (VppOperation & 0xFF), (VppOperation >> 8 & 0xFF), 0, 0, 
                (Vpp_op & 0xFF), (Vpp_op >> 8 & 0xFF), 0, 0, 
                66, 67 ] )
        time.sleep(.1)

    def getVoltagesInfo(self):
        self.write(scr = [71]) 
        return struct.unpack('<IIIIIIII', self.rx[24:24+32]) 

    def applyLedIntensity(self, level):
        self.write(self.SCRIPT_NO_DATA, scr = [0xCF, level & 0xFF])

    def applySelICSP(self, mode = 1): 
        # BootFlash = 0, FlashData = 1
        self.write(self.SCRIPT_NO_DATA, scr = [39, mode & 1])

    # Sets the ICSP clock period to nanoseconds
    def setSpeed(self, speed): 
        # 100, 400, 2400
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

    def applySelPullUpDown(self, dir, pullChannel, pullState, resistance=4700):
        # dir == 0:PullUp,      cmd=205
        # dir == 1:PullDown,    cmd=206
        # pullDirCmd = 205, 206        
        # pullChannel [0..1]
        # resistance = 4700 [0..50000]
        # pullState [0..1]
        pullDirCmd = 205 + ( dir & 1 )
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

    # Puts the PIC device into its 'Programming mode' using the devices Programming Executive. 
    def enterTMOD_PE(self):
        self.runScript('EnterTMOD_PE')     

    # Puts the PIC device into its 'Programming mode' (Low Voltage)
    def EnterTMOD_LV(self):
        self.runScript('EnterTMOD_LV')

    # Exit programming mode
    def ExitTMOD(self):
        self.runScript('ExitTMOD')

    # Read the device ID from the PIC
    def GetDeviceID(self):
        self.runScript('GetDeviceID')
        self.id = struct.unpack('<I', self.rx[24:28])[0] 
        return self.id # family, pic, revision

    # Erase Executive Code Memory 
    def EraseTestmemRange(self, address, size): # size ?
        params  = struct.pack('<I', address)
        params += struct.pack('<I', size)
        self.write(scr = self.SCR['EraseTestmemRange'], prm = params)

    def EraseChip(self, codeGuardOption = 0):
        params = struct.pack('<I', codeGuardOption)
        self.write(scr = self.SCR['EraseChip'], prm = params)

    # Write to flash ( ICSP )
    def WriteProgmem(self, address, size):
        # min size = 192 bytes
        params  = struct.pack('<I', address)
        params += struct.pack('<I', size)
        self.write(
            cmd = SCRIPT_WITH_DOWNLOAD,
            scr = self.SCR['WriteProgmem'], 
            prm = params, 
            transferSize = size
        )

    def WriteDataEEmem(self, address, size):
        params  = struct.pack('<I', address)
        params += struct.pack('<I', size)
        self.write(
            cmd = SCRIPT_WITH_DOWNLOAD,
            scr = self.SCR['WriteDataEEmem'], 
            prm = params, 
            transferSize = size
        )

    def WriteConfigmem(self, address, size):
        params  = struct.pack('<I', address)
        params += struct.pack('<I', size)
        self.write(
            cmd = SCRIPT_WITH_DOWNLOAD,
            scr = self.SCR['WriteConfigmem'], 
            prm = params, 
            transferSize = size
        )

    # Write to Executive Code Memory ( PE_ADDRESS ) not used
    def WriteProgmemPE(self):
        # as WriteProgmem
        pass

    def ReadProgmem(self, address, size):
        # SCRIPT_WITH_UPLOAD
        pass

## COMMON #####################################################################

    def setResistors(self):
        # for PIC24
        # CD 00 5C 12 00 00 00 ... dir=0, pullChannel=0, resistance=4700, pullState=0
        # CE 00 5C 12 00 00 01 ... dir=1, pullChannel=0, resistance=4700, pullState=1 
        # CD 01 5C 12 00 00 00 ... dir=0, pullChannel=1, resistance=4700, pullState=0
        # CE 01 5C 12 00 00 01 ... dir=1, pullChannel=1, resistance=4700, pullState=1       
        self.applySelPullUpDown(0, 0, 0, 4700)
        self.applySelPullUpDown(1, 0, 1, 4700)
        self.applySelPullUpDown(0, 1, 0, 4700)
        self.applySelPullUpDown(1, 1, 1, 4700)

    def get_device_id(self, test_start = True, test_end = True):
        if test_start:
            self.EnterTMOD_LV() 
        res = self.GetDeviceID()
        if test_end: 
            self.ExitTMOD()        
        return res

    def erase_pe(self, test_start = True, test_end = True):
        if test_start:
            self.EnterTMOD_LV() 
        # self.EraseTestmemRange( PE_ADDRESS, PE_SIZE ) 
        if test_end: 
            self.ExitTMOD()          

    def erase_chip(self, codeGuardOption = 0, test_start = True, test_end = True):
        print('Erasing Chip')
        if test_start:
            self.EnterTMOD_LV() 
        self.EraseChip( codeGuardOption ) # codeGuardOption - no info
        if test_end: 
            self.ExitTMOD()  

    def program(self, buffer, address):
        size = len(buffer)
        EP_SIZE = 0x1000
        i = 0        
        self.WriteProgmem(address, size)
        while True:
            if i >= size: 
                break
            self.hid_write(buffer[ i : i + EP_SIZE ], ep = 0x04)
            i += EP_SIZE
        time.sleep( len(buffer) * 0.00001 )
        self.getStatusValueFromKey( KEY_COMMANDS_GET_ERROR_STATUS )

    def program_flash(self, test_start = True, test_end = True):
        size = len(self.BIN_FLASH)
        if size == 0:
            return # no flash   
        print('Programing Flash \t[ %d ]' % len(self.BIN_FLASH))     
        if test_start:
            self.EnterTMOD_LV()   
        self.program(self.BIN_FLASH, 0)  
        if test_end: 
            self.ExitTMOD()  

    def program_eeprom(self, test_start = True, test_end = True):
        size = len(self.BIN_EEPROM)
        if size == 0 or self.device_info['Eeprom'] < 0: 
            return # no epprom
        print('Programing Eeprom \t[ %d ]' % size)
        if test_start:
            self.EnterTMOD_LV() 
        if 'WriteDataEEmem' in self.SCR:
            self.WriteDataEEmem(self.device_info['Eeprom'], size)      
            self.hid_write(self.BIN_EEPROM, ep = 0x04) 
        else:
            print('[WARNING] Program Eeprom - not supported yet')  # TODO        
        if test_end: 
            self.ExitTMOD() 

    def program_config(self, test_start = True, test_end = True):
        if 'WriteConfigmem' in self.SCR:
            size = len(self.BIN_CONFIG)
        else: 
            size = len(self.BIN_FLASH_CONFIG)
        if size == 0: 
            print('[WARNING] NO Configiguration bits')
            return
        print('Programing Config \t[ %d ]' % size) 
        if test_start:
            self.EnterTMOD_LV() 
        if 'WriteConfigmem' in self.SCR:
            self.WriteConfigmem(self.device_info['Config'], size)   
            buffer = self.BIN_CONFIG
        else:
            self.program(self.BIN_FLASH_CONFIG, self.device_info['FlashConfigEnd'] - ((len(self.BIN_FLASH_CONFIG) // 3) * 2)) 
            buffer = self.BIN_FLASH_CONFIG
        self.hid_write(buffer, ep = 0x04)   
        if test_end: 
            self.ExitTMOD() 

###############################################################################
# PlatformIO Uploader
###############################################################################

def dev_uploader(target, source, env):
    hex_file = join(env.get('BUILD_DIR'), env.get('PROGNAME'))+'.hex'

    device = env.BoardConfig().get('upload.device', None)
    info = env.BoardConfig().get('upload.info', None)
    tool = env.BoardConfig().get('upload.tool', None)
    if None == tool: 
        ERROR('Upload tool settings')
    tool_power = env.GetProjectOption('custom_tool_power', None) # INIDOC
    if tool_power: 
        tool['power'] = tool_power
    tool_speed = env.GetProjectOption('custom_tool_speed', None) # INIDOC
    if tool_speed: 
        tool['speed'] = tool_speed

    try:
        USB = usb.core.find(idVendor=0x04D8, idProduct=0x9012) # PicKit4 ( power 50mA )
    except:
        print('\n[ERROR] libusb-1.0.dll not found')
        print('Please, Download and Put libusb-1.0.dll in PIO Python folder:', dirname(PYTHON_EXE), '\n')        
        print('https://github.com/libusb/libusb/releases')        
        exit(0)
    if None == USB:
        USB = usb.core.find(idVendor=0x04D8, idProduct=0x9018) # SNAP ( not power support )
        if USB: 
            INFO('Programmer  SNAP')
    else:
        INFO('Programmer  PICKIT4')
    if None == USB: 
        ERROR('USB Programmer not found')  
    #print(USB)  

    #INFO('Driver    : %s' % usb.util.get_string(USB, USB.iSerialNumber) )
    try: 
        USB.detach_kernel_driver(0)    
    except: 
        pass
    try: 
        USB.attach_kernel_driver(0)
    except: 
        pass
    USB.set_configuration()
    USB.reset() 

    d = GEN4(USB, hex_file, device, info, tool)
    INFO('Serial    : %s' % d.boot())
    INFO('Device    : %s' % device)    

    d.selectPowerSource( d.tool_info['power'] )
    d.shutDownPowerSystem()
    d.setPowerInfo(3250, 3250, 3250)
    # INFO('Voltages  : %s' % str(d.getVoltagesInfo()))

    d.setSpeed(d.tool_info['speed']) 
    # INFO('Speed     : %s' % d.getSpeed())

    d.applySelJTAGSpeed(1) # speed level - no info ... lo/hi ?
    #d.setResistors() # by defaut is ok

    res = d.get_device_id()
    INFO('Device ID : %04X rev %d' % ( res >> 16, res & 0xFFFF ) )

    d.erase_chip()

    d.program_flash()  
    d.program_eeprom() 
    d.program_config()

    d.holdInReset()
    if d.tool_info['release_reset']:
        d.releaseFromReset()

    if d.tool_info['release_power']:
        d.shutDownPowerSystem() # Power OFF    

    INFO('DONE')

    try: 
        USB.detach_kernel_driver(0)
    except: 
        pass
