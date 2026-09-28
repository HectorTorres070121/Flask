from flask import Flask, jsonify
import json

with open("API.json", "r", encoding="utf-8") as json_api:
    datos_json = json.load(json_api)

app = Flask(__name__)

# Endpoint principal
@app.route('/')
def inicio():
    print("Cambio")
    return jsonify("3D:RF:09:7F::")


@app.route('/json/<mac>')
def json_data(mac):
   
    router = datos_json.get(mac.upper(), {})
    
    print("Nombre:", router.get("Name"))
    print("Protocolos:", router.get("Protocolos"))
    print("Estatus:", router.get("estatus", "No especificado"))
    print("VLANs:", router.get("VLANs"))
    return router.get("Name", ("MAC no encontrada", 404))

# Endpoint JSON Servidores
@app.route('/servidor_1')
def servidor_1():
    return jsonify({
        "0001": {
            "nombre": "Servidor-Web-01",
            "ip": "192.168.1.50",
            "politica": "Permitir-HTTP-HTTPS",
            "estado": "Activo"
        },
        "0002": {
            "nombre": "BaseDeDatos-Master",
            "ip": "192.168.1.51",
            "politica": "Solo-Acceso-Interno",
            "estado": "Activo"
        },
        "0003": {
            "nombre": "Servidor-Archivos-01",
            "ip": "192.168.1.52",
            "politica": "Solo-Acceso-Interno",
            "estado": "Activo"
        },
        "0004": {
            "nombre": "Servidor-DNS-01",
            "ip": "192.168.1.53",
            "politica": "DNS-UDP-TCP",
            "estado": "Activo"
        },
        "0005": {
            "nombre": "Servidor-Aplicaciones-01",
            "ip": "192.168.1.54",
            "politica": "Permitir-HTTP-HTTPS",
            "estado": "Activo"
        },
        "0006": {
            "nombre": "Servidor-Backup-01",
            "ip": "192.168.1.55",
            "politica": "Solo-Acceso-Interno",
            "estado": "Activo"
        },
        "0007": {
            "nombre": "Servidor-Monitoreo-01",
            "ip": "192.168.1.56",
            "politica": "Solo-Acceso-Interno",
            "estado": "Activo"
        },
        "0008": {
            "nombre": "Servidor-Correo-01",
            "ip": "192.168.1.57",
            "politica": "Permitir-SMTP-IMAP",
            "estado": "Activo"
        },
        "0009": {
            "nombre": "Servidor-Proxy-01",
            "ip": "192.168.1.58",
            "politica": "Filtrado-Web",
            "estado": "Activo"
        },
        "0010": {
            "nombre": "Servidor-Desarrollo-01",
            "ip": "192.168.1.59",
            "politica": "Acceso-Desarrollo",
            "estado": "Activo"
        }
    })

if __name__ == '__main__':
    app.run(debug=True)