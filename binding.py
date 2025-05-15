import sys
import time
import pygame
import serial.tools.list_ports
from pyvesc.VESC.VESC import VESC
from pyvesc.VESC.messages.setters import SetDutyCycle, SetServoPosition

# Lister les ports série disponibles
print("Ports série disponibles :")
ports = serial.tools.list_ports.comports()
for port in ports:
    print(port.device)

# Connect to VESC
try:
    vesc = VESC("/dev/ttyACM0")
    vesc.set_duty_cycle(0.05)  # Utiliser set_duty_cycle directement
    print("VESC communication established.")
except Exception as e:
    print(f"[ERROR] Could not connect to VESC: {e}")
    sys.exit(1)

# Initialize gamepad
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("No gamepad detected.")
    sys.exit(1)

joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Gamepad detected: {joystick.get_name()}")

# Motor speed control
def send_speed(rt, lt):
    acc = (rt + 1) / 2
    dec = (lt + 1) / 2
    duty = acc - dec
    try:
        vesc.set_duty_cycle(duty)  # Utiliser set_duty_cycle
        print(f"[VESC] Duty cycle = {duty:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to send duty cycle: {e}")

# Servo direction control
def set_direction(val):
    pos = (val + 1) / 2
    try:
        vesc.set_servo(pos)  # Utiliser set_servo
        print(f"[SERVO] Position = {pos:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to send servo position: {e}")

# Main control loop
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
    print("Exiting on user interrupt.")
finally:
    # Arrêter le moteur à la sortie
    vesc.set_duty_cycle(0)  # Utiliser set_duty_cycle
    print("Motor stopped.")