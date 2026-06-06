content = open('backend.py', 'r', encoding='utf-8').read()

import re
# Agregar flush=True a todos los prints dentro de guardar_en_sheets
def add_flush(match):
    s = match.group(0)
    if 'flush=True' not in s:
        s = s[:-1] + ', flush=True)'
    return s

# Solo en las lineas de guardar_en_sheets (aproximadamente)
lines = content.split('\n')
in_guardar = False
new_lines = []
for line in lines:
    if 'def guardar_en_sheets' in line:
        in_guardar = True
    elif in_guardar and line.startswith('def '):
        in_guardar = False
    
    if in_guardar and 'print(' in line and 'flush=True' not in line:
        line = line.replace(')', ', flush=True)', 1)
    new_lines.append(line)

open('backend.py', 'w', encoding='utf-8').write('\n'.join(new_lines))
print('PATCH OK')