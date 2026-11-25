---
title: "メモリのゼロ化"
slug: memory-zeroization
weight: 50
---

# Rust のメモリのゼロ化

最適化を行うコンパイラがある環境でのゼロ化は困難です。Rust では、コンパイラがメモリ管理に課す制約のために、特に厄介です。コンパイラは多くのエイリアスの情報を推論でき、その結果、秘密データの予期しないコピーがスタック上に現れることがあります。たとえば、ブログ記事 ["A pitfall of Rust's move/copy/drop semantics and zeroing data"](https://benma.github.io/2020/10/16/rust-zeroize-move.html) で説明されている落とし穴を考えてみてください。

セキュリティの目標に応じて、「ゼロ化のセキュリティ」には 3 つのレベルを考えられます。

## 各方法の長所と短所

| セキュリティレベル | 長所 | 短所 |
| :---- | :---- | :---- |
| **1** | 値が破棄される前にゼロ化されることを確実にするための具体的なコーディングルールがある。コーディングの負担が小さい | ゼロ化を保証できない。明示的にゼロ化されないコピーを、コンパイラが作ることを許してしまう |
| **2** | ムーブによるコピーの作成を防ぐか、コピーをコード上で明示させる | 明示的なデリファレンスがスタック上にコピーを作るのは防げない。コーディングの負担が大きい |
| **3** | コンパイラと戦う必要がない。データの分離について最も強い保証が得られる。データの寿命とゼロ化について、概念的に単純なモデルになる | 実装に時間がかかる。実行時のリソース消費が大きい。ハードウェアレベルの不確実性がありうるため、メモリのゼロ化が 100% 確実になるわけではない |

{{< hint info >}}
レベル 1 かレベル 2 の対策を実装済みなら、[私たちの `zeroize-audit` スキル](https://github.com/trailofbits/skills/tree/main/plugins/zeroize-audit)を使って、ゼロ化の漏れや、コンパイラに消された消去処理を見つけてください。
{{< /hint >}}

## セキュリティレベル 1: ZeroizeOnDrop を使う (一般的な方法)

大まかに言うと、値がスコープから外れるたびにゼロ化されるようにする、という考え方です。この目標を達成する最も一般的な方法は、[`zeroize`](https://docs.rs/zeroize/latest/zeroize/) クレートです。`#[derive(ZeroizeOnDrop)]` を導出すると、`Drop` の実装が生成されます。その `drop` メソッドは、コンパイラがその値を破棄するときに、値の各フィールドに対して `zeroize` を呼び出します (`#[zeroize(skip)]` が付いたフィールドは飛ばします)。各フィールド自体が `Zeroize` か `ZeroizeOnDrop` を実装している必要があります。この方法は、コンパイラと戦わずに、すべての破棄でゼロ化が行われることを保証しようとするだけの、単純なゼロ化のモデルです。

残念ながら、ムーブは[コピーを作る](https://benma.github.io/2020/10/16/rust-zeroize-move.html)ことがあり、実際によく作ります。一般にムーブは `memcpy` にコンパイルされ、コンパイラは移動元をゼロ化しません。ほかにも、スタックへの退避、ABI の制約、ヒープ上の値の最適化によって、コピーが増えることがあります ([`zeroize` のスタック/ヒープのゼロ化に関する注意](https://docs.rs/zeroize/latest/zeroize/#stackheap-zeroing-notes)を参照)。

ゼロ化に失敗する単純な例を次に示します。`ZeroizeOnDrop` トレイトを実装したスタック上の値が、ヒープにムーブされます ("leak A")。ゼロ化されるのはヒープ上の値だけで、秘密の古いコピーがスタックに残ることがあります。

```rust
use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
struct Secret {
    key: [u8; 32],
}

fn mac(mut key: [u8; 32], msg: &[u8]) -> u8 {
    let mut tag = 0u8;
    for (i, &b) in msg.iter().enumerate() {
        key[i % 32] ^= b;
        tag ^= key[i % 32];
    }
    tag
}

fn main() {
    let s = Secret { key: [0xab; 32] };        // built on main's stack
    let stored = Box::new(s);                  // LEAK A: stack -> heap move
    let tag = mac(stored.key, b"hello world"); // LEAK B: by-value copy
    println!("tag={:02x}", tag);
}
```

{{< hint danger >}}
`Drop` によるゼロ化はベストエフォートです。デストラクタが実行されることは保証されません。`Drop` の実装 (つまり、それが行うゼロ化) は、[`mem::forget`](https://doc.rust-lang.org/std/mem/fn.forget.html) と [`ManuallyDrop`](https://doc.rust-lang.org/std/mem/struct.ManuallyDrop.html)、循環参照 (`Rc`/`Arc`) で生き続ける値、[abort](https://doc.rust-lang.org/std/process/fn.abort.html) (アンワインド中のパニックや、`panic = "abort"` でのパニックを含む)、[`process::exit`](https://doc.rust-lang.org/std/process/fn.exit.html) によって飛ばされます。異常終了のときに秘密を消すために、`ZeroizeOnDrop` だけに頼らないでください。
{{< /hint >}}

## セキュリティレベル 2: ゼロ化の対象をムーブしない、または明示的にムーブする

ベストエフォートの方法に代わる方法は、コンパイラと戦い、コピーがメモリ上に残らないことを保証しようとすることです。

[`Pin`](https://doc.rust-lang.org/std/pin/) 型でムーブを禁止すれば、ムーブによってコンパイラが意図せず作るコピーを防げる可能性があります。次の例のように、`Pin` を使うと、コンパイル時の安全性がある程度得られます。レベル 1 の "leak A" は、もう起こせません (コードがコンパイルされません)。

```rust
use std::{marker::PhantomPinned, pin::pin};

use zeroize::{Zeroize, ZeroizeOnDrop};

#[derive(Zeroize, ZeroizeOnDrop)]
struct Secret {
    key: [u8; 32],
    #[zeroize(skip)]
    _pin: PhantomPinned,
}

fn mac(mut key: [u8; 32], msg: &[u8]) -> u8 {
    let mut tag = 0u8;
    for (i, &b) in msg.iter().enumerate() {
        key[i % 32] ^= b;
        tag ^= key[i % 32];
    }
    tag
}

fn main() {
    let s = pin!(Secret { key: [0xab; 32], _pin: PhantomPinned });
    // The Level 1 leak no longer type-checks:
    //     let _stored = Box::new(*s);
    //            ^^ cannot move out of dereference of `Pin<&mut Secret>`
    let tag = mac(s.key, b"hello world"); // LEAK B: by-value copy
    println!("tag={:02x}", tag);
}

```

しかし、この方法でも、プロセスのメモリに予期しないデータのコピーが作られるのは防げません。上の例でも、`mac` 関数の呼び出しで値渡しのコピーが行われるため、秘密の値のコピーがスタック上に漏れます ("leak B")。

もう少し手の込んだ方法は、[`secrecy`](https://docs.rs/secrecy/latest/secrecy/) クレートを使うことです。秘密データの不用意なコピーを防ぎ、秘密を公開する箇所をコード上で明示させます。

```rust
use secrecy::{ExposeSecret, SecretBox};

fn mac(mut key: [u8; 32], msg: &[u8]) -> u8 {
    let mut tag = 0u8;
    for (i, &b) in msg.iter().enumerate() {
        key[i % 32] ^= b;
        tag ^= key[i % 32];
    }
    tag
}

fn main() {
    let s: SecretBox<[u8; 32]> = SecretBox::init_with_mut(|k| *k = [0xab; 32]);

    // Implicit leaks that the type system rejects:
    //     let d: [u8; 32] = *s;         // ERROR: SecretBox does not Deref to its inner T
    // Safe operations (each shown independently; SecretBox is not Copy/Clone):
    //     let moved = s;                // moves the wrapper; no secret copy is made
    //     println!("{:?}", s);          // Debug is redacted: prints "SecretBox<[u8; 32]>([REDACTED])", not the bytes

    // Leak B is now explicit:
    let tag = mac(*s.expose_secret(), b"hello world");
    println!("tag={:02x}", tag);
}
```

`secrecy` でよくある落とし穴は、初期化の最中に秘密データがスタックに漏れることです。これを避けるには、先に値を作ってからラップするのではなく、`init_with_mut` のような `secrecy` のインプレース初期化 API を使います。次の例は安全ではありません。`key` がスタック上に作られ、そのあとでヒープの領域にムーブされるため、スタック上にコピーが残るからです。

```rust
let key = derive_key();
SecretBox::new(Box::new(key))
```

`secrecy` と `Pin` による解決策には、もう 1 つ欠点があります。OS が秘密をスワップやハイバネーションのイメージに書き込むのを防ぐための、`mlock` やそれに似た仕組みを使っていないことです。

## セキュリティレベル 3: プロセス、アロケータ、スタックを定期的に破棄する

データがもうメモリ上にないことを本当に保証するには (ただし、*保証*の定義はカーネルやハードウェアなどによって変わります)、データがメモリから消えるべき決まった時点 (たとえば、リクエストの処理後) で、プロセスやワーカースレッドを破棄し、それらに関連するメモリをすべて消去します。この方法の最も簡単な形は、結果だけを返し、リクエストが終わったら kill されるワーカープロセスです。スレッドを使うもっと複雑な形では、[スタックと、場合によってはほかのメモリ領域を、明示的に消去](https://docs.rs/clear_on_drop/latest/clear_on_drop/fn.clear_stack_on_return.html)する必要があります。

この方法は、実質的に、メモリレベルのプロセス分離をカーネルが提供することに頼っています。メインのプロセスが侵害されても、秘密の侵害は防げるはずです。ただし、秘密が RAM に残り、ある不定の時点で上書きされるまで残り続けることは防げません (専用の実験機器で、そのデータを取り出せる可能性があります)。

さらに複雑な方法として、サブプロセスやスレッドが kill される直前に、コードがそれらの書き込み可能なメモリ領域を順にたどり、ゼロかランダムなデータで上書きすることも考えられます。しかし、そこまで複雑な解決策でも、データがゼロ化されたと確信できないかもしれません。プロセスレベルの実装では、実質的にハードウェアレベルの保証を与えられないからです。
