#!/usr/bin/python

import os
import signal
import sys

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
    mqttc.loop_stop()

    # some grossness to ensure publishes go through. can't use
    # wait_for_publish() while loop_forever() is still going.
    mqttc.loop_start()
    fireplace_off().wait_for_publish()
    print("setting status to 'OFFLINE'")
    set_status("OFFLINE").wait_for_publish()
    mqttc.loop_stop()

    mqttc.disconnect()

    sys.exit(0)

def set_status(status):
    return mqttc.publish(topic=TOPIC__STATUS, payload=status, qos=2, retain=True)

def mqtt_on_connect(client, userdata, flags, rc):
    print("connected with result code "+str(rc))
    print("setting status to 'ONLINE'")
    set_status("ONLINE")
    print("subscribing to 'rpi/fireplace/power' topic")
    client.subscribe(TOPIC__POWER)

def power_topic(client, userdata, msg):
    payload = msg.payload.decode()
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
    return mqttc.publish(topic=TOPIC__STATE, payload="ON", qos=2, retain=True)

def fireplace_off():
    print("turning off fireplace")
    fireplace.off()
    print("publishing 'OFF' state")
    return mqttc.publish(topic=TOPIC__STATE, payload="OFF", qos=2, retain=True)

def main_loop():
    # setup signal catching
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    mqttc.username_pw_set(username=MQTT__USERNAME,password=MQTT__PASSWORD)
    mqttc.connect(MQTT__HOST, MQTT__PORT, 60)
    mqttc.on_connect = mqtt_on_connect
    mqttc.message_callback_add(TOPIC__POWER, power_topic)

    fireplace_off()

    mqttc.loop_forever()

if __name__ == "__main__":
    main_loop()
