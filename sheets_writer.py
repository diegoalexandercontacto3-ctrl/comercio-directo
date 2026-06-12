import os
import requests
from datetime import datetime
from google.oauth2.service_account import Credentials
import google.auth.transport.requests

def guardar_en_sheets(nombre, direccion, localidad, telefono, producto, total, metodo_pago):
    try:
        private_key = os.getenv('GOOGLE_PRIVATE_KEY', '')
        if '\\n' in private_key:
            private_key = private_key.replace('\\n', '\n')
        
        creds_info = {
            "type": "service_account",
            "project_id": os.getenv('GOOGLE_PROJECT_ID'),
            "private_key": private_key,
            "client_email": os.getenv('GOOGLE_CLIENT_EMAIL'),
            "token_uri": "https://oauth2.googleapis.com/token"
        }
        creds = Credentials.from_service_account_info(
            creds_info,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        creds.refresh(google.auth.transport.requests.Request())
        print(f"CLIENT EMAIL: {creds.service_account_email}", flush=True)
        
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        SHEET_ID = '10NJleuQGDydiXWTLSfQAbgdEs9nTvQyY9FrfCh4bKqg'
        url = f'https://sheets.googleapis.com/v4/spreadsheets/{SHEET_ID}/values/A1:append?valueInputOption=USER_ENTERED&insertDataOption=INSERT_ROWS'
        headers = {
            'Authorization': f'Bearer {creds.token}',
            'Content-Type': 'application/json'
        }
        data = {'values': [[fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago]]}
        resp = requests.post(url, json=data, headers=headers)
        print(f"SHEETS API: {resp.status_code}", flush=True)
        print(f"SHEETS RESPONSE: {resp.text[:300]}", flush=True)
    except Exception as e:
        import traceback
        print(f"SHEETS ERROR: {e}", flush=True)
        print(traceback.format_exc(), flush=True)