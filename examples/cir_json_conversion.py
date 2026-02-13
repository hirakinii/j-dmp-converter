"""AMED → CIR JSON → JSPS 変換の例（CIR 中間ファイル経由）

AMED 形式の Excel ファイルを CIR JSON 形式で保存し、
その CIR JSON ファイルを読み込んで JSPS 形式の Excel へ変換します。
中間表現を JSON ファイルとして保存・確認・編集できるワークフローの例です。

使い方:
    uv run python examples/cir_json_conversion.py <入力AMEDファイル> [CIR出力先] [JSPS出力先]

例:
    uv run python examples/cir_json_conversion.py tests/fixtures/filled_amed_sample.xlsx
    uv run python examples/cir_json_conversion.py input.xlsx cir.json out.xlsx
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.mapping import load_mapping
from adapters.readers.cir_json_reader import CirJsonReader
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.cir_json_writer import CirJsonWriter
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService


def build_service() -> ConversionService:
    """AMED・CIR・JSPS アダプタを登録した ConversionService を構築する。"""
    service = ConversionService()

    # AMED アダプタの登録（Excel 読み込み用）
    amed_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/amed_dmp.yaml")
    service.register_reader("amed", ExcelReader(mapping=amed_mapping))

    # CIR JSON アダプタの登録
    service.register_reader("cir", CirJsonReader())
    service.register_writer("cir", CirJsonWriter())

    # JSPS アダプタの登録（Excel 書き出し用）
    jsps_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/jsps_dmp.yaml")
    service.register_writer(
        "jsps",
        ExcelWriter(
            mapping=jsps_mapping,
            template_path=PROJECT_ROOT / "adapters/templates/jsps_template.xlsx",
        ),
    )

    return service


def main() -> None:
    if len(sys.argv) < 2:
        print(
            f"使い方: uv run python {sys.argv[0]} "
            "<入力AMEDファイル> [CIR出力先] [JSPS出力先]"
        )
        sys.exit(1)

    input_path = Path(sys.argv[1])
    cir_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("output_cir.json")
    jsps_path = Path(sys.argv[3]) if len(sys.argv) >= 4 else Path("output_jsps.xlsx")

    service = build_service()

    # ── ステップ 1: AMED Excel → CIR JSON ──
    print(f"読み込み中: {input_path}")
    cir = service.read("amed", input_path)
    print(f"  課題名: {cir.project[0].title if cir.project else '(未設定)'}")
    print(f"  連絡先: {cir.contact.name}")

    service.write(cir, "cir", cir_path)
    print(f"CIR JSON 出力完了: {cir_path}")

    # ── ステップ 2: CIR JSON → JSPS Excel ──
    print(f"\nCIR JSON 読み込み中: {cir_path}")
    cir_loaded = service.read("cir", cir_path)

    result = service.validate(cir_loaded, "jsps")

    if result.is_complete:
        service.write(cir_loaded, "jsps", jsps_path)
        print(f"JSPS 変換完了: {jsps_path}")
    else:
        print("不足項目:")
        for field in result.missing_fields:
            print(f"  - {field.field_label} ({field.field_path})")
        service.write(cir_loaded, "jsps", jsps_path)
        print(f"JSPS 変換完了（一部空欄あり）: {jsps_path}")


if __name__ == "__main__":
    main()
