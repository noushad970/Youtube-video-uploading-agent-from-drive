import time
import functools
from typing import Callable, Type, Tuple, Any
from app.core.logging_config import logger


def retry_with_backoff(
    retries: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,),
) -> Callable:
    """
    Decorator for retrying a function with exponential backoff.
    Example: 2s -> 4s -> 8s -> ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            attempt = 0
            while attempt < retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempt += 1
                    if attempt >= retries:
                        logger.error(
                            f"Operation {func.__name__} failed after {retries} attempts: {e}"
                        )
                        raise
                    logger.warning(
                        f"Attempt {attempt}/{retries} for {func.__name__} failed: {e}. "
                        f"Retrying in {delay:.1f}s..."
                    )
                    time.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)
        return wrapper
    return decorator
