---
title: "セキュリティの概要"
slug: security-overview
weight: 10
---

# Rust のセキュリティの概要

## 安全性とセキュリティ

Rust のコンパイラは、Rust のメモリ安全性を保証します。入力が何であっても、実行時に未定義動作やデータ競合は起こりません。

したがって、Rust プログラムのセキュリティテストでは、何が未定義動作（UB）とみなされ、何がみなされないかを理解することが重要です。（安全な）Rust で double-free のバグを探しても意味がありませんよね。Rust のコンパイラが行う保証については、Rust Reference の[「Behavior considered undefined」](https://doc.rust-lang.org/reference/behavior-considered-undefined.html)のページを参照してください。

もう 1 つ重要な Rust の概念が、[*安全性*](https://doc.rust-lang.org/nomicon/safe-unsafe-meaning.html)（safety）です。コードに `unsafe` が付くのは、特別な精査が必要なときです。そのコードは、書き方が悪いと未定義動作を起こしかねません。そして、コードが特定の約束事を守るようにする責任は、（コンパイラではなく）開発者にあります。

{{< mermaid >}}
flowchart LR
    subgraph Input[" "]
        direction TB
        A[Safe Rust]
        C[Unsafe Rust]
    end
    A --> B[Is Sound]
    C --> D{Sound?}
    D -->|Yes| B
    D -->|No| E[Not Sound]
    B --> F[No Undefined Behavior]
    E --> G[UB Possible]
    F --> H[Vulnerabilities Possible]
    G --> H

    style Input fill:none,stroke:none
    style A fill:#000,color:#fff,stroke:#000
    style B fill:#000,color:#fff,stroke:#000
    style C fill:#ad182b,color:#fff,stroke:#ad182b
    style D fill:#ad182b,color:#fff,stroke:#ad182b
    style E fill:#ad182b,color:#fff,stroke:#ad182b
    style F fill:#000,color:#fff,stroke:#000
    style G fill:#ad182b,color:#fff,stroke:#ad182b
    style H fill:#ad182b,color:#fff,stroke:#ad182b
{{< /mermaid >}}

セキュリティテストでは、あらゆる `unsafe` コードが[*健全*](https://docs.rs/dtolnay/0.0.7/dtolnay/macro._03__soundness_bugs.html#soundness)（sound）であることを確かめる必要があります。基本的な監査では、より弱い性質を確かめます。つまり、`unsafe` コードを実際に使っている箇所が、未定義動作を起こさないことです。しかし高度なテストでは、健全性を確かめます。つまり、どんな安全な呼び出し側も、その `unsafe` コードを使って UB を起こせないことです。実際、不健全なコードは、脆弱性のかなりよくある原因です。長い間正しく動いていたコードが、ある特定の入力でバグを引き起こすことがあります。

Rust では unsafe コードを見つけるのが簡単で、これがセキュリティテストの労力を大きく減らします。一方で、unsafe コードが（推移的な）依存関係の中に「隠れて」いることもあります。監査のときは、このことに留意する価値があります。

話はまだあります。安全な（定義された）挙動が、脆弱性につながることもあります。[「Behavior not considered unsafe」](https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html)の一覧は、セキュリティバグのよくある原因となる、注目すべき安全な挙動を挙げています。

* [一般的な競合状態](https://doc.rust-lang.org/nomicon/races.html)
  * デッドロック（ブロッキングのバグ）
  * 状態の同期の誤り（ノンブロッキングのバグ）
* リソースリーク
* ポインタの露出
* 算術エラー
* 非決定性
* ロジックエラー

さらに、安全な Rust も、まれに不健全になることがあります。詳しくは、[Rust の GitHub の issue](https://github.com/rust-lang/rust/issues?q=is%3Aissue%20state%3Aopen%20label%3AI-unsound)と、[「Counterexamples in Type Systems」](https://counterexamples.org/intro.html)の資料を確認してください。通常、監査人はこうした特殊なケースに重点を置く必要はありません。

## リソースリーク

Rust のメモリ安全性の保証により、うっかりメモリリークを起こしにくくなっていますが、起こせなくなるわけではありません（[Rust のドキュメント](https://doc.rust-lang.org/book/ch15-06-reference-cycles.html)によります）。最悪の場合、メモリリークがサービス拒否攻撃を可能にするかもしれません。よくないことですが、致命的ではありません。

同様に、安全な Rust でも、ファイルディスクリプタ、共有メモリ、データベース接続、ゾンビスレッドといった他のリソースをリークさせることは許されています。

Rust は、デストラクタを呼ばずに終了することも許されています。たとえば、プログラムがデストラクタの中で HTTP 呼び出し、秘密情報の破棄、データベース接続のクローズを行う場合は、問題になりえます。

## ポインタの露出

ポインタの露出は、まれですが興味深い種類のバグで、[プロセスメモリへのポインタが漏れる](https://codeandbitters.com/main-as-usize/)ものです。攻撃者は、そのようなデータを使って、オペレーティングシステムのアドレス空間配置のランダム化（ASLR）を破れます。これは、低レベルのエクスプロイトの助けになります（攻撃者がメモリ破壊のバグを見つけられた場合の話です）。

ポインタの露出は、プログラムを攻撃可能にしたり、おかしな動きをさせたりしないため、安全とみなされています。それでも、念のため、そうした不要なデータの露出は避けるべきです。

## 算術エラー

Rust では数値の扱いは安全ですが、一部の演算は予期しない結果を生むことがあります。バグの主な原因は 3 つあります。

* [整数オーバーフロー](https://doc.rust-lang.org/reference/expressions/operator-expr.html#overflow)
* [浮動小数点演算の不正確さ](https://seclists.org/oss-sec/2023/q2/99)
* [丸め誤差](https://github.com/crytic/roundme)

[整数のバグには 3 種類](https://phrack.org/issues/60/10.html#article)あります。算術オーバーフロー、幅のオーバーフロー、符号の誤りです。

Rust は算術オーバーフローを、いくつかの方法で扱えます。[ラップアラウンドする](https://doc.rust-lang.org/std/primitive.i32.html#method.wrapping_add)、[ラップアラウンドしてオーバーフローを報告する](https://doc.rust-lang.org/std/primitive.i32.html#method.overflowing_add)、[チェックする（`Option` を返す）](https://doc.rust-lang.org/std/primitive.i32.html#method.checked_add)、[飽和させる](https://doc.rust-lang.org/std/primitive.i32.html#method.saturating_add)、[未定義動作を起こす](https://doc.rust-lang.org/std/primitive.i32.html#method.unchecked_add)、パニックする、です。

| Example                             | Result    | Description                            |
|-------------------------------------|-----------|----------------------------------------|
| 255u8.wrapping_add(1)               | 0         | 何も通知せずにゼロへラップアラウンドする |
| 255u8.overflowing_add(1)            | (0, true) | ラップアラウンドし、オーバーフローのフラグを返す |
| 255u8.checked_add(1)                | None      | Option を返し、オーバーフロー時は None |
| 255u8.saturating_add(1)             | 255       | 最大値で頭打ちにする                   |
| 255u8.unchecked_add(1)              | UB        | unsafe。オーバーフロー時は未定義動作   |
| x + 1, where x == u8::MAX (debug)   | panic     | デバッグビルドでの既定の挙動           |
| x + 1, where x == u8::MAX (release) | 0         | リリースビルドでは何も通知せずにラップアラウンドする |

実行時の算術演算の既定の挙動は、リリースビルドではラップアラウンド、デバッグビルドではパニックです。ただし、これは既定にすぎません。[`overflow-checks`](https://doc.rust-lang.org/cargo/reference/profiles.html#overflow-checks) というプロファイル設定で変えられるので、リリースビルドでオーバーフロー時にパニックさせたり（あるいはデバッグビルドでラップアラウンドさせたり）できます。Rust プログラムをレビューする監査人が最もよく置く前提は、オーバーフローは起こるべきでなく、整数オーバーフローはどれも潜在的なバグだ、というものです。監査人の仕事を楽にしたいなら、ラップアラウンドや飽和を想定している算術演算は、明示的に書いてください。

整数オーバーフローについては、[RFC 560](https://github.com/rust-lang/rfcs/blob/ae1394021c001cae2bcdfe3d7f3098dc9e3fbd27/text/0560-integer-overflow.md) と、ブログ記事[「Myths and Legends about Integer Overflow in Rust」](https://huonw.github.io/blog/2016/04/myths-and-legends-about-integer-overflow-in-rust/)で詳しく読めます。

幅や符号のオーバーフローは、数値型の間で変換するときに起こりえます。Rust には暗黙の型変換がないため、予期しないオーバーフローには、次のどちらかで簡単に対処できます。

* オーバーフローを（たとえばパニックで）明示的に処理する、[チェック付きの変換](https://doc.rust-lang.org/std/convert/trait.TryFrom.html)
* ラップアラウンドが起こりうる（ただし[C とは違い](https://stackoverflow.com/questions/16188263/is-signed-integer-overflow-still-undefined-behavior-in-c)、常に挙動が定義されている）[`as` キャスト](https://doc.rust-lang.org/rust-by-example/types/cast.html)

後者のキャストの方法は間違いを起こしやすく、算術オーバーフローと同じだけの精査が必要です。[`as` キャスト](https://doc.rust-lang.org/rust-by-example/types/cast.html)は、大きい整数型を小さい整数型に変換するとき、デバッグモードでも黙って切り捨てます。

## 非決定性

コンパイルや実行のたびに挙動が異なる Rust プログラムは、システムによっては問題になりえます。たとえば、CPU アーキテクチャの異なるマシン間で相互運用できることが期待されるプログラムや、ブロックチェーンのノードのように、マシン間でデータを計算して同期するプログラムです。

Rust の非決定性には、コンパイル時に入り込むものと、実行時に入り込むものの 2 種類があります。

次のものは、コンパイル時の非決定性の原因です。

* アーキテクチャに依存する整数型（`usize` や `libc::c_char` など）とポインタのサイズ
* [浮動小数点数](https://internals.rust-lang.org/t/pre-rfc-dealing-with-broken-floating-point/2673)
* [NaN のビット表現](https://github.com/rust-lang/rfcs/blob/master/text/3514-float-semantics.md)
* 構造体のフィールドの並べ替え
* 列挙型の判別値

次のものは、実行時の非決定性の原因です。

* [`HashMap`](https://dev.to/gnunicorn/hunting-down-a-non-determinism-bug-in-our-rust-wasm-build-4fk1) と `HashSet` の反復
* 構造体のパディング
* ポインタ（特定のメモリアドレス）

## ロジックエラー {#logic-errors}

ロジックエラーは非常に幅広い話題で、次のような領域を含みます。[トレイトのロジック上の制約](https://doc.rust-lang.org/reference/behavior-not-considered-unsafe.html#logic-errors)、弱い認証、壊れた暗号、不十分なデータ検証、[無限再帰](https://blog.trailofbits.com/2025/02/21/dont-recurse-on-untrusted-input/)、[オペレーティングシステムレベルの TOCTOU バグ](https://blog.trailofbits.com/2020/08/12/sinter-new-user-mode-security-enforcement-for-macos/#:~:text=2.%20Mitigating%20the%20TOCTOU%20risks%20in%20real%2Dtime%20security%20decisions)、エラー処理、処理されていない[パニック](https://blog.cloudflare.com/18-november-2025-outage/)、秘密情報の露出などです。

Rust のロジックバグで興味深い種類に、[「アンワインド安全性」](https://doc.rust-lang.org/std/panic/trait.UnwindSafe.html#what-is-unwind-safety)（unwind safety）に関するものがあります。あるデータが不正な状態のときにパニックしたスレッドは、他のスレッド（`catch_unwind` の仕組みを使えば同じスレッドも）にその不正な状態を観察させてしまうことがあります。これは、一部のロジック上の不変条件を壊したり、（unsafe コードがある場合は）メモリ破壊の原因になったりします。パニックが起きてもプログラム全体が完全には終了しない場合は、この種の安全性についてレビューする必要があります。
