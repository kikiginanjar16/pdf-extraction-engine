from typing import List, Tuple
import fitz  # PyMuPDF

class PDFExtractor:
    def __init__(self, data: bytes):
        self.doc = fitz.open(stream=data, filetype="pdf")

    def meta(self) -> dict:
        m = self.doc.metadata or {}
        return {
            "title": m.get("title"),
            "author": m.get("author"),
            "subject": m.get("subject"),
            "keywords": m.get("keywords"),
            "pages": len(self.doc),
        }

    def extract_text_all(self) -> str:
        parts: List[str] = []
        for page in self.doc:
            text = page.get_text("text") or ""
            parts.append(text)
        return "\n\n".join(parts).strip()

    def extract_text_pages(self, page_indices: List[int]) -> List[Tuple[int, str]]:
        out = []
        for idx in page_indices:
            if 0 <= idx < len(self.doc):
                text = self.doc[idx].get_text("text") or ""
                out.append((idx, text))
        return out
