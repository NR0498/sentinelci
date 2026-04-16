import logging
from logging.config import dictConfig

from fastapi import FastAPI, Request


dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
            }
        },
        "root": {"handlers": ["console"], "level": "INFO"},
    }
)

logger = logging.getLogger("sentinelci.api")

app = FastAPI(title="SentinelCI API", version="1.0.0")


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info("Incoming request %s %s", request.method, request.url.path)
    response = await call_next(request)
    logger.info(
        "Completed request %s %s with status %s",
        request.method,
        request.url.path,
        response.status_code,
    )
    return response


@app.get("/")
def home():
    logger.info("Serving home endpoint")
    return {"message": "SentinelCI is running"}


@app.get("/health")
def health():
    logger.info("Health check requested")
    return {"status": "healthy"}


@app.get("/users/{user_id}")
def get_user(user_id: int):
    logger.info("Fetching user %s", user_id)
    return {"user_id": user_id, "name": "test_user"}
