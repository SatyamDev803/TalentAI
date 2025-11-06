import asyncio
import functools
import time
from typing import Callable

from common.logger import logger


def log_execution_time(func: Callable) -> Callable:
    if asyncio.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"Function {func.__name__} executed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}"
                )
                raise

        return async_wrapper
    else:

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                logger.info(f"Function {func.__name__} executed in {duration:.3f}s")
                return result
            except Exception as e:
                duration = time.time() - start
                logger.error(
                    f"Function {func.__name__} failed after {duration:.3f}s: {str(e)}"
                )
                raise

        return sync_wrapper


def retry(max_attempts: int = 3, backoff: float = 2):
    def decorator(func: Callable) -> Callable:
        if asyncio.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                attempt = 1
                delay = 1

                while attempt <= max_attempts:
                    try:
                        return await func(*args, **kwargs)
                    except Exception:
                        if attempt == max_attempts:
                            logger.error(
                                f"Function {func.__name__} failed after {max_attempts} attempts"
                            )
                            raise

                        logger.warning(
                            f"Attempt {attempt} failed, retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                        delay *= backoff
                        attempt += 1

            return async_wrapper
        else:

            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                attempt = 1
                delay = 1

                while attempt <= max_attempts:
                    try:
                        return func(*args, **kwargs)
                    except Exception:
                        if attempt == max_attempts:
                            logger.error(
                                f"Function {func.__name__} failed after {max_attempts} attempts"
                            )
                            raise

                        logger.warning(
                            f"Attempt {attempt} failed, retrying in {delay}s..."
                        )
                        time.sleep(delay)
                        delay *= backoff
                        attempt += 1

            return sync_wrapper

    return decorator
