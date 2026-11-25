---
title: "ステップバイステップガイド: Burp をすばやく使いこなして自分のアプリをテストする"
slug: guide
summary: "この節では、Burp をすばやく使いこなして自分のアプリをテストするための手順を、順を追って説明します。"
weight: 10
url: docs/web/burp/guide
---

# ステップバイステップガイド: Burp をすばやく使いこなして自分のアプリをテストする

## インストールと最初の手順

最初の手順については、お使いのシステムへの
[Burp Suite Professional のインストールとライセンス登録](https://portswigger.net/burp/documentation/desktop/getting-started/download-and-install)
に関する公式ドキュメントを参照してください。

## プロキシの準備

Chromium ベースの Burp 内蔵ブラウザを起動するには、**Proxy** > **Intercept** タブを選び、**Open browser** ボタンをクリックします。
先に進む前に、[Proxy の intercept](https://portswigger.net/burp/documentation/desktop/tools/proxy/intercept-messages) に慣れておいてください。

Chromium 以外の外部ブラウザ（Firefox や Safari など）を設定したい場合は、[公式ドキュメント](https://portswigger.net/burp/documentation/desktop/external-browser-config)を参照してください。

## 対象の Web アプリケーションを Burp で初めて動かす

1. Burp の内蔵ブラウザで Web アプリケーションを開きます。ログイン、新規登録、使えそうな機能や管理画面の表示など、
   対象にしたい機能をできるだけ多く操作します。
2. [対象をスコープに追加します](https://portswigger.net/burp/documentation/desktop/getting-started/setting-target-scope#:~:text=Step%204%3A%20Set%20the%20target%20scope)。
   **Target** タブで特定のドメインに絞り込むと、テストする範囲を管理できます。

   a. スコープ外の項目を履歴に送らないようにすることを検討してください。
   「‘Do you want Burp Proxy to stop sending out-of-scope items to the history or other Burp tools?」というテキストのポップアップが表示されるので、次のどちらかを選びます。

   * 考えられるドメインをすべて選んだと確信している場合は **Yes** をクリックします。
     想定外のホストに悪意のある可能性があるリクエストを送ってしまうのを避けられます。
     こうすると、設定したスコープの対象だけを Burp Scanner でアクティブに攻撃するように設定できます。
   * 最初の実行で、特定のドメインへの裏側のリクエストがよくわからない場合は **No** をクリックします。
     アプリケーションで何が起きているかを、より詳しく把握できます。

    b. スコープの設定について詳しくは、[Scope](https://portswigger.net/burp/documentation/desktop/tools/target/scope) を参照してください。

3. スコープを設定したら、Burp Proxy を少し見て、インターセプトされた通信で何が起きているかを確認します。

   a. Burp をつないだままアプリケーションを操作すると、不要なリクエスト（`fonts.googleapis.com` へのものなど）が
   **Intercept** タブに大量に現れることがあります。

   b. 興味のないホストのインターセプトをやめるには、**Interception** タブでインターセプトされたリクエストをクリックして右クリックし、
   **Don’t intercept requests** > **To this host** を選びます。以後、Burp は印をつけたホストへのリクエストを自動的に転送します。

   c. 前の手順で質問されたときに **No** を選んだ場合（「Do you want Burp Proxy to stop sending out-of-scope
   items to the history or other Burp tools?」）は、スコープ外（「不要」）の項目が大量に表示されることがあります。

{{< hint info >}}
重要なホットキー: 既定では、**Ctrl+F** で、Burp の Intercept 機能にある現在の HTTP リクエストを転送します。
{{< /hint >}}

## 拡張機能を有効にする {#enabling-extensions}

Burp には拡張機能を追加して、バグを見つける能力を高めたり、
さまざまな作業を自動化したりできます。この節で取り上げる Burp 拡張機能のインストールについて詳しくは、
[拡張機能のインストール](https://portswigger.net/burp/documentation/desktop/extensions/installing-extensions)を参照してください。

拡張機能のなかには、「有効にしたら放っておける」種類のものがあります。多くは、
Burp Scanner のタスクごとに、ユーザーの操作なしで自動的に動くように作られていて、結果は **Dashboard** タブの **Issue activity** ペインに表示されます。
ほとんどの Web アプリケーションに当てはまる、次の拡張機能を一般的におすすめします。

1. [**Active Scan++**](https://portswigger.net/bappstore/3123d5b5f25c4128894d97ea1acc4976) は、Burp Suite 標準のアクティブスキャンとパッシブスキャンの機能を強化します。
標準の Burp Scanner が見逃すかもしれない脆弱性のチェックを追加します。
2. [**Backslash Powered Scanner**](https://portswigger.net/bappstore/9cff8c55432a45808432e26dbb2b41d8) は、既知および未知の種類の
サーバーサイドインジェクションの脆弱性を特定しようとすることで、
アクティブスキャンの機能を拡張します。
3. [**Software Vulnerability Scanner**](https://portswigger.net/bappstore/c9fb79369b56407792a7104e3c4352fb) は、
Burp Suite と連携して、Web アプリケーション内の既知のソフトウェアの脆弱性を自動的に特定します。
4. [**Freddy, Deserialization Bug Finder**](https://portswigger.net/bappstore/ae1cce0c6d6c47528b4af35faebc3ab3) は、
ライブラリや API（.NET や Java など）のシリアライズの問題を検出し、悪用する助けになります。
5. [**J2EEScan**](https://portswigger.net/bappstore/7ec6d429fed04cdcb6243d8ba7358880) は、
J2EE アプリケーションの Web アプリケーションペネトレーションテストで、テストのカバレッジを高めます。
6. [**403 Bypasser**](https://portswigger.net/bappstore/444407b96d9c4de0adb7aed89e826122) は、リクエストメソッドの変更やヘッダの書き換えによって、
HTTP 403 Forbidden のレスポンスを回避しようとします。

上の拡張機能のなかには、Burp に
[Jython または JRuby](https://portswigger.net/burp/documentation/desktop/extensions/installing-extensions#:~:text=Installing%20Jython%20or%20JRuby)
を設定しておく必要があるものがあります。

{{< hint warning >}}
多くの拡張機能を有効にすると性能に影響が出るため、
実際に使っている拡張機能だけを有効にしてください。
有効にしている拡張機能を定期的に見直し、今は使っていないものは読み込みを解除することをおすすめします。
{{< /hint >}}
