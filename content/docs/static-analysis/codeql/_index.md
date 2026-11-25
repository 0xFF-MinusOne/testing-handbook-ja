---
title: "CodeQL"
weight: 2
summary: "CodeQL は、コードをリレーショナルデータベースに変換し、そのデータベースに問い合わせるための独自の宣言型言語を提供する静的解析ツールです。"
bookCollapseSection: true
---

# CodeQL

CodeQL は強力な静的解析フレームワークで、開発者やセキュリティ研究者が、コードベースに対して特定のコードパターンを問い合わせられます。CodeQL の標準ライブラリはインストールに含まれており、手続き間と手続き内の両方の制御フロー解析とデータフロー解析をサポートしています。ただし、独自のクエリを書くための学習コストは高く、CodeQL 標準ライブラリのドキュメントはまだ乏しい点に注意してください。

{{< hint info >}}🎥 Trail of Bits のウェビナー
[Introduction to CodeQL: Examples, Tools and CI Integration](https://www.youtube.com/watch?v=rQRlnUQPXDw)
をご覧ください。CodeQL で実際のセキュリティ問題を見つけた方法、CodeQL を効果的に使うために必要なツール、CodeQL の CI 連携の設定方法を紹介しています
{{< /hint >}}

{{< hint danger >}}

クローズドソースのリポジトリで CodeQL を実行する予定がある場合は、GitHub Enterprise か GitHub Advanced Security のライセンスが必要になることがあります。(詳細は、
[CodeQL のインストール手順](https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/setting-up-the-codeql-cli#1-download-the-codeql-cli-zip-package)
と
[CodeQL のライセンス](https://github.com/github/codeql-cli-binaries/blob/main/LICENSE.md)
を参照してください。)

{{< /hint >}}

## CodeQL を使う利点

- コードベース全体にわたる、手続き間の制御フローとデータフローのクエリをサポートする
- 抽象構文木、制御フローグラフ、データフローグラフを細かく制御できる
- サポートする各言語に、多くのライブラリと定義済みのクエリが付属している
- 既知のバグやセキュリティ脆弱性がコードベースに入り込むのを防ぐ
- CI/CD パイプラインに簡単に追加できる

## 理想的な使いどころ

次の質問は、特定の種類のバグの亜種を見つけるのに CodeQL が適したツールかどうかを判断する助けになります。

- ソースコードとサードパーティの依存関係にアクセスでき、(コンパイル言語の場合は) プロジェクトをビルドできますか。
- オープンソースのコードベースを解析していますか。それとも、CodeQL の利用が GitHub Enterprise か GitHub Advanced Security のライセンスの対象になっていますか。
- CodeQL は、プロジェクトで使っている[言語をサポート](https://codeql.github.com/docs/codeql-overview/supported-languages-and-frameworks)していますか。
- そのバグの種類を表現するのに、抽象構文木の細かい制御、または手続き間の制御フロー解析やデータフロー解析が必要ですか。
- 解析にかかる時間は重要ではありませんか。(複雑な手続き間のクエリは、実行に長い時間がかかることがあります。)

どれか 1 つでも答えが「いいえ」なら、代わりに [Semgrep]({{% relref
"semgrep" %}}) のようなツールで、そのバグの種類をモデル化することから始めるのをお勧めします。
