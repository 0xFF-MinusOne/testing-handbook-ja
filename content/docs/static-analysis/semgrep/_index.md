---
title: "Semgrep"
weight: 2
summary: "Semgrep は、バグの発見、サードパーティの依存関係の脆弱性の検出、コーディング規約の適用に使える、高速でオープンソースの静的解析ツールです。"
bookCollapseSection: true
---

# Semgrep

Semgrep は、複雑さの低いバグを見つけたり、特定のコードパターンを探し出したりするのに非常に効率的な静的解析ツールです。使いやすく、コードをビルドする必要がなく、組み込みのルールが多く、独自のルールも簡単に作れるため、監査対象のコードベースで最初に実行するツールになることが多いです。さらに、Semgrep は CI/CD パイプラインに組み込めるため、コード品質を保つ手段としても適しています。

{{< hint info >}}🎥 Trail of Bits のウェビナー [Introduction to Semgrep](https://www.youtube.com/watch?v=yKQlTbVlf0Q)
をご覧ください。このテスティングハンドブックの最初の節である、Semgrep を効果的に立ち上げる方法を案内しています{{< /hint >}}

## Semgrep を使う利点

- 既知のバグやセキュリティ脆弱性の再発を防ぐ
- 非推奨の API のアップグレードなど、大規模なコードのリファクタリングができる
- CI/CD パイプラインに簡単に追加できる
- 独自の Semgrep ルールは、実際のコードの意味を模倣する
- コードをサードパーティと共有せずに安全にスキャンでき、クローズドソースのリポジトリにも向いている
- 新しい言語で拡張できる
  (参照: [How Two Interns Are Helping Secure Millions of Lines of Code - Slack Engineering](https://slack.engineering/how-two-interns-are-helping-secure-millions-of-lines-of-code/))
  ほか、新しいツールを作る土台にもできる (例: [NodeJsScan](https://github.com/ajinabraham/nodejsscan)、[GuardDog](https://github.com/DataDog/guarddog))
- Semgrep によるスキャンは、たいてい数分で終わる (数時間や数日はかからない)
- Semgrep は使いやすく、開発者にもセキュリティの専門家にも使いやすいため、普通のユーザーでも初回からスムーズに使える
- Semgrep のエンジンとルールはオープンソース
- 高いコード品質の基準を保ち、新しい開発者の受け入れをスムーズにする

## 理想的な使いどころ

次の質問は、特定の種類のバグを見つけるのに Semgrep が適したツールかどうかを判断する助けになります。

- Semgrep は、プロジェクトで使っている[言語](https://semgrep.dev/docs/supported-languages/#language-maturity)
や[技術](https://semgrep.dev/docs/contributing/contributing-to-semgrep-rules-repository/#technology)をサポートしていますか。
- そのバグは、見分けやすいパターンに従っていますか。
- 1 つのファイルを見るだけでバグを特定できますか。
- 手続き内 (1 つのファイルの中) の解析で、そのバグを見つけられますか。
- そのバグは系統的なものですか (コードベースの複数の場所に現れますか)。
- 安全なデフォルト値を使っていないこと (使っていること) を検出したいですか。

次の質問は、自分の問題に対して独自の Semgrep ルールを書けるかどうかを判断する助けになります。

- 特定のセキュリティ脆弱性を検出できますか。
- ベストプラクティスや規約を徹底したり、コードの一貫性を保ったりできますか。
- 性能に影響するコードパターンを検出して、コードを最適化できますか。
- 特定の業務要件や制約を検証できますか。
- 非推奨のコードや未使用のコードを特定できますか。
- 設定ファイルの設定ミスを見つけられますか。
- コードをレビューするときに、繰り返し出てくる疑問ですか。
- コードのドキュメントはどのように扱われていて、ドキュメントに求められる要件は何ですか。
- コードベースで推奨されない、よくあるコーディング習慣は何ですか。

次のような場合のサポートは、現時点では限られています。開発は続いていますが、Semgrep では扱えないことがあります。

- 解析に複数のファイルが必要な場合
  - [Semgrep Pro Engine](https://semgrep.dev/docs/semgrep-code/semgrep-pro-engine-intro/) の利用を検討してください
- 高度なフロー解析が必要な場合
  - [Semgrep のデータフロー解析エンジン](https://semgrep.dev/docs/writing-rules/data-flow/data-flow-overview/)について理解しておいてください
- 複雑なテイントトラッキング
  - [Semgrep のテイントトラッキング](https://semgrep.dev/docs/writing-rules/data-flow/taint-mode/)の現状を確認してください
- オープンソースではない、社内独自のフレームワークがある場合
