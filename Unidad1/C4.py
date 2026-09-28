network_config = {
    "0001": {
        "ip": "192.168.0.2",
        "device": "switch",
        "policy": "Deny all",
        "status": False,
        "lista": [1, 4, 6, 0, 8]
    },
    "0002": {
        "ip": "192.168.0.1",
        "device": "firewall",
        "policy": "avoid .2 .3 .4",
        "status": True,
    },
    "0003": {
        "ip": "192.168.0.254",
        "device": "router",
        "policy": "Allow outbound traffic",
        "status": True,
    },
    "0004": {
        "ip": "192.168.0.10",
        "device": "server",
        "policy": "Restrict SSH access",
        "status": True,
    },
    "0005": {
        "ip": "192.168.0.15",
        "device": "access_point",
        "policy": "Isolate wireless clients",
        "status": True,
    }
}

contenido = network_config.get("0001")
listaA = contenido.get("lista")
num = listaA[2]
#print(network_config.get("0001").get("lista")[2])
print(num)