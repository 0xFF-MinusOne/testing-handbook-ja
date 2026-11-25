---
title: "Dudect"
weight: 45
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
---
# Dudect

{{< math >}}

## 概要

[Dudect](https://github.com/oreparaz/dudect/) は、統計に基づく定数時間の解析ツールです。特定の*コード区間*の実行時間を 2 つの*入力クラス*について測定し、2 つのクラスの測定値の統計的な差を見つけることを目指します。
2 つの入力クラスの時間の測定値が互いにずれていれば、そのコードは入力に依存していて、したがって定数時間ではないことが示唆されます。
最もよく使われる 2 つの入力クラスは次のとおりです。

1. **固定の入力クラス**: \(\mathbf{A}=\{a,a,\cdots,a\}, |A|=n\)
2. **ランダムな入力クラス**: \(\mathbf{B}=\{b_1,b_2,\cdots,b_n\},|B|=n\)

解析対象のコード区間は、ランダムに選ばれた入力 \(i \in \{\mathbf{A}, \mathbf{B}\}\) を受け取ります。
Dudect は時間の測定を複数回行い、入力 \(i\) の入力クラス \(\{\mathbf{A},\mathbf{B}\}\) に基づいて分類します。
ユーザーが指定した回数の測定を集めたあと、[Welch の t 検定](https://en.wikipedia.org/wiki/Welch%27s_t-test)で、2 つの測定値の集合の差を評価します。
有意な差があれば、t 値にそれが表れ、コードの実行時間が入力によって変わることを示します。

## セットアップ

Dudect は現在 x86 アーキテクチャに対応しており、ARM 系のアーキテクチャ向けには[プルリクエスト](https://github.com/oreparaz/dudect/pull/36)があります。
Dudect を使い始めるには、すべての内部関数を定義しているヘッダファイル `dudect.h` をインクルードします。

```c
#define DUDECT_IMPLEMENTATION
#include "dudect.h"
```

Dudect は C の数学ライブラリ `<math.h>` を使うため、コンパイラは `-lm` フラグでそのライブラリをリンクする必要があります。

{{< tabs "beyond" >}}
{{< tab "gcc" >}}

```bash
gcc -lm ct_test.c -o ct_test
```

{{< /tab >}}
{{< tab "clang" >}}

```bash
clang -lm ct_test.c -o ct_test
```

{{< /tab >}}
{{< /tabs >}}

これで、コンパイラは必要なファイルをすべてリンクしますが、ユーザーが実装すべき 2 つの関数が足りないため失敗します。
以下では、この 2 つの関数が何をするかと、Dudect の設定方法を説明します。

## Dudect の使い方

Dudect は、異なる入力を使って、特定のコード区間の実行時間を測定します。
主に 2 つの情報が必要です。

1. どのコード区間を測定するか?  \(\rightarrow\) `do_one_computation`
2. コードにどの入力を与えるか? \(\rightarrow\) `prepare_inputs`

### 計算を 1 回行う

`do_one_computation` 関数の中に書いたコードは、すべて Dudect が時間を測定します。

```c
uint8_t do_one_computation(uint8_t *data) {
    ...
}
```

Dudect は、ランダムに選んだ入力クラスのいずれかの入力データで、この関数を複数回実行します。

### 入力を準備する

計算関数に与える入力は `prepare_inputs` 関数の中で実装し、`do_one_computation` の時間を測る前に毎回呼ぶのではなく、まとめて事前に計算します。

```c
void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes){
    for (size_t i = 0; i < c->number_measurements; i++) {
        classes[i] = randombit();
        uint8_t *input = input_data + (size_t)i * c->chunk_size;
        if (classes[i] == 0) {
            ... // Input class A
        } else {
            ... // Input class B
        }
    }
}
```

すべての入力データは `input_data` 配列に順に格納され、各入力のクラスはランダムに決まります。
Dudect は、このデータを `do_one_computation` 関数の入力として使います。
Welch の t 検定では、どの入力がどの入力クラスに属するかを Dudect が知っている必要があります。
そのため、`classes` 配列に入力クラスを示す 1 か 0 を入れ、t 検定による解析に役立てます。

最後に、各入力に必要なサイズと、1 回の反復で行う測定の回数を、Dudect に設定します。

```c
dudect_config_t config = {
    .chunk_size = /* Size of a single input */,
    .number_measurements = ...,
};
dudect_ctx_t ctx;
dudect_init(&ctx, &config);
```

`dudect_init(&ctx, &config);` 関数は、入力データや時間の測定値などを格納するのに必要なメモリ領域をすべて確保します。

### Dudect のループ

時間の測定値を取得するために `dudect_main(&ctx)` を呼び出します。この関数は次のことを行います。

1. `prepare_inputs` を呼び出してすべての入力を事前に計算し、連続した `ctx->input_data` 配列に格納します。
2. `do_one_computation` 関数を `number_measurements` 回実行し、時間を測定します。
3. 集めた測定値の統計を更新し続け、表示します。

しきい値を較正するため、関数 `dudect_main` は少なくとも 2 回呼び出す必要があります。
有意な差が検出されるまで、無限ループで実行できます。

```c
int run_test(void) {
    ...
    dudect_state_t state = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
    while (state == DUDECT_NO_LEAKAGE_EVIDENCE_YET) {
        state = dudect_main(&ctx);
    }
    dudect_free(&ctx);
    return (int)state;
}
```

指定した時間だけプロセスを実行するには、`timeout` コマンドを使います。

```bash
timeout <NumberOfSeconds> ./ct_test
```

Dudect は、反復のたびに t 検定で新しい統計を計算して報告します。例:

```none
meas:    1.20 M, max t:   +1.61, max tau: 1.47e-03, (5/tau)^2: 1.16e+07. For the moment, maybe constant time.
```

`t-value` の絶対値が大きい場合は、時間にばらつきがある可能性を示し、データに依存する実行経路があることを意味します。
Dudect が一貫して測定結果を `maybe constant time` と報告するなら、検出された時間の差は統計的に有意ではないということです。

## 測定精度を上げる

Dudect が潜在的な時間のリークを検出できるようにするには、入力クラス間の時間の差を覆い隠しかねないノイズを減らすことが重要です。
Dudect は外れ値の測定を統計的に取り除きますが、それでも多くの測定が必要になることがあります。
測定が正確であれば、リークの検出に必要な時間を短くできます。
集めた測定値の精度を上げるために、次のことをおすすめします。

**コードのノイズを減らす**:
テストしたい特定の関数だけを実行し、*鍵の生成*や*暗号の初期化*のような、オーバーヘッドを増やしうる処理を避けます。

**オペレーティングシステムのノイズを減らす**:
とくに短いコード区間で正確に測定するには、オペレーティングシステムからのノイズを減らします。
ノイズを減らすには、**プロセスを CPU コアに固定**し、**そのコアを分離**します。
そうすると、実行中のコンテキストスイッチの回数が減り、より一貫した正確な測定ができます。

プロセスをコアに固定するには、`taskset` コマンドを使います。

```bash
taskset -c 2 ./ct_test
```

コア 0 と 1 は、OS が他のタスクに使うことが多いため避けます。
タスクを固定すると、プロセスを別の CPU で実行する間のキャッシュの無効化に伴う性能の低下を防げます。
さらにノイズを減らすには、特定のカーネルのブートパラメータの設定を検討してください。
詳しくは、この[ガイド](https://manuel.bernhardt.io/posts/2023-11-16-core-pinning/)を参照してください。

## テンプレート

Dudect は、AES などの暗号の[サンプルコード](https://github.com/oreparaz/dudect/tree/master/examples)を提供しており、出発点として適しています。
次は、始めるのに使える簡単なテンプレートです。

```c
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define DUDECT_IMPLEMENTATION
#include "dudect.h"

/* this will be called over and over */
uint8_t do_one_computation(uint8_t *data)
{
    // ToDo: Implement the code you want to test
    <CODE TO MEASURE>
}

void prepare_inputs(dudect_config_t *c, uint8_t *input_data, uint8_t *classes)
{
    for (size_t i = 0; i < c->number_measurements; i++)
    {
        classes[i] = randombit();
        uint8_t *input = input_data + (size_t)i * c->chunk_size;
        if (classes[i] == 0)
        {
            // ToDo: Specify the input data for the first input class
            <INPUT CLASS A>
        }
        else
        {
            // ToDo: Specify the input data for the second input class
            <INPUT CLASS B>
        }
    }
}

int run_test(void)
{
    dudect_config_t config = {
        // ToDo: Set the required size for a singular input
        .chunk_size = <INPUT SIZE NEED FOR ONE COMPUTATION>,
        // ToDo: Set the number of measurements that should be performed per iteration
        .number_measurements = <MEASUREMENTS PER ITERATION>,
    };
    dudect_ctx_t ctx;

    dudect_init(&ctx, &config);

    dudect_state_t state = DUDECT_NO_LEAKAGE_EVIDENCE_YET;
    while (state == DUDECT_NO_LEAKAGE_EVIDENCE_YET)
    {
        state = dudect_main(&ctx);
    }
    dudect_free(&ctx);
    return (int)state;
}

int main(int argc, char **argv)
{
    run_test();
}
```

上のテンプレートのコードは、測定値に有意な差が出て、コードが定数時間ではないと判断されるまで、無限ループで実行されます。

### CI のセットアップ

新しい変更で入り込む時間のリークを検出するには、常時の監視が欠かせません。
継続的にテストすることで、新しいコードを入れたときに定数時間という前提が破られないようにできます。

次の bash スクリプトは、始めるためのテンプレートとして使えます。
次のファイル構成を前提としています。

```none
┣ 📂 tests
┃   ┣ 📜 ct_test.c // Contains the dudect loop
┃   ┗ 📜 dudect.h
```

この bash スクリプトを実行すると、`clang` で `ct_test.c` ファイルを自動的にコンパイルし、`taskset -c 2` で 2 番目のコアでバイナリを実行して、5 分後に実行を止めます。
実際の運用では、測定が多いほど dudect が時間の差を検出する確率が高くなるため、できれば 5 分より長くテストを実行するのが望ましいです。

```bash
#!/bin/bash

# Set the path to the test folder
TEST_DIR="tests"
TEST_FILENAME="ct_test.c"
TEST_DURATION="300s"
CT_TEST="$TEST_DIR/$TEST_FILENAME"
DUDECT_HEADER="$TEST_DIR/dudect.h"

OUTPUT_BINARY="ct_test_bin"
clang -lm -DDUDECT_IMPLEMENTATION -o $OUTPUT_BINARY $CT_TEST

if [ $? -ne 0 ]; then
  echo "Compilation failed."
  exit 1
fi

# Run the compiled binary with taskset on core 2 and timeout
TASKSET_CMD="taskset -c 2"
TIMEOUT_CMD="timeout $TEST_DURATION"
$TASKSET_CMD $TIMEOUT_CMD ./$OUTPUT_BINARY

# Capture the return status of the binary
RETURN_STATUS=$?

# Analyze the return status
if [ $RETURN_STATUS -eq 0 ]; then
  echo "No timing vulnerability detected within the specified time."
  exit 0
elif [ $RETURN_STATUS -eq 124 ]; then
  echo "No timing vulnerability detected within the specified time."
  exit 0
else
  echo "Test failed. Timing vulnerability detected."
  exit 1
fi
```

このスクリプトを定期的に実行すると、ライブラリに入った新しい変更が定数時間という前提を破らないことを確認できます。

## 制限事項 {#limitations}

1. **保証はない**:
Dudect の時間の測定は、条件が許す範囲で信頼できるにすぎません。
`do_one_computation` の中のセキュリティに無関係なコードがノイズを生み、リークの信号を覆い隠すことがあります。
Dudect がリークを見つけなくても、コードにタイミングの脆弱性がないことは保証されません。

2. **システムへの依存**:
結果は、アーキテクチャやシステムの状態によって変わりえます。
同時に動くプロセスが多いマシンではリークの信号を検出できないことがあり、別のマシンでは結果を再現できないことがあります。

3. **さらなる調査が必要**:
Dudect がリークを検出しても、その原因の場所までは特定しません。
TimeCop のような他のツールが、リークの特定に役立ちます。
