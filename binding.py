import sys
import time
import pygame
import serial
import serial.tools.list_ports
from pyvesc.VESC.VESC import VESC
from pyvesc.VESC.messages.setters import SetDutyCycle, SetServoPosition

# --------- Auto-detect VESC port ---------
def find_vesc_port():
    for port in serial.tools.list_ports.comports():
        if "0483:5740" in port.hwid or "STM32" in port.description:
            return port.device
    return None

vesc_port = find_vesc_port()
if not vesc_port:
    print("[ERROR] No VESC detected. Make sure it's connected via USB.")
    sys.exit(1)

print(f"[INFO] VESC detected on port: {vesc_port}")

# --------- Connect to VESC ---------
try:
    vesc = VESC(vesc_port)
    vesc.set_duty_cycle(0.0)
    print("VESC communication established.")
except Exception as e:
    print(f"[ERROR] Could not connect to VESC: {e}")
    sys.exit(1)

# --------- gamepad ---------
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("No gamepad detected.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Gamepad detected: {joystick.get_name()}")

# --------- Control ---------
def send_speed(rt, lt):
    acc = (rt + 1) / 2
    dec = (lt + 1) / 2
    duty = acc - dec

    # Limit duty cycle (30%)
    duty = max(min(duty, 0.3), -0.3)

    try:
        vesc.set_duty_cycle(duty)
        print(f"[VESC] Duty cycle = {duty:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to send duty cycle: {e}")

def set_direction(val):
    pos = (val + 1) / 2
    try:
        vesc.set_servo(pos)
        print(f"[SERVO] Position = {pos:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to send servo position: {e}")

# --------- Main loop ---------
try:
    rt_val = 0.0
    lt_val = 0.0
    while True:
        pygame.event.pump()
        for event in pygame.event.get():
            if event.type == pygame.JOYAXISMOTION:
                print(f"Axis {event.axis} = {event.value:.2f}")
                if event.axis == 0:
                    set_direction(event.value)
                elif event.axis == 2:
                    lt_val = event.value
                elif event.axis == 5:
                    rt_val = event.value
                    send_speed(rt_val, lt_val)
        time.sleep(0.01)
except KeyboardInterrupt:
    print("Exiting on user interrupt.")
finally:
    vesc.set_duty_cycle(0)
    print("Motor stopped.")
