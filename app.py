import json
import os
import re
import tempfile
import threading
from pathlib import Path

from flask import Flask, abort, jsonify, redirect, render_template, request, url_for


app = Flask(__name__)
API_JSON_PATH = Path(__file__).with_name("API.json")
API_JSON_LOCK = threading.Lock()
MAC_PATTERN = re.compile(r"[A-Za-z0-9]{2}(?::[A-Za-z0-9]{2}){5}")
NAME_PATTERN = re.compile(r"[A-Za-zÀ-ÖØ-öø-ÿ0-9][A-Za-zÀ-ÖØ-öø-ÿ0-9 _.-]{0,49}")
VLAN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}")
TOKEN_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,31}")
PORT_PATTERN = re.compile(r"[A-Za-z][A-Za-z0-9/-]{0,31}")
IPV4_PATTERN = re.compile(
    r"(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)"
    r"(?:\.(?:25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}"
)


def load_api_data():
    with API_JSON_PATH.open("r", encoding="utf-8") as json_api:
        data = json.load(json_api)
    if not isinstance(data, dict):
        raise ValueError("API.json debe contener un objeto JSON de routers.")
    return data


def write_api_data(data):
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=API_JSON_PATH.parent,
            delete=False,
        ) as json_api:
            temporary_path = Path(json_api.name)
            json.dump(data, json_api, ensure_ascii=False, indent=2)
            json_api.write("\n")
        os.replace(temporary_path, API_JSON_PATH)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def split_form_list(value):
    return [
        item.strip()
        for item in value.replace(",", "\n").splitlines()
        if item.strip()
    ]


def router_form_values(router=None, mac="", form=None):
    if form is not None:
        vlan_names = form.getlist("vlan_name")
        vlan_ports = form.getlist("vlan_ports")
        vlan_policies = form.getlist("vlan_policies")
        vlan_ets = form.getlist("vlan_et")
        vlan_ips = form.getlist("vlan_ip")
        vlan_sshs = form.getlist("vlan_ssh")
        vlan_count = max(
            len(vlan_names),
            len(vlan_ports),
            len(vlan_policies),
            len(vlan_ets),
            len(vlan_ips),
            len(vlan_sshs),
        )
        vlans = [
            {
                "name": vlan_names[index] if index < len(vlan_names) else "",
                "ports": vlan_ports[index] if index < len(vlan_ports) else "",
                "policies": (
                    vlan_policies[index] if index < len(vlan_policies) else ""
                ),
                "et": vlan_ets[index] if index < len(vlan_ets) else "",
                "ip": vlan_ips[index] if index < len(vlan_ips) else "",
                "ssh": vlan_sshs[index] if index < len(vlan_sshs) else "",
            }
            for index in range(vlan_count)
        ]
        return {
            "mac": form.get("mac", "").strip(),
            "name": form.get("name", "").strip(),
            "protocolos": form.get("protocolos", "").strip(),
            "estatus": form.get("estatus", ""),
            "vlans": vlans,
        }

    router = router or {}
    vlans = [
        {
            "name": vlan_name,
            "ports": "\n".join(vlan.get("Ports", [])),
            "policies": "\n".join(vlan.get("Policies", [])),
            "et": str(vlan.get("ET", True)).lower(),
            "ip": vlan.get("IP", ""),
            "ssh": str(vlan.get("SSH", True)).lower(),
        }
        for vlan_name, vlan in router.get("VLANs", {}).items()
    ]
    if not vlans:
        vlans = [{"name": "VL1", "ports": "", "policies": "", "et": "true", "ip": "", "ssh": "true"}]
    return {
        "mac": mac,
        "name": router.get("Name", ""),
        "protocolos": "\n".join(router.get("Protocolos", [])),
        "estatus": router.get("estatus", "online"),
        "vlans": vlans,
    }


def validate_router_form(values):
    errors = []
    mac = values["mac"].upper()
    if not MAC_PATTERN.fullmatch(mac):
        errors.append(
            "La MAC debe tener seis grupos de dos letras o números separados por dos puntos."
        )
    if not NAME_PATTERN.fullmatch(values["name"]):
        errors.append(
            "El nombre debe tener de 1 a 50 caracteres: letras, números, espacios, punto, guion o guion bajo."
        )
    if values["estatus"] not in {"online", "offline"}:
        errors.append("Selecciona un estado válido.")
    if not values["vlans"]:
        errors.append("Agrega al menos una VLAN.")

    vlan_names = [vlan["name"].strip() for vlan in values["vlans"]]
    if any(not VLAN_PATTERN.fullmatch(vlan_name) for vlan_name in vlan_names):
        errors.append(
            "Cada VLAN debe iniciar con una letra y contener solo letras, números, guion o guion bajo (máximo 32 caracteres)."
        )
    if len({vlan_name.casefold() for vlan_name in vlan_names}) != len(vlan_names):
        errors.append("Los nombres de VLAN no se pueden repetir.")
    for index, vlan in enumerate(values["vlans"], start=1):
        if vlan["et"] not in {"true", "false"}:
            errors.append(f"Selecciona un valor válido para ET en la VLAN {index}.")
        if vlan["ssh"] not in {"true", "false"}:
            errors.append(f"Selecciona un valor válido para SSH en la VLAN {index}.")
        ip = vlan["ip"].strip()
        if ip and not IPV4_PATTERN.fullmatch(ip):
            errors.append(f"La IP de la VLAN {index} debe ser una IPv4 válida.")

    protocols = split_form_list(values["protocolos"])
    if any(not TOKEN_PATTERN.fullmatch(protocol) for protocol in protocols):
        errors.append(
            "Los protocolos solo pueden contener letras, números, guion o guion bajo, y deben iniciar con una letra."
        )
    for index, vlan in enumerate(values["vlans"], start=1):
        ports = split_form_list(vlan["ports"])
        if any(not PORT_PATTERN.fullmatch(port) for port in ports):
            errors.append(
                f"Los puertos de la VLAN {index} solo pueden contener letras, números, / o guion, y deben iniciar con una letra."
            )
        policies = split_form_list(vlan["policies"])
        if any(not TOKEN_PATTERN.fullmatch(policy) for policy in policies):
            errors.append(
                f"Las políticas de la VLAN {index} solo pueden contener letras, números, guion o guion bajo, y deben iniciar con una letra."
            )

    record = {
        "Name": values["name"],
        "Protocolos": split_form_list(values["protocolos"]),
        "estatus": values["estatus"],
        "VLANs": {
            vlan["name"].strip(): {
                "Ports": split_form_list(vlan["ports"]),
                "Policies": split_form_list(vlan["policies"]),
                "ET": vlan["et"] == "true",
                "IP": vlan["ip"].strip(),
                "SSH": vlan["ssh"] == "true",
            }
            for vlan in values["vlans"]
            if vlan["name"].strip()
        },
    }
    return mac, record, errors


def render_router_form(values, editing_mac=None, errors=None, status=200):
    return (
        render_template(
            "router_form.html",
            values=values,
            editing_mac=editing_mac,
            errors=errors or [],
            form_action=(
                url_for("router_edit", mac=editing_mac)
                if editing_mac is not None
                else url_for("router_new")
            ),
        ),
        status,
    )


datos_json = load_api_data()

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


@app.route('/routers')
def routers():
    return render_template("routers.html", routers=load_api_data().items())


@app.route("/routers/new", methods=["GET", "POST"])
def router_new():
    if request.method == "GET":
        return render_router_form(router_form_values())

    values = router_form_values(form=request.form)
    mac, record, errors = validate_router_form(values)
    status = 400
    if not errors:
        with API_JSON_LOCK:
            current_data = load_api_data()
            if any(existing_mac.casefold() == mac.casefold() for existing_mac in current_data):
                errors.append("Ya existe un router con esa MAC.")
            else:
                current_data[mac] = record
                try:
                    write_api_data(current_data)
                except OSError:
                    app.logger.exception("No se pudo guardar API.json")
                    errors.append("No se pudieron guardar los datos en API.json.")
                    status = 500
                else:
                    datos_json.clear()
                    datos_json.update(current_data)
                    return redirect(url_for("routers"))
    return render_router_form(values, errors=errors, status=status)


@app.route("/routers/<mac>/edit", methods=["GET", "POST"])
def router_edit(mac):
    with API_JSON_LOCK:
        current_data = load_api_data()
        if mac not in current_data:
            abort(404)

    if request.method == "GET":
        return render_router_form(
            router_form_values(current_data[mac], mac=mac),
            editing_mac=mac,
        )

    values = router_form_values(form=request.form)
    new_mac, record, errors = validate_router_form(values)
    status = 400
    if not errors:
        with API_JSON_LOCK:
            current_data = load_api_data()
            if mac not in current_data:
                abort(404)
            if new_mac != mac and any(
                existing_mac.casefold() == new_mac.casefold()
                for existing_mac in current_data
                if existing_mac.casefold() != mac.casefold()
            ):
                errors.append("Ya existe un router con esa MAC.")
            else:
                del current_data[mac]
                current_data[new_mac] = record
                try:
                    write_api_data(current_data)
                except OSError:
                    app.logger.exception("No se pudo guardar API.json")
                    errors.append("No se pudieron guardar los datos en API.json.")
                    status = 500
                else:
                    datos_json.clear()
                    datos_json.update(current_data)
                    return redirect(url_for("routers"))
    return render_router_form(
        values,
        editing_mac=mac,
        errors=errors,
        status=status,
    )


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