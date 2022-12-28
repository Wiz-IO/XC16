# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os import listdir
from os.path import join
from shutil import copyfile
from SCons.Script import DefaultEnvironment
from common import dev_init_compiler, dev_ini_add, dev_patch_linker

def init_Template(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    if not listdir( dir ):
        dev_patch_linker(env)
        copyfile( join(env.framework_dir, 'arduino', 'variants', variant, 'fuses'), join(dir, 'fuses.c') )
        open( join(dir, 'main.cpp'), 'w').write('''#include <Arduino.h>

void setup()
{
    pinMode(LED, OUTPUT);
}

void loop()
{
    digitalWrite(LED, HIGH);
    delay(100);
    digitalWrite(LED, LOW);
    delay(100);
} 
''')   
        dev_ini_add(env, '''
;custom_xc16 = C:/Program Files/Microchip/xc16/vX.XX
;custom_heap = 16384     
;monitor_port = COM26
;monitor_speed = 115200
''' )

env = DefaultEnvironment()
core = env.BoardConfig().get('build.core')
variant = env.BoardConfig().get('build.variant')
dev_init_compiler(env)
init_Template(env)

env.Append(
    CPPDEFINES = [ 'ARDUINO=200' ],    
    CPPPATH = [
        join(env.framework_dir, 'arduino', 'api'),
        join(env.framework_dir, 'arduino', 'cores', core), 
        join(env.framework_dir, 'arduino', 'variants', variant), 
    ],
    LIBSOURCE_DIRS = [ join(env.framework_dir, 'arduino', "libraries", core) ],
    LIBPATH        = [ join(env.framework_dir, 'arduino', "libraries", core) ],
)

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'api'),
    join(env.framework_dir, 'arduino', 'api'),
)  

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'core'),
    join(env.framework_dir, 'arduino', 'cores', core), 
)  

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'variant'),
    join(env.framework_dir, 'arduino', 'variants', variant), 
) 