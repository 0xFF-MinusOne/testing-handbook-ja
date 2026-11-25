---
title: "ファジング用の辞書"
slug: dictionary
weight: 2
---

# ファジング用の辞書 {#dictionary-fuzzing}

辞書を使うと、ファザーを誘導できます。辞書は、たいていファイルとしてファザーに渡します。libFuzzer が受け付ける最も単純な入力は、各行が引用符で囲んだ文字列になっている ASCII テキストファイルです。文字列には、"`\xF7\xF8"` のようなエスケープしたバイト列を含められます。説明用に、`hex_value="\xF7\xF8"` のようなキーと値の組を使うこともできます。行頭を `#` にするとコメントになります。次の例を見てください。



{{< customFigure "辞書ファイルの例。ほかの例は[こちら](https://github.com/AFLplusplus/AFLplusplus/tree/ef706ad668b36e65d24f352f5bcee22957f5f1cc/dictionaries)" >}}
```conf
# Lines starting with '#' and empty lines are ignored.

# Adds "blah" (w/o quotes) to the dictionary.
kw1="blah"
# Use \\ for backslash and \" for quotes.
kw2="\"ac\\dc\""
# Use \xAB for hex values
kw3="\xF7\xF8"
# the name of the keyword followed by '=' may be omitted:
"foo\x0Abar"
```

{{< /customFigure >}}


辞書は、libFuzzer、cargo-fuzz、AFL++ の各ファザーで共通して使えます。使い方は次の表のとおりです。


|||
|--- |--- |
|`libFuzzer`|`./fuzz -dict=./dictionary.dict ...`|
|`AFL++`|`afl-fuzz -x ./dictionary.dict ...`|
|`cargo-fuzz`|`cargo fuzz run fuzz_target -- -dict=./dictionary.dict`|
{.skip-table-head}

## 辞書を作る {#generating-a-dictionary}

辞書を作る方法はいくつかあります。



* LLM(大規模言語モデル): OpenAI の ChatGPT のようなツールは、ファジングの対象に合った辞書を作るのに役立ちます。ただし、LLM のハルシネーション(事実でない内容の生成)に注意してください。このハンドブックに載っていない機能を LLM が提案してきたら、本当に存在するかをまず確かめます。タスクを `PNG parser` にして、次の LLM 用プロンプトを試してみてください。
    ```text {.code-fence-wrap}
    A dictionary can be used to guide the fuzzer. A dictionary is passed as a file to the fuzzer usually.
    The simplest input accepted by libFuzzer is an ASCII text file where each line consists of a quoted string. Strings can contain escaped byte sequences like "\xF7\xF8". Optionally, a key-value pair can be used like hex_value="\xF7\xF8" for documentation purposes. Comments are supported by starting a line with #. Write me an example dictionary file for a <fuzzing task>:
    ```
* ヘッダファイル: 関連する文字列を含む C のヘッダファイルが見つかったら、次のコマンドでそれらを取り出せます。
    ```shell
    grep -o '".*"' header.h > header.dict
    ```
* man ページ: ファジングするプロジェクトに man ページがあれば、それを使って辞書を作れます。CLI をファジングするときに特に役立ちます。
    ```shell
    man curl | grep -oP '^\s*(--|-)\K\S+' | sed 's/[,.]$//' | sed 's/^/"&/; s/$/&"/' | sort -u > man.dict
    ```
* AFL++ の [AUTODICTIONARIES](https://github.com/AFLplusplus/AFLplusplus/blob/108fb0b29ad1586e668ba23e23a0eb1a13c45c49/instrumentation/README.lto.md#autodictionary-feature): `afl-clang-lto` を使っていれば、AFL++ がファジング対象のバイナリをもとに辞書を自動で作ります。
* AFL++ を使っていない場合は、strings コマンドで辞書を作る方法があります。
    ```shell
    strings ./binary | sed 's/^/"&/; s/$/&"/' > strings.dict
    ```