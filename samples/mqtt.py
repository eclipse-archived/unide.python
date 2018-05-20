import paho.mqtt.client as mqtt
import unide
from unide.common import Device


def simple_measurement(client, topic):
    # First we create a `Device`, identified by a "deviceID".
    device = Device(deviceID="Device-001")

    # Second, we create the most simple PPMP measurement payload, with
    # just one dimension 'temperature'. The timestamp is automatically
    # set to the current time.
    payload = device.measurement(temperature=45.6)

    # Lastly, we send the payload using MQTT.
    client.publish(topic, payload)


def simple_message(client, topic):
    # First we create a `Device`, identified by a "deviceID".
    device = Device(deviceID="Device-001")

    # Second, we create a simple PPMP message payload.
    payload = device.message("ERR621", description="Error condition 621!")

    # Lastly, we send the payload using MQTT.
    client.publish(topic, payload)


if __name__ == "__main__":
    # Setup a connection to a local MQTT broker.
    client = mqtt.Client()
    client.connect("test.mosquitto.org", 1883, 60)
    topic = "sample"

    # Send off a measurement.
    simple_measurement(client, topic)

    # Send off a message.
    simple_message(client, topic)
