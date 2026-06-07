import re

content = open('backend.py', 'r', encoding='utf-8').read()

# Eliminar la funcion guardar_en_sheets del backend.py
content = re.sub(
    r'\ndef guardar_en_sheets\(.*?\n(?=\ndef |\nif name)',
    '\n',
    content,
    flags=re.DOTALL
)

open('backend.py', 'w', encoding='utf-8').write(content)
print('PATCH OK')