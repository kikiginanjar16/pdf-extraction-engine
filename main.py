import json
from typing import Optional

import fitz  # PyMuPDF
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, AnyUrl
import tempfile
import os
import requests

class UrlIn(BaseModel):
    url: AnyUrl
    output_json: Optional[str] = "output.json"

app = FastAPI(title="PDF Extraction API")

def extract_large_pdf(file_path: str, output_json: str = "output.json") -> list[dict]:
    doc = fitz.open(file_path)
    data: list[dict] = []

    for i, page in enumerate(doc):
        text = page.get_text("text")
        data.append({"page": i + 1, "text": text})
        if (i + 1) % 50 == 0:
            print(f"Processed {i + 1}/{len(doc)} pages")

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Extraction complete: {len(doc)} pages saved to {output_json}")
    return data


@app.get("/api/v1/health")
def health():
    return {"status": "ok"}


@app.post("/api/v1/extract")
async def extract(file: UploadFile = File(...), output_json: Optional[str] = "output.json"):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    try:
        # Save uploaded file to a temporary path
        temp_path = f"/tmp/{file.filename}"
        content = await file.read()
        with open(temp_path, "wb") as f:
            f.write(content)

        data = extract_large_pdf(temp_path, output_json=output_json or "output.json")
        return JSONResponse(content=data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/extract-url")
async def extract_url(payload: UrlIn):
    try:
        # Download the PDF
        resp = requests.get(str(payload.url), timeout=60)
        if resp.status_code != 200:
            raise HTTPException(status_code=400, detail=f"Failed to download URL: {resp.status_code}")

        content_type = resp.headers.get("content-type", "").lower()
        if "pdf" not in content_type and not str(payload.url).lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="URL does not appear to be a PDF")

        # Write to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(resp.content)
            temp_path = tmp.name

        data = extract_large_pdf(temp_path, output_json=payload.output_json or "output.json")
        return JSONResponse(content=data)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)
        except Exception:
            pass

# If you want to run locally without uvicorn CLI, uncomment below:
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


