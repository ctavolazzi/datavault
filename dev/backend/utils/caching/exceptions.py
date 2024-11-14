class CacheError(Exception):
    """Base exception for cache-related errors"""
    pass

class CacheWriteError(CacheError):
    """Raised when cache write operations fail"""
    pass

class CacheReadError(CacheError):
    """Raised when cache read operations fail"""
    pass