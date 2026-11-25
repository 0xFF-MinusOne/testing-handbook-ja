---
title: "サプライチェーン分析"
slug: supply-chain-analysis
weight: 80
---

# Rust のサプライチェーン分析

## 審査

このセクションのツールは、「チェック」よりも「理解」のためのものです。つまり、実行してもバグレポートは出ませんが、依存関係の成熟度と安全性を評価する助けになります。以下のツールは定性的ではなく定量的なので、成熟度についてたしかな根拠を得るには、出力を手作業で詳しくレビューする必要があります。

### cargo-supply-chain

[`cargo-supply-chain`](https://github.com/rust-secure-code/cargo-supply-chain) は、依存関係を通じて暗黙のうちに誰を信頼しているかを明らかにします。その集合は小さいほうが望ましいです。このツールは、依存関係 (ライブラリ) と作者 (公開者) の両方を検出します。

```sh
$ cargo supply-chain crates

Dependency crates with the people and teams that can publish them to crates.io:

1. libc: team "github:rust-lang:libc", team "github:rust-lang:libs", someguy, someother-guy
2. unicode-bidi: team "github:servo:cargo-publish", asterix, obelix
3. bitflags: team "github:bitflags:owners", team "github:rust-lang-nursery:libs", NotMe, notY0u
```

### cargo-vet

[`cargo-vet`](https://mozilla.github.io/cargo-vet/) は、依存関係が「信頼できる第三者」によって監査されたかを確認します。

```sh
$ cargo vet

Vetting Failed!

1 unvetted dependencies:
  regex-syntax:0.8.8 missing ["safe-to-deploy"]

recommended audits for safe-to-deploy:
  Command                                  Publisher   Used By               Audit Size
  cargo vet diff regex-syntax 0.8.5 0.8.8  TheGuy  regex and regex-automata  14 files changed

```

上の `cargo-vet` の失敗は、`regex-syntax` クレートがこのポリシーのもとでは [`safe-to-deploy`](https://mozilla.github.io/cargo-vet/built-in-criteria.html#safe-to-deploy) として審査されていないことを意味します。ただし、このクレートの古いバージョンについては監査が存在します。

[あらかじめ設定された監査者](https://github.com/mozilla/cargo-vet/blob/main/registry.toml)がいくつかあり、[さらに追加でインポート](https://mozilla.github.io/cargo-vet/importing-audits.html)することもできます。次の追加をおすすめします。

* [`rust-crate-audits`](https://github.com/google/rust-crate-audits): Google の監査のコレクション
* [`bytecodealliance/wasmtime`](https://github.com/bytecodealliance/wasmtime/blob/main/supply-chain/audits.toml)

### cargo-crev

[`cargo-crev`](https://github.com/crev-dev/cargo-crev) は、分散型のコードレビューのためのもう 1 つのツールです。

```sh
$ cargo crev verify --show-all

status reviews issues owner      downloads    loc lpidx geiger flgs crate   version latest_t
none     0   3  0   0  0  1 45104K 695354K   7558   115    err ____ memchr  2.7.6   ↓2.7.1
```

監査に暗号の署名をして検証します (これが重要な場合に役立ちます)。性質として `cargo-vet` より分散的ですが、手作業での設定が増えることがあり、バージョン間の差分に対する信頼には対応できません。

{{< hint info >}}
`crev` 形式の監査を `vet` 形式に変換するには、[`crevette` ツール](https://github.com/crev-dev/crevette)を使います。
{{< /hint >}}

### cargo-deny

[`cargo-deny`](https://github.com/EmbarkStudios/cargo-deny) は、依存関係のリントに使えます。次のような問題があるクレートを自動的に検出して警告したい場合に使います。

* 互換性のないライセンスである
* 依存関係ツリーに複数のバージョンがある
* 自分で明示的に禁止している
* 公開されたセキュリティアドバイザリがある

### cargo-unmaintained

[`cargo-unmaintained`](https://github.com/trailofbits/cargo-unmaintained) は Trail of Bits のツールで、`cargo audit` (後述) に加えて使うことで、メンテナンスされていない依存関係をヒューリスティックに検出できます。

### cackle

[`cackle`](https://github.com/cackle-rs/cackle) は、プロジェクトの依存関係が使う API (ファイルシステム、ネットワーク、環境、ソケットなど) を一覧にします。これにより、想定していない API にアクセスする、疑わしい推移的依存関係を検出できます。

## 脆弱性の探索

脆弱性を検出するための決定版のツールは [`cargo audit`](https://crates.io/crates/cargo-audit) です。迷わず使ってください。このツールは、依存関係を既知の脆弱性のデータベースと照合します。

```sh
$ cargo audit

   Scanning Cargo.lock for vulnerabilities (32 crate dependencies)
Crate:     h2
Version:   0.3.20
Title:     Degradation of service in h2 servers with CONTINUATION Flood
Date:      2024-04-03
ID:        RUSTSEC-2024-0332
URL:       https://rustsec.org/advisories/RUSTSEC-2024-0332
Solution:  Upgrade to ^0.3.26 OR >=0.4.4
Dependency tree:
h2 0.3.20
└── project 0.1.0
```

依存関係に脆弱性がなくても、新しいバージョンに更新できるかを知っておく価値があります。そのためには、[`cargo outdated` ツール](https://github.com/kbknapp/cargo-outdated)を使います。

```sh
$ cargo outdated --workspace

All dependencies are up to date, yay!
```

{{< hint info >}}
出力の「removed」というラベルは、その親を更新すると、その依存関係が依存関係ツリーから外れることを意味します。
{{< /hint >}}

新しいバージョンがあるクレートを検出するもう 1 つの方法は、[`cargo edit` を使うこと](https://github.com/killercup/cargo-edit?tab=readme-ov-file#cargo-upgrade)です。

```sh
cargo upgrade --incompatible --dry-run
```

## バージョンの食い違い

プロジェクトが、同じ依存関係の複数の異なるバージョンに依存することがあります。それ自体は必ずしもセキュリティ上の問題ではありませんが、クレートの食い違うバージョンの数は抑えたほうがよいです。

複数のバージョンがある依存関係を検出するには、[`cargo-deny`](https://github.com/EmbarkStudios/cargo-deny) ツールを使います。

```sh
cargo deny check bans --exclude-dev
```

{{< hint info >}}
`warning[duplicate]` という出力を探してください。
{{< /hint >}}

同様に、複数のソース (例: crates.io と github.com) から取得されている依存関係も、何らかの問題を示している可能性があります。そのような問題のある依存関係を報告するには、[`cargo vendor`](https://doc.rust-lang.org/cargo/commands/cargo-vendor.html) (バージョンが同じでソースが異なる場合を検出) か、`cargo-deny` の `sources` チェック (バージョンもソースも異なる場合も検出) を使います。

```sh
cargo vendor --locked ./tmp_path
cargo deny check sources
```

最後に、複数の `Cargo.toml` ファイルで指定されている依存関係を見つけるには、[`cargo-autoinherit`](https://github.com/mainmatter/cargo-autoinherit) の利用を検討してください。
