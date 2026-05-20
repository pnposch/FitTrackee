#!/bin/bash
set -e

# Upgrade database
echo "Upgrading database..."
ftcli db upgrade || { echo "Failed to upgrade database!"; exit 1; }

# Bootstrap single-user account on first start
# Set INIT_USERNAME and INIT_EMAIL to create a user automatically.
# If the user already exists (e.g. on container restart) the command
# prints a warning and continues; it does not fail.
if [ -n "${INIT_USERNAME}" ] && [ -n "${INIT_EMAIL}" ]; then
    echo "Creating initial user '${INIT_USERNAME}'..."
    if [ -n "${INIT_PASSWORD}" ]; then
        ftcli users create "${INIT_USERNAME}" \
            --email "${INIT_EMAIL}" \
            --password "${INIT_PASSWORD}" \
            --role "${INIT_ROLE:-admin}" || true
    else
        ftcli users create "${INIT_USERNAME}" \
            --email "${INIT_EMAIL}" \
            --role "${INIT_ROLE:-admin}" || true
    fi
fi

# Run app w/ gunicorn
echo "Running app..."
exec gunicorn -b 0.0.0.0:5000 "fittrackee:create_app()" --log-level "${LOG_LEVEL:-info}" --error-logfile "${GUNICORN_LOG:-/usr/src/app/logs/gunicorn.log}" --workers="${APP_WORKERS:-1}" --timeout "${APP_TIMEOUT:-30}" --no-control-socket
