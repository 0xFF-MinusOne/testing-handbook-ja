---
title: "Timecop"
weight: 50
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
---

# Timecop (~~Valgrind~~)

[Timecop](https://post-apocalyptic-crypto.org/timecop/) は、潜在的な時間のリークを動的に検出するために作られた、[Valgrind](https://valgrind.org/) のラッパーです。
開発者はメモリ領域を秘密としてマークでき、実行中に、その秘密のメモリ領域に依存する分岐命令やメモリアクセスが行われると、Valgrind がその挙動を報告し、タイミングの脆弱性の特定に役立ちます。

## 概要

Timecop は、Valgrind が提供する関数を包む C のマクロのラッパーです。

## セットアップ

Timecop を使うには、まず Valgrind をインストールする必要があります。
[対応プラットフォーム](https://valgrind.org/info/platforms.html)を見て、お使いのプラットフォームが対応していることを確認してください。
{{< tabs "beyond" >}}
{{< tab "Debian & Ubuntu" >}}

```bash
sudo apt-get install valgrind
```

{{< /tab >}}
{{< tab "Arch Linux" >}}

```bash
sudo pacman -S valgrind
```

{{< /tab >}}
{{< tab "Fedora" >}}

```bash
sudo yum -y install valgrind
```

{{< /tab >}}
{{< tab "Mac (Intel based)" >}}

```bash
brew install valgrind
```

{{< /tab >}}
{{< /tabs >}}

インストールを確認するには、次を実行します。

```bash
valgrind --version
```

Valgrind をインストールしたら、あとは Timecop のヘッダファイル `poison.h` をインクルードするだけです。このファイルは[こちら](https://post-apocalyptic-crypto.org/timecop/#source-code)にあります。

```C
#include "poison.h"
```

あるいは、`memcheck` ライブラリをインクルードして、Valgrind のメモリ検査の関数を直接使うこともできます。

```C
#include "valgrind/memcheck.h"

// VALGRIND_MAKE_MEM_UNDEFINED(addr, len)
// VALGRIND_MAKE_MEM_DEFINED(addr, len)
// VALGRIND_CHECK_MEM_IS_DEFINED(addr, len)
```

## Valgrind の背景

Valgrind は、実行中のメモリ操作を追跡し、メモリリークや use-after-free などの違反を報告する強力なツールです。
メモリ違反の影響は直接には現れないことが多く、検出が難しいため、Valgrind は広く使われるツールになりました。
Valgrind は、Valgrind が作る疑似的な CPU の上でバイナリを実行することで動作し、コンパイル中に計装を行いません。
そのため、どんなバイナリでも実行でき、デバッグも簡単になりますが、実行時の性能を犠牲にします。

### 未初期化の変数

Valgrind が追跡できるメモリ違反の 1 つに、*未初期化の変数*の使用があります。
例:

```C
int a;
```

C のような言語で、こうした未初期化の変数の値を使うのは未定義動作にあたるため、避けるべきです。
Valgrind は、未初期化の変数の使用を追跡し、それが他の値やメモリ領域に伝わることを許します。
プログラムが未初期化の値を次のいずれかに使うと、

- *条件ジャンプ*: 実行のトレースを変える
- *移動*: メモリアクセスのパターンを変える

Valgrind は報告を出します。

未初期化の値が伝わる次の例を考えてみます。

```C {linenos=inline}
int main(){
  int x;
  int z[10] = {0};
  int y = x + 1;
  int a = z[y];
  return 0;
}
```

デバッグシンボルを有効にしたバイナリで Valgrind を実行すると、未初期化の値が使われている場所を特定する報告が出ます。

```bash
$ valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./main
...
==49626== Use of uninitialised value of size 8
==49626==    at 0x10916F: main (main.c:5)
==49626==  Uninitialised value was created by a stack allocation
==49626==    at 0x109139: main (main.c:1)
...
```

## Timecop のマクロ

Timecop は、定数時間の違反を検出する代わりとして、未初期化の値を追跡する Valgrind の機能を利用します。Valgrind の内部機能を使ってメモリ領域を手動で未定義と宣言し、これらの内部関数を C のマクロで包んでいます。

3 つの C マクロを提供します。

- `poison(addr, len)`: `[addr] <-> [addr+len]` のメモリ領域を未定義としてマークします。Valgrind は、実行中の条件ジャンプやメモリアクセスをすべて報告します。
- `unpoison(addr, len)`: メモリ領域を定義済みとしてマークし、poison の操作を元に戻します。
- `is_poisoned(addr, len)`: メモリ領域のどこかが poison されているかを確認します。

定数時間の違反の多くは、秘密の値に依存するメモリアクセスや制御フローの変化によって起こるため、これらの操作を追跡する Valgrind の能力を使えば、開発者がタイミングの脆弱性を見つけやすくなります。
重要な点として、Valgrind は、秘密の値に対する他の操作 (算術演算など) は報告しません。

## 例

以下は、イントロのセクションで説明した RSA で使われる、べき乗剰余の演算の簡単な例です。

```C {linenos=inline}
#include <stdio.h>
#include "valgrind/memcheck.h"

#define poison(addr, len) VALGRIND_MAKE_MEM_UNDEFINED(addr, len)
#define unpoison(addr, len) VALGRIND_MAKE_MEM_DEFINED(addr, len)
#define is_poisoned(addr, len) VALGRIND_CHECK_MEM_IS_DEFINED(addr, len)

typedef unsigned long long ull;

ull mod_exp(ull y, ull d, ull n) {
    ull r = 1;
    y = y % n;
    while (d > 0) {
        if (d & 1) {
            r = (r * y) % n;
        }
        y = (y * y) % n;
        d >>= 1;
    }
    return r;
}

ull rsa_decrypt(ull ct, ull d, ull n) {
    return mod_exp(ct, d, n);
}

int main() {
    ull n = 3233;
    ull d = 413;
    ull ciphertext = 2790;
    // Poison the memory location of the secret exponent d
    poison(&d, sizeof(ull));
    ull plaintext = rsa_decrypt(ciphertext, d, n);
    unpoison(&d, sizeof(ull));

    printf("pt: %llu\n", plaintext);
    return 0;
}
```

秘密の指数 `d` のメモリ領域を poison すると、この値が未初期化としてマークされ、Valgrind は、秘密の指数 `d` に基づく分岐やメモリアクセスをすべて報告します。
Valgrind は、時間に関する前提が満たされていない問題のあるコード行を正しく特定します。

```bash
$ valgrind --leak-check=full --show-leak-kinds=all --track-origins=yes ./toy_example

==72317== Conditional jump or move depends on uninitialised value(s)
==72317==    at 0x40115D: mod_exp (toy_example.c:14)
==72317==    by 0x4011E4: rsa_decrypt (toy_example.c:25)
==72317==    by 0x4012B7: main (toy_example.c:34)
==72317==  Uninitialised value was created by a client request
==72317==    at 0x40128C: main (toy_example.c:33)
==72317== 
==72317== Conditional jump or move depends on uninitialised value(s)
==72317==    at 0x40116F: mod_exp (toy_example.c:15)
==72317==    by 0x4011E4: rsa_decrypt (toy_example.c:25)
==72317==    by 0x4012B7: main (toy_example.c:34)
==72317==  Uninitialised value was created by a client request
==72317==    at 0x40128C: main (toy_example.c:33)
```

### GDB と連携した Valgrind のデバッグ

Valgrind は [GDB](https://www.sourceware.org/gdb/) と連携し、Valgrind が見つけたすべてのエラーで自動的に停止します。また、Valgrind 自体のプロセスのエミュレーション層を隠してくれるため、デバッグが簡単になります。
GDB でより多くの情報を得たい場合は、[pwndbg](https://github.com/pwndbg/pwndbg) の利用を検討してください。

デバッグを始めるには、次を実行します。

```bash
valgrind --vgdb=yes --vgdb-error=0 ./<binary>
```

これは、Valgrind に GDB モードで起動し、バイナリを実行する前に停止するよう指示します。
Valgrind は、GDB でバイナリをデバッグする方法の手順を表示します。
そのためには、正しいバイナリで GDB を起動する必要があり、GDB が起動したら、

```bash
$ gdb ./<binary>
> target remote | vgdb
```

これで GDB が Valgrind に接続し、報告されたエラーのたびに停止します。

## 制限事項 {#limitations}

1. **マイクロアーキテクチャのリーク**: Timecop と Valgrind は、個々の命令が、与えられた入力によって余分に時間がかかるかどうかを検出できません。
2. **カバレッジ**: この方法では、脆弱なコードが実行時に実行されなければ、潜在的な脆弱性を見つけられません。

Clang の [MemorySanitizer](https://clang.llvm.org/docs/MemorySanitizer.html) を使う別の方法は、ライブラリを必要とせずに同様の利点が得られますが、コンパイル時にバイナリを変更します。詳しい情報とチュートリアルは[こちら](https://crocs-muni.github.io/ct-tools/tutorials/memsan)にあります。
