"""
Process pool for CPU-bound extraction tasks.
Automatically detects CPU cores and uses multiprocessing for parallel extraction.
"""
import os
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Optional, Callable, Any
import psutil


class ExtractionPool:
    """
    Process pool manager for CPU-bound extraction tasks.
    Automatically detects and uses available CPU cores.
    """
    
    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize extraction pool with automatic core detection.
        
        Args:
            max_workers: Maximum number of worker processes. If None, uses CPU count - 1
                        (leaves one core for I/O and system tasks)
        """
        if max_workers is None:
            # Use all cores minus 1 (leave one for I/O and system)
            cpu_count = os.cpu_count() or psutil.cpu_count(logical=True) or 4
            max_workers = max(1, cpu_count - 1)
        
        self.max_workers = max_workers
        self._executor: Optional[ProcessPoolExecutor] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.shutdown()
        
    def start(self):
        """Start the process pool."""
        if self._executor is None:
            self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
            self._loop = asyncio.get_event_loop()
            print(f"Extraction pool started with {self.max_workers} worker processes (CPU cores detected: {os.cpu_count() or psutil.cpu_count(logical=True)})")
    
    def shutdown(self, wait: bool = True):
        """Shutdown the process pool."""
        if self._executor:
            self._executor.shutdown(wait=wait)
            self._executor = None
            self._loop = None
    
    async def run_extraction(self, func: Callable, *args, **kwargs) -> Any:
        """
        Run CPU-bound extraction function in process pool.
        
        Args:
            func: Extraction function to run (must be picklable)
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
        
        Returns:
            Result from extraction function
        """
        if self._executor is None:
            self.start()
        
        # Run in process pool
        loop = self._loop or asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, func, *args, **kwargs)
    
    @property
    def is_active(self) -> bool:
        """Check if pool is active."""
        return self._executor is not None


# Global extraction pool instance
_extraction_pool: Optional[ExtractionPool] = None


def get_extraction_pool(max_workers: Optional[int] = None) -> ExtractionPool:
    """
    Get or create global extraction pool.
    
    Args:
        max_workers: Maximum workers (only used on first call)
    
    Returns:
        ExtractionPool instance
    """
    global _extraction_pool
    if _extraction_pool is None:
        _extraction_pool = ExtractionPool(max_workers=max_workers)
        _extraction_pool.start()
    return _extraction_pool


def shutdown_extraction_pool():
    """Shutdown global extraction pool."""
    global _extraction_pool
    if _extraction_pool:
        _extraction_pool.shutdown()
        _extraction_pool = None


