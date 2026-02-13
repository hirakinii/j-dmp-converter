"""AMED → CFA 変換の例（Excel → Word）

AMED 形式の Excel ファイルを読み込み、CFA 形式の Word（DOCX）ファイルへ変換します。
ExcelReader と DocxWriter を組み合わせた異なるファイル形式間の変換例です。

使い方:
    uv run python examples/amed_to_cfa_conversion.py <入力AMEDファイル> [出力CFAファイル]

例:
    uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx
    uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx output_cfa.docx
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.docx_writer import DocxWriter
from core.converter import ConversionService


def build_service() -> ConversionService:
    """AMED（読み込み）・CFA（書き出し）アダプタを登録した ConversionService を構築する。"""
    service = ConversionService()

    # AMED アダプタの登録（Excel 読み込み用）
    amed_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/amed_dmp.yaml")
    service.register_reader("amed", ExcelReader(mapping=amed_mapping))

    # CFA アダプタの登録（Word 書き出し用）
    cfa_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/cfa_dmp.yaml")
    service.register_writer(
        "cfa",
        DocxWriter(
            mapping=cfa_mapping,
            template_path=PROJECT_ROOT / "adapters/templates/cfa_template.docx",
        ),
    )

    return service


def main() -> None:
    if len(sys.argv) < 2:
        print(f"使い方: uv run python {sys.argv[0]} <入力AMEDファイル> [出力CFAファイル]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("output_cfa.docx")

    service = build_service()

    # 1. AMED Excel → CIR に変換
    print(f"読み込み中: {input_path}")
    cir = service.read("amed", input_path)
    print(f"  課題名: {cir.project[0].title if cir.project else '(未設定)'}")
    print(f"  連絡先: {cir.contact.name if cir.contact else '(未設定)'}")

    # 2. ギャップ分析（CFA 向け）
    result = service.validate(cir, "cfa")

    if result.is_complete:
        # 3. CIR → CFA Word に書き出し
        service.write(cir, "cfa", output_path)
        print(f"変換完了: {output_path}")
    else:
        print("不足項目:")
        for field in result.missing_fields:
            print(f"  - {field.field_label} ({field.field_path})")
        # 不足があっても書き出しは可能（不足フィールドは空欄になる）
        service.write(cir, "cfa", output_path)
        print(f"変換完了（一部空欄あり）: {output_path}")


if __name__ == "__main__":
    main()
