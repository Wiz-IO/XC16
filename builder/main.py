# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os.path import join, dirname
from SCons.Script import AlwaysBuild, DefaultEnvironment, Default
from frameworks.wiz import ERROR

from platformio import proc
PYTHON_PATH = dirname(proc.get_pythonexe_path())

env = DefaultEnvironment()

# Workaround, must be here !!!
env.GetCompilerType() 
env.Prepend(_LIBFLAGS='--start-group ')
env.Append(_LIBFLAGS=' --end-group')

env.xc16_dir = env.GetProjectOption('custom_xc16', 'C:\\Program Files\\Microchip\\xc16\\v1.50')
env['ENV']['PATH'] = '' + join(env.xc16_dir, 'bin' + ';' + PYTHON_PATH)

env.xc16_ver = 1.50
x = env.xc16_dir.replace('/','').replace('\\','').split('xc16')
env.xc16_ver = float(x[1].replace('v',''))

env.Replace( 
    BUILD_DIR = env.subst('$BUILD_DIR'),
    ARFLAGS = ['rc'],        
    AR      = 'xc16-ar',
    AS      = 'xc16-as',
    CC      = 'xc16-gcc',
    CXX     = 'xc16-g++',
    LINK    = 'xc16-ld',   
    RANLIB  = 'xc16-ranlib',
    OBJCOPY = 'xc16-objdump', 
    ELFHEX  = 'xc16-bin2hex',
    PROGSUFFIX='.elf',   
)

prg = None

###############################################################################
if 'Baremetal' in env['PIOFRAMEWORK'] or 'Arduino' in env['PIOFRAMEWORK']: 
    elf = env.BuildProgram()
    hex = env.ELF2HEX( join('$BUILD_DIR', '${PROGNAME}'), elf )
    prg = env.Alias( 'buildprog', hex)

else: ERROR('[MAIN] Wrong platform: %s' % env['PIOFRAMEWORK'][0])

AlwaysBuild( prg )

# DEBUG ####################################################################### TODO
debug_tool = env.GetProjectOption('debug_tool')
if None == debug_tool:
    Default( prg )
else:   
    Default( prg )

# UPLOAD ######################################################################
upload = env.Alias('upload', prg, env.VerboseAction('$UPLOADCMD', 'Uploading...'), ) 
AlwaysBuild( upload )

#print(env.Dump())