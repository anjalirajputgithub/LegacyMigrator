"""
This route is the payoff of building analyzer/ and agent/ as separate,
decoupled pieces: it just calls each one and connects the output of one
to the input of the other. Nothing complicated happens here.
"""

from fastapi import APIRouter, HTTPException

from app.analyzer.engine import analyze_code
from app.agent.graph import run_migration
from app.models.schemas import MigrateRequest, MigrateResponse

router = APIRouter()


@router.post("/migrate", response_model=MigrateResponse)
def migrate(request: MigrateRequest) -> MigrateResponse:
    source_bytes = request.code.encode()

    # Step 1: reuse Phase 1's analyzer to know what's actually wrong.
    try:
        findings = analyze_code(source_bytes, request.language)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not findings:
        # Nothing to migrate -- don't waste an LLM call on clean code.
        return MigrateResponse(
            language=request.language,
            original_code=request.code,
            final_code=request.code,
            explanation="No legacy patterns detected -- nothing to migrate.",
            findings_fixed=0,
            revisions=0,
        )

    # Step 2: hand the findings + code to the agent.
    try:
        result = run_migration(request.code, request.language, findings)
    except Exception as e:
        # LLM calls can fail for many reasons (rate limits, network,
        # missing API key) -- surface it clearly instead of a raw 500.
        raise HTTPException(status_code=502, detail=f"Migration agent failed: {e}")

    return MigrateResponse(
        language=request.language,
        original_code=request.code,
        final_code=result["final_code"],
        explanation=result["explanation"],
        findings_fixed=len(findings),
        revisions=result["revisions"],
    )