import serial
from pyvesc.protocol.interface import encode, decode
from pyvesc.messages import SetRPM, GetValues

# Connexion au port série (modifie /dev/ttyUSB0 si besoin)
vesc = serial.Serial('/dev/ttyUSB0', baudrate=115200, timeout=0.1)

# Envoie d'une commande de vitesse
vesc.write(encode(SetRPM(3000)))

# Envoie d'une requête de lecture
vesc.write(encode(GetValues()))

# Lecture et décodage
buffer = b""
while True:
    byte = vesc.read()
    if not byte:
        break
    buffer += byte
    try:
        obj, consumed = decode(buffer)
        if obj:
            print("RPM:", obj.rpm)
            print("Tension:", obj.v_in)
            break
    except Exception:
        pass
