FROM node:24-alpine AS node-builder

WORKDIR /usr/src/app/fittrackee_client

ENV PATH=/usr/src/app/fittrackee_client/node_modules/.bin:$PATH

COPY fittrackee_client/package.json fittrackee_client/package-lock.json ./
RUN apk add --no-cache git && \
    npm ci --ignore-scripts --silent --network-timeout 300000 && \
    npm cache clean --force

COPY fittrackee_client/. .
RUN npm run build

FROM python:3.13-alpine AS python-builder

WORKDIR /usr/src/app/

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_NO_INTERACTION=1 \
    VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml poetry.lock README.md ./
COPY fittrackee/. ./fittrackee/
RUN rm -rf ./fittrackee/tests

RUN apk add --no-cache g++ gdal-dev && \
    python3 -m venv "$VIRTUAL_ENV" && \
    pip install --upgrade --quiet pip wheel poetry==2.3.3 && \
    poetry install --only main --no-interaction --quiet

FROM python:3.13-alpine AS runtime

RUN apk add --no-cache tini libmagic && \
    addgroup -g 1000 -S fittrackee && \
    adduser -H -D -u 1000 -S fittrackee -G fittrackee

WORKDIR /usr/src/app

ENV VIRTUAL_ENV=/opt/venv \
    PATH="/opt/venv/bin:$PATH"

COPY --link --chown=root --chmod=755 --from=python-builder /opt/venv "$VIRTUAL_ENV"
COPY --link --chown=root --chmod=755 --from=python-builder /usr/src/app/fittrackee ./fittrackee
COPY --link --chown=root --chmod=755 --from=node-builder /usr/src/app/fittrackee/dist ./fittrackee/dist
COPY --link --chown=root --chmod=755 docker-entrypoint.sh ./

USER fittrackee

ENTRYPOINT ["/sbin/tini", "--"]