"""Application factory — creates and configures the FastAPI instance."""
from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.config import get_settings
from src.logging_config import configure_logging
from src.middleware.auth import JWTAuthMiddleware
from src.middleware.cors import NexusCORSMiddleware
from src.middleware.error_handler import register_error_handlers
from src.middleware.request_logger import RequestLoggerMiddleware
from src.routes import (
    auth,
    services,
    health,
    agents,
    alerts,
    approvals,
    factory,
    skills,
    artifacts,
    probes,
    metadata_index,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle."""
    settings = get_settings()
    configure_logging(settings.log_level)

    # Initialize upstream clients on startup
    from src.clients.wazuh import WazuhClient
    from src.clients.minio_client import MinIOClient
    from src.clients.athena import AthenaClient
    from src.clients.ai_inference import AIInferenceClient
    from src.clients.metadata_index import MetadataIndexClient

    app.state.wazuh_client = WazuhClient(
        base_url=settings.wazuh_api_url,
        user=settings.wazuh_api_user,
        password=settings.wazuh_api_password,
    )
    app.state.minio_client = MinIOClient.from_settings(settings)
    app.state.athena_client = AthenaClient(base_url=settings.athena_agents_url)
    app.state.ai_inference_client = AIInferenceClient(base_url=settings.ai_inference_url)
    app.state.metadata_index = MetadataIndexClient.from_settings(settings)

    import structlog
    logger = structlog.get_logger()
    logger.info(
        "gateway_started",
        port=settings.port,
        auth_provider=settings.auth_provider,
        wazuh_url=settings.wazuh_api_url,
        minio_endpoint=settings.minio_endpoint,
        object_store_backend=settings.object_store_backend,
        metadata_index=app.state.metadata_index.enabled,
        athena_url=settings.athena_agents_url,
        ai_inference_url=settings.ai_inference_url,
    )

    yield

    # Shutdown: close clients
    await app.state.wazuh_client.close()
    await app.state.athena_client.close()
    await app.state.ai_inference_client.close()


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Nexus API Gateway",
        version="1.0.0",
        docs_url="/docs" if settings.debug else None,
        lifespan=lifespan,
    )

    # Middleware: last added runs first (outermost). Order on the wire:
    # CORS → Auth → Request Logger → routes
    app.add_middleware(RequestLoggerMiddleware)
    app.add_middleware(JWTAuthMiddleware)
    app.add_middleware(
        NexusCORSMiddleware,
        allow_origins=settings.cors_allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Accept"],
        expose_headers=["X-Request-ID"],
        max_age=600,
    )

    # Routes
    app.include_router(probes.router)
    app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
    app.include_router(services.router, prefix="/api/v1", tags=["services"])
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
    app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
    app.include_router(approvals.router, prefix="/api/v1", tags=["approvals"])
    app.include_router(factory.router, prefix="/api/v1", tags=["factory"])
    app.include_router(skills.router, prefix="/api/v1", tags=["skills"])
    app.include_router(artifacts.router, prefix="/api/v1", tags=["artifacts"])
    app.include_router(metadata_index.router, prefix="/api/v1", tags=["metadata-index"])

    # Error handlers
    register_error_handlers(app)

    return app
