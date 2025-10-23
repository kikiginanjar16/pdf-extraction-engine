# PDF Extraction Service

A minimal **FastAPI** service that extracts text + metadata from PDFs using **PyMuPDF**. Packaged with **Dockerfile** and **docker-compose**.

---

## Features
- Full‑text extraction with metadata (title, author, keywords, pages)
- Extract by **selected page indices (0-based)**
- CORS-enabled for browser usage
- Health check endpoint
- OpenAPI spec included (`openapi.yaml`)

---

## Quickstart

```bash
# 1) Clone / copy this folder, then:
cp .env.example .env

# 2) Build & run
docker compose up --build -d

# 3) API docs (FastAPI Swagger UI)
# (OpenAPI file also provided at project root)
open http://localhost:8000/docs
```

### cURL Examples

**Full text + metadata**

```bash
curl -X POST "http://localhost:8000/extract/text"   -H "accept: application/json"   -H "Content-Type: multipart/form-data"   -F "file=@/path/to/file.pdf"
```

**Selected pages (0-based indices)**

```bash
curl -X POST "http://localhost:8000/extract/text/pages"   -H "accept: application/json"   -F 'payload={"pages":[0,2,5]};type=application/json'   -F "file=@/path/to/file.pdf"
```

---

## OpenAPI (Standalone)

An explicit OpenAPI spec is available at **`openapi.yaml`**. You can import it into Postman/Insomnia/Stoplight or generate SDKs.

Example import (with `openapi-generator-cli`, requires Java):
```bash
openapi-generator-cli generate -i openapi.yaml -g typescript-fetch -o ./sdk-ts
```

---

## Configuration

Environment variables (`.env`):

| Key | Default | Description |
| --- | --- | --- |
| `APP_NAME` | `pdf-extractor` | App name shown in docs |
| `MAX_FILE_MB` | `20` | Max upload size in MB |
| `LOG_LEVEL` | `info` | Logging level |
| `CORS_ALLOW_ORIGINS` | `*` | Comma-separated origins |

---

## Development (without Docker)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Run tests:

```bash
pip install pytest
pytest -q
```

---

## Notes & Extensions
- **OCR for scanned PDFs**: add `pytesseract` + `pdf2image` and a new `/extract/ocr` endpoint (requires Tesseract & poppler).
- **Table extraction**: integrate `pdfplumber` or **Camelot** (requires Ghostscript).
- **RAG chunking**: split text by paragraphs/tokens; keep page anchors (`get_text("blocks")`) for citations.
- **Security**: size/type validation, rate limiting, and optionally antivirus scanning.
- **Ops**: run behind NGINX for TLS and client max body size, add Prometheus metrics & structured logging.
- **Containers**: use non-root user, set resource limits in `docker-compose.yml` (mem/cpu) for prod.

---

## License
MIT (replace as needed)
