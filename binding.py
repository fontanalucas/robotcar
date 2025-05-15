import sys
import time
import pygame
from pyvesc.VESC import VESC
from pyvesc.VESC.messages import SetDutyCycle, SetServoPosition, GetValues

def test_vesc_alive():
    try:
        vesc.write(GetValues())
        response = vesc.read(GetValues)
        return response is not None
    except Exception:
        return False

# Connexion au VESC
try:
    vesc = VESC(serial_port="/dev/ttyACM0")
    time.sleep(1)
    if not test_vesc_alive():
        print("[ERREUR] Le VESC ne répond pas.")
        sys.exit(1)
except Exception as e:
    print(f"[ERREUR] Impossible de se connecter au VESC : {e}")
    sys.exit(1)

# Initialisation de la manette
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("Aucune manette détectée.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Manette détectée : {joystick.get_name()}")

def send_speed(rt, lt):
    acc = (rt + 1) / 2
    dec = (lt + 1) / 2
    duty = acc - dec
    try:
        if test_vesc_alive():
            vesc.set(SetDutyCycle(duty))
            print(f"[VESC] Duty = {duty:.2f}")
        else:
            print("[VESC] Ignoré : pas de réponse")
    except Exception as e:
        print(f"[ERREUR] Duty : {e}")

def set_direction(val):
    pos = (val + 1) / 2
    try:
        if test_vesc_alive():
            vesc.set(SetServoPosition(pos))
            print(f"[SERVO] pos = {pos:.2f}")
        else:
            print("[SERVO] Ignoré : pas de réponse")
    except Exception as e:
        print(f"[ERREUR] Servo : {e}")

try:
    rt_val = 0.0
    lt_val = 0.0
    while True:
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                if event.axis == 0:
                    set_direction(event.value)
                elif event.axis == 2:
                    lt_val = event.value
                elif event.axis == 5:
                    rt_val = event.value
                    send_speed(rt_val, lt_val)
        time.sleep(0.01)
except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
