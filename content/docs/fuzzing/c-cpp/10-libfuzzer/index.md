---
title: "libFuzzer"
slug: libfuzzer
weight: 1
---


# libFuzzer {#libfuzzer}

C/C++ のプログラムをファジングしたいなら、libFuzzer が明快で簡単な選択です。LLVM プロジェクトの一部で、ほとんどのプラットフォームで使えるからです。できれば Linux でのファジングをお勧めします。libFuzzer への対応が最も充実しているプラットフォームだからです（たとえば macOS の XCode には、あらかじめ入っていません）。Microsoft の MSVC コンパイラも、最近 [libFuzzer に対応しました](https://learn.microsoft.com/en-us/cpp/build/reference/fsanitize?view=msvc-170)。

libFuzzer は 2022 年の終わりから[メンテナンスのみ](https://llvm.org/docs/LibFuzzer.html#id13)のモードになっていて、新機能は追加されません。ただし、ほかの選択肢よりインストールも使い方も簡単で、幅広く対応されており、当面は保守も続きます。そのため Trail of Bits は、最初のファジングの実験には libFuzzer を使うことをお勧めします。 

より高性能な AFL++ は、libFuzzer 用に書いたファジングのハーネスと互換性があります。つまり、libFuzzer から AFL++ への移行は簡単で、コンパイラを `clang++` から `afl-clang-fast++` に変えるだけで済みます。

{{< fuzzing/intro-os >}}
できれば、ローカルの x86_64 の VM でファジングするか、DigitalOcean、AWS、Hetzner などで VM を借りてファジングすることをお勧めします。


## インストール {#installation}

Ubuntu や Debian を使っているなら、libFuzzer を含む `clang` パッケージを apt でインストールできます。さらに、`llvm` パッケージのツールを使うと、ファジングのカバレッジを評価するのに便利です。


```shell
apt install clang llvm
```

ディストリビューションが提供する LLVM のバージョンが古い場合は、[apt.llvm.org](https://apt.llvm.org/) から好きなバージョンの LLVM をインストールできます。macOS では、Homebrew か Nix で Clang をインストールできます。Windows では、対応しているバージョンの Clang を [Visual Studio からインストール](https://learn.microsoft.com/en-us/cpp/build/clang-support-msbuild?view=msvc-170)できます。ただし、この章で説明するコマンドや手法のすべてが macOS や Windows で動くかどうかは、確かめていません。 

## ファジングのテストをコンパイルする {#compile-a-fuzz-test}

SUT をファジングするバイナリを作るのは簡単です。[はじめに]({{% relref "fuzzing#introduction-to-fuzzers" %}})の `harness.cc` と `main.cc` を再利用します。できあがるバイナリは、ハーネスと libFuzzer のランタイムを使います。Clang コンパイラを使う場合、次のコマンドで、カレントディレクトリに `fuzz` というバイナリができます。

{{< tooltipHighlight shell 
"Compiler for C++"
"Skips the main function"
"Adds debug symbols"
"Sets production optimization level"
"Enables libFuzzer"
>}}
clang++ -DNO_MAIN -g -O2 -fsanitize=fuzzer harness.cc main.cc -o fuzz
{{< / tooltipHighlight >}}



<!-- TODO Mabye add asan by defualt here?-->


SUT やハーネスを変更したときは、再コンパイルが必要です。

ここで重要なフラグは `-fsanitize=fuzzer` で、コンパイラに libFuzzer を使うよう指示します。`-fsanitize=fuzzer` を使うと、裏で多くのことが起こります。 

* libFuzzer のランタイムがリンクされ、ファザーを実行する `main` 関数が提供される。
* [SanitizerCoverage](https://clang.llvm.org/docs/SanitizerCoverage.html) の計装が使われ、コードカバレッジが収集される。
* `-fno-builtin-memcmp` などの Clang のフラグにより、[組み込み関数が無効になる](https://github.com/llvm/llvm-project/blob/202a4c0dfb19823a0c0fc737e32d205efaffb7ff/clang/lib/Driver/SanitizerArgs.cpp#L1363-L1373)。
* ターゲットのアーキテクチャによっては、libFuzzer を有効にすることで、ほかのオプションにも影響が出る可能性がある（手がかりは、LLVM のコードベースを[検索](https://github.com/search?q=repo%3Allvm%2Fllvm-project%20needsfuzzer&type=code)してください）。

フラグ `-DNO_MAIN` は、[はじめに]({{% relref "fuzzing#introduction-to-fuzzers" %}})で定義した、この章で使い続けている例のデフォルトの `main` 関数を無効にするマクロを定義します。libFuzzer が自前の `main` 関数を提供するためです。プロジェクトによっては、バイナリをファジングするときに、同様のマクロを追加する必要があります（ライブラリでは、通常は必要ありません）。

また、`-g` でデバッグシンボルを有効にし、最適化レベルを `-O2` にしています。本番で使われるレベルである可能性が高いので、ファジングにも妥当な最適化レベルです。

プロジェクトが GCC コンパイラに依存している場合は、代わりに AFL++ を [gcc_plugin](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.gcc_plugin.md) と組み合わせて使うことを検討してください。

## 使い方 {#usage}

`./fuzz <corpus_dir>` を実行すると、ファジングを始められます。コーパスのディレクトリは、空のディレクトリでかまいません。できれば、シードのテストケースを用意してください。たとえば PNG のライブラリをファジングするなら、PNG の画像のサンプルを用意するとよいでしょう（具体例は[実際の例](#real-world-examples)を参照）。 

デフォルトでは、libFuzzer はクラッシュを見つけたあとにファジングを続けません。この動作は、実験的なフラグ `-fork=1` と `-ignore_crashes=1` を付けると変えられます（関連するフラグ `-ignore_timeouts` と `-ignore_ooms` は、デフォルトで有効です）。これらのフラグは実験的ですが、広く使われています。そのため、長時間のファジングキャンペーンを始めるときは、次のコマンドを実行することをお勧めします。


```shell
./fuzz -fork=1 -ignore_crashes=1 <corpus_dir>
```

この例は比較的単純なので、空のコーパスのディレクトリで十分です。


```shell
mkdir corpus/
```


コーパスのディレクトリを省略することもできます。その場合、ディスクに保存されるのはクラッシュだけで、コーパス自体は保存されません。そのため、ファジングキャンペーンが終わると、コーパスは失われます。

ここから、ファザーを実行できます。


```shell
./fuzz corpus/
```


例が単純なので、すぐにクラッシュを確認できます。出力には、1 秒あたりの実行回数とコーパスのサイズに関する、現在の統計が含まれます。


{{< customFigure "libFuzzer を実行したときの出力。この出力の詳細は、[libFuzzer のドキュメント](https://llvm.org/docs/LibFuzzer.html#output)を参照してください。強調している部分は、クラッシュを引き起こしたテストケースのパスです。" >}}
```text {linenos=inline,hl_lines=19}
INFO: Running with entropic power schedule (0xFF, 100).
INFO: Seed: 3517090860
INFO: Loaded 1 modules   (9 inline 8-bit counters): 9 [0x55c248efafa0, 0x55c248efafa9),
INFO: Loaded 1 PC tables (9 PCs): 9 [0x55c248efafb0,0x55c248efb040),
INFO: -max_len is not provided; libFuzzer will not generate inputs larger than 4096 bytes
INFO: A corpus is not provided, starting from an empty corpus
#2      INITED cov: 3 ft: 4 corp: 1/1b exec/s: 0 rss: 26Mb
#57     NEW    cov: 4 ft: 5 corp: 2/4b lim: 4 exec/s: 0 rss: 26Mb L: 3/3 MS: 5 CrossOver-ShuffleBytes-InsertByte-CrossOver-InsertByte-
#73     REDUCE cov: 4 ft: 5 corp: 2/3b lim: 4 exec/s: 0 rss: 26Mb L: 2/2 MS: 1 EraseBytes-
#16921  NEW    cov: 7 ft: 8 corp: 5/9b lim: 163 exec/s: 0 rss: 26Mb L: 2/3 MS: 2 ChangeBinInt-EraseBytes-
==11672== ERROR: libFuzzer: deadly signal

  [ ... Stacktrace ...]

SUMMARY: libFuzzer: deadly signal
MS: 4 CrossOver-CrossOver-EraseBytes-ChangeBit-; base unit: 3f786850e387550fdab836ed7e6dc881de23001b
0x61,0x62,0x63,
abc
artifact_prefix='./'; Test unit written to ./crash-a9993e364706816aba3e25717850c26c9cd0d89d
Base64: YWJj
```
{{< /customFigure >}}

最初に、ファザーは、シードを含む設定の情報を出力します。libFuzzer のキャンペーンを再現したいときは、コマンドラインのフラグ `-seed=3517090860` を使います。ただし、再現できるのは、1 つのコアでファジングした場合だけです。[マルチコアでのファジング](#multi-core-fuzzing)では、コアの間で興味深いテストケースを共有する動作が非決定的になります。

 

ファザーの実行中は、`#` で始まる行が出力されます。出力されるデータのより詳しい説明は、[libFuzzer のドキュメント](https://llvm.org/docs/LibFuzzer.html#output)を参照してください。

libFuzzer の出力の最後には、クラッシュにつながった入力を含むファイルのパスが表示されます。入力は、16 進数（0x61,0x62,0x63）、UTF-8（abc）、Base64（YWJj）にエンコードした形でも表示されます。

ベースユニット（クラッシュする入力に至るために[変異]({{% relref "fuzzing#the-default-fuzzing-algorithm-is-mutation-based-and-evolutionary" %}})させた入力）のファイル名も表示されます。このファジングの例では、ベースユニット `3f7868…` には文字列 "ab" が入っていました。ファザーは文字列 "ab" を変異させて、クラッシュする入力 "abc" にたどり着きました。

libFuzzer は、バグを見つけたあとに自動では再開しないことに注意してください。つまり、見つけたバグはすべて直してから、libFuzzer を再実行する必要があります。

より長いファジングキャンペーンを実行する予定なら、バグを見つけたあとも自動で続ける AFL++ の利用を検討してください。


### テストケースを再実行する {#re-execute-a-test-case}

テストケースは `./fuzz <test_case>` で再実行できます。たとえば次のコマンドは、クラッシュを再実行します。


```shell
./fuzz ./crash-a9993e364706816aba3e25717850c26c9cd0d89d
```


これは、見つけたバグのトリアージに役立ちます。実際にはファジングせずに（`-runs=0`）、ディレクトリにあるテストケースを再実行したい場合は、次を実行します。

```shell
./fuzz -runs=0 <directory>
```

### ファザーのオプション {#fuzzer-options}

`./fuzz` を起動するときにコマンドラインのフラグを付けると、いくつかのオプションを設定できます。（`-help=1` を使うと、すべてのオプションが表示されます。）


* **-max_len=4000** テスト入力の最大の長さ。デフォルトでは、libFuzzer が推測します。最小の入力サイズの、少なくとも数倍に設定することをお勧めします。目安として、現実的な最小の入力を見つけて、それを 2 倍にすることを勧めます。入力サイズが大きいほど実行時間が長くなり、探索される入力空間が必ずしも広くなるわけではないことに注意してください。
* **-timeout=2** libFuzzer は、n 秒たつとテストケースの実行を中止します。この値は、ある程度低く設定するのが妥当です。SUT を不当に長い時間ハングさせる入力を見つけることも、目的の 1 つだからです。たとえば、妥当なサイズの PNG 画像の解析は数百ミリ秒を超えないはずなので、これを数秒に設定すれば、たいてい誤検知を避けるのに十分です。 
* **-dict=./dict.dict** ファザーを導く辞書ファイルを指定するオプション。これにより、ファザーは興味深いテストケースをより速く見つけられます。詳細は、[ファジングの辞書]({{% relref 02-dictionary %}})を参照してください。
* **-jobs=10** 10 回のファジングキャンペーンを順番に実行する。詳しくは、下の[マルチコアでのファジング](#multi-core-fuzzing)を参照。
* **-workers=2** `-jobs` フラグで定義したファジングキャンペーンを、2 つのワーカーで実行する。詳しくは、下の[マルチコアでのファジング](#multi-core-fuzzing)を参照。このフラグのデフォルトは、コア数を 2 で割った数。
* **-fork=1 -ignore_crashes=1** libFuzzer が、クラッシュを見つけたあともファジングを続けるようにする。`-fork` フラグは公式には実験的ですが、実際にはよく使われているので、使っても安全だと考えられる。
* **-close_fd_mask=3** 標準入力と標準出力を閉じる。SUT が大量の出力を書き出す場合に、ファジングが速くなる。

## マルチコアでのファジング {#multi-core-fuzzing}

libFuzzer では、マルチコアでのファジングを簡単にサポートしています。ジョブ数と並列度は、`-jobs=n` と `-workers=m` のフラグで制御できます。たとえばジョブ数を 10 にすると、ファザーは 10 回のファジングキャンペーンを順番に実行します。新しいキャンペーンは、クラッシュを見つけたあとに始まります。`workers` フラグを 2 にすると、ジョブは 2 つのプロセスで並列に処理されます。ファジング中に見つかったテストケースは、ファジングのジョブの間で共有されます。共有は `-reload=0` で無効にできます。

`-jobs` と `-workers` のフラグは、[使い方](#usage)のセクションで紹介した `-fork` フラグと組み合わせられます。たとえば、ワーカー数とジョブ数を `4` にして fork を有効にすると、libFuzzer は 2 つのプロセスで継続的にファジングします。


```shell
./fuzz -jobs=4 -workers=4 -fork=1 -ignore_crashes=1 <corpus_dir>
```


代わりに、libFuzzer の fork の機能を使うこともできます。


```shell
./fuzz -fork=4 -ignore_crashes=1 <corpus_dir>
```


fork の機能は公式には実験的なので、`-fork=4` ではなく `-jobs=4` と `-workers=4` のフラグを使うことをお勧めします。ただし、マルチコアでのファジングを重視するなら、AFL++、Hongfuzz、LibAFL など、より高機能なファザーに切り替えてください。

<!-- TODO

add note: There is no clear answer, but:
* There are user reports that the executions per second get lower over time when forking
* https://github.com/google/oss-fuzz/issues/2178
* Not used in oss-fuzz
* https://github.com/google/oss-fuzz/issues/8006
-->

## AddressSanitizer {#addresssanitizer}

ASan は、そのままでは気づかないかもしれないメモリエラーの検出に役立ちます。ASan の一般的な紹介は、[AddressSanitizer]({{% relref "/docs/fuzzing/techniques/03-asan" %}})を参照してください。

たとえば、次のヒープバッファオーバーフローは、ASan がないと通常は検出できません。割り当てたバッファの範囲外にアクセスしていますが、実際には、当たったメモリ（別の割り当てのメタデータの一部かもしれません）はプロセスにまだマップされているため、プログラムはセグメンテーション違反でクラッシュしないのです。

{{< customFigure "main_asan.cc: ASan で検出できるバグの例。プログラムは 1 バイトしか割り当てていないのに、少なくとも 2 バイトを書き込むので、9 行目で範囲外に書き込む。" >}}
```C++ {linenos=inline,hl_lines=9}
void check_buf(char *buf, size_t buf_len) {
    char *last;

    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                last = (char*)malloc(1 * sizeof(char)); // Allocate memory
                last[0] = 'c'; // Write the character 'c'
                last[1] = '\0'; // Write terminating null byte. A heap-buffer overflow is happening here!
                printf("%s", last); // Print the string
                free(last); // Free allocated memory
            }
        }
    }
}
```
{{< /customFigure >}}


libFuzzer で ASan を有効にするには、コンパイラにフラグ `-fsanitize=address` を渡します。ディストリビューションがデフォルトで [`_FORTIFY_SOURCE`](https://www.gnu.org/software/libc/manual/html_node/Source-Fortification.html) を有効にしている場合に備えて、これも無効にしてください（[先頭のアンダースコアが重要](https://blog.trailofbits.com/2023/04/20/typos-that-omit-security-features-and-how-to-test-for-them/)なことに注意）。有効のままだと、強化された関数が ASan に計装されないため、誤検知や見逃しの原因になることがあります。

たとえば、ASan で `main_asan.cc` のメモリ破壊のバグを見つけるには、コンパイル時に `-fsanitize=address` フラグを追加します。

```shell
clang++ -DNO_MAIN -g -O2 -fsanitize=fuzzer -fsanitize=address harness.cc main_asan.cc -U_FORTIFY_SOURCE -o fuzz
```


ファザーを実行すると、次のように ASan のクラッシュが起きます。


{{< customFigure "ASan の出力の例。クラッシュの原因を示す最初の行 `AddressSanitizer: heap-buffer-overflow` に注目してください。" >}}
```text
==1276163==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x6020000c4ab1 at pc 0x55555568631b bp 0x7fffffffda10 sp 0x7fffffffda08
WRITE of size 1 at 0x6020000c4ab1 thread T0
    #0 0x55555568631a in check_buf(char*, unsigned long) /root/handbook/libfuzzer/main_asan.cc:13:25
    #1 0x5555556860bf in LLVMFuzzerTestOneInput /root/handbook/libfuzzer/harness.cc:7:3

(...)

(BuildId: b171fea7226b2f316f8138a7947857763d78aa1d)

0x6020000c4ab1 is located 0 bytes after 1-byte region [0x6020000c4ab0,0x6020000c4ab1)
allocated by thread T0 here:
    #0 0x555555648142 in malloc (/root/handbook/libfuzzer/fuzz+0xf4142) (BuildId: b171fea7226b2f316f8138a7947857763d78aa1d)
    #1 0x55555568621f in check_buf(char*, unsigned long) /root/handbook/libfuzzer/main_asan.cc:11:31
    #2 0x5555556860bf in LLVMFuzzerTestOneInput /root/handbook/libfuzzer/harness.cc:7:3

(...)

SUMMARY: AddressSanitizer: heap-buffer-overflow /root/handbook/libfuzzer/main_asan.cc:13:25 in check_buf(char*, unsigned long)
Shadow bytes around the buggy address:
  0x6020000c4800: fa fa fd fa fa fa fd fa fa fa fd fa fa fa fd fa
  0x6020000c4880: fa fa fd fa fa fa fd fd fa fa fd fd fa fa fd fd
  0x6020000c4900: fa fa fd fd fa fa fd fa fa fa fd fa fa fa fd fa
  0x6020000c4980: fa fa fd fa fa fa fd fa fa fa fd fa fa fa fd fa
  0x6020000c4a00: fa fa fd fa fa fa fd fa fa fa fd fa fa fa fd fa
=>0x6020000c4a80: fa fa 03 fa fa fa[01]fa fa fa fa fa fa fa fa fa
  0x6020000c4b00: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x6020000c4b80: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x6020000c4c00: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x6020000c4c80: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
  0x6020000c4d00: fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa fa
Shadow byte legend (one shadow byte represents 8 application bytes):
  Addressable:           00
  Partially addressable: 01 02 03 04 05 06 07
  Heap left redzone:       fa
  Freed heap region:       fd
  Stack left redzone:      f1
  Stack mid redzone:       f2
  Stack right redzone:     f3
  Stack after return:      f5
  Stack use after scope:   f8
  Global redzone:          f9
  Global init order:       f6
  Poisoned by user:        f7
  Container overflow:      fc
  Array cookie:            ac
  Intra object redzone:    bb
  ASan internal:           fe
  Left alloca redzone:     ca
  Right alloca redzone:    cb
==1276163==ABORTING
```
{{< /customFigure >}}




## 実際の例 {#real-world-examples}


### libpng {#libpng}

libpng は、PNG（Portable Network Graphics）の画像ファイルの読み書きに使われる、オープンソースのライブラリです。このパーサーは、信頼できない入力を解析する状況でよく使われるので、ファジングする価値があります。そのため、パーサーのバグはどれもセキュリティ上の問題につながりえます。

静的ライブラリを作る C のプロジェクトをファジングするなら、次の手順に従えます。

1. プロジェクトのコードベースにある `INSTALL` ファイル（または適切なほかのドキュメント）を読み、静的ライブラリの作り方を調べる。
2. コンパイラを Clang に設定し、コンパイル時に追加のフラグをコンパイラに渡す。
3. 静的ライブラリをビルドする。このとき、C コンパイラにフラグ `-fsanitize=fuzzer-no-link` を渡す。これは、ファジングエンジンをリンクせずに、ファジング関連の計装を有効にする。`main` シンボルを含むランタイムは、あとで `-fsanitize=fuzzer` フラグを使うときにリンクされる。ビルドの手順で静的ライブラリができる。これを `$static_library` と呼ぶ。さらに、フラグ `-fsanitize=address` を渡して ASan を有効にし、メモリ破壊を検出する。
4. 手順 3 でコンパイルした静的ライブラリを見つけ、次を実行する: `clang++ -fsanitize=fuzzer -fsanitize=address $static_library harness.cc -o fuzz`。
5. `./fuzz` を実行すると、ファジングを始められる。

この手順を、有名な libpng ライブラリでたどってみましょう。まず、ソースコードを取得します。


```shell
curl -L -O https://downloads.sourceforge.net/project/libpng/libpng16/1.6.37/libpng-1.6.37.tar.xz
tar xf libpng-1.6.37.tar.xz
cd libpng-1.6.37/
```


libpng をコンパイルする前に、依存するものをインストールする必要があります。

```shell
apt install zlib1g-dev
```

次に、`-fsanitize=fuzzer-no-link` フラグを使って、libFuzzer をリンクせずに、libpng を静的ライブラリとして設定し、コンパイルします。静的ライブラリをビルドするので、まだバイナリはリンクしません。

```shell
export CC=clang CFLAGS="-fsanitize=fuzzer-no-link -fsanitize=address" # Set C compiler and the flag for fuzzing
export CXX=clang++ CXXFLAGS="$CFLAGS" # Set C++ compiler and use C flags
./configure --enable-shared=no # Configure to compile a static library
make # Run compilation
```

デフォルトでは、設定スクリプトは最適化レベルを `-O2` にします。これは、[ファジングのテストをコンパイルするセクション](#compile-a-fuzz-test)で推奨しているレベルです。

ファジングの環境によっては、コンパイルを成功させるために、足りない依存関係をインストールする必要があります。たとえば、素の Ubuntu では、上で説明したように、パッケージ `zlib1g-dev` のインストールが必要になることがあります。

次に、GitHub からハーネスをダウンロードします。通常は、ハーネスを自分で書く必要があります。ただし、この例では、libpng の作者による既存のものを使えば十分です。


```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/f8e5fa92b0e37ab597616f554bee254157998227/contrib/oss-fuzz/libpng_read_fuzzer.cc
```


ここから、ファザーがバグを見つける作業を楽にするために、コーパスを用意します。 
libFuzzer は空のコーパスから始められるので、これは省いてもよい手順です。 <!-- TODO Add a general section about "Corpus preparation" for V2 -->
ただし、ファザーがゼロから始めなくて済むように、実際の入力でコーパスを用意しておくと役立ちます。次のように、有効な PNG ファイルを 1 つ用意するだけでも、ファジングの効果は大きく上がります。


```shell
mkdir corpus/
curl -o corpus/input.png https://raw.githubusercontent.com/glennrp/libpng/acfd50ae0ba3198ad734e5d4dec2b05341e50924/contrib/pngsuite/iftp1n3p08.png
```


ファザーをよりうまく導くために、PNG 形式の[辞書]({{% relref 02-dictionary %}})もダウンロードします。辞書は、PNG が使うマジックバイトなど、ファイル形式についての最初の手がかりをファザーに与えます。


```
curl -O https://raw.githubusercontent.com/glennrp/libpng/2fff013a6935967960a5ae626fc21432807933dd/contrib/oss-fuzz/png.dict
```


最後に、計装した libpng、ハーネス、libFuzzer のランタイムをリンクします。


```shell
$CXX -fsanitize=fuzzer -fsanitize=address libpng_read_fuzzer.cc .libs/libpng16.a -lz -o fuzz
```


次を実行すると、ファジングキャンペーンを開始できます。


```shell
./fuzz -close_fd_mask=3 -dict=./png.dict corpus/
```


### CMake ベースのプロジェクト {#cmake-based-project}

[はじめに]({{% relref "fuzzing#introduction-to-fuzzers" %}})で取り上げたプログラムを、CMake でビルドしているとします。`main.cc` と `harness.cc` をビルドし、そのターゲットを libFuzzer とリンクする CMake のターゲットを追加します。`NO_MAIN` フラグで main 関数を除外していることに注意してください。そうしないと、libFuzzer も main 関数を提供するので、プログラムに main 関数が 2 つできてしまいます。

{{< customFigure "CMakeLists: プログラムと、そのファザーをコンパイルするための CMake ファイルの例" >}}
```cmake
project(BuggyProgram)
cmake_minimum_required(VERSION 3.0)

add_executable(buggy_program main.cc)

add_executable(fuzz main.cc harness.cc)
target_compile_definitions(fuzz PRIVATE NO_MAIN=1)
target_compile_options(fuzz PRIVATE -g -O2 -fsanitize=fuzzer)
target_link_libraries(fuzz -fsanitize=fuzzer)
```

{{< /customFigure >}}


プロジェクトは、次のコマンドでビルドできます。


```shell
cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ .
cmake --build .
```

`./fuzz` を実行すると、ファジングキャンペーンを開始できます。


## 追加の資料 {#additional-resources}

* [Clang の libFuzzer のドキュメント](https://llvm.org/docs/LibFuzzer.html)
* [Google による libFuzzer のチュートリアル](https://github.com/google/fuzzing/blob/master/tutorial/libFuzzerTutorial.md)
