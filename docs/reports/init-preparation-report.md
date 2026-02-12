# 初期構築レポート

**プロジェクト:** J DMP Converter
**作成日:** 2026年2月12日
**フェーズ:** フェーズ1 MVP — 初期スカフォールド完了

---

## 1. 実施内容

### 1.1 プロジェクト設定

| 項目 | 内容 |
| --- | --- |
| パッケージマネージャー | `uv` |
| Python バージョン | >= 3.11 |
| 設定ファイル | `pyproject.toml`（`dependency-groups` で dev 依存を管理） |

**主要な依存パッケージ:**

| パッケージ | 用途 |
| --- | --- |
| `pydantic[email]` | CIR データモデル定義・バリデーション |
| `openpyxl` | Excel (XLSX) の読み書き |
| `python-docx` | Word (DOCX) の読み込み（フェーズ3で使用） |
| `docxtpl` | Word テンプレートへの書き出し（フェーズ3で使用） |
| `pyyaml` | マッピング定義ファイルの読み込み |
| `fastapi` / `uvicorn` | Web API サーバー |
| `pytest` / `pytest-cov` | テスト・カバレッジ |
| `httpx` | API テスト用クライアント |
| `ruff` | リンター |

### 1.2 ディレクトリ構成

```text
j-dmp-converter/
├── pyproject.toml
├── uv.lock
├── core/
│   ├── __init__.py
│   ├── models.py            # CIR (Pydantic モデル)
│   └── converter.py         # 変換パイプライン統括
├── adapters/
│   ├── __init__.py
│   ├── mapping.py           # YAML マッピング定義ローダー
│   ├── definitions/
│   │   ├── amed_dmp.yaml    # AMED 様式マッピング定義
│   │   └── jsps_dmp.yaml    # JSPS 様式マッピング定義
│   ├── templates/           # 様式テンプレートファイル（未配置）
│   │   └── .gitkeep
│   ├── readers/
│   │   ├── __init__.py
│   │   ├── base.py          # Reader 抽象基底クラス
│   │   └── excel_reader.py  # Excel Reader（骨格）
│   └── writers/
│       ├── __init__.py
│       ├── base.py          # Writer 抽象基底クラス
│       └── excel_writer.py  # Excel Writer（テンプレート注入）
├── web/
│   ├── __init__.py
│   └── app.py               # FastAPI アプリケーション
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # 共通フィクスチャ (sample_dmp)
│   ├── fixtures/            # テスト用サンプルファイル（未配置）
│   │   └── .gitkeep
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_models.py       # CIR スキーマバリデーション
│   │   ├── test_mapping.py      # マッピングローダー
│   │   ├── test_converter.py    # 変換サービス
│   │   └── test_excel_writer.py # Excel Writer
│   └── integration/
│       └── __init__.py
└── docs/
    ├── specifications.md
    ├── plans/
    └── reports/
```

### 1.3 CIR データモデル (`core/models.py`)

RDA DMP Common Standard (maDMP) のスキーマ定義をMCPサーバー経由で参照し、Pydantic v2 モデルとして実装した。

**主要エンティティ:**

| モデル | 説明 | maDMP 必須フィールド |
| --- | --- | --- |
| `DMP` | ルートモデル | `title`, `dmp_id`, `created`, `modified`, `language`, `ethical_issues_exist`, `contact`, `dataset` |
| `Project` | 研究課題情報 | `title` |
| `Contact` | DMP 連絡先 | `contact_id`, `mbox`, `name` |
| `Contributor` | 研究参加者 | `contributor_id`, `name`, `role` |
| `Dataset` | データセット | `title`, `dataset_id`, `personal_data`, `sensitive_data` |
| `Distribution` | 配布・保存情報 | `title`, `data_access` |
| `Host` | リポジトリ情報 | `title`, `url` |

**日本独自の拡張フィールド:**

| モデル | フィールド | 説明 |
| --- | --- | --- |
| `Project` | `erad_project_id` | e-Rad 課題 ID |
| `Project` | `jglobal_id` | J-Global ID |
| `Contributor` | `erad_researcher_id` | e-Rad 研究者番号 |
| `Contributor` | `institution_code` | 所属機関コード |

**ギャップ分析用モデル:**

| モデル | 説明 |
| --- | --- |
| `ValidationResult` | バリデーション結果（`is_complete` + `missing_fields`） |
| `MissingField` | 不足フィールド情報（`field_path`, `field_label`, `required_by`） |

### 1.4 テスト結果

```
26 passed in 0.33s
```

| テストファイル | テスト数 | 内容 |
| --- | --- | --- |
| `test_models.py` | 10 | スキーマバリデーション、日本拡張、JSON往復変換 |
| `test_mapping.py` | 3 | YAML ローダー、AMED/JSPS 定義の読み込み |
| `test_converter.py` | 6 | サービス登録、未知フォーマットのエラー、パイプライン |
| `test_excel_writer.py` | 5 | セル注入（連絡先名、課題名、データセット名）、バリデーション |
| **合計** | **26** | **全テスト通過** |

---

## 2. 現状の制約事項

| 項目 | 状態 | 説明 |
| --- | --- | --- |
| `ExcelReader._build_dmp` | `NotImplementedError` | フラットなセル値からネスト CIR への組み立てロジックが未実装 |
| テンプレートファイル | 未配置 | `adapters/templates/` に各機関の様式ファイルが必要 |
| マッピング定義のセル座標 | 仮値 | 実際の様式ファイルのレイアウトに合わせた調整が必要 |
| FastAPI Reader/Writer 登録 | 未接続 | `web/app.py` でアダプタがまだ登録されていない |
| 結合テスト | 未作成 | `tests/integration/` が空 |

---

## 3. 次のステップ

実装計画のフェーズ1 MVP完成に向けた残タスクを優先度順に示す。

### 3.1 直近の作業（フェーズ1 残タスク）

1. **実テンプレートファイルの解析とマッピング座標の確定**
   - `docs/dmps/` にある各機関の実ファイル（`amed-dmp.xlsx`, `jsps-dmp.xlsx` 等）を解析
   - セル座標をマッピング定義 YAML に反映

2. **ExcelReader の完全実装**
   - `_build_dmp` メソッドによるフラット値→CIR構造の変換ロジック
   - AMED 様式の読み込み→CIR のラウンドトリップテスト

3. **FastAPI アダプタ登録とエンドポイント結合**
   - 起動時に Reader/Writer を自動登録する仕組み
   - `/convert` エンドポイントの結合動作確認

4. **結合テスト**
   - AMED 入力 → CIR → AMED 出力のラウンドトリップ
   - AMED 入力 → CIR → JSPS 出力の異種変換

### 3.2 後続フェーズ

| フェーズ | 目標 | 主な作業 |
| --- | --- | --- |
| フェーズ2 | Reader エンジン充実 | 複数機関の Excel Reader、表記ゆれ吸収 |
| フェーズ3 | Word (DOCX) 対応 | `docxtpl` Writer、`python-docx` Reader |
| フェーズ4 | UI/UX 完成 | 不足項目補完 Web フォーム、e-Rad 連携 |
