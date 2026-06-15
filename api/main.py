"""
FastAPI REST API for IIoT Sensor Data
Author: Steve Meka
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime
import json
import threading
import paho.mqtt.client as mqtt
import os
import logging


logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


app = FastAPI(
    title="IIoT Sensor API",
    description="REST API for IIoT sensor data - Temperature, Humidity, Pressure via MQTT",
    version="1.0.0",
    contact={"name": "Steve Meka"}
)

sensor_store: Dict[str, dict] = {}


class SensorReading(BaseModel):
    sensor_id: str
    timestamp: str
    temperature: float
    humidity: float
    pressure: float
    status: str


class SensorInfo(BaseModel):
    sensor_id: str
    last_seen: Optional[str] = None
    status: str = "unknown"


class HealthResponse(BaseModel):
    status: str
    timestamp: str
    sensors_online: int


MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))


def on_connect(client, userdata, flags, reason_code, properties=None):
    if reason_code == 0:
        logger.info("Connected to MQTT Broker successfully")
        client.subscribe("sensors/#", qos=1)
        logger.info("Subscribed to sensors/#")
    else:
        logger.error(f"MQTT connection failed: {reason_code}")


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
        topic_parts = msg.topic.split("/")
        if len(topic_parts) >= 3:
            sensor_id = topic_parts[1]
            measurement = topic_parts[2]
            if sensor_id not in sensor_store:
                sensor_store[sensor_id] = {
                    "sensor_id": sensor_id,
                    "last_seen": None,
                    "status": "unknown",
                    "measurements": {},
                    "temperature": 0.0,
                    "humidity": 0.0,
                    "pressure": 0.0
                }
            if measurement == "full":
                sensor_store[sensor_id].update(payload)
                sensor_store[sensor_id]["last_seen"] = payload.get("timestamp")
                sensor_store[sensor_id]["status"] = payload.get("status", "online")
            elif measurement in ["temperature", "humidity", "pressure"]:
                sensor_store[sensor_id][measurement] = payload.get("value", 0.0)
                sensor_store[sensor_id]["measurements"][measurement] = payload.get("value")
                sensor_store[sensor_id]["last_seen"] = payload.get("timestamp")
                sensor_store[sensor_id]["status"] = "online"
            logger.info(f"Received: {msg.topic} = {payload.get('value')}")
    except Exception as e:
        logger.error(f"MQTT message error: {e}")


def start_mqtt():
    logger.info("MQTT thread starting...")
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id="sensor-api-subscriber")
    client.on_connect = on_connect
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        logger.info(f"MQTT connecting to {MQTT_BROKER}:{MQTT_PORT}")
        client.loop_forever()
    except Exception as e:
        logger.error(f"MQTT connection error: {e}")


mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()


@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health():
    """Health check endpoint"""
    online = sum(1 for s in sensor_store.values() if s.get("status") == "online")
    return HealthResponse(
        status="ok",
        timestamp=datetime.utcnow().isoformat(),
        sensors_online=online
    )


@app.get("/sensors", response_model=List[SensorInfo], tags=["Sensors"])
def list_sensors():
    """List all known sensors"""
    return [
        SensorInfo(
            sensor_id=s["sensor_id"],
            last_seen=s.get("last_seen"),
            status=s.get("status", "unknown")
        )
        for s in sensor_store.values()
    ]


@app.get(
    "/sensors/{sensor_id}",
    response_model=SensorReading,
    tags=["Sensors"],
    responses={404: {"description": "Sensor not found"}}
)
def get_sensor(sensor_id: str):
    """Get full reading for a specific sensor"""
    if sensor_id not in sensor_store:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")
    s = sensor_store[sensor_id]
    return SensorReading(
        sensor_id=s["sensor_id"],
        timestamp=s.get("last_seen", ""),
        temperature=s.get("temperature", 0.0),
        humidity=s.get("humidity", 0.0),
        pressure=s.get("pressure", 0.0),
        status=s.get("status", "unknown")
    )


@app.get(
    "/sensors/{sensor_id}/measurements",
    tags=["Sensors"],
    responses={404: {"description": "Sensor not found"}}
)
def get_measurements(sensor_id: str):
    """Get latest individual measurements for a sensor"""
    if sensor_id not in sensor_store:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")
    return {
        "sensor_id": sensor_id,
        "measurements": sensor_store[sensor_id].get("measurements", {})
    }
