---
title: "AFL++"
slug: aflpp
weight: 2
---


# AFL++ {#afl}

[AFL++](https://github.com/AFLplusplus/AFLplusplus) ファザーは、[AFL](https://github.com/google/AFL) ファザーから派生したものです。ファジングの性能が高く、より高度な機能を備えながら、libFuzzer の代わりとして十分に安定しています。libFuzzer に比べた大きな利点は、AFL++ は複数のコアでファジングのキャンペーンを動かすことを、安定してサポートしている点です([マルチコアファジング](#multi-core-fuzzing)を参照)。

{{< fuzzing/intro-os >}}
AFL++ は [macOS](https://github.com/AFLplusplus/AFLplusplus/blob/stable/docs/INSTALL.md#macos-x-on-x86-and-arm64-m1) など別の環境にも対応していますが、注意点があります。macOS のコンピュータしかない場合は、手元の x86_64 の VM でファジングするか、DigitalOcean、AWS、Hetzner などで VM を借りると、セットアップが簡単になります。


## インストール {#installation}

AFL++ ファザーは、LLVM、Python、Rust など、多くの依存関係を持ちます。AFL++ でファジングするには、十分にテストされている、現行の Debian か Ubuntu のディストリビューションをお勧めします。なお、コンパイル済みの AFL++ を使うと、AFL++ のコンパイル時に使われた Clang と GCC のバージョンに縛られます。次の表に、インストール方法と、対応するコンパイラのバージョンをまとめます。

<!-- TODO translate table to markdown? -->
{{< rawHtml "" >}}
<table>
  <tr>
    <td><strong>方法</strong></td>
    <td><strong>どんなときに使うか</strong></td>
    <td>
      <strong>対応するコンパイラのバージョン(<code>afl-clang-fast/afl-gcc --version</code>)</strong>
    </td>
  </tr>
  <tr>
    <td>Ubuntu/Debian のリポジトリから</td>
    <td>
      <ul>
        <li>最近の、LTS ではない Ubuntu のディストリビューションを使っている。</li>
        <li>AFL++ の基本的な機能だけを使いたい。</li>
      </ul>
    </td>
    <td>
      <ul>
        <li>Ubuntu 23.10: Clang 14 & GCC 13</li>
        <li>Debian 12: Clang 14 & GCC 12</li>
      </ul>
    </td>
  </tr>
  <tr>
    <td>Docker(Docker Hub から)</td>
    <td>
      <ul>
        <li>AFL++ の特定のバージョンを使いたい。</li>
        <li>
          Apple Silicon で動かしていて、手元のデバイスでファジングしたい。この
          Docker イメージは <code>arm64</code> に対応している。
        </li>
        <li>
          Docker を使うと、
          <a href="{{% relref 04-env%}}">ファジング環境</a>で説明している性能の低下がありうることを理解している。
        </li>
      </ul>
    </td>
    <td>このイメージのバージョン 4.35c を書いた時点では、Clang 19 & GCC 11</td>
  </tr>
  <tr>
    <td>Docker(ソースから)</td>
    <td>
      <ul>
        <li>上の行と同じ理由。</li>
        <li>AFL++ の未リリースの機能を試したい。</li>
        <li>AFL++ にパッチを当てたい。</li>
        <li>Docker Hub が使えない。</li>
      </ul>
    </td>
    <td>
      次のファイルで設定できる:
      <a
        href="https://github.com/AFLplusplus/AFLplusplus/blob/stable/Dockerfile#L18-L22"
        >Dockerfile</a
      >。
    </td>
  </tr>
  <tr>
    <td>ソースから</td>
    <td>
      <ul>
        <li>AFL++ の未リリースの機能を試したい。</li>
        <li>AFL++ の特定のバージョンを使い、パッチも当てたい。</li>
        <li>Docker を避けたい。</li>
      </ul>
    </td>
    <td>
      環境変数
      <code>LLVM_CONFIG</code> を、たとえば <code>llvm-config-18</code> に設定して調整できる。
    </td>
  </tr>
</table>
{{< /rawHtml >}}


### Ubuntu {#ubuntu}

最近の Debian か Ubuntu を使っているなら、公式の Ubuntu リポジトリにあるパッケージ版が手軽な選択です。この文章を書いた時点では、Ubuntu 23.10 は AFL++ 4.08c を、Debian 12 はバージョン 4.04c をパッケージにしています。この場合、使える Clang のバージョンは、パッケージ版の AFL++ が対応するものに限られる点に注意してください。


注: `lld` をインストールする前に、使っているディストリビューションで AFL++ がどのバージョンの Clang を使うかを確認してください。`afl-cc --version` を実行して確かめ、対応するバージョンの `lld`(例: `lld-17`)をインストールします。

```shell
apt install afl++ lld-17
```


`lld` パッケージのインストールは、あとで説明する、任意の LTO モードに必要です。使っている Linux ディストリビューションで AFL++ が使う Clang のバージョンによっては、`lld-17` のように特定のバージョンの `lld` をインストールするとよいでしょう。`afl-cc --version` の出力を確かめてください。


### Docker(Docker Hub から) {#docker-from-docker-hub}

AFL++ の最新の安定版を使いたい場合は、Git のタグのどれかを指定して、Dockerhub からイメージを取得します。


```shell
docker pull aflplusplus/aflplusplus:stable
```


特定のバージョンを使いたい場合は、`stable` を、たとえば `4.08c` に置き換えます。


### Docker(ソースから) {#docker-from-source}

別の方法として、特定の Git タグをクローンして、[Docker](https://docs.docker.com/engine/install/) でローカルにビルドすることもできます。


```shell
git clone --depth 1 --branch stable https://github.com/AFLplusplus/AFLplusplus
cd AFLplusplus
docker build -t aflplusplus
```


特定のバージョンを使いたい場合は、`stable` を、たとえば `4.08c` に置き換えます。


### ソースから {#from-source}

[ソースからコンパイル](https://github.com/AFLplusplus/AFLplusplus/blob/stable/docs/INSTALL.md)したい場合は、どの Ubuntu のバージョンを使い、どの依存関係が必要かについて、[Dockerfile](https://github.com/AFLplusplus/AFLplusplus/blob/stable/Dockerfile) の記述を参照してください。


---


ここで、コマンドをホストか Docker で実行する、簡単なラッパースクリプトを作ります。  

Docker の場合は、使い捨てのコンテナを起動します。つまり、実行後にコンテナが自動で削除されます。また、現在の作業ディレクトリを、コンテナ内のパス `/src` にマウントします。さらに、[AFL++ の作者が勧めている](https://github.com/AFLplusplus/AFLplusplus/blob/9d305acbf39549f9625bd030b62c10fce7abe24c/afl-system-config#L59)ように、ファジングの性能を上げるために、` --privileged` を使って `seccomp` を無効にします。最後に、コンテナ内で動くプロセスに、root の全権限も与えます。**この節の最後にあるセキュリティ上の注意を確認してください。このスクリプトを、開発用のノート PC で実行するのは避けてください。代わりに、ファジング専用の仮想マシンを使ってください。**

次のスクリプトを `afl++.sh` という名前で作り、実行できるようにします。

```shell
cat <<'EOF' > ./afl++
#!/bin/sh
AFL_VERSION="${AFL_VERSION:-"stable"}"
case "$1" in
   host)
        shift 
        bash -c "$*"
        ;;
    docker)
        shift
        /usr/bin/env docker run -ti \
            --privileged \
            -v ./:/src \
            --rm \
            --name afl_fuzzing \
            "aflplusplus/aflplusplus:$AFL_VERSION" \
            bash -c "cd /src && bash -c \"$*\""
        ;;
    *)
        echo "Usage: $0 {host|docker}"
        exit 1
        ;;
esac
EOF
chmod +x ./afl++
```


`afl++`: AFL++ をホストか Docker のどちらかで実行するスクリプト。Docker を使う場合は、環境変数 `AFL_VERSION` で AFL++ のバージョン(例: `v4.08c`)を指定できます。指定しなければ、最新の安定版が選ばれます。

最後に、ファジングを始める前に、[`afl-system-config`](https://github.com/AFLplusplus/AFLplusplus/blob/0c054f520eda67b7bb15f95ca58c028e9b68131f/afl-system-config) スクリプトを実行します。システムが設定され、1 秒あたりの実行回数が最大 15% 増えます。 


```shell
./afl++ <host/docker> afl-system-config
```

このコマンドは、使っているシステムを再起動するたびに実行する必要があります。さらに、カーネルのセキュリティ緩和策(たとえば [Spectre](https://en.wikipedia.org/wiki/Spectre_(security_vulnerability)) 対策)を無効にしたい場合は、[`afl-persistent-config`](https://github.com/AFLplusplus/AFLplusplus/blob/0c054f520eda67b7bb15f95ca58c028e9b68131f/afl-persistent-config) スクリプトを実行し、ブートローダを再設定して、システムを再起動します。このスクリプトは、ブートローダの設定を書き換えるため、Docker を使わず、かつ [grub](https://www.gnu.org/software/grub/) ブートローダを使っている場合にだけ実行できます。緩和策は、[VM をホストするベアメタルのサーバーと、VM 自体](https://security.stackexchange.com/questions/199355/is-meltdown-spectre-mitigation-necessary-in-virtual-machine-as-well-as-in-hyperv)の両方で無効にするべきです。再起動したあとは、`afl-system-config` をもう一度実行することを忘れないでください。


```shell
./afl++ host afl-persistent-config
update-grub
reboot
./afl++ <host/docker> afl-system-config
```

再起動したあとは、`cat` `/proc/cmdline` を実行して、`afl-persistent-config` による変更が正しく適用されたかを確かめます。出力に `mitigations=off` が含まれているはずです。含まれていない場合は、grub ブートローダの設定が正しくありません。ファイル `/etc/default/grub` とディレクトリ `/etc/default/grub.d/` の設定を確認してください。設定ファイルのどれかが `GRUB_CMDLINE_LINUX_DEFAULT` を誤って上書きしていると、緩和策が適用されないおそれがあります。たとえば、[cloud-init](https://cloudinit.readthedocs.io/) を使うクラウド環境がこれに当てはまります。


{{< hint danger >}}
**`afl-system-config` と `afl-persistent-config` のスクリプトは root 権限を必要とし、オペレーティングシステムの一部のセキュリティ機能を無効にします。そのため、スクリプトとその出力を必ず確認してください。本番のシステムや、開発環境でファジングしないでください。** たとえばノート PC でファジングしたい場合は、VM を作ってください。Apple Silicon で Docker を使ってファジングする場合は、Docker のコンテナがすでに VM の中で動いています。なお、Linux で Docker を使うと、`afl-system-config` スクリプトで適用した設定は、スクリプトをコンテナの内部で実行しても、コンテナの外に影響することに注意してください。
{{< /hint >}}

## ファジングテストのコンパイル {#compile-a-fuzz-test}

SUT(テスト対象)をファジングするバイナリの作成は、簡単です。できあがるバイナリは、ハーネスと AFL++ のランタイムを使います。

AFL++ ファザーには、[LTO](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.lto.md)、[LLVM](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.llvm.md)、[GCC](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.gcc_plugin.md) など、複数のコンパイルモードがあります。それぞれの詳細は、リンク先のドキュメントを参照してください。どれにするかを決めるには、次の図を参照してください。


{{< resourceFigure "aflpp-decision.drawio.svg" />}}


選んだモードに応じて、それぞれ別のコンパイルコマンド(`afl-clang-lto`、`afl-clang-fast`、`afl-gcc`)を使います。末尾に `++` を付けると、C++ 版(たとえば `afl-clang-lto++`)も使えます。LTO モードは、SUT の計装がより優れていて速いので、お勧めです。ただし、LTO モードが動くかどうかは、プロジェクトによります。まず試してみて、コンパイルに失敗したら、ほかのモードに切り替えてください。

Clang コンパイラを使っていて、LLVM モードを使いたい場合は、次のコマンドでバイナリ `fuzzer` ができます。要するに、`clang++` の呼び出しを `afl-clang-fast++` に置き換えています。[導入]({{% relref "fuzzing#introduction-to-fuzzers" %}})で使った `harness.cc` と `main.cc` を再利用します。


{{< tooltipHighlight shell
"Custom script (see above)"
"Run on host or within Docker"
"AFL++ compiler that uses Clang"
"Skips the main function"
"Sets production optimization level"
"Enables libFuzzer"
 >}}
./afl++ <host/docker> afl-clang-fast++ -DNO_MAIN=1 -O2 -fsanitize=fuzzer harness.cc main.cc -o fuzz
{{< / tooltipHighlight >}}


プロジェクトが GCC コンパイラに依存している場合は、[gcc_plugin](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.gcc_plugin.md) の利用を検討してください。

{{< tooltipHighlight shell
"Custom script (see above)"
"Run on host or within Docker"
"AFL++ compiler that uses GCC"
"Skips the main function"
"Sets production optimization level"
"Enables libFuzzer"
 >}}
./afl++ <host/docker> afl-g++-fast -DNO_MAIN=1 -O2 -fsanitize=fuzzer harness.cc main.cc -o fuzz
{{< / tooltipHighlight >}}


{{< hint info >}}
ヒント: 使っているシステムの GCC のバージョンと、AFL++ の GCC プラグインのコンパイルに使われた GCC のバージョンは、一致していなければなりません。一致していない場合(たとえば、GCC をアップグレードした場合)は、GCC のサポートを使うときにエラーになります。
{{< /hint >}}

最適化レベルは `-O2` にします。本番で使われるレベルである可能性が高いので、ファジングに適した最適化レベルです。なお、`-g` は必要ありません。AFL++ のコンパイラが、既定で追加します。

AFL++ を使うとき、裏では多くのことが起きています。 


* `afl-clang-fast++` バイナリは、Clang のラッパースクリプトで、特定のコンパイルパスや機能を有効にします。
* 使ったモード(LTO、LLVM、Clang、GCC)に応じて、カバレッジの計装が行われます。
* `-fsanitize=fuzzer` を使うと、AFL++ が libFuzzer のハーネスと互換になります。このフラグを使わないと、AFL++ はプログラムの標準入力をファジングします。   

`fuzz` というバイナリを作りました。次の節では、このバイナリを使ってファジングのキャンペーンを始める方法を説明します。

## 使い方 {#usage}

ファジングのキャンペーンを始めるには、まずシードのディレクトリを作ります。これがファザーの入力になります。AFL++ は、空のディレクトリや、空のシードファイルだけが入ったディレクトリには対応していません。


```shell
mkdir seeds
echo "aaaa" > seeds/minimal_seed
```

これで、キャンペーンを始められます。

```shell
./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz
```

{{< hint info >}}
ヒント: afl++ スクリプトで環境変数を設定する方法を示すために、環境変数 AFL_FAST_CAL を 1 にして、最初のキャリブレーションの段階を速くしてみましょう。

```shell
./afl++ <host/docker> AFL_FAST_CAL=1 afl-fuzz -i seeds -o out -- ./fuzz
```
{{< /hint >}}


ファザーの出力は、次の図のようになります。

{{< resourceFigure "aflpp.png" >}}
スクリーンショットの各行の意味は、この[ドキュメント](https://github.com/AFLplusplus/AFLplusplus/blob/358cd1b062e58ce1d5c8efeef4789a5aca7ac5a9/docs/afl-fuzz_approach.md)を参照してください。
{{< / resourceFigure >}}


ファザーの出力は、`out` ディレクトリに保存されます。その中身を次に説明します。

```text
out/default/
├── cmdline - How was the SUT invoked?
├── crashes - Directory with inputs that crash the SUT
│   ├── README.txt - How do I reproduce these crashes?
│   └── id:000000,sig:06,src:000002,time:286,execs:13105,op:havoc,rep:4
├── fuzz_bitmap - Internal fuzzer bit map
├── fuzzer_setup - What was the fuzzer environment and what afl-fuzz arguments were used?
├── fuzzer_stats - When did this campaign run? How long did it run? etc.
├── hangs - Directory with inputs that hang the SUT
├── plot_data - Data over time that can be plotted
└── queue - Test cases that reproduce the final fuzzer state when rerun
    ├── id:000000,time:0,execs:0,orig:minimal_seed
    └── id:000001,src:000000,time:0,execs:8,op:havoc,rep:6,+cov
    └── id:000002,src:000000,time:21,execs:894,op:havoc,rep:2,+cov
```

{{< hint info >}}
ヒント: クラッシュのファイル名には、そのクラッシュがどこから来たかについての、正確な情報が含まれています。名前 `id:000000,sig:06,src:000002,time:286,execs:13105,op:havoc,rep:4` は、ID 0 のクラッシュが、SUT でシグナル 6 を起こしたことを示します。クラッシュの入力は、ID 2 の元のテストケースに由来します。テストケース 2 は、テストケース ID 0 のシード入力に由来します。そのほかのデータは、たとえば、クラッシュがいつ見つかったか、どの変異が発見につながったかを示します。
{{< /hint >}}



{{< hint info >}}
ヒント: ファジングのキャンペーン中や、終わったあとに、その状況を知る最も簡単な方法は、統計を見ることです。

```shell
./afl++ <host/docker> afl-whatsup out
```
そして、グラフを作ります。

```shell
./afl++ <host/docker> afl-plot out/default out_graph/
```
上のコマンドを実行するには、gnuplot をインストールする必要があります(例: apt install gnuplot)。
{{< /hint >}}

### テストケースの再実行 {#re-execute-a-test-case}

バグを調べるために、libFuzzer と同じように、次のコマンドでテストケースを再実行できます。


```shell
./afl++ <host/docker> ./fuzz out/default/crashes/<test_case>
```


ただし、AFL++ が作る libFuzzer 風のバイナリは、ディレクトリ全体を実行できず、個々のテストケースしか実行できません。そのため、複数のテストケースを実行したい場合(たとえば、カバレッジのデータを集めるとき)は、1 つずつ実行するスクリプトを書く必要があります。  

AFL++ が作る libFuzzer 互換のバイナリについて詳しくは、ヘルプのページを参照してください。

```shell
./afl++ <host/docker> ./fuzz -help=1
```

### ファザーのオプション {#fuzzer-options}

AFL++ ファザーには、多くのオプションがあります。`afl-fuzz` ツールで特に役立つのは、次のオプションです。

* **-G 4000** テスト入力の最大の長さ。既定では、AFL++ は 1048576 バイトを使います。最小の入力サイズの数倍以上に設定することをお勧めします。経験則として、現実的な最小の入力を見つけて、それを 2 倍にすることをお勧めします。なお、入力サイズを大きくすると、実行時間が長くなりますが、探索される入力空間が必ずしも広くなるわけではありません。
* **-t 1000** AFL++ は、n ミリ秒たつとテストケースの実行を打ち切ります(既定は 1000 ms)。これは、ほどほどに小さい値にするのが理にかなっています。SUT が不当に長い時間ハングするような入力を見つけることも、目的だからです。たとえば、妥当なサイズの PNG 画像の解析に、数百ミリ秒以上かかるべきではありません。そのため、数秒に設定すれば、たいてい、誤検知を避けるのに十分です。 
* **-m 1000** テストケースのメモリ制限(メガバイト単位)。既定では 0 で、制限なしを意味します。1000 のような妥当な値に設定するべきです。低すぎると、誤検知が出ます。テストケースが、(たとえば、システムの負荷のせいで)通常よりわずかに長くかかることが、ときどきあるためです。
* **-x ./dict.dict** ファザーを誘導する辞書ファイルを指定します。これにより、ファザーは、興味深いテストケースをより速く見つけられます。詳しくは、[ファジング用の辞書]({{% relref 02-dictionary %}})を参照してください。

## 標準入力(stdin)のファジング {#standard-input-stdin-fuzzing}

AFL++ ファザーは、標準入力から入力を受け取る、計装済みのバイナリを実行できます。この方法は、libFuzzer のハーネス(`LLVMFuzzerTestOneInput`)を書くより遅くなりますが、ハーネスを書く必要がないので、使いやすいことがあります。詳しくは、次のヒントで説明します。

{{< hint info >}}
ヒント: AFL++ には、SUT を実行するモードがいくつかあります。違いは、ターゲットの実行のしかたです。内部の詳細ですが、覚えておくとよいでしょう。SUT は、サブプロセス、遅延フォークサーバー、パーシステントモードのどれかで実行できます。

**サブプロセス。** テストケースごとに、サブプロセスが作られます(`execve`)。これは、たとえば SUT がコマンドライン引数や標準入力で入力を受け取る場合に必要です。この場合、呼び出しのたびに新しいプロセスが起動されます。このモードは、環境変数 `AFL_NO_FORKSRV=1` を設定すると有効になります。性能が低いため、このモードはお勧めしませんが、SUT が main 関数の前に初期化を行う場合は、必要になることがあります。

**フォークサーバー。** SUT のためにサブプロセスが起動されます。プログラムは main 関数まで実行されます。実際の main 関数を始める前に、プロセスがフォークされます。実行のたびに、その実行地点からプロセスがフォークされます。これにより、`execve` システムコールの数が減って節約され、性能が上がります。これは、標準入力経由でファジングするときにだけ使えます。

**パーシステントモード。** ファザーは、テストケースを 1 つのプロセスで実行します。テストケースがクラッシュすると、親プロセスがファジングのループを再開します。これは、`LLVMFuzzerTestOneInput` を使う libFuzzer 形式のハーネスを使うときに使えます。ハーネスが、実行のたびに、SUT の状態をきれいにリセットすることが重要です。そうしないと、実行同士が影響し合うおそれがあります。パーシステントモードは、`__AFL_FUZZ_INIT()` と `__AFL_FUZZ_TESTCASE_BUF` のマクロに関係します。

**共有メモリによるファジング。** パーシステントモードだけを有効にした場合、テストケースは、標準入力経由で渡されるか、ファイルから読み込まれます。
共有メモリの機能は、`__AFL_INIT()` と `__AFL_LOOP(n)` のマクロに関係します。
通常、パーシステントモードについてのオンラインの例に出会ったときは、共有メモリによるファジングも有効になっています。 
[引数のファジング](#argument-fuzzing-argument-fuzzing)の例は、パーシステントモードと共有モードを有効にします。ファジングの構成とオペレーティングシステムが許せば、上のすべての場合で、カバレッジ情報は共有メモリを使ってやり取りされます。この共有メモリの使い方は、AFL++ の「共有メモリ」の機能とは関係ありません。

パーシステントモードは、フォークサーバーより少なくとも 10 倍速いので、一般にこちらが好まれます。
{{< /hint >}}


まず、元の例を、標準入力から入力を受け取るように書き換えましょう。


{{< customFigure "main_stdin.cc: 標準入力で入力を受け取るプログラム。" >}}
```C++
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BUF_SIZE 100

void check_buf(char *buf, size_t buf_len) {
    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                abort();
            }
        }
    }
}

int main() {
    char input_buf[MAX_BUF_SIZE];

    if (fgets(input_buf, MAX_BUF_SIZE, stdin) == NULL) {
        return 1;
    }

    size_t len = strlen(input_buf);
    check_buf(input_buf, len);
    return 0;
}
```
{{< /customFigure >}}


上の例は、標準入力から読み込むようになりました。入力 "abc" で abort します。


```shell
./afl++ <host/docker> afl-clang-fast++ -O2 main_stdin.c -o fuzz_stdin
```


ファジングのキャンペーンは、libFuzzer 風のハーネスと同じ方法で始められます。


```shell
./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz_stdin
```


[ファジングテストのコンパイル](#compile-a-fuzz-test)のファジングの構成と比べて、実行速度が大幅に遅いことが分かります。ファジングがパーシステントモードで動いていないためです。性能が低めの VM では、通常、パーシステントモードなしだと 1 秒あたり 1k 回未満、ありだと約 25k 回の実行になります。 

上の例は、libFuzzer のハーネスをやめたため、もうパーシステントモードを使っていません。ただし、次の節で示すように、パーシステントモードをもう一度有効にできます。

### ファザーの最適化: パーシステントモードと共有メモリを有効にする {#optimizing-the-fuzzer-enable-persistent-mode}

パーシステントモードを有効にすると、ファジングの性能が 10〜20 倍に上がります(パーシステントモードが速い理由は、上のヒントを参照)。なお、最初に使ったバージョンは、libFuzzer 形式のハーネスを使っているため、すでにパーシステントモードで動いています。 
ファジングのキャンペーンでは、共有メモリも有効にします。これは、テストケースが、標準入力や引数、ファイルからの読み込みではなく、共有メモリを通じて、ファザーから SUT に渡されることを意味します。

AFL++ ですでに `LLVMFuzzerTestOneInput` を使っているなら、この節は関係ありません。この節は、まだパーシステントモードで動いていないファザーを改善したい場合に関係します。`afl-fuzz` のログ出力で「Persistent mode binary detected」を探すと、すでにパーシステントモードを使っているかを確かめられます。

パーシステントモードと共有メモリを有効にするには、数行のコードを足す必要があります。

1. main 関数が定義されているファイルの include の下に、`__AFL_FUZZ_INIT();` を追加します。
2. 標準入力から読み込む代わりに、AFL++ が埋める変数を定義します(入力のバッファがファイルなど別のところから来る場合は、この例を調整する必要があります)。
    ```C++
    #ifdef __AFL_COMPILER
        unsigned char *input_buf;
        __AFL_INIT();
        input_buf = __AFL_FUZZ_TESTCASE_BUF;
    #else
        char input_buf[MAX_BUF_SIZE];

        if (fgets(input_buf, MAX_BUF_SIZE, stdin) == NULL) {
            return 1;
        }
    #endif
    ```
3. ターゲットのコードを while ループの中に置き、最大の繰り返し回数を 1k から 10k の間に設定します。このパラメータは、AFL++ がメモリリークやグローバルな状態に関する問題に対処するために、プロセスを再起動するまでのサイクル数を決めます。ファジングのターゲットが不安定(たとえば、メモリをリークする、グローバルな状態を保つ)な場合は、小さい値を選びます。プログラムが安定していると考えられる場合(たとえば、Rust のライブラリをファジングする場合)は、大きい値を選びます。
なお、値を `1000k` や `INT_MAX` のような値まで増やしても、再起動の時間が十分に短ければ、性能がそれほど上がることはまずありません。
    ```C++
    while (__AFL_LOOP(1000)) {
        size_t len = strlen(input_buf);
        check_buf(input_buf, len);
    }
    ```

{{< hint info >}}
ヒント: 安定性は、ターゲットのエッジのうち、「安定」とみなされるものの割合で数値化されます。同一の入力を繰り返し送ったとき、データが毎回ターゲットの同じ経路をたどるなら、安定性は 100% と判定されます。

AFL++ の安定性についての詳細は[こちら](https://github.com/AFLplusplus/AFLplusplus/blob/ad0d0c77fb313e6edfee111fecf2bcd16d8f915e/docs/FAQ.md#user-content-why-is-my-stability-below-100percent)を、[安定性を改善する](https://github.com/AFLplusplus/AFLplusplus/blob/stable/docs/best_practices.md#improving-stability)方法についてはこちらを読んでください。
{{< /hint >}}


これらの変更を加えてファジングすると、ファザーの 1 秒あたりの実行回数が上がることに気づくでしょう。性能が上がる理由は、テスト入力が標準入力ではなく、共有メモリから来るようになったからです。参考のために、パーシステントモードを有効にしたプログラムを示します。



{{< customFigure "main_stdin_persist.cc: main_stdin.cc にパーシステントモードを有効にしたバージョン" >}}
```C++
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

__AFL_FUZZ_INIT();

#define MAX_BUF_SIZE 100

void check_buf(char *buf, size_t buf_len) {
    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                abort();
            }
        }
    }
}

int main() {
#ifdef __AFL_COMPILER
    unsigned char *input_buf;
    __AFL_INIT();
    input_buf = __AFL_FUZZ_TESTCASE_BUF;
#else
    char input_buf[MAX_BUF_SIZE];

    if (fgets(input_buf, MAX_BUF_SIZE, stdin) == NULL) {
        return 1;
    }
#endif

    while (__AFL_LOOP(1000)) {
        size_t len = strlen(input_buf);
        check_buf(input_buf, len);
    }
    return 0;
}
```
{{< /customFigure >}}


パーシステントモードの使い方について詳しくは、[こちら](https://github.com/AFLplusplus/AFLplusplus/blob/stable/instrumentation/README.persistent_mode.md)にあります。


## ファイル入力のファジング {#file-input-fuzzing}

AFL++ は、ディスクからファイルを読み込むプログラムのファジングにも対応しています。まず、これまでの例を、コマンドラインで指定したファイルを入力として使うように書き換えます。

{{< customFigure "main_file.cc: ファイルで入力を受け取るプログラム" >}}
```C++
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_BUF_SIZE 100

void check_buf(char *buf, size_t buf_len) {
    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                abort();
            }
        }
    }
}
int main(int argc, char *argv[]) {
    char input_buf[MAX_BUF_SIZE];

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <filename>\n", argv[0]);
        return 1;
    }

    FILE *file = fopen(argv[1], "r");
    if (file == NULL) {
        return 1;
    }

    if (fgets(input_buf, MAX_BUF_SIZE, file) == NULL) {
        if (!feof(file)) { // Check for reading error and not end of file
            fclose(file);
            return 1;
        }
    }

    fclose(file);

    size_t len = strlen(input_buf);
    check_buf(input_buf, len);
    return 0;
}
```
{{< /customFigure >}}


いつもどおり、AFL++ のコンパイラのラッパーを使って、計装済みのバイナリを作ります。


```shell
./afl++ <host/docker> afl-clang-fast++ -O2 main_file.c -o fuzz_file
```


次に、ファジングを始めます。標準入力ではなくファイル入力をファジングしたい場合は、コマンドラインに `@@` を指定して、[ディスクに書き込まれた](https://github.com/AFLplusplus/AFLplusplus/blob/358cd1b062e58ce1d5c8efeef4789a5aca7ac5a9/src/afl-fuzz.c#L2113-L2123)ファイルのパスを AFL++ がどこに置くかを示す必要があります。


```shell
./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz_file @@
```


ファザーは、すぐにクラッシュを見つけるはずです。ファザーを最適化する方法は、[パーシステントモードを有効にする](#optimizing-the-fuzzer-enable-persistent-mode)を参照してください。入力にファイルを使い続けたい場合は、メモリ領域からファイルディスクリプタを作る [`fmemopen`](https://man.archlinux.org/man/fmemopen.3) を使うとよいでしょう。
<!-- TODO Maybe link an example. Consider adapting example to use fmemopen -->



## 引数のファジング {#argument-fuzzing}

まず、これまでの例を、引数から直接入力を受け取るように書き換えます。引数をファジングするには、`main` 関数を含むヘッダファイル [`argv-fuzz-inl.h`](https://github.com/AFLplusplus/AFLplusplus/blob/stable/utils/argv_fuzzing/argv-fuzz-inl.h) を include し、`main` の先頭に `AFL_INIT_ARGV()` を追加する必要があります。


{{< customFigure "main_arg.cc: コマンドライン引数で入力を受け取るプログラム" >}}
```C++
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#ifdef __AFL_COMPILER
#include "argv-fuzz-inl.h"
#endif

void check_buf(char *buf, size_t buf_len) {
    if(buf_len > 0 && buf[0] == 'a') {
        if(buf_len > 1 && buf[1] == 'b') {
            if(buf_len > 2 && buf[2] == 'c') {
                abort();
            }
        }
    }
}

int main(int argc, char *argv[]) {
#ifdef __AFL_COMPILER
    AFL_INIT_ARGV();
#endif

    if (argc < 2) {
        fprintf(stderr, "Usage: %s <input_string>\n", argv[0]);
        return 1;
    }

    char *input_buf = argv[1];
    size_t len = strlen(input_buf);

    check_buf(input_buf, len);

    return 0;
}
```
{{< /customFigure >}}


上のプログラムをコンパイルする前に、必要なヘッダをダウンロードする必要があります。


```shell
curl -O https://raw.githubusercontent.com/AFLplusplus/AFLplusplus/stable/utils/argv_fuzzing/argv-fuzz-inl.h
```

これで、計装済みのバイナリをコンパイルして、いつもどおりファジングを始められます。


```shell
./afl++ <host/docker> afl-clang-fast++ -O2 main_arg.c -o fuzz_arg
./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz_arg
```


バイナリ名に設定される最初の引数を制御したい場合は、`AFL_INIT_ARGV` の代わりに `AFL_INIT_SET0("prog_name")` を使います。

ファザーは、すぐにクラッシュを見つけるはずです。このファザーを速くする方法は、[パーシステントモードを有効にする](#optimizing-the-fuzzer-enable-persistent-mode)を参照し、代わりにマクロ `AFL_INIT_ARGV_PERSISTENT(buf)` と `AFL_INIT_SET0_PERSISTENT("prog_name", buf)` を使います。
<!-- TODO Maybe link an example -->


{{< hint info >}}
ヒント: 引数のファザーはどう動くのか?

ヘッダファイル [`argv-fuzz-inl.h`](https://github.com/AFLplusplus/AFLplusplus/blob/stable/utils/argv_fuzzing/argv-fuzz-inl.h) は、ファザーの入力を使って argv と argc を設定する、2 つのマクロを定義しています。
* マクロ `AFL_INIT_ARGV()` は、コマンドラインからプログラムに渡された引数で、`argv` 配列を初期化します。そのあと、標準入力から引数を読み込み、argv 配列に入れます。配列は 2 つの `NULL` 文字で終端され、空のパラメータは、単独の `0x02` 文字としてエンコードされます。
* マクロ `AFL_INIT_SET0(_p)` は `AFL_INIT_ARGV()` に似ていますが、`argv` 配列の最初の要素に、渡された値も設定します。このマクロは、プログラムの名前を `argv` 配列に残したいときに役立ちます。

どちらのマクロも、関数 `afl_init_argv` を使っています。この関数は、([`read`](https://man.archlinux.org/man/read.3p) 関数を使って)標準入力からコマンドラインを読み込み、引数に分割する役割を担っています。そして、できあがった文字列の配列を静的なバッファに保存し、そのバッファへのポインタを返します。また、`argc` 引数が指す値を、読み込んだ引数の数に設定します。

パーシステントモードを使う場合は、入力を標準入力から読み込まないため、実装が少し異なります。
{{< /hint >}}

### 追加のリソース {#additional-resources}

* **[cURL のファジング。](https://blog.trailofbits.com/2023/02/14/curl-audit-fuzzing-libcurl-command-line-interface/)** Trail of Bits では、引数のファジングを使って cURL のファジングに成功しました。
* **[Sudo の脆弱性の解説。](https://www.youtube.com/playlist?list=PLhixgUqwRTjy0gMuT4C3bmjeZjuNQyqdx)** LiveOverflow が、sudo のバイナリにある [CVE-2021-3156](https://www.cve.org/CVERecord?id=CVE-2021-3156) のバグを再発見する方法についての、YouTube の再生リストを作りました。この章の後半で、この手法をさらに詳しく説明します。
* **[libpng のバグの再発見。](https://www.youtube.com/watch?v=PJLWlmp8CDM)** LiveOverflow が、[CVE-2023-4863](https://www.cve.org/CVERecord?id=CVE-2023-4863) を再発見しようとした試みと、そこで直面した障害を示す YouTube の動画を作りました。

## マルチコアファジング {#multi-core-fuzzing}

AFL++ は、複数のコアでのファジングに対応しています。これには 2 つの利点があります。

* 1 秒あたりの実行回数が増える。通常、使える物理コアの数に比例して増えます。
* 非対称なファジング。少しずつ違う複数のファジングのジョブを起動する、という意味です。たとえば、あるジョブは AddressSanitizer を使い、ほかは使わない、という具合です。こうすれば、AddressSanitizer による性能の低下は、1 つのジョブにしか影響しません。サニタイザなしのジョブが見つけた興味深いテストケースは、見つかったときに、ASan を使って実行されるので、メモリ破壊のバグを検出できる可能性があります。通常、ASan のジョブは 1 つだけにします。

複数のジョブを管理するために、bash のジョブ制御を使います。bash か、互換性のあるシェルを使ってください。まず、メインのファジングのインスタンスを起動します。複数の出力を追うのは効率が悪いので、標準出力ではなくファイルにログを出力します。ディレクトリ `state/` が存在しないことを確認してください。 

`&` に注意してください。これにより、AFL++ はバックグラウンドで動き、現在のシェルを使い続けられます。標準出力とエラー出力を、`1>primary.log` と `2>primary.error` でファイルにリダイレクトして、出力が端末に表示されないようにします。


```shell
./afl++ <host/docker> afl-fuzz -M primary -i seeds -o state -- ./fuzz 1>primary.log 2>primary.error &
```
<!-- TODO tooltips -->


これで、空いているコアの数だけ、セカンダリのジョブを起動できます。


```shell
./afl++ <host/docker> afl-fuzz -S secondary01 -i seeds -o state -- ./fuzz 1>secondary01.log 2>secondary01.error &
./afl++ <host/docker> afl-fuzz -S secondary02 -i seeds -o state -- ./fuzz 1>secondary02.log 2>secondary02.error &
```
<!-- TODO tooltips -->


AFL++ は、ジョブごとに、`state/` にサブディレクトリを作ります。ファジングの進み具合は、次の 2 つのコマンドで確認できます。

* `jobs`: 現在動いているコマンドをすべて一覧にします。動いていないジョブがある場合は、`.log` と `.error` のファイルを確認してください。
* `./afl++ <host/docker> afl-whatsup state/`: 現在動いているインスタンスと、その実行速度、結果を一覧にするには、これを実行します。

次のコマンドを実行して、1 秒ごとに更新を表示することをお勧めします。


```shell
./afl++ <host/docker> watch -n1 --color afl-whatsup state/
```


このコマンドの出力を次に示します。

{{< customFigure "afl-whatsup コマンドの出力例" >}}
```text
/usr/bin/afl-whatsup status check tool for afl-fuzz by Michal Zalewski

Individual fuzzers
==================

>>> ./fuzz instance: primary (0 days, 0 hrs) fuzzer PID: 706733 <<<

  last_find       : 3 minutes, 51 seconds
  last_crash      : 3 minutes, 51 seconds
  last_hang       : none seen yet
  cycles_wo_finds : 5412
  cpu usage 18.7%, memory usage 0.7%
  cycles 5433, lifetime speed 19040 execs/sec, items 0/3 (0%)
  pending 0/0, coverage 40.00%, crashes saved 1 (!)

>>> ./fuzz instance: secondary01 (0 days, 0 hrs) fuzzer PID: 706910 <<<

  last_find       : 3 minutes, 48 seconds
  last_crash      : 3 minutes, 48 seconds
  last_hang       : none seen yet
  cycles_wo_finds : 1961
  cpu usage 18.3%, memory usage 0.7%
  cycles 1963, lifetime speed 18681 execs/sec, items 1/3 (33%)
  pending 0/0, coverage 40.00%, crashes saved 1 (!)

>>> ./fuzz instance: secondary02 (0 days, 0 hrs) fuzzer PID: 706913 <<<

  last_find       : 3 minutes, 48 seconds
  last_crash      : 3 minutes, 48 seconds
  last_hang       : none seen yet
  cycles_wo_finds : 1370
  cpu usage 18.3%, memory usage 0.7%
  cycles 1372, lifetime speed 18017 execs/sec, items 2/3 (66%)
  pending 0/0, coverage 40.00%, crashes saved 1 (!)

Summary stats
=============

       Fuzzers alive : 3
      Total run time : 9 minutes, 0 seconds
         Total execs : 10 millions
    Cumulative speed : 55738 execs/sec
       Average speed : 18579 execs/sec
       Pending items : 0 faves, 0 total
  Pending per fuzzer : 0 faves, 0 total (on average)
       Crashes saved : 3
         Hangs saved : 0
Cycles without finds : 5412/1961/1370
  Time without finds : 3 minutes, 48 seconds
```
{{< /customFigure >}}


ファザーのインスタンスが動いている間、それらは互いに状態とテストケースを共有します。

ファザーを止めるには、次を実行して、穏やかに終了させます。


```shell
kill $(jobs -p)
```


詳しい情報や応用的な使い方は、[こちら](https://aflplus.plus/docs/parallel_fuzzing/)と[こちら](https://aflplus.plus/docs/fuzzing_in_depth/#c-using-multiple-cores)にあります。


## CMPLOG {#cmplog}

CMPLOG/RedQueen は、あらゆるファザーの中で、利用できる最良の、パスの制約を解く仕組みです。
これを有効にするには、ファジングのターゲットを、そのために計装する必要があります。
ファジングのターゲットをビルドする前に、環境変数を設定します。

```shell
./afl++ <host/docker> AFL_LLVM_CMPLOG=1 make
```

ハーネスのコンパイルとリンクに、特別な操作は必要ありません。

CMPLOG で計装したファジングのターゲットでファザーのインスタンスを動かすには、コマンドライン引数に `-c0` を追加します。

```shell
./afl++ <host/docker> afl-fuzz -c0 -S cmplog -i seeds -o state -- ./fuzz 1>cmplog.log 2>cmplog.error &
```


## AddressSanitizer {#addresssanitizer}

ASan は、そのままでは気づかないメモリのエラーを検出するのに役立ちます。たとえば、次のヒープバッファオーバーフローは、ASan なしでは、たいてい検出できません。 

{{< customFigure "main_asan.cc: ASan で検出できるバグの例。プログラムは 9 行目で範囲外に書き込みます。1 バイトしか確保していないのに、少なくとも 2 バイトを書き込んでいるからです。" >}}
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

ASan の一般的な紹介は、[AddressSanitizer]({{% relref "/docs/fuzzing/techniques/03-asan" %}})を参照してください。

AFL++ で AddressSanitizer を有効にするには、環境変数 `AFL_USE_ASAN=1` を設定します。これは ASan を有効にするだけでなく、ASan と互換性のない[ソースの fortification](https://github.com/AFLplusplus/AFLplusplus/blob/ef706ad668b36e65d24f352f5bcee22957f5f1cc/src/afl-cc.c#L1182) も無効にします。

たとえば、ASan を使って main_asan.cc のバグを見つけるには、まず、対応するフラグを付けてコンパイルします。

```shell
./afl++ <host/docker> AFL_USE_ASAN=1 afl-clang-fast++ -DNO_MAIN=1 -O2 -fsanitize=fuzzer harness.cc main_asan.cc -o fuzz
```

ファザーを動かすと、上のヒープバッファオーバーフローが、ファザーによって見つかります。`-m` フラグで設定できるメモリ制限は、ASan では使えません。ASan が、20TB という膨大な仮想メモリを割り当てるためで、これはどんな妥当なメモリ制限も超えます。


## 実際の事例 {#real-world-examples}
### libpng {#libpng}

静的ライブラリを作る C のプロジェクトをファジングする場合は、次の手順に従えます。

1. プロジェクトのコードベースの `INSTALL` ファイル(またはほかの適切なドキュメント)を読み、静的ライブラリの作り方を調べます。
2. コンパイラを AFL++ のコンパイラのラッパー(例: `afl-clang-fast++`)に設定し、コンパイル時に必要なフラグをコンパイラに渡します。
3. 静的ライブラリをビルドし、環境変数 `AFL_USE_ASAN=1` を設定し、フラグ `-fsanitize=fuzzer-no-link `を C コンパイラに渡します。これにより、ファジングエンジンをリンクせずに、ファジング関連の計装が有効になります。`main` シンボルを含むランタイムは、あとで `-fsanitize=fuzzer` フラグを使うときにリンクされます。このビルドの手順で、静的ライブラリができます。これを `$static_library` と呼ぶことにします。環境変数により、ASan がメモリ破壊を検出できるようになります。
4. 手順 3 でコンパイルした静的ライブラリを見つけ、次を呼び出します: `./afl++ <host/docker> AFL_USE_ASAN=1 afl-clang-fast++ -fsanitize=fuzzer $static_library harness.cc -o fuzz`。
5. `./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz` を呼び出して、ファジングを始められます。

有名な libpng ライブラリで、これらの手順を見ていきましょう。まず、ソースコードを取得します。


```shell
curl -L -O https://downloads.sourceforge.net/project/libpng/libpng16/1.6.37/libpng-1.6.37.tar.xz
tar xf libpng-1.6.37.tar.xz
cd libpng-1.6.37/
```


現在のディレクトリに `./afl++` スクリプトがあることを確認するか、下のパスをそれに合わせて調整してください。

libpng をコンパイルする前に、その依存関係をインストールする必要があります。

```shell
apt install zlib1g-dev
```

次に、libFuzzer をリンクせずに、libpng を静的ライブラリとして設定し、コンパイルします。

Docker を使う場合は、プロジェクトのビルドに必要な依存関係が、`./afl++` スクリプトで指定した Docker イメージで、すべて使えるようになっている必要があります。つまり、[Dockerfile を作って](https://docs.docker.com/engine/reference/builder/)、AFL++ のコンテナをもとにしたコンテナを、自分でビルドする必要があるかもしれません。


```shell
export CC=afl-clang-fast CFLAGS=-fsanitize=fuzzer-no-link # Set C compiler and its flags for fuzzing
export CXX=afl-clang-fast++ CXXFLAGS="$CFLAGS" # Set C++ compiler and use C flags
./afl++ <host/docker> CC="$CC" CXX="$CXX" CFLAGS="$CFLAGS" CXXFLAGS="$CFLAGS" AFL_USE_ASAN=1 ./configure --enable-shared=no # Configure to compile a static library
./afl++ <host/docker> AFL_USE_ASAN=1 make # Run compilation
```


既定では、設定スクリプトは最適化レベルを `-O2` にします。これは、[ファジングテストのコンパイル](#compile-a-fuzz-test)の節で勧めているレベルです。

次に、GitHub からハーネスをダウンロードします。通常は、ハーネスを自分で書く必要があります。ただし、この例では、既存のもので十分です。


```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/f8e5fa92b0e37ab597616f554bee254157998227/contrib/oss-fuzz/libpng_read_fuzzer.cc
```


最後に、計装した libpng、ハーネス、libFuzzer のランタイムをリンクします。


```shell
./afl++ <host/docker> AFL_USE_ASAN=1 $CXX -fsanitize=fuzzer libpng_read_fuzzer.cc .libs/libpng16.a -lz -o fuzz
```


キャンペーンを始める前に、シードを用意する必要があります。AFL++ は、空のシードの集合から始められないためです。小さな PNG ファイルの例をダウンロードして用意します。


```shell
mkdir seeds/
curl -o seeds/input.png https://raw.githubusercontent.com/glennrp/libpng/acfd50ae0ba3198ad734e5d4dec2b05341e50924/contrib/pngsuite/iftp1n3p08.png
```


PNG 形式の[辞書]({{% relref 02-dictionary %}}g)もダウンロードして、ファザーをよりうまく誘導します。辞書は、PNG が使うマジックバイトなど、ファイル形式についての最初の手がかりを、ファザーに与えます。


```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/2fff013a6935967960a5ae626fc21432807933dd/contrib/oss-fuzz/png.dict
```


次を実行して、ファジングのキャンペーンを始められます。


```shell
./afl++ <host/docker> afl-fuzz -i seeds -o out -x png.dict -- ./fuzz
```

### CMake ベースのプロジェクト {#cmake-based-project}

[導入]({{% relref "fuzzing#introduction-to-fuzzers" %}})で取り上げたプログラムを、CMake でビルドするとします。`main.cc` と `harness.cc` をビルドし、そのターゲットを AFL++ とリンクする CMake のターゲットを追加します。main 関数は `NO_MAIN` フラグで除外している点に注意してください。そうしないと、プログラムに main 関数が 2 つできてしまいます。


{{< customFigure "CMake の例" >}}
```cmake
project(BuggyProgram)
cmake_minimum_required(VERSION 3.0)

add_executable(buggy_program main.cc)

add_executable(fuzz main.cc harness.cc)
target_compile_definitions(fuzz PRIVATE NO_MAIN=1)
target_compile_options(fuzz PRIVATE -O2 -fsanitize=fuzzer-no-link)
target_link_libraries(fuzz -fsanitize=fuzzer)
```
{{< /customFigure >}}

計装していないバイナリは、次のコマンドでビルドできます。


```shell
./afl++ <host/docker> cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ .
./afl++ <host/docker> cmake --build . --target buggy_program
```


ファザーは、fuzz のターゲットを選び、コンパイラを変えてビルドできます。


```shell
./afl++ <host/docker> cmake -DCMAKE_C_COMPILER=afl-clang-fast -DCMAKE_CXX_COMPILER=afl-clang-fast++ .
./afl++ <host/docker> cmake --build . --target fuzz
```


次を実行して、ファジングのキャンペーンを始められます。


```shell
./afl++ <host/docker> afl-fuzz -i seeds -o out -- ./fuzz
```


ほかのビルドシステムの例は、[こちら](https://aflplus.plus/docs/fuzzing_in_depth/#e-instrumenting-the-target)にあります。

## 追加のリソース {#additional-resources}

* **[AFL++: Combining Incremental Steps of Fuzzing Research.](https://www.usenix.org/system/files/woot20-paper-fioraldi.pdf)** AFL++ についての論文。
* **[Fuzzing in Depth.](https://aflplus.plus/docs/fuzzing_in_depth/)** AFL++ チームによる、応用的なドキュメント。
* **[AFL++ Under The Hood.](https://blog.ritsec.club/posts/afl-under-hood/)** AFL++ の内部についてのブログ記事。
