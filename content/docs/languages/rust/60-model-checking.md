---
title: "モデル検査"
slug: model-checking
weight: 60
---

# Rust のモデル検査

モデル検査とは、プログラムがあらゆる入力に対して正しく動くことを検証することです。

単一の値で試す（ユニットテストのように）、あるいは値の集合で試す（プロパティテストのように）のではなく、取りうるすべての値を調べます。そして、賢いアルゴリズムのおかげで、現実的な時間でテストが終わることを期待します。

## Prusti

[Prusti](https://github.com/viperproject/prusti-dev) は、検証ツールを作るためのフレームワークである [Viper](https://www.pm.inf.ethz.ch/research/viper.html) をもとにしています。シンボリック実行と [Z3 定理証明器](https://github.com/Z3Prover/z3)を使います。

{{< hint warning >}}
学術プロジェクトで、更新が止まっているようです。ただし、この種のテストを試すのには使えます。本番で使うなら、Kani や Verus などの別のツールを検討してください。
{{< /hint >}}

### Prusti のインストール

開発者は、[Visual Studio Code の拡張機能](https://marketplace.visualstudio.com/items?itemName=viper-admin.prusti-assistant)を使うことを勧めています。コマンドラインのツールは、[Prusti の GitHub のリリースページからダウンロード](https://github.com/viperproject/prusti-dev/releases)できます。

### 使い方 {#usage}

コードに対して Prusti を実行するだけで、次のことを調べてくれます。

* 到達可能なパニックがないこと
* 到達可能で失敗するアサーションがないこと
* 整数オーバーフローがないこと

Prusti は、プロジェクト内のすべての関数（到達できないものも含む）を見つけ、それぞれを「独立に」検査します。関数の引数は任意の値を取りうるもの、つまり型による制約しか受けないものと仮定します。

Prusti は[テストコードを検査しない](https://prusti.github.io/prusti/user-guide/tour/testing.html)ので注意してください。

値を制限したり、検証したいコードの性質をさらに定義したりするには、関数の仕様を作る必要があります。

### 関数の仕様 {#function-specifications}

Prusti の最大の強みは、関数の契約（仕様）を記述して検証できることです。関数の仕様は、事前条件と事後条件からなります。

* 事前条件
  * この条件は、呼び出しの前に検査されます。
  * Prusti は、その関数へのすべての呼び出しが、事前条件を満たす引数で行われていることを検証します。
  * 事前条件は、事後条件の検査で考慮する値の集合を絞ります。
* 事後条件
  * この条件は、関数が戻ったあとに検査されます。
  * Prusti は、関数のすべての出口で事後条件が満たされていることを検証します。

次の例では、条件を Rust の属性 `requires`（事前条件）と `ensures`（事後条件）で実装しています。Prusti は、`prusti_check` へのすべての呼び出しが 20 以下の引数を渡しているかを調べます。そのうえで、入力が 20 以下であるとして、`prusti_check` 関数が返しうる値が 10 未満かどうかを調べます。

```rust
use prusti_contracts::*;
fn main() {
    prusti_check(20);
    prusti_check(11);
}

#[requires(x <= 20)]
#[ensures(result < 10)]
fn prusti_check(x: u32) -> u32 {
    if x >= 10 {
        return x / 100;
    }
    return x;
}
```

条件に違反する値が見つかると、Prusti はエラーを返し、[問題を示す値の例](https://prusti.github.io/prusti/user-guide/verify/counterexample.html)を出すこともできます。

{{< hint danger >}}
Prusti は、ループを自動では扱えません。コードを検証するには、[`body_invariant!`](https://prusti.github.io/prusti/user-guide/tour/loop_invariants.html) マクロを使う必要があります。
{{< /hint >}}

## Kani

[Kani](https://github.com/model-checking/kani) は、[CBMC](https://www.cprover.org/cbmc/)（C と C++ 向けの有界モデル検査器）のフロントエンドです。

### Kani のインストール

[Cargo を使って](https://model-checking.github.io/kani/install-guide.html)インストールするだけです。

```sh
cargo install --locked kani-verifier
cargo kani setup
```

### 基本的な使い方

Kani の使い方は、普通のユニットテストを書くのと似ています。まずテストを書き、次のコマンドを実行します。

```sh
cargo kani
```

ただし、具体的な値を使う代わりに、`kani::any()` で「シンボリックな」（制限のない、または非決定的な）変数を作ります。このような変数は、（その型の）どんな値でも取りえます。

テストを実行すると、Kani は、シンボリック変数のあらゆる値について、次のものがないことを検証します。

* 失敗するアサーション
* パニック
* メモリ安全性の問題
* 整数オーバーフロー

テストするコードが複雑すぎると、Kani は終わるまでに長い時間がかかったり、終わらなかったりすることがあります。これを避けるために、次の 3 つの機能が使えます。

* [`kani::assume`](https://model-checking.github.io/kani/tutorial-first-steps.html#assertions-assumptions-and-harnesses): シンボリックな値を制限（上限を設定）します。[Prusti の事前条件](#function-specifications)に少し似ています。
* [`kani::unwind`](https://model-checking.github.io/kani/tutorial-loop-unwinding.html): ループの上限を制御します。Kani は、ループが設定した回数までしか回らないものとして扱います。数が大きいほど、実行は遅くなります。しかし数が小さすぎると、Kani は展開アサーションの失敗（`FAILURE: unwinding assertion loop <N>`）を報告します。これが、Prusti の `body_invariant!` マクロの制限を乗り越える仕組みです。
* [`kani::Arbitrary`](https://model-checking.github.io/kani/tutorial-nondeterministic-variables.html#custom-nondeterministic-types): シンボリックな値に対する型ごとの制限を定義します。

例を見てみましょう。

```rust
pub struct Book {
    title: String,
    pages: u16
}

fn read_book(r: Book) -> u16 {
    return if r.title == "The Black Book" {
        0
    } else {
        let mut letters = 0;
        for page in 0..r.pages {
            if page == 13 {
                panic!("Bad luck");
            }
            letters += page;
        }
        letters
    }
}

#[cfg(kani)]
mod verification {
    use crate::{Book, read_book};

    impl kani::Arbitrary for Book {
        fn any() -> Self {
            let titles = vec!["The Black Book", "Lord of the ToB",
                              "The White Book"];
            let title_id: usize = kani::any();
            kani::assume(title_id < titles.len());
            Book { title: titles[title_id].to_string(), pages: kani::any() }
        }
    }

    #[kani::proof]
    #[kani::unwind(18)]
    fn verify_book() {
        let book: Book = kani::any();
        kani::assume(book.pages < 4096);
        let y = read_book(book);
        assert!(y < 100);
    }
}
```

ここには、単純な構造体と、入力によってはパニックする関数があります。

`#[cfg(kani)]` 属性の下に、新しい `verification` モジュールを定義します。こうしておくと、必要ないときに Kani 専用のコードを無効にできます。続いて `kani::Arbitrary` トレイトを実装し、シンボリックな `Books` の作り方を Kani に教えます。`titles` を 3 つの値に限定し、`pages` フィールドには制限のない数を使います。

そのうえで `#[kani::proof]` 属性を使い、普通のユニットテストに似たテストを書きます。違いは主に次の 3 つです。

* （自分で実装した `kani::Arbitrary` を使って）シンボリックな `book` 変数を生成する
* `book.pages` が 4096 未満になるよう制限する
* `#[kani::unwind(18)]` でループの回数を 18 に制限する

[Kani のドキュメントでは](https://model-checking.github.io/kani/tutorial-loop-unwinding.html)、`#[kani::unwind(X)]` 属性を試行しながら設定することを勧めています。

* 予想されるすべてのループの繰り返し回数の最大値より、少し大きい数から始める。
* Kani が終わるまでに時間がかかりすぎるときは、`unwind` の数を下げる。
* Kani が `FAILURE: unwinding assertion loop X` でエラーになるときは、unwind の数を上げる。

Kani が `FAILURE` を見つけたら、その失敗を引き起こす値の例を、次の 2 つの方法のどちらかで作れます。

* `cargo kani -Z concrete-playback --concrete-playback=print` で、失敗を再現するユニットテストを出力する
* `cargo kani -Z concrete-playback --concrete-playback=inplace` で、[そのユニットテストをソースに直接書き込み](https://model-checking.github.io/kani/reference/experimental/concrete-playback.html)、`cargo kani playback -Z concrete-playback -- <test_name>` で再生する

{{< hint danger >}}
Kani は、次のものに対してはうまくスケールしません。

* 内容に制限のない文字列（任意のデータを含む長い文字列）
* ヒープ割り当てを伴う、シンボリックなサイズの構造体
{{< /hint >}}

## そのほかのモデル検査器

[Creusot](https://github.com/creusot-rs/creusot)

* [Why3](https://www.why3.org/) をもとにしている
* 関数の仕様を与えて検証できる

[Crux-mir](https://github.com/GaloisInc/crucible/tree/master/crux-mir)

* シンボリック解析
* 「シンボリック化した」ユニットテストを書ける

[Flux](https://github.com/flux-rs/flux)

* 篩型（refinement type）の検査器
* 関数に複雑な条件を注釈として付けられる

[Verus](https://github.com/verus-lang/verus)

* SMT ベース
* 関数に `requires` / `ensures` 節を追加できる

[Aeneas](https://github.com/AeneasVerif/aeneas)

* Rust のコードを純粋なラムダ計算に変換する。バックエンドは F\*、Coq、HOL4、Lean

[MIRAI](https://github.com/endorlabs/MIRAI)

* 抽象解釈、テイント解析、定数時間解析を実装している

[Stateright](https://www.stateright.rs/title-page.html)

* Rust 向けの TLA+
* システムの状態機械をモデル化し、その性質をテストできる
