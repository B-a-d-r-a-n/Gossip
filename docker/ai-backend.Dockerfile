FROM python:3.11-slim

WORKDIR /app

RUN pip install uv

COPY ai-backend/pyproject.toml ai-backend/uv.lock* ./
RUN uv sync --frozen

COPY ai-backend ./

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
