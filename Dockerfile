FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

ARG REQUIREMENTS_FILE=requirements.txt

WORKDIR /workspace

COPY app/requirements*.txt /workspace/app/

RUN cp "/workspace/app/${REQUIREMENTS_FILE}" /tmp/requirements.txt && \
    python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install -r /tmp/requirements.txt

COPY app/ /workspace/app/

RUN useradd --create-home appuser

RUN chown -R appuser:appuser /workspace

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
