from pathlib import Path

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "image/jpeg",
    "image/png",
    "image/webp",
    "text/plain",
    "text/csv",
    "application/csv",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

DENIED_EXTENSIONS = {
    ".exe", ".dll", ".com", ".bat", ".cmd", ".ps1", ".sh", ".js", ".mjs", ".html", ".htm", ".svg",
    ".jar", ".msi", ".scr", ".app", ".dmg", ".pkg",
}


def validate_evidence_upload(file_name: str, content_type: str, content: bytes) -> None:
    suffix = Path(file_name).suffix.lower()
    if suffix in DENIED_EXTENSIONS:
        raise ValueError(f"Executable or active-content evidence is not accepted: {suffix}")
    if content_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"Unsupported evidence content type: {content_type}")
    if content_type == "application/pdf" and not content.startswith(b"%PDF-"):
        raise ValueError("PDF signature does not match content type")
    if content_type == "image/png" and not content.startswith(b"\x89PNG\r\n\x1a\n"):
        raise ValueError("PNG signature does not match content type")
    if content_type == "image/jpeg" and not content.startswith(b"\xff\xd8\xff"):
        raise ValueError("JPEG signature does not match content type")
    if content_type in {
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    } and not content.startswith(b"PK\x03\x04"):
        raise ValueError("Office document ZIP signature does not match content type")
