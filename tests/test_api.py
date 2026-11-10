import os
from fastapi.testclient import TestClient
from api.app import app

API_KEY_TEST = "test-clave-secreta-123"


def test_chat_sin_clave_responde_401():
    os.environ["API_KEY"] = API_KEY_TEST
    with TestClient(app) as client:
        response = client.post("/chat", json={"user_id": "u1", "texto": "hola"})
        assert response.status_code == 401
        data = response.json()
        assert "detail" in data


def test_chat_con_clave_responde_200():
    os.environ["API_KEY"] = API_KEY_TEST
    with TestClient(app) as client:
        response = client.post(
            "/chat",
            json={"user_id": "u1", "texto": "¿tienen la polera azul en talla M?"},
            headers={"X-API-Key": API_KEY_TEST},
        )
        assert response.status_code == 200
        data = response.json()
        assert "ruta" in data
        assert "motivo" in data
        assert "respuesta" in data
