# J DMP Converter ソフトウェア仕様書 (SRS)

**バージョン:** 1.0
**作成日:** 2026年2月12日

## 1. はじめに

### 1.1 背景と目的

国内の研究助成機関（AMED, JSPS, JST, METI, ERCA, CFA, MHLW等）が要求するデータマネジメントプラン（DMP）およびメタデータ様式は統一されていません。研究者は助成機関ごとに異なるフォーマット（Excel/Word）への転記作業に忙殺されています。

本システム「J DMP Converter」は、これらの**多様な様式を包括的に扱うコンバーター**です。特定の様式から別の様式への直接変換（）ではなく、**共通中間表現（CIR）**を経由するハブ＆スポーク型アーキテクチャを採用することで、拡張性と保守性を担保し、研究者の事務負担を劇的に軽減することを目的とします。

### 1.2 スコープ

* **入力:** 各助成機関指定のExcel (XLSX) および Word (DOCX) ファイル。
* **処理:** 共通中間表現 (CIR) への正規化、不足項目のバリデーション、ユーザーによる補完。
* **出力:** 各助成機関指定の最新様式へのデータ流し込みとファイル生成。

---

## 2. システムアーキテクチャ

本システムは、入力と出力を「共通中間表現（CIR）」で分離し、テンプレートエンジンを用いて様式の変更に柔軟に対応する構造をとります。

### 2.1 全体構成図 (概念)

```mermaid
graph LR
    Input[入力ファイル<br>(Excel/Word)] --> Reader[Reader Engine<br>(Parser)]
    Reader --> CIR[共通中間表現<br>(CIR: JSON Model)]
    
    UserInput[Web UI / Wizard] -- 補完・修正 --> CIR
    
    CIR --> Writer[Writer Engine<br>(Template Injector)]
    
    Template[様式テンプレート<br>(Excel/Word)] -.-> Writer
    Writer --> Output[出力ファイル<br>(指定様式)]

```

### 2.2 コアコンポーネント

| コンポーネント | 役割 | 技術スタック |
| --- | --- | --- |
| **CIR (Common Intermediate Representation)** | システムの中核となるデータモデル。RDA maDMP標準にe-Rad等の日本独自仕様を加えたJSONスキーマ。 | `Pydantic` |
| **Reader (Importer)** | 各機関のファイルを読み込み、CIRへマッピング・変換する。表記ゆれを吸収するロジックを含む。 | `openpyxl`, `python-docx` |
| **Writer (Exporter)** | CIRのデータをターゲット機関のテンプレートファイルへ書き込む。デザイン情報（フォント等）はコードに含めず、テンプレート側に持たせる。 | `openpyxl`, `docxtpl` |
| **Web API / UI** | ファイルのアップロード、不足情報の入力フォーム、変換実行のインターフェース。 | `FastAPI`, `React` / `Vue.js` |

---

## 3. データモデル仕様 (CIR)

データモデルは **RDA DMP Common Standard** をベースとし、階層構造を持ちます。

### 3.1 主要エンティティ構造

* **Project:** 研究課題情報（課題名、期間、助成機関IDなど）
    * *拡張:* e-Rad課題ID、J-Global ID

* **Person (Contributor):** 研究代表者、データ管理者
    * *拡張:* e-Rad研究者番号、所属機関コード

* **Dataset:** データセット情報（タイトル、データ種別、公開可否、機密性）
* **Distribution:** 配布・保存情報（リポジトリURL、ライセンス、ファイル形式）

### 3.2 マッピング定義の外部化

ソースコードの変更を避けるため、各機関の様式とCIRの対応関係はYAML/JSONファイルで定義します。

```yaml
# マッピング定義例 (amed_mapping.yaml)
mapping:
  principal_investigator_name:
    excel_cell: "B5"
    cir_path: "project.principal_investigator.name"
  project_title:
    excel_cell: "B7"
    cir_path: "project.title"

```

---

## 4. 機能要件

### 4.1 データ取り込み (Input / Reader)

1. **マルチフォーマット対応:**
    * Excel (XLSX) のセル指定読み込み。
    * Word (DOCX) の表構造解析およびプレースホルダー抽出。

2. **インテリジェント・パース:**
    * 非構造化テキスト（Wordの自由記述欄など）に対し、LLM等を用いてキーとなる情報を抽出する補助機能。

### 4.2 データ編集・検証 (Transformation / Logic)

1. **ギャップ分析 (Gap Analysis):**
    * 入力様式（例: AMED）と出力様式（例: JSPS）の差分を検知する。
    * 出力に必要な必須項目がCIR内で欠落している場合、「不足項目リスト」を生成する。

2. **ウィザード形式エディタ:**
    * Webブラウザ上でCIRの内容を表示・編集する。
    * 不足項目リストに基づき、ユーザーに入力を促すアラート機能。

3. **e-Rad/外部DB連携:**
    * 研究者番号等のキー入力に対し、所属や職位を外部APIまたはマスタから自動補完する。

### 4.3 生成・出力 (Output / Writer)

1. **テンプレート・インジェクション:**
    * 機関が配布する様式ファイル（Excel/Word）をそのままテンプレートとして利用する。
    * プログラムは「座標（Excel）」または「タグ（Word）」に対してデータを流し込むのみとし、罫線やフォント操作は行わない。

2. **バージョン管理:**
    * 生成されたDMPのスナップショット保存（申請時、採択時、終了時）。

### 4.4 管理機能

1. **プラグイン・アーキテクチャ:**
    * 新規助成機関の追加は、`Mapping Definition (YAML)` と `Template File` の追加のみで完結させる。

---

## 5. 非機能要件

### 5.1 相互運用性 (Interoperability)

* **maDMP準拠:** 生成されるJSONデータは機械可読な標準形式とし、NII RDC（国立情報学研究所 研究データ基盤）との将来的な連携を可能にする。

### 5.2 セキュリティ・配備 (Security & Deployment)

* **オンプレミス対応:** 機密性の高い研究アイデアを含むため、Dockerコンテナ等を用いて各大学のローカル環境（学内サーバー）で完結して動作可能な構成とする。
* **アクセス制御:** 作成されたDMPへのアクセス権限管理。

### 5.3 ユーザビリティ

* **ガイダンス統合:** 各機関の「記入要領」をツールチップで表示し、PDFマニュアルを参照する手間を省く。

---

## 6. テスト・品質保証計画

**テスト駆動開発 (TDD)** を徹底します。

| テストレベル | 内容 | 対象 |
| --- | --- | --- |
| **Unit Test** | Reader/Writerごとの単体動作検証。Fixture（サンプルファイル）を用いた入出力チェック。 | 各Adapter関数 |
| **Schema Validation** | CIR (Pydantic) が不正なデータ構造を弾くかの検証。 | Core Logic |
| **Integration Test** | A機関読込 -> CIR -> B機関出力 の一連のフロー検証。 | Converter Service |

---

## 7. 開発ロードマップ

### フェーズ1: MVP (Minimum Viable Product)

* **目標:** 「データを持っていれば、特定の書式に出力できる」
* **実装:**
    * CIR (JSON Schema/Pydantic) の策定。
    * Excel Writer (Template Engine) の実装（ターゲット: AMED）。
    * 基本的なWeb API (FastAPI) の立ち上げ。

### フェーズ2: Readerエンジンの開発

* **目標:** 「既存のExcelファイルを再利用できる」
* **実装:**
    * Excel Readerの実装。
    * マッピング定義ファイル (YAML) の設計と実装。
    * AMED入力 -> AMED出力 のラウンドトリップテスト。

### フェーズ3: Word対応と結合

* **目標:** 「Word様式も扱える」
* **実装:**
    * Word Writer (`docxtpl`) の実装。
    * Word Reader (Table parsing) の実装。
    * 異種フォーマット間変換 (Excel <-> Word) の検証。

### フェーズ4: UI/UXの完成

* **目標:** 「誰でも使える」
* **実装:**
    * 不足項目補完のためのWebフォーム (React/Vue)。
    * ドラッグ＆ドロップによるファイルインポートUI。
    * e-Rad情報補完の実装。
