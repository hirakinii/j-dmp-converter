# J DMP Converter 実装計画

## 全体アーキテクチャの前提

* **言語:** Python (データ処理とライブラリが豊富)
* **コア概念:**
    * `Reader`: 各機関のファイル(Excel/Word)を読み込み、CIR(共通中間表現: JSON)へ変換。
    * `Writer`: CIRを読み込み、各機関のテンプレートファイルへデータを流し込む。
    * `CIR (Common Intermediate Representation)`: 内部で持つ正規化されたデータモデル（Pydanticモデル等を推奨）。

---

## フェーズ1：コアモデルの定義と「書き出し」の検証 (MVP: Minimum Viable Product)

まずは「データを持っていれば、特定の書式に出力できる」状態を目指します。

### ステップ 1.1: 共通中間表現 (CIR) の策定

* **目的:** すべての変換のハブとなるデータ構造を決める。
* **TDDアクション:**
    1. **Test (Red):** `test_cir_schema_validation` を作成。必須項目（研究代表者名、課題名など）が欠けたJSONをバリデータに投げ、エラーになることを期待するテスト。
    2. **Implement (Green):** Pydantic等を用いてスキーマクラスを定義。
    3. **Refactor:** RDA DMP Common Standardを参考に階層構造（Project, Person, Dataset等）を整理。

### ステップ 1.2: Excelテンプレートエンジンの開発 (Writer)

* **ターゲット:** AMED_DMP (XLSX)
* **目的:** JSONデータからAMEDの様式を出力する。
* **TDDアクション:**
    1. **Fixture作成:** `AMED_template.xlsx`（空の様式）を用意。
    2. **Test (Red):** `test_amed_writer` を作成。
        * 入力: テスト用CIRデータ（代表者名="山田太郎"）
        * 実行: Writer関数を実行。
        * アサーション: 出力されたExcelの「セルB5」の値が "山田太郎" であることを確認（最初は実装がないので失敗する）。
    3. **Implement (Green):** `openpyxl` を使い、指定セルに値を書き込む処理を実装。
    4. **Refactor:** 「セルB5」のような座標をハードコーディングせず、設定ファイル（YAML）から `{"principal_investigator": "B5"}` のように読み込む仕組みにする。

### ステップ 1.3: 複数機関への対応拡張

* **ターゲット:** JSPS_DMP, METI_DMP
* **TDDアクション:** 1.2と同様の手順を別機関のファイルで繰り返す。共通化できるロジック（設定ファイル読み込み部分など）を親クラスに抽出する。

---

## フェーズ2：データ取り込みエンジンの開発 (Reader)

「既存のExcelファイルを読み込んで再利用したい」という要求に応えます。ここが最も複雑（表記ゆれ等があるため）です。

### ステップ 2.1: Excelパーサーの開発

* **ターゲット:** AMED_DMP (XLSX)
* **目的:** 記入済みのAMED様式を読み込み、CIR (JSON) に変換する。
* **TDDアクション:**
    1. **Fixture作成:** `filled_amed_sample.xlsx`（記入済みファイル）を用意。
    2. **Test (Red):** `test_amed_reader` を作成。
        * 実行: Reader関数にファイルを渡す。
        * アサーション: 返ってきたCIRオブジェクトの `.project.title` が、Excel内の記述と一致するか確認。
    3. **Implement (Green):** 設定ファイルのマッピング定義に従い、セルから値を抽出するロジックを実装。

### ステップ 2.2: 相互変換の結合テスト

* **目的:** AMEDのファイルを読み込み、JSPSの形式で出力できるか確認する。
* **TDDアクション:**
    1. **Test (Red):** `test_conversion_amed_to_jsps`
        * Process: `Read(AMED) -> CIR -> Write(JSPS)`
        * アサーション: 生成されたJSPSファイルの該当セルに、元の情報が転記されているか。

---

## フェーズ3：Word (DOCX) 対応と非構造化データの処理

DOCXは座標（セル番地）という概念が希薄なため、別のアプローチが必要です。

### ステップ 3.1: Wordテンプレートエンジン (Writer)

* **ターゲット:** CFA_DMP (DOCX)
* **技術:** `docxtpl` (Jinja2 for Word) を使用推奨。
* **TDDアクション:**
    1. **Fixture作成:** 様式Wordファイル内の記入箇所を `{{ principal_investigator }}` のようなタグに置き換えたテンプレートを作成。
    2. **Test (Red):** JSONを流し込み、生成されたファイル内に "山田太郎" という文字列が存在するか検索するテスト。
    3. **Implement (Green):** テンプレートレンダリング処理の実装。

### ステップ 3.2: Wordパーサー (Reader) - 難所

* **戦略:** Wordからの抽出は完璧を目指さず、「表（Table）」構造を中心に抽出する。
* **TDDアクション:**
    1. **Test:** Word内の「表2」の「1行目・2列目」のテキストを取得するテスト。
    2. **Implement:** `python-docx` でTableオブジェクトを走査するロジック。

---

## フェーズ4：Webアプリケーション化とUX向上

### ステップ 4.1: APIサーバー構築 (FastAPI)

* **目的:** ブラウザからファイルを受け取り、変換結果を返す。
* **TDDアクション:**
    1. **Test:** `TestClient` を使用し、`/convert` エンドポイントにファイルをPOSTしたら 200 OK と共にファイルが返ってくるかテスト。

### ステップ 4.2: 不足項目補完UI (Frontend)

* **シナリオ:** AMED(項目少) → NEDO(項目多) への変換時、CIR上で情報が足りなくなる。
* **実装:**
    * 変換時に `ValidationResult` を返し、不足フィールド（Missing Fields）のリストをUIに提示。
    * ユーザーがWebフォームで追記した後、完全なCIRにしてから出力するフロー。

---

## 推奨するディレクトリ構成と開発フロー

TDDを円滑に進めるためのリポジトリ構成案です。

```text
/
├── adapters/
│   ├── definitions/       # 各機関のマッピング定義(YAML/JSON)
│   │   ├── amed_dmp.yaml
│   │   └── jsps_dmp.yaml
│   ├── templates/         # 各機関の様式テンプレート(XLSX/DOCX)
│   ├── readers/           # 読み込みロジック
│   └── writers/           # 書き出しロジック
├── core/
│   ├── models.py          # CIR (Pydantic Model)
│   └── converter.py       # 変換統括ロジック
├── tests/
│   ├── fixtures/          # テスト用の記入済みExcel/Word
│   ├── unit/              # 個別のReader/Writerのテスト
│   └── integration/       # AからBへの変換テスト
└── web/                   # Web UI & API

```
