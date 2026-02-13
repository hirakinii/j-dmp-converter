"""AMED → JSPS 変換の基本例

README「クイックスタート」に対応するサンプルコードです。
AMED 形式の Excel ファイルを読み込み、JSPS 形式へ変換します。

使い方:
    uv run python examples/basic_conversion.py <入力AMEDファイル> [出力JSPSファイル]
"""

from __future__ import annotations

import sys
from pathlib import Path

# プロジェクトルートを sys.path に追加
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService


def build_service() -> ConversionService:
    """AMED・JSPS アダプタを登録した ConversionService を構築する。"""
    service = ConversionService()

    # AMED アダプタの登録
    amed_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/amed_dmp.yaml")
    service.register_reader("amed", ExcelReader(mapping=amed_mapping))
    service.register_writer(
        "amed",
        ExcelWriter(
            mapping=amed_mapping,
            template_path=PROJECT_ROOT / "adapters/templates/amed_template.xlsx",
        ),
    )

    # JSPS アダプタの登録
    jsps_mapping = load_mapping(PROJECT_ROOT / "adapters/definitions/jsps_dmp.yaml")
    service.register_reader("jsps", ExcelReader(mapping=jsps_mapping))
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
        print(f"使い方: uv run python {sys.argv[0]} <入力AMEDファイル> [出力JSPSファイル]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) >= 3 else Path("output_jsps.xlsx")

    service = build_service()

    # 1. AMED Excel → CIR に変換
    print(f"読み込み中: {input_path}")
    cir = service.read("amed", input_path)
    print(f"  課題名: {cir.project[0].title if cir.project else '(未設定)'}")
    print(f"  連絡先: {cir.contact.name if cir.contact else '(未設定)'}")

    # 2. ギャップ分析（JSPS 向け）
    result = service.validate(cir, "jsps")

    if result.is_complete:
        # 3. CIR → JSPS Excel に書き出し
        service.write(cir, "jsps", output_path)
        print(f"変換完了: {output_path}")
    else:
        print("不足項目:")
        for field in result.missing_fields:
            print(f"  - {field.field_label} ({field.field_path})")
        # 不足があっても書き出しは可能（不足フィールドは空欄になる）
        service.write(cir, "jsps", output_path)
        print(f"変換完了（一部空欄あり）: {output_path}")


if __name__ == "__main__":
    main()
