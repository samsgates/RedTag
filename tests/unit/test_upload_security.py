import pytest

from app.services.upload_security import validate_evidence_upload


def test_rejects_active_content_extension():
    with pytest.raises(ValueError, match="active-content"):
        validate_evidence_upload("supplier.html", "text/plain", b"hello")


def test_rejects_forged_pdf_signature():
    with pytest.raises(ValueError, match="PDF signature"):
        validate_evidence_upload("supplier.pdf", "application/pdf", b"not-a-pdf")


def test_accepts_valid_pdf_signature():
    validate_evidence_upload("supplier.pdf", "application/pdf", b"%PDF-1.7\nfixture")
