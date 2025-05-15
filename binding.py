import sys
import time
import pygame
import serial

# Force Python to use the local pyvesc directory
sys.path.insert(0, "./pyvesc")

# Import from local version
from VESC.VESC import VESC
from VESC.messages.setters import SetDutyCycle, SetServoPosition

# Connect to VESC
try:
    ser = serial.Serial("/dev/ttyACM0", baudrate=115200, timeout=0.1)
    vesc = VESC(ser)
    vesc.set(SetDutyCycle(0.05))
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
        vesc.set(SetDutyCycle(duty))
        print(f"[VESC] Duty cycle = {duty:.2f}")
    except Exception as e:
        print(f"[ERROR] Failed to send duty cycle: {e}")

# Servo direction control
def set_direction(val):
    pos = (val + 1) / 2
    try:
        vesc.set(SetServoPosition(pos))
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
