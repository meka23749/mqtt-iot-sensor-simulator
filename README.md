# MQTT IoT Sensor Simulator

IIoT sensor simulator that publishes real-time temperature, humidity and pressure data
via MQTT protocol, with a FastAPI REST interface and automated API testing using Schemathesis.

## Architecture

Sensor Simulator (Python)

|

| MQTT Publish (QoS 1)

v

MQTT Broker (Mosquitto)

|

| Subscribe

v

FastAPI REST API

|

| OpenAPI 3.x

v

Schemathesis Tests → GitHub Actions CI

## Features
- MQTT sensor simulation (Temperature, Humidity, Pressure)
- QoS levels (0, 1, 2) support
- Topic structure: sensors/{sensor_id}/{measurement}
- FastAPI REST API with automatic OpenAPI 3.x documentation
- Automated API fuzzing with Schemathesis
- GitHub Actions CI/CD pipeline
- Docker Compose for local development

## Quick Start
pip install -r requirements.txt
docker-compose up -d
python simulator/sensor_publisher.py
uvicorn api.main:app --reload

## API Endpoints
| Method | Endpoint                    | Description              |
|--------|-----------------------------|--------------------------|
| GET    | /sensors                    | List all sensors         |
| GET    | /sensors/{id}               | Get sensor by ID         |
| GET    | /sensors/{id}/measurements  | Get latest measurements  |
| GET    | /health                     | Health check             |
| GET    | /docs                       | OpenAPI documentation    |

## MQTT Topics
| Topic                          | QoS | Description           |
|--------------------------------|-----|-----------------------|
| sensors/{id}/temperature       | 1   | Temperature in Celsius|
| sensors/{id}/humidity          | 1   | Humidity in %         |
| sensors/{id}/pressure          | 1   | Pressure in hPa       |
| sensors/{id}/status            | 0   | Sensor online/offline |

## Tools
- Python 3.11
- FastAPI + Uvicorn
- Paho-MQTT
- Eclipse Mosquitto (MQTT Broker)
- Schemathesis (API fuzzing)
- Docker + Docker Compose
- GitHub Actions

## Author
Steve Meka
