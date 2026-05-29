lines = open('backend.py', 'r', encoding='utf-8').readlines()

nueva = [
    '        try:\n',
    '            datos = extraer_datos_venta(historial_raw + [{\'role\': \'user\', \'content\': mensaje}])\n',
    '            guardar_en_sheets(datos.get(\'nombre\',\'\'), datos.get(\'direccion\',\'\'), datos.get(\'localidad\',\'\'), datos.get(\'telefono\', mensaje), datos.get(\'producto\',\'\'), datos.get(\'total\',\'\'), datos.get(\'metodo_pago\',\'\'))\n',
    '            print(\'SHEETS OK\')\n',
    '        except Exception as e:\n',
    '            import traceback\n',
    '            print(f\'SHEETS ERROR: {e}\')\n',
    '            print(traceback.format_exc())\n',
]

for i, line in enumerate(lines):
    if 'extraer_datos_venta' in line and 'def ' not in line:
        for j in range(i, min(i+3, len(lines))):
            if 'guardar_en_sheets' in lines[j]:
                lines[i:j+1] = nueva
                open('backend.py', 'w', encoding='utf-8').writelines(lines)
                print('PATCH OK')
                exit()

print('NO ENCONTRADO')