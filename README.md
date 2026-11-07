# Проект создания опросов пользователей (UGC)

Технологии **Django + DRF**, ASGI (uvicorn), PostgreSQL, шаблоны + JS.

Идентификация - заголовок `X-User-Id` (middleware), без полноценной авторизации.

## Быстрый старт (Docker)

```bash
docker compose up -d --build
```

- UI: http://localhost:8000/
- Healthcheck: http://localhost:8000/health/
- API следующего вопроса: `GET /api/surveys/<id>/next-question/` + заголовок `X-User-Id` с именем пользователя

Тестовый опрос создается при старте контейнера.

## Быстрый старт (локально через uv)

Нужен запущенный Postgres (при желании можно запустить в контейнере):

```bash
docker compose up -d db
```

Создать файл с переменными окружения по образцу и для локального запуска выставить `DEBUG=True`:

```bash
cp .env.example .env
```

Создать окружение и установить зависимости с помощью менеджера uv:

```bash
uv sync
```

Применить миграции, создать тестовый опрос (при желании), собрать статику и запустить приложение:

```bash
uv run python manage.py migrate
uv run python manage.py create_test_survey
uv run python manage.py collectstatic --noinput
uv run uvicorn config.asgi:application --reload --port 8000
```

Запуск тестов:

```bash
uv run pytest
```

## Краткое описание API

| Метод | Путь | Назначение |
|-------|------|------------|
| GET | `/api/surveys/` | список опросов |
| POST | `/api/surveys/create/` | создание опроса |
| GET | `/api/surveys/<id>/` | детали опроса |
| PATCH | `/api/surveys/<id>/` | изменение названия опроса (только автор) |
| DELETE | `/api/surveys/<id>/` | удаление опроса (только автор) |
| GET | `/api/surveys/<id>/next-question/` | следующий вопрос |
| POST | `/api/surveys/<id>/answers/` | ответ на вопрос (`question_id`, `choice_id`, `free_text?`) |
| GET | `/api/surveys/<id>/stats/` | статистика по опросу (только автор) |

Все пути `/api/*` требуют заголовок `X-User-Id`.
