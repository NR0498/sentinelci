import logging
from logging.config import dictConfig
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.aws_service import AwsArtifactService, AwsServiceError


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
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
aws_service = AwsArtifactService()
dashboard_dir = Path(__file__).resolve().parent / "dashboard"


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


@app.get("/api/aws/status")
def aws_status():
    return aws_service.status()


@app.post("/api/artifacts/upload")
def upload_artifact(file: UploadFile = File(...)):
    if not file.filename:
        raise HTTPException(status_code=400, detail="A filename is required.")
    try:
        return aws_service.upload(
            file.file,
            file.filename,
            file.content_type or "application/octet-stream",
        )
    except AwsServiceError as exc:
        logger.exception("Artifact upload failed")
        raise HTTPException(
            status_code=503,
            detail=f"LocalStack upload failed: {exc}",
        ) from exc


@app.get("/api/artifacts")
def list_artifacts():
    try:
        return {"artifacts": aws_service.list_artifacts()}
    except AwsServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/notifications")
def list_notifications():
    try:
        return {"notifications": aws_service.receive_notifications()}
    except AwsServiceError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/dashboard", include_in_schema=False)
def dashboard():
    return FileResponse(dashboard_dir / "index.html")


if dashboard_dir.exists():
    app.mount(
        "/dashboard-assets",
        StaticFiles(directory=dashboard_dir),
        name="dashboard-assets",
    )
