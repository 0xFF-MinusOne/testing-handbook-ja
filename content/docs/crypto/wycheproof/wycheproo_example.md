---
title: "テストハーネスの例"
weight: 30
# bookFlatSection: false
# bookToc: true
# bookHidden: false
# bookCollapseSection: false
# bookComments: false
# bookSearchExclude: false
---

# Python での Wycheproof テストハーネスの例

この節では、GCM モードの AES を実装した Python ライブラリをテストする、簡単なテストハーネスの書き方を紹介します。
AES-GCM の実装の例として、[cryptography](https://pypi.org/project/cryptography/) パッケージを使います。
テストには、Python で最も人気のあるテストフレームワークの 1 つである [pytest](https://pypi.org/project/pytest/) パッケージを使います。

## 前提条件

既存のリポジトリに、Wycheproof のリポジトリをサブモジュールとして追加します。

```bash
git submodule add https://github.com/C2SP/wycheproof.git
```

Wycheproof を使う最初のステップは、すべてのテストベクタを含む JSON ファイルを解析してテストに使える形にし、簡単なテスト関数を書くことです。

## 1. JSON ファイルを解析する

まず、テスト対象の暗号アルゴリズム用のテストベクタを Wycheproof が提供しているかを、`testvectors` または `testvectors_v1` フォルダの中を探して確認します。
AES-GCM の例では、次のファイルを使います。

- `testvectors_v1/aes_gcm_test.json`

すべてのテストファイルは共通の構造を持っています。この構造を使うと、前の節で説明したように、さまざまな構成に一般化できるテストハーネスを書けます。`aes_gcm_test.json` ファイルには、合計 45 個のテストグループがあります。テストグループは、鍵、IV、タグのサイズで区別されます。基になる AES の実装が特定のパラメータのサイズだけをサポートしている場合は、解析の段階でそれ以外を取り除けます。  

テストベクタを読み込んで解析する例を示します。

```python {linenos=inline}
def load_wycheproof_test_vectors(path: str):
    testVectors = []
    try:
        with open(path, "r") as f:
            wycheproof_json = json.loads(f.read())
    except FileNotFoundError:
        print(f"No Wycheproof file found at: {path}")
        return testVectors

    convert_attr = {"key", "aad", "iv", "msg", "ct", "tag"}
    for testGroup in wycheproof_json["testGroups"]:
        if testGroup["ivSize"] < 64 or testGroup["ivSize"] > 1024:
            continue
        for tv in testGroup["tests"]:
            for attr in convert_attr:
                if attr in tv:
                    tv[attr] = bytes.fromhex(tv[attr])
            testVectors.append(tv)
    return testVectors
```

この関数は JSON ファイルを読み込み、関連する属性を 16 進文字列からバイト列に変換します。
今回の AES-GCM の実装は、IV が特定の範囲にあるものだけを許します。そのため、受け付ける IV のサイズでテストグループを絞り込んでいます。
指定したパラメータに対して、Wycheproof は合計 283 個のテストベクタを提供します。

## 2. テストハーネスを書く

テストベクタを解析したら、次のステップはテストハーネスを書くことです。
すでにテストフレームワークがある場合は、Wycheproof のテストベクタを既存のフレームワークに組み込めます。
特に、テストフレームワークは、一部のテストベクタが失敗することを想定できる柔軟さを備えている必要があります。正しい実装ならエラーを発生させて検証を拒否するように、わざと作られたテストベクタがあるためです。ここでは、AES-GCM の実装の暗号化と復号をチェックする、簡単なテストハーネスの書き方を例として示します。

### 暗号化のテストハーネス

pytest の `parametrize` デコレータを使うと、パラメータ化だけが異なる複数のテストを作れます。
暗号化のテストハーネスの例を示します。

```python {linenos=inline}
@pytest.mark.parametrize("tv", tvs, ids=[str(tv['tcId']) for tv in tvs])
def test_encryption(tv):
    try:
        aesgcm = AESGCM(tv['key'])
        ct = aesgcm.encrypt(tv['iv'], tv['msg'], tv['aad'])
    except ValueError as e:
        assert tv['result'] != 'valid', tv['comment']
        return
    if tv['result'] == 'valid':
        assert ct[:-16] == tv['ct'], f"Ciphertext mismatch: {tv['comment']}"
        assert ct[-16:] == tv['tag'], f"Tag mismatch: {tv['comment']}"
    elif tv['result'] == 'invalid' or tv['result'] == 'acceptable':
        assert ct[:-16] != tv['ct'] or ct[-16:] != tv['tag']
    else:
        assert False
```

この関数は、与えられた入力を暗号化して、暗号化の処理をテストします。
暗号化中に `ValueError` が発生した場合、関数は、そのテストベクタが失敗するはずのものであることを確認します。
例外が発生しなかった場合は、暗号化の結果が期待される結果と一致することを検証します。
具体的には次のとおりです。

1. 成功するはずのテストベクタでは、計算したタグと暗号文の両方が正しいことを確認します。
2. 失敗するはずのテストベクタでは、タグと暗号文のどちらかが正しくないことを確認します。

次のコマンドで、pytest を使ってテストを実行できます。

```bash
pytest /file/path/test.py
```

283 個のテストがすべて成功するはずです。

### 復号のテストハーネス

同様に、復号の処理をテストするには、pytest のパラメータ化の機能を使って、テストベクタのあらゆる組み合わせをテストできます。
復号のテスト関数は、AES の実装に固有の例外を処理し、Wycheproof のテストベクタに付いているフラグにもとづいて、期待される結果を検証します。
AES の実装が特定のエラーを返す場合は、各 Wycheproof テストベクタに付いているフラグを使って、その例外を検証できます。

```python {linenos=inline}
@pytest.mark.parametrize("tv", tvs, ids=[str(tv['tcId']) for tv in tvs])
def test_decryption(test_vector):
    try:
        aes_gcm = AESGCM(test_vector['key'])
        decrypted_msg = aes_gcm.decrypt(test_vector['iv'], test_vector['ct'] + test_vector['tag'], test_vector['aad'])
    except ValueError:
        assert test_vector['result'] != 'valid', test_vector['comment']
        return
    except InvalidTag:
        assert test_vector['result'] != 'valid', test_vector['comment']
        assert 'ModifiedTag' in test_vector['flags'], f"Expected 'ModifiedTag' flag: {test_vector['comment']}"
        return
    assert test_vector['result'] == 'valid', f"No invalid test case should pass: {test_vector['comment']}"
    assert decrypted_msg == test_vector['msg'], f"Decryption mismatch: {test_vector['comment']}"
```

cryptography ライブラリがタグを検証できない場合は、`InvalidTag` 例外が発生します。
この関数は、与えられた暗号文を復号しようとして、復号の処理をテストします。
関数は、いくつかの場合を扱います。

1. `ValueError`: `ValueError` が発生した場合、関数は、そのテストベクタが失敗するはずのものかを確認します。  
2. `InvalidTag`: `InvalidTag` 例外が発生した場合、関数は、そのテストベクタが失敗するはずのものであることを検証し、`ModifiedTag` フラグがあることを確認します。  
3. 復号の成功: 例外が発生しなかった場合、関数は、そのテストベクタが成功するはずのものであり、復号されたメッセージが期待される平文と一致することを確認します。

## まとめ

この記事では、Wycheproof のテストベクタと pytest フレームワークを使って、AES-GCM のテストハーネスを書く方法を示しました。
次の内容を扱いました。

- JSON のテストベクタの解析。
- 暗号化と復号の両方のテスト関数の作成。
- テストフレームワークの中でのエッジケースとエラーの処理。

これらの手順に従えば、暗号の実装が堅牢で、期待される標準に適合していることを確かめられます。
