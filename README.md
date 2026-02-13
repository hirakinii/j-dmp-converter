# J DMP Converter

This tool facilitates conversion between Data Management Plan (DMP) formats required by various Japanese research funding agencies (e.g., AMED, JSPS, METI).
It employs a hub-and-spoke architecture via a **Common Intermediate Representation (CIR: Common Intermediate Representation)**, allowing for flexible adaptation to changes and additions in formats.

```
AMED  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ JSPS (Excel)
JSPS  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ METI (Excel)
METI  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ AMED (Excel)
CFA   (Word)  ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ CFA  (Word)
CIR   (JSON)  ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ CIR  (JSON)
```

## Features

- **Hub-and-Spoke Conversion** — Instead of direct conversion between agencies, all conversions go through CIR. This means only N adapters are needed for N agencies (not N×N).
- **Template Injection Method** — Official Excel/Word formats from each agency are used directly as templates. Values are injected only into cell coordinates and template tags, making it easy to adapt to format changes.
- **Externalization of Mapping Definitions** — Correspondence between cell/table coordinates and CIR fields is managed in YAML. This allows adapting to changes in format layouts without code modification.
- **Gap Analysis** — Automatically detects items not present in the source format and returns a list of missing fields.
- **Web API** — Provides a REST API using FastAPI, supporting file upload, conversion, and missing item supplementation flows.
- **RDA DMP Common Standard Compliance** — CIR is based on the international standard maDMP, with extensions for Japan-specific fields like e-Rad project IDs.

## Supported Formats

| 機関 | ファイル形式 | Reader | Writer | 備考 |
|------|-------------|--------|--------|------|
| AMED（日本医療研究開発機構） | Excel (XLSX) | o | o | R7 版 DMP 様式 |
| JSPS（日本学術振興会） | Excel (XLSX) | o | o | 科研費 DMP 様式例 |
| METI（経済産業省） | Excel (XLSX) | o | o | 委託研究 DMP 様式 |
| CFA（研究助成プログラム） | Word (DOCX) | o | o | CFA DMP 様式 |
| CIR（共通中間表現） | JSON | o | o | CIR の直接読み書き |

## Quick Start

### Prerequisites

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (package manager)

### Installation

```bash
git clone https://github.com/your-org/j-dmp-converter.git
cd j-dmp-converter
uv sync
```

### Usage (Python API)

```python
from pathlib import Path
from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService

# Build the service
service = ConversionService()

# Register AMED adapter
amed_mapping = load_mapping(Path("adapters/definitions/amed_dmp.yaml"))
service.register_reader("amed", ExcelReader(mapping=amed_mapping))
service.register_writer(
    "amed",
    ExcelWriter(mapping=amed_mapping, template_path=Path("adapters/templates/amed_template.xlsx")),
)

# Register JSPS adapter
jsps_mapping = load_mapping(Path("adapters/definitions/jsps_dmp.yaml"))
service.register_writer(
    "jsps",
    ExcelWriter(mapping=jsps_mapping, template_path=Path("adapters/templates/jsps_template.xlsx")),
)

# AMED → CIR → JSPS Conversion
cir = service.read("amed", Path("input_amed.xlsx"))
result = service.validate(cir, "jsps")

if result.is_complete:
    service.write(cir, "jsps", Path("output_jsps.xlsx"))
else:
    print("Missing items:")
    for field in result.missing_fields:
        print(f"  - {field.field_label} ({field.field_path})")
```

### Usage (Web API)

```bash
# Start server
uv run uvicorn web.app:app --reload

# List available formats
curl http://localhost:8000/formats

# AMED → JSPS conversion (file upload)
curl -X POST "http://localhost:8000/convert?source_format=amed&target_format=jsps" 
  -F "file=@input_amed.xlsx" 
  -o output_jsps.xlsx

# Gap analysis
curl -X POST "http://localhost:8000/validate?target_format=jsps" 
  -H "Content-Type: application/json" 
  -d @cir.json

# Conversion complete after supplementing missing items
curl -X POST "http://localhost:8000/convert/complete?target_format=jsps" 
  -H "Content-Type: application/json" 
  -d @supplemented_cir.json 
  -o output_jsps.xlsx
```

### Sample Scripts

Sample scripts are available in the `examples/` directory.

```bash
# Basic AMED → JSPS conversion
uv run python examples/basic_conversion.py tests/fixtures/filled_amed_sample.xlsx

# AMED → CFA conversion (Excel → Word)
uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx

# AMED → CIR JSON → JSPS 変換（中間ファイル経由）
uv run python examples/cir_json_conversion.py tests/fixtures/filled_amed_sample.xlsx

# 複数形式への一括変換
uv run python examples/multi_format_conversion.py tests/fixtures/filled_amed_sample.xlsx
```

## Project Structure

```
j-dmp-converter/
├── core/
│   ├── models.py              # CIR Data Model (Pydantic)
│   └── converter.py           # Conversion Pipeline Management
├── adapters/
│   ├── mapping.py             # YAML Mapping Definition Loader
│   ├── definitions/           # Mapping Definitions for Each Agency
│   │   ├── amed_dmp.yaml
│   │   ├── jsps_dmp.yaml
│   │   ├── meti_dmp.yaml
│   │   └── cfa_dmp.yaml
│   ├── templates/             # Format Templates for Each Agency (XLSX/DOCX)
│   ├── readers/
│   │   ├── base.py            # Reader Abstract Base Class
│   │   ├── excel_reader.py    # Excel Reader
│   │   ├── docx_reader.py     # Word (DOCX) Reader
│   │   └── cir_json_reader.py # CIR JSON Reader
│   └── writers/
│       ├── base.py            # Writer Abstract Base Class
│       ├── excel_writer.py    # Excel Writer
│       ├── docx_writer.py     # Word (DOCX) Writer
│       └── cir_json_writer.py # CIR JSON Writer
├── web/
│   ├── app.py                 # FastAPI Application
│   └── startup.py             # Batch Registration of Readers/Writers
├── examples/
│   ├── basic_conversion.py    # AMED → JSPS 基本変換
│   ├── amed_to_cfa_conversion.py  # Excel → Word 変換
│   ├── cir_json_conversion.py # CIR JSON 経由変換
│   └── multi_format_conversion.py # 複数形式への一括変換
├── tests/
│   ├── conftest.py            # Common Fixtures (sample_dmp)
│   ├── fixtures/              # Sample Files for Testing
│   ├── unit/                  # Unit Tests
│   └── integration/           # Integration Tests
└── docs/
    ├── specifications.md      # Software Specifications
    ├── dmps/                  # Actual DMP files for Each Agency (Reference)
    └── plans/                 # Implementation Plan / Development Strategy
```

## Mapping Definitions

The correspondence between each agency's format and CIR is defined in YAML files. To add a new agency, you only need to add a YAML definition and a template file.

```yaml
# adapters/definitions/amed_dmp.yaml (excerpt)
meta:
  format_id: amed
  format_name: "AMED Data Management Plan"
  file_type: xlsx
  template_sheet: "DMP様式"

mapping:
  project_title:
    cir_path: "project.0.title"
    excel_cell: "D8"
    excel_sheet: "DMP様式"
    required: true

  principal_investigator_name:
    cir_path: "contact.name"
    excel_cell: "D12"
    excel_sheet: "DMP様式"
    required: true
```

## CIR Data Model

CIR is a Pydantic model based on the [RDA DMP Common Standard (maDMP)](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard).

| Model | Description |
|---|---|
| `DMP` | Root model (title, contact, datasets, etc.) |
| `Project` | Research project information (project name, period, e-Rad project ID) |
| `Contact` | DMP contact (name, email, affiliation) |
| `Contributor` | Research participant (e-Rad researcher number, affiliation code) |
| `Dataset` | Dataset (title, type, presence of personal/sensitive information) |
| `Distribution` | Distribution/Storage information (access rights, repository, license) |

## Web API

Provides a FastAPI-based REST API.

| Endpoint | Method | Description |
|---|---|---|
| `/formats` | GET | Get a list of available input/output formats |
| `/convert` | POST | Convert format via file upload |
| `/convert/complete` | POST | Complete conversion after supplementing missing items (2-step conversion) |
| `/validate` | POST | Gap analysis of CIR data |

Conversion flow when there are missing items:

1. Upload file to `/convert` → Returns 422 response with missing items and CIR
2. Client supplements missing items in CIR
3. Send supplemented CIR to `/convert/complete` → Returns converted file

## Tests

```bash
# Run all tests
uv run pytest

# Unit tests only
uv run pytest tests/unit/ -v

# Integration tests only
uv run pytest tests/integration/ -v
```

現在のテスト結果: **121 テスト全 PASS**

| テストファイル | テスト数 | 内容 |
|---------------|---------|------|
| `test_models.py` | 12 | CIR スキーマバリデーション、日本拡張、JSON 往復 |
| `test_mapping.py` | 5 | YAML ローダー、AMED/JSPS/METI 定義 |
| `test_converter.py` | 6 | 変換サービス登録、パイプライン |
| `test_excel_writer.py` | 13 | AMED/JSPS/METI セル注入、バリデーション |
| `test_excel_reader.py` | 35 | unflatten、DMP 構築、AMED/JSPS/METI 読み込み、ラウンドトリップ |
| `test_docx_reader.py` | 11 | CFA Word 読み込み、ラウンドトリップ |
| `test_docx_writer.py` | 8 | CFA Word 書き出し、バリデーション |
| `test_cir_json_reader.py` | 5 | CIR JSON 読み込み、ラウンドトリップ、エラーハンドリング |
| `test_cir_json_writer.py` | 5 | CIR JSON 書き出し、ラウンドトリップ、UTF-8、バリデーション |
| `test_web_app.py` | 13 | Web API エンドポイント、変換・バリデーション、CIR JSON 変換 |
| `test_conversion.py` | 8 | AMED→JSPS/METI 変換、フィクスチャ経由フルパイプライン |

## Development Roadmap

| Phase | Status | Goal |
|---|---|---|
| **Phase 1: MVP** | **Completed** | CIR definition, Excel Writer/Reader, 3 agency support |
| Phase 2: Enhanced Reader | Planned | Absorb notation variations, support additional agencies |
| **Phase 3: Word Support** | **Completed** | DOCX Reader/Writer (CFA) |
| **Phase 4: Web UI** | **In Progress** | FastAPI REST API, missing item supplementation flow |

## Tech Stack

| Purpose | Package |
|---|---|
| Data Model | `pydantic` |
| Excel Operations | `openpyxl` |
| Word Operations | `python-docx` / `docxtpl` |
| Mapping Definitions | `pyyaml` |
| Web API | `fastapi` / `uvicorn` |
| Testing | `pytest` / `pytest-cov` |
| Linter | `ruff` |

## License

Apache-2.0. See [LICENSE](./LICENSE) for details.
