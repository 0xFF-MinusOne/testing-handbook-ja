---
title: "高度な使い方"
slug: advanced
summary: "このセクションでは、独自の CodeQL クエリとクエリパックの作り方、およびテスト方法を説明します。"
weight: 10
---

# 高度な使い方

## ソースとシンクの追加

一部の言語では、新しいソース、シンク、関数のサマリーを宣言する簡単な方法があります。[データ拡張](https://codeql.github.com/docs/codeql-language-guides/customizing-library-models-for-cpp/)です。

モデル化したい関数をすべて列挙した YAML ファイルを作るだけです。これは、プロジェクトに複雑なフローがあり、CodeQL が既知の I/O メソッドからすべてのソースやシンクを自動的に検出できないかもしれない場合に便利です。

ソースとシンクの拡張は、見たままの意味です。サマリーは、1 つの関数の内部でのデータフローを記述するために使います。

たとえば、`boost::asio::read_until` 関数をモデル化するには、次のようなファイルを作ります。

```yaml
extensions:
  - addsTo:
      pack: codeql/cpp-all
      extensible: sourceModel
    data:
      - ["boost::asio", "", False, "read_until", "", "", "Argument[*1]", "remote", "manual"]
```

新しいプロジェクトに取り組むときは、次の流れをお勧めします。

1. codeql データベースを構築する
2. サンプルのクエリを実行して、すべてのソースとシンクを一覧にする
3. 生成された一覧が不完全に見える場合は、データ拡張を使う

LLM は、拡張の検出と作成が得意な場合があります。

## 新しいクエリパックの作成 {#creating-new-query-packs}

CodeQL のクエリは、QL(Query Language の略)という宣言型でオブジェクト指向の言語で書きます。QL は、関数やクラスの定義には Java に似た構文を、クエリの定義には SQL に似た構文を使います。

CodeQL のクエリは、クエリパックにまとめられます。クエリパックのルートは、そのパックが定義するクエリのメタデータを含む `qlpack.yml` ファイルで識別されます。独自のクエリを定義するには、まず、対応するクエリパックを作る必要があります。

新しいクエリパックを作るには、`codeql pack init <scope>/<name>` を実行します。(ここで、_scope_ は、クエリの公開先となる GitHub アカウントまたは GitHub organization の名前で、_name_ は、この名前空間の中でクエリパックを識別する名前です。)これにより、カレントディレクトリに新しいディレクトリ _name_ が作られ、最小限の `qlpack.yml` ファイルが置かれます。

```yaml
---
library: false
warnOnImplicitThis: false
name: <scope>/<name>
version: 0.0.1
```

CodeQL はセマンティックバージョニングを使い、バージョンは既定で 0.0.1 に初期化されます。

クエリの作成と実行に CodeQL の VSCode 拡張機能を使っている場合は、[クエリパックの初期化と `qlpack.yml` ファイルの作成を自動で行えます](#running-custom-queries-using-the-vscode-extension)。

最後に、CodeQL CLI が正しく動くように、[ワークスペースファイル](https://docs.github.com/en/code-security/codeql-cli/using-the-advanced-functionality-of-the-codeql-cli/about-codeql-workspaces)を作る必要があります。

複数のクエリパックを書くと分かっている場合は、開発しやすくするために、次のディレクトリ構成を作ることをお勧めします。

```plain
.
├── CODEOWNERS
├── README.md
├── codeql-workspace.yml
├── cpp
│   ├── lib
│   │   ├── qlpack.yml
│   │   └── scope
│   │       └── security
│   │           └── someLibrary.qll
│   ├── src
│   │   ├── qlpack.yml
│   │   ├── suites
│   │   │   ├── scope-cpp-code-scanning.qls
│   │   │   └── scope-cpp-security.qls
│   │   ├── security
│   │   │   └── AppSecAnalysis
│   │   │       ├── AppSecAnalysis.c
│   │   │       ├── AppSecAnalysis.qhelp
│   │   │       └── AppSecAnalysis.ql
│   └── test
│       ├── qlpack.yml
│       ├── include
│       │   ├── libc
│       │   │   ├── stubs.h
│       ├── library-tests
│       │   └── security
│       │       ├── someLibrary
│       │       │   ├── someLibrary.c
│       │       │   ├── someLibrary.expected
│       │       │   └── someLibrary.ql
│       └── query-tests
│           └── security
│               └── AppSecAnalysis
│                   ├── AppSecAnalysis.c
│                   ├── AppSecAnalysis.expected
│                   └── AppSecAnalysis.qlref
...
```

クエリパックは、言語ごとに分け、さらに種類(セキュリティ、暗号など)ごとにも分けます。これは、GitHub のクエリスイートが使う慣例にも沿っています。

クエリの単体テストの設定方法の推奨事項は、[独自クエリの単体テスト](#unit-testing-custom-queries)のセクションを参照してください。

### 依存関係の追加

独自のクエリを定義するには、解析する言語の CodeQL 標準ライブラリをインポートする必要があります。そのため、標準ライブラリを `qlpack.yml` ファイルの依存関係として追加する必要があります。これは、YAML ファイルを直接編集するか、`codeql pack add` コマンドを使うことで行えます。

{{< tabs "adding-query-pack-deps" >}}

{{< tab "C/C++" >}}

C と C++ 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/cpp-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/cpp-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "Go" >}}

Golang 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/go-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/go-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "Java/Kotlin" >}}

Java と Kotlin 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/java-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/java-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "JavaScript/TypeScript" >}}

JavaScript と TypeScript 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/javascript-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/javascript-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "Python" >}}

Python 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/python-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/python-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "Swift" >}}

Swift 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/swift-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/swift-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "Ruby" >}}

Ruby 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/ruby-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/ruby-all: ^X.Y.Z
```

{{< /tab >}}

{{< tab "C#" >}}

C# 向けの CodeQL 標準ライブラリを(最新バージョンで)依存関係として追加するには、クエリパックのルートディレクトリで次のコマンドを実行します。

```sh
codeql pack add codeql/csharp-all
```

これにより、`qlpack.yml` に次の 2 行が追加されます。

```yaml
dependencies:
  codeql/csharp-all: ^X.Y.Z
```

{{< /tab >}}

{{< /tabs >}}

(`qlpack.yml` の依存関係を手動で更新していて、どのバージョンにするか分からない場合は、常に最新のバージョンに解決される `"*"` を使えます。)

### 新しいパックのインストール

新しいクエリパックを初期化し、依存関係といくつかのサンプルクエリを追加したら、qlpack.yml ファイルがあるすべてのディレクトリ(テスト用のフォルダを含む)で `codeql pack install` を実行する必要があります。

次に、`~/.config/codeql/config` ファイルを次の内容で作成して、新しいクエリを codeql CLI に知らせます。

```plain
--search-path /full/path/to/your/codeql/root/directory
```

## 独自クエリの作成

{{< hint info >}}
独自の CodeQL クエリを書くには、標準ライブラリと標準のクエリにアクセスできる必要があります。スターターワークスペースの利用をお勧めします。

1. [vscode-codeql-starter](https://github.com/github/vscode-codeql-starter.git) リポジトリを手元のコンピュータにクローンします。
`git clone --recursive https://github.com/github/vscode-codeql-starter.git`
2. VSCode で **File** -> **Open Workspace from File** をクリックし、`vscode-codeql-starter` リポジトリの `vscode-codeql-starter.code-workspace` ファイルを開きます。

{{< /hint >}}

QL は宣言型の言語で、CodeQL のクエリは、次の形の SQL に似た構文で表現します。

```mysql
from Type x where P(x) select f(x)
```

ここで、`P(x)` は変数 `x` を含む述語で、`f(x)` は `x` を含む式です。このクエリは、[内包表記による集合](https://en.wikipedia.org/wiki/set-builder_notation)として捉えると、最も分かりやすくなります。つまり、`x` が基底集合 `Type` の要素で、`P(x)` が真であるときの、すべての `f(x)` を選びます。

具体例として、次のクエリを考えます。これは、`memcpy` 関数の呼び出しで、第 1 引数として渡されるすべての式を選びます。

```mysql
import cpp

from
  FunctionCall call
where
  call.getTarget().getName() = "memcpy"
select
  call.getLocation(), call.getArgument(0)
```

ここで、基底集合はすべての関数呼び出しの集合で、これは、C と C++ 向けの CodeQL 標準ライブラリが定義する型 [`FunctionCall`](https://codeql.github.com/codeql-standard-libraries/cpp/semmle/code/cpp/exprs/Call.qll/type.Call$FunctionCall.html) に対応します。述語 `P(x)` は、次で与えられます。

```mysql
x.getTarget().getName() = "memcpy"
```

式 `f(x)` は、`x.getArgument(0)` で与えられます。

### CodeQL のクラス、メソッド、関数

CodeQL の標準ライブラリは、クエリの組み立てに使える多数の型と関数を定義しています。標準ライブラリの上に抽象化を作るために、新しい型や関数を定義することもできます。

たとえば、上のように、`memcpy` 関数のすべての呼び出しを表す新しい型を作りたいとします。これは、次のように、新しい CodeQL の_クラス_を定義することで行います。

```mysql
import cpp

class MemcpyCall extends FunctionCall {
  MemcpyCall() {
    this.getTarget().getName() = "memcpy"
  }

  Expr getDestination() {
    result = this.getArgument(0)
  }

  Expr getSource() {
    result = this.getArgument(1)
  }

  Expr getSize() {
    result = this.getArgument(2)
  }
}

from
  MemcpyCall call
select
  call.getLocation(), call.getDestination()
```

新しい型は、必ず既存の CodeQL の型を_拡張_(つまりサブクラス化)する必要があります。この場合は `FunctionCall` を拡張しており、コードベース内のすべての関数呼び出しの集合の部分集合を定義することに相当します。メソッド `MemcpyCall()` は、クラスの_特性述語_と呼ばれ、関数呼び出しが `MemcpyCall` とみなされるために真でなければならない条件を含みます。(これも内包表記による集合であり、集合 `FunctionCall` のすべての式のうち、特性述語を満たすものからなる部分集合を作っていることに注意してください。)

このクラスはさらに、`memcpy` に渡される個々の引数にアクセスするメソッドを、いくつか定義しています。CodeQL のメソッドと関数は多値です。つまり、複数の値を取りえます。このため、メソッドと関数は、入力と出力の対応する関係(`result` 変数で与えられる)の糖衣構文だと考えるほうが、一般に分かりやすくなります。ある入力の組に対して、複数の出力がこの関係を満たす場合、そのメソッドや関数は多値になります。

CodeQL のメソッドや関数が多値だと分かっている場合は、関数名を `getX` ではなく `getAnX` にして、それを示すことがよくあります。(例は、[`FunctionCall`](https://codeql.github.com/codeql-standard-libraries/cpp/semmle/code/cpp/exprs/Call.qll/type.Call$FunctionCall.html) 型の多値のメソッド `getAnArgument` で、関数に渡される引数のどれかを返します。)

### 全称量化と存在量化

CodeQL は、キーワード `exists` と `forall` による、範囲を限定した量化に対応しています。たとえば、関数 `fun` が一度も呼ばれないときに真になる述語 `isNeverCalled(fun)` を定義するには、次のように、存在量化子 `exists` を使えます。

```mysql
predicate isNeverCalled(Function fun) {
  not exists(FunctionCall call |
    call.getTarget() = fun
  )
}
```

くだけた言い方をすると、これは、`fun` を呼び出す関数呼び出し `call`(つまり、`call.getTarget()` が `fun` に等しいもの)が存在しないことを表します。

### 再帰と推移閉包

CodeQL は、再帰的な述語を標準でサポートしています。例として、[基本ブロック](https://en.wikipedia.org/wiki/Basic_block) `end` が別の基本ブロック `start` から到達可能であるという事実を表すには、次のように、これを捉える述語 `isReachableFrom(start, end)` を定義できます。

```mysql
predicate isReachableFrom(BasicBlock start, BasicBlock end) {
  start = end or isReachableFrom(start.getASuccessor(), end)
}
```

これは基本的に、`end` が `start` に等しいか、`end` が `start` の直接の後続から到達可能であれば、基本ブロック `end` は `start` から到達可能だ、という意味です。

CodeQL は、推移閉包も言語機能としてサポートしています。くだけた言い方をすると、述語 `P` の_推移閉包_は、`P` を 1 回以上繰り返して適用した結果です。`P` の反射推移閉包を考えると便利なこともあり、これは、述語 `P` を 0 回以上適用することに対応します。CodeQL は、この 2 つの構成をどちらも組み込みでサポートしています。`+` 演算子は述語を 1 回以上適用することを、`*` は述語を 0 回以上適用することを表します。例として、上で定義した述語 `isReachableFrom(start, end)` を、次のように推移閉包を使って書き直せます。

```mysql
predicate isReachableFrom(BasicBlock start, BasicBlock end) {
  end = start.getASuccessor*()
}
```

これは、`start` に `getASuccessor()` メソッドを 0 回以上適用して `end` を得られるなら、基本ブロック `end` は `start` から到達可能であるという事実を表します。この定義が、上の再帰的な定義と等価であることは、おそらく明らかでしょう。(`end` が `start` に等しい場合を除くには、上の例の `*` を `+` に置き換えます。)

### クエリのメタデータの追加

クエリのメタデータは、先頭のコメントの中に、次の構文で定義します。

```mysql
/**
 * @name <A short name>
 * @id <scope>/<query-name>
 * @description <A longer description>
 * @kind <The query type>
 * @tags <A list of tags>
 * @problem.severity <The severity of the issue>
 * @precision <The precision of the query>
 */
```

これは、CodeQL CLI が出力する SARIF を埋めるために使われ、また、VSCode や GitHub のコードスキャンなどのツールが、コードスキャンの結果をユーザーに表示するために使われます。`codeql query run` でクエリを実行するだけなら、クエリのメタデータを追加することは厳密には必須ではありませんが、どのクエリにも、次のメタデータのフィールドを必ず含めるのがよい習慣です。

- **name**: クエリが見つける問題を識別する短い文字列にします。SARIF の出力や GitHub のコードスキャンの結果で、問題を説明するために使われます。
- **id**: クエリの一意の識別子にします。小文字、数字、`/`、`-` を含められます。
- **description**: クエリが見つける問題の、より長い説明(通常は数文)です。
- **kind**: クエリの種類です。通常のクエリでは `problem`、[パスクエリ](https://codeql.github.com/docs/writing-codeql-queries/creating-path-queries/)では `path-problem` のどちらかを指定します。
- **tags**: 小文字のタグを、スペースで区切って並べたものです。タグにもとづいてクエリスイートを定義するために使えます。やり方の詳細は、[公式ドキュメント](https://docs.github.com/en/code-security/codeql-cli/using-the-advanced-functionality-of-the-codeql-cli/creating-codeql-query-suites#filtering-the-queries-in-a-query-suite)を参照してください。
- **problem.severity**: 見つかった問題の重大度を表すフィールドで、VSCode や GitHub のコードスキャンなどのツールに表示されます。値は、`error`、`warning`、`recommendation` のいずれかにします。
- **precision**: クエリが生む誤検知の全体的な確率を示すフィールドで、コードスキャンの結果を絞り込むために使えます。`low`、`medium`、`high`、`very-high` のいずれかにします。

{{< hint warning >}}
クエリを `codeql database analyze` で実行する場合や、[GitHub のコードスキャン]({{< relref "20-ci#code-scanning-with-custom-queries" >}})のワークフローの一部として実行する場合は、クエリの種類が出力形式も制限することに注意してください。

`problem` クエリでは、select 文の出力は、見つかった問題の場所を示す `Location` と、それに続く、見つかった問題を説明する `string` で与える必要があります。`path-problem` クエリでは、出力は、シンクを表す `DataFlow::Node`、それに続くソースとシンクを表す 2 つの `DataFlow::PathNode` のインスタンス、さらに続く、根本の問題を説明する `string` で与える必要があります。
{{< /hint >}}

### CodeQL の標準ライブラリ

CodeQL の標準ライブラリは言語ごとに異なり、ライブラリの API 間には大きな違いがあります。独自のクエリを開発したい方は、対象の言語の API ドキュメントを参照することをお勧めします。

- [Go 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/go/)
- [C# 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/csharp/)
- [Ruby 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/ruby/)
- [Swift 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/swift/)
- [Python 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/python/)
- [C と C++ 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/cpp/)
- [Java と Kotlin 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/java/)
- [JavaScript と TypeScript 向けの CodeQL 標準ライブラリ](https://codeql.github.com/codeql-standard-libraries/javascript/)

## 独自クエリの実行

上のクエリを既存のデータベースに対して実行するには、クエリをクエリパックのルートディレクトリ(つまり `qlpack.yml` ファイルがあるディレクトリ)の下に、`MemcpyCall.ql` というファイルとして保存します。これで、次のように `codeql query run` コマンドでクエリを実行できます。

```sh
codeql query run --database codeql.db -- path/to/MemcpyCall.ql
```

クエリを実行すると、コードベース内のすべての `memcpy` の呼び出しについて、その場所(つまり、絶対パス、行番号、列番号)と、関数に渡された第 1 引数が一覧で表示されます。

## 独自クエリの単体テスト {#unit-testing-custom-queries}

CodeQL は、独自のクエリが期待どおりに動くことを確かめるための、単純なテストフレームワークを提供しています。CodeQL のテストは、独自の `qlpack.yml` ファイルで定義される、別のテストパックの下にまとめる必要があります。

```yml
name: <scope>/<name-test>
version: 0.0.1
dependencies:
  <codeql-query-pack-to-test>: "*"
extractor: <language-of-code-to-test>
```

テストしたいクエリごとに、テストパックのルートディレクトリの下にサブディレクトリを作ります。サブディレクトリの名前には、クエリの名前を使い回すのがよい習慣です。つまり、`MemcpyCall.ql` クエリの単体テストを作りたいなら、テストのディレクトリを `MemcpyCall` と名付けます。テストのディレクトリには、次の 3 つのファイルを置きます。

- `test.c`: クエリが見つけるコードのパターンを含むソースファイル
- `MemcpyCall.qlref`: テストするクエリの場所を含む[テキストファイル](https://docs.github.com/en/code-security/codeql-cli/using-the-advanced-functionality-of-the-codeql-cli/query-reference-files)
- `MemcpyCall.expected`: ソースファイルに対してクエリを実行したときに期待される出力を含むテキストファイル

ソースファイルは、外部の依存関係なしに、問題なくビルドできる必要があります。この要件が問題になるのは、主に C/C++ のクエリです。`#include` したいライブラリについて、`extern` 宣言を含むスタブファイルを作る必要があります。例は、[私たちのテスト](https://github.com/trailofbits/codeql-queries/blob/d994c7ca05dab30fe195555ef6943f9d51ec38df/cpp/test/query-tests/security/CStrnFinder/test.c#L1)を参照してください。

クエリをテストするには、次のコマンドを実行します。

```sh
codeql test run -- path/to/test/pack/root/directory
```

これにより、テストパック内のすべてのテストが実行されます。1 つのクエリだけをテストするには、`codeql run test` を実行するときに、対応するテストのディレクトリを指定します。

`MemcpyCall.expected` ファイルがない場合や、クエリが生成した実際の出力と一致しない場合は、エラーが発生し、CodeQL の実際の出力を含む `MemcpyCall.actual` ファイルが作られます。これにより、予期しない動作を調べられるだけでなく、最初の `MemcpyCall.expected` ファイルを生成する便利な方法にもなります。`MemcpyCall.expected` ファイルがない状態でテストを実行して、`MemcpyCall.actual` を生成します。出力が正しいことを確認し、正しければ、`MemcpyCall.actual` を `MemcpyCall.expected` に名前変更します。

CodeQL のクエリのテストについて詳しくは、[公式ドキュメント](https://docs.github.com/en/code-security/codeql-cli/using-the-advanced-functionality-of-the-codeql-cli/testing-custom-queries)を参照してください。

## CI での独自クエリのテスト

### GitHub Actions

[`trailofbits/setup-codeql`](https://github.com/trailofbits/setup-codeql) ワークフローを使うと、GitHub Actions で独自の CodeQL クエリをテストできます。

```yml
name: Test CodeQL queries

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v6
      - uses: trailofbits/setup-codeql@main
      - run: codeql test run --threads=0 /path/to/query-tests
      - run: codeql query format --check-only /path/to/query.ql
```

このワークフローは、クエリの抽出とコンパイル、およびパックの依存関係のインストールをキャッシュすることで、2 回目以降の実行も高速にします。

## CodeQL のエディタ対応

CodeQL CLI には、Language Server Protocol(LSP)のサーバーが含まれています。これを使うと、LSP に対応したエディタで、コードのナビゲーションと診断を利用できます。公式の Tree-sitter リポジトリには、[CodeQL 用の Tree-sitter 文法](https://github.com/tree-sitter/tree-sitter-ql)もあり、Helix などのエディタでシンタックスハイライトを提供するために使えます。さらに、[VSCode](https://marketplace.visualstudio.com/items?itemName=GitHub.vscode-codeql) と [Neovim](https://github.com/pwntester/codeql.nvim) 向けのプラグインがあり、LSP への対応とシンタックスハイライトを提供し、エディタから直接クエリを実行したり、問題をたどったりできます。

### VSCode 拡張機能での独自クエリの実行 {#running-custom-queries-using-the-vscode-extension}

VSCode の CodeQL 拡張機能は、クエリを実行する便利な方法を提供し、独自のクエリの結果を可視化してたどることもできます。この拡張機能では、「CodeQL: Quick Query」コマンドで、既存のデータベースに対して単一のクエリを実行することもできます。

新しいクエリを書くときは、VSCode 拡張機能を使って、選んだプログラミング言語にもとづく `qlpack.yml` ファイルを自動で設定できます。また、Queries タブにある「Create one to get started」ボタンから、クエリの雛形も作れます。

{{< figure src="/generate-codeql-query.png" width="500"
alt="Create a skeleton query using the Queries tab in the VSCode extension" >}}

### VSCode 拡張機能での独自クエリのデバッグ

VSCode 拡張機能では、データベース内の各 AST ノードについて、抽象構文木(AST)を表示することもできます。この機能は、独自のクエリをデバッグするときに非常に役立ちます。

ノードの AST ビューを表示するには、まず使用する CodeQL データベースを設定し、そのあとで、データベースのソースコードをワークスペースに追加する必要があります。手順は次のとおりです。

1. **CodeQL データベースを設定する:** CodeQL 拡張機能のビューに移動し、状況に応じて「Choose Database from Folder」か「Choose Database from Archive」のどちらかで、CodeQL データベースを設定します。
2. **ソースコードをワークスペースに追加する:** 「Databases」ビューでデータベース名を右クリックし、「Add Database Source to Workspace」を選びます。これにより、データベース内の各ソースファイルのコピーが、ファイルピッカーの `[<codeql-database-name> source archive]` の下に追加されます。

   {{< hint warning >}}
   このようにソースコードをワークスペースに追加すると、拡張機能が、前の手順で選んだデータベースを忘れてしまうことがあります。そうなった場合は、上と同じ手順で、データベースを設定し直すだけです。
   {{< /hint >}}
3. **AST を表示する:** データベース内の AST ノードの AST を表示するには、_データベースのソースディレクトリの中_にある、対応するソースファイルに移動します。そのうえで、「CodeQL: View AST」コマンドを使って、ファイルの AST を表示します。各ノードは、対応する CodeQL の型とともに表示され、個々のノードをクリックして、木をたどれます。

{{< figure src="/view-codeql-ast.png" alt="An example of the CodeQL AST in VSCode" >}}
