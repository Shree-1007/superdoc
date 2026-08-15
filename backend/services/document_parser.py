"""Document parser — handles PDF, DOCX, and TXT formats.

Assessment: "It takes in related documents in mixed formats."
"""
import os
import logging
from typing import List
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_documents(paths: List[str]) -> List[dict]:
    """Parse a list of file paths into structured document dicts.
    
    Returns list of dicts with keys: filename, format, content, pages, source_type
    """
    documents = []
    for path in paths:
        try:
            doc = parse_single_document(path)
            if doc:
                documents.append(doc)
        except Exception as e:
            logger.error(f"Failed to parse {path}: {type(e).__name__}: {e}")
            # Graceful degradation — skip bad files, keep processing
            documents.append({
                "filename": os.path.basename(path),
                "format": "unknown",
                "content": f"[PARSE ERROR: {type(e).__name__}: {e}]",
                "pages": 0,
                "source_type": "error",
                "error": str(e),
            })
    return documents


def parse_single_document(path: str) -> dict:
    """Parse a single document file."""
    path = str(path)
    ext = Path(path).suffix.lower()
    filename = os.path.basename(path)

    if ext == ".pdf":
        return _parse_pdf(path, filename)
    elif ext in (".docx", ".doc"):
        return _parse_docx(path, filename)
    elif ext == ".txt":
        return _parse_txt(path, filename)
    else:
        logger.warning(f"Unsupported format: {ext} for {filename}")
        return {
            "filename": filename,
            "format": ext.lstrip("."),
            "content": f"[Unsupported format: {ext}. Supported: .pdf, .docx, .txt]",
            "pages": 0,
            "source_type": "unsupported",
        }


def _parse_pdf(path: str, filename: str) -> dict:
    """Parse PDF using pypdf."""
    try:
        from pypdf import PdfReader
    except ImportError:
        logger.error("pypdf not installed. Install with: pip install pypdf")
        return {
            "filename": filename, "format": "pdf",
            "content": "[ERROR: pypdf not installed]",
            "pages": 0, "source_type": "error",
        }

    reader = PdfReader(path)
    pages = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append(f"[Page {i + 1}]\n{text}")

    return {
        "filename": filename,
        "format": "pdf",
        "content": "\n\n".join(pages),
        "pages": len(reader.pages),
        "source_type": _infer_source_type(filename),
    }


def _parse_docx(path: str, filename: str) -> dict:
    """Parse DOCX using python-docx."""
    try:
        from docx import Document
    except ImportError:
        logger.error("python-docx not installed. Install with: pip install python-docx")
        return {
            "filename": filename, "format": "docx",
            "content": "[ERROR: python-docx not installed]",
            "pages": 0, "source_type": "error",
        }

    doc = Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

    return {
        "filename": filename,
        "format": "docx",
        "content": "\n\n".join(paragraphs),
        "pages": max(1, len(paragraphs) // 25),  # rough page estimate
        "source_type": _infer_source_type(filename),
    }


def _parse_txt(path: str, filename: str) -> dict:
    """Parse plain text file."""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()

    return {
        "filename": filename,
        "format": "txt",
        "content": content,
        "pages": max(1, len(content) // 3000),
        "source_type": _infer_source_type(filename),
    }


def _infer_source_type(filename: str) -> str:
    """Infer document type from filename."""
    lower = filename.lower()
    if "contract" in lower or "msa" in lower or "agreement" in lower:
        return "contract"
    elif "invoice" in lower or "inv" in lower:
        return "invoice"
    elif "amendment" in lower or "addendum" in lower:
        return "amendment"
    elif "report" in lower:
        return "report"
    elif "memo" in lower or "note" in lower:
        return "memo"
    return "document"
