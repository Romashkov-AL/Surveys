#!/bin/sh
set -e

python manage.py migrate --noinput
python manage.py create_test_survey
python manage.py collectstatic --noinput

exec uvicorn config.asgi:application --host 0.0.0.0 --port 8000 --workers 2
