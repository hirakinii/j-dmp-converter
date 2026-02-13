# examples ディレクトリ

このディレクトリには、DMP Converter の様々な使用例を示すサンプルスクリプトが格納されています。

## amed_to_cfa_conversion.py

AMED → CFA 変換の例（Excel → Word）

AMED 形式の Excel ファイルを読み込み、CFA 形式の Word（DOCX）ファイルへ変換します。
ExcelReader と DocxWriter を組み合わせた異なるファイル形式間の変換例です。

使い方:

```sh
uv run python examples/amed_to_cfa_conversion.py <入力AMEDファイル> [出力CFAファイル]
```

例:

```sh
uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx
uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx output_cfa.docx
```

## basic_conversion.py

AMED → JSPS 変換の基本例

README「クイックスタート」に対応するサンプルコードです。
AMED 形式の Excel ファイルを読み込み、JSPS 形式へ変換します。

使い方:

```sh
uv run python examples/basic_conversion.py <入力AMEDファイル> [出力JSPSファイル]
```

## cir_json_conversion.py

AMED → CIR JSON → JSPS 変換の例（CIR 中間ファイル経由）

AMED 形式の Excel ファイルを CIR JSON 形式で保存し、
その CIR JSON ファイルを読み込んで JSPS 形式の Excel へ変換します。
中間表現を JSON ファイルとして保存・確認・編集できるワークフローの例です。

使い方:

```sh
uv run python examples/cir_json_conversion.py <入力AMEDファイル> [CIR出力先] [JSPS出力先]
```

例:

```sh
uv run python examples/cir_json_conversion.py tests/fixtures/filled_amed_sample.xlsx
uv run python examples/cir_json_conversion.py input.xlsx cir.json out.xlsx
```

## multi_format_conversion.py

複数機関間の変換例

AMED・JSPS・METI の 3 機関すべてのアダプタを登録し、
任意の機関間で DMP を変換するサンプルコードです。

使い方:

```sh
uv run python examples/multi_format_conversion.py <変換元形式> <変換先形式> <入力ファイル> [出力ファイル]
# 変換元形式 / 変換先形式: amed, jsps, meti
```

例:
```sh
uv run python examples/multi_format_conversion.py amed meti input_amed.xlsx output_meti.xlsx
uv run python examples/multi_format_conversion.py jsps amed input_jsps.xlsx
```
