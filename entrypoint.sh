#!/bin/bash

set -e

service redis-server start

DJANGO_DEVELOPMENT="${DJANGO_DEVELOPMENT:-False}"

ENV_FILE="./core/settings/.env"

if [ ! -f "$ENV_FILE" ]; then
	echo ".env file not found in /core/settings. Creating one with a generated SECRET_KEY."

	SECRET_KEY=$(python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())")

	echo "DJANGO_SECRET_KEY=$SECRET_KEY" >"$ENV_FILE"
	if [ "$DJANGO_DEVELOPMENT" = "False" ]; then
	echo "DJANGO_DEVELOPMENT=False" >>"$ENV_FILE"
	else
	echo "DJANGO_DEVELOPMENT=True" >>"$ENV_FILE"
	fi
fi

# ===========================================
MARKER_FILE="/run/.migrations_done"
APPS_FILE="apps.txt"

if [ -f "$APPS_FILE" ] && [ ! -f "$MARKER_FILE" ]; then
	echo "Running migrations as marker not found and apps list present."
	mapfile -t APPS < <(grep -vE '^\s*(#|$)' "$APPS_FILE")

	if [ ${#APPS[@]} -eq 0 ]; then
		echo "No apps found in $APPS_FILE; skipping makemigrations."
	else
		printf 'Making migrations for apps: %s\n' "${APPS[*]}"
		python manage.py makemigrations "${APPS[@]}"
	fi

	python manage.py migrate
	mkdir -p "$(dirname "$MARKER_FILE")"
	touch "$MARKER_FILE"
	echo "Migrations complete; marker file created at $MARKER_FILE."
	python fill_database.py
fi

if [ "$DJANGO_DEVELOPMENT" = "False" ]; then

	python initialize_logs.py

	# ===========================================
	MARKER_FILE="/run/.collectstatic_done"

	if [ ! -f "$MARKER_FILE" ]; then
		echo "Running collectstatic as DJANGO_DEVELOPMENT is False and it hasn't run yet."
		rm -rf ./static
		python manage.py collectstatic --link --noinput
		mkdir -p "$(dirname "$MARKER_FILE")"
		touch "$MARKER_FILE"
	fi

fi

# Start a background job for cleaning expired tokens
(
  while true; do
    echo "Running flushexpiredtokens cleanup at $(date)"
    python manage.py flushexpiredtokens || echo "Cleanup failed at $(date)"
    sleep 86400  # 24 hours
  done
) &

exec "$@"
