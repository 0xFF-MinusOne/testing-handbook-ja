---
title: "アプリケーションの処理が正しく動くようにする"
summary: "Burp の自動スキャン機能で最良の結果を得るには、対象のアプリケーションを扱えるように Burp を準備しておくことが欠かせません。そうすれば、アプリケーションのエラーが原因で機能のテストが漏れることがなくなり、より多くのバグを見つけられます。"
weight: 30
url: docs/web/burp/guide/app-handling
---

# アプリケーションの処理が正しく動くようにする

Burp の自動スキャン機能で最良の結果を得るには、対象のアプリケーションを扱えるように Burp を準備しておくことが欠かせません。そうすれば、アプリケーションのエラーが原因で機能のテストが漏れることがなくなり、より多くのバグを見つけられます。

Burp の自動化ツール（Burp Scanner など）を使うときは、次の点に注意してください。

1. **セッション処理**。Burp がセッションを正しく扱い、必要に応じて Cookie を更新し、リクエストごとに必要なヘッダーを更新するようにします（Web アプリケーションによっては、リクエストに署名が必要です）。
また、アクティブスキャン中に、ログアウトするリクエストを送って、Burp が知らないうちにセッションを無効にしてしまわないようにします。
こうした場合に対処するには、セッション処理ルールの設定が必要になることがあります。詳しくは、次の資料を参照してください。

    - [Maintaining an authenticated session](https://portswigger.net/burp/documentation/desktop/testing-workflow/session-management/maintaining-authenticated-session)

    - [Session handling rule editor](https://portswigger.net/burp/documentation/desktop/settings/sessions/session-handling-rules)

2. **CSRF 対策トークン**。[CSRF 対策トークン](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html#token-based-mitigation)を使う Web アプリケーションに Burp を使うと、問題が起こることがあります。アプリケーションは、CSRF 対策トークンを更新せずにリクエストを再送することを、許さないはずだからです。
通常は、セッション処理ルールで CSRF 対策トークンを更新できます。詳しくは、
[Using Burp's Session Handling Rules with anti-CSRF Tokens](https://portswigger.net/support/using-burp-suites-session-handling-rules-with-anti-csrf-tokens) を参照してください。

3. **スロットリング**。Burp を使っても、HTTP の「429 Too Many Requests」ステータスコードやそれに類するものが返らないようにします。
一般に Burp には、特定のステータスコードに対する[自動スロットリングを扱う機能](https://portswigger.net/burp/documentation/desktop/settings/project/tasks#:~:text=Automatic%20throttling%20%2D%20Specify%20the%20response,429%20(Too%20many%20requests))があります。ただし、アプリケーションがトラフィックの超過を知らせる方法は、ほかにもありえます。
可能であれば、テストの間はサーバー側のスロットリングを無効にし、状況に応じて調整します。
それでもスロットリングを回避する必要がある場合は、[IP Rotate](https://portswigger.net/bappstore/2eb2b1cb1cf34cc79cda36f0f9019874) 拡張機能を使えます。

4. **WAF**。WAF がある場合は、WAF がリクエストをブロックしないようにします。
ブロックされる場合は、自分の IP アドレスを許可リストに入れるか、[Bypass WAF](https://portswigger.net/bappstore/ae2611da3bbc4687953a1f4ba6a4e04c) 拡張機能で回避してみてください。

Burp の標準機能（マクロなど）や既存の拡張機能では、上の問題を解決できない特殊なケースもあります。
その場合は、独自の拡張機能を作る必要があります。独自の拡張機能の開発については、
[Creating Burp extensions](https://portswigger.net/burp/documentation/desktop/extensions/creating) に詳しい情報があります。

標準機能の設定、マクロの扱い、独自の拡張機能の作成など、Burp Suite の準備に最初に手間をかけるのは、時間がかかるように思えるかもしれません。しかし、その見返りは大きいことが多くあります。Trail of Bits での経験では、複雑なアプリケーションを扱えるよう Burp Suite を十分にカスタマイズして使いこなすチームは、はるかに多くのセキュリティ脆弱性を見つける傾向があります。
