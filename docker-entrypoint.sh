#!/bin/bash
set -e

# Upgrade database
echo "Upgrading database..."
ftcli db upgrade || { echo "Failed to upgrade database!"; exit 1; }

# Bootstrap single-user account on first start only.
# Checks whether the user already exists before attempting creation,
# so subsequent 'docker compose up' restarts are completely silent.
if [ -n "${INIT_USERNAME}" ] && [ -n "${INIT_EMAIL}" ]; then
    if python3 - <<'PYEOF' 2>/dev/null
import os, sys
os.environ.setdefault("APP_SETTINGS", "fittrackee.config.ProductionConfig")
from fittrackee import create_app, db
from fittrackee.users.models import User
app = create_app(init_email=False)
with app.app_context():
    sys.exit(0 if User.query.filter_by(username=os.environ["INIT_USERNAME"]).first() else 1)
PYEOF
    then
        echo "User '${INIT_USERNAME}' already exists, skipping bootstrap."
    else
        echo "Creating initial user '${INIT_USERNAME}'..."
        if [ -n "${INIT_PASSWORD}" ]; then
            ftcli users create "${INIT_USERNAME}" \
                --email "${INIT_EMAIL}" \
                --password "${INIT_PASSWORD}" \
                --role "${INIT_ROLE:-admin}"
        else
            ftcli users create "${INIT_USERNAME}" \
                --email "${INIT_EMAIL}" \
                --role "${INIT_ROLE:-admin}"
        fi
    fi
fi

# Apply MAX_SINGLE_FILE_SIZE if set (default: 1 MB).
# This is stored in the DB and reapplied on every start so it survives
# container recreations.
if [ -n "${MAX_SINGLE_FILE_SIZE}" ]; then
    python3 - <<PYEOF 2>/dev/null
import os
os.environ.setdefault("APP_SETTINGS", "fittrackee.config.ProductionConfig")
from fittrackee import create_app, db
from fittrackee.application.models import AppConfig
app = create_app(init_email=False)
with app.app_context():
    cfg = AppConfig.query.first()
    if cfg:
        size = int(os.environ["MAX_SINGLE_FILE_SIZE"])
        if cfg.max_single_file_size != size:
            cfg.max_single_file_size = size
            if cfg.max_zip_file_size < size:
                cfg.max_zip_file_size = size
            db.session.commit()
            print(f"max_single_file_size set to {size} bytes")
PYEOF
fi

# Run app w/ gunicorn
echo "Running app..."
exec gunicorn -b 0.0.0.0:5000 "fittrackee:create_app()" --log-level "${LOG_LEVEL:-info}" --error-logfile "${GUNICORN_LOG:-/usr/src/app/logs/gunicorn.log}" --workers="${APP_WORKERS:-1}" --timeout "${APP_TIMEOUT:-30}" --no-control-socket
