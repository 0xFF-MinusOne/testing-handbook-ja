---
title: "ハーネスの書き方"
slug: writing-harnesses
weight: 2
---




# ハーネスの書き方 {#writing-harnesses}

ここでは、ハーネスから得られる結果を最適化するための、Rust 固有のヒントを説明します。一般的な助言は、[ハーネスの書き方](#writing-harnesses)を参照してください。

## arbitrary クレートによる構造を考慮したファジング {#structure-aware-fuzzing-with-the-arbitrary-crate}
<!-- TODO This is a candidate for becoming a general Rust Technique instead of a cargo-fuzz specific one.-->

[arbitrary](https://github.com/rust-fuzz/arbitrary) クレートを使うと、ファジングのハーネスを書きやすくなります。マクロを derive することで、Rust の構造体をファジングの対象にできます。たとえば次のコードでは、`String` を所有する `Name` 構造体を作る必要があります。そこで Arbitrary マクロを derive して、`Name` を作りやすくしました。

{{< customFigure "arbitrary クレートを使う、クレート `your_project` の Rust コード" >}}
```Rust
use arbitrary::{Arbitrary};

#[derive(Debug, Arbitrary)]
pub struct Name {
    data: String
}

impl Name {
    pub fn check_buf(&self) {
        let data = self.data.as_bytes();
        if data.len() > 0 && data[0] == b'a' {
            if data.len() > 1 && data[1] == b'b' {
                if data.len() > 2 && data[2] == b'c' {
                    process::abort();
                }
            }
        }
    }
}
```
{{< /customFigure >}}

arbitrary クレートを使うと、[ファジングのテストを書く]({{% relref "10-cargo-fuzz#write-a-fuzz-test" %}})のハーネスと同じように、このテスト用のファジングのハーネスを簡単に書けます。


{{< customFigure "arbitrary クレートを使ったファジングのテスト" >}}
```Rust
#![no_main]

use libfuzzer_sys::fuzz_target;
use arbitrary::{Arbitrary, Unstructured};

fn harness(data: &[u8]) {
    // Wrap it in an `Unstructured`.
    let mut unstructured = Unstructured::new(data);

    // Generate an `Name` and run our checks.
    if let Ok(name) = your_project::Name::arbitrary(&mut unstructured) {
        name.check_buf();
    }
}

fuzz_target!(|data: &[u8]| {
    harness(data);
});
```
{{< /customFigure >}}

実は cargo-fuzz は arbitrary クレートに対応しているので、これを簡単にできます。

{{< customFigure "arbitrary クレートを使った、短くしたファジングのテスト" >}}
```Rust
#![no_main]

use libfuzzer_sys::fuzz_target;

fn harness(data: &your_project::Name) {
    data.check_buf();
}

fuzz_target!(|data: your_project::Name| {
    harness(&data);
});
```
{{< /customFigure >}}

上の 2 つの例はどちらも、arbitrary クレートをライブラリクレートの依存関係にする必要があります。1 つ目の例では、`fuzz/` ディレクトリの `Cargo.toml` にも依存関係を追加する必要があります。2 つ目の例では、`libfuzzer_sys` の依存関係に含まれる arbitrary が使われるので、その必要はありません。必要な依存関係の宣言は次のとおりです。




{{< customFigure "arbitrary クレートの依存関係の宣言" >}}
```toml
[dependencies]
arbitrary = { version = "1", features = ["derive"] }
```
{{< /customFigure >}}

いつもどおり、ファジングのテストは次のコマンドで始められます。


```shell
cargo +nightly fuzz run fuzz_target_1 
```


arbitrary クレートは、基本的にはバイト配列を Rust の構造体にデシリアライズする方法を提供します。ただし、その逆、つまり Rust の構造体をバイト配列にシリアライズする機能はないという制限があります。これは、シードのコーパスを用意しようとするときに問題になります。特定の Rust の構造体になるバイト配列を、意図して作ることはできないからです。

そのため、arbitrary クレートが役に立つのは、空のコーパスから始める場合だけです。cargo-fuzz は内部で libFuzzer を使っていて、libFuzzer は空のコーパスから始められるので、cargo-fuzz を使う場合は問題になりません。しかし AFL++ など、ほかのファザーはシードの入力を必要とします。


## 初期化コード {#initialization-code}

`fuzz_target!` マクロは `init` パラメータに対応していて、ファジングを始める前に 1 回だけコードのブロックを実行します。これは libFuzzer の [`LLVMFuzzerInitialize`](https://llvm.org/docs/LibFuzzer.html#startup-initialization) に相当します。

入力ごとには繰り返したくない 1 回きりの準備にハーネスが依存しているとき、つまり、ハーネスが必要とする読み取り専用のグローバル状態の、コストの高い初期化があるときは、`init` を使います。[実践的なハーネスのルール]({{% relref "/docs/fuzzing/techniques/01-writing-harnesses#practical-harness-rules" %}})にもあるように、SUT がグローバル状態を変更すると、再現性が損なわれることがあるので注意してください。

{{< customFigure "初期化コードを含むファジングのテスト" >}}
```Rust
#![no_main]

use libfuzzer_sys::fuzz_target;
use std::sync::OnceLock;

static CHECK_BUF: OnceLock<project::CheckBufSlowInit> = OnceLock::new();

fuzz_target!(
    init: {
        CHECK_BUF.set(project::CheckBufSlowInit::new()).unwrap();
    },
    |data: &[u8]| {
        let check_buf = CHECK_BUF.get().unwrap();
        check_buf.check(data);
    }
);
```
{{< /customFigure >}}

構文の詳細は、[`fuzz_target!` マクロのドキュメント](https://docs.rs/libfuzzer-sys/latest/libfuzzer_sys/macro.fuzz_target.html#init-code)を参照してください。
