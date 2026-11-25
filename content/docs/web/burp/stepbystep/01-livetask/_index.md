---
title: "ライブタスク"
slug: livetask
summary: "ライブタスクは、Burp Suite の特定のツールからのトラフィックを処理し、定義済みの動作を実行します。"
weight: 10
url: docs/web/burp/guide/livetask
---
<!-- markdownlint-disable first-line-h1 -->
## ライブタスクの初回実行
<!-- markdownlint-restore -->
{{< hint info >}}
[拡張機能の有効化]({{% relref "docs/web/burp/stepbystep/#enabling-extensions" %}})の手順で、拡張機能を有効にしたことを確認してください。
{{< /hint >}}

[ライブタスク](https://portswigger.net/burp/documentation/desktop/tutorials/using-live-tasks)は、Burp Suite の特定のツール(Burp Proxy、Burp Repeater、Burp Intruder など)からのトラフィックを処理し、定義済みの動作を実行します。ライブタスクの方式では、ライブのアクティブな Burp Scanner タスクを設定して、Web サイトを訪れたときにプロキシ経由のトラフィックを取得し、自動的に Burp Scanner へ送ります。プロキシ経由のリクエストを Burp に自動でスキャンさせるには、次の手順に従います。

1. **Dashboard** を開き、**New live task** をクリックします。
2. **Tools scope** で **Proxy** を選びます。
3. **URL scope** で **Suite scope** を選びます。
4. **Ignore duplicate items based on URL and parameter names** のチェックボックスをオンにします。このオプションを使うと、Burp Suite が同じリクエストを何度もスキャンしなくなります。より正確には、URL とパラメータ名が同じリクエストは、パラメータの値が違っていても、繰り返しスキャンされません。

    例で説明します。

    * アプリケーションにユーザーのプロフィールページがあり、URL `http://example.com/profile?id=1234` でアクセスするとします。アプリケーションを巡回する間に、この URL を異なる `id` の値(`?id=1234`、`?id=2345` など)で何度も訪れることがあります。

    **Ignore duplicate items based on URL and parameter names** をオンにしていると、Burp Suite は、使う `id` の値が違っていても、この URL を 1 回だけスキャンします。これらのリクエスト(`http://example.com/profile?id=1234`、`http://example.com/profile?id=2345` など)は、共通の URL `/profile` と `id` というパラメータ名にもとづいて、重複として扱われます。これにより、スキャン作業の無駄な重複を防げるので、貴重な時間を節約できます。

5. **Scan configuration** に進み、**Select from library** ボタンをクリックして、**Audit coverage - maximum** を選びます。これで、可能な限り網羅的なスキャンになります。詳細は、[組み込みの設定](https://portswigger.net/burp/documentation/scanner/scan-configurations/burp-scanner-built-in-configs)を参照してください。
6. 必要に応じて、ターゲットへの同時リクエスト数をいつでも調整できます。詳細は、[スキャン用のリソースプールの管理](https://portswigger.net/burp/documentation/desktop/automated-scanning/managing-resource-pools)を参照してください。

次に、組み込みの Burp ブラウザを開き、Web サイトを注意深く巡回します。サイトの隅々まで訪れるようにしてください。詳しい情報や個別のリクエストは、**Tasks** > **Live audit from Proxy (suite)** で確認できます。

[**Logger**](https://portswigger.net/burp/documentation/desktop/tools/logger/getting-started) タブを使って、スキャンが内部でどのように動くか、悪意のある可能性があるリクエストに対してアプリケーションがどう反応するかを観察します。サインアウトの API 呼び出し(`/logout` など)をスキャンする場面には注意してください。セッションが終了し、多くのリクエストが HTTP の「401 Unauthorized」エラーで終わるおそれがあります。また、Web アプリケーションファイアウォール(WAF)にブロックされないよう、そして Burp が一定時間内にリクエストを送りすぎないよう注意してください。送りすぎると、HTTP の「429 Too Many Requests」ステータスコードが返ることがあります。Burp による過剰なトラフィックの問題を防ぐには、[自動スロットリング](https://portswigger.net/burp/documentation/desktop/settings/project/tasks#:~:text=requests%20are%20sent.-,Automatic%20throttling,-%2D%20Specify%20the%20response)を参照してください。

{{< hint danger >}}
アクティブな Burp Scanner を使うと、データの消失など、Web サイトに悪影響が出るおそれがあることを忘れないでください。
{{< /hint >}}

また、Burp がアプリケーションのリクエストを正しく処理できているかも確認してください。たとえば、現在のリクエストの HMAC SHA-256 署名をカスタムヘッダーに入れる必要があるアプリケーションがあります。入れないと、サーバーはエラーを返します。CSRF トークン(たとえば `X-CSRF-Token` ヘッダー経由)を厳密に扱う Web アプリケーションもあり、トークンが正しくないと、やはりエラーを返します。アプリケーションのリクエストが正しく処理されないと、テストの精度が下がるおそれがあります。詳細は、[アプリケーションの処理が正しく動くことを確認するセクション]({{% relref "docs/web/burp/stepbystep/03-ensure-working-correctly/" %}})を参照してください。

## 結果はどこにあるか

ライブスキャンで見つかった問題は、主に **Dashboard** > **Tasks** のアクティビティで確認できます。報告された問題を注意深く確認し、重大度が高く、確度が確実な問題には特に注意を払ってください。

また、さまざまな Burp のツールを使うときは、標準でないレスポンスを調べることが重要です。特に次の点を確認します。

   1. **Logger** タブを確認します(使用するメモリの上限を引き上げることを検討してください。[Burp Logger のエントリの扱い](https://portswigger.net/burp/documentation/desktop/tools/logger/settings#:~:text=were%20actually%20captured.-,Capture%20limit,-You%20can%20specify)を参照)。

      a. さらに掘り下げる必要を示している可能性がある、標準でないエラーの HTTP レスポンス(500、502 など)

      b. エラーメッセージやスタックトレースの可能性があるもの

      c. 認可の仕組みを通過すべきでないリクエストに対する、成功のステータスレスポンス(「200 OK」など)

      d. [オープンリダイレクト](https://portswigger.net/kb/issues/00500100_open-redirection-reflected)の問題の可能性がある、302 と 301 のステータスレスポンス

   2. ホワイトボックスの視点で作業しているときは、アプリケーションのログを調べ、クラッシュ、パニック、ログインジェクション([CRLF インジェクション](https://book.hacktricks.xyz/pentesting-web/crlf-0d-0a)や [IP スプーフィング](https://portswigger.net/kb/issues/00400110_spoofable-client-ip-address)を参照)の可能性がないかを探します。
