"""Логика служебных операций."""

from src.web.schemas import ServiceInfo


def get_service_info() -> ServiceInfo:
    """Получить сведения о состоянии сервиса."""
    return ServiceInfo()
