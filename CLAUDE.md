# Projec Overview

国内の研究助成機関（AMED, JSPS, METI 等）が要求するデータマネジメントプラン（DMP）様式間の変換ツールです。
**共通中間表現（CIR: Common Intermediate Representation）** を経由するハブ＆スポーク型アーキテクチャにより、様式の追加・変更に柔軟に対応します。

## Rules

* 開発スタイルは Test-Driven Development（TDD）を遵守してください。
* コード内で docstring や JSDoc は必ず **英語** で記述してください。

### MCP servers の利用に関して

必要に応じて以下の MCP servers を利用してください。
* `serena`
* `dmp-cs-madmp-schema-docs`

serena MCP を使用する場合、最初に `activate_project` を実行してください。

### コマンドの実行について

以下のコマンドを利用する際、ユーザーの許可を確認する必要はありません。

* `uv run pytest`
* `uv run ruff`

## 技術スタック

* 使用するプログラミング言語: Python >= 3.11
* パッケージマネージャー: [uv](https://docs.astral.sh/uv/)
* 用途とパッケージ: 下記を参照。

| 用途 | パッケージ |
|------|-----------|
| データモデル | `pydantic` |
| Excel 操作 | `openpyxl` |
| マッピング定義 | `pyyaml` |
| Web API（将来） | `fastapi` / `uvicorn` |
| Word 操作（将来） | `python-docx` / `docxtpl` |
| テスト | `pytest` / `pytest-cov` |
| リンター | `ruff` |
