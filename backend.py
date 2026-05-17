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
- Ubicacion: La Tablada, Buenos Aires

Productos disponibles:
- Cargador Rapido 4.2A Ditron (salida USB, ultra potente): $13.499

Envios y logistica:
- Envios en moto el mismo dia en CABA y cordon GBA 1°, 2° y 3° de Buenos Aires
- Solo productos chicos (entran en moto)
- Envios a provincias por Correo Argentino
Costo de envio:
- CABA: $6.500
- 1° cordon GBA: $9.500
- 2° cordon GBA: $9.500
- 3° cordon GBA: $9.500
- Provincias o zonas fuera de las anteriores: consultar precio de envio
- Pago contra entrega disponible para envios en moto
- Para provincias se paga por transferencia antes del envio

Metodos de pago:
- Transferencia bancaria: Alias: comerciodirecto / Titular: Diego Alexander Lamberti
- Pago contra entrega (solo CABA y cordon GBA 1°, 2° y 3°)

Proceso de compra por transferencia:
1. El cliente confirma el producto y la direccion de entrega
2. Le das el alias: comerciodirecto / Titular: Diego Alexander Lamberti
3. El cliente hace la transferencia y manda el comprobante al WhatsApp: 1124073472
4. Avisas que sin comprobante no se envia el producto
5. Una vez confirmado el pago se coordina la entrega

Proceso de compra contra entrega:
1. El cliente confirma el producto y da su nombre, direccion y horario disponible
2. Se coordina la entrega y el pago se realiza al recibir el producto

Reglas:
- Siempre responde en espanol, de forma amable y directa
- Cuando un cliente quiere comprar, preguntale el metodo de pago primero
- Si elige transferencia: dal el alias y pedi que manden el comprobante al WhatsApp 1124073472
- Si elige contra entrega: pedile nombre completo, direccion exacta y horario disponible, luego responde exactamente: ESCALAR
- Si el cliente esta enojado, primero disculpate y luego ofrece soluciones
- Si el cliente pide hablar con una persona, responde exactamente: ESCALAR
- No inventes productos ni precios que no esten en la lista"""

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
        notificar_telegram(
            'NUEVA CONSULTA - ComercioDirectoARG\n'
            'Nombre: ' + lead.get('nombre', '') + '\n'
            'Telefono: ' + mensaje
        )
        return jsonify({'respuesta': f"Gracias {lead.get('nombre', '')}. Un responsable te va a contactar a la brevedad al {mensaje}.", 'tipo': 'escalado_completo', 'capturando': None})

    sistema = get_sistema_base(negocio)
    resultado = agente.invoke({
        'mensaje': mensaje, 'tipo': '', 'busqueda': '', 'respuesta': '',
        'historial': historial, 'sistema': sistema
    })

    respuesta = resultado['respuesta']
    tipo = resultado['tipo']

    if 'ESCALAR' in respuesta:
        session['capturando'] = 'nombre'
        respuesta = '¿Me podés decir tu nombre para avisarle a un responsable?'
        tipo = 'escalado'

    session['historial'] = historial_raw + [
        {'role': 'user', 'content': mensaje},
        {'role': 'assistant', 'content': respuesta}
    ]

    return jsonify({'respuesta': respuesta, 'tipo': tipo, 'capturando': session.get('capturando')})

@app.route('/api/reset', methods=['POST'])

def notificar_telegram(mensaje):
    token = os.getenv('TELEGRAM_TOKEN')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    url = f'https://api.telegram.org/bot{token}/sendMessage'
    requests.post(url, data={'chat_id': chat_id, 'text': mensaje})

def reset():
    session.clear()
    return jsonify({'ok': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)