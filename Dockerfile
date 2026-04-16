FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG REQUIREMENTS_FILE=requirements.txt

WORKDIR /app

COPY app/ /app/

RUN cp "/app/${REQUIREMENTS_FILE}" /tmp/requirements.txt && \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r /tmp/requirements.txt

RUN useradd --create-home appuser

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
