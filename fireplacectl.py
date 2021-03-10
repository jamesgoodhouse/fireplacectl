#!/usr/bin/python

# A simple Python application for controlling a relay board from a Raspberry Pi
# The application uses the GPIO Zero library (https://gpiozero.readthedocs.io/en/stable/)
# The relay is connected to one of the Pi's GPIO ports, then is defined as an Output device
# in GPIO Zero: https://gpiozero.readthedocs.io/en/stable/api_output.html#outputdevice

import signal
from sys import exit
from os import environ

import gpiozero
import paho.mqtt.client as mqtt

RELAY_PIN = 17

TOPIC__ROOT = "rpi/fireplace"
TOPIC__POWER = TOPIC__ROOT + "/power"
TOPIC__STATE = TOPIC__ROOT + "/state"
TOPIC__STATUS = TOPIC__ROOT + "/status"

def get_env_var_or_default(var, default):
    val = environ.get(var)
    if val is not None:
        return val

    return default

def get_env_var_or_error(var):
    val = environ.get(var)
    if val is not None:
        return val

    print("'" + var + "' not set")
    exit(1)

MQTT__HOST = get_env_var_or_default("MQTT_HOST", "mosquitto.data")
MQTT__PORT = get_env_var_or_default("MQTT_PORT", 1883)
MQTT__USERNAME = get_env_var_or_error("MQTT_USERNAME")
MQTT__PASSWORD = get_env_var_or_error("MQTT_PASSWORD")

fireplace = gpiozero.OutputDevice(RELAY_PIN, active_high=True, initial_value=False)

def signal_handler(signal, frame):
    print("\nshutting down\n")
    fireplace_off()
    fireplace.close()
    mqttc.disconnect()
    exit(0)

mqttc = mqtt.Client()

def mqtt_on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    print("subscribing to 'rpi/fireplace/power' topic")
    client.subscribe("rpi/fireplace/power")

def mqtt_on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))

    if msg.topic == TOPIC__POWER:
        payload = msg.payload.decode("utf-8")
        if payload == "ON":
            print("received 'ON' command")
            fireplace_on()
        elif payload == "OFF":
            print("received 'OFF' command")
            fireplace_off()
        else:
            print("ignoring unknown payload '"+payload+"'")

def fireplace_on():
    print("turning on fireplace")
    fireplace.on()
    print("publishing 'ON' state")
    mqttc.publish(topic=TOPIC__STATE, payload="ON", qos=2, retain=True)

def fireplace_off():
    print("turning off fireplace")
    fireplace.off()
    print("publishing 'OFF' state")
    mqttc.publish(topic=TOPIC__STATE, payload="OFF", qos=2, retain=True)

def main_loop():
    # setup signal catching
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    fireplace_off()

    mqttc.username_pw_set(username=MQTT__USERNAME,password=MQTT__PASSWORD)
    mqttc.connect(MQTT__HOST, MQTT__PORT, 60)
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_message = mqtt_on_message
    mqttc.loop_forever()

if __name__ == "__main__":
    main_loop()
