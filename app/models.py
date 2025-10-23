from pydantic import BaseModel, Field
from typing import List, Optional

class ExtractTextResponse(BaseModel):
    filename: str
    pages: int
    title: Optional[str] = None
    author: Optional[str] = None
    subject: Optional[str] = None
    keywords: Optional[str] = None
    text: str = Field(description="Full concatenated text from all pages")

class ExtractTextByPagesRequest(BaseModel):
    pages: List[int] = Field(description="0-based page indices to extract")
