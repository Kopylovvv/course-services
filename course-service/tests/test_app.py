from importlib import import_module

import pytest
from fastapi.testclient import TestClient


@pytest.mark.parametrize(
    "url_path,status,response_json",
    (
            ("/", 404, {"detail": "Not Found"}),
            ("/service", 200, {"healthy": True}),
    ),
)
def test_get(app_client, url_path, status, response_json):
    response = app_client.get(url_path)

    assert response.status_code == status
    assert response.json() == response_json


def test_get_openapi(app_client):
    response = app_client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json().get("openapi") == "3.1.0"


def test_get_swagger(app_client):
    response = app_client.get("/docs")

    assert response.status_code == 200
    assert "<!DOCTYPE html>" in response.text


def test_main_startup():
    main = import_module("src.main")

    with TestClient(main.app) as client:
        response = client.get("/service/")

    assert response.status_code == 200
    assert response.json() == {"healthy": True}
