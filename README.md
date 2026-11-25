# Testing Handbook(日本語訳)

Trail of Bits の「Testing Handbook」を日本語に訳したものです。静的解析・動的解析(ファジングなど)のツールを、開発者とセキュリティ担当者が設定・最適化・自動化するための資料です。

- 日本語訳のサイト: <https://0xff-minusone.github.io/testing-handbook-ja/>
- 原文のサイト: <https://appsec.guide>

> **これは非公式の日本語訳です。** Trail of Bits による公式のものではなく、原著者の確認や公認を受けていません。原文と食い違う場合は、原文が正です。

## 原著の表示

| 項目 | 内容 |
| --- | --- |
| タイトル | Testing Handbook |
| 著者 | Trail of Bits |
| 出典 | <https://github.com/trailofbits/testing-handbook>(公開サイト: <https://appsec.guide>) |
| 訳した版 | コミット `768209e`(`UPSTREAM_SHA` に全文) |
| ライセンス | [Creative Commons Attribution 4.0 International (CC BY 4.0)](https://creativecommons.org/licenses/by/4.0/)([LICENSE](LICENSE)) |
| 変更したこと | 本文(`content/`)を英語から日本語に翻訳した。サイトの設定と表示を、日本語訳用に変えた(`config.ja.toml`、`layouts/partials/docs/inject/`、`theme/`)。原文の末尾にあった解析用のスクリプト(HubSpot・Plausible)は外した |

この訳は、原著と同じ CC BY 4.0 で公開します。原著の著作権は Trail of Bits にあります。

## 構成

- `content/` — 訳した本文(Hugo の Markdown)
- `original/` — 原文(比べるための元の版)
- `config.toml` — 上流の設定(そのまま残す)。`config.ja.toml` — 日本語訳用の上書き
- `themes/book/` — Hugo の book テーマ(git submodule)
- `layouts/` — 上流のレイアウトと、訳注・フッターの差し込み(`layouts/partials/docs/inject/`)
- `theme/` — [ja-docs-base](https://github.com/0xFF-MinusOne/ja-docs-base) の部品(用語集の吹き出しなど)と、book 向けの補い。ビルド時に `tools/copy_theme.py` が `static/ja-docs/` にコピーする
- `GLOSSARY.md` — 訳語集。`TRANSLATION_BRIEF.md` — 翻訳の方針

## ビルド

Hugo の**拡張版**(extended)が要ります(book テーマの SCSS のため)。Actions では 0.133.0 を使っています。

```sh
git submodule update --init
python3 tools/copy_theme.py
hugo --config config.toml,config.ja.toml --minify   # public/ にできる
hugo server --config config.toml,config.ja.toml     # 手元で確かめる
```

`main` への push で、GitHub Actions(`.github/workflows/pages.yml`)がビルドして GitHub Pages に出します。

## 翻訳の進め方

1. `content/` の Markdown を訳す。コード・コマンド・URL・リンク先・ショートコード・見出しの ID(`{#id}`)・front matter の `slug` と `weight` は、原文のまま残す。
2. 訳語は `GLOSSARY.md` に合わせる。新しい用語は足す。
3. 下の方法で検査してから、PR にする。

### 検査

```sh
python3 tools/check_md.py                 # content/ の全部
python3 tools/check_md.py docs/crypto     # パスの一部だけ
```

`content/<パス>.md` と `original/content/<パス>.md` を比べ、コードブロック・インラインコード・URL・リンク先・画像・ショートコード・HTML タグの数・見出しの数と ID・表の行数が、原文と同じかを確かめます。

### 原文の更新

`.github/workflows/upstream-watch.yml` が毎日、原著のリポジトリを確かめます。訳した版(`.github/upstream.json` の `base`)から `content/` の Markdown・`static/`・`layouts/` が変わっていたら、Issue を作ります。訳に反映したら `base` を新しいコミットにします。

## 誤訳の報告

訳の誤りや、より良い訳語は、[Issue](https://github.com/0xFF-MinusOne/testing-handbook-ja/issues/new?template=mistranslation.md) で知らせてください。サイトの各ページの上にある「誤訳を報告」からも開けます。原文そのものの誤りは、[原著のリポジトリ](https://github.com/trailofbits/testing-handbook/issues)へお願いします。
