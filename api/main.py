"""
FastAPI REST API for IIoT Sensor Data
Subscribes to MQTT and exposes sensor readings via REST
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

# ===== App =====
app = FastAPI(
    title="IIoT Sensor API",
    description="REST API for IIoT sensor data — Temperature, Humidity, Pressure via MQTT",
    version="1.0.0",
    contact={"name": "Steve Meka"}
)

# ===== In-memory store =====
sensor_store: Dict[str, dict] = {}

# ===== Models =====
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

# ===== MQTT Subscriber =====
MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT   = int(os.getenv("MQTT_PORT", 1883))

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
                    "measurements": {}
                }

            if measurement == "full":
                sensor_store[sensor_id].update(payload)
                sensor_store[sensor_id]["last_seen"] = payload.get("timestamp")
                sensor_store[sensor_id]["status"] = payload.get("status", "online")
            else:
                sensor_store[sensor_id]["measurements"][measurement] = payload.get("value")
                sensor_store[sensor_id]["last_seen"] = payload.get("timestamp")

    except Exception as e:
        print(f"MQTT message error: {e}")

def start_mqtt():
    client = mqtt.Client(client_id="sensor-api-subscriber")
    client.on_message = on_message
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
        client.subscribe("sensors/#", qos=1)
        client.loop_forever()
    except Exception as e:
        print(f"MQTT connection error: {e}")

# Start MQTT subscriber in background thread
mqtt_thread = threading.Thread(target=start_mqtt, daemon=True)
mqtt_thread.start()

# ===== Endpoints =====
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

@app.get("/sensors/{sensor_id}", response_model=SensorReading, tags=["Sensors"])
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

@app.get("/sensors/{sensor_id}/measurements", tags=["Sensors"])
def get_measurements(sensor_id: str):
    """Get latest individual measurements for a sensor"""
    if sensor_id not in sensor_store:
        raise HTTPException(status_code=404, detail=f"Sensor '{sensor_id}' not found")
    return {
        "sensor_id": sensor_id,
        "measurements": sensor_store[sensor_id].get("measurements", {})
    }
