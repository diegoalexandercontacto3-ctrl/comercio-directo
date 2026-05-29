lines = open('backend.py', 'r', encoding='utf-8').readlines()

for i, line in enumerate(lines):
    if 'hoja.append_row' in line:
        indent = len(line) - len(line.lstrip())
        sp = ' ' * indent
        old_line = line
        new_lines = [
            sp + 'todos_datos = hoja.get_all_values()\n',
            sp + 'siguiente_fila = len(todos_datos) + 1\n',
            sp + 'hoja.update(f"A{siguiente_fila}:H{siguiente_fila}", [[fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago]])\n',
            sp + 'print(f"ESCRITO EN FILA {siguiente_fila}", flush=True)\n',
        ]
        lines[i:i+1] = new_lines
        open('backend.py', 'w', encoding='utf-8').writelines(lines)
        print('PATCH OK en linea', i)
        exit()

print('NO ENCONTRADO')