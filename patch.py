content = open('backend.py', 'r', encoding='utf-8').read()

nueva_funcion = '''def guardar_en_sheets(nombre, direccion, localidad, telefono, producto, total, metodo_pago):
    try:
        import json as _json
        import google.auth.transport.requests
        scope = ['https://www.googleapis.com/auth/spreadsheets']
        creds_info = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key": os.getenv('GOOGLE_PRIVATE_KEY', '').replace('\\\\n', '\\n'),
            "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        from google.oauth2.service_account import Credentials
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        creds.refresh(google.auth.transport.requests.Request())
        print(f"TOKEN OK: {creds.token[:20]}", flush=True)
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        SHEET_ID = '10NJleuQGDydiXWTLSfQAbgdEs9nTvQyY9FrfCh4bKqg'
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/Sheet1!A1:append?valueInputOption=USER_ENTERED'
        headers = {'Authorization': f'Bearer {creds.token}', 'Content-Type': 'application/json'}
        data = {'values': [[fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago]]}
        import requests as _requests
        resp = _requests.post(url, json=data, headers=headers)
        print(f"SHEETS API: {resp.status_code} {resp.text[:200]}", flush=True)
    except Exception as e:
        import traceback
        print(f"SHEETS ERROR: {e}", flush=True)
        print(traceback.format_exc(), flush=True)
'''

# Reemplazar la funcion completa
import re
content = re.sub(r'def guardar_en_sheets\(.*?\n(?=def |\Z)', nueva_funcion + '\n', content, flags=re.DOTALL)
open('backend.py', 'w', encoding='utf-8').write(content)
print('PATCH OK')