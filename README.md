# Chat App

Real-time, Docker-first chat platform with an integrated local AI assistant (Ollama). Built with Vue 3 (frontend), FastAPI (backend & AI proxy), PostgreSQL, Redis, and Kafka for streaming.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Getting Started (Docker)](#getting-started-docker)
- [Local Development](#local-development)
- [Services & Ports](#services--ports)
- [Configuration (env)](#configuration-env)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Overview

This repository contains a production-oriented reference implementation of a real-time chat application that demonstrates:

- A single-page Vue 3 frontend that communicates with a FastAPI backend over REST and WebSockets.
- A separate AI proxy service (FastAPI) that routes requests to a local Ollama instance for on-device LLM inference.
- Durable storage with PostgreSQL, fast session/caching with Redis, and message streaming via Kafka for analysis pipelines.
- Docker-first orchestration so the full stack can be brought up locally for development or demos.

The codebase is organized into three primary services in this repository:

- `frontend/` — Vue 3 SPA (Vite)
- `backend/` — FastAPI application (REST + WebSocket server)
- `ai-backend/` — FastAPI AI proxy that talks to Ollama

## Architecture

High level:

```mermaid
flowchart LR
  Frontend["Frontend\n(Vue 3)"] -->|REST / WebSocket| Backend["Backend\n(FastAPI)"]
  Backend -->|AI requests| AIBackend["AI Backend\n(FastAPI)"]
  AIBackend -->|Ollama API| Ollama[(Ollama)]
  Backend --> Postgres[(PostgreSQL)]
  Backend --> Redis[(Redis)]
  Backend --> Kafka[(Kafka)]
```

## Features

- Real-time messaging via WebSockets
- Message streaming for analytics via Kafka
- REST API for management and persistence
- Docker Compose configuration for deployment
- Full Customizable role support
- AI assistant and message analysis via Ollama (local LLM AI integration)
- Persistent storage (Postgres), session/cache (Redis)

## Getting Started (Docker)

Prerequisites: Docker, Docker Compose, 16GB+ RAM recommended (Ollama).

1. Copy the example environment file:

```bash
cp .env.example.docker .env.docker
```

2. Start the stack:

```bash
docker-compose up -d
```

3. Open services:

- Frontend: http://localhost
- Backend API: http://localhost/api
- Ollama API: http://localhost:11434

Tip: The Docker compose brings up an Ollama container — it can be memory-heavy. If you only need the frontend/backend, bring services up selectively in `docker-compose.yml`.

## Local Development

Backend (FastAPI)

```bash
cd backend
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate
uv sync  # or use your preferred tool (poetry/pdm)
uvicorn main:app --reload --port 8000
```

AI Backend (FastAPI)

```bash
cd ai-backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8001
```

Frontend (Vite)

```bash
cd frontend
npm install
npm run dev
```

Notes:
- The backend exposes REST endpoints and a WebSocket endpoint used by the frontend.
- The AI backend expects a running Ollama instance configured via `OLLAMA_URL`.

## Services & Ports

- Frontend: 80 (Docker) / Vite dev default (e.g. 5173)
- Backend: 8000
- AI Backend: 8001
- Ollama: 11434
- PostgreSQL: 5432
- Redis: 6379
- Kafka: 9092

## Configuration (env)

Set the environment variables in the docker/example env file before starting. Common variables:

- `DATABASE_URL` — Postgres DSN. Default used in compose: `postgresql+asyncpg://dev_user:123456@postgres:5432/chat_app`
- `OLLAMA_URL` — Ollama API, e.g. `http://ollama:11434`
- `OLLAMA_MODEL` — Model name served by Ollama (e.g. `llama3.2`)
- `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` — DB credentials
- `REDIS_URL` — Redis connection (e.g. `redis://redis:6379/0`)
- `KAFKA_BOOTSTRAP_SERVERS` — Kafka address (e.g. `kafka:9092`)

Refer to `docker-compose.yml` for how these variables are wired into containers.

## Troubleshooting

- Database connection errors: confirm `DATABASE_URL` and that the Postgres container is healthy (`docker-compose ps`).
- Ollama OOMs or crashes: Ollama needs substantial memory — reduce model size or run Ollama on a machine with more RAM.
- WebSocket issues: check the backend logs (`docker-compose logs backend`) and confirm Redis/Kafka are reachable.

## License

All rights reserved. This code is provided for viewing and evaluation purposes only. No permission is granted for use, reproduction, or distribution.