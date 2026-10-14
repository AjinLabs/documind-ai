"""
DocuMind AI — PDF Processor & Document Extraction Engine
Uses PyMuPDF (fitz) with fallback to pypdf for deterministic, page-accurate extraction.
Features:
- Page-by-page extraction with provenance
- SHA-256 duplicate detection
- Scanned PDF detection
- Table extraction
- Text normalization & metadata extraction
"""
import hashlib
import re
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

logger = logging.getLogger(__name__)

class PDFProcessingError(Exception):
    """Custom exception for PDF processing errors."""
    pass


def calculate_content_hash(file_bytes: bytes) -> str:
    """Calculates SHA-256 hash of file content for duplicate detection."""
    return hashlib.sha256(file_bytes).hexdigest()


def validate_pdf_bytes(file_bytes: bytes, max_size_mb: int = 50) -> Tuple[bool, str]:
    """Validates file size and PDF magic bytes."""
    if not file_bytes:
        return False, "Uploaded file is empty."
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > max_size_mb:
        return False, f"File size ({size_mb:.1f} MB) exceeds maximum limit of {max_size_mb} MB."
    if not file_bytes.startswith(b"%PDF"):
        return False, "Invalid PDF header. File is not a valid PDF document."
    return True, "Valid PDF"


def normalize_text(text: str) -> str:
    """Cleans up text, removes control characters, and standardizes whitespace."""
    if not text:
        return ""
    # Remove null characters and unusual control codes
    text = text.replace("\x00", " ")
    # Normalize irregular spaces and non-breaking spaces
    text = text.replace("\u00a0", " ").replace("\u200b", "")
    # Collapse multiple horizontal whitespace into single space
    text = re.sub(r"[ \t]+", " ", text)
    # Normalize multiple newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Strip trailing and leading whitespace
    return text.strip()


def extract_pdf_data(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """
    Extracts text, pages, metadata, table data, and scanned status from PDF.
    Returns:
        dict with keys: filename, content_hash, page_count, metadata, pages, is_scanned, tables
    """
    is_valid, msg = validate_pdf_bytes(file_bytes)
    if not is_valid:
        raise PDFProcessingError(msg)

    content_hash = calculate_content_hash(file_bytes)
    pages: List[Dict[str, Any]] = []
    metadata: Dict[str, Any] = {}
    is_scanned = False
    extracted_tables: List[Dict[str, Any]] = []

    if PYMUPDF_AVAILABLE:
        try:
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_count = len(doc)
            metadata = {
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", "")
            }

            total_chars = 0
            for page_idx in range(page_count):
                page = doc[page_idx]
                page_num = page_idx + 1
                page_text = page.get_text()
                clean_text = normalize_text(page_text)
                total_chars += len(clean_text)

                # Extract tables if available in PyMuPDF
                try:
                    tabs = page.find_tables()
                    for tab in tabs:
                        table_data = tab.extract()
                        if table_data and len(table_data) > 1:
                            extracted_tables.append({
                                "page_number": page_num,
                                "rows": table_data,
                                "row_count": len(table_data),
                                "col_count": len(table_data[0]) if table_data else 0
                            })
                except Exception:
                    pass

                pages.append({
                    "page_number": page_num,
                    "text": clean_text,
                    "char_count": len(clean_text)
                })

            doc.close()

            # Scanned document detection: if average characters per page is below 40
            if page_count > 0 and (total_chars / page_count) < 40:
                is_scanned = True

        except Exception as e:
            logger.warning(f"PyMuPDF extraction failed for {filename}: {e}. Trying fallback.")
            if PYPDF_AVAILABLE:
                return _extract_with_pypdf(file_bytes, filename, content_hash)
            raise PDFProcessingError(f"Extraction failed: {str(e)}")

    elif PYPDF_AVAILABLE:
        return _extract_with_pypdf(file_bytes, filename, content_hash)
    else:
        raise PDFProcessingError("No PDF extraction library available (neither PyMuPDF nor pypdf found).")

    return {
        "filename": filename,
        "content_hash": content_hash,
        "page_count": len(pages),
        "metadata": metadata,
        "pages": pages,
        "is_scanned": is_scanned,
        "tables": extracted_tables,
        "file_size_bytes": len(file_bytes)
    }


def _extract_with_pypdf(file_bytes: bytes, filename: str, content_hash: str) -> Dict[str, Any]:
    """Fallback extractor using pypdf."""
    import io
    reader = pypdf.PdfReader(io.BytesIO(file_bytes))
    page_count = len(reader.pages)
    pages = []
    total_chars = 0

    for idx, page in enumerate(reader.pages):
        page_num = idx + 1
        raw_text = page.extract_text() or ""
        clean_text = normalize_text(raw_text)
        total_chars += len(clean_text)
        pages.append({
            "page_number": page_num,
            "text": clean_text,
            "char_count": len(clean_text)
        })

    is_scanned = (total_chars / page_count) < 40 if page_count > 0 else True
    return {
        "filename": filename,
        "content_hash": content_hash,
        "page_count": page_count,
        "metadata": dict(reader.metadata) if reader.metadata else {},
        "pages": pages,
        "is_scanned": is_scanned,
        "tables": [],
        "file_size_bytes": len(file_bytes)
    }
