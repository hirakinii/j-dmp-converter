# J DMP Converter

国内の研究助成機関（AMED, JSPS, METI 等）が要求するデータマネジメントプラン（DMP）様式間の変換ツールです。
**共通中間表現（CIR: Common Intermediate Representation）** を経由するハブ＆スポーク型アーキテクチャにより、様式の追加・変更に柔軟に対応します。

```
AMED  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ JSPS (Excel)
JSPS  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ METI (Excel)
METI  (Excel) ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ AMED (Excel)
CFA   (Word)  ─→ Reader ─→ CIR (JSON) ─→ Writer ─→ CFA  (Word)
```

## 特徴

- **ハブ＆スポーク変換** — 機関同士の直接変換ではなく CIR を経由するため、N 機関の対応に必要なアダプタは N 個（N×N ではない）
- **テンプレート注入方式** — 各機関の公式 Excel/Word 様式をそのままテンプレートとして使用し、セル座標・テンプレートタグへの値注入のみを行うため、様式変更への追従が容易
- **マッピング定義の外部化** — セル座標／テーブル座標と CIR フィールドの対応を YAML で管理。コード変更なしに様式レイアウトの変更に対応可能
- **ギャップ分析** — 変換元にない項目を自動検出し、不足フィールドのリストを返却
- **Web API** — FastAPI による REST API を提供。ファイルアップロード・変換・不足項目補完フローに対応
- **RDA DMP Common Standard 準拠** — CIR は国際標準 maDMP をベースに、e-Rad 課題 ID 等の日本独自フィールドを拡張

## 対応様式

| 機関 | ファイル形式 | Reader | Writer | 備考 |
|------|-------------|--------|--------|------|
| AMED（日本医療研究開発機構） | Excel (XLSX) | o | o | R7 版 DMP 様式 |
| JSPS（日本学術振興会） | Excel (XLSX) | o | o | 科研費 DMP 様式例 |
| METI（経済産業省） | Excel (XLSX) | o | o | 委託研究 DMP 様式 |
| CFA（研究助成プログラム） | Word (DOCX) | o | o | CFA DMP 様式 |

## クイックスタート

### 必要環境

- Python >= 3.11
- [uv](https://docs.astral.sh/uv/) (パッケージマネージャー)

### インストール

```bash
git clone https://github.com/your-org/j-dmp-converter.git
cd j-dmp-converter
uv sync
```

### 使い方（Python API）

```python
from pathlib import Path
from adapters.mapping import load_mapping
from adapters.readers.excel_reader import ExcelReader
from adapters.writers.excel_writer import ExcelWriter
from core.converter import ConversionService

# サービスの構築
service = ConversionService()

# AMED アダプタの登録
amed_mapping = load_mapping(Path("adapters/definitions/amed_dmp.yaml"))
service.register_reader("amed", ExcelReader(mapping=amed_mapping))
service.register_writer(
    "amed",
    ExcelWriter(mapping=amed_mapping, template_path=Path("adapters/templates/amed_template.xlsx")),
)

# JSPS アダプタの登録
jsps_mapping = load_mapping(Path("adapters/definitions/jsps_dmp.yaml"))
service.register_writer(
    "jsps",
    ExcelWriter(mapping=jsps_mapping, template_path=Path("adapters/templates/jsps_template.xlsx")),
)

# AMED → CIR → JSPS 変換
cir = service.read("amed", Path("input_amed.xlsx"))
result = service.validate(cir, "jsps")

if result.is_complete:
    service.write(cir, "jsps", Path("output_jsps.xlsx"))
else:
    print("不足項目:")
    for field in result.missing_fields:
        print(f"  - {field.field_label} ({field.field_path})")
```

### 使い方（Web API）

```bash
# サーバー起動
uv run uvicorn web.app:app --reload

# 利用可能な様式一覧
curl http://localhost:8000/formats

# AMED → JSPS 変換（ファイルアップロード）
curl -X POST "http://localhost:8000/convert?source_format=amed&target_format=jsps" \
  -F "file=@input_amed.xlsx" \
  -o output_jsps.xlsx

# ギャップ分析
curl -X POST "http://localhost:8000/validate?target_format=jsps" \
  -H "Content-Type: application/json" \
  -d @cir.json

# 不足項目補完後の変換完了
curl -X POST "http://localhost:8000/convert/complete?target_format=jsps" \
  -H "Content-Type: application/json" \
  -d @supplemented_cir.json \
  -o output_jsps.xlsx
```

### サンプルスクリプト

`examples/` ディレクトリにサンプルスクリプトを用意しています。

```bash
# AMED → JSPS 基本変換
uv run python examples/basic_conversion.py tests/fixtures/filled_amed_sample.xlsx

# AMED → CFA 変換（Excel → Word）
uv run python examples/amed_to_cfa_conversion.py tests/fixtures/filled_amed_sample.xlsx

# 複数形式への一括変換
uv run python examples/multi_format_conversion.py tests/fixtures/filled_amed_sample.xlsx
```

## プロジェクト構成

```
j-dmp-converter/
├── core/
│   ├── models.py              # CIR データモデル (Pydantic)
│   └── converter.py           # 変換パイプライン統括
├── adapters/
│   ├── mapping.py             # YAML マッピング定義ローダー
│   ├── definitions/           # 各機関のマッピング定義
│   │   ├── amed_dmp.yaml
│   │   ├── jsps_dmp.yaml
│   │   ├── meti_dmp.yaml
│   │   └── cfa_dmp.yaml
│   ├── templates/             # 各機関の様式テンプレート (XLSX/DOCX)
│   ├── readers/
│   │   ├── base.py            # Reader 抽象基底クラス
│   │   ├── excel_reader.py    # Excel Reader
│   │   └── docx_reader.py     # Word (DOCX) Reader
│   └── writers/
│       ├── base.py            # Writer 抽象基底クラス
│       ├── excel_writer.py    # Excel Writer
│       └── docx_writer.py     # Word (DOCX) Writer
├── web/
│   ├── app.py                 # FastAPI アプリケーション
│   └── startup.py             # Reader/Writer 一括登録
├── examples/
│   ├── basic_conversion.py    # AMED → JSPS 基本変換
│   ├── amed_to_cfa_conversion.py  # Excel → Word 変換
│   └── multi_format_conversion.py # 複数形式への一括変換
├── tests/
│   ├── conftest.py            # 共通フィクスチャ (sample_dmp)
│   ├── fixtures/              # テスト用サンプルファイル
│   ├── unit/                  # 単体テスト
│   └── integration/           # 結合テスト
└── docs/
    ├── specifications.md      # ソフトウェア仕様書
    ├── dmps/                  # 各機関の DMP 実ファイル（参考資料）
    └── plans/                 # 実装計画・開発戦略
```

## マッピング定義

各機関の様式と CIR の対応は YAML ファイルで定義します。新しい機関を追加する際は、YAML 定義とテンプレートファイルを追加するだけで対応できます。

```yaml
# adapters/definitions/amed_dmp.yaml (抜粋)
meta:
  format_id: amed
  format_name: "AMED データマネジメントプラン"
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

## CIR データモデル

CIR は [RDA DMP Common Standard (maDMP)](https://github.com/RDA-DMP-Common/RDA-DMP-Common-Standard) をベースとした Pydantic モデルです。

| モデル | 説明 |
|--------|------|
| `DMP` | ルートモデル（タイトル、連絡先、データセット等） |
| `Project` | 研究課題情報（課題名、期間、e-Rad 課題 ID） |
| `Contact` | DMP 連絡先（氏名、メール、所属） |
| `Contributor` | 研究参加者（e-Rad 研究者番号、所属機関コード） |
| `Dataset` | データセット（タイトル、種別、個人情報・機微情報の有無） |
| `Distribution` | 配布・保存情報（アクセス権、リポジトリ、ライセンス） |

## Web API

FastAPI ベースの REST API を提供します。

| エンドポイント | メソッド | 説明 |
|---------------|---------|------|
| `/formats` | GET | 利用可能な入出力様式一覧を取得 |
| `/convert` | POST | ファイルアップロードによる様式変換 |
| `/convert/complete` | POST | 不足項目補完後の変換完了（2 ステップ変換） |
| `/validate` | POST | CIR データのギャップ分析 |

不足項目がある場合の変換フロー:

1. `/convert` にファイルをアップロード → 422 レスポンスで不足項目と CIR を返却
2. クライアントが CIR の不足項目を補完
3. `/convert/complete` に補完済み CIR を送信 → 変換結果ファイルを返却

## テスト

```bash
# 全テスト実行
uv run pytest

# 単体テストのみ
uv run pytest tests/unit/ -v

# 結合テストのみ
uv run pytest tests/integration/ -v
```

現在のテスト結果: **108 テスト全 PASS**

| テストファイル | テスト数 | 内容 |
|---------------|---------|------|
| `test_models.py` | 12 | CIR スキーマバリデーション、日本拡張、JSON 往復 |
| `test_mapping.py` | 5 | YAML ローダー、AMED/JSPS/METI 定義 |
| `test_converter.py` | 6 | 変換サービス登録、パイプライン |
| `test_excel_writer.py` | 13 | AMED/JSPS/METI セル注入、バリデーション |
| `test_excel_reader.py` | 35 | unflatten、DMP 構築、AMED/JSPS/METI 読み込み、ラウンドトリップ |
| `test_docx_reader.py` | 11 | CFA Word 読み込み、ラウンドトリップ |
| `test_docx_writer.py` | 8 | CFA Word 書き出し、バリデーション |
| `test_web_app.py` | 10 | Web API エンドポイント、変換・バリデーション |
| `test_conversion.py` | 8 | AMED→JSPS/METI 変換、フィクスチャ経由フルパイプライン |

## 開発ロードマップ

| フェーズ | 状態 | 目標 |
|---------|------|------|
| **Phase 1: MVP** | **完了** | CIR 定義、Excel Writer/Reader、3 機関対応 |
| Phase 2: Reader 充実 | 計画中 | 表記ゆれ吸収、追加機関対応 |
| **Phase 3: Word 対応** | **完了** | DOCX Reader/Writer（CFA） |
| **Phase 4: Web UI** | **進行中** | FastAPI REST API、不足項目補完フロー |

## 技術スタック

| 用途 | パッケージ |
|------|-----------|
| データモデル | `pydantic` |
| Excel 操作 | `openpyxl` |
| Word 操作 | `python-docx` / `docxtpl` |
| マッピング定義 | `pyyaml` |
| Web API | `fastapi` / `uvicorn` |
| テスト | `pytest` / `pytest-cov` |
| リンター | `ruff` |

## ライセンス

Apache-2.0. See [LICENSE](./LICENSE) for details.
