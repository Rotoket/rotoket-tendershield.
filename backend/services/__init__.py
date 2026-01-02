"""
Services module for Tender Shield Pro backend.
"""

from .pandoc_service import docx_to_markdown, PandocServiceError

__all__ = ['docx_to_markdown', 'PandocServiceError']





