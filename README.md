# course-services

Учебный проект системы управления курсами, заданиями, сдачами и проверками кода.
Лабораторная работа № 1 создаёт основу backend-приложения: структуру проекта,
настройки, служебный HTTP-маршрут, логирование, тесты и проверки качества.

## Сервисы и архитектура

- **course-service** — курсы, задания, сдачи и оценки; запуск проверок кода и анализа
  сходства. Сейчас реализован каркас FastAPI и маршрут состояния сервиса.
- **bff** — взаимодействие с клиентами, сессии и адаптация API. Пока каталог-заготовка.
- **code-coordinator** — получение кода, запуск проверок и сбор результатов.
  Пока каталог-заготовка.
- **plagiarism-service** — анализ сходства снимков кода. Пока каталог-заготовка.

По архитектуре предполагаются PostgreSQL, Keycloak, Kafka и хранилища материалов,
снимков кода и результатов. Их интеграции в лабораторной № 1 ещё не реализованы.

## Окружение

Нужны Git, Python 3.14+ и uv. В методичке указана версия uv 0.12.17.
Версии библиотек закреплены в `pyproject.toml` и `uv.lock`.

Все команды ниже выполняются из каталога `course-service`:

```bash
cd course-service
python3 -m venv .tools/uv-0.12.17
.tools/uv-0.12.17/bin/python -m pip install uv==0.12.17
export PATH="$PWD/.tools/uv-0.12.17/bin:$PATH"
uv --version
uv sync --locked
cp .env.example .env
```

Версия uv устанавливается локально в игнорируемую папку `.tools`, без замены
глобального инструмента. В новом терминале снова добавьте её каталог в `PATH`
командой `export` выше.

Группа `dev` включает группы `test` и `lint`, поэтому зависимости для тестирования
и анализа устанавливаются вместе с окружением разработки.

## Настройки

Файл `.env` содержит локальные настройки и исключён из Git. Для воспроизводимого
запуска в репозиторий включён `.env.example` без секретов.

```dotenv
APP__TITLE="Course service"
APP__DESCRIPTION="Course service description"
APP__SUMMARY="Course service summary"
APP__VERSION="0.1.0"
APP__DEBUG=false
```

`BaseSettings` загружает значения, а `env_nested_delimiter="__"` связывает
`APP__TITLE` с полем `settings.app.title`. Поле `app` обязательно: при отсутствии
данных для него запуск завершится ошибкой валидации. Значения остальных полей
вложенной модели могут браться по умолчанию.

При стандартных источниках явно переданные аргументы имеют приоритет перед
окружением процесса, затем идёт `.env`, а затем значения по умолчанию.
Настройки кешируются функцией `get_settings`; после изменения конфигурации
работающий процесс следует перезапустить.

## Локальный запуск

```bash
uv run uvicorn src.main:app \
  --host 127.0.0.1 \
  --port 8888 \
  --env-file .env \
  --workers 1 \
  --log-level info \
  --no-access-log \
  --log-config log-config.yaml
```

`src.main:app` указывает модуль и объект FastAPI. Сервер Uvicorn принимает
HTTP-запросы и передаёт их приложению. Для остановки нажмите Ctrl+C.

Для автоматического перезапуска при изменении Python-файлов можно добавить
`--reload` и убрать `--workers`. Эти режимы совместно не используются.
Для эксперимента с портом замените `--port 8888` на `--port 8889` и обновите адрес
в браузере или Postman.

## Проверка API

| Метод и путь | Результат |
|---|---|
| `GET /` | 404, `{"detail": "Not Found"}` |
| `GET /service/` | 200, `{"healthy": true}` |
| `GET /service` | 307 на `/service/`, затем 200 при следовании перенаправлению |
| `GET /docs` | 200, HTML-страница Swagger UI |
| `GET /openapi.json` | 200, описание API в JSON, OpenAPI 3.1.0 |

Откройте `http://127.0.0.1:8888/service/`, `/docs` и `/openapi.json` в браузере.
Повторите GET-запросы в Postman и сравните статус, Content-Type и тело ответа.
Браузер отображает HTML как страницу, а клиент API позволяет рассмотреть
HTTP-ответ. Для сравнения 307 и 200 отключите автоматическое следование
перенаправлениям в клиенте API.

## Тесты

```bash
uv run pytest
```

Пять тестовых случаев проверяют служебный маршрут, отсутствие корневого маршрута,
OpenAPI, Swagger UI и создание приложения через `src.main`.
Фикстуры в `tests/conftest.py` подготавливают настройки, приложение и TestClient.
Контекстный менеджер TestClient выполняет запуск и завершение жизненного цикла.
Отдельный сервер Uvicorn для этих тестов не требуется.

Включено покрытие строк и ветвлений; минимальный порог — 80%.

## Проверки качества

```bash
uv run pylint src --rcfile pyproject.toml
uv run mypy src --config-file pyproject.toml
uv run ruff check src --config pyproject.toml
uv run black --check --verbose src tests
uv run isort src tests --check
uv run radon hal src
uv run radon cc src -s
uv run radon mi src -s
```

Pylint и Ruff проверяют код, mypy — аннотации типов, Black форматирует код,
isort упорядочивает импорты, Radon рассчитывает метрики сложности.
Mypy использует плагин Pydantic и пакет `types-PyYAML`.

Для автоматического исправления форматирования:

```bash
uv run ruff check src tests --fix
uv run isort src tests
uv run black src tests
```

## Структура course-service

```text
course-service/
├── .env.example
├── log-config.yaml
├── pyproject.toml
├── uv.lock
├── src/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   └── services.py
│   └── web/
│       ├── __init__.py
│       ├── app.py
│       ├── lifespans.py
│       ├── routers.py
│       └── schemas.py
└── tests/
    ├── __init__.py
    ├── conftest.py
    └── test_app.py
```

Локальный `.env` создаётся из `.env.example` и не попадает в репозиторий.
