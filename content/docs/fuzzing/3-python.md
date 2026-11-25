---
title: "Python"
slug: python
weight: 3
---


# Python

Python コードのファジングには、[Atheris](https://github.com/google/atheris) の使用をお勧めします。

## インストール

Atheris は、32 ビットと 64 ビットの Linux、および macOS をサポートしています。Linux のほうが管理が簡単で、たいてい速いので、Linux でのファジングをお勧めします。Mac や Windows 上の Linux 環境で Atheris を実行したい場合は、[Docker Desktop](https://www.docker.com/products/docker-desktop/) の使用をお勧めします。

すぐに使える Linux 環境が必要な場合は、下の [`Dockerfile`](#dockerfile) の節を参照してください。

Atheris をローカルにインストールしたい場合は、まず最近のバージョンの `clang` (できれば[最新リリース](https://github.com/llvm/llvm-project/releases))をインストールし、次のコマンドを実行します。

```bash
python -m pip install atheris
```

{{< hint info >}}
Atheris は libFuzzer をもとに作られているので、libFuzzer についての[節]({{% ref "docs/fuzzing/c-cpp/10-libfuzzer/index.md" %}})も読むことを検討してください。
{{< /hint >}}

## 使い方 {#usage}

### 純粋な Python コードのファジング

Atheris の環境が動くようになったら、Python コードをファジングしてみましょう。

まず、次の内容を `fuzz.py` として保存します。

```python
import sys
import atheris

@atheris.instrument_func
def test_one_input(data: bytes):
    if len(data) == 4:
        if data[0] == 0x46:  # "F"
            if data[1] == 0x55:  # "U"
                if data[2] == 0x5A:  # "Z"
                    if data[3] == 0x5A:  # "Z"
                        raise RuntimeError("You caught me")

def main():
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
```

次に、次のコマンドで Atheris を実行します。

```bash
python fuzz.py
```

比較的すぐに、次のようなクラッシュが出るはずです。

```bash
INFO: Using preloaded libfuzzer
INFO: Running with entropic power schedule (0xFF, 100).
INFO: Seed: 3701051567
INFO: Loaded 2 modules   (15334 inline 8-bit counters): 9595 [0xffff951f58e0, 0xffff951f7e5b), 5739 [0xffff94f843e0, 0xffff94f85a4b),
INFO: Loaded 2 PC tables (15334 PCs): 9595 [0xffff951f7e60,0xffff9521d610), 5739 [0xffff94f85a50,0xffff94f9c100),
INFO: -max_len is not provided; libFuzzer will not generate inputs larger than 4096 bytes
INFO: A corpus is not provided, starting from an empty corpus
#2  INITED cov: 882 ft: 883 corp: 1/1b exec/s: 0 rss: 66Mb
#3  NEW    cov: 882 ft: 885 corp: 2/3b lim: 4 exec/s: 0 rss: 66Mb L: 2/2 MS: 1 CopyPart-
#13 NEW    cov: 884 ft: 1257 corp: 3/7b lim: 4 exec/s: 0 rss: 67Mb L: 4/4 MS: 5 CrossOver-ChangeBinInt-ChangeByte-ChangeBinInt-CopyPart-
#65536  pulse  cov: 884 ft: 1257 corp: 3/7b lim: 652 exec/s: 21845 rss: 98Mb
#71462  NEW    cov: 886 ft: 1379 corp: 4/11b lim: 706 exec/s: 17865 rss: 101Mb L: 4/4 MS: 4 ChangeBinInt-ChangeByte-ChangeBit-CopyPart-
#131072 pulse  cov: 886 ft: 1379 corp: 4/11b lim: 1290 exec/s: 21845 rss: 130Mb
#230788 NEW    cov: 888 ft: 1691 corp: 5/15b lim: 2281 exec/s: 25643 rss: 177Mb L: 4/4 MS: 1 ChangeByte-
#262144 pulse  cov: 888 ft: 1691 corp: 5/15b lim: 2589 exec/s: 26214 rss: 194Mb
#287560 NEW    cov: 890 ft: 1704 corp: 6/19b lim: 2842 exec/s: 26141 rss: 208Mb L: 4/4 MS: 2 InsertByte-EraseBytes-

 === Uncaught Python exception: ===
RuntimeError: You caught me
Traceback (most recent call last):
  File "/app/fuzz.py", line 11, in test_one_input
    raise RuntimeError("You caught me")
RuntimeError: You caught me

==399== ERROR: libFuzzer: fuzz target exited
    #0 0xffff989df9b8 in __sanitizer_print_stack_trace (/opt/venv/lib/python3.11/site-packages/asan_with_fuzzer.so+0x11f9b8) (BuildId: b12d6567a22f7311b104efa346c5035b6837d8d1)
    #1 0xffff989344cc in fuzzer::PrintStackTrace() (/opt/venv/lib/python3.11/site-packages/asan_with_fuzzer.so+0x744cc) (BuildId: b12d6567a22f7311b104efa346c5035b6837d8d1)
    #2 0xffff9891a7c8 in fuzzer::Fuzzer::ExitCallback() (/opt/venv/lib/python3.11/site-packages/asan_with_fuzzer.so+0x5a7c8) (BuildId: b12d6567a22f7311b104efa346c5035b6837d8d1)
    #3 0xffff9822ce88  (/lib/aarch64-linux-gnu/libc.so.6+0x3ce88) (BuildId: 918ff46614b9808b05f1e29a9914132def52f69e)
    #4 0xffff9822cf5c in exit (/lib/aarch64-linux-gnu/libc.so.6+0x3cf5c) (BuildId: 918ff46614b9808b05f1e29a9914132def52f69e)
    #5 0xffff9852eba8 in Py_Exit (/usr/local/bin/../lib/libpython3.11.so.1.0+0x18eba8) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #6 0xffff9852ebd8  (/usr/local/bin/../lib/libpython3.11.so.1.0+0x18ebd8) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #7 0xffff9852ec34  (/usr/local/bin/../lib/libpython3.11.so.1.0+0x18ec34) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #8 0xffff98601af8 in _PyRun_SimpleFileObject (/usr/local/bin/../lib/libpython3.11.so.1.0+0x261af8) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #9 0xffff9860172c in _PyRun_AnyFileObject (/usr/local/bin/../lib/libpython3.11.so.1.0+0x26172c) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #10 0xffff985fa04c in Py_RunMain (/usr/local/bin/../lib/libpython3.11.so.1.0+0x25a04c) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #11 0xffff985a1ef4 in Py_BytesMain (/usr/local/bin/../lib/libpython3.11.so.1.0+0x201ef4) (BuildId: 3e68e83acff0ce909056da94a6b647416bc78ec5)
    #12 0xffff9821773c  (/lib/aarch64-linux-gnu/libc.so.6+0x2773c) (BuildId: 918ff46614b9808b05f1e29a9914132def52f69e)
    #13 0xffff98217814 in __libc_start_main (/lib/aarch64-linux-gnu/libc.so.6+0x27814) (BuildId: 918ff46614b9808b05f1e29a9914132def52f69e)
    #14 0xaaaae095086c in _start (/usr/local/bin/python3.11+0x86c) (BuildId: 4556bff17c135ffcd799fb46df15a21e0c671da8)

SUMMARY: libFuzzer: fuzz target exited
MS: 1 CopyPart-; base unit: cc3a45e08551b2e1d4f50d233a2a1b6c24f6dee8
0x46,0x55,0x5a,0x5a,
FUZZ
artifact_prefix='./'; Test unit written to ./crash-aea2e3923af219a8956f626558ef32f30a914ebc
Base64: RlVaWg==
```

見てのとおり、例外を起こす入力 `"FUZZ"` が見つかりました。この例は、Atheris が純粋な Python コードを計装し、カバレッジを追跡できることを示しています。一般的には、アプリケーションやライブラリのより広い部分をファジングするために、[`atheris.instrument_imports` や `atheris.instrument_all`](https://github.com/google/atheris#python-coverage) のようなものを使うことになります。

自分のターゲットをファジングするには、`test_one_input` 関数を、ターゲットの関数を呼び出すように変更します。

### Python の C 拡張のファジング

Python の C 拡張のファジングには、もう少し手間がかかります。正しいコンパイラフラグを付けてコンパイルする必要があります。用意されている [`Dockerfile`](#dockerfile) を使っているなら、これらはすでに設定されているはずです (`CC`、`CFLAGS`、`LD_PRELOAD` など)。

例として、[`cbor2`](https://github.com/agronholm/cbor2) プロジェクトをファジングしてみましょう。Python の C 拡張のコンポーネントと、バイナリデータを解析する機能を含んでおり、ファジングに特に向いています。

まず、パッケージをインストールします。

```bash
CBOR2_BUILD_C_EXTENSION=1 python -m pip install --no-binary cbor2 cbor2==5.6.4
```

環境変数 `CBOR2_BUILD_C_EXTENSION` とフラグ `--no-binary` により、コンパイル済みのバイナリを使わずに、C 拡張のコードがローカルでコンパイルされます。これで、コンパイルされたオブジェクトに、ファジングと [`AddressSanitizer`](https://clang.llvm.org/docs/AddressSanitizer.html) の機能を計装できます。

まず、次の内容を `cbor2-fuzz.py` として保存します。

```python
import sys
import atheris

# _cbor2 ensures the C library is imported
from _cbor2 import loads

def test_one_input(data: bytes):
    try:
        loads(data)
    except Exception:
        # We're searching for memory corruption, not Python exceptions
        pass

def main():
    atheris.Setup(sys.argv, test_one_input)
    atheris.Fuzz()

if __name__ == "__main__":
    main()
```

次に、次のコマンドで Atheris を実行します。

```bash
python cbor2-fuzz.py
```

これで `cbor2` のファジングが始まりますが、運良くバグを見つけない限り、クラッシュは期待しないでください。この例は、既存の Python の C 拡張をファジングする方法の実演です。

{{< hint info >}}
用意された Docker イメージではなくローカルで実行する場合は、[`LD_PRELOAD` を手動で設定](https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#option-a-sanitizerlibfuzzer-preloads)する必要があることに注意してください。
{{< /hint >}}

## 追加の資料

- [Python の C 拡張を継続的にファジングする](https://blog.trailofbits.com/2024/02/23/continuously-fuzzing-python-c-extensions/)
- [純粋な Python コードのファジング](https://github.com/google/atheris#using-atheris)
- [Python の C 拡張のファジング](https://github.com/google/atheris/blob/master/native_extension_fuzzing.md)
- [CI での Python のファジング](https://google.github.io/clusterfuzzlite//build-integration/python-lang/)

### Dockerfile {#dockerfile}

Docker 環境で Atheris を使うには、次のコードを `Dockerfile` に保存します。

```dockerfile
# https://hub.docker.com/_/python
ARG PYTHON_VERSION=3.11

FROM python:$PYTHON_VERSION-slim-bookworm

RUN python --version

RUN apt update && apt install -y \
    ca-certificates \
    wget \
    && rm -rf /var/lib/apt/lists/*

# LLVM builds version 15-19 for Debian 12 (Bookworm)
# https://apt.llvm.org/bookworm/dists/
ARG LLVM_VERSION=19

RUN echo "deb http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-$LLVM_VERSION main" > /etc/apt/sources.list.d/llvm.list
RUN echo "deb-src http://apt.llvm.org/bookworm/ llvm-toolchain-bookworm-$LLVM_VERSION main" >> /etc/apt/sources.list.d/llvm.list
RUN wget -qO- https://apt.llvm.org/llvm-snapshot.gpg.key > /etc/apt/trusted.gpg.d/apt.llvm.org.asc

RUN apt update && apt install -y \
    build-essential \
    clang-$LLVM_VERSION \
    && rm -rf /var/lib/apt/lists/*

ENV APP_DIR "/app"
RUN mkdir $APP_DIR
WORKDIR $APP_DIR

ENV VIRTUAL_ENV "/opt/venv"
RUN python -m venv $VIRTUAL_ENV
ENV PATH "$VIRTUAL_ENV/bin:$PATH"

# https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#step-1-compiling-your-extension
ENV CC="clang-$LLVM_VERSION"
ENV CFLAGS "-fsanitize=address,fuzzer-no-link"
ENV CXX="clang++-$LLVM_VERSION"
ENV CXXFLAGS "-fsanitize=address,fuzzer-no-link"
ENV LDSHARED="clang-$LLVM_VERSION -shared"
ENV LDSHAREDXX="clang++-$LLVM_VERSION -shared"
ENV ASAN_SYMBOLIZER_PATH="/usr/bin/llvm-symbolizer-$LLVM_VERSION"

# Allow Atheris to find fuzzer sanitizer shared libs
# https://github.com/google/atheris#building-from-source
RUN LIBFUZZER_LIB=$($CC -print-file-name=libclang_rt.fuzzer_no_main-$(uname -m).a) \
    python -m pip install --no-binary atheris atheris

# https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#option-a-sanitizerlibfuzzer-preloads
ENV LD_PRELOAD "$VIRTUAL_ENV/lib/python3.11/site-packages/asan_with_fuzzer.so"

# 1. Skip memory allocation failures for now, they are common, and low impact (DoS)
# 2. https://github.com/google/atheris/blob/master/native_extension_fuzzing.md#leak-detection
ENV ASAN_OPTIONS "allocator_may_return_null=1,detect_leaks=0"

CMD ["/bin/bash"]
```

次に、次のコマンドでコンテナをビルドして実行します。
- `docker build -t atheris .`
- `docker run -it atheris`

[UBSAN を使いたい](https://llvm.org/docs/LibFuzzer.html#fuzzer-usage)場合は、`CFLAGS` と `CXXFLAGS` の変更が必要になることがあります。
