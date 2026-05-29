lines = open('backend.py', 'r', encoding='utf-8').readlines()

# Buscar linea 249 (datos = extraer_datos_venta) dentro del bloque ESCALAR
for i, line in enumerate(lines):
    if 'extraer_datos_venta' in line and i > 235:  # solo el bloque ESCALAR
        guardar_idx = None
        for j in range(i, min(i+3, len(lines))):
            if 'guardar_en_sheets' in lines[j]:
                guardar_idx = j
                break
        if guardar_idx:
            datos_line = lines[i].lstrip().rstrip('\n')
            guardar_line = lines[guardar_idx].lstrip().rstrip('\n')
            new_block = [
                '        try:\n',
                '            ' + datos_line + '\n',
                '            print(f"DATOS EXTRAIDOS: {datos}", flush=True)\n',
                '            ' + guardar_line + '\n',
                '            print("SHEETS OK", flush=True)\n',
                '        except Exception as e:\n',
                '            import traceback\n',
                '            print(f"SHEETS ERROR: {e}", flush=True)\n',
                '            print(traceback.format_exc(), flush=True)\n',
            ]
            lines[i:guardar_idx+1] = new_block
            open('backend.py', 'w', encoding='utf-8').writelines(lines)
            print('PATCH OK en linea', i)
            exit()

print('NO ENCONTRADO')