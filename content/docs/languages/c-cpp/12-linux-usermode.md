---
title: "Linux ユーザーモード"
slug: linux-usermode
aliases:
- lang-c-cpp-linux-usermode
weight: 12
---

# Linux ユーザーモード

このリストは、Unix 環境で C/C++ の標準ライブラリを使うときの、よくある確認項目と、ありがちな落とし穴をまとめたものです。

{{< checklist >}}

- [ ] [`checksec`](https://github.com/etke/checksec.rs) を実行して、実行ファイルのエクスプロイト緩和策を調べる。
  - NX、PIE、スタッククッキー、RELRO、`FORTIFY_SOURCE`、スタッククラッシュ対策、SafeStack、ShadowCallStack などの緩和策が使われているかを確認する。
  - 本番向けのリリースにデバッグ情報が含まれていないことを確認する。
- [ ] マルチスレッドのプログラムで、[スレッドセーフでない関数](https://www.gnu.org/software/libc/manual/html_node/POSIX-Safety-Concepts.html)が使われていないかを確認する。
  - これらの関数のうち、[`gethostbyname`](https://man7.org/linux/man-pages/man3/gethostbyname.3.html#:~:text=pointers%20to%20static%20data%2C%20which%20may%20be%20overwritten%20by%20later%20calls.), [`inet_ntoa`](https://linux.die.net/man/3/inet_ntoa), [`strtok`](https://man7.org/linux/man-pages/man3/strtok.3.html)、[`localtime`](https://man7.org/linux/man-pages/man3/localtime.3.html) などは、静的なデータへのポインタを返すことがあります。これらのポインタは、すべて同じデータを指すことがあるので、シングルスレッドのプログラムでも注意して扱う必要があります。
- [ ] シグナルハンドラで再入不可能な関数が使われていないかを確認する。[lcamtuf の記事](https://lcamtuf.coredump.cx/signals.txt)を参照。
  - [ ] シグナルハンドラで `errno` を変更してはならない(または、保存して復元しなければならない)。
- [ ] 比較の処理が、範囲外のデータを読まないことを確認する。
  - `std::equal` は、長さの異なるコレクションに対する 3 つのイテレータで呼ぶと、範囲外を読む。
  - `memcmp` は、サイズの引数が正しく計算されていないと、範囲外を読むことがある。
  - `strncmp` は、長さの異なる文字列と不正なサイズで呼ぶと、範囲外を読むことがある。実際に見つかった文字列比較のバグは、[`cstrnfinder`](https://github.com/disconnect3d/cstrnfinder) を参照。
- [ ] `argv[0]` が NULL ではないと決めつけていないことを確認する。[Qualys の CVE-2021-4034](https://www.qualys.com/2022/01/25/cve-2021-4034/pwnkit.txt) を参照。
- [ ] 環境変数が慎重に扱われていることを確認する。
  - `getenv` と `setenv` は[スレッドセーフではない](https://www.geldata.com/blog/c-stdlib-isn-t-threadsafe-and-even-safe-rust-didn-t-save-us#the-real-culprit-setenv-and-getenv)(ただし、[glibc で最近改善された](https://github.com/bminor/glibc/commit/7a61e7f557a97ab597d6fca5e2d1f13f65685c61))。
  - ユーザーが環境変数を制御できるようにするのは、たいてい安全ではない(たとえば、[bash のエクスポートされた関数](https://archive.zhimingwang.org/blog/2015-11-25-bash-function-exporting-fiasco.html)や [`LIBC_FATAL_STDERR_`](https://github.com/j00ru/ctf-tasks/tree/master/CONFidence%20CTF%202015/Main%20event/Night%20Sky) を考えてみてほしい)。
  - 高い権限のプロセスが、より低い権限のプロセスを作ると、新しいプロセスは、`procfs` ファイルシステム経由で、親プロセスの環境変数を読める。
    - `setenv(SOME_SENSITIVE_ENV, "overwrite", 1)` は、古い環境変数の値をスタックに残す(`/proc/$pid/environ` で読める)。これは DoS の経路にもなりうる点に注意。
    - [`PR_SET_MM_ENV_START`](https://man7.org/linux/man-pages/man2/PR_SET_MM.2const.html)/`PR_SET_MM_ENV_END` の `prctl` 操作を使うと、環境変数を隠せる。親プロセスのスタックメモリの該当アドレスを上書きして、環境変数を隠すこともできる。
  - 汎用のライブラリは、可能なら `getenv` の代わりに [`secure_getenv`](https://www.man7.org/linux/man-pages/man3/getenv.3.html) を使うべき
- [ ] `open` などのファイルシステム関連の関数が、慎重に扱われていることを確認する。
  - `access`(ファイルの存在の確認)を呼んだあとに `open` を呼ぶ処理は、競合状態に対して脆弱。
  - `destination` 引数のどの部分でも攻撃者が制御できる `rename` の呼び出しは、[競合状態に対して脆弱](https://gergelykalman.com/slides/the_forgotten_art_of_filesystem_magic.pdf)。
  - `O_NOFOLLOW` フラグを付けた `open` の呼び出しは、ディレクトリのシンボリックリンクを解決する。たいていは、代わりに `RESOLVE_NO_SYMLINKS` か `O_NOFOLLOW_ANY` を使うべき。
  - `O_CLOEXEC` フラグを付けない `open` の呼び出しは、ファイルディスクリプタを子プロセスにリークする。
- [ ] 権限の放棄(`seteuid`、`setgid` などの使用や、`execve` の呼び出し時のような暗黙の権限の放棄)が、慎重に実装されていることを確認する。
  - 権限を放棄する関数の戻り値は、必ず確認しなければならない。
    - 関数呼び出しの組み合わせによっては、エラーを返さずに権限の放棄に失敗することがある。たとえば、`seteuid(X)` のあとに `setuid(X)` を呼ぶと、エラーなしで成功しても、[権限を永続的には放棄できない](https://www.usenix.org/legacy/events/sec02/full_papers/chen/chen.pdf)ことがある。
    - [グループの権限は、ユーザーの権限より先に放棄すべき](https://www.oreilly.com/library/view/secure-programming-cookbook/0596003943/ch01s03.html#:~:text=As%20discussed%20above%2C%20always%20drop%20group%20privileges%20before%20dropping%20user%20privileges%3B%20otherwise%2C%20group%20privileges%20may%20not%20be%20able%20to%20be%20fully%20dropped.).
    - できれば、放棄したあとに、新しい権限を[明示的に確認する](https://people.eecs.berkeley.edu/~daw/papers/setuid-login08b.pdf)。たとえば、`setuid(X)` のあとに `if (getuid() == X)` を続けるべき。
    - 必要なときは、[`setgroups`](https://linux.die.net/man/2/setgroups) の呼び出しで、補助グループを消さなければならない。
  - 同じアドレス空間で、権限レベルの異なる複数のスレッドを動かすのは危険。[`vfork` の注意点](https://www.man7.org/linux/man-pages/man2/vfork.2.html#CAVEATS)を参照。
  - [`ioperm`](https://linux.die.net/man/2/ioperm) で設定した権限、[レコードロック](https://linux.die.net/man/2/fcntl64)、[インターバルタイマー](https://linux.die.net/man/2/setitimer)、[リソース使用量](https://linux.die.net/man/2/getrusage)の情報は、`execve` の呼び出しをまたいで保たれる(`fork` では保たれない)。
  - ファイルディスクリプタ(通常のもの、[ロック](https://linux.die.net/man/2/flock)、[タイマー](https://linux.die.net/man/2/timerfd_settime)など)、[アフィニティマスク](https://linux.die.net/man/2/sched_getaffinity), [スケジューリングポリシー](https://linux.die.net/man/2/sched_getscheduler)、[シグナルマスク](https://linux.die.net/man/2/rt_sigprocmask)、[セッション ID](https://linux.die.net/man/2/setsid)、[プロセスグループ ID](https://linux.die.net/man/2/getpgid)、[補助グループ](https://linux.die.net/man/2/setgroups)、[リソース制限](https://linux.die.net/man/2/setrlimit)、`NO_NEW_PRIVS` の prctl 設定は、`fork` と `execve` の呼び出しをまたいで保たれる。
  - [ケーパビリティ](https://linux.die.net/man/7/capabilities)の継承は複雑。親プログラムが持っていて、子が継承すべきでないケーパビリティは、すべてマニュアルを読んで確認する。
- [ ] 使うべきでない、安全でない標準ライブラリの関数が使われていないかを探す。
  - そのような関数には、`sprintf`、`vsprintf`、`strcpy`、`stpcpy`、`strcat`、`gets`、`%s` を使った `scanf`(境界の確認なし)、`tmpnam`、`tempnam`、`mktemp`(競合状態)、`alloca`、`putenv`(メモリ管理が複雑すぎる)などがある。
- [ ] 戻り値として返されるエラーが、すべて正しく処理されていることを確認する。
  - `(v)s(n)printf`、`write`、`read` など、負の値を返しうる関数の呼び出しで、戻り値を確認しているかを探す。負の戻り値の誤った扱いは、昔からよくある問題。
  - `mmap` 関数は、エラー時に `NULL` ではなく `MAP_FAILED` を返す。
  - [`atoi`](https://man7.org/linux/man-pages/man3/atoi.3.html) のような関数は、エラーをまったく知らせないので、おそらく使うべきではない。
- [ ] 戻り値だけでは成功と失敗を区別できない関数が、適切に扱われているかを探す。そのような関数では、呼び出しの前に `errno` を消しておかなければならない(そうしないと、`errno` の値が、以前の関数呼び出しの残りかもしれない)。
  - `clock` や `times` のような関数は、エラー時と、クロックティックが正当に一周したときの両方で `-1` を返す。
  - `strtol`、`strtoull`、`pow`、`log` のような関数は、正当な入力と `ERANGE` のオーバーフローの両方で、境界の値(`LONG_MAX` など)を返す。
  - `getchar` や `fgetc` のような関数は、エラー時と、実際のファイルの終端のときの両方で `EOF` を返す。
  - `dlsym` のような関数は、エラー時と、エラーではない正当な場合の一部で `NULL` を返す。戻り値に加えて、`dlerror` も確認しなければならない。
- [ ] `snprintf` の使い方を調べて、戻り値が正しく扱われていることを確認する。
  - 戻り値は紛らわしく、よく誤解される。実際に書き込まれたバイト数ではなく、十分な領域があれば最終的な文字列に*書き込まれたはずの*文字数を返す。
- [ ] 処理を終えていないのに成功を返す関数が、適切に扱われているかを探す。
  - `read` や `write` のような関数は、エラーにならなくても、処理を終えていないことがある。たとえば `read` は、要求した量のバイトを読み終えていないことがあり、おそらく繰り返す必要がある。
- [ ] `write`、`read` など、`EINTR` エラーを処理していない関数の呼び出しで、適切にエラーを処理しているかを探す。
  - 標準ライブラリのほとんどの関数の呼び出しは、このエラーのあと、たいてい繰り返すべき。EINTR エラーについては、[この資料](https://android.googlesource.com/platform/bionic/+/master/docs/EINTR.md)を参照。
  - [`close` 関数は例外](https://lwn.net/Articles/576478/)で、`EINTR` エラーのあとに、もう一度呼んではならない。
- [ ] `snprintf`、`vsprintf`、`memcpy` などの関数の入力に、重なり合うバッファが使われていないかを探す。問題になることがある。
  - 同じバッファを入力と出力に渡すと、未定義動作になることが多い。
  - `source` に `offset` を足したメモリが `destination` と重なっていると、その関数呼び出しは未定義動作になることがある。
- [ ] `strlen` と `strcpy` を組み合わせた使い方を調べる。この組み合わせは、ヌルバイトの数え間違いを起こしやすい。
  - `strlen` は、返す長さに `NULL` 終端を含めないが、`strcpy` は `NULL` をコピーする。詳しくは、[この X の投稿](https://twitter.com/h0mbre_/status/1396529223372840963/photo/1)を参照。
- [ ] `scanf("%d", &x)` への入力を調べて、初期化されていないデータのリークにつながるケースがないかを確認する。
  - 入力として `-` や `+` のような不正な文字を渡すと、`scanf` が変数 `x` を変更しなくなり、そうしたリークにつながる可能性がある。
- [ ] `strncat` の使い方を調べる。よく誤用される。
  - `size` 引数は、`destination` バッファではなく、`source` 文字列のサイズを指す。
- [ ] `strncpy` の使い方を調べる。コピー先の文字列を、常にヌル終端するとは限らない。
- [ ] glibc の [`qsort`](https://man7.org/linux/man-pages/man3/qsort.3.html)、`std::sort`、[`std::stable_sort`](https://en.cppreference.com/w/cpp/algorithm/stable_sort.html) を、[推移的でない比較関数](https://www.qualys.com/2024/01/30/qsort.txt)で呼んでいないかを探す。悪用できる。
- [ ] `memcpy` や `memmove`(およびほかの関数の可能性もある)を、負の `size` 引数で呼んでいないかを探す。こうしたケースは、[悪用できる](https://github.com/n132/RetroverFlow)可能性が高い。
  - 負の整数が大きな `size_t` にオーバーフローするケースは、大量の書き込みが、有用なことをする前にクラッシュを起こすはずなので、悪用できないように見える。ただし、[libc のバージョンや CPU の機能によっては](https://x.com/disconnect3d_pl/status/1909918427084452076)、最適化によって、このオーバーフローが悪用可能になることがある。
- [ ] 初期化されていないロックに対する、スピンロック関数([`pthread_spin_trylock`](https://man7.org/linux/man-pages/man3/pthread_spin_lock.3.html) など)の呼び出しを探す。
- [ ] 文字列が有効な IP アドレスかを確かめるために `inet_aton` 関数が使われていないかを探す。この関数は[厳密ではない](https://disconnect3d.pl/2021/02/16/terrible-inet-aton/)ので、このように使うべきではない。
  - glibc とリンクした場合、渡されたホストアドレスが有効な IP アドレスであるときだけでなく、有効な IP アドレスで*始まっている*ときにも、成功を返す。たとえば、次の呼び出しは成功を返す: `inet_aton("1.1.1.1 whatever")`。
- [ ] `connect(AF_UNSPEC)` の脆弱な使い方がないかを確認する。すでに接続している TCP ソケットを切断するのに使える。
  - ソケットは、新しいアドレスに再接続できる。この手口で、[過去に nsjail からの脱出](https://github.com/google/nsjail/commit/273ce6bc846b7325c7f0915067c54bf8cf6f5654)が可能になった。
- [ ] ソケットが(`shutdown` 関数によって)半分だけ閉じられる場合がないかを確認する。
  - 接続が閉じられたあとで、かつソケット経由でデータをまだ読む(または書く)必要がある場合にだけ、リモート側に脆弱性があるときの、エクスプロイトに役立つことがある。
- [ ] サイズが可変の構造体が、[長さ 0 や要素 1 個の配列で実装されていないかを探す。間違いを起こしやすい](https://github.com/torvalds/linux/blob/master/Documentation/process/deprecated.rst#zero-length-and-one-element-arrays)。
- [ ] 独自の `printf`\ 風の関数を調べて、可変長引数の型の誤用を防ぐために、[`format` 属性](https://clang.llvm.org/docs/AttributeReference.html#format)が使われていることを確認する。
- [ ] `va_start` の使い方を調べて、必ず `va_end` と対で使われていることを確認する。詳しくは、この [StackOverflow の議論](https://stackoverflow.com/questions/587128/what-exactly-is-va-end-for-is-it-always-necessary-to-call-it)を参照。
- [ ] [`NULL` の代わりに 0 を使っていない](https://man7.org/linux/man-pages/man3/NULL.3const.html)ことを確認する。
{{< /checklist >}}
