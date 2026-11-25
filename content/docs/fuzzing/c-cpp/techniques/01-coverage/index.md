---
title: "カバレッジの分析"
slug: coverage-analysis
weight: 2
---


# カバレッジの分析 {#coverage-analysis}

ファジング中に達成したコードカバレッジを信頼できるようにすることは、2 つの理由で欠かせません。1 つ目は、ファジング用ハーネスがアプリケーションのどの部分を実行しているかを評価したいからです。

たとえば、次の図のようなマジック値のチェックは、ファザーが突破しにくいことがあります。こうしたチェックを見つけておくことが重要です。そうすれば、その値を[辞書]({{% relref 02-dictionary %}})や、シードコーパスのテストケースを通して、ファザーに与えられます。


{{< customFigure "突破しにくいことがあるマジック値のチェック" >}}
```
if (buf == 0x7F454C46) {
    // start parsing buf
}
```
{{< /customFigure >}}


2 つ目は、ファザーを切り替えたり、ハーネスや SUT を更新したりするときに、カバレッジが変わるかを確認したいからです。カバレッジが下がった場合は、新しい機能が導入されたために、ハーネスを拡張する必要があるのかもしれません。カバレッジが上がった場合は、おそらくハーネスを改善できたか、SUT がファジングしやすくなったのでしょう。

ファジングのカバレッジは、ファザーの能力と性能の代わりとなる指標です。カバレッジはファジングエンジンの性能を測る指標として[理想的ではない](https://arxiv.org/abs/1808.09700)ことは広く認められていますが、それでも、ハーネスが特定の環境で動作するかどうかは、カバレッジから分かります。

次のフローチャートは、理想的なカバレッジ分析のワークフローを示しています。このワークフローでは、各ファジングキャンペーンの後に生成されたコーパスを使ってカバレッジを計算します。これが推奨される方法です。



{{< resourceFigure "coverage-flow.svg" "alt" 300>}}
理想的なファジングのワークフロー: 各ファジングキャンペーンの後に、コードカバレッジを評価する。その結果にもとづいて、SUT またはハーネスを更新し、新しいファジングキャンペーンを始める。
{{< /resourceFigure >}}

{{< hint info >}}
プロのヒント: 長期間にわたってファジングの性能を追跡するために、特定のファザーが返す統計を使うべきではありません。たとえば、AFL++ はコードカバレッジを示す値を出力します。しかし、この値は他のファザーと比較できません。ファザーによって、値の計算方法が異なることがあるためです。

最も比較しやすいデータは、カバレッジの測定のために作られた専用のツールが生成します。
{{< /hint >}}

次の節では、カバレッジレポートを生成する 2 つの方法を見ていきます。LLVM ベースの計装と、GCC ベースの計装です。LLVM は、カバレッジレポートを安定して非常に高速に生成する方法を提供します。LLVM のツールキットは、Clang 独自の [SanitizerCoverage](https://clang.llvm.org/docs/SanitizerCoverage.html) の計装と、GCC 互換の [gcov](https://gcc.gnu.org/onlinedocs/gcc/Gcov.html) の計装をサポートしています。GCC がサポートするのは、gcov の計装だけです。

どちらの方法でも、カバレッジを分かりやすく表現でき、結果の HTML レポートは複数のページで構成されます。ただし、gcov の出力によるレポートの生成は、LLVM によるものと比べて効率が悪く、時間がかかります。

## LLVM の SanitizerCoverage によるコードカバレッジ {#code-coverage-using-llvm-sanitizercoverage}

LLVM プロジェクトは、カバレッジデータを収集できるようにする [SanitizerCoverage](https://clang.llvm.org/docs/SanitizerCoverage.html) のインターフェースとツールを提供しています。libFuzzer や AFL++ の既定の計装は、ファジング中にこの API を使って、より多くのコードを見つけるようファザーを導きます。

同じ LLVM の機能は、ファジングのコーパスのカバレッジを分析するのにも使えます。この節では、次のことを説明します。

1. コーパスの生成に使ったファザーに関係なく、カバレッジデータを収集するためにプロジェクトをビルドする
2. ファジングのコーパスに対して、バイナリを再実行する
3. データを HTML レポートに変換する

まず、`execute-rt.cc` というカスタムのランタイムを定義します。このランタイムは、既存のコーパスを実行する main 関数を提供します。

{{< customFigure "execute-rt.cc: コーパスを実行するためのランタイム" >}}
```C++ {id=execute_rt_src}
#include <stdio.h>
#include <stdlib.h>
#include <dirent.h>
#include <string.h>
#include <stdint.h>

extern "C" int LLVMFuzzerTestOneInput(const uint8_t *data, size_t size);

void load_file_and_test(const char *filename) {
    FILE *file = fopen(filename, "rb");
    if (file == NULL) {
        printf("Failed to open file: %s\n", filename);
        return;
    }

    fseek(file, 0, SEEK_END);
    long filesize = ftell(file);
    rewind(file);

    uint8_t *buffer = (uint8_t*) malloc(filesize);
    if (buffer == NULL) {
        printf("Failed to allocate memory for file: %s\n", filename);
        fclose(file);
        return;
    }

    long read_size = (long) fread(buffer, 1, filesize, file);
    if (read_size != filesize) {
        printf("Failed to read file: %s\n", filename);
        free(buffer);
        fclose(file);
        return;
    }

    LLVMFuzzerTestOneInput(buffer, filesize);

    free(buffer);
    fclose(file);
}

int main(int argc, char **argv) {
    if (argc != 2) {
        printf("Usage: %s <directory>\n", argv[0]);
        return 1;
    }

    DIR *dir = opendir(argv[1]);
    if (dir == NULL) {
        printf("Failed to open directory: %s\n", argv[1]);
        return 1;
    }

    struct dirent *entry;
    while ((entry = readdir(dir)) != NULL) {
        if (entry->d_type == DT_REG) {
            char filepath[1024];
            snprintf(filepath, sizeof(filepath), "%s/%s", argv[1], entry->d_name);
            load_file_and_test(filepath);
        }
    }

    closedir(dir);
    return 0;
}
```

{{< /customFigure >}}



次のコンパイルコマンドで、カバレッジ情報を出力できる、計装済みのバイナリを作ります。


```shell
clang++ -DNO_MAIN -O2 -fprofile-instr-generate -fcoverage-mapping main.cc harness.cc execute-rt.cc -o fuzz_exec
```
<!-- TODO tooltips -->

[libFuzzer の節]({{% relref "10-libfuzzer#compile-a-fuzz-test" %}})の例と同様に、既定の main 関数を無効にする必要があります。また、カバレッジの計算をより正確にするために、最適化も無効にする必要があります。できあがったバイナリは、実行するとカバレッジデータを出力します。バイナリの第 1 引数は、テストケースのあるディレクトリです。次のコマンドで、`fuzz.profraw` ファイルが生成されます。


```shell
LLVM_PROFILE_FILE=fuzz.profraw ./fuzz_exec corpus/
```


次に、`.profraw` ファイルを、インデックス付きの `.profdata` ファイルに変換する必要があります。必要な LLVM のツールがインストールされていることを確認してください。Debian/Ubuntu では、パッケージ名は `llvm` です（例: `apt install llvm`）。


```shell
llvm-profdata merge -sparse fuzz.profraw -o fuzz.profdata
```


カバレッジ用のバイナリ `fuzz_exec` と `.profdata` ファイルがあれば、レポートを生成できます。ハーネスと実行用のランタイムのカバレッジには関心がないので、除外します。


```shell
llvm-cov report ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='harness.cc|execute-rt.cc'
```
<!-- TODO tooltips -->

出力には、ファイルごとと全体のカバレッジが表示されます。


```text
Filename       Regions    Missed Regions     Cover   Functions  Missed Functions  Executed       Lines      Missed Lines     Cover    Branches   Missed Branches     Cover
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
/root/main.cc       13                13     0.00%           1                 1     0.00%           9                 9     0.00%          12                12     0.00%
--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
TOTAL               13                13     0.00%           1                 1     0.00%           9                 9     0.00%          12                12     0.00%
```

`llvm-cov report` の代わりに `llvm-cov show` を使うと、より詳細なテキスト形式の出力を生成できます。出力は、ファイル名の接頭辞を付けて絞り込めます。たとえば、次のコマンドは、`main.cc` ファイルだけの出力を表示します。


```shell
llvm-cov show ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='harness.cc|execute-rt.cc' /root/main.cc
```
<!-- TODO tooltips -->

次の図のとおり、コーパスは現在、`abort()` 文を除くすべての行をカバーしています。



{{< customFigure "テキスト形式のカバレッジデータ。強調表示された行は実行されていません。" >}}
```C++ {linenos=inline,hl_lines=[8,9]}
       |#include <stdlib.h>
       |#include <string.h>
       |
      3|void check_buf(char *buf, size_t buf_len) {
      3|    if(buf_len > 0 && buf[0] == 'a') {
      3|        if(buf_len > 1 && buf[1] == 'b') {
      1|            if(buf_len > 2 && buf[2] == 'c') {
      0|                abort();
      0|            }
      1|        }
      3|    }
      3|}
```
{{< /customFigure >}}

追加のパラメータ `-format=html -output-dir fuzz_html/` を付けると、同じ情報を HTML で出力します。出力先のディレクトリを設定することが重要です。設定しないと、出力は 1 つの HTML ファイルになります。


```shell
llvm-cov show ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='harness.cc|execute-rt.cc' /root/main.cc -format=html -output-dir fuzz_html/
```
<!-- TODO tooltips -->

{{< resourceFigure "cov1.png" >}}
`llvm-cov` が生成した HTML のカバレッジレポート
{{< /resourceFigure >}}

{{< hint info >}}
プロのヒント: LLVM と Clang のバージョン 18 では、ディレクトリごとのインデックスページを生成できます。これにより、レポートのルートのページが、何百もの個別のファイルで埋まらずに済みます。`llvm-cov show` を呼ぶときに、フラグ `-format=html`、`-output-dir fuzz_html/`、`-show-directory-coverage` を付けるだけです。
{{< /hint >}}

注意: コーパスにクラッシュする入力が含まれている場合、カバレッジデータを生成できません。カバレッジデータを生成できるのは、SUT が正常に終了する場合だけです。理想的には、バグを修正してからファザーを再実行して、カバレッジデータを収集します。そうすれば、以前はクラッシュしていた入力のカバレッジデータも収集できます。

あるいは、クラッシュする入力を、手動または自動で除外します。別の方法として、SUT を実行する前（つまり `LLVMFuzzerTestOneInput` を呼ぶ前）に、プロセスを `fork()` する方法もあります。

LLVM のスタックで HTML レポートを生成したい場合は、lcov 形式にエクスポートしてから、lcov ツールで HTML ページを生成することをお勧めします。lcov を使うと、ソースファイルごとのレポートを生成できます。これは、バージョン 18 より前の LLVM ではできません。

```shell
llvm-cov export ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='harness.cc|execute-rt.cc' -format=lcov > fuzz.lcov

apt install lcov
genhtml --output-directory fuzz_html/ fuzz.lcov
```

できあがった HTML は、`fuzz_html/` ディレクトリに保存されます。

{{< resourceFigure "cov2.png" >}}
lcov が生成した HTML のカバレッジレポート
{{< /resourceFigure >}}


## gcov と gcovr によるコードカバレッジ {#code-coverage-using-gcov-and-gcovr}

[gcov](https://gcc.gnu.org/onlinedocs/gcc/Gcov.html) の計装は、GCC と LLVM の両方が提供しています。gcov を使えば、優れたツールである [gcovr](https://gcovr.com/) で HTML レポートを生成できます。LLVM を使う場合、GCC の計装は、フラグ `-ftest-coverage` と `-fprofile-arcs` で追加できます。前の節の [`execute-rt.cc`](#execute_rt_src) ランタイムを使って、カバレッジ用のバイナリをコンパイルできます。


```shell
clang++ -DNO_MAIN -O2 -ftest-coverage -fprofile-arcs main.cc harness.cc execute-rt.cc -o fuzz_exec_gcov
```
<!-- TODO tooltips -->


同じコンパイルの指示は、GCC でも有効です。その場合は、`clang++` を `g++` に置き換えます。

コンパイル中に、オブジェクトファイルごとに `.gnco` ファイルが作られます。実行中に、オブジェクトファイルごとに `.gnca` ファイルが作られるか、更新されます。環境変数 `GCOV_PREFIX` と `GCOV_PREFIX_STRIP` を使うと、ファイルを別の場所へコピーできます（詳しくは[こちら](https://llvm.org/docs/CommandGuide/llvm-cov.html#id2:~:text=By%20default%2C%20the,to%20find%20them.)を参照）。バイナリを呼び出すたびに、.gnca ファイルは少しずつ更新されます。つまり、古い .gnca ファイルを削除せずにプログラムを何度も実行すると、ヒットカウンタは増え続けます。gcovr ツールを使うと、これらのファイルの扱いが簡単になります。

最初のステップは、既存のコーパスに対してカバレッジ用のバイナリを実行することです。


```shell
./fuzz_exec_gcov corpus/
```

次に、gcovr がインストールされていることを確認します。ディストリビューションが提供するバージョンは古い可能性があるため、Python の pip で gcovr をインストールすることをお勧めします。LLVM/Clang 14 以降を使う場合は、gcovr 5.1 以上が必要です（バージョン 5.1 には、この[パッチ](https://github.com/gcovr/gcovr/pull/525/files#diff-26284e367af8a1344772d5e18ab13d7e5518c701936c21733b2a18c13e2b958cL31-R31)が含まれています）。
```shell
python3 -m venv venv
source venv/bin/activate
pip3 install gcovr
```

インストールしたばかりのツールで、リポジトリ全体のテキストレポートを生成できます。関係のないファイルは除外します。
```
gcovr --gcov-executable "llvm-cov gcov" --exclude harness.cc --exclude execute-rt.cc --root .
```


gcovr には、GCC ではなく LLVM の gcov を使うよう指示する必要があります。カバレッジ用のバイナリを GCC でコンパイルした場合も、同じコマンドが使えます。その場合は、`--gcov-executable` フラグを省略するだけです。また、ハーネスと実行用のランタイムは、レポートから除外します。

次のデータが返されます。

```text
------------------------------------------------------------------------------
                           GCC Code Coverage Report
Directory: .
------------------------------------------------------------------------------
File                                       Lines    Exec  Cover   Missing
------------------------------------------------------------------------------
main.cc                                        9       8    88%   10
------------------------------------------------------------------------------
TOTAL                                          9       8    88%
------------------------------------------------------------------------------
```

同じデータは、`--json` フラグを付けると JSON でも出力できます。HTML レポートは、`--html-details -o coverage.html` を付けると生成できます。


```shell
gcovr --gcov-executable "llvm-cov gcov" --exclude harness.cc --exclude execute-rt.cc --root . --html-details -o coverage.html
```
<!-- TODO tooltips -->


{{< hint info >}}
プロのヒント: 次のバージョンの gcovr（バージョン 6.1）には、より快適にレビューできる、モダンなテーマが入ります。master のバージョン（`pip3 install git+https://github.com/gcovr/gcovr.git`）を使えば、`--html-theme github.green` フラグを付けて、すでにそのテーマを楽しめます。
{{< /hint >}}

HTML レポートの出力には、ヒット数と、実行されなかった行が表示されます。
{{< resourceFigure "cov3.png" >}}
gcovr が生成した HTML のカバレッジレポート
{{< /resourceFigure >}}


**前に述べたとおり、gcov は、カバレッジ用のバイナリを複数回実行する間、`.gcda` ファイルを少しずつ更新します。最初からやり直すには、gcovr を実行した後にすべての `.gcda` ファイルを手動で削除するか、`--delete` フラグを付けます。**


## 実際の例 {#real-world-examples}


### libpng {#libpng}

前の節で、[libFuzzer](#libpng) と [AFL++](#libpng) で libpng をファジングしました。今度は、そのカバレッジを分析して、ファジングの強さを調べたいと思います。

まず、コーパスを調べ、テストケースの数を数えて、使えるテストケースがあることを確認します。

```
ls corpus | wc -l
```

libFuzzer と AFL++ 用に libpng を設定したときと同様に、今度は、LLVM でカバレッジレポートを生成することを目標に、異なる設定をします。


```shell
export CC=clang CFLAGS="-fprofile-instr-generate -fcoverage-mapping" # Set C compiler and its flags for generating coverage
export CXX=clang++ CXXFLAGS="$CFLAGS" # Set C++ compiler and use C flags
./configure --enable-shared=no --disable-tools # Configure to compile a static library
make # Run compilation
```


ファジングの環境によっては、コンパイルを成功させるために、足りない依存関係をインストールする必要があるかもしれません。たとえば、素の Ubuntu のインストールでは、前述のとおり、`zlib1g-dev` パッケージのインストールが必要になることがあります。

libpng のツールは、コンパイルの問題を起こすため、`--disable-tools` フラグで無効にしました。

カバレッジデータを出力するバイナリを作るために、まず、ファジング中に使ったのと同じハーネスを用意します。


```shell
curl -O https://raw.githubusercontent.com/glennrp/libpng/f8e5fa92b0e37ab597616f554bee254157998227/contrib/oss-fuzz/libpng_read_fuzzer.cc
```

次に、計装済みの libpng、ハーネス、[実行用のランタイム](#execute_rt_src)をリンクします。


```shell
$CXX $CFLAGS libpng_read_fuzzer.cc .libs/libpng16.a execute-rt.cc -lz -o fuzz_exec
```


最後に、テストケースを実行し、データの保存先を指定できます。


```shell
LLVM_PROFILE_FILE=fuzz.profraw ./fuzz_exec corpus/
```


次に、.profraw ファイルを、インデックス付きの .profdata ファイルに変換する必要があります。


```shell
llvm-profdata merge -sparse fuzz.profraw -o fuzz.profdata
```


カバレッジ用のバイナリ fuzz_exec と .profdata ファイルがあれば、レポートを生成できます。ハーネスと実行用のランタイムのカバレッジには関心がないので、除外します。


```shell
llvm-cov report ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='libpng_read_fuzzer.cc|execute-rt.cc'
```
<!-- TODO tooltips -->

HTML レポートを生成するには、次のようにします。


```shell
llvm-cov show ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='libpng_read_fuzzer.cc|execute-rt.cc' -format=html -output-dir fuzz_html/
```
<!-- TODO tooltips -->


#### GCC でコードカバレッジを生成する

説明のために、同じことを GCC で行う方法も示します。ここでも、libpng が特定のコンパイラとコンパイルフラグを使うように設定します。


```shell
export CC=gcc CFLAGS="-ftest-coverage -fprofile-arcs" # Set C compiler and its flags for generating coverage
export CXX=g++ CXXFLAGS="$CFLAGS" # Set C++ compiler and use C flags
./configure --enable-shared=no --disable-tools # Configure to compile a static library
make # Run compilation
```


これで、すべてをリンクできます。


```shell
$CXX $CFLAGS libpng_read_fuzzer.cc .libs/libpng16.a execute-rt.cc -lz -o fuzz_exec_gcov
```


最後に、既存のコーパスを実行できます。カバレッジデータは、オブジェクトファイルと同じ場所に書き込まれます。


```shell
./fuzz_exec_gcov corpus/
```


gcovr を使えば、HTML レポートを生成できます。


```shell
gcovr --exclude libpng_read_fuzzer.cc --exclude execute-rt.cc --root . --gcov-ignore-errors=no_working_dir_found
```

フラグ `--gcov-ignore-errors=no_working_dir_found` を使って、エラーを 1 つ無視する必要があったことに注意してください。あなたの用途では、これは不要かもしれません。
<!-- TODO work on this again. Not sure why this is thrown -->


### CMake ベースのプロジェクト {#cmake-based-project}

CMake プロジェクトを [libFuzzer](#cmake-based-project) と [AFL++](#cmake-based-project) でファジングしたとして、今度は、カバレッジを生成するように調整したいとします。次の図は、buggy_program という実行ファイルを定義する CMakeLists ファイルです。メインのバイナリに加えて、ファジング用のバイナリが定義されています。さらに、既存のファズテストのテストケースを実行できるバイナリも追加されています。


{{< customFigure "例のプロジェクトの CMakeLists ファイル" >}}
```cmake
project(BuggyProgram)
cmake_minimum_required(VERSION 3.0)

add_executable(buggy_program main.cc)

add_executable(fuzz main.cc harness.cc)
target_compile_definitions(fuzz PRIVATE NO_MAIN=1)
target_compile_options(fuzz PRIVATE -g -O2 -fsanitize=fuzzer)
target_link_libraries(fuzz -fsanitize=fuzzer)

add_executable(fuzz_exec main.cc harness.cc execute-rt.cc)
target_compile_definitions(fuzz_exec PRIVATE NO_MAIN)
target_compile_options(fuzz_exec PRIVATE -O2 -fprofile-instr-generate -fcoverage-mapping)
target_link_libraries(fuzz_exec -fprofile-instr-generate)
```
{{< /customFigure >}}


次のコマンドで、プロジェクトをビルドできます。


```shell
cmake -DCMAKE_C_COMPILER=clang -DCMAKE_CXX_COMPILER=clang++ .
cmake --build . --target fuzz_exec
```


これで、`fuzz_exec` バイナリを既存のコーパスに対して実行し、カバレッジデータを生成できます。最後に、そのバイナリを使ってレポートを生成できます。より詳しい手順は、前の節の libpng の実際の例を参照してください。


```shell
LLVM_PROFILE_FILE=fuzz.profraw ./fuzz_exec corpus/
llvm-profdata merge -sparse fuzz.profraw -o fuzz.profdata
llvm-cov report ./fuzz_exec -instr-profile=fuzz.profdata -ignore-filename-regex='libpng_read_fuzzer.cc|execute-rt.cc'
```

## 追加の資料 {#additional-resources}

* [LLVM のソースベースのコードカバレッジのドキュメント](https://clang.llvm.org/docs/SourceBasedCodeCoverage.html)
    * [llvm-cov CLI のドキュメント](https://llvm.org/docs/CommandGuide/llvm-cov.html)
* [gcovr のドキュメント](https://gcovr.com/)
* [低レベルの SanitizerCoverage のドキュメント](https://clang.llvm.org/docs/SanitizerCoverage.html)
