"""
IIoT Sensor Simulator
Publishes temperature, humidity and pressure data via MQTT
Author: Steve Meka
"""

import json
import time
import random
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
import paho.mqtt.client as mqtt


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class SensorReading:
    sensor_id: str
    timestamp: str
    temperature: float
    humidity: float
    pressure: float
    status: str


def generate_reading(sensor_id: str) -> SensorReading:
    """Generate realistic sensor data with slight variations"""
    return SensorReading(
        sensor_id=sensor_id,
        timestamp=datetime.utcnow().isoformat(),
        temperature=round(random.uniform(18.0, 35.0), 2),
        humidity=round(random.uniform(30.0, 80.0), 2),
        pressure=round(random.uniform(990.0, 1030.0), 2),
        status="online"
    )


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        logger.info("Connected to MQTT Broker")
    else:
        logger.error(f"Connection failed with code {rc}")


def on_publish(client, userdata, mid):
    logger.debug(f"Message {mid} published")


class SensorPublisher:
    def __init__(
        self,
        broker: str = "localhost",
        port: int = 1883,
        sensors: list = None,
        interval: float = 5.0,
        qos: int = 1
    ):
        self.broker = broker
        self.port = port
        self.sensors = sensors or ["sensor-001", "sensor-002", "sensor-003"]
        self.interval = interval
        self.qos = qos

        self.client = mqtt.Client(client_id="sensor-simulator")
        self.client.on_connect = on_connect
        self.client.on_publish = on_publish

    def connect(self):
        self.client.connect(self.broker, self.port, keepalive=60)
        self.client.loop_start()

    def publish_reading(self, reading: SensorReading):
        base_topic = f"sensors/{reading.sensor_id}"

        topics = {
            f"{base_topic}/temperature": reading.temperature,
            f"{base_topic}/humidity": reading.humidity,
            f"{base_topic}/pressure": reading.pressure,
            f"{base_topic}/status": reading.status,
        }

        for topic, value in topics.items():
            payload = json.dumps({
                "value": value,
                "timestamp": reading.timestamp,
                "sensor_id": reading.sensor_id
            })
            self.client.publish(topic, payload, qos=self.qos)
            logger.info(f"Published -> {topic} | value={value} | QoS={self.qos}")

        self.client.publish(
            f"{base_topic}/full",
            json.dumps(asdict(reading)),
            qos=self.qos
        )

    def run(self):
        self.connect()
        logger.info(
            f"Simulating {len(self.sensors)} sensors"
            f" | interval={self.interval}s | QoS={self.qos}"
        )

        try:
            while True:
                for sensor_id in self.sensors:
                    reading = generate_reading(sensor_id)
                    self.publish_reading(reading)
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Simulator stopped")
            self.client.loop_stop()
            self.client.disconnect()


if __name__ == "__main__":
    publisher = SensorPublisher(
        broker="localhost",
        port=1883,
        sensors=["sensor-001", "sensor-002", "sensor-003"],
        interval=5.0,
        qos=1
    )
    publisher.run()
