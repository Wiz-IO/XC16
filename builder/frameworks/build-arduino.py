# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os import listdir
from os.path import join
from shutil import copyfile
from SCons.Script import DefaultEnvironment
from common import dev_init_compiler

env = DefaultEnvironment()
core    = env.BoardConfig().get('build.core')
variant = env.BoardConfig().get('build.variant')

def init_Template(env):
   dir = join( env.subst('$PROJECT_DIR'), 'src' )
   if not listdir( dir ):
        copyfile( join(env.platform_dir, 'arduino', 'variants', variant, 'fuse'), join(dir, 'fuses.c') )
        open( join(dir, 'main.cpp'), 'w').write('''// WizIO 2022 Georgi Angelov
#include <Arduino.h>

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
    

dev_init_compiler(env)
init_Template(env)



env.Append(
    CPPDEFINES = [ 'ARDUINO=200' ],    
    CPPPATH = [
        join(env.framework_dir, 'arduino', 'api'),
        join(env.framework_dir, 'arduino', 'cores', core), 
        join(env.framework_dir, 'arduino', 'variants', variant), 
    ],
    CXXFLAGS = [ '-std=c++0x', ],
    LIBSOURCE_DIRS = [ join(env.framework_dir, 'arduino', "libraries", core) ],
    LIBPATH        = [ join(env.framework_dir, 'arduino', "libraries", core) ],
)

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'api'),
    join(env.framework_dir, 'arduino', 'api'),
)  

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'core'),
    join(env.framework_dir, 'arduino', 'cores', env.BoardConfig().get('build.core')), 
)  

env.BuildSources( 
    join('$BUILD_DIR', 'arduino', 'variant'),
    join(env.framework_dir, 'arduino', 'variants', env.BoardConfig().get('build.variant')), 
) 