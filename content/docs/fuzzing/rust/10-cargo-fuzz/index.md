---
title: "cargo-fuzz"
slug: cargo-fuzz
weight: 2
---



# cargo-fuzz {#cargo-fuzz}

[cargo-fuzz](https://github.com/rust-fuzz/cargo-fuzz) は、Cargo を使っている Rust プロジェクトをファジングするときの事実上の標準です。バックエンドには libFuzzer を使います。Cargo を使っていない場合は、cargo-fuzz を使えないことに注意してください。

cargo-fuzz クレートをインストールすると、Cargo のサブコマンドがインストールされます。そのため、cargo-fuzz は Cargo を使うことが前提です。このサブコマンドは、Rust プロジェクトに必要なコンパイルフラグを自動的に有効にし、AddressSanitizer などのサニタイザの有効化にも対応しています。


## インストール {#installation}

cargo-fuzz は、nightly 版の Rust ツールチェーンでしか使えない機能を使います。[rustup](https://rustup.rs/) でインストールできます。


```shell
rustup install nightly
```


次のコマンドを実行して、インストールが成功したことを確認します。


```shell
cargo +nightly --version
```


ツール自体のインストールは、`cargo install` を使う方法をおすすめします。


```shell
cargo install cargo-fuzz
```

## ファジングテストを書く {#write-a-fuzz-test}

この章の[はじめに]({{% relref "fuzzing#introduction-to-fuzzers" %}})で紹介した、`main` と `check_buf` 関数からなる例を思い出しましょう。ここでは `check_buf` 関数をファジングテストします。そのために、テストしたいコードがライブラリクレートの一部になるように、プロジェクトを組み替えます。

最初の時点では、プロジェクトはおそらく、Cargo のプロジェクトファイル（Cargo.toml ファイル）と `main.rs` からなっています。Cargo.toml には、`your_project` のようなプロジェクト名が指定されています。


```text
src/main.rs
Cargo.toml
```


main.rs ファイルを、プログラムのエントリポイントである main 関数と、ファジングテストしたいコードに分けます。その結果、次のファイルになります。


{{< customFigure "src/lib.rs" >}}
```Rust
use std::process;

pub fn check_buf(buf: &[u8]) {
    if buf.len() > 0 && buf[0] == b'a' {
        if buf.len() > 1 && buf[1] == b'b' {
            if buf.len() > 2 && buf[2] == b'c' {
                process::abort();
            }
        }
    }
}
```
{{< /customFigure >}}

{{< customFigure "src/main.rs" >}}
```Rust
fn main() {
    let buffer: &[u8] = b"123";
    your_project::check_buf(buffer);
}
```
{{< /customFigure >}}

これで、プロジェクトは次の構成になりました。

```text
src/main.rs
src/lib.rs
Cargo.toml
```


次の手順は、cargo-fuzz でプロジェクトを初期化することです。


```shell
cargo fuzz init
```


これにより、`fuzz/` サブディレクトリに、お使いの Cargo クレートに依存する新しい Cargo プロジェクトが作られます。ディレクトリ `fuzz/fuzz_targets` には、依存関係の [libfuzzer-sys](https://github.com/rust-fuzz/libfuzzer) を使う Rust プログラムが入っています。`fuzz_targets/fuzz_target_1.rs` ディレクトリに生成される既定のファイルを、次のように調整できます。


{{< customFigure "fuzz_targets/fuzz_target_1.rs" >}}
```Rust
#![no_main]

use libfuzzer_sys::fuzz_target;

fn harness(data: &[u8]) {
    your_project::check_buf(data);
}

fuzz_target!(|data: &[u8]| {
    harness(data);
});
```
{{< /customFigure >}}


これで cargo-fuzz の設定は完了です。cargo-fuzz で実行できるハーネスを作りました。ファジングターゲットの実際の名前は、`fuzz/Cargo.toml` ファイルで定義されています。ファジングテストはそれぞれ、独立した cargo のバイナリです。

`fuzz_target!` マクロは、ファジングを始める前に、1 回限りのセットアップコードを実行することにも対応しています。詳しくは、[初期化コード]({{% relref "techniques/03-writing-harnesses#initialization-code" %}})を参照してください。

## 使い方 {#usage}

ファジングテストは、次のように cargo-fuzz を呼び出して実行できます。


```shell
cargo +nightly fuzz run fuzz_target_1
```

プロジェクトに unsafe な Rust が含まれず、C/C++ のコードも呼び出さない場合は、オプション `--sanitizer none` を付けると、ファジングの性能を大きく改善できます。既定では、メモリ関連のバグを検査する AddressSanitizer が有効になっています。Rust はメモリ安全な言語なので、unsafe な Rust を使っていなければ、AddressSanitizer の使用は実行を不必要に遅くします（ご自身の用途で ASan を有効にするか無効にするか迷う場合は、[AddressSanitizer](#addresssanitizer) の節を参照してください）。

コーパスは `fuzz/corpus/fuzz_fuzz_target_1/` ディレクトリに保存されます。クラッシュは `fuzz/artifacts/fuzz_fuzz_target_1/` に保存されます。

### テストケースを再実行する {#re-execute-a-test-case}

テストケースは、`cargo +nightly fuzz run fuzz_target_1 <test_case>` で再実行できます。たとえば、次のコマンドはクラッシュを再実行します。


```shell
cargo +nightly fuzz run fuzz_target_1 fuzz/artifacts/fuzz_target_1/crash-04629f583cb62b4c23651a9b9b1749abbad5f932
```


これは、見つかったバグのトリアージに役立ちます。実際にはファジングせずに、テストケースのディレクトリを再実行したい場合（`-runs=0`）は、次のように実行します。

```shell
cargo +nightly fuzz run fuzz_target_1 <directory> -- -runs=0
```

たとえば、コーパスを再実行するには、次のコマンドを実行します。

```shell
cargo +nightly fuzz run fuzz_target_1 fuzz/corpus/fuzz_target_1 -- -runs=0
```

### ファザーのオプション {#fuzzer-options}

cargo-fuzz の実行時にコマンドラインフラグを付けると、いくつかのオプションを調整できます。


* **–-sanitizer none** どのサニタイザを有効にするかを制御します。既定では ASan が有効で、unsafe な Rust のコードをファジングするときに役立ちます。unsafe な Rust を使っていなければ、サニタイザを無効にして、性能を大きく高められます。（詳しくは、[AddressSanitizer](#addresssanitizer) の節を参照してください。）


* **–-jobs 1** [マルチコアでのファジング]({{% relref "10-libfuzzer#multi-core-fuzzing" %}})で簡単に触れた、libFuzzer の実験的なフォーク機能を有効にします。この機能の使用はおすすめしません。

cargo-fuzz 固有のオプションのほかに、`--` に続けて libFuzzer のオプションを付けると、libFuzzer のオプションも使えます。次の例では、libFuzzer のコマンドラインオプションをすべて表示します。


```shell
cargo +nightly fuzz run fuzz_target_1 -- -help=1
```

たとえば、次のコマンドでは、ファザーを導き、興味深いテストケースをより速く見つけられるようにする辞書ファイルを指定できます。（詳しくは、[ファジング用の辞書]({{% relref 02-dictionary %}})を参照してください。）


```shell
cargo +nightly fuzz run fuzz_target_1 -- -dict=./dict.dict
```

## AddressSanitizer {#addresssanitizer}

ASan は、見逃されかねないメモリエラーの検出に役立ちます。ASan の全般的な紹介は、[AddressSanitizer]({{% relref "/docs/fuzzing/techniques/03-asan" %}})を参照してください。

cargo-fuzz でファジングするとき、ASan は既定で有効です。コードや依存関係で [unsafe な Rust](https://doc.rust-lang.org/book/ch19-01-unsafe-rust.html) を使っていない場合、これは良くない既定かもしれません。ASan の目的はメモリ破壊のバグの検出ですが、unsafe なコードのない Rust はメモリ安全なので、この場合は ASan が不要なことがあります。プロジェクトが unsafe な Rust を使っているかどうかは、[cargo-geiger](https://github.com/geiger-rs/cargo-geiger) プロジェクトで判断できます。

ASan を無効にすると、2 倍程度の高速化が見込めます。

ASan は、フラグ ​​`--sanitizer none` で無効にできます。


```shell
cargo +nightly fuzz run ​​--sanitizer none fuzz_target_1
```


Rust のサニタイザの多くは、執筆時点で[不安定](https://doc.rust-lang.org/beta/unstable-book/compiler-flags/sanitizer.html)な機能であるため、現在は nightly ツールチェーンが必要です。そのため、プロジェクトのコンパイルで問題が起きたら、インストールした nightly ツールチェーンの別のバージョンを試すとよいかもしれません。



## 実際の例 {#real-world-examples}


### Cargo crate: ogg {#cargo-crate-ogg}

ogg クレートは、メディアデータを含む [ogg](https://en.wikipedia.org/wiki/Ogg) ファイルを解析します。ogg 形式はメディア用のコンテナ形式で、そうしたファイルは異なるコーデックを格納できます。パーサは、信頼できないデータを渡されても正しく動作しなければならないため、ファジングしやすく、価値の高い対象でもあります。

既存の Cargo クレートをファジングする手順を見ていきましょう。まず、クレートのソースコードをチェックアウトします。

```shell
git clone https://github.com/RustAudio/ogg.git
cd ogg/
```


次に、cargo-fuzz を初期化します。

```shell
cargo fuzz init
```

次に、ハーネスを書くときの良い出発点になりそうな、プロジェクト内のサンプル、ユニットテスト、結合テストを探します。たとえば、ogg クレートの [repack のサンプル](https://github.com/RustAudio/ogg/blob/5ee8316e6e907c24f6d7ec4b3a0ed6a6ce854cc1/examples/repack.rs)です。このサンプルを、ファイルではなくメモリに対して読み書きするように書き換えます。`Result:Err(_)` という enum のケースで示される Rust のエラーは無視します。ファザーが生成した不正なファイルに対してエラーを返すのは、望ましい動作だからです。エラーの場合は、現在の入力をスキップします（`if let Ok(r) = … {` の文を参照）。

次のコードは、cargo-fuzz 用に `fuzz/fuzz_targets/fuzz_target_1.rs` に保存した、ハーネスとエントリポイントです。

{{< customFigure "ogg ライブラリ用のハーネス" >}}
```Rust
#![no_main]

use ogg::{PacketReader, PacketWriter};
use ogg::writing::PacketWriteEndInfo;
use std::fs::File;
use std::io::Cursor;

use libfuzzer_sys::fuzz_target;

fn harness(data: &[u8]) {
    let mut data = data.to_vec();
    let mut pck_rdr = PacketReader::new(Cursor::new(data));

    pck_rdr.delete_unread_packets();

    let output = Vec::new();

    let mut pck_wtr = PacketWriter::new(Cursor::new(output));

    if let Ok(r) = pck_rdr.read_packet() {
        if let Ok(r) = pck_rdr.read_packet() {
            match r {
                Some(pck) => {
                    let inf = if pck.last_in_stream() {
                        PacketWriteEndInfo::EndStream
                    } else if pck.last_in_page() {
                        PacketWriteEndInfo::EndPage
                    } else {
                        PacketWriteEndInfo::NormalPacket
                    };
                    let stream_serial = pck.stream_serial();
                    let absgp_page = pck.absgp_page();
                    let _ = pck_wtr.write_packet(pck.data, stream_serial, inf, absgp_page);
                }
                // End of stream
                None => return,
            }
        }
    }
}

fuzz_target!(|data: &[u8]| {
    harness(data);
});
```
{{< /customFigure >}}

ファジングの性能を高めるために、最初のテストケースをダウンロードして、ファザーにシードとして与えられます。

```shell
mkdir fuzz/corpus/fuzz_target_1/
curl -o fuzz/corpus/fuzz_target_1/320x240.ogg https://commons.wikimedia.org/wiki/File:320x240.ogg
```


これでファザーを実行できます。


```shell
cargo +nightly fuzz run fuzz_target_1
```


コーパスは `fuzz/corpus/fuzz_target_1/` に保存されます。コーパスを長期にわたって使う方法は、[FAQ]({{% relref "05-faq" %}})を参照してください。

次の手順は、カバレッジを調べ、ハーネスやシードのコーパスを改善できないかを確認することです（[カバレッジ分析]({{% relref "techniques/01-coverage/index.md" %}})を参照）。

## 参考資料 {#additional-resources}

* [cargo-fuzz に関する Rust Fuzz Book](https://rust-fuzz.github.io/book/cargo-fuzz.html)
