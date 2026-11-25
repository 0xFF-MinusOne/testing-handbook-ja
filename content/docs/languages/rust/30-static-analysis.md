---
title: "静的解析"
slug: static-analysis
weight: 30
---

# Rust の静的解析

静的解析とは、ソースコードを実行せずに解析することです。

## Clippy

Clippy は基本となるリンターです。とにかく使ってください。

[Clippy のリント](https://rust-lang.github.io/rust-clippy/master/index.html)は、グループとレベルに分類されています。グループは、リントが検出する問題の種類による分類です。レベルは、リントが問題を見つけたときにどうするかを表します。

* Allow: 問題を無視する
* Warn: メッセージを stderr に出力する
* Deny: エラーコードを返す（CI パイプラインで便利）

Clippy は `rustc` コンパイラのラッパーです。そのため Clippy を実行すると、`rustc` のリントに加えて、[Clippy 独自のリント](https://doc.rust-lang.org/rustc/lints/listing/index.html)も実行されます。これらのリントも同じように分類されていて、同じフラグと設定オプションで制御できます。

単発のセキュリティレビューでは、バグがありそうなコードの手がかりを得たいはずです。その場合は、デフォルトの設定を使います。選ばれた警告と deny のリントが有効になります。

```sh
cargo clippy
```

非常に成熟したコードベースの監査では、より多くのグループを有効にしたいところです。

```sh
cargo clippy -- -W clippy::pedantic -W clippy::nursery
```

最後に、すべてを有効にすることもできます（`rustc` の allow のリントは 1 つずつ有効にする必要があり、追加の機能が必要なものもあります）。`-Zcrate-attr` は `-Z` フラグなので、このコマンドは nightly ツールチェーンで実行する必要があります。

```sh
cargo +nightly clippy -- \
 -Zcrate-attr="feature(non_exhaustive_omitted_patterns_lint)" \
 -Zcrate-attr="feature(strict_provenance_lints)" \
 -Zcrate-attr="feature(multiple_supertrait_upcastable)" \
 -Zcrate-attr="feature(must_not_suspend)" \
 $(rustc +nightly -W help | grep '  allow' | tr -s ' ' | cut -d' ' -f2 | sed 's/^/-W /') \
 -W clippy::pedantic -W clippy::nursery -W clippy::restriction -A dead_code
```

{{< hint info >}}
私たちのお気に入りのリントは次のとおりです。

* [`arithmetic_side_effects`](https://rust-lang.github.io/rust-clippy/master/index.html#arithmetic_side_effects): 算術演算の副作用になりうるもの（整数オーバーフロー、ゼロ除算など）を検出する
* [`string_slice`](https://rust-lang.github.io/rust-clippy/master/index.html#string_slice): `&str` のスライスをすべて指摘する。インデックスが UTF-8 の文字の境界にないとパニックすることがある
* [`must_use_candidate`](https://rust-lang.github.io/rust-clippy/master/index.html#must_use_candidate): `#[must_use]` を付けられる公開関数を検出する

```sh
# WARNING: The next command modifies files!
cargo clippy --fix --allow-dirty -- -W clippy::must_use_candidate
cargo check --all-targets
```

{{< /hint >}}

Clippy の結果が多い場合は、検出結果を SARIF 形式で出力し、[SARIF Explorer](https://github.com/trailofbits/vscode-sarif-explorer) でコードエディタ上でレビューするとよいでしょう。そのためには、サードパーティの [`clippy-sarif`](https://crates.io/crates/clippy-sarif) ツールを使います。

ツールをインストールします。

```sh
cargo install clippy-sarif
```

次に、Clippy の出力をパイプで渡します。

```sh
cargo clippy --message-format=json | clippy-sarif
```

CI/CD パイプラインのように継続的に使う場合は、誤検知を最小限にして、重要なリントに絞りたいところです。そのために、次の指針に従います。

* Clippy のデフォルトの設定を使う。
* 推奨される `clippy::restriction` のリントを有効にする（下の例を参照）。
* `clippy::pedantic` グループから選んだリントを有効にする（プロジェクトに応じて、1 つずつ判断して有効にします）。
* 警告をエラーにして、どんな問題でも CI/CD が失敗するようにする。
* 有効にしたリントの特定の検出結果を黙らせる必要が本当にあるときは、コードに `#[allow(..)]` 属性を付ける。その場所でなぜリントを無効にしたのか、必ずコメントに書く。

```sh
cargo clippy -- \
 -Dwarnings -A clippy::style -W clippy::arithmetic_side_effects \
 -W clippy::string_slice -W clippy::infinite_loop \
 -W clippy::float_cmp_const
 # then enable style and pedantic like -W clippy::same_item_push -W clippy::cast_lossless
```

Clippy に新しいリントを提供することもできます。その場合は、[公式のガイダンスに従ってください](https://doc.rust-lang.org/clippy/development/index.html)。

{{< hint info >}}
Clippy がテストに対して警告を出さないようにするには、次の設定を使います（たとえば `clippy.toml` ファイルに書きます）。

```toml
allow-expect-in-tests = true
allow-panic-in-tests = true
allow-unwrap-in-tests = true
```

{{< /hint >}}

## Dylint

[Dylint](https://github.com/trailofbits/dylint) は、ユーザーが指定した動的ライブラリのリントを実行します。これにより、開発者は自分専用のリントのコレクションを保守できます。新しい Clippy のリントを書いてプルリクエストを送ることもできますが、いつも理想的な方法とは限りません。

* 新しいリントを、プロジェクト固有のものにはできない。
* 新しいリントで、サードパーティのクレートを対象にはできない。
* 複雑なリントは、保守の手間から歓迎されないことがある。
* 誤検知の多いリントは、歓迎されないことがある。

さらに、Clippy をフォークせずに Dylint でリントを書くと、[不安定な `rustc` API への対応や、ほかの人とのリントの共有がしやすくなります](https://blog.trailofbits.com/2021/11/09/write-rust-lints-without-forking-clippy/)。

{{< resourceFigure "30-dylint.svg" "Clippy と Dylint のリンクの違い" >}}
EuroRust 2024 の講演「Linting with Dylint」のスライド。
{{< /resourceFigure >}}

### クイックスタート

ツールをインストールします。

```sh
cargo install cargo-dylint dylint-link
```

Trail of Bits が提供するリントで実行します。

```sh
cargo dylint  \
 --git https://github.com/trailofbits/dylint \
 --pattern examples/general \
 -- --no-deps --message-format=json | clippy-sarif > dylint.sarif
```

### 自分のリントを書く

自分のリントを書くこともできますが、簡単な作業ではなく、この章の範囲を超えます。大まかには、リントの種類を決める必要があります。

* Pre-expansion: マクロが展開される前の AST に対して実行される
* Early: マクロが展開されたあとの AST に対して実行される
* Late: 高水準中間表現（HIR）に対して実行される。つまり、名前の解決や型の検査などが終わったあと

詳しい指針は、[Samuel Moelius の「Linting with Dylint」EuroRust 2024](https://youtu.be/MjlPUA7sAmA?t=548) の講演を見てください。

## そのほかのツール

### Semgrep

Semgrep は Rust 言語に対応しています。このツールの詳しい情報は、ハンドブックの [Semgrep のページ]({{% relref "/docs/static-analysis/semgrep" %}})を見てください。

```sh
semgrep --config "p/rust"
```

### no-panic

[`dtolnay/no-panic` マクロ](https://github.com/dtolnay/no-panic)を使うと、コンパイラを解析エンジンとして、特定の関数にパニックがないことを証明できます。
