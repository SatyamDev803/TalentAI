# """Enhanced logging configuration for Resume Parser Service."""

# import logging
# import sys
# from datetime import datetime
# from pathlib import Path


# def setup_logging(log_level: str = "INFO") -> None:
#     """Configure structured logging with file and console output.

#     Args:
#         log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
#     """
#     # Create logs directory
#     logs_dir = Path("logs")
#     logs_dir.mkdir(exist_ok=True)

#     # Create log filename with date
#     log_file = logs_dir / f"resume_parser_{datetime.now().strftime('%Y%m%d')}.log"

#     # Define log format
#     log_format = (
#         "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
#     )

#     # Create formatters
#     formatter = logging.Formatter(log_format, datefmt="%Y-%m-%d %H:%M:%S")

#     # Console handler (colorful output)
#     console_handler = logging.StreamHandler(sys.stdout)
#     console_handler.setLevel(getattr(logging, log_level.upper()))
#     console_handler.setFormatter(formatter)

#     # File handler (all logs)
#     file_handler = logging.FileHandler(log_file)
#     file_handler.setLevel(logging.DEBUG)
#     file_handler.setFormatter(formatter)

#     # Configure root logger
#     root_logger = logging.getLogger()
#     root_logger.setLevel(logging.DEBUG)
#     root_logger.addHandler(console_handler)
#     root_logger.addHandler(file_handler)

#     # Suppress noisy libraries
#     logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
#     logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
#     logging.getLogger("sentence_transformers").setLevel(logging.WARNING)

#     logging.info(f"✅ Logging configured: {log_file}")


# class PerformanceLogger:
#     """Log performance metrics for resume processing."""

#     def __init__(self):
#         self.logger = logging.getLogger(__name__)

#     def log_parsing_performance(
#         self,
#         resume_id: str,
#         filename: str,
#         parsing_time: float,
#         embedding_time: float,
#         ai_summary_time: float,
#         total_time: float,
#         success: bool,
#     ):
#         """Log resume parsing performance metrics."""
#         status = "✅ SUCCESS" if success else "❌ FAILED"

#         self.logger.info(
#             f"{status} | Resume: {filename} | "
#             f"Parsing: {parsing_time:.2f}s | "
#             f"Embedding: {embedding_time:.2f}s | "
#             f"AI Summary: {ai_summary_time:.2f}s | "
#             f"Total: {total_time:.2f}s"
#         )

#     def log_search_performance(
#         self,
#         query: str,
#         results_count: int,
#         search_time: float,
#         embedding_time: float,
#     ):
#         """Log semantic search performance metrics."""
#         self.logger.info(
#             f"🔍 Search: '{query[:50]}...' | "
#             f"Results: {results_count} | "
#             f"Embedding: {embedding_time:.3f}s | "
#             f"Search: {search_time:.3f}s"
#         )
