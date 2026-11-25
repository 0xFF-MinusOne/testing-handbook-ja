---
title: "動的解析"
slug: dynamic-analysis
weight: 20
---

# Rust の動的解析

動的解析には 2 つの種類があります。ファジングテストと、ユニットテストや機能テストのような「標準的な」テストです。

この章では、標準的なテストに焦点を当てます。これは、すべてのプロジェクトが実装しておくべき基本的なレベルのテストです。基本的なテストでも、セキュリティの観点から多くの改善を積み上げられます。Rust のファジングについては、このハンドブックの [Rust のファジングの章]({{% relref "/docs/fuzzing/rust" %}})を参照してください。

Rust のコードベースでユニットテストを実行する標準のツールは、[`cargo test`](https://doc.rust-lang.org/cargo/commands/cargo-test.html) です。このツールの基本的な設定と使い方はよく知られているので、紹介は省きます。新しいテストランナーの [`cargo nextest`](https://nexte.st/index.html) も試せます。

```rust
#[cfg(test)]
mod tests {
    #[test]
    fn true_dilemma() {
        assert_ne!(true, false);
    }
}
```

ユニットテストを書いて、すべて通るようになったら、それを改善していきましょう。

## ランダム化

### テストの順序のシャッフル

グローバルな状態に依存するテストや、互いに依存関係があるテストは、バグがあっても、通常の実行では通ってしまうことがあります。既定では、テストは複数のスレッドで、（ほぼ）アルファベット順に実行されます。そのため、擬似的に決定的です。

問題のあるテスト間の依存関係を見つけるには、実行のエントロピーを高めます。理想的には、並列実行をせず、ランダムな順序でテストを実行します。

```sh
cargo +nightly test -- -Z unstable-options --test-threads 1 --shuffle
```

ランダムな順序へのシャッフルは、[`nextest` ではできない](https://github.com/nextest-rs/nextest/discussions/1784)ことに注意してください。

{{< hint danger >}}
この方法は規模に応じて拡張できないため、CI/CD パイプラインで多用すべきではありません。代わりに、こうしたテストはときどき手動で開始してください。
{{< /hint >}}

上の `cargo test` コマンドを複数回実行します。いずれかの実行でテストの失敗が報告されたら、表示される「シャッフルのシード」を使って、エラーを確実に再現できます。

{{< details "試してみる例: cargo test のシャッフルのシード" >}}

次のテストは、cargo test で実行すると、ランダムに失敗します。再現できる失敗を得るには、次を実行します。

```sh
cargo +nightly test -- -Z unstable-options --test-threads 1 --shuffle-seed 1337
```

```rust
fn main() { println!("Hello, world!"); }

static mut GLOB_VAR: i32 = 2;

unsafe fn global_var_set(arg: i32) {
    GLOB_VAR = arg;
}

#[cfg(test)]
mod tests {
    use crate::{GLOB_VAR, global_var_set};

    #[test]
    fn a_true_dilemma() {
        unsafe { assert_eq!(GLOB_VAR, 2); }
        unsafe { global_var_set(5); }
        unsafe { assert_eq!(GLOB_VAR, 5); }
        assert_ne!(true, false);
    }

    #[test]
    fn not_true_dilemma() {
        unsafe { assert_eq!(GLOB_VAR, 2); }
        assert_ne!(true, false);
    }
}
```

{{< /details >}}

### フィーチャのランダム化

Rust のコードは、[Cargo のフィーチャ](https://doc.rust-lang.org/cargo/reference/features.html)による条件付きコンパイルに対応しています。理想的には、テストは、プログラムのあらゆる版を網羅します。それを確実にするには、フィーチャの考えられる（または対応している）すべての組み合わせに対して、テストを実行する必要があります。

この作業には、[`cargo hack`](https://github.com/taiki-e/cargo-hack) を使います。まず、すべてのフィーチャを個別にしてコードをテストし、次に、複数のフィーチャを組み合わせて 1 回の実行でテストします。

{{< tabs "cargo-hack" >}}
{{< tab "Shell" >}}

```sh
cargo +nightly install cargo-hack --locked
cargo hack test --each-feature
cargo hack test --feature-powerset --depth 2
```

{{< /tab >}}
{{< tab "CI" >}}

```yaml
- uses: taiki-e/install-action@6da51af62171044932d435033daa70a0eb3383ba
  with:
    tool: cargo-hack
- run: cargo hack test --feature-powerset --depth 2 --workspace
```

{{< /tab >}}
{{< /tabs >}}

{{< hint info >}}
テストの出力にある `info: running` という文字列を探すと、どのフィーチャが使われたかを確認できます。

`--print-command-list` オプションを使うと、ドライランができます。

`--keep-going` オプションを使うと、コンパイルの失敗を飛ばして進めます。
{{< /hint >}}

{{< details "試してみる例: 3 つのフィーチャでの cargo hack" >}}

次のテストは、cargo test コマンドで実行すると通ります。`cargo hack test --each-feature` でも通ります。テストが失敗するコードパスを見つけるには、次を実行します。

```sh
cargo hack test --feature-powerset --depth 2
```

```toml
# Cargo.toml
[features]
fone = []
ftwo = []
fthree = []
```

```rust
fn main() { println!("Hello, world!"); }

#[allow(unreachable_code)]
fn feature_one() -> i32 {
    #[cfg(all(feature = "fone", feature = "fthree", not(feature = "ftwo")))]
    {
        return 3;
    }
    #[cfg(feature = "fone")] {
        return 1;
    }
    #[cfg(feature = "ftwo")] {
        return 2;
    }
    return 0;
}


#[cfg(test)]
mod tests {
    use crate::{feature_one};

    #[test]
    fn feature_test1() {
        let z = feature_one();
        assert!(z < 3);
    }
}
```

{{< /details >}}

## 整数オーバーフロー

ほとんどの整数オーバーフローは、デバッグビルドで（または [`overflow-checks` フラグ](https://doc.rust-lang.org/rustc/codegen-options/index.html#overflow-checks)を設定したときに）、実行時に検出されます。また、起こりうるオーバーフローを静的に見つけられる、[Clippy の `arithmetic_side_effects` lint](https://rust-lang.github.io/rust-clippy/master/index.html#arithmetic_side_effects) もあります。

ただし、どちらの方法でも、明示的なキャストでのオーバーフローは検出されません。`expr as T` という式でのオーバーフローをテストで検出するには、[`cast_checks`](https://github.com/trailofbits/cast_checks) ツールを使えます。

プロジェクトの `Cargo.toml` ファイルに次を追加して、インストールします。

```toml
[dependencies]
cast_checks = "0.1.6"
```

次に、オーバーフローが起こりうると疑う関数に `#[cast_checks::enable]` を付けて、いつもどおりテストを実行します。

別の方法として、`#![feature(custom_inner_attributes, proc_macro_hygiene)]` でインナー属性の機能を有効にして、該当するモジュールに `#![cast_checks::enable]` 属性を付けます。

{{< details "試してみる例: cast_checks の動作" >}}
この例では、算術オーバーフローは標準のオーバーフロー検査で検出されるため、`int_overflow_simple` テストは常に通ります。しかし、`int_overflow_in_cast` テストでオーバーフローを検出するには、`cast_checks` を使う必要があります。

```rust
#![feature(custom_inner_attributes, proc_macro_hygiene)]

fn main() { println!("Hello, world!"); }

mod overflow_lib {
    #![cast_checks::enable]

    pub(crate) fn do_overflow(a: i32) -> i32 {
        return a * 8;
    }

    pub(crate) fn as_u16(z: i32) -> u16 {
        z as u16
    }
}

#[cfg(test)]
mod tests {
    use crate::{overflow_lib::as_u16, overflow_lib::do_overflow};

    #[should_panic]
    #[test]
    fn int_overflow_simple() {
        let y_str = "2147483647";
        let y = y_str.parse::<i32>().unwrap();
        let _ = do_overflow(y);
    }

    #[should_panic]
    #[test]
    fn int_overflow_in_cast() {
        let y_str = "2147483647";
        let y = y_str.parse::<i32>().unwrap();
        println!("{}", y);
        let _ = as_u16(y);
    }
}
```

{{< /details >}}

性能への配慮から、オーバーフロー検査は、リリースビルドではなく、テストとデバッグビルドでだけ有効にしたいことが多いでしょう。

## サニタイザ {#sanitizers}

Rust はメモリ安全ですが、unsafe の世界への門を開いて、use-after-free や初期化されていないメモリの読み取りといった、よく知られた脆弱性を持ち込むことがあります。さらに、Rust のコンパイラは、[メモリリーク](https://doc.rust-lang.org/book/ch15-06-reference-cycles.html)や[一般的な競合状態](https://doc.rust-lang.org/nomicon/races.html)については、強い保証を提供しません。

深いバグを見つけるために、[さまざまなサニタイザ](https://doc.rust-lang.org/beta/unstable-book/compiler-flags/sanitizer.html)を使ってテストを実行できます。ここでのサニタイズとは、コンパイル時にビルドを計装し、専用のランタイムライブラリとリンクすることです。実行時には、計装によって、特定の種類の問題が探されます。サニタイザ付きでテストを実行すると、コンパイル時間、実行時間、メモリ使用量が増えるという欠点があります。

セキュリティテストでよく使われる Rust のサニタイザには、次のようなものがあります。

* AddressSanitizer
* HWAddressSanitizer
* LeakSanitizer
* MemorySanitizer
* ThreadSanitizer

有効にするには、環境変数 `RUSTFLAGS` を設定します。

次の例は、示している `x86_64-unknown-linux-gnu` ターゲットが対応する範囲のサニタイザを実行します。サニタイザはターゲットごとに異なるため、HWAddressSanitizer などの場合は、サニタイザ名とターゲットトリプルを調整してください。

{{< hint warning >}}
現時点では、サニタイザには nightly ツールチェーンを使う必要があります。stable ツールチェーンを使うと、コンパイルが次のエラーで失敗します。

`error: failed to run rustc to learn about target-specific information`
{{< /hint >}}

{{< tabs "rust-sanitizers" >}}
{{< tab "Cargo test" >}}

```sh
for sanitizer in "address" "leak" "memory" "thread"; do
    echo "Testing with $sanitizer"
    export RUSTFLAGS="-Zsanitizer=$sanitizer"
    export RUSTDOCFLAGS="$RUSTFLAGS"
    cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu
done
```

{{< /tab >}}
{{< tab "Cargo nextest" >}}

```sh
for sanitizer in "address" "leak" "memory" "thread"; do
    echo "Testing with $sanitizer"
    export RUSTFLAGS="-Zsanitizer=$sanitizer"
    export RUSTDOCFLAGS="$RUSTFLAGS"
    cargo +nightly nextest run -Zbuild-std --target x86_64-unknown-linux-gnu
done
```

{{< /tab >}}
{{< /tabs >}}

いくつかのヒントです。

* コンパイルが失敗する場合は、[明示的に `--target` オプションを付けて](https://github.com/rust-lang/rust/issues/48199#issuecomment-743406233)、nightly ツールチェーンを使います。

* 使えるツールチェーンを調べるには、`rustup toolchain list` コマンドを使います。

* すべてのターゲットが同等に扱われるわけではありません。[そのサニタイザが対応しているターゲット](https://github.com/rust-lang/rust/issues/123615#issuecomment-2041791236)を確認してください。

* doctest がある場合は、`RUSTFLAGS` と `RUSTDOCFLAGS` の両方を使います。

* サニタイザどうしは互換性がありません。一度に 1 つのサニタイザでコンパイルしてください。例外は、AddressSanitizer と LeakSanitizer で、この 2 つは一緒に使えます。

* ThreadSanitizer と MemorySanitizer を使うときは、`-Zbuild-std` で標準ライブラリを再コンパイルすることが[必須](https://doc.rust-lang.org/beta/unstable-book/compiler-flags/sanitizer.html#instrumentation-of-external-dependencies-and-std)です。AddressSanitizer では推奨されます。

* MemorySanitizer では、すべてのコードをサニタイズする必要があります。C/C++ の依存関係はすべて、（標準ライブラリに加えて）`-fsanitize=memory` フラグでビルドする必要があります。

* ThreadSanitizer については、次の点に注意してください。

  * 既知の制限として、`std::sync::atomic::fence` とインラインアセンブリのコードには対応していません。

  * 誤検知を減らすには、テストを単一のスレッドで実行します（`RUST_TEST_THREADS=1` または `--test-threads=1`）。マルチスレッドのテスト実行での ThreadSanitizer のエラーは、（実際のコードではなく）テスト自体のバグを示している可能性があり、調べる価値があることに注意してください。

{{< details "試してみる例: ASAN を使ったテスト" >}}

次のテストは通りますが、実はバグがあります。AddressSanitizer を使うと、見つけられます。

```sh
RUSTFLAGS='-Zsanitizer=address' cargo +nightly test -Zbuild-std --target x86_64-unknown-linux-gnu
```

```rust
fn main() { println!("Hello, world!"); }

#[cfg(test)]
mod tests {
    #[test]
    fn uaf() {
        let a = vec![7, 3, 3, 1];
        let b = a.as_ptr();
        drop(a);
        let _z = unsafe { *b };
    }
}
```

{{< /details >}}

## Miri

[Miri](https://github.com/rust-lang/miri) は、Rust の「中間レベルの中間表現」のインタープリタです。Miri は、未定義動作と、次のような関連する問題の検出に役立ちます。

* メモリ破壊のバグ
* メモリリーク
* 初期化されていないデータの使用
* メモリアラインメントの問題
* エイリアシングの問題
* データ競合

Miri を使うには、実行可能なコードを指定する必要があります（動的解析を行うため）。最も簡単なのは、テストを Miri 経由で実行することです。nightly ツールチェーンが必要なことに注意してください。

{{< tabs "miri-tests" >}}
{{< tab "Miri with cargo test" >}}

```sh
rustup +nightly component add miri
cargo +nightly miri test
```

{{< /tab >}}
{{< tab "Miri with nextest" >}}

```sh
cargo +nightly miri nextest run
```

{{< /tab >}}
{{< /tabs >}}

別の方法として、テスト環境で、デバッグビルドを Miri に置き換えられます。Miri は計装したバイナリをコンパイルするのではなく、インタープリタなので、コンパイル済みのバイナリを、完全な Cargo コマンドの呼び出しに置き換える必要があります。

```sh
cargo +nightly miri run
```

最後に、ファジングと Miri を組み合わせられます。ファザーは、テストハーネスがコードのかなりの割合をカバーするような入力を生成するはずで、おそらくユニットテストよりも多くなります。Miri は、生成された入力を活用できます。

1. [いつもどおりコードをファジングします]({{% relref "/docs/fuzzing/rust" %}})。
2. ファザーが生成したファイルごとに、Miri の下でコードを実行します。

残念ながら、ファジングと Miri を組み合わせる[単一のコマンドはありません](https://github.com/rust-fuzz/cargo-fuzz/issues/370)。ハーネスごとにテストを追加する必要があります。効率よく行うには、[`rstest`](https://docs.rs/rstest/latest/rstest/) クレートによるテストフィクスチャを使えます。たとえば、バイナリ `fuzz_target_1` をファジングするコードは、次のようになります。

```rust
#![cfg_attr(not(any(miri, test)), no_main)]

use libfuzzer_sys::fuzz_target;
use rust_tests::check_buf;
fn harness(data: &[u8]) {
    check_buf(data);
}

fuzz_target!(|data: &[u8]| {
    harness(data);
});

#[cfg(test)]
#[cfg(miri)]
mod tests {
    use {
        crate::{harness},
        rstest::rstest,
        std::{fs::File, io::Read, path::PathBuf},
    };

    #[rstest]
    fn miri(#[files("corpus/fuzz_target_1/*")] path: PathBuf) {
        let mut input = File::open(path).unwrap();
        let mut buf = Vec::new();
        input.read_to_end(&mut buf).unwrap();
        harness(&buf);
    }
}
```

その後、このコマンドを実行します。コーパスのファイルにアクセスするには、Miri の分離を無効にする必要があります。

```sh
MIRIFLAGS="-Zmiri-disable-isolation" cargo +nightly miri nextest run --bin fuzz_target_1
```

Miri を使うときは、次のヒントを心に留めておいてください。

* Miri はかなり遅いことがあります。

  * CI のジョブでは、慎重に使います。

  * テストを、適度な大きさの関数に分割するようにします。

  * 必要なら、最も実行時間の長いテストを無効にします。

  * `-Zmiri-disable-stacked-borrows` や `-Zmiri-disable-validation` のような、最も重い Miri の検出機能を無効にすることを検討します。

  * 速度を上げるには、[`nextest` で `--test-threads` または `-j` フラグ](https://nexte.st/docs/integrations/miri/#benefits)を使います。

    * テストのスレッド間で共有されるリソースでのデータ競合は、[検出されません](https://github.com/rust-lang/miri#:~:text=Note%3A%20This%20one%2Dtest%2Dper%2Dprocess%20model%20means)。

* doctest は、`nextest` ではまだ[サポートされていない](https://github.com/nextest-rs/nextest/issues/16)ことに注意してください。

* safe なプログラムでも、Miri は価値を提供できます。

  * unsafe な依存関係の内部に、バグが潜んでいるかもしれません。

  * メモリリークや一部のデータ競合は、safe な Rust でも起こりえます。

* Miri が実装している OS の API は、ごく限られた一部です。

  * 標準出力への出力、ファイルシステムへのアクセス、環境変数について、基本的な対応しかありません。

  * FFI には対応していません。

  * テストを、「純粋でない」関数（未実装の API を呼ぶもの）と「純粋な」関数（呼ばないもの）に分けて、後者にだけ Miri を実行する必要があるかもしれません。

* 実行の決定性を下げるには、`MIRIFLAGS="-Zmiri-disable-isolation"` と `RUSTFLAGS="-Zrandomize-layout"` を使います。

* Miri は、コードをコンパイルするときに、Rust の sysroot をダウンロードしてコンパイルします。

  * Miri を使うには、ネットワークアクセスを有効にし、[依存関係のベンダリングを無効に](https://fuchsia.dev/fuchsia-src/development/languages/rust/miri#setup_miri)する必要があります。

* Miri の検査の一部は、既定では有効になっていません。

  * たとえば、`-Zmiri-tree-borrows` を使うと、実験的な stacked borrows を、（これも実験的で、より新しい）tree borrows に置き換えられます。

* Miri の新機能がまとめられている、[Ralf のブログ](https://www.ralfj.de/blog/)に注目しておきましょう。

{{< details "試してみる例: Miri の動作" >}}

次のテストは、通常は通ることも失敗することもありますが、Miri は未定義動作を報告するはずです。

```rust
fn main() { println!("Hello, world!"); }

#[cfg(test)]
mod tests {
    fn x() {}


    #[test]
    fn miri_example() {
        let f = x as *const usize;
        let y = unsafe {
            *f.map_addr(|a| a + 8)
        };
        assert_eq!(y, 0x841f0f);
    }
}
```

{{< /details >}}

## proptest によるプロパティテスト

通常のユニットテストは、単一のシナリオをテストするのに最適です。単一の具体的な値を与えて、コードが期待どおりに動作するかを確認することで、コードをテストします。

しかし、単一の値を使う代わりに、入力の集合を生成し、ユニットテストを複数回実行して、すべての入力で正しく動作するかを確認できます。これは「プロパティテスト」と呼ばれます。ある性質（テストケース）が、想定されるすべての（または多くの）入力で成り立つことを、実質的に検証しているためです。

通常のユニットテストではなくプロパティテストを使うべきかは、どう判断すればよいでしょうか。

* プロパティテスト: 複雑なコード、例を列挙するのが面倒、正しさへの要求が高い、[てこの効きが大きいシナリオ]({{% relref "/docs/fuzzing#what-to-fuzz" %}})
* ユニットテスト: 単純なコード、具体的なケースで動作を伝えるのが最も適している、リグレッションテスト

この作業には、[proptest](https://github.com/proptest-rs/proptest) ツールを使いましょう。有名な [QuickCheck](https://hackage.haskell.org/package/QuickCheck) に着想を得たツールです。

まず、開発用の依存関係としてツールをインストールします。

```toml
[dev-dependencies]
proptest = "1.11.0"
# Only needed for the `#[derive(Arbitrary)]` example below
proptest-derive = "0.8.0"
```

proptest を使うには、ユニットテストを書く必要があります。ただし、テストに使う値を直接書き込む代わりに、値のジェネレータ（proptest のドキュメントでは「ストラテジ」と呼ばれる）を定義します。proptest は、ランダムに生成した値で、ユニットテストを数十回実行します。

proptest には、多くの[設定可能なストラテジ](https://docs.rs/proptest/latest/proptest/)が付属しています。

* 整数用の範囲型ジェネレータ
* 文字列用の正規表現ジェネレータ
* `bit`、`bool`、`char` の値用の単純なジェネレータ
* `std::collections` 用のランダムサイズのジェネレータ
* `Option` と `Result` 用のジェネレータ

ジェネレータは[組み合わせられます](https://proptest-rs.github.io/proptest/proptest/tutorial/macro-prop-compose.html)。次の `Strategy` のメソッドと `prop_oneof!` マクロを使って、生成をさらに組み合わせたり制限したりもできます。

* `prop_map` メソッドでマッピングする
* `prop_filter` メソッドでフィルタリングする
* `prop_oneof!` マクロで enum を作る
* `prop_recursive` メソッドで再帰する

コード例を見てみましょう。

```rust
fn simple_thingy_dingy(a: u64, b: &str) -> u64 {
    return a + match b.parse::<u64>() {
        Ok(x) => x,
        Err(_) => b.len() as u64,
    };
}

#[cfg(test)]
mod tests {
    use crate::simple_thingy_dingy;
    use proptest::prelude::*;

    proptest! {
        #![proptest_config(ProptestConfig::with_cases(100))]
        #[test]
        fn test_simple_thingy_dingy(a in 1337..7331u64, b in "[0-9]{1,3}") {
            println!("{a} | {b}");
            let sum = simple_thingy_dingy(a, &b);
            assert!(sum >= a);
            assert!(sum > 1337);
        }
    }
}
```

`simple_thingy_dingy` 関数は、ユニットテストしたい関数です。そのために、テストを `proptest!` ヘルパーで包む必要があります。そして、値 `a` と `b` に 2 つのジェネレータを使います。整数用の範囲型ジェネレータと、文字列用の正規表現ジェネレータです。

あとは `cargo test` を実行して、proptest が終わるのを待つだけです。`cargo test -- --show-output` を実行すると、どんな値が生成されたかを観察できます。

既定では、proptest はユニットテストを 256 回実行しますが、`ProptestConfig::with_cases` で変更できます。

ユニットテストを失敗させる入力が見つかると、その入力が `proptest-regressions` ディレクトリに書き込まれます。

見てのとおり、使う値のすべてについてストラテジを書く必要があります。しかし、代わりに、`Arbitrary` トレイトを使って[型のストラテジ](https://proptest-rs.github.io/proptest/proptest/tutorial/arbitrary.html)を作れます。このトレイトは、`proptest-derive` クレートが derive してくれます。

```rust
#[cfg(test)]
mod tests {
    use proptest::prelude::*;
    use proptest_derive::Arbitrary;

    #[derive(Debug, Arbitrary)]
    struct Point {
        #[proptest(strategy = "-100i32..=100")]
        x: i32,
        #[proptest(strategy = "-100i32..=100")]
        y: i32,
    }

    impl Point {
        fn distance_from_origin(&self) -> f64 {
            ((self.x.pow(2) + self.y.pow(2)) as f64).sqrt()
        }
    }

    proptest! {
        #[test]
        fn test_distance_is_non_negative(point: Point) {
            prop_assert!(point.distance_from_origin() >= 0.0);
        }

        #[test]
        fn test_distance_within_bounds(point: Point) {
            // Max distance: sqrt(100^2 + 100^2) ≈ 141.4
            prop_assert!(point.distance_from_origin() <= 150.0);
        }
    }
}
```

{{< hint info >}}
proptest を、サニタイザや Miri などのほかの改善と組み合わせて、テストをさらに強化できます。

proptest を Miri と使うには、永続化（`proptest-regressions` ディレクトリ）を無効にする必要があります。

```sh
PROPTEST_DISABLE_FAILURE_PERSISTENCE=true \
MIRIFLAGS='-Zmiri-env-forward=PROPTEST_DISABLE_FAILURE_PERSISTENCE' \
cargo +nightly miri test
```

{{< /hint >}}

最後に、テストを自動化するために、私たちの [`property-based-testing`](https://github.com/trailofbits/skills/tree/main/plugins/property-based-testing) スキルを使ってください。

## カバレッジ

テストがどれだけのカバレッジを持っているかを知ることは、きわめて重要です。カバレッジの収集は、4 つの手順からなります。

* コンパイル時の計装
* テストの実行と、「生」のデータの生成
* 実行ごとの結果のマージ
* マージしたデータの、使いやすい形式（HTML レポートなど）への変換

主なデータ形式は 2 つあります。

* LLVM 形式: `profraw`（プロセスごと）と `profdata`（マージ済み）
* gcov 形式: `gcno`（コンパイル中に生成）と `gcda`（実行中に生成）

2 つのパイプラインは、おおよそ次のように対応します。

| 段階 | LLVM | gcov |
| :---- | :---- | :---- |
| コンパイル時のマッピング | バイナリ内の `__llvm_covmap` セクション | `.gcno` |
| 実行ごとの生の出力 | `.profraw`（プロセスごとに 1 つ） | `.gcda`（プロセス終了時にその場でマージされる） |
| オフラインのマージツール | `llvm-profdata merge` → `.profdata` | `gcov-tool merge`（出力は同じく `.gcda`）または `lcov --add-tracefile`（→ `.info`） |
| レポートを作るツール | `llvm-cov` が `.profdata` とバイナリを読む | `gcov` / `lcov` / `genhtml` が `.gcno` と `.gcda`、または `.info` を読む |

一般的な計装のバックエンド（エンジン）は 4 つあります。

* [LLVM Instrument Coverage](https://doc.rust-lang.org/rustc/instrument-coverage.html)
  * コンパイラのフロントエンドが、ソース領域ごとのカウンタを挿入するため、計装がソースレベルの構造を把握している。
  * カウンタは、実行中にプロセス内で加算され、プロセス終了時に `__llvm_profile_*` ランタイムによって書き出される。
* [LLVM SanitizerCoverage](https://clang.llvm.org/docs/SanitizerCoverage.html)
  * コンパイラが、関数、基本ブロック、エッジ、比較の箇所に、オーバーヘッドの小さい `__sanitizer_cov_*` コールバックを挿入する。
  * コールバックは実行時に呼ばれ、コーパスの誘導のために、ファザーがプロセス内で利用する。
* [GCC `gcov`](https://gcc.gnu.org/onlinedocs/gcc/Gcov.html)
  * コンパイラのバックエンドのパスが、CFG の弧（基本ブロックのエッジ）を計装する。デバッグ情報以外には、ソースレベルの認識はない。
  * カウンタは、実行中にプロセス内で加算され、プロセス終了時に gcov のランタイムによって書き出される。
* ptrace ベース
  * コンパイル時の計装はなく、トレーサが、各文の最初の命令に `INT3` ブレークポイントを置く。
  * トレーサは、`ptrace` 経由で `SIGTRAP` を処理することで、実行時にヒット数を数える。

{{< hint danger >}}
`gcov` エンジンは、[Rust ではサポートされなくなりました](https://github.com/rust-lang/rust/pull/131829)。
このエンジンと gcov 形式は、C/C++ のコードベースでは、今でもよく使われています。
{{< /hint >}}

{{< hint warning >}}
SanitizerCoverage は、一般的なカバレッジ分析のためではなく、[ファジングのため]({{% relref "/docs/fuzzing/rust/techniques/01-coverage" %}})のものです。
{{< /hint >}}

上のエンジンを包んで、Rust プロジェクトで使いやすくした、一般的なツールが 3 つあります。 [`grcov`](https://github.com/mozilla/grcov), [`llvm-cov`](https://github.com/taiki-e/cargo-llvm-cov), and [`tarpaulin`](https://github.com/xd009642/tarpaulin).

| 機能 / ツール | `grcov` | `llvm-cov` | `tarpaulin` |
| :---- | :---- | :---- | :---- |
| バックエンド | LLVM | LLVM | LLVM、ptrace |
| 入力 | `profraw`/`profdata` または `gcno`/`gcda` | `profraw`/`profdata` | 独自の生の出力 |
| カバレッジ | 行、関数、分岐 | 行、関数、分岐、リージョン、MC/DC | 行 |
| 出力形式 | LCOV、JSON、HTML、Cobertura、Coveralls+、Markdown、ADE | テキスト、LCOV、JSON、HTML、Cobertura、Codecov | テキスト、LCOV、JSON、HTML、XML |
| ファイルを除外する | `--ignore` | [`--ignore-filename-regex`](https://github.com/taiki-e/cargo-llvm-cov?tab=readme-ov-file#exclude-file-from-coverage) | `--exclude-files` |
| 関数を除外する | コード内のマーカーと正規表現で | [属性で](https://github.com/taiki-e/cargo-llvm-cov?tab=readme-ov-file#exclude-code-from-coverage) | [属性で](https://github.com/xd009642/tarpaulin?tab=readme-ov-file#ignoring-code-in-files) |
| テストのカバレッジを除外する | できない | [できる](https://github.com/taiki-e/cargo-llvm-cov/issues/123) | `--ignore-tests` |
| C/C++ のカバレッジを有効にする | 不明 | [`--include-ffi`](https://github.com/taiki-e/cargo-llvm-cov?tab=readme-ov-file#get-coverage-of-cc-code-linked-to-rust-librarybinary) | 不明 |
| 異なるビルド間で実行結果をマージできるか | できない | [できる](https://github.com/taiki-e/cargo-llvm-cov?tab=readme-ov-file#merge-coverages-generated-under-different-test-conditions) | [できる](https://github.com/xd009642/tarpaulin?tab=readme-ov-file#command-line)（ただし差分のみ表示） |

{{< hint warning >}}
LLVM のソースベースのエンジンによる分岐カバレッジ（上の `grcov` と `llvm-cov` の `branches` のセル）には、[`-Zcoverage-options=branch`](https://doc.rust-lang.org/rustc/instrument-coverage.html#-zcoverage-options) でコンパイルした **nightly** ツールチェーンが必要です。stable ツールチェーンでは、`grcov` の `--branch` フラグは黙って無視され、分岐のデータは生成されません。以下の例のレポートで、分岐が 0 になっているのはそのためです。
{{< /hint >}}

コマンドラインでカバレッジの統計を確認したり、多くあるカバレッジの可視化ツールのいずれかを使ったりするときに、必要になるのは、たいてい HTML レポートです。

<!-- Below we use ?: in links to make them open in a new tab -->

| HTML 出力 / ツール | `grcov` | `llvm-cov` | `tarpaulin` |
| :---- | :---- | :---- | :---- |
| 例 | [`grcov` を開く]({{% staticref "/languages/rust/coverage/grcov_llvm/?:" %}}) [`lcov` 付きの `grcov` を開く]({{% staticref "/languages/rust/coverage/grcov_llvm_lcov/?:" %}}) | [`llvm-cov` を開く]({{% staticref "/languages/rust/coverage/llvm_cov/?:" %}}) [`llvm-cov-pretty` を開く]({{% staticref "/languages/rust/coverage/llvm_cov_pretty/?:" %}}) | [`tarpaulin` を開く]({{% staticref "/languages/rust/coverage/tarpaulin-report.html?:" %}}) |
| Rust の構文を扱えるか | はい | はい | はい |
| Rust のジェネリクスを展開するか | いいえ | `--show-instantiations` | いいえ |
| ヒット数を含むか | はい | はい | はい |
| 複数ファイルでの出力に対応するか | はい | はい | いいえ |

{{< tabs "coverage-html-reports" >}}
{{< tab "grcov llvm" >}}
![grcov の HTML レポート](grcov_llvm1.png)

---

![grcov の HTML レポート 2](grcov_llvm2.png)
{{< /tab >}}

{{< tab "grcov llvm with lcov" >}}
![grcov と lcov の HTML レポート](grcov_llvm_lcov1.png)

---

![grcov と lcov の HTML レポート 2](grcov_llvm_lcov2.png)
{{< /tab >}}

{{< tab "llvm-cov" >}}
![llvm-cov の HTML レポート](llvm_cov1.png)

---

![llvm-cov の HTML レポート 2](llvm_cov2.png)
{{< /tab >}}

{{< tab "llvm-cov with llvm-cov-pretty" >}}
![llvm-cov-pretty の HTML レポート](llvm_cov_pretty1.png)

---

![llvm-cov-pretty の HTML レポート 2](llvm_cov_pretty2.png)
{{< /tab >}}

{{< tab "tarpaulin" >}}
![tarpaulin の HTML レポート](tarpaulin1.png)

---

![tarpaulin の HTML レポート 2](tarpaulin2.png)
{{< /tab >}}

{{< /tabs >}}

テストのカバレッジを生成するための、一般的なおすすめは次のとおりです。

* 手早いテストには、`llvm-cov`（[`llvm-cov-pretty`](https://crates.io/crates/llvm-cov-pretty) と併用）を使います。実行が最も簡単で、ジェネリクスを解決し、見やすい HTML を出力します。
* 複雑なプロジェクトには、`llvm-cov` か `grcov` のどちらかを使います。どちらも申し分なく、読みやすい出力を生成できます。
* ほかのツールが正しく動作しないときは、`tarpaulin` を使います。[開発者によると](https://github.com/xd009642/tarpaulin?tab=readme-ov-file#nuances-with-llvm-coverage)、次のような場合にそうなることがあります。
  * コードが予期せずパニックする。
  * 競合状態がある。
  * コードがフォークする。

プロファイリングには、[`measureme`](https://github.com/rust-lang/measureme) の使用を検討してください。[Miri や Chrome DevTools](https://medium.com/source-and-buggy/data-driven-performance-optimization-with-rust-and-miri-70cb6dde0d35) と併用できるかもしれません。

{{< hint info >}}
[Testing Handbook リポジトリの `materials/rust/coverage`](https://github.com/trailofbits/testing-handbook/tree/main/materials/rust/coverage) フォルダに移動してください。
そこに、上で示した HTML レポートを生成した Dockerfile があります。
{{< /hint >}}

## テストの検証（ミューテーションテスト）

テストは誰がテストするのでしょうか。テストが重要な分岐を見逃していたら、どうなるでしょうか。重要なテストにバグがあって、誤って通ってしまうとしたら、どうなるでしょうか。テストの検証には、ミューテーションテストの利用をおすすめします。

### テストのカバレッジの穴

ミューテーションテストでは、ソースコードを変更し（変更したものをミュータントと呼ぶ）、テストがその変更を検出するかを確かめます。このテスト手法については、ブログ記事[「Use mutation testing to find the bugs your tests don't catch」](https://blog.trailofbits.com/2025/09/18/use-mutation-testing-to-find-the-bugs-your-tests-dont-catch/)で詳しく読めます。

まず、基本的でも申し分のない、ユニットテストのカバレッジが必要です。そのうえで、次のツールのいずれかを使って、十分にテストされていない、またはバグがあるかもしれないコード領域の一覧を、自動で得ます。

[`cargo-mutants`](https://mutants.rs/welcome.html)

* 使いやすい
* [`syn` ライブラリ](https://docs.rs/syn/latest/syn/)で、すべてのファイルの AST を解析する
* 型を部分的に認識する
* 複数のマシンで[ジョブを分割](https://mutants.rs/shards.html)できる

[`universalmutator`](https://github.com/agroce/universalmutator)

* 複数の言語に対応している
* `cargo-mutants` より手動での設定が多く必要
* 解析モードが 2 つある（正規表現と [Comby](https://github.com/comby-tools/comby)）
* Trivial Compiler Equivalence（TCE）の最適化により、テストの実行前に、冗長なミュータントを取り除く

### 既存のテストのバグ

テストのバグを見つけるためのユニークな方法は、テストを変異させて、通るかを確認することです。通るなら、テストに何か問題があるかもしれないことを示します。これは、実際のコードを変異させるのとは違います。ここで見つけようとしているのは、テストのバグであって、カバレッジの穴やコードのバグではありません。

変異と検証の処理を自動化するには、[Necessist を使います](https://github.com/trailofbits/necessist)。

```sh
cargo install necessist
```

Necessist は、各テストの文を順に取り上げて、1 つずつ削除し、テストがそれでも通るかを確認することで動作します。命令を削除しても通る、変異させたテストは、次のように表示されます。

```text
filename:line-line `removed code` passed
```

命令を削除してもテストが通るなら、その命令は冗長で、テストの動作を変えていません。これは、テストにバグがあるかもしれないことを示します。本当にバグがあるかどうかは、そのあと手動で調べる必要があります。

{{< hint info >}}
Necessist はテストのバグを見つけることを目的としていますが、その結果から、実際のコードの問題が明らかになることもあります。
{{< /hint >}}

{{< details "試してみる例: Necessist を使ったテスト" >}}

Necessist は、`parser_detects_errors` テストが、1 行を削除しても通ることを報告するはずです。これは、テストか `validate_data` 関数のどちらかにあるマジックナンバーが誤っていて、「本当の」バグが適切にテストされていないことを示します。

```rust
fn validate_data(data: &Data) -> Result<(), ()> {
    if !data.magic.eq(&[0x13, 0x37]) { return Err(()) }
    if data.len as usize != data.content.len() { return Err(()) }
    return Ok(());
}

struct Data {
    magic: [u8; 2],
    len: u8,
    content: String
}

#[cfg(test)]
mod tests {
    use crate::{Data, validate_data};

    #[test]
    fn parser_detects_errors() {
        let mut blob = Data{
            magic: [0x73, 0x31],
            len: 2,
            content: "AB".parse().unwrap(),
        };
        blob.content = blob.content + "Y";
        let result = validate_data(&blob);
        assert!(result.is_err());
    }
}
```

{{< /details >}}

Necessist は遅く、誤検知がそれなりの数出ることがあります。CI パイプラインではなく、ときどき手動で実行することをおすすめします。

このツールは `necessist.db` ファイルを生成します。中断した実行を再開するのに使えます。新しいテストを速くするために、このデータベースは、実行のあいだ保持しておくべきです。

## 参考資料

* [「The Rust Programming Language」第 11 章: Testing](https://web.mit.edu/rust-lang_v1.25/arch/amd64_ubuntu1404/share/doc/rust/html/book/second-edition/ch11-00-testing.html): Rust でのユニットテストと結合テストの基本
* [Ed Page の「Iterating on Testing in Rust」](https://epage.github.io/blog/2023/06/iterating-on-test/): `cargo` `test` で起こりうる問題を挙げ、`cargo-nextest` を紹介している
* [Unsafe Rust and Miri by Ralf Jung \- Rust Zürisee June 2023](https://www.youtube.com/watch?v=svR0p6fSUYY)
