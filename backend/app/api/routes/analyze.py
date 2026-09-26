"""
The HTTP layer. Notice this file is thin -- it does almost nothing except:
validate the request (handled automatically by the pydantic model),
call analyze_code(), and shape the response. All the real logic lives in
analyzer/engine.py. This separation matters: if you ever add a CLI or a
batch-processing job later, they call analyze_code() directly and never
touch this file.
"""

from fastapi import APIRouter, HTTPException

from app.analyzer.engine import analyze_code
from app.models.schemas import AnalyzeRequest, AnalyzeResponse

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        findings = analyze_code(request.code.encode(), request.language)
    except ValueError as e:
        # Shouldn't normally happen since pydantic's Literal type already
        # restricts `language`, but this is a safety net if that ever
        # changes -- always handle the "unsupported input" case explicitly
        # rather than letting an unhandled exception produce a raw 500.
        raise HTTPException(status_code=400, detail=str(e))

    return AnalyzeResponse(
        language=request.language,
        finding_count=len(findings),
        findings=findings,
    )
