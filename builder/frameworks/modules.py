# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

import os, hashlib
from wiz import INFO, ERROR
from importlib.machinery import SourceFileLoader

def PRINT_MODULE_INFO(txt): 
    INFO('\t%s' % txt)

def dev_module_load(env, module_path, params=None):
    module_path = env.subst( module_path )
    name = hashlib.md5( module_path.encode() ).hexdigest()
    if name not in env.modules:
        SourceFileLoader(name, module_path).load_module().init( env, params )
        env.modules.append(name)

def dev_init_modules(env):
    env.modules = []
    env['MODULES'] = env.modules_dir = os.path.join( env.platform_dir, 'modules', env['PIOFRAMEWORK'][0])
    lines = env.GetProjectOption('custom_modules', None) # INIDOC
    if lines:
        INFO('PROJECT MODULES')
        for line in lines.split('\n'):
            if line == '': 
                continue

            line = line.strip().replace('\r', '').replace('\t', '')
            delim = '='
            params = ''
            if delim in line:
                params = line[ line.index( delim ) + 1 : ].strip()
                params = ' '.os.path.join( params.split() )
                line = line.partition( delim )[0].strip()
            module_path = env.subst( line ).strip()

            if False == os.path.isabs( module_path ):
                module_path = env.subst( os.path.join( '$MODULES', module_path ) ) 

            if False == os.path.exists( module_path ):
                ERROR('[MODULE] File not found: %s' % module_path)

            if True == os.path.isdir( module_path ):
                for root, dirs, files in os.walk( module_path ):
                    files = [ f for f in files if f.endswith('.py') ] 
                    for file in files:
                        if not os.path.basename( file ).startswith('module-'): 
                            continue 
                        dev_module_load(env, os.path.join(root, file), params)
            else:
                if not os.path.basename( module_path ).startswith('module-'):
                    ERROR('[MODULE] Unknown file: <%s> Must begin with "module-"' % os.path.basename(module_path))
                dev_module_load(env, module_path, params)
