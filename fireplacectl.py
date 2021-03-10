#!/usr/bin/python

# A simple Python application for controlling a relay board from a Raspberry Pi
# The application uses the GPIO Zero library (https://gpiozero.readthedocs.io/en/stable/)
# The relay is connected to one of the Pi's GPIO ports, then is defined as an Output device
# in GPIO Zero: https://gpiozero.readthedocs.io/en/stable/api_output.html#outputdevice

import signal
import sys
import os
from time import sleep

import gpiozero
import paho.mqtt.client as mqtt

RELAY_PIN = 17

TOPIC__ROOT = "rpi/fireplace"
TOPIC__POWER = TOPIC__ROOT + "/power"
TOPIC__STATE = TOPIC__ROOT + "/state"
TOPIC__STATUS = TOPIC__ROOT + "/status"

MQTT__HOST = os.getenv("MQTT_HOST", "mosquitto.data")
MQTT__PORT = os.getenv("MQTT_PORT", 1883)
MQTT__USERNAME = os.environ.get("MQTT_USERNAME")
MQTT__PASSWORD = os.environ.get("MQTT_PASSWORD")

fireplace = gpiozero.OutputDevice(RELAY_PIN, active_high=True, initial_value=False)

mqttc = mqtt.Client()

def signal_handler(signal, frame):
    print("\nshutting down\n")
    fireplace_off()
    fireplace.close()
    sleep(5)
    mqttc.disconnect()
    sys.exit(0)

def mqtt_on_connect(client, userdata, flags, rc):
    print("connected with result code "+str(rc))
    print("subscribing to 'rpi/fireplace/power' topic")
    client.publish(topic=TOPIC__STATUS, payload="ON", qos=2, retain=True)
    client.subscribe("rpi/fireplace/power")

def mqtt_on_disconnect(client, userdata, rc):
    print("disconnected")

def mqtt_on_publish(client, userdata, result):
    print("data published")

# convert to message_callback_add()
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

    mqttc.username_pw_set(username=MQTT__USERNAME,password=MQTT__PASSWORD)
    mqttc.connect(MQTT__HOST, MQTT__PORT, 60)
    mqttc.on_connect = mqtt_on_connect
    mqttc.on_disconnect = mqtt_on_disconnect
    mqttc.on_message = mqtt_on_message
    mqttc.on_publish = mqtt_on_publish

    fireplace_off()

    mqttc.loop_forever()

if __name__ == "__main__":
    main_loop()
