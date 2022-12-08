# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os.path import join, dirname
from shutil import copyfile
from SCons.Script import Builder
from wiz import INFO, FRAMEWORK_NAME

def dev_patch_linker(env):
    dir = join( env.subst('$PROJECT_DIR'), 'src' )
    copyfile(
        join(env.xc16_dir, 'support', env.core, 'gld', 'p' + env.chip + '.gld'),
        join(dir, 'p' + env.chip + '.gld')
    )
    f = open(join(dir, 'p' + env.chip + '.gld'), 'r')
    txt = f.read()
    f.close()
    txt = txt.replace('*(.user_init);', 'KEEP( *(.user_init) ); /* WIzIO: --gc-sections workaround */')
    open(join(dir, 'p' + env.chip + '.gld'), 'w').write(txt)

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

    INFO('XC16      : %s' % env.xc16_ver)
    env.core = dev_get_value(env, 'core', 'PIC24F') # INIDOC
    INFO('CORE      : %s' % env.core )
    env.chip = dev_get_value(env, 'mcu', '24FJ256GB206') # INIDOC
    INFO('CHIP      : %s' % env.chip )

    env.Append(
        #ASFLAGS=[],
        CPPDEFINES = [
           '__bool_true_and_false_are_defined', 
           '__PIC' + env.chip + '__',
           'FCY=' + dev_get_value(env, 'f_cpu', '16000000L'), # INIDOC, FCY = FOSC / 2
        ],
        CPPPATH = [
            join('$PROJECT_DIR', 'src'),
            join('$PROJECT_DIR', 'lib'),
            join('$PROJECT_DIR', 'include'),
            join(env.xc16_dir, 'include'),
            join(env.xc16_dir, 'support', 'generic', 'h'),
            join(env.xc16_dir, 'support', env.core, 'h'),
        ],
        CFLAGS = [],
        CCFLAGS = [
            #'-O0', # !!! LICENSED COMPILER
            '-mcpu=' + env.chip,
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
            join(env.xc16_dir, 'lib', env.core),
            join('$PROJECT_DIR', 'lib'), 
        ],
        LIBS = [ 'm', 'c', 'pic30' ], 
        LINKFLAGS = [ 
            '--heap='+env.GetProjectOption('custom_heap', '8129'), # INIDOC    
            '--local-stack', 
            '--gc-sections',            
            '-p' + env.chip, 
            '--script', join('src', 'p' + env.chip + '.gld'),            
            '-Map=%s.map' % env.subst(join('$BUILD_DIR','$PROGNAME')) if env.GetProjectOption('custom_map', None) else '', # INIDOC enable
        ],

        BUILDERS = dict(
            ELF2HEX = Builder(
                action = env.VerboseAction(' '.join([ '$ELFHEX', '$SOURCES', '-a']), 'Creating HEX $TARGET'),
                suffix = '.hex'
            )           
        ),        
    )

    if env.GetProjectOption('custom_asm', None): # INIDOC enable
        env.AddPostAction(
            '$BUILD_DIR/${PROGNAME}.elf',
            env.VerboseAction(' '.join([ '$OBJCOPY', '-omf=elf', '-S', '$BUILD_DIR/${PROGNAME}.elf', '> $BUILD_DIR/${PROGNAME}.lst']), 'Creating List ${PROGNAME}.lst'),
        )