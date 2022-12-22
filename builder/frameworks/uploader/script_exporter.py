# Copyright 2022 (c) 2022 WizIO ( Georgi Angelov )

import re, json 
from os.path import join, normpath, dirname

'''
<scripts>
  <commit>7acb7c9d66</commit>
  <version>000448</version>
  <script>
    <function>InitSWD</function>
    <processor>ATSAMA5D21</processor>
    <ri4command>0x00000215</ri4command>
    <scrbytes>
        <byte>0x91</byte>
    </scrbytes>
  </script>    
'''

scripts_file_path = 'C:/Program Files/Microchip/MPLABX/v5.50/packs/Microchip/PICkit4_TP/1.8.1120/firmware/scripts.xml' # select path

DIC = {}
DIC['PIC'] = 'PIC24FJ256GB206' # select pic

THIS_DIR = normpath( dirname(__file__) )

def get_scr(f):
    SCR = []
    while True:
        LL = f.readline() 
        if '</scrbytes>' in LL: 
            return SCR
        LL = LL.strip().replace('<byte>', '').replace('</byte>', '')#.replace('0x', '')
        SCR.append( int(LL,0) )

def get_script(f):
    global DIC
    L = f.readline()
    L += f.readline()
    L += f.readline()
    if '<processor>' + DIC['PIC'] not in L: return    
    SCR = []
    while True:
        LL = f.readline()  
        if '</script>' in LL: 
            name = re.search('%s(.*)%s' % ('<function>', '</function>'), L).group(1)
            #print('FUNCTION :', name)    
            #print('SCRIPT   :', SCR)  
            DIC[name] = SCR   
            break
        SCR = get_scr(f)
        L += LL
    print()

f = open(scripts_file_path, 'r')
while True:
    line = f.readline()
    if '' == line: break
    if '<script>' in line:
        get_script(f)


f.close()
print(DIC)
json_object = json.dumps(DIC, indent = 2, sort_keys=True) 
with open( join(THIS_DIR, DIC['PIC'] + '.json'), 'w') as outfile: outfile.write(json_object)
print('[EXIT]')
exit(0)

