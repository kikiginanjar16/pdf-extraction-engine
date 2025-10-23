from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

from app.models import ExtractTextResponse, ExtractTextByPagesRequest
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
async def extract_text_by_pages(payload: ExtractTextByPagesRequest, file: UploadFile = File(...)):
    data = await file.read()
    if len(data) > settings.MAX_FILE_MB * BYTES_PER_MB:
        raise HTTPException(status_code=413, detail="File too large")

    try:
        extractor = PDFExtractor(data)
        chunks = extractor.extract_text_pages(payload.pages)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"PDF parse failed: {e}")

    return JSONResponse({str(idx): text for idx, text in chunks})

@app.get("/healthz", summary="Health check")
async def healthz():
    return {"status": "ok"}
