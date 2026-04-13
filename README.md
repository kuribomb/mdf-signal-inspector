# python_template

Python プロジェクト用テンプレートリポジトリ。
用途に応じたブランチを選んでプロジェクトを開始する。

## テンプレート一覧

| ブランチ | 用途 | 主な技術 |
|---|---|---|
| [`python-base`](../../tree/python-base) | 汎用 Python ツール | Black, Ruff, Pytest |
| [`python/fastapi`](../../tree/python/fastapi) | Web API | FastAPI, uvicorn, httpx |
| [`python/svelte`](../../tree/python/svelte) | フルスタック Web | FastAPI + SvelteKit |
| [`python/pyside6`](../../tree/python/pyside6) | デスクトップアプリ | PySide6, pytest-qt |

## 使い方

使いたいブランチを指定してクローンし、`.git` を削除して新規リポジトリとして開始する。

```bat
git clone --branch python/fastapi --single-branch https://github.com/kuribomb/python_template.git my-project
cd my-project
rmdir /s /q .git
git init
git add .
git commit -m "Initial commit"
```

`python/fastapi` の部分を使いたいブランチ名に変える。

## ブランチ構成

```
main              ← このファイル（インデックス）
python-base       ← 共通ベーステンプレート
python/fastapi    ← python-base から派生
python/svelte     ← python-base から派生
python/pyside6    ← python-base から派生
```
