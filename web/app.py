"""FastAPI application for J DMP Converter.

Provides endpoints for:
- File upload and conversion
- Gap analysis (validation)
- Available format listing
"""

from __future__ import annotations

from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse

from core.converter import ConversionService
from core.models import DMP, ValidationResult

app = FastAPI(
    title="J DMP Converter",
    description="Japanese DMP format converter with Common Intermediate Representation",
    version="0.1.0",
)

# Global conversion service instance — readers/writers are registered at startup
converter = ConversionService()


@app.get("/formats")
def list_formats() -> dict[str, list[str]]:
    """List all available input and output formats."""
    return {
        "readers": converter.available_readers(),
        "writers": converter.available_writers(),
    }


@app.post("/validate", response_model=ValidationResult)
async def validate_dmp(dmp: DMP, target_format: str) -> ValidationResult:
    """Perform gap analysis between CIR data and a target format.

    Accepts a JSON DMP body and returns missing fields for the target format.
    """
    try:
        return converter.validate(dmp, target_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/convert")
async def convert_file(
    file: UploadFile,
    source_format: str,
    target_format: str,
) -> FileResponse:
    """Convert an uploaded file from one agency format to another.

    1. Reads the uploaded file using the source format reader
    2. Validates the CIR for the target format
    3. Writes the output file using the target format writer
    """
    suffix = Path(file.filename or "input").suffix or ".xlsx"

    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        tmp_in.flush()
        input_path = Path(tmp_in.name)

    output_path = input_path.with_name(f"converted_{target_format}{suffix}")

    try:
        result_path, validation = converter.convert(
            source_format, target_format, input_path, output_path
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    if not validation.is_complete:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Missing required fields for target format",
                "missing_fields": [f.model_dump() for f in validation.missing_fields],
            },
        )

    return FileResponse(
        path=str(result_path),
        filename=f"converted_{target_format}{suffix}",
        media_type="application/octet-stream",
    )
