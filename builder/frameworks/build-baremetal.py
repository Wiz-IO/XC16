# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os import listdir
from os.path import join
from SCons.Script import DefaultEnvironment
from common import dev_init_compiler, dev_ini_add, dev_patch_linker

def init_Template(env):
   dir = join( env.subst('$PROJECT_DIR'), 'src' )
   if not listdir( dir ):
        dev_patch_linker(env)
        open( join(dir, 'main.c'), 'w').write('''#include <xc.h>
#include <libpic30.h>      

int main(void)
{
    _TRISE3 = 0;
    while(1) {
        _LATE3 = 0;
        __delay_ms(100);
        _LATE3 = 1;
        __delay_ms(100);
    }
}
''')
        dev_ini_add(env, '''
;custom_xc16 = C:/Program Files/Microchip/xc16/vX.XX
;custom_heap = 16384        
;monitor_port = COM33
;monitor_speed = 115200
''' )

env = DefaultEnvironment()
dev_init_compiler(env)
init_Template(env)

#env.Append()
