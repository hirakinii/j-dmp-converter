"""FastAPI application for J DMP Converter.

Provides endpoints for:
- File upload and conversion
- Gap analysis (validation)
- Missing field supplementation (two-step conversion)
- Available format listing
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile

from fastapi import FastAPI, HTTPException, UploadFile
from fastapi.responses import FileResponse, JSONResponse

from core.converter import ConversionService
from core.models import DMP, ValidationResult
from web.startup import register_all

# Global conversion service instance — readers/writers are registered at startup
converter = ConversionService()

# Suffix lookup for target formats
_FILE_TYPE_SUFFIX: dict[str, str] = {
    "xlsx": ".xlsx",
    "docx": ".docx",
    "json": ".json",
}

# Direct format-id to suffix mapping (for formats without a mapping definition)
_FORMAT_SUFFIX: dict[str, str] = {
    "cir": ".json",
}


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Register all readers/writers at startup."""
    register_all(converter)
    yield


app = FastAPI(
    title="J DMP Converter",
    description="Japanese DMP format converter with Common Intermediate Representation",
    version="0.1.0",
    lifespan=lifespan,
)


def _get_target_suffix(target_format: str) -> str:
    """Determine the output file suffix from the target format's writer mapping."""
    if target_format in _FORMAT_SUFFIX:
        return _FORMAT_SUFFIX[target_format]
    writer = converter._writers.get(target_format)
    if writer is None:
        return ".xlsx"
    mapping = getattr(writer, "_mapping", None)
    if mapping is not None:
        return _FILE_TYPE_SUFFIX.get(mapping.file_type, ".xlsx")
    return ".xlsx"


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
        raise HTTPException(status_code=400, detail=str(e)) from e


@app.post("/convert", response_model=None)
async def convert_file(
    file: UploadFile,
    source_format: str,
    target_format: str,
) -> FileResponse | JSONResponse:
    """Convert an uploaded file from one agency format to another.

    1. Reads the uploaded file using the source format reader
    2. Validates the CIR for the target format
    3. If complete, writes and returns the output file
    4. If incomplete, returns 422 with the intermediate CIR and missing fields
       so the client can supplement the data via /convert/complete
    """
    suffix = Path(file.filename or "input").suffix or ".xlsx"
    target_suffix = _get_target_suffix(target_format)

    with NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
        content = await file.read()
        tmp_in.write(content)
        tmp_in.flush()
        input_path = Path(tmp_in.name)

    try:
        dmp = converter.read(source_format, input_path)
        validation = converter.validate(dmp, target_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not validation.is_complete:
        return JSONResponse(
            status_code=422,
            content={
                "detail": {
                    "message": "Missing required fields for target format",
                    "missing_fields": [
                        f.model_dump() for f in validation.missing_fields
                    ],
                    "dmp": dmp.model_dump(mode="json"),
                },
            },
        )

    output_path = input_path.with_name(f"converted_{target_format}{target_suffix}")
    result_path = converter.write(dmp, target_format, output_path)

    return FileResponse(
        path=str(result_path),
        filename=f"converted_{target_format}{target_suffix}",
        media_type="application/octet-stream",
    )


@app.post("/convert/complete")
async def convert_complete(
    dmp: DMP,
    target_format: str,
) -> FileResponse:
    """Complete a conversion using a supplemented CIR (JSON DMP).

    Used as the second step when /convert returns 422 with missing fields.
    The client supplements the CIR data and posts it here to get the output file.
    """
    try:
        validation = converter.validate(dmp, target_format)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    if not validation.is_complete:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Still missing required fields",
                "missing_fields": [
                    f.model_dump() for f in validation.missing_fields
                ],
            },
        )

    target_suffix = _get_target_suffix(target_format)

    with NamedTemporaryFile(suffix=target_suffix, delete=False) as tmp_out:
        output_path = Path(tmp_out.name)

    result_path = converter.write(dmp, target_format, output_path)

    return FileResponse(
        path=str(result_path),
        filename=f"converted_{target_format}{target_suffix}",
        media_type="application/octet-stream",
    )
