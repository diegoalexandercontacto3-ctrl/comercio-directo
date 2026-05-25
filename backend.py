import os
from dotenv import load_dotenv
from typing import TypedDict, List
from langgraph.graph import StateGraph, END
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_community.tools import DuckDuckGoSearchRun
from flask import Flask, request, jsonify, render_template, session
import requests
import secrets
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)

buscador = DuckDuckGoSearchRun()
llm = ChatGroq(model='llama-3.1-8b-instant', temperature=0.7)

def get_sistema_base(negocio):
    return """Sos el asistente virtual de ComercioDirectoARG, una tienda de tecnologia y hogar con sede en La Tablada, Buenos Aires, Argentina.

Informacion del negocio:
- Nombre: ComercioDirectoARG
- Rubro: Tecnologia original a precio directo
- Instagram: @comerciodirectoarg

Productos disponibles:
- Cargador Rapido 4.2A Ditron (salida USB, ultra potente): $13.499

Zonas de entrega y costos de envio (entrega al dia habil siguiente):
IMPORTANTE sobre zonas: Los barrios de CABA (Palermo, Belgrano, Villa Crespo, Recoleta, Caballito, San Telmo, Almagro, Flores, Balvanera, Boedo, barracas, La Boca, Mataderos, Liniers, Devoto, Saavedra, Colegiales, Chacarita, Villa Urquiza, Paternal, Monte Castro, Versalles, Villa del Parque, Villa Santa Rita, Villa General Mitre, Villa Pueyrredon, Villa Ortuzar, Agronomia, Parque Avellaneda, Nueva Pompeya, Parque Patricios, San Cristobal, Montserrat, Puerto Madero, Retiro, Once, Barracas, Villa Lugano, Villa Soldati, Pompeya, Parque Chacabuco, Villa Riachuelo) son SIEMPRE zona CABA con costo $6.500. NUNCA los clasifiques como GBA.
- CABA: $6.500
- 1er cordon GBA (Avellaneda, Lanus, Lomas de Zamora, La Matanza Norte, Moron, Hurlingham, Ituzaingo, Tres de Febrero, San Martin, Vicente Lopez, San Isidro, San Fernando): $9.500
- 2do cordon GBA (Quilmes, Almirante Brown, Esteban Echeverria, Ezeiza, Merlo, Moreno, Ituzaingo, Tigre, Malvinas Argentinas, Jose C Paz, San Miguel): $9.500
- 3er cordon GBA (Florencio Varela, Berazategui, La Plata, Berisso, Ensenada, Presidente Peron, San Vicente, Matanza Sur, Marcos Paz, General Rodriguez, Lujan, Pilar, Escobar, Campana, Zarate, Canuelas): $11.000
- Provincias o zonas no listadas: consultar precio

Metodos de pago:
- Transferencia bancaria: Alias: comerciodirecto / Titular: Diego Alexander Lamberti
- Pago contra entrega (disponible en todas las zonas listadas)

REGLA CRITICA: En ambos procesos de venta, haz UNA SOLA PREGUNTA POR VEZ, en el orden exacto indicado. NO calcules ni informes datos hasta tener la respuesta del paso anterior. NO te saltes ningun paso.

Proceso de venta contra entrega:
Cuando el cliente quiere comprar, DEBES seguir estos pasos EN ORDEN ESTRICTO. NO calcules precios ni zonas hasta tener TODOS los datos de los pasos anteriores:
1. Preguntar el producto que quiere comprar
2. Preguntar su nombre completo
3. Preguntar su direccion exacta (calle, numero, piso/depto si tiene)
4. Preguntar el partido o localidad
5. Calcular el costo de envio segun la zona
6. Confirmar el total: precio del producto + costo de envio
7. Informar que la entrega es al dia habil siguiente
8. Pedir numero de telefono de contacto
9. Una vez que tenes todos los datos responde exactamente: ESCALAR

Proceso de venta por transferencia:
Cuando el cliente quiere comprar, DEBES seguir estos pasos EN ORDEN ESTRICTO. NO calcules precios ni zonas hasta tener TODOS los datos de los pasos anteriores:
1. Preguntar el producto que quiere comprar
2. Preguntar su nombre completo
3. Preguntar su direccion exacta (calle, numero, piso/depto si tiene)
4. Preguntar el partido o localidad
5. Calcular el costo de envio segun la zona
6. Confirmar el total: precio del producto + costo de envio
7. Informar que la entrega es al dia habil siguiente
8. Pedir numero de telefono de contacto
9. Dar el alias: comerciodirecto / Titular: Diego Alexander Lamberti e informar que debe mandar el comprobante al WhatsApp: 1124073472
10. Avisar que sin comprobante no se envia el producto
11. Una vez que tenes todos los datos responde exactamente: ESCALAR

Reglas:
- Siempre responde en espanol, de forma amable y directa
- Cuando un cliente quiere comprar, primero confirma el producto que quiere comprar, luego pregunta el metodo de pago
- Si el cliente esta enojado, primero disculpate y luego ofrece soluciones
- Si el cliente pide hablar con una persona o con alguien del equipo, DEBES responder UNICAMENTE la palabra: ESCALAR
- NUNCA des el numero de WhatsApp directamente cuando pide hablar con una persona
- NUNCA inventes numeros de telefono, direcciones, ni informacion que no este en este prompt
- NUNCA menciones numeros de contacto de la tienda porque no los tenes
- No inventes productos ni precios que no esten en la lista
- La entrega siempre es al dia habil siguiente, nunca el mismo dia
- Si el cliente eligio contra entrega, NUNCA menciones el alias ni la transferencia bancaria
- Si el cliente eligio transferencia, NUNCA menciones el pago contra entrega
- Despues de tener todos los datos NO sigas respondiendo preguntas, espera que un humano tome el control
- Cuando tengas todos los datos del cliente para la entrega, responde UNICAMENTE la palabra: ESCALAR
- La palabra ESCALAR es una palabra interna, NUNCA la menciones al cliente ni digas que vas a escalar. Solo usala como respuesta interna cuando tengas todos los datos completos.
- NUNCA ofrezcas ni menciones el numero de telefono de la tienda durante la conversacion, solo pedi el numero del cliente para coordinar la entrega"""

class Estado(TypedDict):
    mensaje: str
    tipo: str
    busqueda: str
    respuesta: str
    historial: List
    sistema: str

def clasificar(estado):
    prompt = [SystemMessage(content='Clasifica en UNA sola palabra: queja, busqueda o consulta.'),
              HumanMessage(content=estado['mensaje'])]
    resultado = llm.invoke(prompt)
    return {'tipo': resultado.content.strip().lower()}

def buscar_web(estado):
    resultado = buscador.run(estado['mensaje'])
    return {'busqueda': resultado}

def responder_consulta(estado):
    mensajes = [SystemMessage(content=estado['sistema'])]
    mensajes += estado['historial']
    mensajes.append(HumanMessage(content=estado['mensaje']))
    resultado = llm.invoke(mensajes)
    return {'respuesta': resultado.content}

def responder_con_busqueda(estado):
    mensajes = [SystemMessage(content=estado['sistema'])]
    mensajes += estado['historial']
    mensajes.append(HumanMessage(content=f"Pregunta: {estado['mensaje']}\n\nInfo: {estado['busqueda']}"))
    resultado = llm.invoke(mensajes)
    return {'respuesta': resultado.content}

def manejar_queja(estado):
    mensajes = [SystemMessage(content=estado['sistema'] + '\nATENCION: El cliente esta presentando una queja.')]
    mensajes += estado['historial']
    mensajes.append(HumanMessage(content=estado['mensaje']))
    resultado = llm.invoke(mensajes)
    return {'respuesta': resultado.content}

def decidir(estado):
    tipo = estado['tipo']
    if 'queja' in tipo: return 'queja'
    elif 'busqueda' in tipo: return 'buscar'
    else: return 'consulta'

grafo = StateGraph(Estado)
grafo.add_node('clasificar', clasificar)
grafo.add_node('buscar', buscar_web)
grafo.add_node('responder_busqueda', responder_con_busqueda)
grafo.add_node('consulta', responder_consulta)
grafo.add_node('queja', manejar_queja)
grafo.set_entry_point('clasificar')
grafo.add_conditional_edges('clasificar', decidir,
    {'queja': 'queja', 'buscar': 'buscar', 'consulta': 'consulta'})
grafo.add_edge('buscar', 'responder_busqueda')
grafo.add_edge('responder_busqueda', END)
grafo.add_edge('consulta', END)
grafo.add_edge('queja', END)
agente = grafo.compile()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/config', methods=['POST'])
def config():
    data = request.json
    session['negocio'] = data.get('negocio')
    session['historial'] = []
    session['capturando'] = None
    session['lead'] = {}
    return jsonify({'ok': True})

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    mensaje = data.get('mensaje')
    negocio = session.get('negocio', 'el negocio')
    historial_raw = session.get('historial', [])
    capturando = session.get('capturando')
    
    historial = []
    for m in historial_raw:
        if m['role'] == 'user':
            historial.append(HumanMessage(content=m['content']))
        else:
            historial.append(AIMessage(content=m['content']))

    if capturando == 'nombre':
        session['lead'] = {'nombre': mensaje}
        session['capturando'] = 'telefono'
        session['historial'] = historial_raw + [
            {'role': 'user', 'content': mensaje},
            {'role': 'assistant', 'content': '¿Cuál es tu número de teléfono?'}
        ]
        return jsonify({'respuesta': '¿Cuál es tu número de teléfono?', 'tipo': 'escalado', 'capturando': 'telefono'})

    if capturando == 'telefono':
        lead = session.get('lead', {})
        lead['telefono'] = mensaje
        session['lead'] = lead
        session['capturando'] = None
        session['historial'] = historial_raw + [
            {'role': 'user', 'content': mensaje},
            {'role': 'assistant', 'content': f"Gracias {lead.get('nombre', '')}. Un responsable te va a contactar a la brevedad al {mensaje}."}
        ]
        lead = session.get('lead', {})
        historial_raw = session.get('historial', [])
        resumen = 'NUEVA VENTA - ComercioDirectoARG\n'
        resumen += 'Nombre: ' + lead.get('nombre', '') + '\n'
        resumen += 'Telefono: ' + mensaje + '\n'
        resumen += '\nConversacion:\n'
        for m in historial_raw[-10:]:
            rol = 'Cliente' if m['role'] == 'user' else 'Agente'
            resumen += rol + ': ' + m['content'] + '\n'
        notificar_telegram(resumen)
        datos = extraer_datos_venta(historial_raw + [{'role': 'user', 'content': mensaje}])
        guardar_en_sheets(datos['nombre'], datos['direccion'], datos['localidad'], datos['telefono'], datos['producto'], datos['total'], datos.get('metodo_pago', ''))
        return jsonify({'respuesta': f"Gracias {lead.get('nombre', '')}. Un responsable te va a contactar a la brevedad al {mensaje}.", 'tipo': 'escalado_completo', 'capturando': None})

    sistema = get_sistema_base(negocio)
    resultado = agente.invoke({
        'mensaje': mensaje, 'tipo': '', 'busqueda': '', 'respuesta': '',
        'historial': historial, 'sistema': sistema
    })

    respuesta = resultado['respuesta']
    tipo = resultado['tipo']

    if 'ESCAL' in respuesta.upper() or 'ESCOA' in respuesta.upper():
        historial_raw = session.get('historial', [])
        resumen = 'NUEVA VENTA - ComercioDirectoARG\n\nConversacion:\n'
        for m in historial_raw[-20:]:
            rol = 'Cliente' if m['role'] == 'user' else 'Agente'
            resumen += rol + ': ' + m['content'] + '\n'
        resumen += 'Cliente: ' + mensaje + '\n'
        notificar_telegram(resumen)
        _lead = session.get('lead', {})
        datos = extraer_datos_venta(historial_raw + [{'role': 'user', 'content': mensaje}])
        guardar_en_sheets(datos['nombre'], datos['direccion'], datos['localidad'], datos['telefono'], datos['producto'], datos['total'], datos.get('metodo_pago', ''))
        respuesta = 'Perfecto! Ya le avisamos a un responsable de ComercioDirectoARG. Te van a contactar a la brevedad para confirmar tu pedido.'
        tipo = 'escalado_completo'

    session['historial'] = historial_raw + [
        {'role': 'user', 'content': mensaje},
        {'role': 'assistant', 'content': respuesta}
    ]

    return jsonify({'respuesta': respuesta, 'tipo': tipo, 'capturando': session.get('capturando')})

@app.route('/api/reset', methods=['POST'])

def extraer_datos_venta(historial_raw):
    try:
        import json
        texto = "\n".join([f"{'Cliente' if m['role']=='user' else 'Agente'}: {m['content']}" for m in historial_raw[-20:]])
        prompt = [SystemMessage(content='Extrae datos del CLIENTE (no del vendedor Diego Alexander Lamberti ni de ComercioDirectoARG) de esta conversación de venta. Responde SOLO con JSON valido, sin texto extra: {"nombre":"","direccion":"","localidad":"","telefono":"","producto":"","total":"","metodo_pago":""}'),
                  HumanMessage(content=texto)]
        resultado = llm.invoke(prompt)
        texto_respuesta = resultado.content.strip()
        inicio = texto_respuesta.find('{')
        fin = texto_respuesta.rfind('}') + 1
        texto_respuesta = texto_respuesta[inicio:fin]
        datos = json.loads(texto_respuesta)
        return datos
    except Exception as e:
        print(f"Error extrayendo datos: {e}")
        return {"nombre":"","direccion":"","localidad":"","telefono":"","producto":"","total":""}

def guardar_en_sheets(nombre, direccion, localidad, telefono, producto, total, metodo_pago):
    try:
        scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
        import json as json_module
        creds_info = json_module.loads(os.getenv('GOOGLE_CREDENTIALS'))
        creds_info['private_key'] = creds_info['private_key'].replace('\\n', '\n')
        creds = Credentials.from_service_account_info(creds_info, scopes=scope)
        client = gspread.authorize(creds)
        sheet = client.open("Ventas comercio directo").sheet1
        fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
        sheet.append_row([fecha, nombre, direccion, localidad, telefono, producto, total, metodo_pago])
    except Exception as e:
        print(f"Error guardando en Sheets: {e}")

def notificar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = 'https://api.telegram.org/bot' + token + '/sendMessage'
    requests.post(url, data={'chat_id': chat_id, 'text': mensaje})

def reset():
    session.clear()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)