---
title: "Linux カーネル"
slug: linux-kernelmode
aliases:
- lang-c-cpp-linux-kernelmode
weight: 14
---

# Linux カーネル

このリストには、Linux カーネルのドライバとモジュールの基本的なチェック項目が含まれます。

{{< checklist >}}

- [ ] ユーザー空間から来るデータの使用がすべて検証されていることを確認する。
  - コード内の [`__user` タグ](https://elixir.bootlin.com/linux/v6.16/source/include/linux/compiler_types.h#L31)を探す。ユーザー空間のデータすべてにタグが付いているとは限らないが、出発点としては良い。
  - [`copy_from_user(to, from, size)`](https://elixir.bootlin.com/linux/v6.16/source/include/linux/uaccess.h#L205) の使用を検証する。
    - 長さが正しく検証されていること。
    - 初期化されていない `to` アドレスがないこと。
    - 低レベルの [`__copy_from_user`](https://elixir.bootlin.com/linux/v6.16/source/include/linux/uaccess.h#L102) 関数は、[`access_ok`](https://elixir.bootlin.com/linux/v6.16/source/include/asm-generic/access_ok.h#L31) 識別子と一緒に使うこと。
- [ ] [`copy_to_user(to, from, size)`](https://elixir.bootlin.com/linux/v6.16/source/include/linux/uaccess.h#L217) の使用が検証されていることを確認する。
  - `from` のメモリは (構造体のパディングを含めて) 初期化されていること。
- [ ] [`user_access_{begin,end}`](https://elixir.bootlin.com/linux/v6.16/source/include/linux/uaccess.h#L551-L552) の使用をレビューする。
  - これらの呼び出しは、カーネルコードに [SMAP](https://en.wikipedia.org/wiki/Supervisor_Mode_Access_Prevention) を無効化/有効化させる。これらの呼び出しの間にあるコードは、慎重にレビューする必要がある。
- [ ] ユーザー空間からカーネルへの、そのほかの方法をレビューする。
  - 少なくとも次の関数をレビューする: `get_user`、`strncpy_from_user`、`copy_struct_from_user`、`access_process_vm`、`get_user_pages`。
  - `__put_user` や `unsafe_put_user` のように、明示的に安全でない関数の使用は、特に注意してレビューする。
- [ ] カーネルがユーザー空間のメモリを 1 回ではなく 2 回取得またはコピーしている箇所を確認する。これは TOCTOU (ダブルフェッチ) の問題につながる。
  - これは、システムコールの前後のフックが関わっているときによく起こる。
- [ ] コードベースで、ポインタの漏えいがないかレビューする。
  - たとえば、`%p` フォーマット文字列を使うと、カーネルのアドレスが漏れることがある。この問題の緩和策は [`kptr_restrict`](https://www.kernel.org/doc/html/latest/admin-guide/sysctl/kernel.html#kptr-restrict) を使うことである。開発者は `%pK` か `%px` のフォーマット文字列を使うこと。
- [ ] ユーザー空間に渡したファイルディスクリプタ (たとえば [`fd_install`](https://elixir.bootlin.com/linux/v6.16/source/fs/file.c#L637) で渡したもの) を、[カーネルがもう使っていない](https://github.com/torvalds/linux/commit/f1ce3986baa62cffc3c5be156994de87524bab99)ことを確認する。
  - ユーザー空間は、そのディスクリプタに対して `close` や `dup2` を呼び出して別のファイルを指すようにできる。するとカーネルは想定と異なるファイル構造体を使うことになり、use after free のような問題につながることがある。
- [ ] [`strlen_user`](https://elixir.bootlin.com/linux/v3.19.8/source/lib/strnlen_user.c#L126) と `strnlen_user` (古いカーネルでしか使われない) の使用を確認する。これらの関数はヌルバイトを*含む*長さを返す。ユーザー空間の `strlen` 関数とは動作が違うため、混乱のもとになりうる。
- [ ] [`strncpy_from_user`](https://elixir.bootlin.com/linux/v6.16/source/lib/strncpy_from_user.c#L113) の使用を調べる。コピー先の文字列がヌル終端されないことがある (標準ライブラリの `strncpy` と同じ動作)。
- [ ] 参照カウントが[正しく実装されている](https://blog.lexfo.fr/cve-2017-11176-linux-kernel-exploitation-part1.html)ことを確認する (`fget`/`fput`、`sock_hold`/`sock_put`、`get_pid_task/get_task_struct/put_task_struct`、`{get,put}_pid`、`d_find_alias/dget/dput` など)。
  - 二重のデクリメントがないこと (use-after-free の状態を引き起こす)。
  - インクリメントの抜けがないこと (use-after-free の状態を引き起こす)。
  - 二重のインクリメントがないこと (宙に浮いたオブジェクトを引き起こす)。
  - デクリメントの抜けがないこと (宙に浮いたオブジェクトを引き起こす)。
  - 独自の参照カウンタに正しい型が使われていること ([`refcount_t` と `atomic_t`](https://www.kernel.org/doc/html/v4.16/core-api/refcount-vs-atomic.html))。
  - [`try_module_get`](https://www.kernel.org/doc/html/next/driver-api/basics.html#c.try_module_get) のような、参照カウントを取る関数の戻り値が確認されていること。
- [ ] ミューテックスのロックが正しく実装されていることを確認する (`mutex_lock`、`spin_lock`)。
- [ ] 一度だけ初期化される変数に、[`__ro_after_init`](https://www.kernel.org/doc/html/latest/security/self-protection.html#:~:text=For%20variables%20that%20are%20initialized%20once%20at%20__init%20time%2C%20these%20can%20be%20marked%20with%20the%20__ro_after_init%20attribute.) 属性が使われていることを確認する。
- [ ] 動的なメモリ確保が正しいか調べる。
  - [正しい版の free が常に使われている](https://github.com/torvalds/linux/blob/master/scripts/coccinelle/api/kfree_mismatch.cocci) (たとえば `kmalloc-kfree` と `vmalloc-vfree`)。
  - 戻り値を `NULL` と比較して確認している。
  - [確保してから `memset` するのではなく、ゼロ埋めの関数を使っている](https://github.com/torvalds/linux/blob/master/scripts/coccinelle/api/alloc/zalloc-simple.cocci)。
  - [スタックベースの確保 (`vmalloc`) と、対応する解放の間で Oops が起こりえない](https://blog.quarkslab.com/nvidia_gpu_kernel_vmalloc_exploit.html)。
- [ ] グローバルな初期化関数 ([`genl_register_family`](https://www.infradead.org/~tgr/libnl/doc/api/group__genl__mngt.html#gac625c0fe5d060cb587efcbeaa44b3ff2) や [`init_module`](https://elixir.bootlin.com/linux/v6.16/source/include/linux/module.h#L76) など) がメモリを確保する場合、対応する終了処理の関数がそのメモリを解放していることを確認する。
- [ ] カーネルのメモリマッピングの保護を変更するコードでは、システムコールテーブルのような読み取り専用ページが、変更後も読み取り専用のままであることを確認する。
- [ ] 管理操作を実行できたり、(ポインタや設定などを通じて) 機密データを取得できたりするインターフェース (procfs のエントリ、sysfs のファイル、デバイスファイル、ioctl や netlink の操作など) すべてが、root ユーザーと、関連する[ケーパビリティ](https://man7.org/linux/man-pages/man7/capabilities.7.html)を要求することを確認する。
  - 権限の低いユーザーでも、自分の名前空間の中 (たとえば Docker コンテナの内部) では root (UID 0 のユーザー) になれる。ケーパビリティのチェックが抜けていると、root 所有の procfs ファイルにアクセスされたり、[カーネルポインタが漏れたり](https://blog.trailofbits.com/2024/03/08/out-of-the-kernel-into-the-tokens/#:~:text=of%20expected%20algorithms.-,KASLR%20bypass%20in%20privilege%2Dless%20containers,-Next%20is%20a)することがある。
- [ ] 正しいプロセスに対してケーパビリティのチェックが行われていることを確認する。
  - たとえば、呼び出したプロセスだけでなく、そのリソースを作成したプロセスのケーパビリティもチェックする必要がある。詳しくは [CVE-2023-2002](https://marc.info/?l=oss-security&m=168164424404224) を参照。
- [ ] 独自のファイルシステム (`file_system_type` 構造体で定義) とファイル (`file_operations` 構造体で定義) で、[`owner` フィールドが `THIS_MODULE` に設定されている](https://www.kernel.org/doc/html/next/filesystems/vfs.html)ことを確認する。
- [ ] カーネル向けの静的解析を使う。
  - 主なツールは Coccinelle である。[Linux のリポジトリ](https://github.com/torvalds/linux/tree/master/scripts/coccinelle)と [Coccinelle のウェブサイト](https://coccinelle.gitlabpages.inria.fr/website/impact_linux.html)にあるルールと一緒に使う (ルールは手動でダウンロードする必要がある)。

{{< /checklist >}}
