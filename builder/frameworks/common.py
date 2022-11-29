# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

from os.path import join, dirname, exists
from SCons.Script import Builder, COMMAND_LINE_TARGETS
from wiz import INFO,LOG,ERROR,FRAMEWORK_NAME

def dev_get_value(env, name, default):
    return env.GetProjectOption('custom_%s' % name, # ini user config  
           env.BoardConfig().get('build.%s' % name, default) ) # default from board

def dev_init_compiler(env, application_name = 'APPLICATION'):
    env['PLATFORM_DIR' ] = env.platform_dir  = dirname( env['PLATFORM_MANIFEST'] )
    env['FRAMEWORK_DIR'] = env.framework_dir = env.PioPlatform().get_package_dir( FRAMEWORK_NAME )    
    env.Replace( 
        PROGNAME = env.GetProjectOption('custom_name', application_name) # INIDOC 
    )

    env.core = dev_get_value(env, 'core', 'PIC24F') 
    INFO('CORE      : %s' % env.core )
    env.chip = dev_get_value(env, 'mcu', '24FJ256GB206') 
    INFO('CHIP      : %s' % env.chip )

    env.Append(
        #ASFLAGS=[],
        CPPDEFINES = [
           '__bool_true_and_false_are_defined', 
           '__PIC' + env.chip + '__',
           'FCY=' + dev_get_value(env, 'f_cpu', '16000000L'), # FCY = FOSC / 2
        ],
        CPPPATH = [
            join('$PROJECT_DIR', 'src'),
            join('$PROJECT_DIR', 'lib'),
            join('$PROJECT_DIR', 'include'),
            join(env.xc16_dir, 'include'),
            join(env.xc16_dir, 'support', 'generic', 'h'),
            join(env.xc16_dir, 'support', env.core, 'h'),
            join(env.xc16_dir, 'support', 'peripheral_24F' if '24F' in env.core else 'peripheral_30F_24H_33F'),
        ],
        CFLAGS = [],
        CCFLAGS = [
            '-O0', # !!!
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
            '-fno-rtti',
            '-fno-exceptions',
            '-fno-use-cxa-atexit',          # __cxa_atexit, __dso_handle
            "-fno-threadsafe-statics",      # __cxa_guard_acquire, __cxa_guard_release            
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
            #'--handles',
            #'--data-init',
            '--heap='+env.GetProjectOption('custom_heap', '8129'),
            #'--stack=16',             
            '--local-stack', 
            '-p' + env.chip, 
            '--script', 
            join(env.xc16_dir, 'support', env.core, 'gld', 'p' + env.chip + '.gld'), 
            '-Map=%s.map' % env.subst(join('$BUILD_DIR','$PROGNAME')),
            #'--gc-sections', # !!!
            #'--report-mem',
        ],

        BUILDERS = dict(
            ELF2HEX = Builder(
                action = env.VerboseAction(' '.join([ '$HEX', '$SOURCES',]), 'Creating HEX $TARGET'),
                suffix = '.hex'
            )           
        ),        
    )

    env.AddPostAction(
        '$BUILD_DIR/${PROGNAME}.elf',
        env.VerboseAction(' '.join([ '$OBJCOPY', '-d', '$SOURCES', '> $BUILD_DIR/${PROGNAME}.lst']), 'Creating List ${PROGNAME}.lst'),
    )