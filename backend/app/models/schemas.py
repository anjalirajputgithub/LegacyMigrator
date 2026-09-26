"""
Pydantic models define the API's request/response "shape". This is what
gives you automatic validation (e.g. reject requests missing 'code') and
automatic docs at /docs -- you get both for free just by declaring types
here.
"""

from typing import Literal
from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    code: str = Field(..., description="The source code to analyze", min_length=1)
    language: Literal["python", "javascript"] = Field(
        ..., description="Which language grammar/rules to use"
    )


class Finding(BaseModel):
    line: int
    rule_id: str
    severity: Literal["info", "warning", "error"]
    message: str
    snippet: str


class AnalyzeResponse(BaseModel):
    language: str
    finding_count: int
    findings: list[Finding]
