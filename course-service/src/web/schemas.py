"""Модели данных API."""

from pydantic import BaseModel, ConfigDict


class BaseSchemaModel(BaseModel):
    """Общие настройки моделей API."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        populate_by_name=True,
    )


class ServiceInfo(BaseSchemaModel):
    """Сведения о состоянии сервиса."""

    healthy: bool = True
