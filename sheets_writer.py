import os
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

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
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        cliente = gspread.authorize(creds)
        print("GSPREAD: autorizado", flush=True)
        sheet = cliente.open_by_key('10NJleuQGDydiXWTLSfQAbgdEs9nTvQyY9FrfCh4bKqg')
        print(f"GSPREAD: sheet abierto - {sheet.title}", flush=True)
        hoja = sheet.sheet1
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        hoja.append_row([fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago])
        print("GSPREAD: fila guardada OK", flush=True)
    except Exception as e:
        import traceback
        print(f"GSPREAD ERROR: {e}", flush=True)
        print(traceback.format_exc(), flush=True)