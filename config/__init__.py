"""
config package

This repository currently keeps source files in the project root.
Some scripts expect a `config` package, so we re-export Settings here.
"""

from settings import Settings

__all__ = ["Settings"]

