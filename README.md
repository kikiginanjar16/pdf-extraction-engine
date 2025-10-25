# PDF Extraction API

FastAPI-based service to extract text from PDF files using PyMuPDF. Includes a production-ready Dockerfile.

## Features
- Upload a PDF and get per-page text as JSON
- Saves extracted output to `output.json`
- Health check endpoint
- Dockerized with Python 3.11 slim image

## Requirements
- Python 3.10+
- Or Docker

## Install (local)
```bash
pip install -r requirements.txt
```

## Run (local)
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Endpoints
- `GET /api/v1/health` — service status
- `POST /api/v1/extract` — multipart form file field `file` (PDF). Optional `output_json` query/form field (default: `output.json`).

### Example (curl)
```bash
curl -F "file=@FS.pdf" http://localhost:8000/api/v1/extract > output.json
```

## Docker
Build:
```bash
docker build -t pdf-extraction:latest .
```
Run:
```bash
docker run --rm -p 8000:8000 pdf-extraction:latest
```

## Notes
- Uploaded files are written to `/tmp` inside the container.
- The generated `output.json` is inside the container; mount a volume if you want to persist it:
```bash
docker run --rm -p 8000:8000 -v %CD%:/app pdf-extraction:latest  # Windows PowerShell
# or
docker run --rm -p 8000:8000 -v $(pwd):/app pdf-extraction:latest  # macOS/Linux
```
- Large PDFs can be memory intensive; PyMuPDF processes pages sequentially.


### URL extraction
- `POST /api/v1/extract-url` — JSON body: `{ "url": "https://example.com/file.pdf", "output_json": "output.json" }`

Example:
```bash
curl -X POST http://localhost:8000/api/v1/extract-url \
  -H "Content-Type: application/json" \
  -d '{"url":"https://example.com/file.pdf"}'
```
