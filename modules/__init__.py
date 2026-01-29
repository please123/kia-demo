"""
modules package

Provide package-style imports expected by `main.py` / `test_setup.py`.
"""

from text_extractor import TextExtractor
from metadata_generator import MetadataGenerator
from csv_handler import CSVHandler

__all__ = ["TextExtractor", "MetadataGenerator", "CSVHandler"]

