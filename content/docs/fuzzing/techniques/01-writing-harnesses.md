---
title: "ハーネスの書き方"
slug: writing-harnesses
weight: 1
---

# ハーネスの書き方 {#writing-harnesses}

この節では、ファジングの設定で最も重要な部分であるファジングハーネスをうまく書くための手法を紹介します。ハーネスの出来が悪いと、アプリケーションの重要な部分がカバーされないことがあります。


## バイト配列だけではない入力 {#beyond-byte-arrays}

ファジングしたいコードは、単純なバイト配列だけでなく、もっと複雑な入力を受け取ることがよくあります。ごく基本的な例が、次の 0 による除算を含むファジングテストです。関数 `divide` への入力は 2 つの整数なので、工夫して、バイト配列からそれらを作り出す必要があります。ここでは、生のバイト列を 32 ビット整数に単純にキャストして作ります。バイト配列は、システムのアーキテクチャ（リトルエンディアンかビッグエンディアンか）によって解釈が変わることがあるので注意してください。

次のハーネスを使えば、どのファザーでもこのバグをすぐに見つけられます。




{{< tabs "beyond" >}}
{{< tab "C/C++" >}}
```C++
#include <stdint.h>
#include <stdlib.h>

double divide(uint32_t numerator, uint32_t denominator) {
    // Bug: No check if denominator is zero
    return numerator / denominator;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    // Ensure exactly 2 4-byte numbers (numerator and denominator) are read
    if(size != 2 * sizeof(uint32_t)){
        return 0;
    }

    // Split input into numerator and denominator
    int numerator = *(uint32_t*)(data);
    int denominator = *(uint32_t*)(data + sizeof(uint32_t));

    divide(numerator, denominator);

    return 0;
}
```

{{< /tab >}}

{{< tab "Rust" >}}
```Rust
#![no_main]

use libfuzzer_sys::fuzz_target;
use std::slice;

pub fn divide(numerator: i32, denominator: i32) -> i32 {
    // Rust automatically checks for division by zero at runtime,
    // so we don't need an explicit check.
    numerator / denominator
}

fuzz_target!(|data: &[u8]| {
    if data.len() != 2 * std::mem::size_of::<i32>() {
        return;
    }

    // Split input into numerator and denominator
    let numerator = i32::from_ne_bytes([data[0], data[1], data[2], data[3]]);
    let denominator = i32::from_ne_bytes([data[4], data[5], data[6], data[7]]);

    divide(numerator, denominator);
});
```
{{< /tab >}}
{{< /tabs >}}


次の文字列連結関数のように、もっと複雑な C/C++ の例になると、補助クラス [`FuzzedDataProvider`](https://github.com/llvm/llvm-project/blob/main/compiler-rt/include/fuzzer/FuzzedDataProvider.h) を使いたくなるかもしれません。このヘッダはプロジェクトにコピーして、次のように使えます。

```C++
#include <stdint.h>
#include <stdlib.h>
#include "./FuzzedDataProvider.h"

char* concat(const char* inputStr, size_t inputStrLen,
    const char* anotherStr, size_t anotherStrLen,
    size_t allocation_size) {

    if (allocation_size <= 1 || allocation_size > 1 << 16) {
        return NULL;
    }

    char* result = (char*)malloc(allocation_size);

    if (result == NULL) {
        return NULL;
    }

    memcpy(result, inputStr, inputStrLen);
    memcpy(result + inputStrLen, anotherStr, anotherStrLen);

    return result;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    FuzzedDataProvider fuzzed_data(data, size);

    size_t allocation_size = fuzzed_data.ConsumeIntegral<size_t>();

    std::vector<char> str1 =
        fuzzed_data.ConsumeBytesWithTerminator<char>(32, 0xFF);

    std::vector<char> str2 =
        fuzzed_data.ConsumeBytesWithTerminator<char>(32, 0xFF);

    char* concatenated = concat(&str1[0], str1.size(), &str2[0], str2.size(), allocation_size);
    if (concatenated != NULL) {
        free(concatenated);
    }

    return 0;
}
```


上の例は、2 つの C 形式の文字列と最大割り当てサイズを受け取るパラメータを持つ concat 関数をファジングします。ただし、この関数にはバグがあります。文字列の長さの合計が、割り当てサイズに対して検査されていません。そのため、割り当てサイズが小さすぎると、`memcpy` 関数がバッファオーバーフローを起こします。

ハーネス関数 `LLVMFuzzerTestOneInput` は、`FuzzedDataProvider` を使って、整数を 1 つ、続いてデータ文字列を 2 つ読み取ります。データ文字列の長さは、区切りによって決まります。

内部では、`FuzzedDataProvider` クラスが可変長データの消費を処理します。最初の文字列では、ほかのデータと区切るために、マジック値 `0xFF` を使っています。たとえば、入力が 2 つの文字列だけでできているなら、値 `\FF` で入力を区切れます。`Hello World\FFHello Trail of Bits\FF` のようにです。

文字列と整数が混ざる場合は、`0xB105F00D` のような、より複雑な区切りに頼る必要があるかもしれません。理論上は、この値で入力を分割できます。`Hello World\xB1\x05\xF0\x0DHello Trail of Bits\xB1\x05\xF0\x0D\x0F` のようにです。ただし、区切りのデータ型はデータの型と一致していなければならないため、`FuzzedDataProvider` ではこれはできません。バイト配列を扱う場合、区切りにできるのは 1 バイトだけです。

この節で説明した上の手法は、[libFuzzer の Google 版ドキュメント](https://github.com/google/fuzzing/blob/master/docs/split-inputs.md)でも説明されています。

より高度な使い方が、次のプロのヒントで取り上げる構造化ファジングです。一般に、構造化ファジングはより多くの設定が必要ですが、変異によって入力が解析できなくなることがないため、ファジングの性能を高められます。 <!-- revise this with a structured fuzzing sections -->

{{< hint info >}}
プロのヒント: 上の考え方を一般化すると、何らかのデータ形式がほしいことが多い、という結論になります。上の例では、形式は単純で、8 バイトの配列に 2 つの整数が入っていると想定しています。もっと複雑な形式なら、任意のデータをエンコードできるでしょう。

ただし、ほとんどのデータ形式はこの目的には向きません。ファザーによるわずかな変更で、入力全体が無効になってしまうためです。たとえば、JSON ファイルから 1 文字（たとえば `2`）を削除したり変更したりすると、パーサがデシリアライザで失敗することがあります。
```json
{
    "numerator": 9,
    "denominator": 2̶
}
```

対照的に、バイナリの入力データ形式では、どのビットを反転しても、新しく、興味深い可能性のある入力が生まれます（ファザーは、入力がどれも 8 バイトちょうどであることを学習するだけでよいのです）。

まとめると、プログラムが複雑な入力を想定しているなら、適切なデータ形式という観点で考えます。

入力が高度に構造化されているなら、libFuzzer の[protobuf メッセージのフィールドをファジングするカスタムミューテータ](https://github.com/google/fuzzing/blob/master/docs/structure-aware-fuzzing.md#protocol-buffers-as-intermediate-format)を調べるとよいでしょう。入力のデータ形式として protobuf を使い、カスタマイズしたミューテータによって、protobuf の形式自体ではなく、中身をファジングできます。これはすでに、文法ファザーに近いものです。
{{< /hint >}}





## インターリーブ型ファジング {#interleaved-fuzzing}

ファジングハーネスへの入力を使って、対象のどのコードを実行するかを操れます。これは、対象にある関連する複数の API を動かすときに役立ちます。複数の算術演算が使える次の例を見てください。すべての演算は、入力としてちょうど 2 つの double を取ります。入力の最初のバイトに基づいてすべての関数を実行する、1 つのファジングハーネスを書けます。

次のコードは、ハーネスを定義し、整数の加算・減算・乗算・除算ができる SUT を実装します。ハーネスは最初のバイトを取り、それに基づいていずれかの命令を実行すると決めます。続いて、入力から 2 つの整数を解析し、算術演算を呼び出します。ハーネスは、入力が十分な長さであることも確認します。

実装がクラッシュしないように、`divide` 関数は、除数が 0 でないことと、除算でオーバーフローが起きないことを確認する必要があります。その後、算術関数（`add`、`subtract`、`multiply`、`divide`）の呼び出しがコンパイルの最適化で取り除かれないように、結果の値を出力します。


{{< tabs "interleaved" >}}
{{< tab "C/C++" >}}
```C++
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <limits.h>

int32_t add(int32_t a, int32_t b);
int32_t subtract(int32_t a, int32_t b);
int32_t multiply(int32_t a, int32_t b);
int32_t divide(int32_t a, int32_t b);

int32_t add(int32_t a, int32_t b) {
    return a + b;
}

int32_t subtract(int32_t a, int32_t b) {
    return a - b;
}

int32_t multiply(int32_t a, int32_t b) {
    return a * b;
}

int32_t divide(int32_t a, int32_t b) {
    // Avoid division by zero and int overflow
    if (b != 0 && !(a == INT_MIN && b == -1)) {
        return a / b;
    }
    return 0;
}

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size) {
    if (size < 1 + 2 * sizeof(int32_t)) {
        return 0;
    }

    uint8_t mode = data[0];
    int32_t numbers[2];
    int32_t r = 0;
    memcpy(numbers, data + 1, 2 * sizeof(int32_t));

    // We select functions based on the first byte of the fuzzing data
    switch (mode % 4) {
    case 0:
        r = add(numbers[0], numbers[1]);
        break;
    case 1:
        r = subtract(numbers[0], numbers[1]);
        break;
    case 2:
        r = multiply(numbers[0], numbers[1]);
        break;
    case 3:
        r = divide(numbers[0], numbers[1]);
        break;
    }

    printf("%d", r);

    return 0;
}
```
{{< /tab >}}

{{< tab "Rust" >}}
```Rust
#![no_main]
use libfuzzer_sys::fuzz_target;

pub trait Arithmetic: Sized {
    fn add(self, other: Self) -> Self;
    fn subtract(self, other: Self) -> Self;
    fn multiply(self, other: Self) -> Self;
    fn divide(self, other: Self) -> Option<Self>;
}

impl Arithmetic for f64 {
    fn add(self, other: Self) -> Self {
        self + other
    }

    fn subtract(self, other: Self) -> Self {
        self - other
    }

    fn multiply(self, other: Self) -> Self {
        self * other
    }

    fn divide(self, other: Self) -> Option<Self> {
        if other == 0.0 { None } else { Some(self / other) }
    }
}

fuzz_target!(|data: &[u8]| {
    if data.len() < 1 + 2 * std::mem::size_of::<f64>() {
        return;  // Not enough data for mode and two f64 numbers
    }

    let mode = data[0];
    let numbers = &data[1..];

    if let [first, second] = *bytemuck::try_cast_slice::<_, f64>(numbers).unwrap_or_else(|_| &[0.0, 0.0]) {
        match mode % 4 {
            0 => { first.add(second); },
            1 => { first.subtract(second); },
            2 => { first.multiply(second); },
            3 => { first.divide(second); },
            _ => {}
        }
    }
});
```
{{< /tab >}}
{{< /tabs >}}


インターリーブ型ファジングには、複数の利点があります。
* 対象によっては、個別のファジングハーネスを書くよりも、より広い範囲を動かす 1 つのハーネスを書くほうが早いことがあります。
* ハーネスが 1 つということは、コーパスも 1 つということです。そのため、実装した演算やファジングテストのあいだで、テストケースが関連していることを確かめてください。除算にとって興味深い入力は、減算にとっても興味深いことがあります。


## ハーネスの実践的なルール {#practical-harness-rules}

ハーネスは任意のコードを実行できますが、ハーネスを実装するときは、いくつかのルールに従うと有益です。これらは、libFuzzer の公式[ドキュメント](https://llvm.org/docs/LibFuzzer.html#id23)を元にしています。

実際、これらの指針は、ハーネスのコードだけでなく、SUT のコードベース全体にも当てはまります。SUT にパッチを当てる方法は、「SUT へのパッチ: 障害を乗り越える」の節（[C/C++]({{% relref "/docs/fuzzing/c-cpp/techniques/02-obstacles#sut-patching-overcoming-obstacles" %}})、[Rust]({{% relref "/docs/fuzzing/rust/techniques/02-obstacles#sut-patching-overcoming-obstacles" %}})）を参照してください。

ファジングハーネスを実装するときは、書く言語に関係なく、次の点を考慮してください。



* ハーネスは、空の入力、巨大な入力、不正な形式の入力など、あらゆる入力を処理しなければならない。たとえば、大きな入力が、ハーネスのコードが原因で想定外のメモリ不足を起こしてはならない。 \
**理由:** ファザーはランダムな入力でハーネスを呼び出すため、ハーネスは、あらゆる入力を定められた方法で処理できるように備えておく必要があります。
* [`exit`](https://man.archlinux.org/man/exit.3p) 関数を呼んではならない。 \
**理由:** exit を呼ぶと、ファジングを含むプロセス全体が止まります。回復できない状況を知らせたい場合は、SUT の中で [`abort`](https://man.archlinux.org/man/abort.3p) を呼びます。

* スレッドを使う場合は、`LLVMFuzzerTestOneInput` 関数の終わりで、すべてのスレッドを [`joined`](https://man.archlinux.org/man/pthread_join.3p) の状態（pthread_join 済み）にしなければならない。 \
**理由:** 呼び出しはそれぞれ独立して行い、最後まで完了させてから、次のファジングのテストケースに進むべきです。
* ハーネスは速くあるべきで、高い複雑さ、ログ出力、過剰なメモリ使用は避ける。 \
**理由:** 速度は、ファジングの成否に大きく影響します。1 秒あたりの実行回数を十分に得る（通常は 1 コアあたり数百〜数千回）には、SUT を速く実行することが重要です。メモリ使用量が少なければ、より多くのコアで並列にファジングできます。
* ハーネスは決定性を保ち、乱数や、入力に基づかない判断のような非決定性は避ける。たとえば、`/dev/random` からの読み取りは避ける。 \
**理由:** SUT がクラッシュしたら、ファジングキャンペーンが終わったあとで、そのクラッシュを再現できるべきです。ハーネスに非決定性を加えると、バグがファジング中に一度しか起きず、再現できなくなる可能性が高くなります。
* グローバルな状態の変更は、できるだけ避ける。たとえば、[PRNG](https://en.wikipedia.org/wiki/Pseudorandom_number_generator) のグローバルな状態に依存する [rand](https://man.archlinux.org/man/rand.3) の呼び出しは避ける。[シングルトン](https://en.wikipedia.org/wiki/Singleton_pattern)パターンはグローバルな状態を伴うため、避ける。 \
**理由:** 非決定性と同様に、グローバルな状態が原因で、テストケースがファジング中にしかクラッシュせず、あとではクラッシュしなくなることがあり、再現性が制限されます。たとえば、SUT の実行中にシングルトンがデータのサンプルを集めますが、クラッシュするまでに集められるのは `n` 個までだとします。実行のたびにグローバルな状態をリセットしないと、SUT は `n` 回の実行後にクラッシュするかもしれません。`n` 回目の実行の入力が原因ではなく、グローバルな状態が原因です。
* 対象は絞るのがよい。関連のない複数のデータ形式は、個別の対象に分ける。 \
**理由:** PNG と TCP パケットを 1 回のキャンペーンでファジングしても、あまり意味はないでしょう。PNG で見つかったコーパスのエントリは、TCP パケットのファジングには、まず関係がないためです。
