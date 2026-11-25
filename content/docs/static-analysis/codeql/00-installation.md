---
title: "インストールと最初の手順"
slug: installation
summary: "このセクションでは、CodeQL のインストール方法と、CodeQL データベースのビルドと解析の方法を説明します。"
weight: 1
---

# インストールと最初の手順

## 初期設定

詳しいインストール手順は、公式の
[ドキュメント](https://docs.github.com/en/code-security/codeql-cli/getting-started-with-the-codeql-cli/setting-up-the-codeql-cli).

### CodeQL のインストール

CodeQL は手動でインストールできます。macOS または Linux を使っている場合は、パッケージマネージャーの Homebrew を使うこともできます。

{{< tabs "installing-codeql" >}}

{{< tab "手動でインストールする" >}}
CodeQL CLI を手動でインストールするには、[CodeQL のリリースページ](https://github.com/github/codeql-action/releases)に移動し、お使いのアーキテクチャ向けの最新のバンドルをダウンロードします。
{{< /tab >}}

{{< tab "Homebrew を使う" >}}
macOS または Linux では、次のコマンドで Homebrew を使って CodeQL をインストールできます。

```sh
brew install --cask codeql
```

{{< /tab >}}

{{< /tabs >}}

どちらの方法でも、インストールされるバンドルには、`codeql` のバイナリ、対応する言語向けのクエリライブラリ、含まれるすべてのクエリのコンパイル済みバージョンが入っています。

### CodeQL を最新に保つ

CodeQL は活発に開発されています。こうした改善の恩恵を受け、セキュリティテストをできるだけ効果的に行うために、最新のリリースに更新し続けることが重要です。

CodeQL を手動でインストールした場合は、[CodeQL のリリースページ](https://github.com/github/codeql-action/releases)に移動して、新しい更新をダウンロードする必要があります。Homebrew で CodeQL をインストールした場合は、次のコマンドを実行すると、手元のインストールを最新にできます。

```shell
brew upgrade codeql
```

## データベースのビルド

新しい CodeQL データベースをビルドするには、通常、対応するコードベースをビルドできる必要があります。コードベースがクリーンな状態であること(たとえば `make clean`、`go clean` などを実行して)を確認してから、次のように CodeQL CLI でコードベースをビルドします。

{{< tabs "building-a-database" >}}

{{< tab "C/C++" >}}

C または C++ のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `cpp` を渡します。ビルドコマンドは、`command` 引数で指定します。

```shell
codeql database create codeql.db --language=cpp --command='make -j8'
```

CMake のようなメタビルドシステムを使っている場合は、まず `cmake` を実行してビルド設定ファイルを生成し、そのあとで実際のビルドコマンドを CodeQL に渡します。

ソースファイルが、ビルドする場所と同じツリーにない場合(たとえば、`cmake` でアウトオブソースビルドを行っている場合)は、データベースの生成時に `--source-root` 引数を追加して、ソースファイルツリーのルートを正しく設定します。
{{< /tab >}}

{{< tab "Go" >}}

Golang のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `go` を渡します。

```shell
codeql database create codeql.db --language=go
```

ビルドスクリプトや、より複雑なビルドシステムを使っている場合は、`--command` 引数でビルドコマンドを CodeQL に渡せます。

{{< /tab >}}
{{< tab "Java/Kotlin" >}}

Java または Kotlin のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `java` を渡します。

```shell
codeql database create codeql.db --language=java
```

ビルドスクリプトや、より複雑なビルドシステムを使っている場合は、`--command` 引数でビルドコマンドを CodeQL に渡せます。

{{< /tab >}}
{{< tab "JavaScript/TypeScript" >}}

JavaScript または TypeScript のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `javascript` を渡します。

```shell
codeql database create codeql.db --language=javascript
```

{{< /tab >}}
{{< tab "Python" >}}

Python のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `python` を渡します。

```shell
codeql database create codeql.db --language=python
```

{{< /tab >}}
{{< tab "Swift" >}}

Swift のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `swift` を渡します。

```shell
codeql database create codeql.db --language=swift
```

ビルドスクリプトや、より複雑なビルドシステムを使っている場合は、`--command` 引数でビルドコマンドを CodeQL に渡せます。

{{< /tab >}}
{{< tab "Ruby" >}}

Ruby のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `ruby` を渡します。

```shell
codeql database create codeql.db --language=ruby
```

ビルドスクリプトや、より複雑なビルドシステムを使っている場合は、`--command` 引数でビルドコマンドを CodeQL に渡せます。

{{< /tab >}}
{{< tab "C#" >}}

C# のプロジェクトのデータベースをビルドするには、CodeQL CLI に言語として `csharp` を渡します。

```shell
codeql database create codeql.db --language=csharp
```

ビルドスクリプトや、より複雑なビルドシステムを使っている場合は、`--command` 引数でビルドコマンドを CodeQL に渡せます。

{{< /tab >}}
{{< /tabs >}}

### 個別のファイルを除外する

インタプリタ型の言語では、`--codescanning-config=codeql-config.yml` を使い、`codeql-config.yml` ファイルに `paths-ignore` を書きます。

```yaml
paths-ignore:
  - node_modules
  - vendor
  - external
  - "**/*.min.js"
  - "**/*.bundle.js"
  - "**/generated/**"
  - "**/dist/**"
  - "**/tests/**"
```

コンパイル型の言語で、サードパーティのライブラリをデータベースに含めないようにするには、次のコツが必要です。プロジェクトを一度ビルドし、プロジェクトに直接関係するオブジェクトファイル(解析したいもの)を削除してから、CodeQL CLI でプロジェクトのデータベースをビルドします。

CodeQL はビルドの過程を計装し、各コンパイル単位の情報を順次データベースに追加します。つまり、コンパイラが 1 つ以上のソースファイルをスキップした場合(たとえば、対応するオブジェクトファイルがすでにあり、最新であるため)、対応する関数や型もデータベースに追加されません。

ただし、ファイルを無視すると、CodeQL は対応するコードについて部分的な知識しか持てず、それらのファイルで定義された関数やメソッドを通るデータフローを推論できなくなることを覚えておいてください。このため、サードパーティのライブラリは含めておき、代わりに、問題が見つかったコードベース内の場所にもとづいて絞り込むほうが、よいことが多いです。これは、実行時の動的リンクに頼るより、サードパーティのライブラリをベンダリングして取り込むほうが、一般により網羅的な解析結果が得られるということでもあります。

### 複数ステップのビルド

複数のビルドから、1 つの CodeQL データベースを作れます。これは、コードベースがいくつかの異なる Docker コンテナでビルドされる場合や、複数のサブプロジェクトが関わっている場合に役立ちます。

手順は、CodeQL の `init`、`trace-command`、`finalize` の各コマンドを使うことです。

```bash
codeql database init \
    --overwrite --source-root=. --language=cpp --begin-tracing \
    -- ${BUILD_CACHE_DATABASE}

codeql database trace-command \
    -- ${BUILD_CACHE_DATABASE} ${CC} -c lib/lib1.c -o lib/lib1.o
codeql database trace-command \
    -- ${BUILD_CACHE_DATABASE} ${CC} -c lib/lib2.c -o lib/lib2.o
codeql database trace-command \
    -- ${BUILD_CACHE_DATABASE} ${CC} main.c lib/lib1.o lib/lib2.o -o main

codeql database finalize -- ${BUILD_CACHE_DATABASE}
```

## データベースの解析

CodeQL のバンドルには、コンパイル済みのクエリパックが一式含まれています。CodeQL CLI を使って、サードパーティのクエリパックをインストールすることもできます。インストール済みのクエリパックの一覧を見るには、次のコマンドを使います。

```shell
codeql resolve qlpacks
```

`codeql database analyze` コマンドは、既存のデータベースに対して一連のクエリを実行します。出力はファイルに書き込まれ、出力形式はコマンドラインの引数で指定します。次のコマンドは、コンパイル済みのクエリパック `codeql/cpp-queries` を、指定した CodeQL データベースに対して実行します。出力は、SARIF ファイル `results.sarif` に書き込まれます。

```shell
codeql database analyze codeql.db --format=sarif-latest --output=results.sarif -- codeql/cpp-queries
```

[SARIF](https://github.com/microsoft/sarif-tutorials) は、多くの静的解析ツールが使う共通の出力形式です。VSCode を使っているなら、[VSCode SARIF Explorer 拡張機能](https://marketplace.visualstudio.com/items?itemName=trailofbits.sarif-explorer)で SARIF の結果を表示できます。SARIF のほかに、CodeQL は CSV 形式の出力にも対応しています。

いくつかのヒントです。

* 解析の範囲を制御するには、[`--threat-model` フラグを使う](https://docs.github.com/en/code-security/reference/code-scanning/codeql/codeql-cli-manual/database-analyze#--threat-modelname)
* 解析を速くするには、`--threads=0` を使う

## 新しいクエリパックのインストール

CLI のバンドルに同梱されているコンパイル済みのクエリパックのほかに、CodeQL CLI を使って、サードパーティのクエリパックをインストールすることもできます。公開されているクエリパックは、_スコープ_、_名前_、省略可能な_バージョン_で識別されます。GitHub container registry に公開されているクエリパックでは、スコープは、対応するリポジトリを所有する組織またはアカウントを表します。次のコマンドは、Trail of Bits が公開している `cpp-queries` と `go-queries` のクエリパックを(最新バージョンで)ダウンロードします。

```shell
codeql pack download trailofbits/cpp-queries trailofbits/go-queries
```

私たちが公開している CodeQL のクエリとクエリパックの詳細は、[trailofbits/codeql-queries](https://github.com/trailofbits/codeql-queries) リポジトリを参照してください。
