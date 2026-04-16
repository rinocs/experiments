from pydantic import BaseModel, Field
from typing import List, Literal

class GradeResult(BaseModel):
    relevance: Literal["relevant", "irrelevant"]
    reason: str = Field(..., min_length=1)

class SourceItem(BaseModel):
    source: str
    chunk: int | None = None
    page: int | None = None

class ChatResponse(BaseModel):
    answer: str
    sources: List[SourceItem]
    confidence: float = Field(..., ge=0, le=1)
