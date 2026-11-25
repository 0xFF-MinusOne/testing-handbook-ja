---
title: "SUT へのパッチ適用: 障害を乗り越える"
slug: obstacles
weight: 2
---

# SUT へのパッチ適用: 障害を乗り越える {#sut-patching-overcoming-obstacles}

コードベースは、ファジングに向いていないことがよくあります。たとえば、コードがチェックサムを使っている場合や、システム時刻をシードとする PRNG（たとえば [`rand`](https://man.archlinux.org/man/rand.3) を使うもの）のようなグローバルな状態に依存している場合です。こうしたコードは、同じ入力でも異なる動きをします。SUT で起こりうる問題については、[ハーネスの実践的なルール]({{% relref "01-writing-harnesses#practical-harness-rules" %}})を参照してください。SUT にチェックサムやグローバルな状態がある場合は、以降の段落で示すように、ファジング専用のパッチを当てて、ファジング中のプログラムの挙動を変えるとよいでしょう。 

C/C++ のファザーは通常、マクロ `FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` を定義します。少なくとも libFuzzer、AFL++、LibAFL、Hongfuzz ではそうです。このマクロが定義されていれば、プログラムはファジング用にコンパイルされています。このマクロにもとづく条件付きコンパイルを使うと、コード内の障害を乗り越えられます。たとえば、ファザーがコードの深い経路まで到達する妨げになりがちな、ハッシュ値のチェックです。次の図に例を示します。




{{< customFigure "`FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` の使用例" >}}
```C++
if (checksum != expected_hash) {
// Eliminate the need for guessing checksums by ignoring this error during fuzzing
#ifndef FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION
  return -1;
#endif
}

// Continue program execution
```
{{< /customFigure >}}


この方法では、ファジング中と本番とで SUT の挙動が異なることに注意してください。チェックを不用意に省くと、ファジング中に誤検知を招くことがあります。たとえば、設定ファイルの検証を省くと、設定値が特定の形式であることをコードが前提としているため、SUT がクラッシュするかもしれません。検証で、設定にゼロ以外の整数が含まれることを保証している場合、検証の後に呼ばれるコードは、ゼロの値に出会うと正しく動かなくなる可能性があります。次の例を参照してください。



{{< customFigure "設定の検証を省く `FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION` の問題のある使い方。ファジング中に誤検知を招くことがあります。" >}}
```C++
#ifndef FUZZING_BUILD_MODE_UNSAFE_FOR_PRODUCTION
if (!validate_config(&config)) {
    // return error if config contains zero values
    return -1;
}
#endif

// assume no negative values exist

int32_t result = 100 / config.x; // Can crash if validation is skipped
```
{{< /customFigure >}}

このマクロを実際に使っている例が、OpenSSL プロジェクトにあります。暗号アルゴリズムの動きを変えるために、[このマクロを使っています](https://github.com/openssl/openssl/blob/afb19f07aecc84998eeea56c4d65f5e0499abb5a/crypto/cmp/cmp_vfy.c#L665-L678)。
