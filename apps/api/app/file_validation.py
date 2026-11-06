"""Bound input before parsers run. This is not a malware scanner or parser sandbox."""

import io
import re
import zipfile
from fastapi import HTTPException

MAX_BYTES = 20 * 1024 * 1024
MAX_EXPANDED = 32 * 1024 * 1024


def validate_upload(filename: str, data: bytes) -> str:
    name = filename.replace("\\", "/").rsplit("/", 1)[-1]
    if not name or len(name) > 255 or re.search(r"[\x00-\x1f\x7f]", name):
        raise HTTPException(422, "Invalid document filename")
    suffix = name.lower().rsplit(".", 1)[-1]
    if suffix not in {"pdf", "docx", "txt", "md"}:
        raise HTTPException(415, "Supported formats: PDF, DOCX, TXT, MD")
    if not data or len(data) > MAX_BYTES:
        raise HTTPException(413, "File must be between 1 byte and 20 MB")
    if suffix in {"txt", "md"}:
        try:
            text = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            raise HTTPException(415, "Text documents must be UTF-8") from None
        if re.search(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", text):
            raise HTTPException(415, "Binary data is not a text document")
    elif suffix == "pdf":
        if not data.startswith(b"%PDF-") or b"%%EOF" not in data[-1024:]:
            raise HTTPException(415, "File is not a complete PDF")
    else:
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                entries = archive.infolist()
                names = [entry.filename for entry in entries]
                if (
                    len(entries) > 500
                    or len(set(names)) != len(names)
                    or sum(e.file_size for e in entries) > MAX_EXPANDED
                ):
                    raise ValueError("Archive bounds")
                if not {"[Content_Types].xml", "word/document.xml"}.issubset(names):
                    raise ValueError("Not DOCX")
                for entry in entries:
                    if (
                        entry.flag_bits & 1
                        or entry.file_size / max(entry.compress_size, 1) > 100
                    ):
                        raise ValueError("Encrypted or excessive compression")
                    if (
                        entry.filename.startswith("/")
                        or ".." in entry.filename.split("/")
                        or "\\" in entry.filename
                    ):
                        raise ValueError("Unsafe archive path")
                    if entry.filename.lower().endswith("vbaproject.bin"):
                        raise ValueError("Macros not accepted")
                    if entry.filename.lower().endswith(".xml"):
                        xml = archive.read(entry)
                        if b"<!DOCTYPE" in xml.upper() or b"<!ENTITY" in xml.upper():
                            raise ValueError("External XML declarations not accepted")
        except (zipfile.BadZipFile, ValueError, RuntimeError, OSError):
            raise HTTPException(
                415, "Invalid, encrypted, or unsafe DOCX archive"
            ) from None
    return name
