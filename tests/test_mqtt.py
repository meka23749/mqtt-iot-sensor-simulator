"""
MQTT Integration Tests
Tests MQTT publish/subscribe flows, QoS levels and topic structure
Author: Steve Meka
"""

import json
import time
import paho.mqtt.client as mqtt


BROKER = "localhost"
PORT = 1883
TIMEOUT = 5


class MQTTTestClient:
    def __init__(self):
        self.received_messages = []
        self.connected = False
        self.client = mqtt.Client(
            mqtt.CallbackAPIVersion.VERSION2,
            client_id="test-client"
        )
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message

    def _on_connect(self, client, userdata, flags, reason_code, properties=None):
        self.connected = (reason_code == 0)

    def _on_message(self, client, userdata, msg):
        self.received_messages.append({
            "topic": msg.topic,
            "payload": json.loads(msg.payload.decode()),
            "qos": msg.qos
        })

    def connect(self):
        self.client.connect(BROKER, PORT, keepalive=60)
        self.client.loop_start()
        time.sleep(1)
        return self.connected

    def subscribe(self, topic, qos=1):
        self.client.subscribe(topic, qos=qos)

    def publish(self, topic, payload, qos=1):
        self.client.publish(topic, json.dumps(payload), qos=qos)

    def disconnect(self):
        self.client.loop_stop()
        self.client.disconnect()


def test_mqtt_broker_connection():
    """Verify connection to MQTT broker"""
    client = MQTTTestClient()
    connected = client.connect()
    assert connected, "Failed to connect to MQTT broker"
    client.disconnect()


def test_mqtt_publish_subscribe_qos1():
    """Verify publish/subscribe flow with QoS 1"""
    client = MQTTTestClient()
    client.connect()
    client.subscribe("test/sensor-001/temperature", qos=1)
    time.sleep(0.5)

    payload = {
        "value": 22.5,
        "timestamp": "2026-01-01T00:00:00",
        "sensor_id": "sensor-001"
    }
    client.publish("test/sensor-001/temperature", payload, qos=1)
    time.sleep(1)

    assert len(client.received_messages) > 0
    msg = client.received_messages[0]
    assert msg["topic"] == "test/sensor-001/temperature"
    assert msg["payload"]["value"] == 22.5
    assert msg["qos"] == 1
    client.disconnect()


def test_mqtt_topic_structure():
    """Verify correct topic structure sensors/{id}/{measurement}"""
    client = MQTTTestClient()
    client.connect()
    client.subscribe("sensors/#", qos=1)
    time.sleep(0.5)

    measurements = {
        "sensors/sensor-001/temperature": {
            "value": 23.1,
            "timestamp": "2026-01-01T00:00:00",
            "sensor_id": "sensor-001"
        },
        "sensors/sensor-001/humidity": {
            "value": 55.0,
            "timestamp": "2026-01-01T00:00:00",
            "sensor_id": "sensor-001"
        },
        "sensors/sensor-001/pressure": {
            "value": 1013.2,
            "timestamp": "2026-01-01T00:00:00",
            "sensor_id": "sensor-001"
        },
    }

    for topic, payload in measurements.items():
        client.publish(topic, payload, qos=1)

    time.sleep(1)
    topics_received = [m["topic"] for m in client.received_messages]

    assert "sensors/sensor-001/temperature" in topics_received
    assert "sensors/sensor-001/humidity" in topics_received
    assert "sensors/sensor-001/pressure" in topics_received
    client.disconnect()


def test_mqtt_qos_levels():
    """Verify all QoS levels work correctly"""
    client = MQTTTestClient()
    client.connect()

    for qos in [0, 1, 2]:
        client.subscribe(f"test/qos{qos}", qos=qos)
        time.sleep(0.3)
        payload = {
            "value": qos,
            "timestamp": "2026-01-01T00:00:00",
            "sensor_id": f"qos-test-{qos}"
        }
        client.publish(f"test/qos{qos}", payload, qos=qos)

    time.sleep(1)
    assert len(client.received_messages) >= 3
    client.disconnect()


def test_mqtt_payload_structure():
    """Verify payload contains required fields"""
    client = MQTTTestClient()
    client.connect()
    client.subscribe("sensors/sensor-002/#", qos=1)
    time.sleep(0.5)

    payload = {
        "value": 21.5,
        "timestamp": "2026-06-13T10:00:00",
        "sensor_id": "sensor-002"
    }
    client.publish("sensors/sensor-002/temperature", payload, qos=1)
    time.sleep(1)

    assert len(client.received_messages) > 0
    msg = client.received_messages[0]["payload"]
    assert "value" in msg
    assert "timestamp" in msg
    assert "sensor_id" in msg
    client.disconnect()
