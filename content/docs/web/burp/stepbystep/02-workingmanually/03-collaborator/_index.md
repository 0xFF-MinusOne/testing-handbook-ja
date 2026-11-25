---
title: "Burp Collaborator"
slug: collaborator
summary: "Burp Collaborator は、Burp Suite Professional のエコシステムに含まれるツールで、Web アプリケーションに潜む脆弱性を見つける助けになります。対象とのその場のやり取りだけにテストを限定せずに済むため、Burp Collaborator によって、アウトオブバンド（OOB）の脆弱性を特定できるようになります。"
weight: 3
bookToc: true
url: docs/web/burp/guide/manual-work/collaborator
---

# Burp Collaborator

Burp Collaborator は、Burp Suite Professional のエコシステムに含まれるツールで、
Web アプリケーションに潜む脆弱性を見つける助けになります。対象とのその場のやり取りだけにテストを限定せずに済むため、
Burp Collaborator によって、アウトオブバンド（OOB）の脆弱性を特定できるようになります。

## これは何か

簡単に言うと、Burp Collaborator は、さまざまなプロトコル（HTTP、HTTPS、DNS、SMTP など）でリクエストを受け取れるサーバーです。
対象のアプリケーションから直接返ってくるレスポンスには現れず、
アプリケーションがほかのシステムに対して開始する接続に現れる脆弱性を、検出できます。これが、アウトオブバンドの脆弱性と呼ばれる理由です。

Burp Collaborator は、対象のアプリケーションに送るペイロードに使える一意の識別子（Burp Collaborator サーバーのサブドメイン）を生成します。
アプリケーションが、ペイロードに基づくその一意の場所と想定外のやり取りをした場合、
Burp Collaborator がそのやり取りを捕捉し、脆弱性の可能性を知らせてくれます。

## 主な利用場面

OOB の脆弱性を明らかにする Burp Collaborator の能力は、セキュリティテストの道具立てに加える強力な武器です。
ほかのテスト手法では見逃しかねない欠陥を発見できます。

Burp Collaborator は Burp Suite のさまざまな部分に組み込まれています。たとえば Burp Scanner は、
Burp Collaborator を使うさまざまな脆弱性を自動でテストしますし、Burp Intruder や Burp Repeater といったツールでは、
Burp Collaborator の機能を手動で活用できます。また、[Collaborator Everywhere](https://portswigger.net/bappstore/2495f6fb364d48c3b6c984e226c02968)
のようなサードパーティの拡張機能を使うと、リクエストの特定の部分に Burp Collaborator のペイロードを自動的に追加できます。

Burp Collaborator が見つける助けになる、代表的なセキュリティ上の問題は次のとおりです。

1. **サーバーサイドリクエストフォージェリ（SSRF）**。ユーザーが指定した任意の URL からコンテンツを取得できるアプリケーションは、
だまされて Burp Collaborator サーバーにアクセスしてしまうことがあり、SSRF の脆弱性の可能性を示します。詳しくは、
[サーバーサイドリクエストフォージェリ（SSRF）](https://portswigger.net/web-security/ssrf)を参照してください。

2. **ブラインド XML 外部エンティティ（XXE）処理**。Burp Collaborator サーバーへの参照を含む DOCTYPE を持つ XML ペイロードをアプリケーションが処理し、
Burp Collaborator サーバーへの呼び出しが発生した場合、多くは
XXE の脆弱性があることを意味します。詳しくは、[XML 外部エンティティ（XXE）インジェクション](https://portswigger.net/web-security/xxe)を参照してください。

3. **DNS のやり取り**。アプリケーションに注入したペイロードによって、サーバーが Burp Collaborator サーバーに対して想定外の
DNS 参照を行う場合、安全でないデータ処理やサーバーサイドテンプレート
インジェクションなど、さまざまな問題の可能性があります。たいていは、DNS のやり取りは、セキュリティ上の問題を明らかにするためのより深い調査の足がかりになります。

## Burp Collaborator クライアント

Burp Suite には Burp Collaborator クライアントが含まれていて、検出されたやり取りがないかを Burp Collaborator サーバーに問い合わせます。
Burp Suite 内で Collaborator のペイロード（一意の URL、DNS サブドメイン、メールアドレス）を使うたびに、アプリケーションは
そのペイロードに関するやり取りがないかを、Burp Collaborator サーバーに自動的にポーリングします。

手動テストでは、**Collaborator** タブを使ってペイロードを生成し、コピーできます。
OOB のやり取りが発生すると、通知されます。

{{< resourceFigure "collaborator-tab.png" >}}
Burp の **Collaborator** タブの例
{{< / resourceFigure >}}

- Burp Repeater では、リクエストを右クリックして **Insert Collaborator payload** を選ぶか、Taborator 拡張機能を有効にして
`$collabplz` というプレースホルダを使えます。詳しくは、
[Burp Repeater]({{% relref "/docs/web/burp/stepbystep/02-workingmanually/01-repeater" %}})の節を参照してください。

- Burp Intruder では、[Collaborator payloads](https://portswigger.net/burp/documentation/desktop/tools/intruder/configure-attack/payload-types#:~:text=processing%20rule.-,Collaborator%20payloads,-This%20generates%20and)
タイプを使うか、Taborator 拡張機能を有効にして `$collabplz` というプレースホルダを使えます。
詳しくは、[Burp Intruder]({{% relref "/docs/web/burp/stepbystep/02-workingmanually/02-intruder" %}})
の節を参照してください。

{{< hint warning >}}
Burp Collaborator のペイロードは、ディスクに保存された [Burp プロジェクト](https://portswigger.net/burp/documentation/desktop/projects)の中だけで生成することを忘れないでください。
一時的な Burp プロジェクトで生成すると、Burp を再起動したときにアクセスできなくなります。
{{< /hint >}}

## Burp Collaborator を無効にする

テスト対象のアプリケーションのなかには、Burp Collaborator サーバーであっても、第三者のサーバーに公開してはならないものがあります。
こうした場合に注意することは欠かせませんが、Burp Collaborator を無効にすると
一部の脆弱性を特定できなくなるおそれがあるため、慎重に検討してください。

Burp Collaborator に関連する機能は、**Collaborator** の設定タブでどれでもオフにできます。

{{< resourceFigure "collaborator-settings.png" >}}
Burp Collaborator の **Settings** パネル
{{< / resourceFigure >}}

機密性の高い環境では、Burp Collaborator サーバーの専用インスタンスを展開することを検討してください。
サーバーを特定のドメイン名に割り当てる手段が限られ、内部ネットワークの IP アドレスだけに頼るしかない場合でも、
専用の Burp Collaborator サーバーを持つと成果が上がることが多いと感じています。

## 専用の Burp Collaborator サーバーを設定する

既定では、Burp Suite Professional は PortSwigger がホストする Burp Collaborator サーバー（たとえば `oastify.com` ドメイン配下）を使います。
しかし、セキュリティテストの場面によっては、Burp Collaborator サーバーの専用インスタンスを設定する必要があります。
内部の、ルーティングできないシステムをテストする場合や、プライバシーのためなどが理由です。

自前の Burp Collaborator サーバーを動かすには、[専用の Burp Collaborator サーバーのデプロイ](https://portswigger.net/burp/documentation/collaborator/server/private)の手順に従う必要があります。

## ピンバックに Burp Collaborator のドメイン名を使う必要はない

元の Burp Collaborator サーバーの IP アドレスを指していて、HTTP リクエストの別の場所で独自ドメイン用の一意の識別子を使っていれば、
どんなドメイン名でも使えます。これにより、
`oastify.com` ドメインが拒否リストに入っているという制限を、簡単に回避できます。

たとえば、`8oxo34j107g7kxk2ais46459u00sojc8.oastify.com` という Burp Collaborator ペイロードが
IP アドレス `54.77.139.23` を指しているとき、この IP アドレスを指す独自ドメイン（たとえば
`tobbytest.com`）を設定できます。tobbytest.com にリクエストを送り、`User-Agent` ヘッダを `8oxo34j107g7kxk2ais46459u00sojc8` に設定します。
それでも Burp Collaborator は、HTTP リクエストを受け取ったと知らせてくれます。

{{< customFigure "User-Agent ヘッダを変更して tobbytest.com サーバーにリクエストを送る curl コマンド" >}}

```sh {linenos=false}
curl -A 8oxo34j107g7kxk2ais46459u00sojc8 tobbytest.com     
```

{{< /customFigure >}}

{{< resourceFigure "burp-collaborator-ua.png" >}}
`User-Agent` ヘッダにペイロードを入れた、Burp Collaborator へのリクエスト
{{< / resourceFigure >}}
