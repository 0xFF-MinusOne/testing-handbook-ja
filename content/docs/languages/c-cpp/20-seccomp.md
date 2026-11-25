---
title: "Seccomp/BPF"
slug: seccomp
aliases:
- lang-c-cpp-seccomp
weight: 20
---

# Seccomp

[サンドボックス化は難しい](https://www.youtube.com/watch?v=gJpaxisyQfY)ものです。それでも必要で、seccomp を使う場合は、次のことを確認してください。

{{< checklist >}}

- [ ] BPF フィルタが[アーキテクチャを確認している](https://man7.org/linux/man-pages/man2/seccomp.2.html#:~:text=Because%20numbering%20of%20system%20calls%20varies%20between%20architectures%20and) (例: `x86-64` と `i386`)。
- [ ] BPF フィルタが [ABI/呼び出し規約を確認している](https://man7.org/linux/man-pages/man2/seccomp.2.html#:~:text=The%20arch%20field%20is%20not%20unique%20for%20all%20calling%20conventions.) (例: `x86-64` アーキテクチャでの `x86-64` と `x32` の ABI)。
  - つまり、`0x40000000` (`__X32_SYSCALL_BIT` フラグ) より大きい番号のシステムコールを確認するということです。
- [ ] [`vsyscall` と `VDSO` で実装されたシステムコールが正しく扱われている](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html#caveats)。
  - これが重要なのは、`gettimeofday`、`time`、`getcpu`、`clock_gettime` のような、最適化されたシステムコールだけです。
  - seccomp と `VDSO` の相互作用については、さらなる調査が必要です。
- [ ] [`io_uring` のシステムコールがブロックされている](https://manpages.debian.org/unstable/liburing-dev/io_uring_setup.2.en.html)。
  - これらのシステムコールを使うと、プログラムが、BPF フィルタに気づかれずに一部のシステムコールを実行できます。なお、[Docker は既定で `io_uring` のシステムコールをブロックします](https://github.com/moby/moby/pull/46762)。
- [ ] 意味的に等価なシステムコールがすべて同じ方法で扱われている (例: `chmod`、`fchmod`、`fchmodat`、`fchmodat2`、`seccomp`、`prctl(PR_SET_SECCOMP)`)。
  - [カーネルのシステムコール表](https://github.com/torvalds/linux/blob/master/arch/x86/entry/syscalls/syscall_64.tbl)を参照してください。
- [ ] カーネル内でのコード実行を可能にするシステムコール (例: `kexec_file_load`、`finit_module`) が防がれている。
  - 悪意のあるカーネルモジュールは、seccomp のサンドボックスを簡単に操作できます。
- [ ] 次のシステムコールのいずれかがブロックまたはトレースされている場合、[`restart_syscall` システムコールもブロックまたはトレースされている](https://github.com/moby/moby/commit/5abd881883883a132f96f8adb1b07b5545af452b): `poll`、`nanosleep`、`clock_nanosleep`、`futex`。
- [ ] 必要なら、古いカーネルのバージョンに対応している。
  - [ ] Linux カーネル 5.4 より前のバージョンでは、BPF フィルタが [`compat` システムコールの混同を確認している](https://man7.org/linux/man-pages/man2/seccomp.2.html#:~:text=Additionally%2C%20kernels%20prior%20to%20Linux%205.4%20incorrectly%20permitted%20nr) (つまり、`__X32_SYSCALL_BIT` ビットを付けて 64 ビット ABI のシステムコールを呼び出すこと)。
  - [ ] Linux カーネル 4.8 より前のバージョンでは、BPF フィルタが、[サンドボックス化されたすべてのプロセスで `ptrace` の使用を無効にしている](https://www.exploit-db.com/exploits/46434)。
  - [ ] きわめて古い Linux カーネルのバージョンでは、サンドボックスが、seccomp 関連のシステムコールではなく、[`/proc` ファイルシステムへのアクセスをブロックしている](https://lkml.indiana.edu/hypermail/linux/kernel/0706.1/2525.html)。
  - [ ] Android の LG のカーネルにある、[バグのある `sys_set_media_ext` システムコールが正しく扱われている](https://chromium.googlesource.com/chromium/src/+/refs/heads/main/sandbox/linux/seccomp-bpf/sandbox_bpf.cc#59)。
- [ ] システムコールの特別な処理が必要な場合 (単純な許可/不許可ではない場合)、[landlock](https://docs.kernel.org/userspace-api/landlock.html) や[名前空間](https://man7.org/linux/man-pages/man7/namespaces.7.html)のような仕組みが使われている。
- [ ] システムコールの特別な処理が必要で、その作業に seccomp を使わなければならない場合、`SECCOMP_SET_MODE_FILTER` オプションを、`SECCOMP_RET_TRACE` アクションと `ptrace` とともに使っている。
  - [ ] `SECCOMP_SET_MODE_FILTER` を、`SECCOMP_FILTER_FLAG_NEW_LISTENER` や `seccomp_unotify` とともに使っていない。この仕組みは本質的に安全ではありません。[`seccomp_unotify` の man ページ](https://man7.org/linux/man-pages/man2/seccomp_unotify.2.html)を参照してください。
  - [ ] 似た[システムコールのユーザーディスパッチの仕組み](https://www.kernel.org/doc/html/v6.1/admin-guide/syscall-user-dispatch.html)も、本質的に安全ではない。
  - [ ] `SECCOMP_RET_USER_NOTIF` アクションは `SECCOMP_RET_TRACE` アクションより優先される。seccomp のサンドボックスを有効にしたあとは、`SECCOMP_RET_USER_NOTIF` の追加を許してはならない。最も安全な解決策は、`seccomp` と `prctl(PR_SET_SECCOMP)` をまとめて禁止することです。
  - [ ] 下の、BPF フィルタのハンドラと `ptrace` のチェックリストを参照している。
{{< /checklist >}}

## BPF フィルタのハンドラと ptrace

seccomp フィルタが `SECCOMP_RET_TRACE` アクションを使う場合は、すべての BPF フィルタのハンドラをレビューする必要があります。これらのハンドラは通常、サンドボックス化されたプロセス (「トレーシー」) を `ptrace` の仕組みでトレースしているプロセス (「トレーサー」) に実装されます。次のことを確認してください。

{{< checklist >}}

- [ ] すべての `ptrace` のトレースオプション (例: `PTRACE_O_TRACEFORK`、`PTRACE_O_TRACECLONE` など) をトレーシーに使っている。
  - そうしないと、トレーシーが子プロセスを作って `execve` を呼び出し、サンドボックスから脱出するおそれがあります。
- [ ] サンドボックス化されたすべてのプロセスに `PTRACE_O_EXITKILL` が設定されている。
  - そうしないと、トレーサーのプロセスがクラッシュしたときに、悪意のあるプロセスが、サンドボックス化されたトレーシーをトレースして、すべての `SECCOMP_RET_TRACE` アクション (`ptrace-stop` イベント) を処理できてしまいます。
- [ ] トレーシーがトレーサーに影響を与えるのに使えるシステムコールが禁止されている。
  - トレーサーの TID を指定した `rt_sigqueueinfo` と `rt_tgsigqueueinfo`
  - トレーサーの TID を指定した `kill`、`tgkill`、`tkill`
  - トレーサーの TID を指定した `setpriority`、`sched_{setaffinity,setattr,setparam,setscheduler}`、`prlimit64`
  - トレーサーの TID を指定した `process_vm{writev,readv}`
  - `/proc/<tracer-pid>` と `/proc/<tracer-pid>/task/<tracer-tid>` に対する `open`、`rename` などの似たシステムコール
- [ ] `ptrace-stop` イベントを起こしたシステムコールを特定するのに、[正しいシステムコール表が使われている](https://github.com/strace/strace/issues/103)。
  - この情報はイベントには含まれません。
  - システムコール番号を特定するには、トレーサーは次のようにできます。
    - 新しいカーネルでは `PTRACE_GET_SYSCALL_INFO` を使う
    - 古いカーネルでは、レジスタを読み (例: `PTRACE_GETREGSET` で)、次を確認する (これは少し厄介で、TOCTOU のバグが起きやすいことが多い)。
      - レジスタのビット幅 (`RAX` と `EAX`)
      - システムコールの実行に使われた命令 (x64 の `int 0x80` と `sysenter` 命令は x86 の表を使い、`syscall` は x64 の表を使う)
      - CS レジスタのフラグ
      - `vsyscall` の仕組みを使っているか (`RIP & ~0x0C00 == 0xFFFFFFFFFF600000`)
        - 使っている場合、実行された命令を見つけるのはより複雑になり、保存された RIP を見つけるためにスタックを解析する必要がある。
  - カーネルは、システムコール番号を int にダウンキャストします ([少なくとも現代のカーネルはそうです](https://elixir.bootlin.com/linux/v6.13.3/source/arch/x86/entry/entry_64.S#L113-L121)。64 ビットと 32 ビットの両方のシステムコール表で)。そのため、BPF フィルタは、システムコール番号に 32 ビットのオペコードを使うべきです。
- [ ] ハンドラが、引数 (レジスタ) を ABI に従って解釈している ([値が黙って切り詰められることがあります](https://man7.org/linux/man-pages/man2/seccomp.2.html#:~:text=When%20checking%20values%20from%20args%2C%20keep%20in%20mind%20that%20arguments%20are))。
  - BPF フィルタとハンドラは、引数のビット幅について一致している必要があります。ビット幅を確かめるには、[BPF オペコードのドキュメント](https://www.kernel.org/doc/html/v5.17/bpf/instruction-set.html)を確認してください。
- [ ] メモリレベルの競合状態に対処している。
  - トレーサーがトレーシーのメモリを読む場合、そのメモリが、(1 つのスレッドグループまたはプロセスの中の) 別のスレッドや、(メモリを明示的に共有している場合は) 別のプロセスによって、非同期に変更されている可能性があります。この競合状態を完全に直すのは困難です。
  - 単一のプロセスなら、この競合状態は、システムコールの入口のフックが呼ばれたときにトレーシーの他のすべてのスレッドを一時停止し、システムコールの出口で再開することで直せます。タスク (プロセスまたはスレッド) のグループを一時停止するには、Linux カーネルの機能である cgroups (コントロールグループ) を使えます。[cgroups v1 では、freezer コントローラ/サブシステム](https://docs.kernel.org/admin-guide/cgroup-v1/freezer-subsystem.html)を使えます。[cgroups v2 では、`cgroup.freeze` ファイル](https://docs.kernel.org/admin-guide/cgroup-v2.html)に書き込むことで、cgroup 内のすべてのタスク (と、すべての子孫の cgroup のタスク) を凍結できます。[cgroup v2 のドキュメントの Thread Granularity のセクション](https://docs.kernel.org/admin-guide/cgroup-v2.html#thread-granularity)も読むことをおすすめします。
  - 共有メモリの競合状態から守るには、トレーサーは、そのメモリマップを共有しているすべてのプロセスを凍結する必要があります。あるいは、メモリを排他的にロックする方法もあります (他のプロセスがロックを解除できないことが前提です。この解決策には、さらなる調査が必要です)。
  - [`userfaultfd`](https://man7.org/linux/man-pages/man2/userfaultfd.2.html) システムコールを使うと、[攻撃者が 100% の確実さで競合に勝てます](https://github.com/rexguowork/phantom-attack/blob/main/phantom_v1/attack_openat.c#L238)。
- [ ] オペレーティングシステムレベルの競合状態に対処している。
  - シンボリックリンクによるファイルパスの変更や、トレーシーのリソース (カレントワーキングディレクトリ、環境変数、ファイルディスクリプタ、`/proc/<pid>` 以下のあらゆるもの) の変更など、一般的な脆弱性がすべて当てはまります。
  - 上の 2 つの競合状態は、ハンドラの実行中だけでなく、ハンドラとカーネルの実行の間 (システムコールの中) でも起こりうることに注意してください。
- [ ] システムコールを破棄 (スキップ) すべき場合、それを `syscall-exit-stop` ではなく `syscall-enter-stop` (または `ptrace-stop`) で行っている。`syscall-exit-stop` イベントはシステムコールの実行後に起こるため、その停止でシステムコールの戻り値を変更してエラーを示しても、システムコールはすでに実行されており、その影響は元に戻せません。
- [ ] ハンドラ内でトレーシーを強制終了すべき場合、それを `SIGKILL` で行っている (つまり、すぐに終了させる)。ハンドラが戻ってから終了するまでの間にトレーシーが実行できてしまうような、遅延のある仕組みでは行わない。
- [ ] シグナルと `ptrace` のイベントが正しく扱われている。
  - [ ] [`syscall-enter-stop` と `syscall-exit-stop`](https://man7.org/linux/man-pages/man2/ptrace.2.html#:~:text=If%20the%20tracee%20was%20restarted%20by%20PTRACE_SYSCALL%20or%20PTRACE_SYSEMU) のイベントを、トレーサーが正しく追跡しなければならない。`ptrace` API には、この 2 つを区別する手段がありません。よくあるエクスプロイトは、トレーシーに `SIGTRAP` シグナルを手動で送るか、トレーシーに `int 3` (ソフトウェア割り込み命令) を実行させて、ハンドラを混乱させるものです。よくある解決策は `PTRACE_O_TRACESYSGOOD` オプションを使うことです。これにより、トレーサーは `syscall-{enter,exit}-stop` とその他の `stop` コマンドを簡単に区別できます。
  - [ ] `SIGKILL` はプロセスを突然終了させることができ、そのイベントを正しく処理しなければならない。
    - `syscall-exit-stop` イベントは、システムコールの実行後に配信されないことがあります。システムコールのトレースは `syscall-enter-stop` の中で始め、`syscall-exit-stop` またはトレーシーの終了イベントのどちらかの中で終えるべきです。そうしないと、実行されたシステムコールをトレーサーが見逃すことがあります。
    - [`ptrace` の man ページ](https://man7.org/linux/man-pages/man2/ptrace.2.html#:~:text=The%20tracer%20cannot%20assume%20that%20the%20ptrace%2Dstopped%20tracee%20exists)によれば、「トレーサーは、ptrace で停止したトレーシーが存在すると仮定できない」とされています。
    - `PTRACE_EVENT_EXIT` イベントは、[カーネルのバージョンによって](https://man7.org/linux/man-pages/man2/ptrace.2.html#:~:text=depending%20on%20the%0A%20%20%20%20%20%20%20kernel%20version%3B%20see%20BUGS%20below)、`SIGKILL` のあとに配信されることも、されないこともあります。
  - [ ] `WIFEXITED(status)` と `WIFSIGNALED(status)` を伴うシグナルは、[トレーシーの終了時に必ず配信されるとは限りません](https://github.com/facebookexperimental/reverie/issues/15)。たとえば、(スレッドグループのリーダーではない) スレッドが `execve` を呼び出したときには配信されません。トレーサーは、トレーシーのあらゆる終了を検出するために、`PTRACE_EVENT_EXEC` も使うべきです。
  - [ ] 新しいプロセスが fork または clone されると、`PTRACE_EVENT_CLONE` (親向け) と `PTRACE_EVENT_STOP` (子向け) のシグナルが、順序が決まらないまま同時に配信される。この挙動により、競合状態のバグが起こりうる。
- [ ] `CLONE_UNTRACED` フラグを付けた `clone` システムコールが許可されていない。
  - このフラグを使うと、トレーシーは、子が元のトレーサーにトレースされない形で clone できます。トレーシーはその後、新しいスレッドに `ptrace` でアタッチして、すべての `SECCOMP_RET_TRACE` アクションを処理できます (関連する seccomp フィルタを事実上無効にできます)。なお、この手口は、システムコールを明示的に破棄する seccomp アクション (`SECCOMP_RET_ERRNO` など) には効かず、これらは引き続きブロックされます。この脆弱性を防ぐには、次のことが必要です。
    - `clone` システムコールを処理して、`ptrace-stop` イベントでフラグを取り除くか、そのフラグ付きの `clone` をブロックする (ブロックは、間違いが起きにくいため、BPF で実装すべきです)。
      - `clone3` システムコールはブロックし、[その戻り値を `ENOSYS` に設定する](https://github.com/moby/moby/commit/9f6b562d)必要があります。このシステムコールは引数をメモリに格納するため、BPF フィルタでは調べられません。`ptrace` のハンドラは TOCTOU 攻撃に対して脆弱になります。`ENOSYS` エラーを返すと、プログラムは `clone` を使う方法に切り替えます。
    - カーネルが、[`clone` の引数の順序を逆にしている](https://www.kernelconfig.io/config_clone_backwards3)ことがあります (`CONFIG_CLONE_BACKWARDS*` の設定。[Flatpak の seccomp の実装](https://github.com/flatpak/flatpak/blob/9766ee05b1425db397d2cf23afd24c7f6146a69f/common/flatpak-run.c#L2937-L2944)を参照してください)。
- [ ] トレーサーが `PTRACE_PEEK*` の `ptrace` 呼び出しを使う場合、エラーが正しく処理されている。戻り値ではなく `errno` を確認しなければならない。
- [ ] トレーサーの `ptrace(ATTACH/SEIZE)` 呼び出しの戻り値が確認されている。
  - エラーは、サンドボックス化が有効に働いていないことを意味します。悪意のあるプロセスが、トレーシーへのアタッチを試みるおそれがあるためです。
  - トレーシー (または悪意のあるプロセス) は、`prctl(PR_SET_PTRACER)` や `prctl(PR_SET_DUMPABLE, 0)` を使う、YAMA ポリシー (`/proc/sys/kernel/yama/ptrace_scope`) を変更するなど、複数の方法でエラーを強制しようとするかもしれないことに注意してください。
- [ ] `vsyscall` の仕組みで実行されるシステムコールが正しく扱われている。
  - このようなシステムコールは、[動的に置き換えられず、破棄することしかできません](https://www.kernel.org/doc/html/latest/userspace-api/seccomp_filter.html#caveats)。
- [ ] 可能なら、次のあまり知られていないシステムコールがブロックされている。これらのシステムコールで seccomp を回避できるはずはありませんが、通常は「念のため」ブロックすべきです。他のシステムコールのフィルタを回避するのに悪用される可能性があるためです。
  - [`modify_ldt`](https://github.com/flatpak/flatpak/issues/4297)
  - `uselib`
  - [ファイルシステムを操作するシステムコール](https://github.com/flatpak/flatpak/security/advisories/GHSA-67h7-w3jq-vh4q) (`chroot`、`pivot_root`、`mount`、`move_mount`、`open_tree`、`fsopen`、`fsmount`)
  - [VM/NUMA の操作](https://github.com/flatpak/flatpak/blob/9766ee05b1425db397d2cf23afd24c7f6146a69f/common/flatpak-run.c#L2926-L2932) (`move_pages`、`mbind`、`set_mempolicy`、`migrate_pages`)

{{< /checklist >}}
