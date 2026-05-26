import io
import magic
from typing import Tuple, Optional

import pdfplumber
from docx import Document
import Pypdf2

from backend.utils.file_utils import(
    FileParsingError,
    TextExtractionError,
    FileUploadError,
    log_error,
    log_warning,
    log_info,
    with_fallback
)

from backend.core.config import (
    MAX_FILE_SIZE_BYTES,
    MAX_FILE_SIZE_MB,
    ALLOWED_FILE_TYPES,
    MAXFILE_SIZE_BYTES
)

class FileParsingError(Exception):
    pass

class FileValidationError(Exception):
    pass
