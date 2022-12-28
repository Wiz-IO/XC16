# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os.path import join, dirname
from shutil import copyfile
from SCons.Script import Builder
from wiz import INFO, FRAMEWORK_NAME
from uploader.GEN4 import dev_uploader

def dev_patch_linker(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    copyfile(
        join(env.xc16_dir, 'support', env.category, 'gld', 'p' + env.mcu + '.gld'),
        join(dir, 'p' + env.mcu + '.gld')
    )
    f = open(join(dir, 'p' + env.mcu + '.gld'), 'r')
    txt = f.read()
    f.close()
    txt = txt.replace('*(.user_init);', 'KEEP( *(.user_init) ); /* WIzIO: --gc-sections workaround */')
    open(join(dir, 'p' + env.mcu + '.gld'), 'w').write(txt)

def dev_ini_add(env, txt):
    f = open( join( env.subst('$PROJECT_DIR'), 'platformio.ini' ), 'a+' )
    f.write(txt) 
    f.close()

def dev_get_value(env, name, default):
    return env.GetProjectOption('custom_%s' % name, # ini user config  
           env.BoardConfig().get('build.%s' % name, default) ) # default from board

def dev_init_compiler(env):
    env['PLATFORM_DIR' ] = env.platform_dir  = dirname( env['PLATFORM_MANIFEST'] )
    env['FRAMEWORK_DIR'] = env.framework_dir = env.PioPlatform().get_package_dir( FRAMEWORK_NAME )    
    env.Replace( 
        PROGNAME = env.GetProjectOption('custom_name', 'APPLICATION') # INIDOC 
    )

    INFO('XC16 : %s' % env.xc16_ver)
    if 'Arduino' in env['PIOFRAMEWORK']:
        INFO('CORE : %s' % env.BoardConfig().get('build.core') )
    env.category = env.BoardConfig().get('build.category')      
    env.mcu     = env.BoardConfig().get('build.mcu')           
    INFO('CHIP : %s' % env.mcu )
    heap = dev_get_value(env, 'heap', '0') # INIDOC 
    INFO('HEAP : %s' % heap ) 

    env.Append(
        #ASFLAGS=[],
        CPPDEFINES = [
           '__PIC' + env.mcu + '__',
           'FCY=' + dev_get_value(env, 'f_cpu', '16000000L'), # INIDOC, FCY = FOSC / 2
        ],
        CPPPATH = [
            join('$PROJECT_DIR', 'src'),
            join('$PROJECT_DIR', 'lib'),
            join('$PROJECT_DIR', 'include'),
            join(env.xc16_dir, 'include'),
            join(env.xc16_dir, 'support', 'generic', 'h'),
            join(env.xc16_dir, 'support', env.category, 'h'),
        ],
        CFLAGS = [
            '-std=gnu99',
        ],
        CCFLAGS = [
            #'-O0', # LICENSED COMPILER
            '-mcpu=' + env.mcu,
            '-mno-eds-warn',
            '-mlarge-code', 
            '-mlarge-data', 
            '-mlarge-scalar',            
            '-fdata-sections',
            '-ffunction-sections',            
            '-Wall',
            '-Wextra',
            '-Wfatal-errors',
            '-Wno-unused-parameter',
            '-Wno-unused-function',
            '-Wno-unused-variable',
            '-Wno-unused-value',
            '-no-legacy-libc' if env.xc16_ver > 1.25 else '', 
        ],
        CXXFLAGS = [
            '-D__bool_true_and_false_are_defined',
            '-std=c++0x',
            '-fno-rtti',
            '-fno-exceptions',
            '-fno-use-cxa-atexit',      # __cxa_atexit, __dso_handle
            "-fno-threadsafe-statics",  # __cxa_guard_acquire, __cxa_guard_release            
            '-fno-non-call-exceptions',
        ],
        LIBSOURCE_DIRS = [ 
            join('$PROJECT_DIR', 'lib'), 
        ],        
        LIBPATH = [ 
            join(env.xc16_dir, 'lib'),
            join(env.xc16_dir, 'lib', env.category),
            join('$PROJECT_DIR', 'lib'), 
        ],
        LIBS = [ 'm', 'c', 'pic30' ], 
        LINKFLAGS = [ 
            '--heap=' + heap,  
            '--local-stack', 
            '--gc-sections',            
            '-p' + env.mcu, 
            '--script', join('src', 'p' + env.mcu + '.gld'),            
            '-Map=%s.map' % env.subst(join('$BUILD_DIR','$PROGNAME')) if env.GetProjectOption('custom_map', None) else '', # INIDOC enable
        ],
        BUILDERS = dict(
            ELF2HEX = Builder(
                action = env.VerboseAction(' '.join([ '$ELFHEX', '$SOURCES', '-a']), 'Creating HEX $TARGET'),
                suffix = '.hex'
            )           
        ), 
        UPLOADCMD = dev_uploader,       
    )

    if env.GetProjectOption('custom_asm', None): # INIDOC enable
        env.AddPostAction(
            '$BUILD_DIR/${PROGNAME}.elf',
            env.VerboseAction(' '.join([ '$OBJCOPY', '-omf=elf', '-S', '$BUILD_DIR/${PROGNAME}.elf', '> $BUILD_DIR/${PROGNAME}.lst']), 'Creating List ${PROGNAME}.lst'),
        )
    
###############################################################################
