import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": getattr(record, "service", "unknown"),
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    def __init__(self):
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )


def setup_logging(
    service_name: str,
    log_level: str = "INFO",
    log_format: str = "text",
    enable_file_logging: bool = True,
    logs_dir: Optional[Path] = None,
) -> None:
    if log_format.lower() == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)

    handlers = [console_handler]

    if enable_file_logging:
        logs_dir = logs_dir or Path("logs")
        logs_dir.mkdir(exist_ok=True)

        log_file = logs_dir / f"{service_name}_{datetime.now().strftime('%Y%m%d')}.log"

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(TextFormatter())
        handlers.append(file_handler)

        logging.info(f"Logging to file: {log_file}")

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    root_logger.handlers.clear()

    for handler in handlers:
        root_logger.addHandler(handler)

    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sentence_transformers").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args, **kwargs):
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)

    logging.info(f"{service_name.upper()} logging configured")


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class PerformanceLogger:
    def __init__(self, logger_name: Optional[str] = None):
        self.logger = logging.getLogger(logger_name or __name__)

    def log_operation(
        self,
        operation: str,
        duration: float,
        success: bool = True,
        **extra_data,
    ):
        status = "SUCCESS" if success else "FAILED"
        message = f"{status} | {operation} | Duration: {duration:.3f}s"

        if extra_data:
            message += f" | {extra_data}"

        if success:
            self.logger.info(message)
        else:
            self.logger.error(message)

    def log_parsing_performance(
        self,
        filename: str,
        parsing_time: float,
        embedding_time: float,
        ai_summary_time: float,
        total_time: float,
        success: bool,
    ):
        status = "SUCCESS" if success else "FAILED"

        self.logger.info(
            f"{status} | Resume: {filename} | "
            f"Parsing: {parsing_time:.2f}s | "
            f"Embedding: {embedding_time:.2f}s | "
            f"AI: {ai_summary_time:.2f}s | "
            f"Total: {total_time:.2f}s"
        )

    def log_search_performance(
        self,
        query: str,
        results_count: int,
        search_time: float,
        embedding_time: float,
    ):
        self.logger.info(
            f"Search: '{query[:50]}...' | "
            f"Results: {results_count} | "
            f"Embedding: {embedding_time:.3f}s | "
            f"Search: {search_time:.3f}s"
        )


# Module-level logger for convenience
logger = get_logger(__name__)
