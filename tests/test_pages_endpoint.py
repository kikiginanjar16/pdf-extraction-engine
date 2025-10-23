from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_pages_payload_validation():
    # A fake PDF buffer (route should reject if parsing fails, but we test 400 for invalid payload first)
    fake_pdf = b"%PDF-1.4\n%%EOF"
    # Missing payload -> should 422 because required form field is missing
    files = { "file": ("fake.pdf", fake_pdf, "application/pdf") }
    r = client.post("/extract/text/pages", files=files)
    assert r.status_code in (400, 422)
