---
title: "Burp Intruder"
summary: "Burp Intruder は、ウェブアプリケーションに対するカスタマイズした攻撃を自動化するツールで、HTTP リクエストのファザーとして使えます。"
weight: 2
bookToc: true
url: docs/web/burp/guide/manual-work/intruder
---

# Burp Intruder

Burp Intruder は、ウェブアプリケーションに対するカスタマイズした攻撃を自動化するツールで、HTTP リクエストのファザーとして使えます。
元になるリクエストを何度も繰り返す攻撃を設定する機能があります。
Burp Intruder は、あらかじめ決めた位置にさまざまなペイロードを挿入して、元のリクエストを変えられます。
そのため、とくに想定外の入力や悪意のある入力に依存する脆弱性を見つけるための、汎用的なツールになります。

リクエストを Burp Intruder に送るには、リクエストを右クリックして **Send to Intruder** を選びます。

Burp Intruder の基本的な使い方は、公式のドキュメント [Getting started with Burp Intruder](https://portswigger.net/burp/documentation/desktop/tools/intruder/getting-started) を参照してください。
とくに、リクエストの中に攻撃する場所が複数ある場合に備えて、攻撃タイプを理解しておきましょう。

{{< resourceFigure "intruder-attack-type.png" >}}
Burp Intruder の攻撃タイプの例
{{< / resourceFigure >}}

## ワードリスト

ワードリストは、攻撃中に Burp がリクエストに埋め込むペイロード（つまり入力文字列）を集めたファイルです。
ワードリストを使うと、ウェブアプリケーションが想定外の入力や不正な形式の入力をどう扱うかをテストできます。

**ワードリストを用意します。** Burp には単純な組み込みのリストがありますが、より広く調べるには自分のリストを用意すべきです。たとえば、
次は広く使われている公開のワードリストです。

- [SecLists](https://github.com/danielmiessler/SecLists)
- [Payloads All The Things](https://github.com/swisskyrepo/PayloadsAllTheThings)

次は、複数のワードリストをまとめた例です。

- [`payloads.txt`](https://gist.github.com/ahpaleus/e80654d82e718731e8b5385d5df56f2b)
  
ターゲットによって、ワードリストごとの効果は大きく変わります。
ワードリストは、アプリケーションの特性と、探している脆弱性の種類に合わせて選んでください。
次のような場面があります。

1. **言語に特化したリスト**。特定の言語が中心のアプリケーションをテストする場合は、その言語に特化した
ワードリストを使うと、より成果が上がることがあります。たとえば、SecLists の[大きな英語のワードリスト](https://github.com/danielmiessler/SecLists/blob/master/Discovery/Web-Content/raft-large-words-lowercase.txt)は、
隠れた、またはドキュメントにない POST、GET、JSON のパラメータを探すときに役立ちます。
2. **脆弱性に特化したリスト**。特定の脆弱性を検出するために作られたワードリストもあります。
SQL インジェクションをテストしたいなら、SQL インジェクションのペイロードがぎっしり詰まったワードリストを使います。
同様に、ファイルやディレクトリの列挙の脆弱性を探しているなら、
よくあるファイル名やディレクトリ名のワードリストが、それを見つける助けになります。
3. **技術スタックに特化したリスト**。アプリケーションの基盤技術によっては、ほかより向いているワードリストがあります。
たとえば、アプリケーションが Adobe Experience Manager で作られているなら、[`aem2.txt`](https://github.com/danielmiessler/SecLists/blob/3ff9658de5742e4ebb73aff996d6a1170e0a256e/Discovery/Web-Content/aem2.txt)
 のリストで、隠れたファイルや脆弱性が見つかることがあります。

自分の経験、新しい調査、ターゲットの特性に基づいて、リストにペイロードを足していくのは、よい習慣です。

{{< hint info >}}
**カスタムのワードリストの場所を設定します。** Burp Intruder には、基本的な[あらかじめ定義されたペイロードのリスト](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/payload-lists)が付属しています。
[Intruder の設定](https://portswigger.net/burp/documentation/desktop/settings/tools/intruder#payload-list-location:~:text=Saving%20attacks.-,Payload%20list%20location,-These%20settings%20enable)で、カスタムのワードリストを入れた自分のディレクトリを読み込めます。
これで、カスタムのワードリストをすぐに使えるようになります。
{{< /hint >}}

{{< resourceFigure "custom-wordlists.png" "" 600>}}
Burp Intruder のカスタムのペイロードリストの例
{{< / resourceFigure >}}

{{< hint info >}}
[Taborator](https://portswigger.net/bappstore/c9c37e424a744aa08866652f63ee9e0f) 拡張機能を使い、ワードリストに `$collabplz`
というプレースホルダを追加します。
リクエストを処理するときに、Taborator がこれを有効な
[Burp Collaborator]({{% relref "/docs/web/burp/stepbystep/02-workingmanually/03-collaborator" %}}) のペイロードに自動で置き換えます。
たとえば、`?url=http://$collabplz` は `?url=http://p6abcw7n8g5z5uw332mv6r3rhin9bzzo.oastify.com` に変わります。
ホストとのやり取りが観測されると、**Taborator** タブに出力が表示されます。
{{< /hint >}}

## どこを §攻撃§ するか

Burp Intruder に攻撃する場所を指示するには、ペイロードを `§§` の文字で挟んで置きます。では、HTTP リクエストの中で、攻撃する場所は具体的にどこでしょうか。
バグはどこにでもありうるので、思いつく限りの場所にプレースホルダを置いてください
（パス、パスの途中、パラメータ、パラメータ名、ヘッダーの値、追加のヘッダーなど）。
成功するかどうかは、ターゲット、探しているバグ、使うワードリスト、創意工夫、経験によります。

さらに、ターゲットにペイロードマーカー `§§` を追加して、リクエストの送信先の URL を
パラメータ化することもできます（図 3）。

{{< resourceFigure "target-payload-markers.png" "" 400>}}
Burp Intruder のターゲットへのペイロードマーカーの追加
{{< / resourceFigure >}}

{{< hint info >}}
Burp Intruder の [Auto 機能](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/positions#:~:text=Apply%20automatic%20payload%20markers%20%2D%20click%20Auto%20%C2%A7)を使うと、
クエリパラメータやボディのパラメータなど、リクエストの中のよくある位置に、
ペイロードマーカーを自動で置けます。
{{< /hint >}}

## 何を見るか

Burp Intruder の攻撃をうまく実行するのは、最初の一歩にすぎません。大事なのは、結果を徹底的に分析して、
脆弱性の可能性を探すことです。分かりやすい攻撃の結果（機密の `/etc/passwd`
ファイルがレスポンスで返ってくるなど）のほかに、次のことも考えてください。

1. **結果を観察する**。エラーメッセージ、スタックトレース、想定外のレスポンスボディを観察します。
入力したペイロードがアプリケーションの動作に異常を起こしたことを示し、
さらに調べるべき脆弱性の可能性を示唆していることがあります。

2. **レスポンスから抽出する**。リクエストを右クリックして、[**Define extract grep from response**](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/settings#grep-extract)
をクリックし、レスポンスの抽出ルールを作ります。これにより別の列ができ、各レスポンスの特定の場所の内容が抽出されます。
たとえば、特定の HTML タグの間の値を抽出すると、クロスサイトスクリプティング（XSS）を特定できることがあります。
`Location` ヘッダーの値を抽出すると、オープンリダイレクトの脆弱性を検出できることがあります。

3. **Burp Collaborator のやり取りを見る**。Burp Intruder の攻撃で Burp Collaborator のペイロードを使うと、
アウトオブバンドの脆弱性を特定できます。Burp Collaborator のペイロードを挿入したとき（またはリクエストで
Taborator 拡張機能の `$collabplz` を使ったとき）は、**Collaborator** タブでやり取りを確認します。
Taborator を使う場合は、代わりに **Taborator** タブにやり取りが表示されます。
4. **特定の列を並べ替える**。結果の列を適切に並べ替えると、より多くの手がかりが得られます。

   a. **Length**: 普通でない長さのレスポンスを探します。ほとんどが似た長さで、少数だけが大きく外れている場合、
   その違いにつながったペイロードが、アプリケーションに想定外の動作を起こした可能性があります。
   たとえば、どのレスポンスの長さも通常は 1565 なのに、1 つだけ 1337 を返す場合です。注入した入力によって
   動作が違った可能性を示しています。

   b. **HTTP レスポンスコード**: 500 や 502 のようなコードは、サービス拒否（DoS）の脆弱性の可能性を示すことがあります。
   302 のレスポンスも、オープンリダイレクトの脆弱性の手がかりになりえます。リクエストの認証に関わる部分を
   テストしているときに、想定外の 200 や 201 のステータスコードが返ってきたら、認可を回避できる脆弱性の可能性があります。

   c. **レスポンス時間**: 異常に長い、あるいは極端に短いレスポンス時間は、DoS 攻撃や、時間ベースのブラインド SQL インジェクション攻撃のような、
   sleep に関わるインジェクションの欠陥を示すことがあります。結果の表を設定するには、**Columns** メニューをクリックして、
   **Response received** または **Response completed** を選びます。

## Burp Intruder のさまざまなヒント

1. Burp Intruder の攻撃用に、[専用のリソースプールを作ります](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/resource-pool)。
Burp Scanner と Burp Intruder が、リクエストを出すワーカーを取り合わないようにするためです。

2. デフォルトでは、Burp Intruder は最終的なペイロードの特定の文字を URL エンコードします。
ペイロードのエンコードを有効にした場合と無効にした場合で、攻撃を 2 回実行することを検討してください。ペイロードのエンコードの設定方法は、[Burp Intruder のペイロード処理](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/processing#:~:text=Configuring%20payload%20encoding)
を参照してください。

3. [Hackvertor](https://portswigger.net/bappstore/65033cbd2c344fbabe57ac060b5dd100) 拡張機能を使うと、入力をさまざまな方法でエスケープやエンコードするタグを使えます。
Hackvertor のタグの中に `§§` の文字を置けます。たとえば、
`<@jwt('HS256','secret')>§payload§<@/jwt>`

4. 拡張機能が生成するペイロードタイプもあります
（たとえば [Freddy, Deserialization Bug Finder](https://portswigger.net/bappstore/ae1cce0c6d6c47528b4af35faebc3ab3) から）。
Burp Intruder の **Payloads** タブで、**Payload type** のドロップダウンメニューから **Extension-generated** を選び、
続いて具体的なペイロードの設定を選ぶと使えます（図 4）。

   {{< resourceFigure "extension-generated.png" "" 550>}}
   Burp Intruder で攻撃を設定するときの **Payloads** タブ。
   {{< / resourceFigure >}}

5. [Recursive grep](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/payload-types#:~:text=WIENER%0APeter%20wiener-,Recursive%20grep,-This%20enables%20you)
のペイロードタイプを使うと、直前のリクエストのレスポンスからテキストを抽出して、そのテキストを現在のリクエストのペイロードとして使えます。
設定の例は、[NahamCon2023: Bug Bounty Village workshop](https://youtu.be/rM61brpBV48?t=9199)（2:33:19 から）を参照してください。

6. 攻撃は必ず一時プロジェクトのモードで実行します（[攻撃の設定の **Save attack to project file**](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/settings#:~:text=Intruder%20settings.-,Save%20attack,-Professional) は、クリックし*ない*でください）。
結果をあとで残したい場合は、[**Save the attack to the project file**](https://portswigger.net/burp/documentation/desktop/tools/intruder/results/saving-attacks)
をクリックします。

7. [Intruder は、コラボレーターのペイロードを自動で生成できます](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/payload-types#:~:text=processing%20rule.-,Collaborator%20payloads,-This%20generates%20and)。
ペイロードのソースと、ペイロード後の処理のどちらでも使えます。攻撃が終わったあとにやり取りが見つかった場合は、
攻撃が削除されていなければ、結果にやり取りの回数が反映され、Event log に問題が報告されます。

{{< resourceFigure "collabo-event-log.png" >}}
Burp Collaborator のペイロードのやり取りで Event log に報告された問題
{{< / resourceFigure >}}

{{< resourceFigure "collabo-interaction-column.png" "" 550>}}
Burp Collaborator のペイロードのやり取りがあったときの、Burp Intruder の攻撃の Interactions 列
{{< / resourceFigure >}}
