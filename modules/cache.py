"""Generic cache module for storing and retrieving data"""

import os
import json
import modules.logger as logger


class Cache:
    """Generic cache with file-based storage"""

    def __init__(self, cache_dir, file_extension=".txt"):
        """
        Initialize cache

        Args:
            cache_dir: Directory to store cache files
            file_extension: File extension for cache files (default: .txt)
        """
        self.cache_dir = cache_dir
        self.file_extension = file_extension

        # Create cache directory if it doesn't exist
        os.makedirs(self.cache_dir, exist_ok=True)
        logger.info(f"Cache initialized: {self.cache_dir}")

    def _get_filepath(self, key):
        """Get filepath for a cache key"""
        # Sanitize key to make it filesystem-safe
        safe_key = "".join(c for c in key if c.isalnum() or c in ("-", "_"))
        return os.path.join(self.cache_dir, f"{safe_key}{self.file_extension}")

    def exists(self, key):
        """
        Check if key exists in cache

        Returns:
            bool: True if key exists, False otherwise
        """
        filepath = self._get_filepath(key)
        return os.path.exists(filepath)

    def get(self, key, fetch_callback=None):
        """
        Get value from cache, or fetch and store if not found

        Args:
            key: Cache key
            fetch_callback: Optional callback function(key) -> (success, value)
                           Called if key not in cache

        Returns:
            tuple: (success: bool, value: str or error_message: str)
        """
        filepath = self._get_filepath(key)

        # Try to read from cache
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    value = f.read()
                logger.info(f"Cache hit: {key}")
                return True, value
            except Exception as e:
                logger.error(f"Error reading cache for {key}: {str(e)}")
                # Continue to fetch if read fails

        # Cache miss - use callback if provided
        if fetch_callback:
            logger.info(f"Cache miss: {key}, fetching...")
            success, value = fetch_callback(key)

            if success:
                # Store in cache
                store_success, store_msg = self.set(key, value)
                if not store_success:
                    logger.warning(f"Failed to cache {key}: {store_msg}")
                return True, value
            else:
                return False, value

        # No callback and not in cache
        return False, f"Key '{key}' not found in cache and no fetch callback provided"

    def set(self, key, value):
        """
        Store value in cache

        Args:
            key: Cache key
            value: Value to store (string)

        Returns:
            tuple: (success: bool, message: str)
        """
        filepath = self._get_filepath(key)

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(value)
            logger.info(f"Cached: {key} ({len(value)} chars)")
            return True, f"Cached successfully"
        except Exception as e:
            logger.error(f"Error caching {key}: {str(e)}")
            return False, f"Error caching: {str(e)}"

    def delete(self, key):
        """
        Delete key from cache

        Returns:
            tuple: (success: bool, message: str)
        """
        filepath = self._get_filepath(key)

        if not os.path.exists(filepath):
            return False, f"Key '{key}' not found in cache"

        try:
            os.remove(filepath)
            logger.info(f"Deleted from cache: {key}")
            return True, "Deleted successfully"
        except Exception as e:
            logger.error(f"Error deleting {key}: {str(e)}")
            return False, f"Error deleting: {str(e)}"

    def list_keys(self):
        """
        List all keys in cache

        Returns:
            list: List of cache keys
        """
        try:
            files = os.listdir(self.cache_dir)
            # Remove file extensions to get keys
            keys = [
                f.replace(self.file_extension, "")
                for f in files
                if f.endswith(self.file_extension)
            ]
            return keys
        except Exception as e:
            logger.error(f"Error listing cache keys: {str(e)}")
            return []

    def clear(self):
        """
        Clear all cache entries

        Returns:
            tuple: (success: bool, message: str)
        """
        try:
            files = os.listdir(self.cache_dir)
            count = 0
            for f in files:
                if f.endswith(self.file_extension):
                    os.remove(os.path.join(self.cache_dir, f))
                    count += 1
            logger.info(f"Cache cleared: {count} entries deleted")
            return True, f"Cleared {count} entries"
        except Exception as e:
            logger.error(f"Error clearing cache: {str(e)}")
            return False, f"Error clearing cache: {str(e)}"
