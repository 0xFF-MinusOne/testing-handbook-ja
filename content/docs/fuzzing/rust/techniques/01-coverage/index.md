---
title: "カバレッジ解析"
slug: coverage-analysis
weight: 2
---


# カバレッジ解析 {#coverage-analysis}

ファジング中に達成したコードカバレッジを信頼できる状態にしておくことは、2 つの理由で重要です。1 つ目は、ファジングのハーネスがアプリケーションのどの部分を実行しているかを評価したいからです。

たとえば、次の図のようなマジックバリューのチェックは、ファザーが突破しにくいことがあります。このようなチェックを見つけておくと、その値を[辞書]({{% relref 02-dictionary %}})かシードコーパスのテストケースを通じて、ファザーに与えられます。

{{< customFigure "突破しにくいことがあるマジックバリューのチェック" >}}
```Rust
if (buf == 0x7F454C46) {
    // start parsing buf
}
```
{{< /customFigure >}}

2 つ目は、ファザーを切り替えたり、ハーネスや SUT を更新したりしたときに、カバレッジが変わったかどうかを確認したいからです。カバレッジが下がったなら、新しい機能が導入されたために、ハーネスを拡張する必要があるかもしれません。カバレッジが上がったなら、おそらくハーネスを改善できたか、SUT がファジングしやすくなったのでしょう。

ファジングのカバレッジは、ファザーの能力と性能の代わりになる指標です。ファジングエンジンの性能を測るのにカバレッジは[理想的ではない](https://arxiv.org/abs/1808.09700)ことが広く認められていますが、カバレッジを見れば、ハーネスが特定の環境で動いているかどうかは分かります。

次のフローチャートは、理想的なカバレッジ解析のワークフローを示しています。このワークフローでは、ファジングキャンペーンのたびに生成されたコーパスを使ってカバレッジを計算します。これが推奨の方法です。

{{< resourceFigure "coverage-flow.svg" "alt" 300>}}
理想的なファジングのワークフロー: ファジングキャンペーンのたびに、コードカバレッジを評価します。その結果に基づいて SUT やハーネスを更新し、新しいファジングキャンペーンを始めます。
{{< /resourceFigure >}}

{{< hint info >}}
プロのヒント: 長期間にわたってファジングの性能を追跡するのに、使っているファザー自身が返す統計を使うべきではありません。たとえば AFL++ は、コードカバレッジを示す値を出力します。しかし、この値は計算方法がファザーごとに違うことがあるため、ほかのファザーとは比較できません。

最も比較しやすいデータは、カバレッジの測定のために作られたツールが生成します。
{{< /hint >}}

cargo-fuzz ツールは、コーパスに対するカバレッジを出力できます。取得したカバレッジデータをもとに、標準的な Rust のツールで HTML レポートを生成できます。

cargo-fuzz ツールを使うには、使用する nightly ツールチェーンに llvm-tools-preview コンポーネントをインストールしておく必要があります。


```shell
rustup toolchain install nightly --component llvm-tools-preview
```


次に、cargo-fuzz でカバレッジデータを出力します。cargo-fuzz ツールは、カバレッジの計装を付けてプロジェクトを再コンパイルし、コーパス内のすべてのテストケースを実行します。


```shell
cargo +nightly fuzz coverage fuzz_target_1
```


cargo-fuzz ツールは、統合したカバレッジを `.profdata` ファイルに書き出したと報告します。次に、[cargo-binutils](https://github.com/rust-embedded/cargo-binutils) と [rustfilt](https://github.com/luser/rustfilt) のツールをインストールする必要があります。


```shell
cargo install cargo-binutils
cargo install rustfilt
```

次のスクリプトを作成し、実行可能にします。カバレッジの生成を手作業で呼び出すのはかなり複雑なので、スクリプトにします。


{{< customFigure "HTML のカバレッジを生成するスクリプト。ファジング用バイナリのパスは [cargo-fuzz のソースコード](https://github.com/rust-fuzz/cargo-fuzz/blob/c4a4d33181b36bea49e20a9639e801ae88aa59c5/src/project.rs#L289-L295)で定義されています。" >}}
```sh
cat <<'EOF' > ./generate_html
#!/bin/sh
if [ $# -lt 1 ]; then
    echo "Error: Name of fuzz target is required."
    echo "Usage: $0 fuzz_target [sources...]"
    exit 1
fi
FUZZ_TARGET="$1"
shift
SRC_FILTER="$@"
TARGET=$(rustc -vV | sed -n 's|host: ||p')
cargo +nightly cov -- show -Xdemangler=rustfilt \
  "target/$TARGET/coverage/$TARGET/release/$FUZZ_TARGET" \
  -instr-profile="fuzz/coverage/$FUZZ_TARGET/coverage.profdata"  \
  -show-line-counts-or-regions -show-instantiations  \
  -format=html -o fuzz_html/ $SRC_FILTER
EOF
chmod +x ./generate_html
```
{{< /customFigure >}}

最後に、HTML レポートを生成して `fuzz_html/` に保存します。


```shell
./generate_html fuzz_target_1 src/lib.rs
```


{{< hint info >}}
プロのヒント: 次の表は、実行している cargo コマンドをさらに詳しく説明したものです。
|||
|--- |--- |
|`cargo +nightly cov --`|Rust ツールチェーンの llvm-cov ツールを呼び出す|
|`show`|このサブコマンドは HTML レポートを生成できる|
|`-Xdemangler=rustfilt`|[rustfilt](https://github.com/luser/rustfilt) のデマングラを使い、関数名を読みやすくする|
|`"target/$TARGET/coverage/$TARGET/release/$FUZZ_TARGET"`|計装された Rust のバイナリまたはオブジェクトファイルのパス|
|`-instr-profile="fuzz/coverage/$FUZZ_TARGET/coverage.profdata"`|統合したカバレッジデータのパス|
|[`-show-line-counts-or-regions`](https://releases.llvm.org/5.0.1/docs/CommandGuide/llvm-cov.html#cmdoption-llvm-cov-show-show-line-counts-or-regions) [`-show-instantiations`](https://releases.llvm.org/5.0.1/docs/CommandGuide/llvm-cov.html#cmdoption-llvm-cov-show-show-instantiations)|Rust で出力を理解しやすくするオプション|
|`-format=html -o fuzz_html/`|形式を HTML にし、HTML ファイルをディレクトリに出力する|
|`src/lib.rs`|任意で、ソースファイルのパスを追加して出力を絞り込める。ここでは lib.rs ファイルだけに関心がある。|
{.skip-table-head}
{{< /hint >}}

## 実際の例 {#real-world-examples}


### Cargo のクレート: ogg {#cargo-crate-ogg}

[前の節](#cargo-crate-ogg)では、ogg クレートをファジングしました。ここでは、ファジングキャンペーンのカバレッジを評価し、十分なカバレッジを達成できたかを確認します。

まず、コーパスを調べて、テストケースが見つかったことを確認します。


```shell
ls fuzz/corpus/fuzz_target_1/ | wc -l
```

次に、コーパスから統合したカバレッジデータを生成します。
```shell
cargo +nightly fuzz coverage fuzz_target_1
```

最後に、[カバレッジ解析](#coverage-analysis)の節で紹介した `generate_html` スクリプトを使って HTML レポートを生成し、分野の知識を使ってファジングの性能を評価します。

コードカバレッジが予想外に低い場合は、もっと多様なシードを探すか、ハーネスのバグを直す必要があるかもしれません。ただし、悪いカバレッジを決める単一の数値はありません。これは、クレートの書き方や、特定のコードへの到達しにくさに大きく左右されます。
