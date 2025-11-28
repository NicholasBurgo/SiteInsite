"""
Async I/O utilities for safe concurrent file operations.
Uses locks to serialize writes and prevent race conditions.
"""
import asyncio
import json
import os
from typing import Dict, Any, Callable, Optional


class AsyncFileWriter:
    """
    Async file writer that serializes writes to prevent race conditions.
    Each file gets its own lock.
    """
    
    def __init__(self):
        self._locks: Dict[str, asyncio.Lock] = {}
    
    def _get_lock(self, file_path: str) -> asyncio.Lock:
        """Get or create lock for a file."""
        if file_path not in self._locks:
            self._locks[file_path] = asyncio.Lock()
        return self._locks[file_path]
    
    async def write_json(self, file_path: str, data: Any, update_func: Optional[Callable] = None):
        """
        Write JSON file, optionally updating existing data.
        
        Args:
            file_path: Path to JSON file
            data: Data to write (if update_func is None) or data to merge (if update_func provided)
            update_func: Optional function(data, existing) -> updated_data
        """
        lock = self._get_lock(file_path)
        async with lock:
            try:
                # Ensure directory exists
                dir_path = os.path.dirname(file_path)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                
                # If update_func provided, read existing data first
                if update_func:
                    if os.path.exists(file_path):
                        with open(file_path, 'r') as f:
                            existing = json.load(f)
                    else:
                        existing = None
                    data_to_write = update_func(data, existing)
                else:
                    data_to_write = data
                
                # Write atomically using temp file
                temp_path = file_path + '.tmp'
                with open(temp_path, 'w') as f:
                    json.dump(data_to_write, f, indent=2)
                
                # Atomic rename
                os.replace(temp_path, file_path)
                
            except Exception as e:
                print(f"Error writing {file_path}: {e}")
                if os.path.exists(file_path + '.tmp'):
                    try:
                        os.remove(file_path + '.tmp')
                    except:
                        pass


# Global async file writer instance
_async_writer: Optional[AsyncFileWriter] = None


def get_async_writer() -> AsyncFileWriter:
    """Get or create global async file writer."""
    global _async_writer
    if _async_writer is None:
        _async_writer = AsyncFileWriter()
    return _async_writer

