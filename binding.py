import sys
import time
import pygame
from pyvesc.VESC import VESC
from pyvesc.VESC.messages import SetDutyCycle
import Jetson.GPIO as GPIO

SERVO_PIN = 33
PWM_FREQ = 50
GPIO.setmode(GPIO.BOARD)
GPIO.setup(SERVO_PIN, GPIO.OUT)
pwm_servo = GPIO.PWM(SERVO_PIN, PWM_FREQ)
pwm_servo.start(7.5)
try:
    vesc = VESC(serial_port="/dev/ttyACM0")
except Exception as e:
    print(f"[ERREUR] Impossible de se connecter au VESC : {e}")
    exit()
pygame.init()
pygame.joystick.init()
if pygame.joystick.get_count() == 0:
    print("Aucune manette détectée.")
    exit()
joystick = pygame.joystick.Joystick(0)
joystick.init()
print(f"Manette détectée : {joystick.get_name()}")
def send_speed(rt, lt):
    """RT accélère, LT freine/recul. Les deux vont de -1 à 1"""
    acc = (rt + 1) / 2
    dec = (lt + 1) / 2
    duty = acc - dec
    vesc.set(SetDutyCycle(duty))
    print(f"[VESC] Duty = {duty:.2f}")
def set_direction(val):
    """val entre -1 et 1, converti en angle servo entre 5 et 10%"""
    pos = (val + 1) / 2
    duty = 5 + pos * 5
    pwm_servo.ChangeDutyCycle(duty)
    print(f"[SERVO] Angle virtuel : {int((pos - 0.5) * 360)}°, PWM: {duty:.2f}%")
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
except KeyboardInterrupt:
    print("\nArrêt demandé par l'utilisateur.")
finally:
    pwm_servo.stop()
    GPIO.cleanup()