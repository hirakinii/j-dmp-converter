"""複数機関間の変換例

AMED・JSPS・METI の 3 機関すべてのアダプタを登録し、
任意の機関間で DMP を変換するサンプルコードです。

使い方:
    uv run python examples/multi_format_conversion.py <変換元形式> <変換先形式> <入力ファイル> [出力ファイル]

    変換元形式 / 変換先形式: amed, jsps, meti

例:
    uv run python examples/multi_format_conversion.py amed meti input_amed.xlsx output_meti.xlsx
    uv run python examples/multi_format_conversion.py jsps amed input_jsps.xlsx
"""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService

# 対応機関の定義
FORMATS = {
    "amed": {
        "definition": "adapters/definitions/amed_dmp.yaml",
        "template": "adapters/templates/amed_template.xlsx",
    },
    "jsps": {
        "definition": "adapters/definitions/jsps_dmp.yaml",
        "template": "adapters/templates/jsps_template.xlsx",
    },
    "meti": {
        "definition": "adapters/definitions/meti_dmp.yaml",
        "template": "adapters/templates/meti_template.xlsx",
    },
}


def build_service() -> ConversionService:
    """全機関のアダプタを登録した ConversionService を構築する。"""
    service = ConversionService()

    for format_id, paths in FORMATS.items():
        mapping = load_mapping(PROJECT_ROOT / paths["definition"])
        service.register_reader(format_id, ExcelReader(mapping=mapping))
        service.register_writer(
            format_id,
            ExcelWriter(
                mapping=mapping,
                template_path=PROJECT_ROOT / paths["template"],
            ),
        )

    return service


def main() -> None:
    format_ids = ", ".join(FORMATS.keys())

    if len(sys.argv) < 4:
        print(
            f"使い方: uv run python {sys.argv[0]} <変換元形式> <変換先形式> <入力ファイル> [出力ファイル]\n"
            f"  変換元形式 / 変換先形式: {format_ids}"
        )
        sys.exit(1)

    source_format = sys.argv[1]
    target_format = sys.argv[2]
    input_path = Path(sys.argv[3])
    output_path = (
        Path(sys.argv[4])
        if len(sys.argv) >= 5
        else Path(f"output_{target_format}.xlsx")
    )

    if source_format not in FORMATS:
        print(f"エラー: 未対応の変換元形式 '{source_format}' (対応: {format_ids})")
        sys.exit(1)
    if target_format not in FORMATS:
        print(f"エラー: 未対応の変換先形式 '{target_format}' (対応: {format_ids})")
        sys.exit(1)

    service = build_service()

    # convert() で読み込み → ギャップ分析 → 書き出しを一括実行
    print(f"変換: {source_format.upper()} → {target_format.upper()}")
    print(f"入力: {input_path}")

    written, result = service.convert(source_format, target_format, input_path, output_path)

    if result.is_complete:
        print(f"変換完了: {written}")
    else:
        print(f"変換完了（一部空欄あり）: {written}")
        print("不足項目:")
        for field in result.missing_fields:
            print(f"  - {field.field_label} ({field.field_path})")


if __name__ == "__main__":
    main()
