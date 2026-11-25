#!/usr/bin/env python3
"""Hugo のビルドの前に実行する。theme/ の中身(ja-docs-base の部品と、book 向けの補い)を static/ja-docs/ にコピーする。
static/ja-docs/ は生成物なので、Git には入れない(.gitignore)。content/ は書き換えない。"""
import shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
dst = root / "static" / "ja-docs"
dst.mkdir(parents=True, exist_ok=True)
for f in sorted((root / "theme").glob("*")):
    if f.is_file():
        shutil.copy2(f, dst / f.name)
print(f"copied theme -> {dst}")
