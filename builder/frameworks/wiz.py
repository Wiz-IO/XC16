# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

import os, sys, shutil, time, click, inspect
from os.path import exists

PLATFORM_NAME  = 'XC16'
FRAMEWORK_NAME = 'framework-' + PLATFORM_NAME

MODE_INSTALL    = 0
MODE_INTEGRATE  = 1

def LOG(txt = ''):
    #txt = '[] %s() %s' % (inspect.stack()[1][3], txt)
    #open('D:/LOG.txt', 'a+').write(txt + '\n')
    pass

def ERROR(txt = ''):
    txt = '%s() %s' % (inspect.stack()[1][3], txt)
    click.secho( '[ERROR] %s \n' % txt, fg='red') 
    time.sleep(.1)
    sys.exit(-1)

def INFO(txt): 
    click.secho( '   %s' % (txt), fg='blue') # BUG: Windows: 4 same chars

def MKDIR(dir, test=False):    
    if dir and not exists(dir): 
        if test:
            if '.platformio' not in dir or PLATFORM_NAME not in dir: # just in case
                ERROR('Platform name is not in path: %s' % dir) 

        os.makedirs(dir, exist_ok=True)

def RMDIR(dir, test=False):  
    if dir and exists(dir): 
        if test:
            if '.platformio' not in dir or PLATFORM_NAME not in dir: # just in case
                ERROR('Platform name is not in path: %s' % dir)

        shutil.rmtree( dir, ignore_errors=True )

        timeout = 50
        while exists( dir ) and timeout > 0: 
            time.sleep(.1)  
            timeout -= 1  
        if timeout == 0: 
            ERROR('Delete folder: %s' % dir)