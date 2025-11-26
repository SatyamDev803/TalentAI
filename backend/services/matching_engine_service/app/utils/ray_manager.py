import ray
from typing import Optional
from common.logging import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class RayManager:
    _initialized = False
    _dashboard_port: Optional[int] = None

    @classmethod
    def init_ray(cls):
        if cls._initialized:
            logger.info("Ray already initialized")
            return

        try:
            if settings.ray_enabled:
                logger.info(f"Initializing Ray with {settings.ray_num_cpus} CPUs")

                ray.init(
                    num_cpus=settings.ray_num_cpus,
                    dashboard_port=(
                        settings.ray_dashboard_port
                        if settings.ray_dashboard_port
                        else None
                    ),
                    ignore_reinit_error=True,
                    logging_level="INFO",
                    log_to_driver=False,
                    _system_config={
                        "scheduler_report_heartbeat_interval_ms": 0,
                        "scheduler_report_events": False,
                    },
                )

                cls._initialized = True
                cls._dashboard_port = settings.ray_dashboard_port

                logger.info("Ray initialized successfully")
                if cls._dashboard_port:
                    logger.info(
                        f"Ray Dashboard: http://localhost:{cls._dashboard_port}"
                    )
            else:
                logger.warning("Ray is disabled in configuration")
        except Exception as e:
            logger.error(f"Failed to initialize Ray: {e}")
            cls._initialized = False

    @classmethod
    def shutdown_ray(cls):
        if cls._initialized:
            try:
                logger.info("Shutting down Ray...")
                ray.shutdown()
                cls._initialized = False
                logger.info("Ray shutdown complete")
            except Exception as e:
                logger.error(f"Error shutting down Ray: {e}")

    @classmethod
    def is_initialized(cls) -> bool:
        return cls._initialized

    @classmethod
    def get_cluster_resources(cls) -> dict:
        if not cls._initialized:
            return {}

        try:
            return ray.cluster_resources()
        except Exception as e:
            logger.error(f"Error getting cluster resources: {e}")
            return {}
