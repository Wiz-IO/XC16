# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os import listdir
from os.path import join
from SCons.Script import DefaultEnvironment
from common import dev_init_compiler

env = DefaultEnvironment()

def init_Template(env):
   dir = join( env.subst('$PROJECT_DIR'), 'src' )
   if not listdir( dir ):
      open( join(dir, 'main.c'), 'w').write('''// WizIO 2022 Georgi Angelov
#include <xc.h>
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

dev_init_compiler(env)
init_Template(env)

env.Append(
    CPPPATH = [],
    CXXFLAGS  =  [ '-std=c++0x', ],
)

# TODO