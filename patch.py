content = open('backend.py', 'r', encoding='utf-8').read()

patch = """
    if tipo == 'escalado':
        try:
            datos = extraer_datos_venta(historial_raw + [{'role': 'user', 'content': mensaje}])
            guardar_en_sheets(datos['nombre'], datos['direccion'], datos['localidad'], datos['telefono'], datos['producto'], datos['total'], datos.get('metodo_pago', ''))
        except Exception as e:
            import traceback
            print(f'SHEETS ERROR: {e}')
            print(traceback.format_exc())

"""

target = "    session['historial'] = historial_raw + ["

last_idx = content.rfind(target)
if last_idx != -1:
    new_content = content[:last_idx] + patch + content[last_idx:]
    open('backend.py', 'w', encoding='utf-8').write(new_content)
    print('PATCH OK')
else:
    print('TARGET NO ENCONTRADO')