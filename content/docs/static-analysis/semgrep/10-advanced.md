---
title: "高度な使い方"
slug: advanced
summary: "この節では、新しいルールの作り方を含む、Semgrep の高度な使い方を説明します。"
weight: 10
---

# 高度な使い方

## Semgrep でプロジェクトのコード (の一部) を無視する

Semgrep は、内容を解析するのではなく、ファイルの拡張子でプログラミング言語を判定します。
標準的でない拡張子のファイルをスキャンするときに、Semgrep に使わせたい言語を指定するには、`--scan-unknown-extensions` フラグと `--lang` フラグを使います。例:

```sh
semgrep --config /path/to/your/config --lang python --scan-unknown-extensions /path/to/your/file.xyz
```

この例では、`.xyz` という拡張子は Python ファイルの標準的な拡張子ではありませんが、Semgrep は `/path/to/your/file.xyz` ファイルを Python ファイルとしてスキャンします。

拡張子が標準的でない場合でも、特定の言語に対して Semgrep を使いたいときに制限を回避する方法については、GitHub の issue [Allow user to specify file extensions for languages #3090](https://github.com/semgrep/semgrep/issues/3090) も参照してください。

### ファイルとディレクトリ

- 既定では、Semgrep は既定の
[.semgrepignore](https://github.com/semgrep/semgrep/blob/develop/src/targeting/default.semgrepignore) ファイルに従います。
- リポジトリに `.gitignore` ファイルがあれば、Semgrep はそれも参照します。
- 2 つのファイルの内容が衝突する場合は、`.semgrepignore` ファイルが優先されます。つまり、
  `.gitignore` ファイルが含めているファイルを `.semgrepignore` ファイルが除外していれば、Semgrep はそのファイルを解析しません。

スキャンを始める前に、プロジェクトのディレクトリにあるファイルとディレクトリを確認することをお勧めします。
一部のパスは、既定で除外されていることに注意してください。サードパーティのライブラリや単体テストをスキャンに含めるなど、既定の除外の動作を変えたい場合は、独自の `.semgrepignore` ファイルを作成できます。

### コードの一部を除外する

Semgrep が誤ったコードパターンを指摘しないようにするには、パターンに一致する行の直前の行か、その行自体に、コメントを入れます (例: `// nosemgrep: rule-id`)。`//` と `nosemgrep` の間にスペースを入れることが重要です。

ベストプラクティスとして、次の点を心がけてください。

- 一般的な `// nosemgrep` コメントですべてのルールを無効にするのではなく、コメントでは特定の検出結果だけを除外する。
- ルールを無効にした理由を説明するか、リスクを受け入れる判断の根拠を示す。
- 誤検知に出会い、Semgrep のルールを無視したい場合は、Semgrep の開発チームか、そのルールを担当する社内の開発チームにフィードバックする。これは、ルールの精度を上げ、今後の誤検知の可能性を減らすのに役立ちます。

特定のルールについて `nosemgrep` でコードブロックを無視する方法の詳細は、
[コードの無視に関する Semgrep のドキュメント](https://semgrep.dev/docs/ignoring-files-folders-code/#ignoring-code-through-nosemgrep)を参照してください。

## 独自のルールを書く

Semgrep には構築済みのルールのライブラリがありますが、独自のルールを作ると、対象のコードベースと要件に合わせて、セキュリティテストを大きく強化できます。ただし、適切な指針と理解がなければ、効果的な Semgrep ルールを作るのは難しいことがあります。この節では、質の高い Semgrep ルールを作るために欠かせない知識と技術を紹介します。ルール言語の構文、効果的なパターンの作り方、エッジケースの扱い方、強力な独自 Semgrep ルールの作り方を学びます。これは、潜在的なセキュリティ脆弱性を早い段階で検出するのに役立ち、最終的にはテストの工程を改善します。

### 独自ルールの例

独自ルールを作る出発点として、次のスキーマで `custom_rule.yaml` ファイルを作成します。

```yaml {linenos=inline}
rules:
  - id: rule-id
    languages: [go]
    message: Some message
    severity: ERROR # INFO / WARNING / ERROR
    pattern: test(...)
```

### 独自ルールを実行する

- 上のルールを単一のファイルとして実行するには、次のコマンドを使います。

```shell
semgrep --config custom_rule.yaml
```

- ディレクトリ内のルールの集まりを実行するには、次のようにします。

```shell
semgrep --config path/
```

### 独自ルールを書くための基本

独自の Semgrep ルールを書き始めるには、いくつかの重要な概念とツールを理解することが大切です。

1. **Semgrep の構文に慣れる**: まず、公式の [Learn Semgrep Syntax](https://semgrep.dev/learn) のページを見てください。Semgrep のルールを書くための基本を、網羅的に説明しています。
1. **言語ごとのパターンの例を参照する**: 特定のプログラミング言語に合わせた例は、[Semgrep Pattern Examples by Language](https://semgrep.dev/embed/cheatsheet) を参照してください。
1. **Semgrep Playground を使う**: [Semgrep Playground](https://semgrep.dev/playground/new) は、ルールを書いてテストするのに便利なオンラインのツールです。ただし、Playground を使うときは、次の点を考慮することが重要です。
{{< hint danger >}}**プライバシーの懸念に注意してください**: Semgrep Playground では、ローカルのマシンにソフトウェアをダウンロードやインストールせずに、コードを試せます。このプラットフォームはルールのテストやデバッグに役立ちますが、スキャンのために送信したコードに含まれるパスワード、API キー、その他の秘密情報が漏れる可能性があります。
      機密性の高いコードには、適切なセキュリティとプライバシーの管理がされたローカルの開発環境を、必ず使ってください。{{< /hint >}}
    - **`simple mode` を使う**: Semgrep Playground の simple mode では、ルールのパターンを簡単に組み合わせられます。
    - **`Share` ボタンを使う**: Share ボタンで、ルールとテストコードをほかの人と共有できます。
    - **テストコードにテストを追加する**: Semgrep Playground で作業しながらルールの有効性を評価するために、[テスト](https://semgrep.dev/docs/writing-rules/testing-rules/)
      (例: `# ruleid: <id>`) をテストコードに入れます
      ([例](https://semgrep.dev/s/ezxE)を参照)。
    - **コメントの制限に注意する**: Semgrep Playground は、リンクを共有したり、ルールを「フォーク」(Ctrl+S) したりするときに、コメントを保持しません。詳細は、この [GitHub の issue](https://github.com/semgrep/semgrep/issues/7120) を参照してください。

### 構成要素

#### 省略記号 (`...`)

{{< hint info >}}**目的**: 省略記号 (`...`) は、0 個以上の引数、文、パラメータなどに一致させるために使い、パターンマッチをより柔軟にします。
{{< /hint >}}

Python 用のルールの例を示します。

```yaml {linenos=inline}
rules:
  - id: rule-id
    languages: [Python]
    message: Some message
    severity: INFO
    pattern: requests.get(..., verify=False, ...)
```

ここで、`verify=False` 引数の前後にある省略記号により、パターンは、`verify` パラメータの前後にある任意の数の引数に一致します。これにより、`verify=False` 引数さえあれば、さまざまな引数の組み合わせの関数呼び出しに、パターンを一致させられます。

このパターンは、次のコード片に一致します。

```python {linenos=inline, hl_lines=[1,3,6]}
requests.get(verify=False, url=URL)
requests.post(verify=False, url=URL)
requests.get(URL, verify=False, timeout=3)
requests.head()
requests.get(URL)
requests.get(URL, verify=False)
```

2 つ目の例では、省略記号を使って、`if` 文のあとに、その `if` ブロック内の `return` 文のあとにある不要な `else` ブロックが続く場合に一致するパターンを作ります。

Python 用の `unnecessary-if-else-pattern` ルールを次に示します。

```yaml {linenos=inline}
rules:
  - id: unnecessary-if-else-pattern
    languages: [Python]
    message: Unnecessary else after return $X
    severity: INFO
    pattern: |
      if ...:
        return ...
      else:
        ...
```

では、パターンの構成要素を順に見ていきましょう。

1. `if ...:`: パターンのこの部分は、テストされている条件にかかわらず、任意の `if` 文に一致します。
`if` 文の中の省略記号はワイルドカードで、条件として使われる任意の式やコード構造に一致します。
この柔軟さにより、このパターンは、さまざまな条件の幅広い `if` 文を検出できます。
2. `return ...`: 一致した `if` ブロックの中で、`return` 文のあとに省略記号があります。このワイルドカードは、返される任意の式や値に一致します。これにより、このパターンは、`return True`、`return False`、`return x`、`return calculate_result()` のように、さまざまな値や式を返す `return` 文を検出できます。
3. `else` ブロック内の `...`: `else` ブロックの省略記号は、任意の数の文に一致するワイルドカードです。

このパターンは、次のコード片に一致します。

```py {linenos=inline}
if a > b:
  return True
else:
  print("a is not greater than b")
```

Semgrep のルールに省略記号 (`...`) を含めると、コード構造のばらつきを考慮した、より柔軟で網羅的なパターンを作れます。

#### メタ変数

{{< hint info >}}**目的**: メタ変数は、特定のコードのスコープにわたって、値に一致させ、追跡するために使います。
ドル記号に続く大文字の文字で表します (例: `$X`、`$Y`、`$COND`)。{{< /hint >}}

Golang でのパターンの例を示します。

```yaml
pattern: $X.($TYPE)
```

メタ変数 `$X` は、次のものに一致します。

```go {linenos=inline, hl_lines=[1,2]}
msg, ok := m.(*MsgDonate) // $X = m
p := val.(types.Pool) // $X = val
x := val
msg, ok = m
```

メタ変数は、Semgrep ルールの出力メッセージに埋め込むこともできます。
たとえば、次のルールを考えてみましょう。

```yaml {linenos=inline}
rules:
  - id: metavariable-example-rule
    patterns:
      - pattern: func $X(...) { ... }
    message: Found $X function
    languages: [golang]
    severity: WARNING
```

次のコードに対して、

```go {linenos=inline}
func test123(input string) {
    fmt.Println("test")
}
```

Semgrep の出力に、次のように `Found test123 function` というメッセージが返されます。

```shell
$ semgrep -f rule.yml
# (...)
     metavariable-example-rule
        Found test123 function

          1┆ func test123(input string) {
          2┆     fmt.Println("test")
          3┆ }
```

メタ変数は、あとのパターンマッチや検証に使える値を取り込むことで、より動的で汎用的な Semgrep ルールを作る助けになります。

##### メタ変数を活用する

メタ変数にはさまざまな使い方があり、Semgrep のルールを、コード解析時により動的で適応的にします。よくある用途には、次のものがあります。

1. **変数名に一致させる**: メタ変数を使うと、コード内の変数名に一致させられるため、ルールを柔軟にして、さまざまな状況に適用できます。例:

    ```yaml
    pattern: $X := $Y
    ```

    このパターンは、`a := b` や `result := calculation()` のような代入に一致します。

2. **関数呼び出しを取り込む**: メタ変数を使うと、関数呼び出しとその引数を取り込めます。
    これは、安全でない可能性のある関数や非推奨の関数を検出するのに役立ちます。例:

    ```yaml
    pattern: $FUNC($ARG)
    ```

    このパターンは、`dangerousFunc(input)` や `deprecatedFunc(arg1, arg2)` のような関数呼び出しに一致します。

3. **制御構造に一致させる**: メタ変数は、ループや条件分岐などの特定の制御構造を、特にその構造の中で使われる式に注目して、特定する助けになります。例:

    ```yaml
    pattern: for $INDEX := $INIT; $COND; $UPDATE { ... }
    ```

    このパターンは、`for i := 0; i < 10; i++ { ... }` のような for ループに一致します。

4. **コードパターンを比較する**: メタ変数を使うと、コードの異なる部分を比較して、一貫性を確かめたり、潜在的なバグを防いだりできます。たとえば、`if-else` 文の両方の分岐で同じ代入が行われている場合を検出できます。

    ```yaml
    pattern: if $COND { $X = $Y } else { $X = $Y }
    ```

    このパターンは、次のようなコードに一致します。

    ```go {linenos=inline}
    if someCondition {
        x = y
    } else {
        x = y
    }
    ```

5. **複数行にまたがるパターンを特定する**: メタ変数を使うと、複数行のコードにわたって値に一致させ、追跡できます。これにより、複数の文にまたがるパターンを検出できます。例:

    ```yaml
    pattern: |
      $VAR1 := $EXPR1
      $VAR2 := $VAR1
    ```

    このパターンは、次のようなコードに一致します。

    ```go {linenos=inline}
    a := b + c
    d := a
    ```

まとめると、メタ変数は、動的で適応的な Semgrep ルールを作る強力な手段です。コードのスコープにわたって値を取り込んで追跡できるため、複雑なパターンを特定でき、開発者やセキュリティの専門家に役立つ出力メッセージを提供できます。

#### ネストしたメタ変数

{{< hint info >}}**目的**: ネストしたメタ変数を使うと、メタ変数を含むパターンに一致させられます。そのメタ変数は、さらに別のメタ変数を含み、一定の条件を満たしている必要があります。{{< /hint >}}

ルールの例を示します。

```yaml {linenos=inline}
rules:
  - id: metavariable-pattern-nest
    languages: [python]
    message: substraction in foo(bar(...))
    patterns:
      - pattern: foo($X, ...)
      # First metavariable-pattern
      - metavariable-pattern:
          metavariable: $X
          patterns:
            - pattern: bar($Y)
            # Nested metavariable pattern
            - metavariable-pattern:
                metavariable: $Y
                patterns:
                  - pattern: ... - ...
    severity: WARNING
```

このルールは、次の Python コードに一致します。

```python {linenos=inline}
foo(bar(1-2))
foo(bar(bar(1-2)))
```

ネストしたメタ変数を使うと、複数のメタ変数の間の関係を定義できるため、Semgrep のルールで、より複雑で正確なパターンマッチができます。

#### `metavariable-pattern` による、複数言語が混在するファイルのスキャン

{{< hint info >}}**目的**: 1 つのファイルの中にある、異なる言語にまたがるパターンに一致させる
(例: HTML に埋め込まれた JavaScript)。{{< /hint >}}

例: HTML ファイル内で使われている JavaScript の [eval](https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Global_Objects/eval) 関数を、すべて見つけます ([例](https://semgrep.dev/s/W9by))。

```yaml {linenos=inline}
rules:
  - id: metavariable-pattern-nest
    languages: [html]
    message: eval in JS
    patterns:
      - pattern: <script ...>$Y</script>
      - metavariable-pattern:
          metavariable: $Y
          language: javascript
          patterns:
            - pattern: eval(...)
    severity: WARNING
```

このルールは、次の HTML コードに一致します。

```html {linenos=inline}
<script>
    console.log('test123');
    eval(1+1);
</script>
```

`metavariable-pattern` を使うと、複数の言語が混在するファイルで、言語をまたいだパターンマッチができ、混在言語のファイル内の特定のコードパターンを特定できます。

#### `metavariable-pattern` と `pattern-either` を使う

{{< hint info >}}**目的**: メタ変数に一致しうる、複数の代替パターンを指定する。{{< /hint >}}

例: 変数宣言が、いくつかの特定の型のどれかを使っている箇所を指摘します
([例](https://semgrep.dev/s/J0zk)
/
[trailofbits.go.string-to-int-signedness-cast.string-to-int-signedness-cast](https://semgrep.dev/playground/r/trailofbits.go.string-to-int-signedness-cast.string-to-int-signedness-cast?editorMode=advanced)
ルール)。

```yaml {linenos=inline}
rules:
  - id: metavariable-pattern-multiple-or
    languages: [go]
    message: xyz
    patterns:
      - pattern: var $A $TYPE = ...
      - metavariable-pattern:
          metavariable: $TYPE
          pattern-either:
            - pattern: uint8
            - pattern: uint16
            - pattern: uint32
            - pattern: int8
            - pattern: int16
            - pattern: int32
    severity: WARNING
```

このルールは、次の Go コードに一致します。

```go {linenos=inline, hl_lines=["1-6"]}
var a uint8 = 255
var b uint16 = 65535
var c uint32 = 4294967295
var d int8 = -128
var e int16 = -32768
var f int32 = -2147483648
var g string = "xyz"
```

`metavariable-pattern` と `pattern-either` を組み合わせると、指定した条件のどれかを満たす場合に `metavariable` に一致する Semgrep ルールを作れます。

#### Metavariable-pattern と patterns

{{< hint info >}}**目的**: `metavariable-pattern` と `patterns` を使って、メタ変数 `$X` が_すべての_条件 (`patterns`) を満たす箇所を指摘します ([例](https://semgrep.dev/s/BJqv) / [lxml-in-pandas ルール](https://semgrep.dev/playground/r/trailofbits.python.lxml-in-pandas.lxml-in-pandas?editorMode=advanced))
{{< /hint >}}

ルールの例を示します。

```yaml {linenos=inline}
rules:
  - id: metavariable-pattern-and-patterns
    languages:
      - go
    message: xyz1
    patterns:
      - pattern: var $A $TYPE = $Z
      - metavariable-pattern:
          metavariable: $Z
          patterns:
            - pattern-not: |
                  -128
            - pattern-not: |
                  -32768
    severity: WARNING
```

このルールは、次の Go コードに一致します。

```go {linenos=inline, hl_lines=[1,3]}
var b uint16 = 65535
var d int8 = -128
var c uint32 = 4294967295
var e int16 = -32768
```

#### 定数伝播

Semgrep の定数伝播とは、`metavariable` が特定の値や関係を持つ箇所に一致させる処理のことです。

##### メタ変数が特定の値を持つ箇所に一致させる

{{< hint info >}}**目的**: メタ変数が特定の値や関係を持つ箇所に一致させるには、
`metavariable-comparison` キーを使います。{{< /hint >}}

例: 変数 `$X` が `1337` より大きい場合に一致させます ([例](https://semgrep.dev/s/LqeL))。

```yaml {linenos=inline}
rules:
  - id: metavariable-comparison
    languages: [python]
    message: $X is higher than 1337
    patterns:
      - pattern: function($X)
      - metavariable-comparison: # Match when $X > 1337
          metavariable: $X
          comparison: $X > 1337
    severity: WARNING
```

このルールは、次の Python コードに一致します。

```python {linenos=inline, hl_lines=["2-3"]}
n = 1339
function(n) # Match (n > 1337)
function(1338) # Match (constant > 1337)
function(123)
```

##### 特定のメタ変数を比較する

{{< hint info >}}**目的**: 特定のメタ変数を比較する。{{< /hint >}}

例: 1 番目の引数が 2 番目の引数より小さい関数に一致させます ([例](https://semgrep.dev/s/dYnd))。

```yaml {linenos=inline}
rules:
  - id: metavariable-comparison-rule
    patterns:
      - pattern: f($A, $B)
      - metavariable-comparison:
          comparison: int($A) < int($B)
          metavariable: $A
    message: $A < $B
    languages: [python]
    severity: WARNING
```

このルールは、次の Python コードに一致します。

```python {linenos=inline,hl_lines=["1-2"]}
f(1,2)
f(2,3)
f(4,3)
f(12312,1)
```

#### ディープ式演算子

{{< hint info >}}**目的**: コード内の深くネストした式に一致させる。{{< /hint >}}
ディープ式演算子は、条件文、ループ、関数呼び出しのような複雑な構造の奥に埋もれた特定のパターンを特定したいときに便利です。ディープ式演算子を使うと、コード構造の中でどれだけ深い位置にあっても、特定のコードパターンを対象にするルールを作れます。

ディープ式演算子は `<... ...>` で表します。開きと閉じの省略記号の間にある、任意のコード構造に一致するワイルドカードとして働きます。ディープ式演算子を使えば、ネストの深さにかかわらずパターンに一致する Semgrep ルールを作れます。

**例**: `if` 文の中にネストした関数呼び出しに一致させます ([例](https://semgrep.dev/s/2Qv8))。

`if` 文の中にある特定の関数呼び出し (例: `user.is_admin()`) に、どれだけ深くネストしていても一致させたいとします。

```yaml {linenos=inline}
rules:
- id: deep-expression-example
  pattern: |
      if <... user.is_admin() ...>:
        print(...)
  message: if statement with is_admin() check
  languages: [python]
  severity: WARNING
```

このルールは、次の Python コードに一致します。

```python {linenos=inline}
if user.authenticated() and user.is_admin() and user.has_group(gid):
    print("hello")
```

#### `pattern-inside` と `pattern-not-inside` を理解する

##### `pattern-inside` を使う

`pattern-inside` を使うと、関数やクラスの定義、ループ、条件ブロックのような特定のコード構造の**中に**ある場合にだけ、パターンに一致するルールを作れます。

`pattern-inside` を使って、機密性の高い関数がループの中で呼び出されている場合を検出する例を示します。

```yaml {linenos=inline}
rules:
- id: sensitive_function_in_loop
  languages:
    - python
  message: "Sensitive function called inside a loop"
  severity: WARNING
  patterns:
    - pattern-inside: |
        for ... in ...:
            ...
    - pattern: |
        sensitive_function(...)
```

この例では、`pattern-inside` 演算子で Python の任意の `for` ループに一致させ、2 つ目のパターンで `sensitive_function()` の呼び出しに一致させています。ルールが発動するのは、両方のパターンに一致したとき、つまり `sensitive_function` がループの**中で**呼び出されているときだけです。

`sensitive_function_in_loop` ルールを発動させる Python コードの例を示します。

```python {linenos=inline, hl_lines=[10]}
def sensitive_function(data):
    # Process sensitive data
    pass

def main():
    data_list = ['data1', 'data2', 'data3']

    for data in data_list:
        # Call to sensitive_function is inside a loop
        sensitive_function(data)

def second(data):
    sensitive_function(data)
```

##### `pattern-not-inside` を使う

`pattern-not-inside` は `pattern-inside` の反対で、指定した文脈の中に**ない**場合にだけ、パターンに一致させるために使います。この演算子を使うと、コードの特定の部分を解析から除外でき、ルールをさらに絞り込んで、誤検知を減らせます。

たとえば、`pattern-not-inside` を使うと、`print_debug()` 関数の呼び出しが `if debug:` ブロックの外で行われている場合を検出できます。

```yaml {linenos=inline}
rules:
- id: print_debug_outside_debug_block
  languages:
    - python
  message: "print_debug() should be called inside a 'if debug:' block"
  severity: WARNING
  patterns:
    - pattern-not-inside: |
        if debug:
            ...
    - pattern: |
        print_debug(...)
```

このルールの使い方を示す Python コードの例を次に示します。

```python {linenos=inline, hl_lines=[11]}
debug = True

def print_debug(msg):
    print("DEBUG:", msg)

def correct_usage():
    if debug:
        print_debug("This is a debug message inside a 'if debug:' block")

def incorrect_usage():
    print_debug("This is a debug message outside a 'if debug:' block")

def main():
    correct_usage()
    incorrect_usage()
```

##### `pattern-inside` と `pattern-not-inside` を組み合わせる

場合によっては、`pattern-inside` と `pattern-not-inside` の両方の演算子を使って、特定のパターンがある文脈の中にはあるが、別の文脈の中にはない場合を捉えるルールを作りたいことがあります。

**例**: 関数内にあるが `main()` 内にはない `print()` 呼び出しを検出する。

`print()` の呼び出しを `main()` 関数の中でだけ許可し、ほかのどの関数でも許可しないというルールを徹底したいとします。これは、`pattern-inside` と `pattern-not-inside` の演算子を組み合わせたルールで実現できます。

```yaml {linenos=inline}
rules:
- id: print_calls_outside_main
  languages:
    - python
  message: "print() calls should only be inside the main() function"
  severity: WARNING
  patterns:
    - pattern-inside: |
        def $X(...):
            ...
    - pattern-not-inside: |
        def main(...):
            ...
    - pattern: |
        print(...)
```

この例では、`pattern-inside` 演算子が任意の関数定義に一致し、`pattern-not-inside` 演算子が `main()` 関数を確実に除外します。
最後のパターンは `print()` 関数の呼び出しに一致します。ルールが発動するのは、`main()` 以外の関数の中で `print()` の呼び出しが見つかったときだけです。

`print_calls_outside_main` ルールを発動させる Python コードの例を示します。

```python {linenos=inline, hl_lines=[3,11]}
def sample_function():
    # print() call inside a function other than main()
    print("This is a sample function")

def main():
    print("This is the main function")
    sample_function()

def other_function():
    some_function()
    print("XYZ")
```

#### テイントモード

テイントモードは、あるデータが 1 つの場所から別の場所へ流れる様子を追跡できる、Semgrep の強力な機能です。
テイントモードを使うと、次のことができます。

1) **複数の変数にわたるデータの流れを追跡する:** テイントモードでは、データが異なる変数、関数、コンポーネントの間をどう移動するかをたどれます。安全でない流れの経路 (たとえば、特定のサニタイザが使われていない状況) も簡単に特定できます。
2) **インジェクションの脆弱性を見つける:** テイントモードは、SQL インジェクション、コマンドインジェクション、XSS 攻撃などの、インジェクションの脆弱性を特定するのに特に便利です。
3) **単純で壊れにくい Semgrep ルールを書く:** テイントモードを使うと、`if` 文やループなどの構造にネストした特定のコードパターンに強い、Semgrep ルールを簡単に書けます。

テイントモードを使うには、独自の Semgrep ルールに、`mode: taint` を設定し、`pattern-sources`/`pattern-sinks` フィールドを指定する必要があります。

この[例](https://semgrep.dev/s/el3X)を見てください。

```yaml {linenos=inline}
rules:
  - id: taint-tracking-example1
    mode: taint
    pattern-sources:
      - pattern: getData()
    pattern-sinks:
      - pattern: printToUser(...)
    message: data flows from getData to printToUser
    languages: [python]
    severity: WARNING
```

必要に応じて、Semgrep ルールに追加のフィールドを使うと、テイント解析をさらに絞り込めます。

- `pattern-propagators`: このフィールドでは、汚染されたデータを伝播する関数やメソッドを指定できます
([例](https://semgrep.dev/s/7Nrv))。詳細は、
[副作用によるサニタイザ](https://semgrep.dev/docs/writing-rules/data-flow/taint-mode/#sanitizers-by-side-effect)も参照してください。
- `pattern-sanitizers`: このフィールドでは、汚染されたデータをサニタイズする関数やメソッドを指定できます。
詳細は、[テイントモードのドキュメント](https://semgrep.dev/docs/writing-rules/data-flow/taint-mode/#propagators)を参照してください。

### パターンを組み合わせる

Semgrep のルールを書いていると、1 つのパターン (例: `pattern: evil_function(...)`) では、検出したい動作を捉えきれない状況に出会うことがあります。そのような場合は、次のどれかを使って、パターンを組み合わせられます。

- `patterns`: この方法は、複数のパターンを論理 AND (&&) で組み合わせます。つまり、ルールが発動するには、すべてのパターンに一致する必要があります。これは、複数の条件を同時に満たすコード片を検出したいときに便利です。
- `pattern-either`: この方法は、複数のパターンを論理 OR (||) で組み合わせます。つまり、どれかのパターンに一致すれば、ルールが発動します。これは、指定した条件のうち少なくとも 1 つを満たすコード片を検出したいときに便利です。

    2 つの安全でない関数 `insecure_function_1()` と `insecure_function_2()` の呼び出しを検出したいとします。
    これは、`pattern-either` 演算子で実現できます。

    ```yaml {linenos=inline}
    rules:
    - id: insecure_function_calls
      languages:
        - python
      message: "Call to an insecure function detected"
      severity: WARNING
      patterns:
        - pattern-either:
            - pattern: |
                insecure_function_1(...)
            - pattern: |
                insecure_function_2(...)
    ```

    この例では、`pattern-either` 演算子で、`insecure_function_1()` と `insecure_function_2()` のどちらかの呼び出しに一致させています。これらのパターンのどれかに一致すれば、ルールが発動します。

    `insecure_function_calls` ルールを発動させる Python コードの例を示します。

    ```yaml {linenos=inline, hl_lines=[9,12]}
    def insecure_function_1():
        print("Insecure function 1 called")

    def insecure_function_2():
        print("Insecure function 2 called")

    def main():
        # Call to insecure_function_1() triggers the rule
        insecure_function_1()

        # Call to insecure_function_2() also triggers the rule
        insecure_function_2()
    ```

- `pattern-regex`: これは、複数行モードの [PCRE](https://www.pcre.org/original/doc/html/pcrepattern.html) 互換のパターンでコードに一致させます。つまり、正規表現のパターンでコードに一致させます。

#### ルールの構文図

次の図は、ルールの関連するフィールド同士の関係を理解するのに役立ちます。ルールを書いているときは、[Semgrep Playground](https://semgrep.dev/playground/new) の advanced mode を使って、ルールをテストし、改良できます。Playground は、ルールのエラーを強調表示し、すぐにフィードバックを返してくれます。

{{< mermaid >}}
flowchart TB

Fields{Rule Fields} ---->|Only one is allowed| Required{Required}
click Fields "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional:~:text=Rule%20syntax-,Rule%20syntax,-TIP"
    Required ==> id
    click id "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional:~:text=Description-,id,-string"
    Required ==> message
    click message "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional:~:text=no%2Dunused%2Dvariable-,message,-string"
    Required ==> severity
    click severity "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional:~:text=Rule%20messages.-,severity,-string"
    Required ==> languages((languages))
    click languages "https://semgrep.dev/docs/writing-rules/rule-syntax/#language-extensions-and-tags"
    Required ===>|Only one is required| Pattern_Fields{Pattern Fields}
    click Pattern_Fields "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional:~:text=pattern*,in%20multiline%20mode"

click Required "https://semgrep.dev/docs/writing-rules/rule-syntax/#required"

Pattern_Fields ==> pattern
click pattern "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern"
Pattern_Fields ==> pattern-regex[pattern-regex]
click pattern-regex "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-regex"
Pattern_Fields ==> pattern-either((pattern-either))
click pattern-either "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-either"
Pattern_Fields ==> patterns((patterns))
click patterns "https://semgrep.dev/docs/writing-rules/rule-syntax/#patterns"
pattern-either -.-> pattern-regex
pattern-either -.-> pattern
pattern-either -.-> pattern-inside
click pattern-inside "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-inside"
pattern-either <-.-> patterns

patterns -.-> pattern-inside

patterns <-..-> metavariable-pattern{metavariable-pattern}
click metavariable-pattern "https://semgrep.dev/docs/writing-rules/rule-syntax/#metavariable-pattern"
    metavariable-pattern --> metavariable2[metavariable]
    metavariable-pattern -.-> language
    metavariable-pattern -.-> pattern
    metavariable-pattern -.-> pattern-either
    metavariable-pattern -.-> pattern-regex

patterns -.-> metavariable-regex{metavariable-regex}
click metavariable-regex "https://semgrep.dev/docs/writing-rules/rule-syntax/#metavariable-regex"
    metavariable-regex --> metavariable
    metavariable-regex --> regex

patterns -.-> metavariable-comparison{metavariable-comparison}
click metavariable-comparison "https://semgrep.dev/docs/writing-rules/rule-syntax/#metavariable-comparison"
    metavariable-comparison --> metavariable3[metavariable]
    metavariable-comparison --> comparison
    metavariable-comparison -.-> base
    metavariable-comparison -.-> strip

patterns -.-> pattern
patterns -.-> pattern-not
click pattern-not "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-not"
patterns -.-> pattern-not-inside
click pattern-not-inside "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-not-inside"
patterns -.-> pattern-not-regex
click pattern-not-regex "https://semgrep.dev/docs/writing-rules/rule-syntax/#pattern-not-regex"

Fields -.-> Optional{Optional}

Optional -.-> options(options)
Optional -.-> fix(fix)
Optional -.-> metadata(metadata)
Optional -.-> paths(paths)

click Optional "https://semgrep.dev/docs/writing-rules/rule-syntax/#optional"
click options "https://semgrep.dev/docs/writing-rules/rule-syntax/#options"
click fix "https://semgrep.dev/docs/writing-rules/rule-syntax/#fix"
click metadata "https://semgrep.dev/docs/writing-rules/rule-syntax/#metadata"
click paths "https://semgrep.dev/docs/writing-rules/rule-syntax/#paths"
{{< /mermaid >}}

**例 1**:
図を見ると、`pattern-either` フィールドと `pattern-not` フィールドは、直接つながっていません。
ただし、`patterns` フィールドを使えば組み合わせられます。このフィールドは、含まれるすべてのパターンに対して、論理 AND の演算を行います。

**例 2**:
たとえば、`pattern-either` で複数のパターンを論理 OR で組み合わせ、さらに `pattern-not` で特定のパターンを除外したい場合は、同じ `patterns` フィールドの下に両方を入れればできます。
その結果の組み合わせは、`pattern-either` フィールドに含まれるいずれかのパターンを満たし、かつ `pattern-not` で指定したパターンを除くコードにだけ、一致します。
ルールの例 [`exclude-when-using-secure-option`](https://semgrep.dev/s/vgob) を参照してください。

### 汎用パターンマッチ

サポートされていない言語や文脈でも、汎用パターンで一致させられます。
設定ファイルや XML などには `generic` 言語を使い、誤検知を減らすために、`paths` の `include` フィールドで特定の拡張子と組み合わせます。

たとえば、[`nsc-allows-plaintext-traffic`
ルール](https://semgrep.dev/playground/r/java.android.best-practice.network-security-config.nsc-allows-plaintext-traffic?editorMode=advanced)を見てください。このルールは、Android マニフェストの XML ファイルをスキャンして、設定ミスの可能性を探します。

```yaml {linenos=inline}
rules:
  - id: nsc-allows-plaintext-traffic
    languages: [generic]
    patterns:
      - pattern: |
          <base-config ... cleartextTrafficPermitted="true" ... >
      - pattern-not-inside: |
          <!-- ... -->
      - pattern-not-inside: >
          <network-security-config ... InsecureBaseConfiguration ... > ... ...
          ... ... ... ... ... ... ... ... </network-security-config>
    severity: INFO
    paths:
      include:
        - "*.xml"
```

### メタデータ

メタデータのフィールドは、ルールに追加の情報を付けられる Semgrep の機能です。
ルールにメタデータのフィールドを含めると、問題の対処について、開発者により多くの文脈と指針を示せます。
この情報には、ルールの重大度、推奨される修正方法、作成者の連絡先などの詳細を入れられます。
メタデータを含めると、ルールに出会う開発者にとって、ルールをより有益で、行動につなげやすいものにできます。
これは、開発者が優先順位を付けて、問題をより効率的に修正する助けになり、最終的にコードベース全体のセキュリティを高めます。

開発者に文脈と指針を示すほかにも、組織が Semgrep のメタデータを使いたくなる理由がいくつかあります。

1. **標準化。** 組織のすべての Semgrep ルールで、メタデータのフィールドを一貫して使うと、どのルールに出会っても、開発者が同じ種類の情報と推奨事項を見られるようになります。
これは、セキュリティレビューの工程を標準化し、問題の優先順位付けと対処を簡単にするのに役立ちます。
   - 例: [Semgrep Registry のセキュリティカテゴリで必須のフィールドを含める](https://semgrep.dev/docs/contributing/contributing-to-semgrep-rules-repository/#including-fields-required-by-security-category)と、
   開発者は、`confidence` と `impact` のメタデータが高い検出結果を優先します。
2. **協力。** Semgrep ルールに作成者の情報を含めると、組織のほかのメンバーが、セキュリティの問題について協力しやすくなります。
    - 例: ある人が特定のルールについて質問があったり、詳しい情報が必要だったりするとします。その場合は、
    `author` に直接連絡して、説明してもらえます。
3. **コンプライアンス。** 組織が、特定のセキュリティ規制や標準に準拠する必要があるとします。
この場合は、Semgrep ルールに `compliance` のメタデータフィールドを入れて、そのルールがどの規制や標準に関係するかを示せます。これにより、コードベースが関連するすべての要件に準拠していることを確実にできます。

[hooray-taint-mode](https://semgrep.dev/playground/s/4K3g) ルールのように、メタデータのフィールドは自由に作れます。

Semgrep Registry のセキュリティカテゴリで必須の、次のメタデータフィールドを含めることをお勧めします。

1. `cwe`: セキュリティ上の問題を分類する、[Common Weakness Enumeration](https://cwe.mitre.org/index.html) の識別子。
2. `confidence`: ルールの精度の評価。high、medium、low で表す。
3. `likelihood`: 検出された問題が悪用される確率の見積もり。high、medium、low で表す。
4. `impact`: 検出された問題が悪用された場合に生じうる被害の大きさ。high、medium、low で表す。
5. `subcategory`: ルールのより具体的な分類。次のカテゴリのどれかに入ります。
[vuln、audit、guardrail](https://semgrep.dev/docs/contributing/contributing-to-semgrep-rules-repository/#subcategory)。

これらのメタデータフィールドを含めると、貴重な文脈を提供でき、利用者が、ルールが検出した問題のセキュリティ上の意味を、よりよく理解する助けになります。

### さまざまなヒント

#### 文字列でない要素を含む配列に一致させる

この Semgrep ルールは、文字列でない要素を少なくとも 1 つ含む、JavaScript か TypeScript の配列を検出することを目的としています。
この [array-with-a-non-string-element の例](https://semgrep.dev/s/BJnb)を見てください。

```yaml {linenos=inline}
rules:
  - id: array-with-a-non-string-element
    languages: [js]
    message: array with element that is not a string
    severity: WARNING
    patterns:
      - metavariable-pattern:
          metavariable: $A
          patterns:
            - pattern-not: "..."
      - pattern: [..., $A, ...]
```

#### pattern-either から否定パターンを「取り除く」

この Semgrep ルールは、関数 `a(...)`、`b(...)`、`c(...)` が呼び出される Python のコード片を検出しますが、関数 `a()` が引数 `x` で呼び出される場合には一致させないことを目的としています。
この [pattern-not-with-pattern-either の例](https://semgrep.dev/s/5N96)を見てください。

```yaml {linenos=inline}
rules:
- id: pattern-not-in-pattern-either
  patterns:
    - pattern-either:
       - pattern: a(...)
       - pattern: b(...)
       - pattern: c(...)
    - pattern-not: a(x)
  message: pattern either with one negative pattern
  languages: [python]
  severity: WARNING
```

### Semgrep ルールの品質を保つ

新しいルールを公開したり、既存のルールを更新したりする前に、ルールが一定の基準を満たし、有効であることを確かめることが重要です。
これを助けるために、私たちは、_Contributing to Trail of Bits Semgrep Rules_ の文書に、[開発の実践のチェックリスト](https://github.com/trailofbits/semgrep-rules/blob/main/CONTRIBUTING.md#development-practices)を用意しました。これに従えば、独自のルールが公開できる状態かどうかを確認できます。

### 独自ルールを書くときの助け

{{< hint danger >}}**警告:** 機密のコードベースや非公開のコードベースに固有の可能性がある、ルールの作成についての外部の支援を求めたり、ルールの出力を共有したりする際は、注意してください。そうすると、コードの所有者の身元、コードの一部、特定のバグが、意図せず漏れてしまうおそれがあります。{{</hint>}}

独自ルールの作業で問題に行き当たったときに、助けになるリソースがいくつかあります。
特に役立つものは、次の 2 つです。

- [Semgrep Community Slack](https://go.semgrep.dev/slack) は、独自ルールの開発について助けを求めるのに最適な場所です。このチャンネルには、Semgrep のアーキテクチャと構文に詳しい開発者がいます。
たいてい、質問にすぐ答えてくれます。ルールの構成や、起こった問題のデバッグについて、案内してくれます。さらに、この Slack チャンネルは、似たプロジェクトに取り組むほかの開発者とつながるのにも最適で、ほかの人の経験から学んだり、自分の知見を共有したりできます。
- [Semgrep の GitHub の issue](https://github.com/semgrep/semgrep/issues) を使って、バグの報告、新機能の提案、特定の問題についての支援の依頼ができます。

## 最高の性能を出すための Semgrep ルールの徹底的なテスト

Semgrep ルールの網羅的なテストを作ることは、ルールが期待どおりに動き、幅広いテストケースをカバーしていることを確かめるために欠かせません。さまざまなコードのサンプルに対してルールを徹底的にテストすることで、意図した脆弱性、潜在的なエラー、コーディング規約の違反を、ルールが正確に特定できることを確認できます。これは最終的に、より信頼でき、効果的な、セキュリティとコード品質の解析につながります。

### 網羅的なテストケースを設計する

独自の Semgrep ルールに対する、バランスの取れたテストスイートは、ルールの機能の複数の面をカバーするべきです。

テストケースを設計するときは、次の点を考慮してください。

1. **コードのサンプルを含むファイルを作る**: ルールと同じ名前で、コードを含むファイルを作ります。
たとえば、ルールのファイル名が `unsafe-exec.yml` なら、対応する `unsafe-exec.py` ファイルを作り、サンプルコードを入れます。
2. **多様なコードのサンプルを取り入れる**: テストファイルにコードのサンプルを追加するときは、次のガイドラインに従います。
    - 真陽性のコメントを少なくとも 1 つ入れる (例: `// ruleid: id-of-your-rule`)。
    - 真陰性のコメントを少なくとも 1 つ入れる (例: `// ok: id-of-your-rule`)。
    - 理解しやすい、単純で説明的な例から始める。
    - より高度で複雑な例に進む。たとえば、ネストした構造 (例: `if` 文の内側) や、深い式を含むもの。
    - ルールの精度や効率に挑戦するようなエッジケースを入れる。たとえば、大きな入力値、複雑なコード構造、珍しいデータ型など。
    - ループ、条件分岐、クラス、関数など、言語のさまざまな機能と構文に対して、ルールをテストする。
    - ルールを発動させてはならないコードのサンプルを意図的に作り、そのような場合にルールが誤検知を出さないことを確かめる。
3. **すべてのテストが通ることを確かめる**: `$ semgrep --test` コマンドを実行して、すべてのテストケースが通ることを確認します。
4. **実際のコードに対してルールを評価する**: 実際のシナリオでの有効性を評価するために、自分のプロジェクト、オープンソースのリポジトリ、そのほかのコードベースにある実際のコードに対して、ルールをテストします。

## CI で独自ルールをテストする

### GitHub Actions

次のワークフローを使うと、GitHub Actions で独自の Semgrep ルールをテストできます。

```yml
name: Test Semgrep rules

on: [push, pull_request]

jobs:
  semgrep-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
          cache: "pip"
      - run: python -m pip install -r requirements.txt
      - run: semgrep --test --test-ignore-todo ./path/to/rules/
```

依存関係をキャッシュしてワークフローの実行を速めるために、`requirements.txt` (または、[`poetry` や `pipenv` の同等のもの](https://github.com/actions/setup-python/blob/main/docs/advanced-usage.md#caching-packages)) のファイルに、必ず `semgrep` を含めてください。ここでは `--test-ignore-todo` を付けて、[TODO テスト](https://semgrep.dev/docs/writing-rules/testing-rules)で CI の実行が失敗しないようにしている点に注意してください。TODO テストは、今後のルール改善のための、貴重な形のドキュメントです。

## 自動修正機能

自動修正機能は、特定された脆弱性、潜在的なエラー、コーディング規約の違反を、自動的に修正できます。

自動修正機能を使うことには、多くの利点があります。

- 大規模なコードベースのベストプラクティスのすべてを、開発者全員に教え込むのは現実的ではありません。自動修正は、その隙間を埋め、必要に応じて指針を示せます。
- 自動修正は、単調な変更をなくして、開発者の集中を保ち、より複雑な作業に専念できるようにします。
- 自動修正を加えると、新しいベストプラクティスがコードベースに導入されたときに、開発者がそれを学び、身につけられます。
- 自動修正は、必要なときに修正を提供でき、単純な lint の警告よりも、はるかに行動につなげやすく、学びにもなります。
- 非推奨について開発者に知らせなければ、開発者は非推奨のコンポーネントを使ってはいけないことも、代わりに何を使うべきかも分かりません。自動修正は、こうした移行を円滑にする助けになります。

### 自動修正機能付きの Semgrep ルールを作る

自動修正機能付きのルールを開発するには、次の手順に従います (自動修正機能を実装したルールは、[ioutil-readdir-deprecated](https://semgrep.dev/s/wPEX) を参照してください)。

1. ルールに `fix` キーを追加し、特定された脆弱性の置換パターンを指定します。

    自動修正機能付きのルールの例を示します。

    ```yaml {linenos=inline}
    rules:
      - id: ioutil-readdir-deprecated
        languages: [golang]
        message: ioutil.ReadDir is deprecated. Use more efficient os.ReadDir.
        severity: WARNING
        pattern: ioutil.ReadDir($X)
        fix: os.ReadDir($X)
    ```

    次の Golang のコードに対して、

    ```go {linenos=inline}
    package main

    import (
      "fmt"
      "io/ioutil"
      "log"
      "os"
    )

    func main() {
        // ruleid: ioutil-readdir-deprecated
      files, err := ioutil.ReadDir(".")
      if err != nil {
        log.Fatal(err)
      }

      for _, file := range files {
        fmt.Println(file.Name())
      }
    }
    ```

2. 標準のコマンドでルールを実行し、ルールが意図した問題を検出していることを確認します。

    ```bash
    $ semgrep -f rule.yaml
    # (...)
    Findings:

      readdir.go
        ioutil-readdir-deprecated
            ioutil.ReadDir is deprecated. Use more efficient os.ReadDir.

            ▶▶┆ Autofix ▶ os.ReadDir(".")
            11┆ files, err := ioutil.ReadDir(".")
    # (...)
    ```

3. `--dryrun` と `--autofix` のオプションを付けてルールを実行すると、解析したコードを変更せずに、自動修正機能がコードに対してどう動くかをプレビューできます。

    ```bash
    $ semgrep -f rule.yaml --dryrun --autofix
    # (...)
    Findings:

      readdir.go
        ioutil-readdir-deprecated
            ioutil.ReadDir is deprecated. Use more efficient os.ReadDir.

            ▶▶┆ Autofix ▶ os.ReadDir(".")
            11┆ files, err := os.ReadDir(".")
    # (...)
    ```

4. 自動修正用の新しいテストファイルを作ります。ファイルの拡張子の前に `.fixed` の接尾辞を付けます
(例: `readdir.go` -> `readdir.fixed.go`)。このファイルには、自動修正を適用したあとに期待される出力を入れます。

    `readdir.fixed.go` ファイルの内容:

    ```go {linenos=inline}
    package main

    import (
      "fmt"
      "io/ioutil"
      "log"
      "os"
    )

    func main() {
        // ruleid: ioutil-readdir-deprecated
      files, err := os.ReadDir(".")
      if err != nil {
        log.Fatal(err)
      }

      for _, file := range files {
        fmt.Println(file.Name())
      }
    }
    ```

5. テストを実行して、自動修正が期待どおりに動くことを確認します。

    ```shell
    $ semgrep --test
    1/1: ✓ All tests passed
    1/1: ✓ All fix tests passed
    ```

6. これで、`--autofix` オプションを付けて、解析したファイルに自動修正を適用する準備ができました。

    ```shell
    $ semgrep -f rule.yaml --autofix
    # (...)
    Findings:

      readdir.go
        ioutil-readdir-deprecated
            ioutil.ReadDir is deprecated. Use more efficient os.ReadDir.

            ▶▶┆ Autofix ▶ os.ReadDir(".")
            11┆ files, err := ioutil.ReadDir(".")
    # (...)
    ```

これらの手順に従うと、問題を特定し、それを修正する解決策を提供する、効果的な自動修正機能付きの独自 Semgrep ルールを作れます。

### 正規表現による自動修正

上で紹介した `fix` フィールドでは単純な文字列の置換を指定できますが、`fix-regex` フィールドでは、より複雑な正規表現ベースの置換ができます。詳細は、公式ドキュメントの
[Autofix with regular expression replacement](https://semgrep.dev/docs/writing-rules/autofix/#autofix-with-regular-expression-replacement) を参照してください。

## Semgrep ルールの最適化

{{< hint info >}}繰り返し使える手順で、ルールの性能を高め、誤検知を最小限に抑えます。 {{< /hint >}}

Semgrep ルールを最適化することは、高い性能を保ち、誤検知を最小限に抑えるために重要です。
この節では、効率的で正確な Semgrep ルールの作り方を案内します。

1. **時間のサマリーを解析する**: 結果に時間のサマリーを含めるには、`--time` フラグを使います。次の情報が得られます。
    - 合計時間 / 設定の時間 / コアの時間
    - Semgrep-core の時間
      - 合計の CPU 時間
      - ファイルの解析時間
      - ルールの解析時間
      - マッチングの時間
    - 解析が遅かった上位 5 ファイル
    - マッチングが遅かった上位 5 ルール
2. **検出結果を特定のファイルパスに絞り込む**: 検出結果を、特定のファイルパス (例: Dockerfile) に限定すべきかを検討します。
    - `paths` キーワードを使うと、特定のルールを特定のパスに適用できます。たとえば、
      [avoid-apt-get-upgrade](https://semgrep.dev/playground/r/generic.dockerfile.best-practice.avoid-apt-get-upgrade.avoid-apt-get-upgrade)
      ルールは、Dockerfile だけを対象にしています。

        ```yaml {linenos=inline,linenostart=17}
          paths:
              include:
                - "*dockerfile*"
                - "*Dockerfile*"
        ```

3. **`pattern-inside` と `pattern-not-inside` を使う**: `pattern-inside` と `pattern-not-inside` の句を使うと、パターンに一致させる (または一致させない) 文脈を、それぞれ指定できます。

    ループの中で `insecure_function()` が呼び出され、そのあとに `log_data()` の呼び出しのような特定の文が続く箇所を、ログレベルが `DEBUG` に設定されているときに限って特定したい、という場面を考えます。

    最初は、1 つの `pattern` 文で実現できます。

    ```yaml {linenos=inline}
    rules:
    - id: insecure_function_in_loop_followed_by_debug_log
      languages: [python]
      message: |
        Insecure function called within a loop
        followed by log_data() with log level DEBUG
      severity: WARNING
      pattern: |
        for ... in ...:
            ...
            insecure_function(...)
            ...
            log_data("DEBUG", ...)
    ```

    `insecure_function_in_loop_followed_by_debug_log` ルールを発動させる Python コードの例を示します。

    ```python {linenos=inline, hl_lines=["11-17"]}
    def insecure_function():
        print("Insecure function called")

    def log_data(log_level, msg):
        if log_level == "DEBUG":
            print("DEBUG:", msg)

    def main():
        data_list = ['data1', 'data2', 'data3']

    for data in data_list:
        # Call to insecure_function() within a loop,
        # followed by log_data() with log level DEBUG triggers the rule
        insecure_function()
        other_function()
        function1337()
        log_data("DEBUG", "Insecure function called with data: " + data)
    ```

    `insecure_function_in_loop_followed_by_debug_log` ルールを実行しても、`for` ループ全体が表示されるため、最も分かりやすい出力にはならないかもしれません。

    ```shell
    $ semgrep -f insecure_function_in_loop_followed_by_debug_log.yml
    # (...)
      insecure_function_in_loop_followed_by_debug_log
        Insecure function called within a loop followed by log_data() with log level DEBUG

        11┆ for data in data_list:
        12┆  # Call to insecure_function() within a loop,
        13┆  # followed by log_data() with log level DEBUG triggers the rule
        14┆  insecure_function()
        15┆  other_function()
        16┆  function1337()
        17┆  log_data("DEBUG", "Insecure function called with data: " + data)
    ```

    このような検出結果では、`insecure_function()` の呼び出しだけが重要な場合があります。出力を改善するには、代わりに次の句を使えます。
    1. `patterns`: この句は、2 つのサブパターンを論理 AND 演算子で組み合わせます。つまり、すべてのサブパターンに一致する必要があります。

          a. `pattern-inside`: この句は、Python コード内の任意の `for` ループに一致し、後続のパターンの文脈を確立します。ルールが発動するために満たすべき条件を設定し、論理 AND 演算の最初の部分として働きます。

          b. `pattern`: このサブパターンは、任意の関数の呼び出しと、それに続く `log_data("DEBUG", ...)` の呼び出しに一致します。この `pattern` と、前の `pattern-inside` に一致すれば、ルールが発動する可能性があります。

          c. `focus-metavariable`: この演算子は、検出結果を、`$FUNC` に一致したコード行に絞ります。

          d. `metavariable-pattern`: このサブパターンは、`$FUNC` を、`insecure_function` という名前の関数に限定します。

    `insecure_function_in_loop_followed_by_debug_log` ルールの修正版を示します。

    ```yaml {linenos=inline}
    rules:
    - id: insecure_function_in_loop_followed_by_debug_log_fixed
      languages: [python]
      message: |
        Insecure function called within a loop
        followed by log_data() with log level DEBUG
      severity: WARNING
      patterns:
        - pattern-inside: |
            for ... in ...:
                ...
        - pattern: |
            $FUNC(...)
            ...
            log_data("DEBUG", ...)
        - focus-metavariable: $FUNC
        - metavariable-pattern:
            metavariable: $FUNC
            pattern: insecure_function
    ```

    Semgrep ルール `insecure_function_in_loop_followed_by_debug_log_fixed` を実行すると、より簡潔で焦点の絞られた出力が得られます。

    ```shell
    $ semgrep -f insecure_function_in_loop_followed_by_debug_log_fixed.yml
    # (...)
      insecure_function_in_loop_followed_by_debug_log_fixed
          Insecure function called within a loop followed by log_data() with log level DEBUG

          13┆ insecure_function()
    ```

4. **省略記号 `...` の使用を最小限にする**: 省略記号は、幅広いコード片に一致させる強力な手段ですが、使いすぎると、性能の問題や誤検知を招くことがあります。省略記号の使用は、正確なパターンマッチに必要な場面に限ってください。
5. **メタ変数が必要かどうかを判断する**: ルールにメタ変数を使う前に、本当に必要かどうかを判断します。
メタ変数は、値を取り込んで比較するのに役立ちますが、ルールが正しく動くのに不要なら、取り除くことを検討してください。

    たとえば、メタ変数 `$X` を使う、次の Semgrep ルールを考えます。

    ```yaml {linenos=inline}
    rules:
      - id: unnecessary_metavariable_example
        languages: [python]
        message: The variable is assigned the value 123
        pattern: $X = 123
        severity: WARNING
    ```

    このルールは、値が `123` の任意の変数の代入に一致します。ただし、変数名を取り込む必要がないなら、メタ変数 `$X` は不要かもしれません。その場合は、代わりに、任意の式に一致する `...` 演算子を使えます。

    ```yaml {linenos=inline}
    rules:
      - id: without_metavariable_example
        languages: [python]
        message: A variable is assigned the value 123
        pattern: ... = 123
        severity: WARNING
    ```

    メタ変数 `$X` を `...` 演算子に置き換えると、意図した機能を失わずに、ルールの複雑さを減らし、性能を改善できます。この方法は、メタ変数がルールの目的や、あとの比較や確認に欠かせない場合には、使わないでください。
6. **実際のコードでルールをテストする**: ルールの有効性を確かめるために、実際のコードのサンプルでテストします。
   これにより、ルールを本番環境に展開する前に、潜在的な問題や誤検知を特定できます。
