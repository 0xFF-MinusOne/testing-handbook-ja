---
title: "SUT へのパッチ: 障害の克服"
slug: obstacles
weight: 2
---


# SUT へのパッチ: 障害の克服 {#sut-patching-overcoming-obstacles}
<!-- TODO Candidate for becoming a general Rust Technique in V2 -->

コードベースは、ファジングに向いていないことがよくあります。たとえば、コードがチェックサムを使っていたり、システム時刻でシードされる PRNG([rand](https://docs.rs/rand/latest/rand/) など)のようなグローバルな状態に依存していたりすると、同じ入力でもコードの挙動が変わってしまいます。SUT で起こりうる問題の詳細は、[実践的なハーネスの規則]({{% relref "01-writing-harnesses#practical-harness-rules" %}})を参照してください。SUT にチェックサムやグローバルな状態がある場合は、以降の段落で示すように、ファジング専用のパッチを当てて、ファジング中のプログラムの挙動を変えるとよいでしょう。 

Rust のファザーは、Rust プロジェクトのコンパイル時に設定される構成オプションを定義しています。[`cfg!(test)`](https://doc.rust-lang.org/reference/conditional-compilation.html#test) という構成オプションと同様に、`cfg!(fuzzing)` オプションはファジング中に有効になります。条件付きコンパイルを使うと、コード内の障害を乗り越えられます。たとえば、ハッシュの検査は、ファザーがより深いコードパスのカバレッジに到達するのをよく妨げます。次の図に例を示します。

{{< customFigure "`cfg!(fuzzing)` の使用例" >}}
```Rust
if checksum != expected_hash {
    // Eliminate the need for guessing checksums by ignoring this error during fuzzing
    if !cfg!(fuzzing) {
        return Err(MyError::Hash)
    }
}

// Continue program execution
```
{{< /customFigure >}}



これは、SUT がファジング中と本番とで異なる挙動をするということです。検査を安易に省略すると、ファジング中に誤検知を招くことがあります。たとえば、設定ファイルの検証を省略すると、コードが設定値に一定の形式を期待しているために、SUT がクラッシュするかもしれません。検証で、設定に 0 以外の整数が入っていることを保証している場合、検証のあとに呼ばれるコードは、値が 0 だと正しく動かなくなる可能性があります。次の例を見てください。


{{< customFigure "設定の検証を省略する `cfg!(fuzzing)` の問題のある使い方。ファジング中に誤検知を招くことがあります。" >}}
```Rust
if !cfg!(fuzzing) {
    config.validate()?; // return error if config contains zero values
}

// assume no negative values exist

let result = 100 / config.x; // Can crash if validation is skipped
```

{{< /customFigure >}}

たとえば、ogg クレートは `cfg!(fuzzing)` を使って、[プロジェクトをファジングしていないときだけチェックサムの検査を行っています](https://github.com/RustAudio/ogg/blob/5ee8316e6e907c24f6d7ec4b3a0ed6a6ce854cc1/src/reading.rs#L298-L300)。`cfg!(fuzzing)` の検査を追加すると、ファジングのカバレッジを大きく伸ばせますが、ソースコードの変更が必要です。
