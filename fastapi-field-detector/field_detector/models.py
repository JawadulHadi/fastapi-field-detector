from typing import Literal

from pydantic import BaseModel, Field

FieldType = Literal['signature', 'initials', 'date', 'name', 'checkbox', 'text']


class Box(BaseModel):
    """Normalised page coordinates: 0..1, origin at the top-left."""
    x: float
    y: float
    w: float
    h: float


class DetectedField(BaseModel):
    type: FieldType
    role_key: str
    page: int = Field(ge=1)
    box: Box
    label: str
    required: bool = True
    confidence: float = Field(ge=0, le=1)
    reason: str
    source: Literal['rule', 'llm', 'rule-guess'] = 'rule'


class DetectResponse(BaseModel):
    pages: int
    fields: list[DetectedField]
    warnings: list[str] = []
