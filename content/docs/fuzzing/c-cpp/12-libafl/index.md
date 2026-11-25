---
title: "LibAFL"
slug: libafl
weight: 3
---


# LibAFL {#libafl}

[LibAFL](https://github.com/AFLplusplus/LibAFL/) ファザーは、AFL++ のような [AFL](https://github.com/google/AFL)\ 系のファザーの機能を実装しています。AFL++ と同様に、LibAFL は libFuzzer よりも優れたファジング性能と高度な機能を提供します。ただし、LibAFL では、すべての機能がモジュール式でカスタマイズ可能な形で提供されます。実際、LibAFL は、独自のファザーを実装するために使えるライブラリです。LibAFL はライブラリなので、libFuzzer (`apt install clang`) や AFL++ (`apt install afl++`) のように、1 行のコマンドでインストールすることはできません。ただし、LibAFL は libFuzzer の代替としてそのまま使えます。もう 1 つの使い方は、Rust のプロジェクトを作り、ライブラリを使ってファザーを作ることです。この LibAFL のセクションでは、**1\) libFuzzer の代替としての利用**と **2\) Rust ライブラリとしての LibAFL** の両方を扱います。

{{< fuzzing/intro-os >}}

## セットアップ {#setup}

まず、LibAFL の 2 つの主要な依存関係である Clang/LLVM と Rust をインストールします。システムの Clang のバージョンが 14 より大きければ、ディストリビューションから直接インストールしてかまいません。

```shell
apt install clang
```

特定のバージョンの Clang を使いたい場合は、[apt.llvm.org](https://apt.llvm.org/) から Clang をインストールします。

```shell
wget https://apt.llvm.org/llvm.sh
chmod +x llvm.sh
sudo ./llvm.sh 15
```

次に、このバージョンの Clang を使うよう Rust に伝える必要があります。Rust は、リンカ `cc` がパス上にあることに依存しています。変数 `RUSTFLAGS` を設定して、リンカのバイナリのバージョンを変更できます。

```shell
export RUSTFLAGS="-C linker=/usr/bin/clang-15"
```

また、[cc クレート](https://docs.rs/cc/latest/cc/)は `cc` プログラムに依存しています。変数 `CC` と `CXX` を設定して、そのクレートが使うコンパイラを変更できます。

```shell
export CC="clang-15"
export CXX="clang++-15"
```

LibAFL の Rust プロジェクトをコンパイルしたあとは、これらの環境変数を[解除](https://man7.org/linux/man-pages/man1/unset.1p.html)したほうがよいかもしれません。テスト対象 (SUT) のコンパイルを妨げる可能性があるためです。

LLVM のバージョン要件は、[予告なく変わることがあります](https://github.com/AFLplusplus/LibAFL/pull/2046/files)。執筆時点では、LLVM 15 から 18 を使うべきです。迷ったときや問題が起きたときは、[README](https://github.com/AFLplusplus/LibAFL/blob/main/README.md) を参照してください。

次に、[rustup](https://rustup.rs/) で Rust をインストールします。

```shell
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

追加のシステム依存パッケージのインストールが必要な場合があります。

```shell
apt install libssl-dev pkg-config
```

## libFuzzer の代替としての LibAFL {#libafl-as-libfuzzer-drop-in-replacement}

libFuzzer 互換レイヤーは、Rust の nightly 版に依存します。LLVM ツールを含む最新の nightly 版をインストールします。

```shell
rustup toolchain install nightly --component llvm-tools
```

次に、LibAFL のソースコードをクローンして、libFuzzer の代替をビルドします。ここでは、特定のバージョンではなく main ブランチを使っている点に注意してください。LibAFL にはリリースがありますが、このファザーはまだ活発に開発中のため、一般には main ブランチを使うことをおすすめします。

```shell
git clone https://github.com/AFLplusplus/LibAFL
cd LibAFL/libafl_libfuzzer_runtime
./build.sh
```

これで、カレントワーキングディレクトリに、`libFuzzer.a` という静的バイナリができました。

### ファズテストをコンパイルする {#compile-a-fuzz-test-libfuzzer}

[libFuzzer のセクション]({{% relref "10-libfuzzer" %}})と同様に、[イントロダクション]({{% relref "fuzzing#introduction-to-fuzzers" %}})の `harness.cc` と `main.cc` をコンパイルします。フラグ `-fsanitize=fuzzer` で既定の libFuzzer を使う代わりに、独自の libFuzzer ランタイムを渡します。`harness.cc` と `main.cc` が作業ディレクトリにあることを確認してください。

```shell
clang++ -DNO_MAIN -g -O2 -fsanitize=fuzzer-no-link libFuzzer.a harness.cc main.cc -o fuzz
```

SUT かハーネスを変更した場合は、再コンパイルが必要な点に注意してください。

フラグ `-fsanitize=fuzzer-no-link` は、いくつかのコンパイラオプションを有効にしますが、`-fsanitize=fuzzer` を使った場合とは異なり、ファザーのランタイムをリンクしません。`-DNO_MAIN`、`-g`、`-O2` の詳細は、[libFuzzer のセクション]({{% relref "10-libfuzzer#compile-a-fuzz-test" %}})を参照してください。

### 使い方 {#usage}

`./fuzz <corpus_dir>` を実行するとファジングが始まります。コーパスのディレクトリは空でもかまいません。理想的には、PNG パーサをファジングするなら小さな PNG 画像のような、シードのテストケースを用意します。

従来の libFuzzer と同様に、この代替も、最初のクラッシュを見つけるとファジングを止めます。これは、フラグ `-fork=1` と `-ignore_crashes=1` を使うと変更できます。これらは、既定の libFuzzer の実装と違い、LibAFL では実験的ではありません。フラグ `-fork=1` を指定すると、LibAFL は [`SimpleRestartingEventManager`](https://docs.rs/libafl/0.12.0/libafl/events/simple/struct.SimpleRestartingEventManager.html) を使って、プロセスを fork し、子プロセスを再起動します。LibAFL では、フラグ `-fork` と `-jobs` が同義である点に注意してください。これらのフラグに 1 より大きい値を指定すると、マルチプロセスに対応した、より高機能な [`LlmpRestartingEventManager`](https://docs.rs/libafl/0.12.0/libafl/events/llmp/struct.LlmpRestartingEventManager.html) が使われます。長時間のファジングキャンペーンには、次のコマンドをおすすめします。

```shell
./fuzz -fork=1 -ignore_crashes=1 <corpus_dir>
```

この例は比較的単純なので、空のコーパスのディレクトリで十分です。

```shell
mkdir corpus/
```

コーパスのディレクトリを省略することもできます。その場合、ディスクに保存されるのはクラッシュだけで、コーパス自体は保存されません。そのため、ファジングキャンペーンが終わるとコーパスは失われます。

これで、ファザーを実行できます。

```shell
./fuzz corpus/
```

例が単純なので、すぐにクラッシュが見つかります。出力には、現在の 1 秒あたりの実行回数とコーパスのサイズの統計が含まれます。

{{< customFigure "libFuzzer の実行結果。" >}}
```text
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 33.333%
                  (CLIENT) corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 3/9 (33%)
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 33.333%, size_edges: 33.333%
                  (CLIENT) corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 3/9 (33%), size_edges: 3/9 (33%)
[Testcase    #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 33.333%, size_edges: 33.333%
                  (CLIENT) corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 3/9 (33%), size_edges: 3/9 (33%)
We imported 1 inputs from disk.
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, stability: 100.000%, edges: 33.333%, size_edges: 33.333%
                  (CLIENT) corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, stability: 9/9 (100%), edges: 3/9 (33%), size_edges: 3/9 (33%)
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 44.444%, size_edges: 33.333%, stability: 100.000%
                  (CLIENT) corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 4/9 (44%), size_edges: 3/9 (33%), stability: 9/9 (100%)
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 44.444%, size_edges: 44.444%, stability: 100.000%
                  (CLIENT) corpus: 1, objectives: 0, executions: 1, exec/sec: 0.000, edges: 4/9 (44%), size_edges: 4/9 (44%), stability: 9/9 (100%)
[Testcase    #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 44.444%, size_edges: 44.444%, stability: 100.000%
                  (CLIENT) corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 4/9 (44%), size_edges: 4/9 (44%), stability: 9/9 (100%)
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 55.556%, size_edges: 44.444%, stability: 100.000%
                  (CLIENT) corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 5/9 (55%), size_edges: 4/9 (44%), stability: 9/9 (100%)
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 55.556%, size_edges: 55.556%, stability: 100.000%
                  (CLIENT) corpus: 2, objectives: 0, executions: 30, exec/sec: 0.000, edges: 5/9 (55%), size_edges: 5/9 (55%), stability: 9/9 (100%)
[Testcase    #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 3, objectives: 0, executions: 354, exec/sec: 0.000, edges: 55.556%, size_edges: 55.556%, stability: 100.000%
                  (CLIENT) corpus: 3, objectives: 0, executions: 354, exec/sec: 0.000, edges: 5/9 (55%), size_edges: 5/9 (55%), stability: 9/9 (100%)
[2024-06-06T14:39:11Z ERROR libafl::executors::hooks::unix::unix_signal_handler] Crashed with SIGABRT
[2024-06-06T14:39:11Z ERROR libafl::executors::hooks::unix::unix_signal_handler] Child crashed!
[2024-06-06T14:39:11Z ERROR libafl::executors::hooks::unix::unix_signal_handler] input: "8ac0f08adee16e49"
    ━━━━━━━━━━━━ CRASH ━━━━━━━━━━━━━━━━
    Received signal SIGABRT at 0x00761319e969fc, fault address: 0x00000000000000
    ━━━━━━━━━━━━ REGISTERS ━━━━━━━━━━━━
    r8 : 0x007ffff7d61830, r9 : 0x00000000000000, r10: 0x00000000000008, r11: 0x00000000000246,
    r12: 0x00000000000006, r13: 0x00000000000016, r14: 0x00761316080cc2, r15: 0x00000000000025,
    rdi: 0x00000000005f2c, rsi: 0x00000000005f2c, rbp: 0x00000000005f2c, rbx: 0x0076131a441940,
    rdx: 0x00000000000006, rax: 0x00000000000000, rcx: 0x00761319e969fc, rsp: 0x007ffff7d61760,
    rip: 0x00761319e969fc, efl: 0x00000000000246,
    ━━━━━━━━━━━━ BACKTRACE ━━━━━━━━━━━
       0: libafl_bolts::minibsod::generate_minibsod
                 at libafl_bolts/src/minibsod.rs:1080:30
       1: libafl::executors::hooks::unix::unix_signal_handler::inproc_crash_handler
                 at libafl/src/executors/hooks/unix.rs:208:32
       2: libafl::executors::hooks::unix::unix_signal_handler::<impl libafl_bolts::os::unix_signals::Handler for libafl::executors::hooks::inprocess::InProcessExecutorHandlerData>::handle
       3: libafl_bolts::os::unix_signals::handle_signal
                 at libafl_bolts/src/os/unix_signals.rs:436:5
       4: <unknown>
       5: pthread_kill
       6: gsignal
       7: abort
       8: _Z9check_bufPcm
                 at libafl_libfuzzer/libafl_libfuzzer_runtime/main.cc:8:17
       9: LLVMFuzzerTestOneInput
                 at libafl_libfuzzer/libafl_libfuzzer_runtime/harness.cc:7:3
      10: libafl_libfuzzer_test_one_input
                 at

...

libafl_libfuzzer/libafl_libfuzzer_runtime/src/lib.rs:500:9
      17: LLVMFuzzerRunDriver
                 at libafl_libfuzzer/libafl_libfuzzer_runtime/src/lib.rs:641:32
      18: main
                 at libafl_targets/src/libfuzzer.c:37:10
      19: <unknown>
      20: __libc_start_main
      21: _start

    ━━━━━━━━━━━━ MAPS ━━━━━━━━━━━━
    7fff7000-8fff7000 rw-p 00000000 00:00 0
    8fff7000-2008fff7000 ---p 00000000 00:00 0
    2008fff7000-10007fff8000 rw-p 00000000 00:00 0
    5596786b1000-559678764000 r--p 00000000 08:01 524035                     libafl_libfuzzer/libafl_libfuzzer_runtime/fuzz
    559678764000-559678d69000 r-xp 000b3000 08:01 524035

...

    76131a4a8000-76131a4aa000 rw-p 00039000 08:01 16134                      /usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2
    7ffff7d46000-7ffff7d67000 rw-p 00000000 00:00 0                          [stack]
    7ffff7dea000-7ffff7dee000 r--p 00000000 00:00 0                          [vvar]
    7ffff7dee000-7ffff7df0000 r-xp 00000000 00:00 0                          [vdso]
    ffffffffff600000-ffffffffff601000 --xp 00000000 00:00 0                  [vsyscall]

[Objective   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 3, objectives: 1, executions: 548, exec/sec: 0.000, edges: 55.556%, size_edges: 55.556%, stability: 100.000%
                  (CLIENT) corpus: 3, objectives: 1, executions: 548, exec/sec: 0.000, edges: 5/9 (55%), size_edges: 5/9 (55%), stability: 9/9 (100%)
```
{{< /customFigure >}}

`[UserStats #0]` や `[Testcase #0]` で始まる行は、記録されたイベントです。`UserStats` イベント (`Client Heartbeat` イベントとも呼ばれます) は、現在のファジングキャンペーンの状況を伝えるために定期的に発行されます。`Testcase` イベントは、新しいテストケースが見つかるたびに発行されます。新しいテストケースもクラッシュも見つからなければ、しばらく新しいログが出ないのは普通のことです。

イベントに加えて、追加の情報も表示されます。たとえば、ファザーがすでに動いている時間 (`run time`)、ファジングしている並列プロセスの数 (`clients`)、コーパスのエントリ数 (`corpus`)、見つかったクラッシュまたはメモリ不足のバグの数 (`objectives`)、SUT が呼び出された回数 (`executions`)、現在の 1 秒あたりの実行回数 (`exec/sec`) です。複数のコアでファジングしている場合 (`-fork` または `-jobs` フラグを使用) は、個々のファジングプロセスごとの統計と、全体を集計した統計が表示されます。

{{< customFigure "libFuzzer モードが表示する統計の例" >}}
```text
[UserStats   #0]  (GLOBAL) run time: 0h-0m-0s, clients: 1, corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 100.000%, size_edges: 100.000%
                  (CLIENT) corpus: 0, objectives: 0, executions: 0, exec/sec: 0.000, edges: 2/2 (100%), size_edges: 2/2 (100%)
```
{{< /customFigure >}}

フラグ `-tui=1` は、テキストベースのグラフィカルな統計表示を有効にします。また、メインのプロセスではなく、fork した子プロセスでファジングすることも暗黙のうちに有効にします。fork のロジックは、LibAFL の [fuzz](https://github.com/AFLplusplus/LibAFL/blob/c7207dceb05695f9beca297b220198c9dd78cccc/libafl_libfuzzer/runtime/src/fuzz.rs#L193-L228) 関数に実装されています。

{{< resourceFigure "libafl.png" >}}
LibAFL の TUI
{{< /resourceFigure >}}


## Rust ライブラリとしての LibAFL

LibAFL をより柔軟に使う方法は、ライブラリとして使うことです。LibAFL という名前が示すとおり、このプロジェクトは主にファザーです。前のセクションで説明した libFuzzer 互換レイヤーを使う方法は、コアのライブラリには含まれず、ほとんどは、とても手軽に始めるための方法です。LibAFL を最大限に活用したいなら、ライブラリを使って独自のファザーを実装することを検討してください。

### LibAFL ベースのファザーを作る

このセクションでは、ハーネス `harness.cc`、ターゲット `main.cc`、そして独自に設定した LibAFL のファザーランタイムをコンパイルします。そのために、LibAFL を使う新しい Rust プロジェクトを立ち上げます。そして、できあがったバイナリを、ハーネスとターゲットのプログラムにリンクします。

appsec\_guide という名前の新しい Rust プロジェクトを作り、LibAFL の依存関係を追加します。

```shell
cargo init --lib appsec_guide
cd appsec_guide
cargo add libafl@0.13 libafl_targets@0.13 libafl_bolts@0.13 libafl_cc@0.13 --features "libafl_targets@0.13/libfuzzer,libafl_targets@0.13/sancov_pcguard_hitcounts"
```

機能の選択は、LibAFL のファザーを正しく作るうえで欠かせない部分です。

* `libafl_targets/libfuzzer`: libFuzzer の挙動を軽量に模倣する補助関数をいくつか追加します。たとえば、`libafl_targets::libfuzzer_test_one_input` を呼び出して `LLVMFuzzerTestOneInput` を呼び出すラッパー関数を提供します。また、のちほど定義する `libafl_main` 関数を呼び出す[main 関数を定義](https://github.com/AFLplusplus/LibAFL/blob/571c4c111e99924cf4ed5580622a018b3dbb21c9/libafl_targets/src/libfuzzer.c#L35-L46)します。
* `libafl_targets/sancov_pcguard_hitcounts`: カバレッジの統計を保持するグローバルなマップを追加します。また、[LLVM のカバレッジ計装](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html)がカバレッジマップを埋めるのに使える関数を定義します。

{{< hint info >}}
プロのヒント: 先ほど、LibAFL はまだ開発途上だと述べました。代わりに LibAFL の特定のコミットを使いたい場合は、次のコマンドを使います。
```shell
cargo add --git https://github.com/AFLplusplus/LibAFL --rev 2356ba575 libafl libafl_targets libafl_bolts libafl_cc --features "libafl_targets/libfuzzer,libafl_targets/sancov_pcguard_hitcounts"
```
上のコマンドでエラーになる[バグ](https://github.com/rust-lang/cargo/issues/13121)が見つかっているため、Rust を最新版に更新する必要があるかもしれません。
{{< /hint >}}

この例のファザーはコマンドラインオプションを使います。そのため、clap の依存関係を追加する必要があります。

```shell
cargo add clap@4 --features "derive"
```

ライブラリのクレートは、静的ライブラリとしてコンパイルする必要があります。そのためには、`Cargo.toml` ファイルで `crate-type` を `staticlib` に設定します。

{{< customFigure "ファザーの最終的な `Cargo.toml` ファイル" >}}
```toml
[package]
name = "appsec_guide"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["staticlib"]

[dependencies]
clap = { version = "4", features = ["derive"] }
libafl = "0.13.1"
libafl_bolts = "0.13.1"
libafl_cc = "0.13.1"
libafl_targets = { version = "0.13.1", features = ["libfuzzer", "sancov_pcguard_hitcounts"] }
```
{{< /customFigure >}}

基本的なプロジェクトを用意したら、`src/lib.rs` ファイルを空にします。以下のファザーの[完全なソースコード](https://github.com/trailofbits/testing-handbook/tree/main/materials/fuzzing/libafl/appsec_guide)は GitHub にあります。

次の図は、LibAFL のファザーの基本的な骨組みを示します。骨組みには、インポート、解析したコマンドラインオプションを含む構造体、`libafl_main` 関数が含まれます。`libafl_main` 関数の中で、コマンドラインオプションを解析し、クロージャ `run_client` を定義し、最後に LibAFL の [Launcher](https://docs.rs/libafl/0.13.1/libafl/events/launcher/index.html) ですべてを設定します。ランチャーのインスタンスを設定するために、いくつかのオプションを定義します。

* `.shmem_provider()` は、共有メモリのプロバイダを設定します。共有メモリは、ファジングのクライアントを同期するために使われます。実装は OS に応じて選ばれます。
* `.configuration()` は、ファザーに名前を付けます。ここでは「default」です。
* `.monitor()` は、集計した統計を `./fuzzer_stats.toml` という TOML ファイルに記録し、現在の統計を標準出力に記録するモニターを設定します。
* `.run_client()` は、ファザーとクライアントを作るラムダを定義します。
* `.cores()` は、どのコアを何個使うかを定義します。一般には、`Cores::from_cmdline` 関数で、文字列から `Cores` のインスタンスを作ります。たとえば、文字列「0」は、ID `0` のコアで動く、単一のクライアントのファザーを作ります。文字列「0,8-15」は、コア `0` と、ID 8 から 15 まで (両端を含む) のコアで動く、9 個のクライアントを起動します。
* `.broker_port()` は、メインのブローカープロセスが使うポートを設定します。クライアントとメインのブローカープロセスの最初の通信は、TCP で行われます。
* `.remote_broker_addr()` は、すでにブローカープロセスがある場合に、接続先のブローカープロセスを設定するのに使えます。そうでなければ、`None` に設定できます。
* `.stdout_file()` は、SUT の標準出力をリダイレクトします。出力が重要でなく、うるさい場合は、`/dev/null` に設定したくなるかもしれません。ここでこのオプションをコメントアウトしているのは、`run_client` クロージャの中で表示される出力も隠れてしまい、ファザーの問題を見えなくするおそれがあるためです。

{{< customFigure "LibAFL のファザーの骨組み。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)は、Testing Handbook の GitHub リポジトリにあります。" >}}
```rust
use libafl::{
    ...
};
use libafl_bolts::{
    ...
};
use libafl_targets::{libfuzzer_initialize, libfuzzer_test_one_input, std_edges_map_observer};
...

/// The commandline args this fuzzer accepts
#[derive(Debug, Parser)]
#[command(
    name = "appsec_guide",
    about = "A libfuzzer-like fuzzer with llmp-multithreading support and a launcher"
)]
struct Opt {
    ...
}

/// The main fn, `no_mangle` as it is a C symbol
#[no_mangle]
pub extern "C" fn libafl_main() {
    let opt = Opt::parse();

    println!(
        "Workdir: {:?}",
        env::current_dir().unwrap().to_string_lossy().to_string()
    );

    let mut run_client = |state: Option<_>, mut restarting_mgr, _core_id| {

       ...

       Ok(())
    };

    let shmem_provider = StdShMemProvider::new().expect("Failed to init shared memory");

    let monitor = OnDiskTOMLMonitor::new(
        "./fuzzer_stats.toml",
        MultiMonitor::new(|s| println!("{s}")),
    );

    let broker_port = opt.broker_port;
    let cores = opt.cores;

    match Launcher::builder()
        .shmem_provider(shmem_provider)
        .configuration(EventConfig::from_name("default"))
        .monitor(monitor)
        .run_client(&mut run_client)
        .cores(&cores)
        .broker_port(broker_port)
        .remote_broker_addr(opt.remote_broker_addr)
//     .stdout_file(Some("/dev/null"))
        .build()
        .launch()
    {
        Ok(()) => (),
        Err(Error::ShuttingDown) => println!("Fuzzing stopped by user. Good bye."),
        Err(err) => panic!("Failed to run launcher: {err:?}"),
    }
}
```
{{< /customFigure >}}

骨組みのコードは、まだどのターゲットもファジングしません。実際のファザーの設定は、`run_client` クロージャの中で行います。LibAFL はマルチプロセスにネイティブで対応しているため、クロージャを複数回実行することで、複数のクライアントを扱えます。

次の図は、`run_client` クロージャの中でファザーのクライアントを設定する手順を、順を追って示します。

{{< customFigure "ファザーのフィードバックの設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// Create an observation channel using the coverage map
let edges_observer =
    HitcountsMapObserver::new(unsafe { std_edges_map_observer("edges") }).track_indices();

// Create an observation channel to keep track of the execution time
let time_observer = TimeObserver::new("time");

// Feedback to rate the interestingness of an input
// This one is composed of two feedbacks in OR
let mut feedback = feedback_or!(
    // New maximization map feedback linked to the edges observer
    MaxMapFeedback::new(&edges_observer),
    // Time feedback
    TimeFeedback::new(&time_observer)
);
```
{{< /customFigure >}}

作成するファザーは、カバレッジと時間で導かれます。カバレッジは、グローバルなマップから集められます。ハーネスを実行するたびに、LibAFL はマップのデータを使って、カバレッジが増えたかどうかと、新しいエッジがいくつ見つかったかを判断します。上のコードは、まず 2 つのオブザーバを定義し、それらをフィードバックとして使います。フィードバックは、基本的に、テストケースの実行が興味深いものだったかどうかを定義します。マクロ `feedback_or!` は、どちらか一方のフィードバックがあれば、そのテストケースを興味深いと判断することを指定します。

オブザーバは、スケジューラとエグゼキュータを設定するときに、再び重要になります。ここで、`edges_observer` がインデックスを追跡できる点に注意してください (`track_indices` 関数の呼び出しを参照)。

{{< customFigure "ファザーの目的の設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// A feedback to choose if an input is a solution or not
let mut objective = feedback_or_fast!(CrashFeedback::new(), TimeoutFeedback::new());
```
{{< /customFigure >}}

ファザーには、導くためのフィードバックだけでなく、ゴールを定めるためのフィードバックも必要です。これはフィードバックと同様に定義します。ここでは、ファザーのゴールは、クラッシュする入力とタイムアウトする入力を見つけることです。どちらの種類のフィードバックも、LibAFL のコアのエンジンがネイティブで対応しているため、オブザーバを必要としない点に注意してください。`feedback_or!` ではなく `feedback_or_fast!` マクロを使うことで、クラッシュが起きたときは、タイムアウトのフィードバックは評価されません。

{{< customFigure "ファザーの状態の設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// If not restarting, create a State from scratch
let mut state = state.unwrap_or_else(|| {
    StdState::new(
        // RNG
        StdRand::new(),
        // Corpus that will be evolved, we keep it in memory for performance
        InMemoryCorpus::new(),
        // Corpus in which we store solutions (crashes in this example),
        // on disk so the user can get them after stopping the fuzzer
        OnDiskCorpus::new(&opt.output).unwrap(),
        // States of the feedbacks.
        // The feedbacks can report the data that should persist in the State.
        &mut feedback,
        // Same for objective feedbacks
        &mut objective,
    )
    .unwrap()
});

println!("We're a client, let's fuzz :)");
```
{{< /customFigure >}}

次に、新しいファザーの状態を作ります。クラッシュしたあとでこのクライアントを再起動する場合は、既存の状態を再利用します。新しい状態を作るときは、乱数生成器 (RNG)、コーパス、フィードバックの定義を指定できます。RNG には、ほとんどの用途で `StdRand` で十分です。RNG は、テストケースを変異させたり、新しいテストケースを生成したりするのに使われます。

ファザーは 2 つのコーパスを使います。1 つは興味深いテストケースを格納するもの、もう 1 つは目的を満たすテストケース (タイムアウトまたはクラッシュするテストケース) を格納するものです。この例では、テストケースに `InMemoryCorpus` を使うため、カバレッジを増やす、見つかったテストケースは、再起動すると失われます。`InMemoryCorpus` を [`InMemoryOnDiskCorpus`](https://docs.rs/libafl/0.13.1/libafl/corpus/inmemory_ondisk/struct.InMemoryOnDiskCorpus.html) に置き換えると、テストケースを主にメモリに置きつつ、ディスクにもバックアップを保存できます。


{{< customFigure "変異と変異ステージの設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// Setup a basic mutator with a mutational stage
let mutator = StdScheduledMutator::new(havoc_mutations());
let mut stages = tuple_list!(StdMutationalStage::new(mutator));
```
{{< /customFigure >}}

ここから、ファザーが使う変異を定義します。AFL++ などのファザーでおなじみの havoc 変異を使います。LibAFL には、テストケースごとに実行されるステージという概念があります。


{{< customFigure "スケジューリングアルゴリズムの設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// A minimization+queue policy to get test cases from the corpus
let scheduler =
    IndexesLenTimeMinimizerScheduler::new(&edges_observer, QueueScheduler::new());
```
{{< /customFigure >}}

どのテストケースを変異させて実行するかをスケジューリングすることは、ファジングの重要な部分です。最も単純な戦略は、ランダムにテストケースを選ぶことで、これは [`RandScheduler`](https://docs.rs/libafl/0.13.1/libafl/schedulers/struct.RandScheduler.html) に実装されています。上のコードは、有望なテストケースをキューのように選ぶスケジュールを定義します。そのために、ファザーは、どのテストケースが短く、実行時間が短いかを記述する状態を保持します。内部的には、LibAFL は、ファザーの状態 ([`TopRatedsMetadata`](https://docs.rs/libafl/latest/libafl/schedulers/minimizer/struct.TopRatedsMetadata.html)) とテストケース ([`IsFavoredMetadata`](https://docs.rs/libafl/0.13.1/libafl/schedulers/minimizer/struct.IsFavoredMetadata.html) と [`MapIndexesMetadata`](https://docs.rs/libafl/latest/libafl/feedbacks/map/struct.MapIndexesMetadata.html)) にメタデータを付けます。ここで注意すべき重要な点は、この特定のスケジューラは、インデックスを追跡できるオブザーバがあることに依存している点です。`edges_observer` は、設定時に `track_indices` 関数を使ったため、これを満たしています。
詳しくは、[ソースコード](https://github.com/AFLplusplus/LibAFL/blob/571c4c111e99924cf4ed5580622a018b3dbb21c9/libafl/src/schedulers/minimizer.rs)を参照してください。


{{< customFigure "スケジューラ、フィードバック、目的に基づくファザーの設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// A fuzzer with a corpus scheduler, feedback, and objective
let mut fuzzer = StdFuzzer::new(scheduler, feedback, objective);
```
{{< /customFigure >}}

これで、ファザーを設定し、スケジューラをフィードバックと目的に結び付ける準備ができました。


{{< customFigure "ハーネスとエグゼキュータの設定。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// The wrapped harness function, calling out to the LLVM-style harness
let mut harness = |input: &BytesInput| {
    let target = input.target_bytes();
    let buf = target.as_slice();
    libfuzzer_test_one_input(buf);
    ExitKind::Ok
};

let mut executor = InProcessExecutor::with_timeout(
    &mut harness,
    tuple_list!(edges_observer, time_observer),
    &mut fuzzer,
    &mut state,
    &mut restarting_mgr,
    opt.timeout,
)?;
```
{{< /customFigure >}}

単純ですが重要な手順は、ハーネスの定義です。上のハーネスは、`LLVMFuzzerTestOneInput` 関数のラッパーである `libfuzzer_test_one_input` を呼び出します。このハーネスは libFuzzer と互換性があるため、この関数はこの用途にうってつけです。


{{< customFigure "任意で、LLVMFuzzerInitialize 関数を呼び出してハーネスを初期化します。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// The actual target run starts here.
// Call LLVMFUzzerInitialize() if present.
let args: Vec<String> = env::args().collect();
if libfuzzer_initialize(&args) == -1 {
    println!("Warning: LLVMFuzzerInitialize failed with -1");
}
```
{{< /customFigure >}}

現時点では、ハーネスで `LLVMFuzzerInitialize` 関数を使っていませんが、ハーネスに初期化が必要な場合に備えて、この関数があれば呼び出すのがよい習慣です。LibAFL は、この関数があればリンクして呼び出し、なければ何も起こりません。


{{< customFigure "最初のテストケースを読み込み、そのあと永遠にループして、ファジングを始めます。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/lib.rs)" >}}
```rust
// In case the corpus is empty (on first run), reset
if state.must_load_initial_inputs() {
    state
        .load_initial_inputs(&mut fuzzer, &mut executor, &mut restarting_mgr, &opt.input)
        .unwrap_or_else(|_| panic!("Failed to load initial corpus at {:?}", &opt.input));
    println!("We imported {} inputs from disk.", state.corpus().count());
}

fuzzer.fuzz_loop(&mut stages, &mut executor, &mut state, &mut restarting_mgr)?;
```
{{< /customFigure >}}

最後の設定は、クライアントが最初に起動したときに最初のコーパスを読み込み、`fuzz_loop` 関数を呼び出してファジングのループを始めることです。ここで注意すべき重要な点は、コーパスのテストケースのどれも興味深くなければ、ファザーは開始も実行もされないことです。ターゲットのカバレッジ計装が失敗した場合に、そうなる可能性があります。

これで、ファザーをビルドできます。

```shell
cargo build --release
```

できあがったバイナリは `target/release/libappsec_guide.a` にあります。

### ファズテストをコンパイルする {#compile-a-fuzz-test-rust}

前のセクションでは、独自の LibAFL ベースのファザーを作りました。次は、コンパイルしたファザーのランタイムである `libappsec_guide.a` を、ハーネスとターゲットにリンクします。[イントロダクション]({{% relref "fuzzing#introduction-to-fuzzers" %}})の `harness.cc` と `main.cc` を再利用します。できあがったバイナリは、ハーネスと libFuzzer のランタイムを使います。

このセクションでは、最終的なバイナリを作る 2 つの方法を紹介します。1 つ目は、冗長な方法でのリンクで、ファザーを作るのに必要な LLVM の機能をすべて詳しく示します。2 つ目は標準的な方法で、LibAFL を初めて使う人におすすめです。ただし、裏で何が起きているかを理解することは重要なので、冗長な方法から始めます。

#### 冗長な計装とリンク

Clang コンパイラを使う場合、次のコマンドで、カレントワーキングディレクトリに `fuzz` というバイナリができます。

```shell
clang++-15 -DNO_MAIN -g -O2 -fsanitize-coverage=trace-pc-guard -fsanitize=address -Wl,--whole-archive target/release/libappsec_guide.a -Wl,--no-whole-archive main.cc harness.cc -o fuzz
```

各引数の説明は次のとおりです。

* `clang++-15`: SUT を計装するのに使うコンパイラです。特定のバージョンの LLVM を使うには、たとえば `clang++` の代わりに `clang++-15` を使います。
* `-DNO_MAIN -g -O2`: これらの引数は、main.cc の `main` 関数のコンパイルを防ぎ、デバッグシンボルを追加して、最も一般的な本番用の最適化レベルを使います。
* `-fsanitize-coverage=trace-pc-guard`: この引数は、LLVM のカバレッジ計装を有効にします。これは必須です。そうしないと、ファザーはフィードバックを得られず、コーパスにテストケースを追加しません。
* `-fsanitize=address`: この引数は、AddressSanitizer を有効にします。
* `-Wl,--whole-archive target/release/libappsec_guide.a -Wl,--no-whole-archive`: これらの引数は、ファザーのランタイム全体をリンクします。`--whole-archive` がないと、リンカはファジングのランタイムを完全に捨て、[`libafl_main` 外部シンボル](https://github.com/AFLplusplus/LibAFL/blob/571c4c111e99924cf4ed5580622a018b3dbb21c9/libafl_targets/src/libfuzzer.c#L29)を null に設定します。この挙動はウィークシンボルに関連しており、この [StackOverflow の質問](https://stackoverflow.com/questions/2627839/weak-linking-with-static-libraries)でも説明されています。もう 1 つの回避策は、whole archive のフラグの代わりに `-u libafl_main` を追加することです。
* `main.cc harness.cc`: コンパイル、計装、リンクする SUT とハーネスです。
* `-o fuzz` \- 出力バイナリの引数です。

できあがったバイナリ `fuzz` を実行すると、ファジングキャンペーンが始まります。

#### 標準的なリンク

LibAFL で、ランタイム、SUT、ハーネスをリンクする標準的な方法は、コンパイラのラッパーを作ることです。SUT とハーネスをコンパイルするとき、LLVM の Clang を直接使う代わりに、コンパイルのフラグを解析し、フラグを変更・追加・削除して、LLVM の Clang を呼び出す、独自のラッパーを呼び出します。

LibAFL プロジェクトは、ラッパーを簡単に作れるライブラリ `libafl_cc` を提供しています。次の図はコンパイラのラッパーです。これを `libafl_cc.rs` として、Rust クレートの `src/bin` (Rust のバイナリの既定のパス) に追加します。


{{< customFigure "src/bin/libafl_cc.rs: LibAFL 用のコンパイラのラッパーのバイナリ。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/bin/libafl_cc.rs)" >}}
```rust
use std::env;

use libafl_cc::{ClangWrapper, CompilerWrapper, Configuration, ToolWrapper};

pub fn main() {
    let args: Vec<String> = env::args().collect();
    if args.len() > 1 {
        let mut dir = env::current_exe().unwrap();
        let wrapper_name = dir.file_name().unwrap().to_str().unwrap();

        let is_cpp = match wrapper_name[wrapper_name.len()-2..].to_lowercase().as_str() {
            "cc" => false,
            "++" | "pp" | "xx" => true,
            _ => panic!("Could not figure out if c or c++ wrapper was called. Expected {dir:?} to end with c or cxx"),
        };

        dir.pop();

        let mut cc = ClangWrapper::new();
        if let Some(code) = cc
            .cpp(is_cpp)
            .parse_args(&args)
            .expect("Failed to parse the command line")
            .link_staticlib(&dir, "appsec_guide")
            .add_args(&Configuration::GenerateCoverageMap.to_flags().unwrap())
            .add_args(&Configuration::AddressSanitizer.to_flags().unwrap())
            .run()
            .expect("Failed to run the wrapped compiler")
        {
            std::process::exit(code);
        }
    } else {
        panic!("LibAFL CC: No Arguments given");
    }
}
```
{{< /customFigure >}}

ラッパーのバイナリの名前によって、SUT が C か C++ かが決まります。そのため、プロジェクトに `src/bin/libafl_ccx.rs` というバイナリをもう 1 つ追加しました。


{{< customFigure "src/bin/libafl_cxx.rs: LibAFL 用の C++ コンパイラのラッパーのバイナリ。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide/src/bin/libafl_cxx.rs)" >}}
```rust
pub mod libafl_cc;

fn main() {
    libafl_cc::main();
}
```
{{< /customFigure >}}


次を実行して、両方のラッパーをコンパイルできます。

```shell
cargo build --release
```

そのあと、最終的なファザーのバイナリをコンパイルできます。

```shell
target/release/libafl_cxx -DNO_MAIN -g -O2 main.cc harness.cc -o fuzz
```

これで、それぞれ異なる接尾辞が付いた、複数のバイナリができます。ファザーにはカバレッジ計装が必要なので、`fuzz` バイナリを使う必要があります。`add_configuration` で設定を追加すれば、異なる計装を施した、さらに多くのバイナリを作れます。LibAFL のファザーは、計装と互換性がある必要がある点に注意してください。たとえば、ラッパーのスクリプトに cmplog 計装を追加しても、LibAFL のファザーは新しい計装を認識しません。ファザーの設定で、オブザーバとフィードバックを調整する必要があります。

### 使い方 {#usage}

初期コーパスを `corpus/` ディレクトリに置いて、単一のコアでファジングするには、次のコマンドを実行します。

```shell
./fuzz --cores 0 --input corpus
```

ファザーは、他にもいくつかのオプションに対応しています。たとえば、`--timeout` は、一定の実行時間を超える入力を見つけ、`--output` は、クラッシュまたはタイムアウトを起こすテストケースを保存するディレクトリを設定します。

既定の出力は、[libFuzzer の代替としての LibAFL](#libafl-as-libfuzzer-drop-in-replacement) のセクションで見た出力と同じように見えます。さらに、このセクションで作ったファザーは、統計を、ハードコードされた `fuzzer_stats.toml` というファイルに記録します。

ファザーは `main.cc` のバグをすぐに見つけます。ただし、既定では、バグを見つけてもファザーは終了しません。代わりにファジングを続け、ターミナルに表示される `objectives` カウンタが増えていきます。

以降のセクションでは、LibAFL がいかに拡張しやすいかを示す、追加の API を紹介します。

### ファザーを拡張する: バックトレースのハッシュでクラッシュの重複を排除する

上で紹介したファザーは、同じバグが原因でクラッシュするテストケースを、出力ディレクトリに保存します。たとえば、最初の 4 バイトにテストケースのサイズより大きい整数が入っていると、バッファオーバーフローを起こすテストケースがあるとします。他のバイトを変異させたものは別のテストケースですが、同じメモリ破壊を引き起こす可能性が高いです。出力ディレクトリは、同じメモリ破壊に至るテストケースですぐにいっぱいになります。これを避けるために、クラッシュのバックトレースを解析し、バックトレースが新しい場合にだけテストケースを保存する LibAFL の機能を使えます。

この LibAFL の機能には、2 つのコンポーネントが必要です。

* クラッシュが起きたときにバックトレースを見るオブザーバ、そして
* クラッシュが起きたときに評価されるフィードバック。このフィードバックは、クラッシュのバックトレースが新しいかを確認します。そのクラッシュが以前に観測されていなければ、フィードバックは true を返します。

まず、バックトレースのオブザーバを作ります。この例のファザーでは、各ファザーのクライアントが [`InProcessExecutor`](https://docs.rs/libafl/0.13.1/libafl/executors/inprocess/type.InProcessExecutor.html) を使うため、ハーネスの種類を `InProcess` に設定する必要があります。フォークサーバを使う場合は、これを変更してください。


{{< customFigure "バックトレースのオブザーバの作成。まだどこにも使われていません。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_deduplicate/src/lib.rs)" >}}
```rust
let backtrace_observer = libafl::prelude::BacktraceObserver::owned("BacktraceObserver", libafl::observers::HarnessType::InProcess);
```
{{< /customFigure >}}

次に、エグゼキュータの宣言にあるオブザーバのタプルに、オブザーバを追加します。ここに追加しないと、オブザーバは実行されません。


{{< customFigure "更新したエグゼキュータの宣言。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_deduplicate/src/lib.rs)" >}}
```rust
let mut executor = InProcessExecutor::with_timeout(
    &mut harness,
    tuple_list!(edges_observer, time_observer, backtrace_observer),
    &mut fuzzer,
    &mut state,
    &mut restarting_mgr,
    opt.timeout,
)?;
```
{{< /customFigure >}}

最後に、目的の定義を `NewHashFeedback` で更新します。`feedback_and` マクロを使うため、新しいバックトレースが見つかった場合にだけ、目的が追加されます。このフィードバックは、最新のバックトレースのハッシュを取得して、集合に保存します。そのハッシュがまだ観測されていない場合にだけ、フィードバックは true を返します。


{{< customFigure "更新した目的の宣言。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_deduplicate/src/lib.rs)" >}}
```rust
let mut objective = feedback_and!(feedback_or_fast!(CrashFeedback::new(), TimeoutFeedback::new()), libafl::feedbacks::new_hash_feedback::NewHashFeedback::new(&backtrace_observer));
```
{{< /customFigure >}}

{{< hint info >}}
プロのヒント: 見つかったクラッシュを修正したあと、またはクラッシュが見つからなかった場合は、重複排除なしで少なくとも 1 回ファザーを実行することをおすすめします。LibAFL にはまだ安定版のリリースがないため、重複排除にバグがあり、クラッシュを見逃す可能性があります。この機能は、ターゲットを初めてファジングし、到達しやすいクラッシュがある場合には、引き続き役立ちます。ただし、最初のクラッシュ群を修正したあとは、重複排除なしでファザーを再実行してください。
{{< /hint >}}

### ファザーを拡張する: 辞書によるファジング

辞書の情報でファジングするために、まず、例のファザーにコマンドラインオプションを追加します。引数の解析には [clap](https://github.com/clap-rs/clap) ライブラリを使います。ここでは、AFL++ と同じように、短いフラグ `-x,` を使う tokens 引数を追加します。LibAFL は、辞書を指して「トークンの集合」という言葉を使います。[AFL++ の辞書の形式](https://github.com/AFLplusplus/AFLplusplus/blob/stable/dictionaries/README.md)は、ここで読み込むトークンのファイルと互換性があります。



{{< customFigure "辞書ファイルを解析する、ファザーの新しい引数。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_tokens/src/lib.rs)" >}}
```rust
/// The commandline args this fuzzer accepts
#[derive(Debug, Parser)]
#[command(
    name = "appsec_guide",
    about = "A libfuzzer-like fuzzer with llmp-multithreading support and a launcher"
)]
struct Opt {
    ...

    #[arg(
    short = 'x',
    long,
    help = "Path to a tokens file",
    name = "TOKENS"
    )]
    tokenfile: Option<PathBuf>,
}
```
{{< /customFigure >}}

次に、トークンのファイルへのパスを使って、トークンを読み込みます。まず `Tokens` 構造体を作り、トークンのファイルから内容を埋めます。そのあと、トークンをファザーの状態に追加します。


{{< customFigure "ファイルからトークンを読み込み、ファザーの状態に追加する。" >}}
```rust
let mut state = state.unwrap_or_else(|| {
    ...
});

let mut tokens = Tokens::new();
if let Some(tokenfile) = &opt.tokenfile {
    tokens.add_from_file(tokenfile)?;
}

println!("Using tokens: {:?}", &tokens);

if !tokens.is_empty() {
    state.add_metadata(tokens);
}
```
{{< /customFigure >}}

ファザーがトークンを利用できるようになったので、状態のメタデータを実際に使う変異を、ミューテータに追加する必要があります。havoc 変異のリストを、トークンの変異で拡張します。


{{< customFigure "havoc 変異とトークンの変異を使う、更新したミューテータ。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_tokens/src/lib.rs)" >}}
```rust
let mutator = StdScheduledMutator::new(havoc_mutations().merge(tokens_mutations()));
```
{{< /customFigure >}}

これで、ファザーの基本的な設定は完了です。特定の目的に特化したファザーなら、トークンをコマンドラインインターフェースで設定できるようにせず、ハードコードすることを選んでもよいでしょう。たとえば PNG ファイル形式なら、次のようなトークンを作れます。


{{< customFigure "PNG ファイル形式のハードコードされたトークン" >}}
```rust
state.add_metadata(Tokens::from([
    vec![137, 80, 78, 71, 13, 10, 26, 10], // PNG header
    "IHDR".as_bytes().to_vec(),
    "IDAT".as_bytes().to_vec(),
    "PLTE".as_bytes().to_vec(),
    "IEND".as_bytes().to_vec(),
]));
```
{{< /customFigure >}}

#### 自動トークンによるファジング

AFL++ は当初、[AUTODICTIONARY](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.lto.md#autodictionary-feature) 機能を導入しました。これは、Clang のコンパイルパスを使って、プログラムからマジック値やチェックサムを抽出するものです。ファザーはこれらの値を使って、ファジングのカバレッジを改善できます。

まず、`main.cc` ファイルの `check_buf` 関数を更新して、自動トークン機能が値を抽出するのに使える `memcmp` 関数の呼び出しを含めます。


{{< customFigure "memcmp を呼び出す SUT。ファザーは入力を文字列「buf」と比較しています。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_tokens/src/lib.rs)" >}}
```rust
void check_buf(char *buf, size_t buf_len) {
    if (buf_len >= 4) {
        if (memcmp(buf, "buf", 4) == 0) {
            abort();
        }
    }

    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                abort();
            }
        }
    }
}
```
{{< /customFigure >}}

このパスは、`libafl_cc.rs` ファイルに自動トークンのパスを含めることで有効にできます。


{{< customFigure "自動トークンのコンパイルパスを有効にする。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_tokens/src/lib.rs)" >}}
```rust
let mut cc = ClangWrapper::new();
if let Some(code) = cc
    .cpp(is_cpp)
    // silence the compiler wrapper output, needed for some configure scripts.
    .silence(true)
    .parse_args(&args)
    .expect("Failed to parse the command line")
    .link_staticlib(&dir, "appsec_guide")
    .add_args(&Configuration::GenerateCoverageMap.to_flags().unwrap())
    .add_args(&Configuration::AddressSanitizer.to_flags().unwrap())
    .add_pass(LLVMPasses::AutoTokens)
    .run()
    .expect("Failed to run the wrapped compiler")
{
    std::process::exit(code);
}
```
{{< /customFigure >}}

Clang のパスが成功したことを確認するには、`gdb` を使って、セクションに値が入っているかを調べられます。

```shell
echo "p (uint8_t *)__token_start" | gdb fuzz
```

グローバル変数が null なら、パスは実行されていません。

SUT とハーネスを `libafl_cc` でコンパイルすると、ファザーに新しいセクションが追加されます。次のコードで、コンパイルに組み込まれたトークンを実行時に読み取り、`Tokens` 構造体に追加できます。


{{< customFigure "コンパイルに組み込まれた自動トークンの取り込み。[完全なソースコード](https://github.com/trailofbits/testing-handbook/blob/main/materials/fuzzing/libafl/appsec_guide_tokens/src/lib.rs)" >}}
```rust
tokens += libafl_targets::autotokens()?;
```
{{< /customFigure >}}

### ファザーを拡張する: デバッグ

LibAFL のファザーをデバッグする必要が生じることがあります。マルチプロセスの性質のため、GDB のようなデバッガでアタッチするのが難しいことがあります。簡単なコツは、ファザーを単一のプロセスで動かすことです。Launcher を作って起動する代わりに、`run_client` クロージャを直接実行できます。ランチャーのコードをコメントアウトして、クロージャを直接呼び出すだけです。


{{< customFigure "ファザーを単一のプロセスで動かすための調整。" >}}
```rust
run_client(None, libafl::prelude::SimpleEventManager::new(monitor), 0).unwrap();

// match Launcher::builder()
//     .shmem_provider(shmem_provider)
//     .configuration(EventConfig::from_name("default"))
//     .monitor(monitor)
//     .run_client(&mut run_client)
//     .cores(&cores)
//     .broker_port(broker_port)
//     .remote_broker_addr(opt.remote_broker_addr)
//     .stdout_file(Some("/dev/null"))
//     .build()
//     .launch()
// {
//     Ok(()) => (),
//     Err(Error::ShuttingDown) => println!("Fuzzing stopped by user. Good bye."),
//     Err(err) => panic!("Failed to run launcher: {err:?}"),
// }
```
{{< /customFigure >}}

そのあと、GDB でファザーを実行できます。

```shell
gdb --args ./fuzz --cores 0 --input corpus
```



## 実際の例 {#real-world-examples}

### libpng {#libpng}

静的ライブラリを生成する C のプロジェクトをファジングする場合は、次の手順に従えます。

1. プロジェクトのコードベースにある `INSTALL` ファイル (または他の適切なドキュメント) を読んで、静的ライブラリの作り方を調べます。
2. コンパイラを、LibAFL ベースのファザーのラッパーに設定し、コンパイル時に必要なフラグをコンパイラに渡します。
3. LibAFL のコンパイラのラッパーを使って、静的ライブラリをビルドします。このビルド手順で、計装された静的ライブラリができます。これを `$static_library` と呼びます。
4. 手順 3 でコンパイルした静的ライブラリを見つけ、`target/release/libafl-cxx $static_library harness.cc -o fuzz` を実行します。
5. `./fuzz --input seeds/ --cores 0-8` を実行すると、ファジングを始められます。

有名な libpng ライブラリで、この手順を順にやってみましょう。まず、ソースコードを取得します。

```shell
curl -L -O https://downloads.sourceforge.net/project/libpng/libpng16/1.6.37/libpng-1.6.37.tar.xz
tar xf libpng-1.6.37.tar.xz
cd libpng-1.6.37/
```

libpng をコンパイルする前に、その依存パッケージをインストールする必要があります。

```shell
apt install zlib1g-dev
```

次に、Cargo プロジェクトへのパスを保持する変数を設定します。

```shell
export FUZZER_CARGO_DIR="/some/path"
```

次に、libFuzzer をリンクせずに、libpng を静的ライブラリとして設定し、コンパイルします。

```shell
export CC=$FUZZER_CARGO_DIR/target/release/libafl_cc
export CXX=$FUZZER_CARGO_DIR/target/release/libafl_cxx
./configure --enable-shared=no # Configure to compile a static library
make # Run compilation
```

既定では、設定スクリプトは最適化レベルを `-O2` に設定します。これは、[ファズテストをコンパイルする](#compile-a-fuzz-test-libfuzzer)のセクションでおすすめしているレベルです。

次に、GitHub からハーネスをダウンロードします。通常は、ハーネスを自分で書く必要があります。ただ、この例では、既存のもので十分です。

```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/f8e5fa92b0e37ab597616f554bee254157998227/contrib/oss-fuzz/libpng_read_fuzzer.cc
```

最後に、計装した libpng、ハーネス、libFuzzer のランタイムをまとめてリンクします。

```shell
$CXX libpng_read_fuzzer.cc .libs/libpng16.a -lz -o fuzz
```

キャンペーンを始める前に、シードを用意する必要があります。AFL++ は、空のシードの集合から始められないためです。小さなサンプルの PNG ファイルをダウンロードして用意します。

```shell
mkdir seeds/
curl -o seeds/input.png https://raw.githubusercontent.com/glennrp/libpng/acfd50ae0ba3198ad734e5d4dec2b05341e50924/contrib/pngsuite/iftp1n3p08.png
```

前のセクションで説明したとおり、トークンファイルを使う `-x` オプションを追加した場合は、PNG 形式の[辞書]({{% relref 02-dictionary %}})もダウンロードして、ファザーをよりうまく導けます。辞書は、PNG が使うマジックバイトなど、ファイル形式についての最初の手がかりをファザーに与えます。

```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/2fff013a6935967960a5ae626fc21432807933dd/contrib/oss-fuzz/png.dict
```

ファジングキャンペーンは、次を実行して始められます。

```shell
./fuzz --input seeds/ --cores 0 -x png.dict
```

### CMake ベースのプロジェクト {#cmake-based-project}

[イントロダクション]({{% relref "fuzzing#introduction-to-fuzzers" %}})で触れたプログラムのビルドに、CMake を使っているとします。`main.cc` と `harness.cc` をビルドし、ターゲットを LibAFL とリンクする CMake のターゲットを追加します。main 関数は `NO_MAIN` フラグで除外している点に注意してください。そうしないと、プログラムに main 関数が 2 つできてしまいます。


{{< customFigure "CMake の例" >}}
```cmake
project(BuggyProgram)
cmake_minimum_required(VERSION 3.0)

add_executable(buggy_program main.cc)

add_executable(fuzz main.cc harness.cc)
target_compile_definitions(fuzz PRIVATE NO_MAIN=1 )
target_compile_options(fuzz PRIVATE -g -O2)
```
{{< /customFigure >}}

計装なしのバイナリは、次のコマンドでビルドできます。

```shell
cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ .
cmake --build . --target buggy_program
```

次に、Cargo プロジェクトへのパスを保持する変数を設定します。

```shell
export FUZZER_CARGO_DIR="/some/path"
```

そこから、libFuzzer をリンクせずに、libpng を静的ライブラリとして設定し、コンパイルします。

ファザーは、ファズのターゲットを選び、コンパイラを変更することでビルドできます。

```shell
cmake -DCMAKE_C_COMPILER=$FUZZER_CARGO_DIR/target/release/libafl_cc  -DCMAKE_CXX_COMPILER=$FUZZER_CARGO_DIR/target/release/libafl_cxx .
cmake --build . --target fuzz
```

ファジングキャンペーンは、次を実行して始められます。

```shell
./fuzz --input seeds/ --cores 0
```

## 追加のリソース

* [LibAFL の公式ハンドブック](https://aflplus.plus/libafl-book/)
* [Rust のプロジェクトで LibAFL を使う方法の説明](https://github.com/AFLplusplus/LibAFL/tree/main/crates/libafl_libfuzzer#usage)
  - [LibAFL のシムで cargo-fuzz を使うプロジェクト](https://github.com/AFLplusplus/LibAFL/tree/main/fuzzers/fuzz_anything/cargo_fuzz)の例
