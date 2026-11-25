---
title: "落とし穴と自滅の元"
slug: gotchas-and-footguns
weight: 40
---

# Rust の落とし穴と自滅の元

このセクションでは、Rust コードを手動でレビューするときに使えるチェックリストを示します。このリストは、私たちが監査で遭遇したよくある問題をまとめたものです。網羅的ではありませんが、監査をすばやく始めるための足がかりになります。

## safe なコードの場合

{{< checklist >}}

- [ ] 文字列の比較を確認する。
  - 等価比較の代わりに、部分一致(`starts_with`、`ends_with`、`contains`)が使われていることがよくあります。
  - 比較で大文字小文字を区別するかどうかが、問題の原因になることがよくあります。
- [ ] 文字列から別のデータ型(`Vec` など)への変換と、その逆の変換を確認する。UTF-8 のエンコードに関する問題が伴うことがあります。有効な UTF-8 でない可能性があるバイト列の扱い方には、次の選択肢があります。
  - `unwrap` 付きの `from_utf8`: 厳密。変換できないデータでパニックする
  - `from_utf8_lossy`: 損失あり。無効な UTF-8 列を U+FFFD(置換文字)に置き換える
  - `OsStr`/`OsString`: プラットフォーム固有の文字列向け。`to_str` メソッドは、UTF-8 でないデータに対して None を返す
- [ ] `Vec`、`HashMap`、`HashSet`、`indexmap::IndexSet` の各型(およびほかの型)の `with_capacity` メソッドが、ユーザーが制御できるデータで呼ばれていないことを確認する。大きな値は、サービス拒否につながるおそれがあります。
  - 渡される容量が `isize::MAX` バイトより小さいことも、[パニックを防ぐために](https://doc.rust-lang.org/std/vec/struct.Vec.html#panics)確認します。
  - [Serde の `size_hint`](https://github.com/serde-rs/serde/issues/744) のように、`with_capacity` メソッドを間接的に公開するメソッドもあるので注意してください。
- [ ] ユーザーが、任意に深い再帰的な構造体を作れないことを確認する。そのような構造体を drop すると、スタックオーバーフローにつながるおそれがあります。(例は[「If a Tree Falls in a Forest, Does It Overflow the Stack?」](https://matklad.github.io/2022/11/18/if-a-tree-falls-in-a-forest-does-it-overflow-the-stack.html)を参照。)
- [ ] `std::process::exit` を使うのを最小限にしていることを確認する。この関数を呼ぶとプロセスが即座に終了し、登録済みの drop ハンドラがすべて迂回されます。
- [ ] 配列にアクセスする前に、適切な境界チェックを行っていることを確認する。範囲外の配列アクセスは、サービス拒否につながるおそれがあります。
- [ ] 型変換の前に、精度の損失を防ぐための適切なチェックを行っていることを確認する(たとえば `u64` から `f64` への変換では、`f64` 型の仮数部が 53 ビットしかありません)。
- [ ] [`serialize_struct` メソッドに渡すフィールド数が、実際にシリアライズされるフィールド数と一致している](https://github.com/trailofbits/dylint/tree/master/examples/general/wrong_serialize_struct_arg)ことを確認する。`serde-binary` など一部のシリアライズ形式では、フィールド数が正しくないと、シリアライズされたデータが切り詰められる可能性があります。つまり、そのデータをデシリアライズすると、元の値とは異なる値になります。
- [ ] 秘密情報を、伸長できる `Vec` にシリアライズしてから、あとで `Zeroizing` で包むことを避ける。再割り当てにより、以前のヒープ上のコピーがゼロクリアされないまま残るおそれがあります。
- [ ] パニックを起こしうるメソッドと操作をすべてレビューする。パニックにつながる操作のレビューに役立つツールは、このハンドブックのほかのセクションで説明しています。
  - `unwrap` と `expect`(パニックを起こす最も一般的なメソッド)
  - [`todo!`](https://doc.rust-lang.org/std/macro.todo.html)、[`unimplemented!`](https://doc.rust-lang.org/std/macro.unimplemented.html)、[`assert!`](https://doc.rust-lang.org/std/macro.assert.html)、[`unreachable!`](https://doc.rust-lang.org/std/macro.unreachable.html) の各マクロ
  - 範囲外アクセス
  - 大きなメモリ割り当て(`MAX` の上限を超えるとパニック、OOM エラーでは異常終了する)
  - 文字の境界でない位置での文字列のスライス
  - `RefCell`
    - この構造体は借用の規則を実行時に強制するため、`borrow`/`borrow_mut` の呼び出しはパニックする可能性があります。
  - [`HeaderMap`](https://docs.rs/http/latest/http/header/struct.HeaderMap.html#limitations)
    - この構造体は、32,768(2^15)個を超える要素を追加するとパニックします。
  - `Duration::from_secs_f{32,64}` and `Duration::new`
    - `Duration::from_secs_f{32,64}` は負の入力でパニックします。`Duration::new` は、超過したナノ秒を秒に繰り上げて正規化し、その繰り上げで秒のカウンタがオーバーフローしたときだけパニックします。
- [ ] コレクションの中にあるキーが、ハッシュと等価性(`HashMap`)や順序(`BinaryHeap`)を変えるような形で変更されていないことを確認する。そうした変更はロジックのエラーであり、パニックや誤った結果を招くおそれがあります。
- [ ] `debug_assert!` などのデバッグ用マクロが、実際のデータ検証に使われていないことを確認する。これらのマクロは、本番ビルドでは取り除かれます。
- [ ] ファイルディスクリプタの使い方を確認する
  - 生のファイルディスクリプタが、すべての実行パスで明示的に閉じられていることを確認します。生のディスクリプタは `Drop` では閉じられません。
  - 所有するファイルディスクリプタが、`Drop` による自動的な処理と、[`close` メソッド](https://docs.rs/nix/latest/nix/unistd/fn.close.html)による明示的な処理で、2 回閉じられていないことを確認します。
  - 生のファイルディスクリプタの使い方が [I/O safe](https://github.com/rust-lang/rfcs/blob/master/text/3128-io-safety.md) であることをレビューします。
- [ ] フラッシュのエラーを受け取るために、`BufWriter` を明示的にフラッシュする。値が drop されるときの自動フラッシュでは、エラーが無視されます。
- [ ] [`PathBuf::join`](https://doc.rust-lang.org/std/path/struct.PathBuf.html#method.join) に絶対パスを使っていないことを確認する。パストラバーサルの問題につながるおそれがあります。
- [ ] テストでしか使わない関数が、`#[cfg(test)]` で保護されていることを確認する。
- [ ] `#![allow(...)]` の使用それぞれに正当な理由があり、`#[allow(...)]` が使われすぎていないことを確認する。
- [ ] ビット演算子(`&`、`^`、`|`)と比較演算子(`==`、`!=`)の優先順位は、Rust と C で異なる。C のコードを書き換えるときは注意が必要です。
- [ ] テスト専用の Cargo のフィーチャー(モックなど)が、`[dependencies]` に含まれておらず、`default` フィーチャーセットにも含まれていないことを確認する。プロジェクトの検証には `cargo tree -e features` を使います。
- [ ] オペレーティングシステムとのやり取りに起因しうる問題がないか、コードをレビューする(考え方は [C/C++ の章]({{% relref "/docs/languages/c-cpp" %}})を参照)。システムコール、libc の関数呼び出し、そのほかのオペレーティングシステムとのやり取りは、既知の落とし穴に照らして確認します。
- [ ] [「Secure Rust Guidelines checklist」](https://anssi-fr.github.io/rust-guide/checklist.html)を確認する。

{{< /checklist >}}

## unsafe なコードの場合

unsafe なコードで確認すべきよくある問題を、次に挙げます。詳しくは、[Rustonomicon](https://doc.rust-lang.org/nomicon/intro.html) を読んでください。

{{< checklist >}}

- [ ] Rust では、union へのアクセスはすべて unsafe です。実際のデータに合ったユニオンのフィールドが使われていることを確認する。
- [ ] `memset` や `memcpy` のような libc API の使用を探す。その多くは、safe な Rust の対応するものに置き換えられます。
- [ ] 構造体に `#[repr(packed)]` が使われている場合は、アラインされていないフィールドに `read_unaligned`/[`write_unaligned`](https://doc.rust-lang.org/std/ptr/fn.write_unaligned.html#on-packed-structs) が使われていることを確認する。
- [ ] [`std::mem::uninitialized`](https://doc.rust-lang.org/std/mem/fn.uninitialized.html) と `mem::zeroed` の使用を確認する。
- [ ] `MaybeUninit` の使い方をレビューし、`assume_init` の呼び出しがすべて、初期化のあとに行われていることを確認する。
  - 部分的にしか初期化されていないデータの drop が、正しく実装されていることを確認します。
- [ ] [`std::mem::forget`](https://doc.rust-lang.org/std/mem/fn.forget.html) の使用を確認する。
- [ ] 変更不可の参照 `&` から変更可能な `&mut` への `transmute` や `cast` の使用を確認する(未定義動作の可能性が高い)。
  - [`bytemuck`](https://docs.rs/bytemuck/latest/bytemuck/) や [`zerocopy`](https://docs.rs/zerocopy/latest/zerocopy/) のクレートを使うほうが、より安全な代替手段になる場合があります。
- [ ] `static mut` の使い方をレビューし、[代わりに同期を使うよう勧める](https://github.com/rust-lang/rust/issues/53639)。
- [ ] `#[unsafe(no_mangle)]` のような [unsafe 属性](https://github.com/rust-lang/rfcs/blob/master/text/3325-unsafe-attributes.md)の使い方をレビューする。

{{< /checklist >}}
