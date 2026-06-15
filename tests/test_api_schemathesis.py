"""
Automated API Tests using Schemathesis
Tests REST API against OpenAPI 3.x specification
Author: Steve Meka
"""

import schemathesis
import requests


schema = schemathesis.from_uri("http://localhost:8000/openapi.json")

BASE_URL = "http://localhost:8000"


@schema.parametrize()
def test_api_fuzzing(case):
    """
    Automatically generates and runs test cases from OpenAPI spec.
    Tests all endpoints with valid and invalid inputs.
    """
    response = case.call()
    case.validate_response(response)


def test_health_endpoint():
    """Health endpoint returns 200 and correct structure"""
    response = requests.get(f"{BASE_URL}/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "timestamp" in data
    assert "sensors_online" in data


def test_sensors_list():
    """Sensors list endpoint returns 200 and a list"""
    response = requests.get(f"{BASE_URL}/sensors")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_sensor_not_found():
    """Unknown sensor returns 404"""
    response = requests.get(f"{BASE_URL}/sensors/unknown-sensor-999")
    assert response.status_code == 404
    data = response.json()
    assert "detail" in data


def test_sensor_measurements_not_found():
    """Unknown sensor measurements returns 404"""
    response = requests.get(f"{BASE_URL}/sensors/unknown-sensor-999/measurements")
    assert response.status_code == 404


def test_health_response_schema():
    """Health response matches expected schema"""
    response = requests.get(f"{BASE_URL}/health")
    data = response.json()
    assert isinstance(data["status"], str)
    assert isinstance(data["sensors_online"], int)
    assert isinstance(data["timestamp"], str)
