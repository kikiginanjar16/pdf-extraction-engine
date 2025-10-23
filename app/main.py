import httpx
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.models import ExtractTextResponse, ExtractTextByPagesRequest, ExtractFromUrlRequest, ExtractFromUrlByPagesRequest
from app.settings import settings
from app.extractors.pdf_extractor import PDFExtractor

app = FastAPI(title=settings.APP_NAME)

# CORS
origins = [o.strip() for o in settings.CORS_ALLOW_ORIGINS.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BYTES_PER_MB = 1024 * 1024

MAX_DOWNLOAD_MB = settings.MAX_FILE_MB
BYTES_PER_MB = 1024 * 1024  # keep same constant

async def _fetch_pdf_bytes(url: str) -> bytes:
    # Basic validation
    parsed = httpx.URL(url)
    if parsed.scheme not in ("https", "http"):
        raise HTTPException(status_code=400, detail="URL must start with http or https")
    timeout = httpx.Timeout(20.0, connect=10.0)
    headers = {"User-Agent": f"{settings.APP_NAME}/1.0"}
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
            # Stream to enforce size limit
            resp = await client.get(url)
            ct = resp.headers.get("content-type", "").lower()
            if "pdf" not in ct and not str(url).lower().endswith(".pdf"):
                # Not strictly fatal because some servers mislabel, but we enforce
                raise HTTPException(status_code=400, detail=f"URL does not appear to be a PDF (content-type={ct})")
            # Enforce size if Content-Length advertised
            cl = resp.headers.get("content-length")
            if cl and cl.isdigit():
                if int(cl) > MAX_DOWNLOAD_MB * BYTES_PER_MB:
                    raise HTTPException(status_code=413, detail=f"Remote file too large. Max {MAX_DOWNLOAD_MB}MB")
            data = resp.content
            if len(data) > MAX_DOWNLOAD_MB * BYTES_PER_MB:
                raise HTTPException(status_code=413, detail=f"Remote file too large. Max {MAX_DOWNLOAD_MB}MB")
            if resp.status_code >= 400:
                raise HTTPException(status_code=resp.status_code, detail=f"Fetch failed with status {resp.status_code}")
            return data
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"Download error: {e}")

@app.post("/extract/text", response_model=ExtractTextResponse, summary="Extract full text & metadata")
async def extract_text(file: UploadFile = File(...)):
    if file.content_type not in {"application/pdf", "application/octet-stream"}:
        raise HTTPException(status_code=400, detail="File must be a PDF")

    data = await file.read()
    if len(data) > settings.MAX_FILE_MB * BYTES_PER_MB:
        raise HTTPException(status_code=413, detail=f"File too large. Max {settings.MAX_FILE_MB}MB")

    try:
        extractor = PDFExtractor(data)
        meta = extractor.meta()
        text = extractor.extract_text_all()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")

    return ExtractTextResponse(
        filename=file.filename,
        pages=meta["pages"],
        title=meta.get("title"),
        author=meta.get("author"),
        subject=meta.get("subject"),
        keywords=meta.get("keywords"),
        text=text,
    )

@app.post("/extract/text/pages", summary="Extract text by page indices (0-based)")
async def extract_text_by_pages(payload: str = Form(...), file: UploadFile = File(...)):
    import json
    from pydantic import ValidationError

    data = await file.read()
    if len(data) > settings.MAX_FILE_MB * BYTES_PER_MB:
        raise HTTPException(status_code=413, detail="File too large")

    # Parse JSON string from multipart field
    try:
        model = ExtractTextByPagesRequest.model_validate_json(payload)
    except (ValidationError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid payload JSON: {e}")

    try:
        extractor = PDFExtractor(data)
        chunks = extractor.extract_text_pages(model.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")

    return JSONResponse({str(idx): text for idx, text in chunks})

@app.get("/healthz", summary="Health check")
async def healthz():
    return {"status": "ok"}("/healthz", summary="Health check")
async def healthz():
    return {"status": "ok"}


@app.post("/extract/text/url", response_model=ExtractTextResponse, summary="Extract full text & metadata from PDF URL")
async def extract_text_from_url(payload: ExtractFromUrlRequest):
    data = await _fetch_pdf_bytes(payload.url)
    try:
        extractor = PDFExtractor(data)
        meta = extractor.meta()
        text = extractor.extract_text_all()
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")

    return ExtractTextResponse(
        filename=payload.url.split("/")[-1] or "remote.pdf",
        pages=meta["pages"],
        title=meta.get("title"),
        author=meta.get("author"),
        subject=meta.get("subject"),
        keywords=meta.get("keywords"),
        text=text,
    )

@app.post("/extract/text/pages/url", summary="Extract text by page indices (0-based) from PDF URL")
async def extract_text_by_pages_from_url(payload: ExtractFromUrlByPagesRequest):
    data = await _fetch_pdf_bytes(payload.url)
    try:
        extractor = PDFExtractor(data)
        chunks = extractor.extract_text_pages(payload.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")
    return JSONResponse({str(idx): text for idx, text in chunks})

