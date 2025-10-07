"""
Advanced OCR - Math Problem Image to Word Document Converter
"""

__version__ = "1.0.0"
__author__ = "Advanced OCR Team"

from .image_processor import ImageProcessor
from .llm_client import LLMClient
from .formula_converter import FormulaConverter
from .document_generator import DocumentGenerator

__all__ = [
    "ImageProcessor",
    "LLMClient", 
    "FormulaConverter",
    "DocumentGenerator"
]

