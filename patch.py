content = open('backend.py', 'r', encoding='utf-8').read()

old = "    notificar_telegram(resumen)\n    datos = extraer_datos_venta(historial_raw + [{'role': 'user', 'content': mensaje}])\n    guardar_en_sheets(datos['nombre'], datos['direccion'], datos['localidad'], datos['telefono'], datos['producto'], datos['total'], datos"

# Buscar donde termina la linea de guardar_en_sheets
idx = content.find("    notificar_telegram(resumen)")
end_idx = content.find("\n    return jsonify", idx)

if idx != -1 and end_idx != -1:
    bloque_nuevo = """    notificar_telegram(resumen)
    try:
        datos = extraer_datos_venta(historial_raw + [{'role': 'user', 'content': mensaje}])
        guardar_en_sheets(datos.get('nombre', lead.get('nombre','')), datos.get('direccion',''), datos.get('localidad',''), datos.get('telefono', mensaje), datos.get('producto',''), datos.get('total',''), datos.get('metodo_pago',''))
        print("SHEETS OK desde capturando")
    except Exception as e:
        import traceback
        print(f"SHEETS ERROR capturando: {e}")
        print(traceback.format_exc())"""
    new_content = content[:idx] + bloque_nuevo + content[end_idx:]
    open('backend.py', 'w', encoding='utf-8').write(new_content)
    print('PATCH OK')
else:
    print('TARGET NO ENCONTRADO - idx:', idx, 'end_idx:', end_idx)