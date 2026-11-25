---
title: はじめに
summary: "自動テストハンドブックは、Trail of Bits で使っている多くの静的解析・動的解析ツールについて、開発者やセキュリティ専門家が設定・最適化・自動化するための手引きです。"
weight: 1
---

# Trail of Bits Testing Handbook

<!-- markdown-link-check-disable -->
Testing Handbook は、[Trail of Bits](https://www.trailofbits.com/) で使っている多くの静的解析・動的解析ツールについて、
開発者やセキュリティ専門家が設定・最適化・自動化するための手引きです。
<!-- markdown-link-check-enable -->
私たちは日々の業務で、クラウドネイティブなソフトウェアから組み込み機器まで、さまざまなソフトウェアプロジェクトを監査しています。
適切なセキュリティツールを使えば開発の早い段階で容易に見つけられるはずの問題が、
気づかれないままソフトウェアのライフサイクルを通り抜けてしまう例を、よく目にします。

私たちは、コードベースのセキュリティ分析を行うときに使える実践的なドキュメントを提供することで、
あらゆる技術スタックの開発チームが、ソフトウェアのセキュリティ水準を高める取り組みを支援したいと考えています。

{{< columns >}}

## わかりやすく

ソフトウェア開発ライフサイクルのあらゆる段階で、
セキュリティツールを効果的に設定できるよう、できるだけわかりやすくすることを目指します。

<--->

## 謎を解く

そのなかで、ファジングやテイント解析といった
静的解析・動的解析の技法の謎も解き明かしたいと考えています。

{{< /columns >}}

## なぜ必要なのか

- 既存のツールを設定・最適化するためのドキュメントは、セキュリティ専門家向けに書かれていることが多く、
  開発者にとって使いやすいとは限りません。
  特にファジングのツールで顕著です。わかりやすいドキュメントがないために、
  本来は簡単に設定できるはずのセキュリティツールで、開発者がいらだち、導入が進まないことがあります。
- ローカルでは簡単に設定できるツールでも、CI/CD パイプラインに組み込むのは難しいことがあります。
- セキュリティツールは、オンラインのドキュメントに従って設定されることが多いものの、
  設定が最適化されることはまれです。調整が足りないと、ツールの結果にノイズが多くなり、
  役に立つどころか、かえっていらだちの原因になります。

## ツール

現在、次のツールと技法を扱っています。

{{< columns >}}

### 静的解析

- [Semgrep]({{< relref "semgrep" >}})
- [CodeQL]({{< relref "codeql" >}})

<--->

### 動的解析

- [ファジング]({{< relref "fuzzing" >}})
- [Burp Suite Professional]({{< relref "/docs/web/burp/" >}})

<--->

### 言語

- [C/C++ セキュリティチェックリスト]({{< relref "/docs/languages/c-cpp" >}})
- [Rust]({{< relref "/docs/languages/rust" >}})

{{< /columns >}}

扱うツールを増やしている最中で、セキュリティに関するほかのテーマも
取り上げる予定です。今後の更新にご期待ください。

### 近日公開 (!)

- kAFL
- 形式検証と Tamarin

## 静的解析ツール用のカスタムクエリ

Trail of Bits の中心的な目標の一つは、繰り返し起こりそうな問題を見つけて解決することです。
そこで役立つのがカスタムクエリです。チーム全体の知識と経験をもとに作られており、
ソフトウェアプロジェクトに先回りした、効果的なセキュリティを提供します。

{{< details title="[Trail of Bits の公開 Semgrep ルール](https://github.com/trailofbits/semgrep-rules)" open=true >}}
プロジェクトのルートフォルダに移動して、すぐに使えます。

```sh
semgrep --config "p/trailofbits"
```

{{< /details >}}

{{< details title="[Trail of Bits の公開 CodeQL クエリ](https://github.com/trailofbits/codeql-queries)" open=true >}}
C、C++、Go 用の公開 CodeQL クエリをインストールするには、`codeql pack download` を実行するだけです。

```sh
codeql pack download trailofbits/cpp-queries trailofbits/go-queries
```

既存のデータベースに対して C と C++ 用のクエリを実行するには、次のコマンドを実行します。

```shell
codeql database analyze codeql.db --format=sarif-latest --output=results.sarif -- trailofbits/cpp-queries
```

{{< /details >}}

## カスタムファザー

私たちは、ソフトウェアのバグを探す監査でファジングを多用しています。
そのため、目的に合うファザーが見つからないときは、自分たちで作ることがよくあります。
次は、私たちが作り、使うことを推奨しているファザーの一覧です。

- [Mishegos](https://github.com/trailofbits/mishegos): x86 デコーダ向けの差分ファザー
- [Ruzzy](https://github.com/trailofbits/ruzzy): 純粋な Ruby コードと Ruby の C 拡張向けの、カバレッジガイド型ファザー
- [Medusa](https://github.com/crytic/medusa): 並列化された、カバレッジガイド型の、変異ベースの Solidity スマートコントラクト用ファザー
- [Echidna](https://github.com/crytic/echidna): Ethereum スマートコントラクト用ファザー
- [Tayt](https://github.com/crytic/tayt): StarkNet スマートコントラクト用ファザー

## フィードバック
<!-- markdown-link-check-disable -->
私たちは、Testing Handbook の品質をできるだけ高く保ち、内容を充実させ続けたいと考えています。
改善できる点に気づいたら、ぜひお知らせください。お知らせいただくには、
[Testing Handbook の GitHub ページ](https://github.com/trailofbits/testing-handbook)で issue を立てるのが最も確実です。
<!-- markdown-link-check-enable -->
