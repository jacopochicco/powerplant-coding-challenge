# Use official Python image
FROM python:3.11-slim as base

# Set environment variables

ENV POETRY_VERSION=1.8.2 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Install system dependencies and Poetry

RUN apt-get update && apt-get install -y curl build-essential \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && ln -s /root/.local/bin/poetry /usr/local/bin/poetry \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy only dependency files first for caching
COPY pyproject.toml poetry.lock* /app/

# Install dependencies
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi

# Copy the rest of the application
COPY ./app /app/app
COPY ./tests /app/tests

# Expose FastAPI port
EXPOSE 8888

# Run the app
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8888"]

# Tests
FROM base as test
CMD ["pytest", "/app/tests/test_main.py"]
