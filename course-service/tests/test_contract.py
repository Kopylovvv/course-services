"""Проверки контракта, примеров и граничных значений лабораторной № 2."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
import yaml
from fastapi.testclient import TestClient
from openapi_schema_validator import OAS30ReadValidator, OAS30WriteValidator
from openapi_spec_validator import validate

ROOT = Path(__file__).resolve().parents[1]
SPEC = yaml.safe_load((ROOT / "openapi.yaml").read_text(encoding="utf-8"))


def expand(value: Any) -> Any:
    """Разрешить локальные ссылки для проверки отдельных схем."""
    if isinstance(value, list):
        return [expand(item) for item in value]
    if isinstance(value, dict):
        if "$ref" in value:
            target: Any = SPEC
            assert value["$ref"].startswith("#/")
            for part in value["$ref"][2:].split("/"):
                target = target[part.replace("~1", "/").replace("~0", "~")]
            return expand(target)
        return {key: expand(item) for key, item in value.items()}
    return value


def validator(name: str) -> OAS30WriteValidator:
    """Получить валидатор входной схемы с проверкой форматов."""
    return OAS30WriteValidator(
        expand(SPEC["components"]["schemas"][name]),
        format_checker=OAS30WriteValidator.FORMAT_CHECKER,
    )


def test_openapi_and_all_examples() -> None:
    """Спецификация и каждый пример запроса/ответа соответствуют схемам."""
    validate(SPEC)
    count = 0
    for path in SPEC["paths"].values():
        for operation in path.values():
            request_body = operation.get("requestBody", {})
            payloads = [(request_body, OAS30WriteValidator)]
            payloads += [
                (expand(response), OAS30ReadValidator)
                for response in operation["responses"].values()
            ]
            for payload, validator_class in payloads:
                for media in payload.get("content", {}).values():
                    check = validator_class(
                        expand(media["schema"]),
                        format_checker=validator_class.FORMAT_CHECKER,
                    )
                    if "example" in media:
                        check.validate(media["example"])
                        count += 1
                    for example in media.get("examples", {}).values():
                        check.validate(example["value"])
                        count += 1
    assert count > 100


def test_auth_idempotency_and_path_parameters() -> None:
    """Все операции защищены, POST имеет ключ, шаблоны имеют UUID-параметры."""
    operation_ids = []
    assert SPEC["security"] == [{"bearerAuth": []}]
    for path, methods in SPEC["paths"].items():
        for method, operation in methods.items():
            operation_ids.append(operation["operationId"])
            assert operation.get("security", SPEC["security"])
            assert {"401", "403", "422", "500"} <= operation["responses"].keys()
            parameters = [expand(item) for item in operation.get("parameters", [])]
            if method == "post":
                assert any(
                    p["name"] == "Idempotency-Key"
                    and p["in"] == "header"
                    and p["required"]
                    for p in parameters
                )
            for parameter in parameters:
                if parameter["in"] == "path":
                    assert "{" + parameter["name"] + "}" in path
                    assert parameter["required"]
                    assert parameter["schema"]["format"] == "uuid"
            if "204" in operation["responses"]:
                assert "content" not in operation["responses"]["204"]
    assert len(operation_ids) == len(set(operation_ids)) == 19


@pytest.mark.parametrize(
    "name,payload",
    [
        ("CoursePatch", {}),
        ("AssignmentPatch", {}),
        ("ReviewPatch", {}),
        ("CoursePatch", {"title": None}),
        ("AssignmentPatch", {"date_end": None}),
        ("ReviewPatch", {"mark": None}),
        ("AssignmentPatch", {"attempts_limit": 2}),
        ("AssignmentPatch", {"attempts_limit": 11}),
        ("AssignmentPatch", {"attempts_limit": 3.5}),
        ("ReviewCreate", {"feedback": "Хорошо", "mark": -0.1, "status": "PASSED"}),
        ("ReviewCreate", {"feedback": "Хорошо", "mark": 10.1, "status": "PASSED"}),
        ("ReviewCreate", {"feedback": "Хорошо", "mark": 8, "status": "COMPLETED"}),
        (
            "SubmissionCreate",
            {
                "assignment_id": "not-a-uuid",
                "repository_url": "https://example.org/repo",
            },
        ),
        (
            "SubmissionCreate",
            {
                "assignment_id": "a64f6a42-a0dc-41e3-a7e1-e6fa1cd29605",
                "repository_url": "file:///tmp/repo",
            },
        ),
    ],
)
def test_invalid_payloads(name: str, payload: dict[str, Any]) -> None:
    """Отклонить пустые PATCH, null, неправильные типы, UUID и границы."""
    assert list(validator(name).iter_errors(payload))


@pytest.mark.parametrize(
    "name,payload",
    [
        ("CoursePatch", {"status": "ACTIVE"}),
        ("AssignmentPatch", {"materials_url": None}),
        ("AssignmentPatch", {"attempts_limit": 3}),
        ("AssignmentPatch", {"attempts_limit": 10}),
        ("ReviewCreate", {"feedback": "Проверено", "mark": 0, "status": "FAILED"}),
        ("ReviewCreate", {"feedback": "Проверено", "mark": 10, "status": "PASSED"}),
        ("ReviewCreate", {"feedback": "Проверено", "mark": 8.5, "status": "PASSED"}),
    ],
)
def test_valid_boundaries(name: str, payload: dict[str, Any]) -> None:
    """Принять границы диапазонов, дробную оценку и удаление ссылки."""
    validator(name).validate(payload)


def test_client_cannot_spoof_author_or_server_fields() -> None:
    """Клиент не задаёт чужого автора или серверные поля."""
    for name, extra in [
        ("SubmissionCreate", {"student_id": "b767702f-e433-43f5-b201-b74185993059"}),
        ("SubmissionCreate", {"status": "COMPLETED"}),
        ("CourseCreate", {"id": "550e8400-e29b-41d4-a716-446655440000"}),
        ("ReviewCreate", {"type": "auto"}),
    ]:
        payload = deepcopy(SPEC["components"]["schemas"][name]["example"])
        payload.update(extra)
        assert list(validator(name).iter_errors(payload))


def test_pagination_limits() -> None:
    """Проверить границы query-параметров независимо от тела запроса."""
    for name, invalid, valid in [
        ("Limit", [0, 101, "10"], [1, 10, 100]),
        ("Offset", [-1, "0"], [0, 100]),
    ]:
        check = OAS30WriteValidator(SPEC["components"]["parameters"][name]["schema"])
        for value in invalid:
            assert list(check.iter_errors(value))
        for value in valid:
            check.validate(value)


def test_generated_app() -> None:
    """Приложение импортируется, документация и все маршруты доступны."""
    from generated.main import app

    with TestClient(app) as client:
        assert client.get("/docs").status_code == 200
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert set(response.json()["paths"]) == set(SPEC["paths"])
    expected = {
        (path, method.upper())
        for path, methods in SPEC["paths"].items()
        for method in methods
    }
    actual = {
        (route.path, method)
        for route in app.routes
        if route.path.startswith("/api/v1/")
        for method in route.methods
    }
    assert actual == expected
