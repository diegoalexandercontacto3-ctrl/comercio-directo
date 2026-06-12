import os
import json
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

def guardar_en_sheets(nombre, direccion, localidad, telefono, producto, total, metodo_pago):
    try:
        creds_raw = os.getenv('GOOGLE_CREDENTIALS')
        creds_info = json.loads(creds_raw)
        creds_info['private_key'] = creds_info['private_key'].replace('\\n', '\n')
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        cliente = gspread.authorize(creds)
        sheet = cliente.open_by_key('10NJleuQGDydiXWTLSfQAbgdEs9nTvQyY9FrfCh4bKqg')
        hoja = sheet.sheet1
        fecha = datetime.now().strftime('%d/%m/%Y %H:%M')
        hoja.append_row([fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago])
        print("GSPREAD OK", flush=True)
    except Exception as e:
        import traceback
        print(f"GSPREAD ERROR: {e}", flush=True)
        print(traceback.format_exc(), flush=True)