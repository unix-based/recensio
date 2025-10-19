"""
Modern context managers for the application.
Provides clean resource management and error handling.
"""

import asyncio
from typing import AsyncGenerator, Optional, Any, Dict
from contextlib import asynccontextmanager
from app.logger import get_module_logger

logger = get_module_logger(__name__)


@asynccontextmanager
async def ai_operation_context(operation_name: str, **kwargs) -> AsyncGenerator[Dict[str, Any], None]:
    """Async context manager for AI operations.
    
    Provides structured logging and error handling for AI operations.
    
    Args:
        operation_name: Name of the AI operation
        **kwargs: Additional context information
        
    Yields:
        Context dictionary with operation information
        
    Raises:
        Exception: If AI operation fails
    """
    context = {
        "operation": operation_name,
        "start_time": asyncio.get_event_loop().time(),
        **kwargs
    }
    
    try:
        logger.info(f"Starting AI operation: {operation_name}")
        yield context
        logger.info(f"AI operation completed successfully: {operation_name}")
    except Exception as e:
        logger.error(f"AI operation failed: {operation_name} - {str(e)}")
        context["error"] = str(e)
        raise
    finally:
        duration = asyncio.get_event_loop().time() - context["start_time"]
        logger.info(f"AI operation duration: {operation_name} - {duration:.2f}s")


@asynccontextmanager
async def background_task_context(task_id: str, task_name: str) -> AsyncGenerator[Dict[str, Any], None]:
    """Async context manager for background tasks.
    
    Provides structured logging and progress tracking for background tasks.
    
    Args:
        task_id: Unique task identifier
        task_name: Name of the background task
        
    Yields:
        Context dictionary with task information
        
    Raises:
        Exception: If background task fails
    """
    context = {
        "task_id": task_id,
        "task_name": task_name,
        "start_time": asyncio.get_event_loop().time(),
        "status": "running"
    }
    
    try:
        logger.info(f"Starting background task: {task_name} (ID: {task_id})")
        yield context
        context["status"] = "completed"
        logger.info(f"Background task completed: {task_name} (ID: {task_id})")
    except Exception as e:
        context["status"] = "failed"
        context["error"] = str(e)
        logger.error(f"Background task failed: {task_name} (ID: {task_id}) - {str(e)}")
        raise
    finally:
        duration = asyncio.get_event_loop().time() - context["start_time"]
        logger.info(f"Background task duration: {task_name} (ID: {task_id}) - {duration:.2f}s")


@asynccontextmanager
async def rate_limit_context(operation: str, max_concurrent: int = 10) -> AsyncGenerator[None, None]:
    """Async context manager for rate limiting.
    
    Provides semaphore-based rate limiting for operations.
    
    Args:
        operation: Name of the operation being rate limited
        max_concurrent: Maximum concurrent operations allowed
        
    Yields:
        None
        
    Raises:
        Exception: If rate limit is exceeded
    """
    # Create a semaphore for this operation type
    semaphore = asyncio.Semaphore(max_concurrent)
    
    try:
        await semaphore.acquire()
        logger.debug(f"Rate limit acquired for operation: {operation}")
        yield
    except Exception as e:
        logger.error(f"Rate limit error for operation {operation}: {str(e)}")
        raise
    finally:
        semaphore.release()
        logger.debug(f"Rate limit released for operation: {operation}")


@asynccontextmanager
async def retry_context(
    operation: str, 
    max_retries: int = 3, 
    delay: float = 1.0,
    backoff_factor: float = 2.0
) -> AsyncGenerator[None, None]:
    """Async context manager for retry logic.
    
    Provides exponential backoff retry mechanism.
    
    Args:
        operation: Name of the operation being retried
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff_factor: Factor to multiply delay by after each retry
        
    Yields:
        None
        
    Raises:
        Exception: If all retries are exhausted
    """
    current_delay = delay
    last_exception = None
    
    for attempt in range(max_retries + 1):
        try:
            logger.debug(f"Retry attempt {attempt + 1} for operation: {operation}")
            yield
            if attempt > 0:
                logger.info(f"Operation succeeded after {attempt + 1} attempts: {operation}")
            return
        except Exception as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(f"Operation failed (attempt {attempt + 1}), retrying in {current_delay}s: {operation}")
                await asyncio.sleep(current_delay)
                current_delay *= backoff_factor
            else:
                logger.error(f"Operation failed after {max_retries + 1} attempts: {operation}")
                raise last_exception
