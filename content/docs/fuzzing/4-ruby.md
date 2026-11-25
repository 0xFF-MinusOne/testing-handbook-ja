---
title: "Ruby"
slug: ruby
weight: 4
---


# Ruby

Ruby のコードのファジングには、[Ruzzy](https://github.com/trailofbits/ruzzy) をお勧めします。

## インストール

Ruzzy は Linux x86-64 と AArch64/ARM64 に対応しています。macOS や Windows で Ruzzy を動かしたい場合は、[`Dockerfile`](https://github.com/trailofbits/ruzzy/blob/main/Dockerfile) をビルドするか、[開発環境](https://github.com/trailofbits/ruzzy#developing)を使ってください(両方でも構いません)。Ruzzy には新しいバージョンの `clang`(`14.0.0` まで遡って動作を確認)が必要で、できれば[最新のリリース](https://github.com/llvm/llvm-project/releases)を使ってください。

次のコマンドで Ruzzy をインストールします。

```bash
MAKE="make --environment-overrides V=1" \
CC="/path/to/clang" \
CXX="/path/to/clang++" \
LDSHARED="/path/to/clang -shared" \
LDSHAREDXX="/path/to/clang++ -shared" \
    gem install ruzzy
```

ここでは多くのことをしているので、順に見ていきましょう。

- 環境変数 `MAKE` は、Ruzzy の C 拡張をコンパイルするときの `make` コマンドを上書きします。これにより、拡張のコンパイル時に、後に続く環境変数を `make` に尊重させます。
- 残りの環境変数は、コンパイル時に適切な `clang` のバイナリを使うためのものです。これにより、正しいファジングに必要な最新の `clang` の機能が使えます。

インストールで問題が起きたときは、次のコマンドでデバッグ出力を得られます。

```bash
RUZZY_DEBUG=1 gem install --verbose ruzzy
```

{{< hint info >}}
Ruzzy は libFuzzer をもとに作られているので、libFuzzer についての[この節]({{% ref "docs/fuzzing/c-cpp/10-libfuzzer/index.md" %}})もあわせて読むとよいでしょう。
{{< /hint >}}

## 使い方 {#usage}

### はじめに

Ruzzy には、動作を示すための[簡単な例](https://llvm.org/docs/LibFuzzer.html#toy-example)が付いています。

まず、次の環境変数を設定します。

```bash
export ASAN_OPTIONS="allocator_may_return_null=1:detect_leaks=0:use_sigaltstack=0"
```

これらのオプションの細かい意味をすべて理解する必要はありませんが、気になる方のために説明します。

1. メモリ割り当ての失敗はよくあり、影響も小さい(DoS)ので、今は無視します。
1. Python と同じく、Ruby のインタプリタは[データをリークします](https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#leak-detection)。そのため、これも今は無視します。
1. Ruby は [sigaltstack を無効にする](https://github.com/ruby/ruby/blob/master/doc/contributing/building_ruby.md#building-with-address-sanitizer)ことを勧めています。

そのうえで、次のコマンドで例を実行できます。

```bash
LD_PRELOAD=$(ruby -e 'require "ruzzy"; print Ruzzy::ASAN_PATH') \
    ruby -e 'require "ruzzy"; Ruzzy.dummy'
```

_`LD_PRELOAD` が必要な理由は、[Atheris](https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#option-a-sanitizerlibfuzzer-preloads) の場合と同じです。ただし `ASAN_OPTIONS` と違って、ほかのプログラムに影響するおそれがあるため、`export` しないほうがよいでしょう。_

すぐに、次のようなクラッシュが出るはずです。

```bash
INFO: Running with entropic power schedule (0xFF, 100).
INFO: Seed: 2527961537
...
==45==ERROR: AddressSanitizer: heap-use-after-free on address 0x50c0009bab80 at pc 0xffff99ea1b44 bp 0xffffce8a67d0 sp 0xffffce8a67c8
...
SUMMARY: AddressSanitizer: heap-use-after-free /var/lib/gems/3.1.0/gems/ruzzy-0.7.0/ext/dummy/dummy.c:18:24 in _c_dummy_test_one_input
...
==45==ABORTING
MS: 4 EraseBytes-CopyPart-CopyPart-ChangeBit-; base unit: 410e5346bca8ee150ffd507311dd85789f2e171e
0x48,0x49,
HI
artifact_prefix='./'; Test unit written to ./crash-253420c1158bc6382093d409ce2e9cff5806e980
Base64: SEk=
```

メモリ違反を起こす入力(`"HI"`)を正しく見つけたことが分かります。この違反が起きた理由は、[`dummy.c`](https://github.com/trailofbits/ruzzy/blob/main/ext/dummy/dummy.c) で確かめられます。

クラッシュしたケースは、次のコマンドで再実行できます。

```bash
LD_PRELOAD=$(ruby -e 'require "ruzzy"; print Ruzzy::ASAN_PATH') \
    ruby -e 'require "ruzzy"; Ruzzy.dummy' \
    ./crash-253420c1158bc6382093d409ce2e9cff5806e980
```

使えるサニタイザは次のとおりです。

- `Ruzzy::ASAN_PATH`: [AddressSanitizer](https://clang.llvm.org/docs/AddressSanitizer.html)
- `Ruzzy::UBSAN_PATH`: [UndefinedBehaviorSanitizer](https://clang.llvm.org/docs/UndefinedBehaviorSanitizer.html)

### 純粋な Ruby コードのファジング {#fuzzing-pure-ruby-code}

例として、小さな Ruby スクリプトをファジングしてみましょう。純粋な Ruby コードをファジングするには、トレーサのスクリプトとファジング用のハーネスという 2 つの Ruby スクリプトが必要です。トレーサのスクリプトが必要なのは、Ruby インタプリタの実装上の都合によるものです。必要だということ以外に、この仕組みの細部を理解する必要はありません。

まず、トレーサのスクリプトです。これを `test_tracer.rb` と呼ぶことにします。

```ruby
# frozen_string_literal: true

require 'ruzzy'

Ruzzy.trace('test_harness.rb')
```

次に、ファジング用のハーネスです。これを `test_harness.rb` と呼ぶことにします。

```ruby
# frozen_string_literal: true

require 'ruzzy'

def fuzzing_target(input)
  if input.length == 4
    if input[0] == 'F'
      if input[1] == 'U'
        if input[2] == 'Z'
          if input[3] == 'Z'
            raise
          end
        end
      end
    end
  end
end

test_one_input = lambda do |data|
  fuzzing_target(data) # Your fuzzing target would go here
  return 0
end

Ruzzy.fuzz(test_one_input)
```

次のコマンドで、このファイルを実行してファジングを始められます。

```bash
LD_PRELOAD=$(ruby -e 'require "ruzzy"; print Ruzzy::ASAN_PATH') \
    ruby test_tracer.rb
```

すぐに、次のようなクラッシュが出るはずです。

```bash
INFO: Running with entropic power schedule (0xFF, 100).
INFO: Seed: 2311041000
...
/app/ruzzy/bin/test_harness.rb:12:in `block in <top (required)>': unhandled exception
    from /var/lib/gems/3.1.0/gems/ruzzy-0.7.0/lib/ruzzy.rb:15:in `c_fuzz'
    from /var/lib/gems/3.1.0/gems/ruzzy-0.7.0/lib/ruzzy.rb:15:in `fuzz'
    from /app/ruzzy/bin/test_harness.rb:35:in `<top (required)>'
    from bin/test_tracer.rb:7:in `require_relative'
    from bin/test_tracer.rb:7:in `<main>'
...
SUMMARY: libFuzzer: fuzz target exited
MS: 1 CopyPart-; base unit: 24b4b428cf94c21616893d6f94b30398a49d27cc
0x46,0x55,0x5a,0x5a,
FUZZ
artifact_prefix='./'; Test unit written to ./crash-aea2e3923af219a8956f626558ef32f30a914ebc
Base64: RlVaWg==
```

例外を起こす入力(`"FUZZ"`)を正しく見つけたことが分かります。

自分のターゲットをファジングするには、`test_one_input` の `lambda` を、ターゲットの関数を呼ぶように書き換えてください。

### Ruby の C 拡張のファジング {#fuzzing-ruby-c-extensions}

例として、[`msgpack-ruby`](https://github.com/msgpack/msgpack-ruby) ライブラリをファジングしてみましょう。まず、gem をインストールします。

```bash
MAKE="make --environment-overrides V=1" \
CC="/path/to/clang" \
CXX="/path/to/clang++" \
LDSHARED="/path/to/clang -shared" \
LDSHAREDXX="/path/to/clang++ -shared" \
CFLAGS="-fsanitize=address,fuzzer-no-link -fno-omit-frame-pointer -fno-common -fPIC -g" \
CXXFLAGS="-fsanitize=address,fuzzer-no-link -fno-omit-frame-pointer -fno-common -fPIC -g" \
    gem install msgpack
```

Ruzzy のコンパイルで使った環境変数に加えて、`CFLAGS` と `CXXFLAGS` を指定しています。これらのフラグはファジングの助けになり、アドレスサニタイザや、より詳しいスタックトレース情報といった便利な機能を有効にします。詳しくは [AddressSanitizerFlags](https://github.com/google/sanitizers/wiki/AddressSanitizerFlags) を見てください。

次に、`msgpack` 用のファジングハーネスが必要です。次のコードは、[libFuzzer の経験](https://llvm.org/docs/LibFuzzer.html#fuzz-target)がある方にはなじみがあるかもしれません。

```ruby
# frozen_string_literal: true

require 'msgpack'
require 'ruzzy'

test_one_input = lambda do |data|
  begin
    MessagePack.unpack(data)
  rescue Exception
    # We're looking for memory corruption, not Ruby exceptions
  end
  return 0
end

Ruzzy.fuzz(test_one_input)
```

このファイルを `fuzz_msgpack.rb` と呼ぶことにします。次のコマンドで、このファイルを実行してファジングを始められます。

```bash
LD_PRELOAD=$(ruby -e 'require "ruzzy"; print Ruzzy::ASAN_PATH') \
    ruby fuzz_msgpack.rb
```

libFuzzer のオプションは、次のように Ruby スクリプトに渡せます。

```bash
LD_PRELOAD=$(ruby -e 'require "ruzzy"; print Ruzzy::ASAN_PATH') \
    ruby fuzz_msgpack.rb /path/to/corpus
```

詳しくは [libFuzzer のオプション](https://llvm.org/docs/LibFuzzer.html#options)を見てください。

自分のターゲットをファジングするには、`test_one_input` の `lambda` を、ターゲットの関数を呼ぶように書き換えてください。

## 追加のリソース

- [Introducing Ruzzy, a coverage-guided Ruby fuzzer](https://blog.trailofbits.com/2024/03/29/introducing-ruzzy-a-coverage-guided-ruby-fuzzer/)
- [Fuzzing pure Ruby code](https://github.com/trailofbits/ruzzy#fuzzing-pure-ruby-code)
- [Fuzzing Ruby C extensions](https://github.com/trailofbits/ruzzy#fuzzing-ruby-c-extensions)
