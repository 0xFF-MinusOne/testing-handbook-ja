---
title: "インストールと最初の一歩"
slug: installation
summary: "このセクションでは、Semgrep をインストールする手順と、使い始める方法を説明します。"
weight: 1
---

# インストールと最初の一歩

## 初期設定

インストールの詳しい手順は、公式の
[Installing and running Semgrep locally](https://semgrep.dev/docs/getting-started/#installing-and-running-semgrep-locally)
のドキュメントを参照してください。

### Semgrep のインストール

オペレーティングシステムや好みに応じて、Semgrep のインストール方法はいくつかあります。
{{< tabs "installing-semgrep" >}}

{{< tab "Python パッケージインストーラ" >}} pip で Semgrep をインストールするには、次のコマンドを実行します。

```sh
python3 -m pip install semgrep
```

{{< /tab >}}
{{< tab "Homebrew" >}} macOS または Linux を使っている場合は、Homebrew で Semgrep をインストールできます。Homebrew でインストールするには、
次のコマンドを実行します。

```sh
brew install semgrep
```

{{< /tab >}}
{{< tab "Docker コンテナの Semgrep" >}} Semgrep を Docker コンテナで使いたい場合は、公式の Semgrep の
Docker イメージを使えます。
最新の Semgrep の Docker イメージは、[Docker Hub](https://hub.docker.com/r/returntocorp/semgrep) のページにあります。
{{< /tab >}}
{{< /tabs >}}

### Semgrep を最新に保つ

Semgrep はセキュリティツールで、新機能の追加やバグの修正によって改善が続いています。こうした改善を活かし、セキュリティテストをできるだけ効果的にするために、
最新のリリースに追従しておくことが大切です。

#### 更新の確認

Semgrep は、実行したときに新しいバージョンがあれば知らせてくれます。更新がある場合は、
次のようなメッセージが表示されます。

```shell
$ semgrep -c auto
# (...)
A new version of Semgrep is available. See https://semgrep.dev/docs/upgrading
```

[Semgrep Releases](https://github.com/semgrep/semgrep/releases) のページを見て、
手動で更新を確認することもできます。

#### Semgrep の更新

インストールの方法に応じて、Semgrep の更新方法はいくつかあります。詳しくは、公式の
[Updating Semgrep](https://semgrep.dev/docs/upgrading/) のドキュメントを参照してください。

{{< tabs "updating-semgrep" >}}
{{< tab "Python パッケージインストーラ" >}} Python パッケージインストーラ（pip）で更新するには:

```shell
python3 -m pip install --upgrade semgrep
```

{{< /tab >}}

{{< tab "Homebrew" >}} Homebrew で更新するには:

```shell
brew upgrade semgrep
```

{{< /tab >}}

{{< tab "Docker コンテナの Semgrep" >}}
Semgrep を Docker コンテナで使っている場合は、最新の Semgrep のイメージでコンテナを再ビルドすれば更新できます。
最新の Semgrep の Docker イメージは、[Docker Hub](https://hub.docker.com/r/returntocorp/semgrep) のページにあります。
{{< /tab >}}
{{< /tabs >}}

## Semgrep の実行

### 始める前に

{{< hint danger >}}

#### 注意 1: プライバシー

auto モード（`--config auto` 引数）では、メトリクスをオンラインで送信する必要があります。つまり、スキャンしたソースコードに関するメタデータの一部が、Semgrep のサーバーに送られます。
オープンソースのプロジェクトでは問題になりませんが、
非公開のコードに Semgrep を使うときは考慮が必要です（[Semgrep のプライバシーポリシー](https://semgrep.dev/docs/metrics/)を参照）。
`--metrics=off` 引数を付けて Semgrep を実行すると、メトリクスを無効にできます。

{{< /hint >}}

#### 注意 2: 無視されるファイル

Semgrep のデフォルトの設定では、`/tests`、`/test`、`/vendors` のフォルダをスキップします。これらもスキャンしたい場合は、
`.semgrepignore` ファイルで、スキップするものを調整します。`.semgrepignore` の使い方の詳細は、
[ファイルやフォルダの無視に関する Semgrep のドキュメント](https://semgrep.dev/docs/ignoring-files-folders-code/)を参照してください。

個別のファイルを含めたり除外したり、ワイルドカードを使ったりするときの、よく使う構文を簡単にまとめます。

- 特定のファイルやディレクトリを無視するには、そのパスを `.semgrepignore` ファイルに追加します。

  ```sh
  path/to/ignore/file.ext
  path_to_ignore/
  ```

- 特定の拡張子のファイルをすべて無視するには、ワイルドカード `*` を使います。

  ```sh
  *.ext
  ```

### 「auto」設定での事前の実行

リポジトリで次のコマンドを使うと、検出したプログラミング言語やファイル名に基づいて、
関連する組み込みのルールセットが自動で検出され、使われます。

```sh
semgrep --config auto
```

### 最適なセキュリティテストのためのルールセットの調整

セキュリティテストでは、的を絞って集中することが重要です。Semgrep の「auto」設定は、コードに基づいて一般的なルールを自動で適用してくれる、
便利な出発点ですが、必ずしも最も正確な結果になるとは限りません。誤検知を最小限にして、検出結果のノイズを減らすには、
コードベースに関係のあるルールセットだけを選ぶことが欠かせません。

ルールセットをカスタマイズすると、テストの進め方が効率的になり、自分のコードに関係のない問題に使う時間を省けます。
「auto」設定は、セキュリティテストの最初の一歩としては役に立ちますが、
自分の用途に合った、より正確で効率的な解析のためには、ルールセットを微調整することが重要です。

1. **Semgrep Registry を探る**: [Semgrep Registry](https://semgrep.dev/explore) を見て、必要に合うルールセットを探します。
Semgrep Registry には幅広いルールセットがあり、組織の要件やコーディング規約に合うものを見つけられます。
2. **メトリクスの収集を無効にする**: Semgrep を使うときに、匿名の利用メトリクスを送りたくない場合は、
次のどちらかの方法で無効にできます。

   - 環境変数 [SEMGREP_SEND_METRICS](https://semgrep.dev/docs/cli-reference/#:~:text=SEMGREP_SEND_METRICS) を設定します。
    シェルの設定ファイルに書くか、現在のシェルのセッションで変数を export します。

      ```sh
      export SEMGREP_SEND_METRICS=off
      ```

      環境変数を設定すると、Semgrep は実行中に匿名の利用メトリクスを送信しなくなります。

   - `alias` コマンドを使います。

     ```sh
     alias semgrep="semgrep --metrics=off"
     ```

     このコマンドは、`--metrics=off` オプション付きの Semgrep コマンドのエイリアスを作ります。Semgrep を使うたびに、
     エイリアスのコマンドが実行され、メトリクスが送信されなくなります。alias コマンドをシェルの設定ファイルに追加すると、
     ターミナルのセッションをまたいで使える、_永続的な_エイリアスになります
     （具体的なファイルは、使っているシェルによります）。

     {{< hint danger >}}`alias` コマンドを使う方法には注意してください。エイリアスは、対話的なシェルのセッションでしか働かないからです。
     スクリプトから Semgrep を実行すると、メトリクスは送信されてしまいます。メトリクスの収集を無効にする方法としては、
     環境変数を使う方法を第一の選択肢にすることをお勧めします。{{< /hint>}}

3. **カスタマイズしたルールセットを使う**: 選んだルールセットで、現在のディレクトリとそのサブディレクトリをスキャンするには、
次のコマンドを実行します。
   - Semgrep Registry にあるルールセットの場合:

     ```sh
     # Runs the trailofbits ruleset with Semgrep
     semgrep --config="p/trailofbits"
     ```

   - ディレクトリにあるルールセット（Semgrep Registry にないものなど）の場合:

     ```sh
     # Runs Semgrep rules from the /home/semgrep-rules directory
     semgrep -f /home/semgrep-rules
     ```

    {{< hint info >}}`-c`、`-f`、`--config` のフラグは、どれもスキャンで使うルールセットを指定するという同じ目的なので、
    入れ替えて使えます。{{</hint>}}

   - あらかじめ用意された複数のルールを同時に実行するには、`--config`（または短縮形の `-c`、`-f`）の引数を複数指定します。

     ```sh
     semgrep --config="p/trailofbits" --config="p/r2c-security-audit"
     ```

   - 一時的なルール（例: `semgrep -e 'exec(...)' --lang=py ./`）を使うと、ルールをその場で渡せます。

4. **出力形式の概要**: Semgrep は複数の出力形式に対応していて、好みやツールに合わせて結果を便利に解析できます。

   a. 使える形式:
      Semgrep のスキャン結果は、Emacs、JSON、GitLab SAST、
      GitLab Secrets、JUnit XML、SARIF、Vim など、さまざまな出力形式から選べます。使える出力形式をすべて見るには、`semgrep scan --help` を実行します。

   b. 外部のツールと出力形式を組み合わせる:
     - **SARIF 形式**: SARIF 形式は、Visual Studio Code と
       [SARIF Explorer](https://marketplace.visualstudio.com/items?itemName=trailofbits.sarif-explorer) 拡張機能で使います。
       解析結果をレビューしやすく、個々の問題を掘り下げて、その
       影響と重大度を把握できます。`p/default` ルールセットを SARIF 出力形式で使う例:

       ```sh
       semgrep -c p/default --sarif --output scan_results.sarif
       ```

     - **VIM 形式**: VIM 形式を使うと、検出結果に関する情報がすべて 1 行にまとまるので、
       テキストエディタの Vim を使う人に便利です。`p/default` ルールセットを VIM 出力形式で使う例:

       ```sh
       semgrep -c p/default --vim --output scan_results.vim
       ```

   c. 結果の絞り込みと制限:
     - `--severity [INFO|WARNING|ERROR]` フラグを使うと、指定した重大度（`INFO`/`WARNING`/`ERROR`）に一致する
       ルールの検出結果だけを報告します。
     - 特定のルールのメタデータ（影響など）で結果を絞り込める、分かりやすいフラグは、現時点ではありません。
       回避策の可能性については、GitHub の issue
       [Feature request: CLI support for filtering by rule metadata](https://github.com/semgrep/semgrep/issues/6752)
       を参照してください。

   d. データフローのトレース:

      `--dataflow-traces` フラグを使うと、ローカルでない値が検出結果にどう関わっているかが分かります。このオプションは、
      報告された問題につながる、変数、関数呼び出し、そのほかのコード要素の間のデータフローを示す、
      詳細な出力を生成します。

      たとえば、次のような場面で、データフローのトレースが役に立ちます。
      - Semgrep が SQL インジェクションの脆弱性の可能性を見つけたとします。その場合、データフローのトレースを使うと、
        ユーザーの入力がさまざまな関数を通って、最終的に安全でない SQL クエリに使われるまでを追えます。これにより、
        適切な入力のサニタイズをどこで実装すべきかを特定できます。
      - Semgrep がパストラバーサルの脆弱性の可能性を検出したとします。その場合、データフローのトレースから、
        サニタイズされていない入力の発生元、それを処理する関数、脆弱性を生むファイル I/O の操作といった、
        脆弱性につながったコード要素の並びが分かります。このデータを分析すると、
        根本の原因をより効果的に特定し、適切な修正を施せます。

      このフラグは現在、テイントモードに対応していて、汚染されたデータの流れを、その_発生元（source）_から_到達先（sink）_まで追跡します。

      Semgrep の標準的な出力を示す、[次の例](https://semgrep.dev/s/X4AK)を見てみましょう。

      ```shell
      $ semgrep -f taint_mode_test.yml taint_mode.py
       # (...)
       Found unsanitized flow

                 3┆ return output(data)
       # (...)
      ```

      `--dataflow-traces` オプションを付けると、より詳しい解析結果が得られます。

      ```shell
      $ semgrep --dataflow-traces -f taint_mode_test.yml taint_mode.py
      # (...)
      Found unsanitized flow

                3┆ return output(data)
                ⋮┆----------------------------------------

                Taint comes from:
                 taint_mode.py
                  2┆ data = get_user_input()

                Taint flows through these intermediate variables:
                  2┆ data = get_user_input()

                This is how taint reaches the sink:
                 taint_mode.py
                  3┆ return output(data)
      # (...)
      ```

      また、さらに処理するために `--json`（JSON 出力）を使うこともできます。

      ```sh
      $ semgrep --json --dataflow-traces -f rule.yml test3.py
      Scanning 1 file.
      # (...)
      {
      # (...)
      "path": "test3.py",
      "start": { "col": 5, "line": 8, "offset": 146 } }}],
      "taint_sink": ["CliLoc", [ {"end": {"col": 29,"line": 10,"offset": 226 },
      "path": "test3.py","start": { "col": 12, "line": 10, "offset": 209 }
      },
      "html_output(data)"]],
      "taint_source": ["CliLoc", [{ "end": {"col": 28,"line": 8,"offset": 169},
      "path": "test3.py", "start": { "col": 12, "line": 8, "offset": 153 }},
      "get_user_input()"]]
      },
      "engine_kind": "OSS",
      "lines": "    return html_output(data)",
      "message": "Found dangerous HTML output",
      "severity": "WARNING"
      # (...)
      },
      # (...)
      ```

    e. 出力の詳細さとデバッグ:
      - `--verbose` フラグを使うと、どのルールが動いているか、どのファイルがスキップされたかなどの
        詳しい情報が表示されます。
      - `--debug` フラグを使うと、`--verbose` フラグを使ったときと同じ情報に加えて、
     デバッグ用の情報も表示されます。

### サードパーティの Semgrep ルールの管理

デフォルトでは、[Semgrep Explore](https://semgrep.dev/explore) のウェブサイトにあるさまざまなルールを、
Semgrep で自動的に適用できます。たとえば、CWE Top 25 のルールを使うには、次のコマンドを使います。

```sh
semgrep --config "p/cwe-top-25"
```

Semgrep Explore が提供するデフォルトのルールに、個々のセキュリティ研究者などが作った外部のルールを加えると、テストの能力を高められます。ただし、多くのルールセットは、
作者が管理するリポジトリに置かれていて、公式の Semgrep のリポジトリには含まれていないことがあります。これらのルールを効果的に管理するには、
[semgrep-rules-manager](https://github.com/iosifache/semgrep-rules-manager/) の利用を検討してください。
semgrep-rules-manager の目的は、サードパーティから質の高い Semgrep ルールを集めることです。

semgrep-rules-manager を使い始めて、対応しているカスタムの Semgrep ルールをすべてダウンロードするには、次の手順に従います。

```sh
# Install semgrep-rules-manager via pip (see https://github.com/iosifache/semgrep-rules-manager#installation for more info)
$ pip install semgrep-rules-manager

# Create a new directory for downloaded Semgrep rules
$ mkdir -p $HOME/custom-semgrep-rules

# Use semgrep-rules-manager to download custom rulestes
$ semgrep-rules-manager --dir $HOME/custom-semgrep-rules download
✅ 7 sources were successfully downloaded

# Show downloaded Semgrep rules
$ ls $HOME/custom-semgrep-rules
0xdea  community  dgryski  elttam  gitlab  kondukto  trailofbits

# Run downloaded rules in the current directory
$ semgrep -f $HOME/custom-semgrep-rules
```

semgrep-rules-manager は、`community`、`trailofbits`、`dgryski`、`gitlab` のように、Semgrep Explore にすでに含まれているルールセットも
ダウンロードすることがあるので注意してください。

### Semgrep を実行するときのその他のヒント

- [オートコンプリートの機能](https://semgrep.dev/docs/cli-reference/#autocomplete)を導入すると、
  コマンドラインで作業するときに `TAB` キーで作業を速められます。
- 大きなコードベースで Semgrep を実行したときに、エラー `No file descriptors available` が出る場合は、
開いているファイルが多すぎることを示しています。この問題を解決するには、UNIX の `ulimit` コマンドで、許可するファイルディスクリプタの数を増やします。

  UNIX の `ulimit` コマンドで許可するファイルディスクリプタの数を増やすには、次のコマンドを使います。

  ```sh
  # Check the current limit of file descriptors:
  $ ulimit -n
  256
  # To increase the limit, use the following command,
  # replacing NEW_LIMIT with the desired number of file descriptors:
  $ ulimit -n NEW_LIMIT # e.g. ulimit -n 4096
  ```

  この変更は、現在のターミナルのセッションにだけ適用されることを覚えておいてください。
