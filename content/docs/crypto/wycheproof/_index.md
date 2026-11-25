---
title: "Wycheproof"
weight: 3
summary: "Wycheproof は、既存の暗号アルゴリズム向けのテストベクタ集です。開発者は、実装の検証や、既知の攻撃・脆弱性の確認に使えます。"
bookCollapseSection: true
math: true
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookComments: false
# bookSearchExclude: false
---

# Wycheproof

{{< math >}}

[Wycheproof](https://github.com/C2SP/wycheproof) は、既存の暗号アルゴリズムの正しさを検証し、既知の攻撃に対してテストするための、大規模なテストベクタ集です。
もとは Google が開発したもので、現在はコミュニティが管理するプロジェクトとなっており、貢献者が特定の暗号構成のテストベクタを追加できます。

## 概要

Wycheproof は、暗号の実装にある既知の脆弱性を見つけるためのテストベクタの集まりを提供します。
次のものを含む、幅広い暗号アルゴリズムに対応しています。

- AES-GCM
- ChaCha20-Poly1305
- ECDH
- RSA

そのほかにも多数あります。

テストベクタはすべて、公式の [GitHub リポジトリ](https://github.com/C2SP/wycheproof)に置かれています。
ベクタのファイルは `testvectors_v1` フォルダに、対応する JSON スキーマのファイルは `schemas` フォルダにあります。

テストベクタは JSON 形式のファイルに入っています。これをテスト用ハーネスの入力として使い、実際の出力をテストベクタに書かれた期待される出力と比べることで、暗号の実装が正しいかを検証できます。[JSON スキーマ](https://json-schema.org/)のファイルは、テストベクタの構造を記述しています。

Wycheproof のテストベクタを使うには、テスト用ハーネスを書いて、テストしたい暗号ライブラリのテスト手順に組み込みます。
このハーネスは、特定の構成の JSON ファイルを読み取り、各テストベクタの入力と期待される出力を使って、実装を検証します。
場合によっては、[omissis/go-jsonschema](https://github.com/omissis/go-jsonschema) のようなツールで、JSON スキーマのファイルから、その言語向けの JSON データの表現を生成するのが、いちばん簡単です。

## リポジトリの構成

Wycheproof のリポジトリは、次のような構成です。

```text
┣ 📜 README.md       : Project overview
┣ 📂 doc             : Documentation
┣ 📂 schemas         : Test vector schemas
┗ 📂 testvectors_v1  : Test vectors
```

ほとんどの開発者にとって重要なのは `schemas` と `testvectors_v1` のフォルダです。すべてのスキーマと、JSON 形式のテストベクタが入っているからです。
この 2 つのフォルダの構成と、各テストファイルの構造を、以下で説明します。

## テストベクタの構造

各 JSON テストファイルは、たとえば AES-GCM のような、特定の暗号構成をテストします。
各 JSON ファイルは複数の*テストグループ*からなり、各テストグループは複数のテストベクタを含みます。
たとえば AES-GCM では、すべてのテストベクタが `aes_gcm_test.json` に入っており、44 個のテストグループと 316 個のテストベクタからなります。

```text
📂 testvectors_v1
┣ 📜 aes_gcm_test.json
┃   ┣━━ test group 1
┃   ┃   ┣━━ test vector 1
┃   ┃   ┣━━ test vector ...
┃   ┃   ┗━━ test vector 67
┃   ┣━━ test group ...
┃   ┃   ┗━━ test vector ...
┃   ┗━━ test group 44
┃       ┣━━ test vector 315
┃       ┗━━ test vector 316
┣ 📜 ecdh_secp256k1_test.json
┃   ┣━━ test group 1
┃   ┃   ┣━━ test vector 1
┃   ┃   ┣━━ ...
...
```

上の図は、`testvectors_v1` フォルダが、**AES-GCM** や **ECDH** といった異なる暗号アルゴリズムを、別々のファイルに分けて整理している例です。
各ファイルは複数のテストグループを含み、各テストグループは複数のテストベクタを含みます。
以下では、各テストファイルの構造と、異なる構成のテストファイルに共通する点を、さらに詳しく説明します。

## テストファイル

テストファイルには、ある暗号アルゴリズムのテストに使うテストベクタがすべて入っています。
すべてのテストファイルには、次の共通の属性があります。

```json
"algorithm"         : The name of the algorithm tested
"schema"            : The JSON schema which can be found in the `schema` folder at the root of the Wycheproof project
"numberOfTests"     : The total number of test vectors inside this file
"header"            : More detailed description of the intended of the test vectors present in the current file
"notes"             : Provides a more in depth explanation of different flags present in each test vector 
"testGroups"        : An array of one or multiple test groups
```

### テストグループ

テストグループは、鍵のサイズ、IV のサイズ、公開鍵、曲線といった共通の属性にもとづいて、テストをまとめたものです。
この分類により、テスト対象の構成に関係する特定の条件を満たすテストだけを取り出せます。

### テストベクタ

各テストベクタには、特定の暗号アルゴリズムに必要な入力と、期待される出力がすべて含まれています。
構造はアルゴリズムごとに違いますが、すべてのテストベクタに共通する属性があります。

#### 共通の属性

Wycheproof のテストベクタには、すべてのテストベクタに存在する属性があります。
すべてのテストベクタに共通するのは、次の 4 つのフィールドです。

- `tcId`: ファイル内でテストベクタを一意に識別する ID。
- `comment`: テストケースについての補足情報。
- `flags`: 特定の種類のテストケースと、その潜在的な危険性の説明。`notes` フィールドで参照されます。
- `result`: テストが成功すべきかどうか。

`result` フィールドは重要で、3 つの値を取ります。

- **valid**: テストケースは成功すべきです。
- **acceptable**: テストケースは成功してもよいものの、理想的でない性質を含んでいます。本来は失敗するのが望ましいが、通っても許容されます。
- **invalid**: テストケースは失敗すべきです。

#### 固有の属性

固有の属性は、テスト対象の暗号アルゴリズムの入力と出力に固有のものです。
たとえば、AES-GCM のテストには `key`、`iv`、`aad`、`msg`、`ct`、`tag` が含まれ、secp256k1 の ECDH のテストには `public`、`private`、`shared` が含まれます。

## CI の設定

時間がたつと、Wycheproof は既存のテストファイルに新しいテストベクタを追加することがあります。
これは開発者にとって大きな利点です。テスト用ハーネスを一度書くだけで、追加の作業なしに、新しいテストベクタの恩恵を受けられるからです。そのため、ハーネスで使うテストベクタを常に最新に保つことをお勧めします。
Wycheproof は、GitHub リポジトリのサブモジュールとして追加することをお勧めします。
それができない場合のために、Wycheproof のリポジトリから特定のテストベクタを取得する簡単なスクリプトも用意しています。

言語のエコシステムによっては、Wycheproof がパッケージとして提供されています。たとえば、PHP では [packagist 経由](https://packagist.org/packages/c2sp/wycheproof)で、Go では[埋め込みの FS を持つ go.mod モジュール](https://github.com/C2SP/wycheproof/blob/main/testvectors.go)として使えます。

### Git のサブモジュール

Wycheproof を git のサブモジュールとして追加すると、テスト対象の構成に追加された新しいテストベクタを、自動で使えるようになります。

```bash
git submodule add git@github.com:C2SP/wycheproof.git
```

### テストベクタの取得

Wycheproof を git のサブモジュールとして追加できない場合は、特定の構成を取得して `.wycheproof` フォルダに置く、簡単なスクリプトを使えます。GitHub は git の [archive コマンド](https://github.com/isaacs/github/issues/554)に対応していないため、指定した JSON を取得する単純な `curl` のクエリで代用しています。次の例では、AES-GCM と AES-EAX のテストファイルを取得します。

```bash {linenos=inline}
#!/bin/bash

TMP_WYCHEPROOF_FOLDER=".wycheproof/"
TEST_VECTORS=('aes_gcm_test.json' 'aes_eax_test.json')
BASE_URL="https://raw.githubusercontent.com/C2SP/wycheproof/master/testvectors_v1/"

# Create wycheproof folder
mkdir -p $TMP_WYCHEPROOF_FOLDER

# Request all test vector files if they don't exist
for i in "${TEST_VECTORS[@]}"; do
  if [ ! -f "${TMP_WYCHEPROOF_FOLDER}${i}" ]; then
    curl -P "$TMP_WYCHEPROOF_FOLDER" "${BASE_URL}${i}"
    if [ $? -ne 0 ]; then
      echo "Failed to download ${i}"
      exit 1
    fi
  fi
done
```

このスクリプトは `.wycheproof` というフォルダを作り、`ALGORITHMS` 変数で指定した JSON ファイルを、`curl` で GitHub のサーバーから取得して保存します。
テスト用ハーネスを実行する前にこのスクリプトを走らせれば、Wycheproof のテストベクタが最新に保たれ、新しいテストベクタの恩恵を受けられます。

## 理想的な使いどころ

Wycheproof は、既存の暗号実装が、既知のエッジケースや、開発中によくある間違いに対して正しいかを検証する場面で、最も力を発揮します。
{{< hint warning >}}
Wycheproof は、新しい暗号アルゴリズムを作るために使うものではありません。Wycheproof は、既存の確立したアルゴリズムのテストベクタ集であり、それらのアルゴリズムの実装をテストするために使うべきものです。
{{< /hint >}}

## 実際の事例 {#real-world-examples}

Wycheproof は、**OpenJDK の SHA1withDSA** や **Bouncy Castle の ECDHC** といった、有名な暗号ライブラリのバグを見つけるのに役立ってきました。
さらに、[pycryptodome](https://pypi.org/project/pycryptodome/) や[そのほか多くのもの](https://github.com/C2SP/wycheproof?tab=readme-ov-file#what-downstream-projects-use-wycheproof-testvectors)のライブラリが、実装のテストに Wycheproof のテストベクタを使っています。
Wycheproof をテストの工程に組み込めば、暗号ソリューションの安全性と信頼性を高められます。

### ケーススタディ: elliptic(npm)

[Elliptic](https://www.npmjs.com/package/elliptic) は、素の JavaScript で書かれた楕円曲線暗号のライブラリです。
週に数百万回ダウンロードされ、約 3000 のパッケージから依存されている、人気のライブラリです。
このライブラリは、次のアルゴリズムに対応しています。

- ECDH
- ECDSA
- EdDSA

これらを、多数の異なる曲線で使えます。
Wycheproof のテストベクタを使って、バージョン 6.5.6(この項目の執筆時点で最新のバージョン)の安全性を調べました。Wycheproof により、ECDSA と EDDSA の両方のモジュールで、複数の脆弱性を見つけられました。

- [CVE-2024-42459](https://nvd.nist.gov/vuln/detail/CVE-2024-42459)
- [CVE-2024-42460](https://nvd.nist.gov/vuln/detail/CVE-2024-42460)
- [CVE-2024-42461](https://nvd.nist.gov/vuln/detail/CVE-2024-42461)

以下では、Wycheproof をどのように適用したかを順を追って説明し、実際の使い方の例を示します。

#### ファイルの読み取り

最初の手順は、EdDSA が対応している曲線をすべて洗い出し、その曲線のテストベクタを Wycheproof が提供しているかを確認することです。
EDDSA オブジェクトのコンストラクタは、曲線の名前を入力として受け取ります。
ソースコードを調べると、このバージョンのライブラリは、`ed25519` 曲線を使う EdDSA にしか対応していないことが分かります。

```javascript
function EDDSA(curve) {
  assert(curve === 'ed25519', 'only tested with ed25519 so far');
  ...
}
```

[Wycheproof の GitHub リポジトリ](https://github.com/C2SP/wycheproof)の中で対応するファイルを探すのは、その曲線を検索するだけで素早くでき、結果は `testvectors_v1/ed25519_test.json` というファイルです。
JavaScript で JSON ファイルを読み取るのは簡単で、数行のコードで済みます。

```javascript
try {
  const fileContent = await fs.readFile(PATH);
  const data = JSON.parse(fileContent.toString());
  data.testGroups.forEach(testGroup => {
    testGroup.tests.forEach(test => {
      test['pk'] = testGroup.publicKey.pk;
      tests.push(test);
    });
  });
} catch (err) {
  console.error('Error reading or parsing file:', err);
  throw err;
}
```

上のコードでは、`testvectors_v1/ed25519_test.json` を読み込み、すべてのテストベクタをグローバルの `tests` 変数に追加しています。
署名の検証に使う公開鍵は、テストグループの中にパラメータとして入っているので、それを各テストベクタに加えています。
すべてのテストベクタを読み込めたら、各テストベクタを使うテスト用ハーネスを書けます。

#### テスト用ハーネス

elliptic ライブラリは単体テストのフレームワークを使っており、そこに新しい Wycheproof のテストベクタを組み込みました。テストベクタごとに個別のテストケースを生成する、テストファクトリを作りました。

```javascript
function testFactory(tcId) {
  it(`[${tcId + 1}] `, function () {
    const test = tests[tcId];
    const ed25519 = new eddsa('ed25519');
    const key = ed25519.keyFromPublic(toArray(test.pk, 'hex'));
    let sig;

    if (test.result === 'valid') {
      sig = key.verify(test.msg, test.sig);
      assert.equal(sig, true, `[${test.tcId}] ${test.comment}`);
    } else if (test.result === 'invalid') {
      try {
        sig = key.verify(test.msg, test.sig);
      } catch (err) {
        // Point could not be decoded
        console.log(err);
        sig = false;
      }
      assert.equal(sig, false, `[${test.tcId}] ${test.comment}`);
    }
  });
}

for (var tcId = 0; tcId < expectedTests; tcId++) {
  testFactory(tcId);
}
```

テストベクタの期待される結果に応じて、署名の検証が成功したか、あるいは、捕捉したアサーションまたは署名が無効であることによって失敗したか、をアサートします。
残りの暗号構成である ECDH と ECDSA についても、同じようにテスト用ハーネスを書く作業を繰り返しました。

#### 結果

すべてのテストベクタを実行すると、テストランナーはいくつかのテストが失敗したと報告します。さらに調べた結果、少なくとも 3 つの脆弱性があると結論づけられます。
よく見ると、これらのテストはすべて失敗するべきだったのに、有効な署名として誤って受理されていました。

失敗したテストベクタは次のとおりです。

{{< hint danger>}}

❌ \[[eddsa](https://github.com/C2SP/wycheproof/blob/master/testvectors_v1/ed25519_test.json)\]\[tcId 37\] 署名から 0 バイトを取り除く

❌ \[[ecdsa](https://github.com/C2SP/wycheproof/blob/master/testvectors_v1/ecdsa_secp256k1_sha256_test.json)\]\[tcId 06\] Legacy: r の ASN エンコードで先頭の 0 が欠けている

❌ \[[ecdsa](https://github.com/C2SP/wycheproof/blob/master/testvectors_v1/ecdsa_secp521r1_sha512_test.json)\]\[tcId 07\] シーケンス \[r, s\] の長さに先頭の 0 が含まれている

{{< /hint >}}

Wycheproof では、各テストベクタの comment フィールドを見れば、そのテストベクタが見つけようとしている脆弱性を、簡単に理解できます。
comment フィールドが曖昧すぎて、もっと情報が必要なときは、各テストベクタの flags フィールドと、JSON ファイルのルートにある notes フィールドの、各フラグの説明を見ます。

失敗したテストベクタを理解するために、ライブラリのソースコードを調べて、これらの脆弱性の根本原因を突き止めました。

#### EDDSA

最初に失敗したテストベクタは、ed25519 曲線の EDDSA アルゴリズムのものでした。原因となる関数は `EDDSA.prototype.verify` で、署名が有効かどうかを確認します。

```javascript
/**
* @param {Array} message - message bytes
* @param {Array|String|Signature} sig - sig bytes
* @param {Array|String|Point|KeyPair} pub - public key
* @returns {Boolean} - true if public key matches sig of message
*/
EDDSA.prototype.verify = function verify(message, sig, pub) {
  message = parseBytes(message);
  sig = this.makeSignature(sig);
  var key = this.keyFromPublic(pub);
  var h = this.hashInt(sig.Rencoded(), key.pubBytes(), message);
  var SG = this.g.mul(sig.S());
  var RplusAh = sig.R().add(key.pub().mul(h));
  return RplusAh.eq(SG);
};
```

この問題は、EDDSA の署名の長さが一度も確認されないことに起因し、署名の末尾に 0 を足したり取り除いたりできてしまいます。

```text
Valid signature:   ...6a5c51eb6f946b30d
Invalid signature: ...6a5c51eb6f946b30d0000
```

単純な長さの確認を加えれば、この脆弱性は直り、攻撃者が署名の末尾に 0 を足したり取り除いたりして、無効な署名を作ることを防げます。

```javascript
  if(sig.length !== 128) {
    return false;
  }
```

この脆弱性は、合意の不一致という問題につながりえます。こうした無効な署名を正しく拒否するライブラリがある一方で、elliptic はこの不正な署名を受理してしまい、あるメッセージに対して有効な署名を複数作れてしまうからです。
ただし、署名を読み取ったあとは、末尾の 0 が取り除かれ、内部の署名の表現は正しい形になります。この脆弱性には [CVE-2024-42459](https://nvd.nist.gov/vuln/detail/CVE-2024-42459) が割り当てられました。

#### ECDSA

失敗した 2 つのテストベクタは、無効な署名のエンコードを受理しており、EDDSA の問題と同じ、1 つのメッセージに有効な署名が複数ありうるという問題につながっていました。どちらの問題も、DER でエンコードされた署名の仕様に関わるものでした。

**1 つ目の問題**は、ビットの配置が不正なことに起因します。r と s の最初のビットは、正の整数であることを示すために 0 でなければなりません。しかし、DER でエンコードされた署名を読み込むとき、この性質は一度も確認されず、暗黙のうちに 0 だと仮定されています。
この暗黙の仮定により、複数のエンコードが可能になりますが、DER では複数のエンコードは認められていません。

この問題を直すには、DER の読み込み関数に、該当する位置の確認を加える必要があります。

```javascript
Signature.prototype._importDER = function _importDER(data, enc) {
  ...
  if ((data[p.place] & 128) !== 0) {
    return false;
  }
  ...

  if ((data[p.place] & 128) !== 0) {
    return false;
  }
  ...
}
```

新しいコードを実行すると、そのテストベクタの署名は無効と判定され、正しく拒否されます。この脆弱性には [CVE-2024-42460](https://nvd.nist.gov/vuln/detail/CVE-2024-42460) が割り当てられました。

**2 つ目の問題**は、1 つ目の問題に似ています。DER エンコードは、Tag-Length-Value(タグ・長さ・値)の形式に従います。エンコードの例を次に示します。

```text
<Tag><Lenght><Value>
  02    20    813ef79ccefa9a56f7ba805f0e478584fe5f0dd5f567bc09b5123ccbc9832365
```

長さのフィールドは 16 進数でエンコードされ、値のフィールドが何バイトを占めるかを示します。長さのフィールドには、長さの先頭に 0 のビットを含めてはいけませんが、これは明示的に確認されていません。DER データの長さを読み取る `getLength` 関数はこの確認をしないため、複数の DER エンコードが許されてしまいます。

```javascript
function getLength(buf, p) {
  ...
  if(buf[p.place] === 0x00) {
    return false;
  }
  ...
}
```

長さのパラメータが 0 でないことを保証する確認を加えると、無効な署名は失敗するようになり、テストベクタを満たします。[CVE-2024-42461](https://nvd.nist.gov/vuln/detail/CVE-2024-42461)

#### まとめ

このような間違いを見つけるのは難しいことがありますが、Wycheproof のテストベクタを使えば、こうしたコーナーケースを見つけやすくなります。
構成ごとに少し手直しするだけで使い回せるテスト用ハーネスを作ることに時間をかければ、こうした脆弱性を見逃さないために大いに役立ちます。
