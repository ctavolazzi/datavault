"""Custom exceptions for DataVault"""

class DataVaultError(Exception):
    """Base exception for DataVault"""
    pass

class StorageError(DataVaultError):
    """Raised when there's an error with data storage"""
    pass

class DataValidationError(DataVaultError):
    """Raised when data validation fails"""
    pass 