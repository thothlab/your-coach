# syntax=docker/dockerfile:1.7

# Stage 1: build the Mini-App static bundle.
FROM node:22-alpine AS mini-app-build
WORKDIR /build/mini-app
COPY mini-app/package.json mini-app/package-lock.json ./
RUN npm ci
COPY mini-app/ ./
RUN npm run build && node scripts/check-bundle-size.mjs

# Stage 2: backend runtime (slim Python).
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    APP_ENV=prod \
    MINI_APP_DIST=/app/mini-app/dist
WORKDIR /app

RUN apt-get update \
  && apt-get install -y --no-install-recommends curl \
  && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/alembic.ini /app/backend/
COPY backend/src /app/backend/src
COPY backend/alembic /app/backend/alembic
RUN pip install --upgrade pip \
 && pip install /app/backend

COPY --from=mini-app-build /build/mini-app/dist /app/mini-app/dist

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
  CMD curl -fsS http://localhost:8000/healthz || exit 1
CMD ["python", "-m", "trainbeat", "serve"]
