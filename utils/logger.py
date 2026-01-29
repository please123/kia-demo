"""
Compatibility wrapper for `utils.logger`.

The actual implementation lives in the project root `logger.py`.
"""

from logger import setup_logger

__all__ = ["setup_logger"]

