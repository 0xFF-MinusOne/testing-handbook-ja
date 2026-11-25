---
title: "AddressSanitizer"
slug: asan
weight: 3
---


# AddressSanitizer {#addresssanitizer}
<!-- TODO dd comment to move this to a better place. Potentially outside the fuzzing chapter -->

AddressSanitizer (ASan) は、ソフトウェアテスト、とくにファジングで広く使われているツールです。ASan は、バッファオーバーフローや use-after-free のような、見逃されがちなメモリエラーの検出に役立つため、ファジングでの利点が大きいといえます。

ASan はこうした脆弱性を見つけるのに効果的なので、ファジングでは標準的に使われていますが、いくつか欠点もあります。



* 大きな欠点の 1 つは、ファジングが約 2〜4 倍遅くなることです。この速度の低下は、テストの信頼性と深さを高めることとのトレードオフです。
* ASan は、Linux 以外のプラットフォーム (Windows と macOS) では十分にサポートされていません。
* ASan は、OS から大量の仮想メモリ (通常は約 20TB) をマップします。(この量はかつて 16TB、つまりアドレス空間の 1/8 でした。[AddressSanitizer: A Fast Address Sanity Checker](https://www.usenix.org/sites/default/files/conference/protected-files/serebryany_atc12_slides.pdf) を参照してください。) そのため、使っているファザーによるメモリ制限を無効にする必要があります (例: libFuzzer なら `-rss_limit_mb 0`、AFL++ なら `-m none`)。


こうした制限はあるものの、ファジングで ASan を使い、メモリエラーの検出能力を高めてソフトウェアの安全性と信頼性を向上させる利点は、欠点を上回ることが多く、ソフトウェア開発のライフサイクルで価値あるツールです。

ユニットテストでも ASan を有効にするのは理にかなっています。ただし、本番環境では ASan を使わないでください。[アプリケーションがかえって安全でなくなる](https://www.openwall.com/lists/oss-security/2016/02/17/9)ことがあるためです。ASan は、あくまで検出のためのツールです。

一般に、ASan はコンパイル時とリンク時にフラグ `-fsanitize=address` を指定して有効にします。ただし、組み込み方法はファザーごとに異なります。そのため、次のセクションを参照してください。

* C/C++
    * [libFuzzer: AddressSanitizer]({{% relref "/docs/fuzzing/c-cpp/10-libfuzzer#addresssanitizer" %}})
    * [AFL++: AddressSanitizer]({{% relref "/docs/fuzzing/c-cpp/11-aflpp#addresssanitizer" %}})
* Rust: 
    * [cargo-fuzz: AddressSanitizer]({{% relref "/docs/fuzzing/rust/10-cargo-fuzz#addresssanitizer" %}})

ASan は [Google GitHub](https://github.com/google/sanitizers/wiki/AddressSanitizer) で文書化されています。環境変数 `ASAN_OPTIONS` で ASan を設定するフラグについて詳しく知りたい場合は、サニタイザ共通のフラグについては[このページ](https://github.com/google/sanitizers/wiki/SanitizerCommonFlags)を、ASan 固有のフラグについては[こちらのページ](https://github.com/google/sanitizers/wiki/AddressSanitizerFlags)を参照してください。設定例は次のとおりです。


```shell
ASAN_OPTIONS=verbosity=1:abort_on_error=1
```

よく使われるフラグは次のとおりです。

* `verbosity=1`: 実際のプログラムが始まる前に情報を表示します。ASan の出力が表示されるかどうかで、バイナリがサニタイズされているかを確認するのに便利です。
* `detect_leaks=0`: [リークサニタイザ](https://github.com/google/sanitizers/wiki/AddressSanitizerLeakSanitizer)を有効にするかどうかを制御します。リークがあってもファザーはすぐにはクラッシュしませんが、リークの結果はファジングキャンペーンの最後に表示されます。
* `abort_on_error=1`: エラーを表示したあと、[`_exit`](https://man.archlinux.org/man/_exit.3.en) ではなく [`abort`](https://man.archlinux.org/man/abort.3p) を呼び出します。[`abort`](https://man.archlinux.org/man/abort.3p) の呼び出しを必要とする一部のファザーで便利です。

ASan を使うときによくある落とし穴は、[GitHub の FAQ](https://github.com/google/sanitizers/wiki/AddressSanitizer#faq) にまとまっています。

Clang を使っている場合は、その[ドキュメント](https://clang.llvm.org/docs/AddressSanitizer.html)を参照してください。GCC を使っている場合は、こちらの[ドキュメント](https://gcc.gnu.org/onlinedocs/gcc/Instrumentation-Options.html#index-fsanitize_003daddress)も参照してください。
