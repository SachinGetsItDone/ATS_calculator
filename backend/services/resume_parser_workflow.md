# Resume Parser — How It Works

## Overview

`resume_parser.py` takes a raw uploaded file (bytes + filename), validates it, extracts all readable text from it, and returns that text along with some metadata. It supports **PDF** and **DOCX** formats.

---

## Top-Level Entry Point

```
parse_resume_file(file_data: bytes, filename: str) -> (text, metadata)
```

This is the only function the API layer calls. Everything else is internal.

**Flow:**

```
API layer
   │
   ▼
parse_resume_file()
   │
   ├─── Phase 1: validate_file()
   │        ├─ check file size  (too big → error)
   │        ├─ check not empty  (0 bytes → error)
   │        ├─ detect MIME type via libmagic
   │        └─ check MIME is in SUPPORTED_MIME_TYPES → returns file_type ('pdf' / 'docx')
   │
   └─── Phase 2: extract_text(file_data, file_type)
            ├─ 'pdf'  → extract_text_from_pdf()
            ├─ 'docx' → extract_text_from_docx()
            └─ 'doc'  → extract_text_from_doc()  ← always raises (unsupported)
```

On success, returns `(text_string, metadata_dict)`.

---

## Phase 1 — Validation (`validate_file`)

| Check | What happens on failure |
|---|---|
| `len(file_data) > MAX_FILE_SIZE_BYTES` | Returns `False` with a size error message |
| `len(file_data) == 0` | Returns `False` with an "empty file" message |
| `magic.from_buffer()` crashes | Returns `False` with the exception message |
| MIME type not in `SUPPORTED_MIME_TYPES` | Returns `False` with a "unsupported type" message |
| All pass | Returns `(True, '', file_type)` |

`libmagic` reads the actual byte signature of the file — this is more reliable than checking the filename extension, which can be faked.

---

## Phase 2 — Text Extraction

### PDF path (`extract_text_from_pdf`)

PDFs are tricky — some libraries handle certain PDFs better than others. This uses a **primary + fallback** strategy via `with_fallback()`:

```
extract_text_from_pdf()
   │
   ├─── Primary: _extract_pdf_with_pdfplumber()
   │        ├─ opens PDF from bytes
   │        ├─ iterates every page, calls page.extract_text()
   │        ├─ appends hyperlinks from _extract_pdf_hyperlinks()
   │        └─ raises TextExtractionError if nothing extracted
   │
   └─── Fallback: _extract_pdf_with_pypdf2()   (only runs if pdfplumber fails)
            ├─ same idea, different library (PyPDF2)
            ├─ appends hyperlinks from _extract_pdf_hyperlinks()
            └─ raises TextExtractionError if nothing extracted
```

If **both** fail, `extract_text_from_pdf` raises `FileParsingError` (PDF is corrupted / scanned image / password-protected).

### Hyperlink extraction (`_extract_pdf_hyperlinks`)

PDF hyperlinks (LinkedIn, GitHub, etc.) are stored in **annotation objects**, not in the visible text layer. This function walks every page's `/Annots` list, finds `/Link` annotations, reads the `/URI` field, and collects any URL that starts with `http`.

### DOCX path (`extract_text_from_docx`)

```
extract_text_from_docx()
   ├─ parse Document from bytes
   ├─ collect text from all paragraphs  (headings, bullets, body)
   ├─ collect text from all table cells
   ├─ join everything with newlines
   ├─ walk doc.part.rels to find embedded hyperlinks
   └─ return combined text
```

DOCX stores hyperlinks in the document's **relationship table** (`doc.part.rels`), not inline — so they need a separate pass.

### DOC path (`extract_text_from_doc`)

Legacy `.doc` format is **not supported**. This function immediately raises `FileParsingError` with a message telling the user to convert to DOCX or PDF.

---

## Error Classes

| Class | When it's raised |
|---|---|
| `FileValidationError` | File is wrong type, too big, empty, or unreadable by libmagic |
| `FileParsingError` | File passed validation but text could not be extracted |
| `TextExtractionError` | Internal — signals to `with_fallback` that a specific extractor got nothing |

---

## Metadata returned

```python
{
    'filename':        'resume.pdf',   # original filename
    'file_type':       'pdf',          # resolved type
    'file_size_bytes': 204800,         # raw upload size
    'text_length':     4823,           # characters extracted
    'success':         True,
}
```

---

## Dependency Map

```
parse_resume_file
├── validate_file
│   └── magic.from_buffer  (libmagic)
├── extract_text
│   ├── extract_text_from_pdf
│   │   ├── _extract_pdf_with_pdfplumber  (pdfplumber)
│   │   ├── _extract_pdf_with_pypdf2      (PyPDF2)
│   │   └── _extract_pdf_hyperlinks       (PyPDF2)
│   ├── extract_text_from_docx            (python-docx)
│   └── extract_text_from_doc             (raises immediately)
└── with_fallback  (from file_utils)
```
