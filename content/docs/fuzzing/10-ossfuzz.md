---
title: "OSS-Fuzz"
slug: oss-fuzz
weight: 6
---


# OSS-Fuzz

[OSS-Fuzz](https://google.github.io/oss-fuzz/) は、Google が開発しているオープンソースのプロジェクトです。継続的なファズテストのための分散インフラストラクチャを無償で提供することで、オープンソースソフトウェアのセキュリティと安定性を高めることを目指しています。OSS-Fuzz のような既存のフレームワークを使うと、ハーネスを手作業で実行するよりも多くの利点があります。作業が効率化され、変更も簡単になります。OSS-Fuzz に受け入れられるのは一部のプロジェクトだけですが、中核がオープンソースなので、誰でも自分の OSS-Fuzz のインスタンスをホストし、非公開のプロジェクトに使えます。


この章では、プロジェクトの開発者向けに、OSS-Fuzz を活用する方法を説明します。自分の非公開のインスタンスでプロジェクトをファジングする方法と、ファジングの計算を Google に任せる方法です。また、セキュリティ研究者向けには、既存のプロジェクトで単一のハーネスを実行する方法、ハーネスを拡張する方法、個別のクラッシュを再現する方法を説明します。


## OSS-Fuzz のプロジェクトの構成要素

OSS-Fuzz は、ハーネスのビルドと起動、およびカバレッジの計算のための、簡単な CLI フレームワークを提供します。これにより、ハーネスをローカルで作成してテストする作業が効率化されます。また、OSS-Fuzz はサービスとしても使え、カバレッジ情報などのファジングの出力から生成された静的な Web ページをホストします。


すべての構成要素がオープンソースというわけではありませんが、このプラットフォームの能力を示すために、公開されている OSS-Fuzz のツールを一覧にまとめました。自分の作業にどう活用できるかについても、コメントを添えています。


* [バグトラッカー](https://issues.oss-fuzz.com/issues?q=status:open)でできること:
   * 特定のプロジェクトのバグを確認する。（バグは、最初はメンテナにだけ見えますが、後で[公開されます](https://google.github.io/oss-fuzz/getting-started/bug-disclosure-guidelines/)。）
   * 新しい issue を作成し、コメントする。
   * 公開されている issue のやり取りを読む。
   * 自分のプロジェクトで見たバグに似た、公開済みのバグを**すべてのプロジェクト**から探し、問題の理解に役立てる。（OSS-Fuzz の公開 issue すべてから、任意のフレーズを検索できます。）
* [ビルドステータスのシステム](https://oss-fuzz-build-logs.storage.googleapis.com/index.html)は、すべてが正しく動いているか、そうでなければ問題がどのくらい続いているかを追跡するのに役立ちます。具体的には次のとおりです。
   * 登録されているすべてのプロジェクトのビルドステータス。
   * 最後にビルドが成功した日付。
* [Fuzz Introspector](https://oss-fuzz-introspector.storage.googleapis.com/index.html) は、OSS-Fuzz に登録されたプロジェクトのカバレッジを、カバレッジのデータとヒット頻度を含めて表示します。ファザーの性能を理解し、妨げになっているものを特定できます。
   * このツールについて詳しくは、説明と例が載っている[このケーススタディ](https://github.com/ossf/fuzz-introspector/blob/main/doc/CaseStudies.md)を読んでください。

## CLI: 単一のハーネスを実行する

OSS-Fuzz を使うために、プラットフォーム全体をホストする必要はありません。代わりに、OSS-Fuzz は、その機能に簡単にアクセスできる便利なヘルパースクリプトを提供しています。たとえば、単一のファジング用ハーネスを実行して、特定のプロジェクトの潜在的な脆弱性を見つけたり、以前にクラッシュを起こした入力でハーネスを実行したりできます。ヘルパースクリプトは、新しいファジング用ハーネスのテストや、古いハーネスを別の設定で実行することにも使えます。クラッシュする入力や別のコンパイラを使う場合などが含まれます。


まず、メインの oss-fuzz リポジトリをクローンし、次のように `infra/helper.py` スクリプトを使って、ヘルパースクリプトで可能な操作を確認します。


```sh
$ git clone https://github.com/google/oss-fuzz
$ cd oss-fuzz
$ python3 infra/helper.py --help
```


ハーネスを実行する手順は次のとおりです。
* まず、`build_image` 引数にプロジェクト名を指定して、ヘルパースクリプトを実行します: `build_image --pull <project-name>`
* 次に、`build_fuzzers` コマンドに、選んだ[サニタイザ](https://google.github.io/oss-fuzz/reference/glossary/#sanitizers)とプロジェクト名を続けて、ヘルパースクリプトをもう一度実行します: `build_fuzzers --sanitizer=<sanitizers-list> <project-name>`。[AddressSanitizer](https://appsec.guide/docs/fuzzing/techniques/asan/) と [LeakSanitizer](https://github.com/google/sanitizers/wiki/AddressSanitizerLeakSanitizer) には、`--sanitizer=address` を使います。C や C++ 以外の言語では、サニタイザのサポートが限られることがあります。たとえば、[Rust がサポートするのは、エンジンとして libfuzzer を使った AddressSanitizer だけ](https://google.github.io/oss-fuzz/getting-started/new-project-guide/rust-lang/#projectyaml)です。
* 最後に、ファザーを実行するには、`run_fuzzer` コマンドに、プロジェクト名とハーネス名、必要ならファザーの引数を続けて使います: `run_fuzzer <project-name> <harness-name> [<fuzzer-args>]`


手順を飛ばしても、ヘルパースクリプトが、抜けた手順を自動で実行するはずです。


`build_fuzzers` コマンドは、ファジングのターゲットを `/build/out/<project-name>/` ディレクトリにビルドします。このディレクトリには、llvm-symbolizer、ハーネス、辞書、コーパスなどが入ります。クラッシュしたファイルもここに保存されます。


{{< hint info >}}
**プロのヒント:** 新しいハーネスに取り組むときは、ソースコードからコードをコピーしたり、手作業で取得したりするのは避けてください。代わりに、Dockerfile（または他のハーネス）を見て、コードが Docker イメージにどうコピーされるかを理解してください。既存のプロジェクトの設定に、コードを取得する処理が含まれている可能性が高く、その場合、ヘルパースクリプトを使えば、最新版がすでに用意されています。
{{< /hint >}}


## カバレッジの分析 {#coverage-analysis}

OSS-Fuzz は、プロジェクトのコードカバレッジの Web ページ形式のレポートも生成できます。


* まず、[gsutil をインストール](https://cloud.google.com/storage/docs/gsutil_install)します。gcloud の初期化（[gcloud init](https://cloud.google.com/sdk/gcloud/reference/init)）は省略できます。 
* 次に、Coverage Sanitizer でハーネスをビルドします（`python3 infra/helper.py --sanitizer=coverage <project-name>`）。 
* 最後に、カバレッジ分析を実行し、ページをホストします。ローカルのコーパスを使うこと（`--no-corpus-download`）もできます。次のコマンドは、レポートを生成してローカルでホストし、ローカルの Web アドレスをコンソールに表示します。
   * `python3 infra/helper.py coverage <project-name>`


詳しい手順は、[OSS-Fuzz の公式ドキュメント](https://google.github.io/oss-fuzz/advanced-topics/code-coverage/)を参照してください。

### 例

OSS-Fuzz のスクリプトでプロジェクトをファジングする方法を示すために、OSS-Fuzz に登録されている簡単なプロジェクト、irssi を見てみましょう。ここでは、docker コマンドでコンテナを実行できることを前提とします。


まず、OSS-Fuzz のリポジトリをクローンします。


```sh
git clone https://github.com/google/oss-fuzz
cd oss-fuzz
```


次に、oss-fuzz のメインディレクトリで次のコマンドを実行して、ファジング用ハーネスをビルドし、実行します。


```sh
python3 infra/helper.py build_image --pull irssi
python3 infra/helper.py build_fuzzers --sanitizer=address irssi
python3 infra/helper.py run_fuzzer irssi irssi-fuzz
```


irssi のファジング用ハーネスの中で使われている libFuzzer フレームワークから、次のような出力が出るはずです。


```sh
$ python3 infra/helper.py run_fuzzer irssi irssi-fuzz
INFO:__main__:Running: docker run --rm --privileged --shm-size=2g --platform linux/amd64 -i -e FUZZING_ENGINE=libfuzzer -e SANITIZER=address -e RUN_FUZZER_MODE=interactive -e HELPER=True -v /private/tmp/oss-fuzz/build/out/irssi:/out -t gcr.io/oss-fuzz-base/base-runner run_fuzzer irssi-fuzz.
Using seed corpus: irssi-fuzz_seed_corpus.zip
/out/irssi-fuzz -rss_limit_mb=2560 -timeout=25 /tmp/irssi-fuzz_corpus -max_len=2048 < /dev/null
INFO: Running with entropic power schedule (0xFF, 100).
INFO: Seed: 1531341664
INFO: Loaded 1 modules   (95687 inline 8-bit counters): 95687 [0x1096c80, 0x10ae247),
INFO: Loaded 1 PC tables (95687 PCs): 95687 [0x10ae248,0x1223eb8),
INFO:      719 files found in /tmp/irssi-fuzz_corpus
INFO: seed corpus: files: 719 min: 1b max: 170106b total: 367969b rss: 48Mb
#720        INITED cov: 409 ft: 1738 corp: 640/163Kb exec/s: 0 rss: 62Mb
#762        REDUCE cov: 409 ft: 1738 corp: 640/163Kb lim: 2048 exec/s: 0 rss: 63Mb L: 236/2048 MS: 2 ShuffleBytes-EraseBytes-
#818        REDUCE cov: 409 ft: 1738 corp: 640/163Kb lim: 2048 exec/s: 0 rss: 63Mb L: 188/2048 MS: 1 EraseBytes-
#880        NEW    cov: 409 ft: 1739 corp: 641/164Kb lim: 2048 exec/s: 0 rss: 63Mb L: 116/2048 MS: 2 CrossOver-InsertRepeatedBytes-
#912        REDUCE cov: 409 ft: 1739 corp: 641/163Kb lim: 2048 exec/s: 0 rss: 63Mb L: 146/2048 MS: 2 EraseBytes-CopyPart-
#933        NEW    cov: 412 ft: 1742 corp: 642/164Kb lim: 2048 exec/s: 0 rss: 63Mb L: 13/2048 MS: 1 ChangeBit-
(...)
```

## OSS-Fuzz の Docker イメージ

ハーネスは、ビルドディレクトリをボリュームとしてマウントした Docker コンテナの中で、ビルドされ、実行されます。実行用のイメージは、すべてのプロジェクトで共通です。各プロジェクトは、それぞれ専用の Docker イメージでビルドされ、そのイメージは、この[`base image`](https://github.com/google/oss-fuzz/blob/master/infra/base-images/base-image/Dockerfile)を間接的な土台とする必要があります。


{{< hint info >}}
**プロのヒント:** ベースイメージは、[特定の Ubuntu のバージョン](https://github.com/google/oss-fuzz/blob/8ae6ed7a343954defc8ff4c688d761518d7fcb5c/infra/base-images/base-image/Dockerfile#L19)を使っています。また、特定のコンパイラのバージョンが `base_clang` イメージから引き継がれますが、メンテナはプロジェクトの Docker イメージに何でもインストールできます（プロジェクトを登録する場合は、承認が必要なことがあります）。
{{< /hint >}}


ファジングのターゲットは、そのプロジェクト専用の Docker イメージでビルドされます。（プロジェクトのメンテナは、依存関係のインストールとソースコードの取得のための Dockerfile を用意する必要があります。） 


{{< hint info >}}
Docker イメージは、OSS-Fuzz が提供するイメージを土台にする必要があります。可能であれば、そのイメージが提供するコンパイラを使うのが最善です。
{{< /hint >}}

次に、イメージの並びを示します。後の項目は、前の項目の上に作られます。
* [`base_image`](https://github.com/google/oss-fuzz/blob/master/infra/base-images/base-image): 特定のバージョンの Ubuntu
* [`base_clang`](https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-clang): clang をコンパイルする。clang は、**ほとんど**のプロジェクトのコンパイルに使われる。`base_image` が土台
* [`base_builder`](https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-builder): いくつかのビルドの依存関係。`base_clang` が土台
   * C と C++ 以外の言語向けには、[`base_builder_go`](https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-builder-go) のようなイメージがあります。完全な一覧は、[/oss-fuzz/infra/base-images/](https://github.com/google/oss-fuzz/tree/master/infra/base-images) ディレクトリで確認してください。
* ファジングのターゲットを**ビルド**するための、自分のプロジェクトの Docker イメージ（`base_builder/base_builder_*` が土台）: これは自分で作る必要があります。


次のイメージは、ハーネスの実行に別々に使われ、すべてのプロジェクトに共通です。
* [`base_runner`](https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-runner)（`base_clang` が土台）
* [`base_runner_debug`](https://github.com/google/oss-fuzz/tree/master/infra/base-images/base-runner-debug)（デバッグ用のツール付き。`base_runner` が土台）


## 自分のプロジェクトを OSS-Fuzz で使う

オープンソースのプロジェクトに取り組んでいるなら、OSS-Fuzz に登録して、Google のインフラストラクチャで継続的に無償でファジングしてもらうことをお勧めします。OSS-Fuzz に受け入れられるかどうかは、最終的には OSS-Fuzz チームの判断であることに注意してください。OSS-Fuzz は、新しいプロジェクトの提案ごとに[重要度スコア](https://github.com/ossf/criticality_score)（[この例](https://github.com/google/oss-fuzz/pull/11444#issuecomment-1875907472)を参照）を付け、この値でプロジェクトを受け入れるかを判断します。ただし、自分の OSS-Fuzz のコピーにプロジェクトを追加することはできます。自分のプロジェクトだけをファジングすれば、手順を効率化できるかもしれません。簡単なプロジェクトを OSS-Fuzz でファジングする方法を、以下に説明します。
* 一般に、次の 3 つのファイルを作る必要があります。`project.yaml`（プロジェクトの一般的な情報）、Dockerfile（ビルドの依存関係をすべて含むイメージ）、`build.sh`（ハーネスのビルド）です。
* 自分のファイルに取りかかる前に、[oss-fuzz に登録されている既存のプロジェクトのファイル](https://github.com/google/oss-fuzz/tree/master/projects)を見ておくのが最善です。
* ハーネスのソースコードは、oss-fuzz プロジェクトの外に置くことをお勧めします。[cURL のように](https://github.com/curl/curl-fuzzer)、ファジング専用のリポジトリを作っているプロジェクトもあります。
* 現在の手順の全体は、oss-fuzz の[入門ページ](https://google.github.io/oss-fuzz/getting-started/accepting-new-projects/)に書かれているので、詳細はそのページを確認してください。


## ToB が OSS-Fuzz にプロジェクトを組み込んだ方法

[この pull request](https://github.com/google/oss-fuzz/pull/11444) を見てください。CBOR シリアライズ形式のエンコード・デコード用ライブラリである [cbor2](https://github.com/agronholm/cbor2) プロジェクトを、OSS-Fuzz に追加するものです。特に、次の点に注目してください。
1. PR の[最初のメッセージ](https://github.com/google/oss-fuzz/pull/11444#issue-2064583587)。cbor2 ライブラリとその依存先を簡単に紹介しています。
2. プロジェクトに付けられた[重要度スコア](https://github.com/google/oss-fuzz/pull/11444#issuecomment-1875907472)
3. [実際の OSS-Fuzz のプロジェクト設定とハーネスの実装](https://github.com/google/oss-fuzz/pull/11444/files)。そう、これだけ簡単なのです。


 詳しくは、ブログ記事[Continuously Fuzzing Python C Extensions](https://blog.trailofbits.com/2024/02/23/continuously-fuzzing-python-c-extensions/)を参照してください。


{{< hint info >}}
**OSS-Fuzz を含む、ファザーの使い方についてのさらなる案内は、[FAQ]({{% relref "05-faq" %}})を参照してください。**
{{< /hint >}}

*FAQ から、OSS-Fuzz に関する質問の例を紹介します。*

{{< rawHtml "" >}} 
<details open="true">
<summary>FAQ (Fuzzily Asked Questions)</summary>
{{< fuzzing/oss-fuzz-faq >}}
</details>
{{< /rawHtml >}}
