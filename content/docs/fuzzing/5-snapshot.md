---
title: "スナップショットファジング"
slug: snapshot-fuzzing
summary: "スナップショットファジングを使うと、セキュリティエンジニアは、従来は解析が難しかったソフトウェア（カーネルレベルのソフトウェアなど。ただし、この手法はそれらに限られません）を効果的にテストできます。ドライバーや、アンチウイルスソフトウェアを含む他のカーネルモードのコンポーネントを監査する場合でも、スナップショットファジングは、重大な脆弱性を見つける強力な手段になります。自分の環境でスナップショットファジングを行う手順は、この節を参照してください。"
weight: 6
url: docs/fuzzing/snapshot-fuzzing
---


# スナップショットファジング

## はじめに

スナップショットファジングとは、ターゲットのプログラムまたは OS のスナップショット（メモリの状態、レジスタの状態、実行を再開するのに必要なその他の情報）を取り、エミュレートされた環境で実行を続けながらメモリ上のデータを変異させ、実行がクラッシュしたとき、または指定した地点に達したときに、プログラムを元のスナップショットの状態に戻す、という手法です。

スナップショットファジングには、多くの利点があります。

* 実行のたびにプログラムを起動する必要がないので、高速にできます。プログラムを望みの状態（たとえばファイルを読み込んだ時点）でスナップショットに取り、そこからテストを始められます。   
* この過程は完全に決定的、または非常に高い決定性を持ちます。  
  * ターゲットは常に同じ状態から始まります。  
  * 同じファズ入力は、同じ結果になるはずです。  
  * テストで、再現できないクラッシュが生じません。  
  * 実行に差があるなら、それは未知の状態ではなく、ユーザーの入力によるものです。  
* ソースコードは不要です（ただし、もちろんシンボルがあると役に立ちます）。  
* コードカバレッジの追跡、クラッシュの検出、ダーティメモリの追跡が簡単です。

一方で、いくつかの欠点もあります。

* スナップショットの準備には時間がかかり、間違いも起きやすいです。  
  * たとえば、Windows のプログラムをターゲットにするには、KDNET の設定、VM のスナップショットの作成、ハーネスの準備など、時間のかかる手順が必要です。  
* 既存のファザーには細かいバグが多く、特定の状況で動かすには暗黙知が必要です。たとえば、特定のエミュレーション用バックエンドで特定のターゲットを実行するには、特定のレジスタのビットを取り除く必要があり、そうしないとエラーになる、といったことを知っておく必要があります。

この Testing Handbook の章では、what the fuzz（wtf）というツールで作ったファザーを使って、Windows のカーネルドライバーに対するスナップショットファジングを実演します。wtf は、分散型で、コードカバレッジガイド型で、カスタマイズでき、クロスプラットフォームの、スナップショットベースのファザーで、ユーザーモードとカーネルモードの両方のターゲット向けに設計されています。主に Windows 向けに実装されていますが、他のプラットフォームをサポートする拡張もあります。

* [Linux](https://github.com/0vercl0k/wtf/blob/main/linux_mode)   
* [macOS](https://blog.talosintelligence.com/talos-releases-new-macos-fuzzer/) 

そのほかの注目すべきスナップショットファザーには、次のものがあります。

* [Snapchange by AWS](https://github.com/awslabs/snapchange)   
* [Nyx](https://github.com/nyx-fuzz) 

wtf が生まれた経緯と、IDA のファジングでの使われ方については、[このブログ記事](https://doar-e.github.io/blog/2021/07/15/building-a-new-snapshot-fuzzer-fuzzing-ida/)を、独自のスナップショットファザーの開発については、[このブログ記事のシリーズ](https://h0mbre.github.io/New_Fuzzer_Project/)を参照してください。

## 前提条件

このチュートリアルでは、**ホストマシン**は、WinDbg を使って、カーネルドライバーを載せた**ゲストマシン**をネットワーク越しに（KDNET を使って）デバッグする、開発者のマシンです。ホストマシンは、Hyper-V を動かす Windows 11（x64）のマシンで、ゲストは Windows 11 の開発環境の [VM](https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/quick-start/quick-create-virtual-machine) です。

次の点にも注意してください。

* VMware では、WinDbg 拡張機能でスナップショット（CPU の状態と物理メモリのダンプ）を作成できません。何年も前からある VMware のバグのせいで、スナップショットを取るソフトウェアが正しく動かないためです。  
* （ホストが Windows の場合は）[VirtualKD](https://sysprogs.com/legacy/virtualkd/) と組み合わせた VirtualBox の利用を検討できます。

### ホストマシンの準備

1. [Hyper-V を有効にします](https://techcommunity.microsoft.com/t5/educator-developer-blog/step-by-step-enabling-hyper-v-for-use-on-windows-11/ba-p/3745905)。  
2. [Visual Studio 2022](https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk#download-icon-for-visual-studio-step-1-install-visual-studio-2022)、[Windows SDK](https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk#download-icon-for-sdk-step-2-install-sdk)、[WDK](https://learn.microsoft.com/en-us/windows-hardware/drivers/download-the-wdk#download-icon-for-wdk-step-3-install-wdk)、[CMake](https://cmake.org/download/)、[Git](https://git-scm.com/download/win) をインストールします。  
3. （任意）クラッシュのトリアージに必要な依存関係をビルドするために、[Rust](https://www.rust-lang.org/tools/install) をインストールします。  
4. まだインストールしていなければ、[WinDbg](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/) デバッガをインストールします。  
5. [WinDbg でデバッグシンボルを設定します](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/symbol-path#using-a-symbol-server-srv)。`Symbol paths` 設定の 1 行目には、Windows のシンボル用に、シンボルサーバーとローカルキャッシュのパス（`C:\symbols`）を含めます。それ以外の行は、特定のターゲット（カーネルドライバーなど）のシンボルに使えます。  
6. リポジトリをクローンします。  
   1. [`wtf` リポジトリ](https://github.com/0vercl0k/wtf/)  
   2. [`symbolizer-rs` リポジトリ](https://github.com/0vercl0k/symbolizer-rs/)（任意。クラッシュのトリアージにのみ必要）  
7. [snapshot WinDbg 拡張機能](https://github.com/0vercl0k/snapshot/releases)をダウンロードします。   
8. [Visual Studio Developer Command Prompt](https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell?view=vs-2022) を開き、先ほどクローンした `wtf`\\`src\build` ディレクトリに移動して、[`build-release-msvc.bat`](https://github.com/0vercl0k/wtf/blob/main/src/build/build-release-msvc.bat) スクリプトを実行します。コンパイルはエラーなく終わるはずで、最後の行に、コンパイルされた wtf のバイナリ（`wtf.exe`）のパスが表示されます。コンパイルした `wtf.exe` のバイナリを実行できることを確認してください（たとえば、`C:\Users\user\wtf\src\build\RelWithDebInfo\wtf.exe --help` を使います）。

### ゲストマシンの最初の準備

1. \[HOST\] Hyper-V で新しい[ゲスト VM](https://learn.microsoft.com/en-us/virtualization/hyper-v-on-windows/quick-start/quick-create-virtual-machine)を作成します。  
   1. 作成した VM の設定を編集します。  
      1. 仮想プロセッサは 1 つだけ割り当てます。  
      2. RAM は 4 GB だけにします。  
      3. セキュアブートを無効にします。  
2. \[GUEST\] [Windows SDK のインストーラー](https://developer.microsoft.com/en-us/windows/downloads/windows-sdk/)をダウンロードします。インストーラーの実行時に、「Debugging Tools for Windows」を選択します。  
3. \[GUEST\] [KVA Shadow](https://msrc.microsoft.com/blog/2018/03/kva-shadow-mitigating-meltdown-on-windows/) を無効にします。これは、ユーザーランドのアプリケーションをファジングするときに必要です。wtf ツールの [`disable-kva.cmd`](https://github.com/0vercl0k/wtf/blob/main/scripts/disable-kva.cmd) スクリプトをダウンロードし、管理者として実行して、マシンを再起動します。  
4. \[GUEST\] [このガイド](https://medium.com/@ophirharpaz/kdnet-tutorial-for-noobs-68669778bbd4)に従って（または、[Microsoft の公式ガイド](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/setting-up-a-network-debugging-connection-automatically)を参照して）、KDNET を設定します。  
   a. PowerShell で `bcdedit` コマンドを実行する場合は、PowerShell の構文解析を抑えるために、`bcdedit` の後、後続の引数の前に `--%` を入れるのを忘れないでください。  
   b. ホストマシンでターミナルを開き、`ipconfig` コマンドを実行して、「Ethernet Adapter vEthernet (Default Switch)」のセクションにある IPv4 アドレスを書き留めます。これが、ガイドで参照されている `bcdedit` の `/dbgsettings` コマンドの `hostip` の値に使うべき IP アドレスです。

チュートリアルのこの時点で、ホストマシンで WinDbg を実行し、[Attach to kernel](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/windbg-kernel-mode-preview) 機能でゲスト VM をデバッグできることを確認してください。

{{< resourceFigure "figure1.png" "">}}
WinDbg で KDNET によるカーネル接続に成功した状態
{{< / resourceFigure >}}



## Windows ドライバーを作成する

[Windows の公式チュートリアル](https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/writing-a-very-small-kmdf--driver)に従ってドライバー（名前は `KmdfHelloWorld` とします）を作成しますが、`Driver.c` ファイルは次のソースコードに置き換えてください。

```c
#include <ntddk.h>	// Core Windows kernel definitions for all drivers

#define NT_DEVICE_NAME	L"\\Device\\KmdfHelloWorld" // Name of the device object
#define DOS_DEVICE_NAME L"\\??\\KmdfHelloWorldLink" // MS-DOS device name

// The IOCTL function codes for customer use:
#define IOCTL_MESSAGE_PROCESS_MESSAGE \
    CTL_CODE( FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)

// Declarations for callbacks
VOID
PrintIrpInfo(
    PIRP Irp
);

BOOLEAN
CheckTimestamp(
    LARGE_INTEGER time
);

DRIVER_INITIALIZE DriverEntry;
_Dispatch_type_(IRP_MJ_CREATE)
_Dispatch_type_(IRP_MJ_CLOSE)
DRIVER_DISPATCH OnCreateClose;

_Dispatch_type_(IRP_MJ_DEVICE_CONTROL)
DRIVER_DISPATCH OnDeviceControl;
DRIVER_UNLOAD OnUnloadDriver;

// Driver's initialization routine
NTSTATUS
DriverEntry(
    _In_ PDRIVER_OBJECT		DriverObject,
    _In_ PUNICODE_STRING	RegistryPath
)
{
    // NTSTATUS variable to record success or failure
    NTSTATUS ntStatus;

    UNICODE_STRING ntUnicodeString; // NT Device Name (NT_DEVICE_NAME)
    UNICODE_STRING ntWin32NameString; // Win32 Name (DOS_DEVICE_NAME)
    PDEVICE_OBJECT deviceObject = NULL;

    UNREFERENCED_PARAMETER(RegistryPath); // Avoid compiler warning about the unused RegistryPath parameter

    // Initialize a Unicode strin with the NT_DEVICE_NAME
    RtlInitUnicodeString(&ntUnicodeString, NT_DEVICE_NAME);

    ntStatus = IoCreateDevice(
        DriverObject,				// Pointer to the driver object
        0,							// Don't use a device extension
        &ntUnicodeString,			// A buffer containing the name of the device object
        FILE_DEVICE_UNKNOWN,		// A device type
        FILE_DEVICE_SECURE_OPEN,	// Device characteristics - FILE_DEVICE_SECURE_OPEN "Directs the I/O manager to apply the security descriptor of the device object to relative opens and trailing file name opens for the device"
        FALSE,						// Specifies if the device object represents an exclusive device. If exclusive access to a device is enabled, only one handle to the device can be open at a time
        &deviceObject				// Pointer to a variable that receives a pointer to the newly created DEVICE_OBJECT structure
    );

    if (!NT_SUCCESS(ntStatus)) {
        DbgPrint("Couldn't create the device object\n");
        return ntStatus;
    }

    // Initialize the driver object with a subset of major function codes (create, close, device I/O control)
    DriverObject->MajorFunction[IRP_MJ_CREATE] = OnCreateClose;
    DriverObject->MajorFunction[IRP_MJ_CLOSE] = OnCreateClose;
    DriverObject->MajorFunction[IRP_MJ_DEVICE_CONTROL] = OnDeviceControl;

    // The routine to perform any operations necessary before the system unloads the driver
    DriverObject->DriverUnload = OnUnloadDriver;

    // Initialize a Unicode String with the DOS_DEVICE_NAME
    RtlInitUnicodeString(&ntWin32NameString, DOS_DEVICE_NAME);

    // Create a symlink between the device name and the DOS device name
    ntStatus = IoCreateSymbolicLink(&ntWin32NameString, &ntUnicodeString);

    if (!NT_SUCCESS(ntStatus)) {
        // Remove a device object from the system when unable to create a symlink
        DbgPrint("Unable to create a symlink\n");
        IoDeleteDevice(deviceObject);

        return ntStatus;
    }

    return ntStatus;
}

// Routine to unload a driver - the OS calls this function when the callout driver is unloaded from the system.
VOID OnUnloadDriver(_In_ PDRIVER_OBJECT DriverObject)
{
    PDEVICE_OBJECT deviceObject = DriverObject->DeviceObject;
    UNICODE_STRING uniWin32NameString;

    // Initialize a Unicode String with the DOS_DEVICE_NAME
    RtlInitUnicodeString(&uniWin32NameString, DOS_DEVICE_NAME);

    // Delete the symlink
    IoDeleteSymbolicLink(&uniWin32NameString);

    if (deviceObject != NULL) {
        // Remove a device object from the system
        IoDeleteDevice(deviceObject);
    }
}

// The routine to handle IRPs Open and Close
NTSTATUS OnCreateClose(PDEVICE_OBJECT DeviceObject, PIRP Irp) {
    UNREFERENCED_PARAMETER(DeviceObject);
    //PAGED_CODE();

    // Fill the status of the IRP
    Irp->IoStatus.Status = STATUS_SUCCESS;
    Irp->IoStatus.Information = 0;

    // The caller has completed all processing for a given I/O request
    // return the given IRP to the I/O manager
    IoCompleteRequest(Irp, IO_NO_INCREMENT);

    return STATUS_SUCCESS;
}


// User-mode application sends IOCTLs to the driver by calling DeviceIoControl
// and causes the I/O manager to create an IRP_MJ_DEVICE_CONTROL request and set it to the driver
// So here we have the general logic when handling our IOCTL
NTSTATUS
OnDeviceControl(
    PDEVICE_OBJECT DeviceObject,	// A pointer to the device object
    PIRP Irp						// A pointer to the IRP for the request
)
{
    PIO_STACK_LOCATION	irpSp = NULL; // Pointer to the current stack location
    NTSTATUS			ntStatus = STATUS_SUCCESS;
    
    CHAR* kernelProphecyMessage = "The day has not yet come"; // Message from the kernel
    size_t kernelProphecyMessageLength = strlen(kernelProphecyMessage) + 1;

    LARGE_INTEGER systemTime; // To store time

    UNREFERENCED_PARAMETER(DeviceObject);

    //PAGED_CODE();

    irpSp = IoGetCurrentIrpStackLocation(Irp); // Get the pointer to the current stack location

    switch (irpSp->Parameters.DeviceIoControl.IoControlCode) { // Check the IOCTL function code passed to the device driver
    case IOCTL_MESSAGE_PROCESS_MESSAGE:
        DbgPrint("Called IOCTL_MESSAGE_PROCESS_MESSAGE\n");

        DbgPrint("Input received from userland: %s", (char*)Irp->AssociatedIrp.SystemBuffer);
        
        PrintIrpInfo(Irp);

        CHAR* messageFromUserland = (char*)Irp->AssociatedIrp.SystemBuffer;
        DbgPrint("[EXPLOIT] messageFromUserland: %s\n", messageFromUserland);

        // It is only possible to invoke vulnerability on doomsday (1234567890 Unix time)

        // Get time
        KeQuerySystemTime(&systemTime);

        BOOLEAN doomsDay = CheckTimestamp(systemTime);

        if (doomsDay) {
            DbgPrint("The time has come...");

            // Vulnerability
            if (strcmp(messageFromUserland, "DEADBEEF\x00") == 0) {
                unsigned int* bad_ptr;
                bad_ptr = (unsigned int*)0xdeadbeef;
                DbgPrint("Killing :O\n");
                *bad_ptr = 'X'; // kill :O
            }
        }

        // Send the prophecy back to the user land
        // IoStatus is the status of the IRP
        Irp->IoStatus.Information = kernelProphecyMessageLength; // The number of bytes written
        Irp->IoStatus.Status = STATUS_SUCCESS;

        DbgPrint("Sending to userland: %s\n", kernelProphecyMessage);
        DbgPrint("IMPORTANT: strlen of messageFromKernel: %lld\n", kernelProphecyMessageLength);

        RtlCopyMemory(Irp->AssociatedIrp.SystemBuffer, kernelProphecyMessage, kernelProphecyMessageLength);
        IoCompleteRequest(Irp, IO_NO_INCREMENT);

        return STATUS_SUCCESS;
    default:
        // Unrecognized I/O control code
        ntStatus = STATUS_INVALID_DEVICE_REQUEST;
        DbgPrint("ERROR: uncrecognized IOCTL %x\n",
            irpSp->Parameters.DeviceIoControl.IoControlCode);
        return ntStatus;
    }
}

// Print some members of the IRP structure for debug purpose
VOID
PrintIrpInfo(
    PIRP Irp)
{
    PIO_STACK_LOCATION  irpSp;
    // Get the pointer to the I/O stack location
    irpSp = IoGetCurrentIrpStackLocation(Irp);

    //PAGED_CODE();

    // Get the `SystemBuffer` member used when the I/O manager uses the METHOD_BUFFERED
    // for passing the user's buffer to the driver
    DbgPrint("\tIrp->AssociatedIrp.SystemBuffer = 0x%p\n",
        Irp->AssociatedIrp.SystemBuffer);

    // The UserBuffer is the pointer to the buffer provided by the client that initiated I/O operation
    DbgPrint("\tIrp->UserBuffer = 0x%p\n", Irp->UserBuffer);

    // Get the buffer size for input data
    DbgPrint("\tirpSp->Parameters.DeviceIoControl.InputBufferLength = %d\n",
        irpSp->Parameters.DeviceIoControl.InputBufferLength);

    // Get the buffer size for output data
    DbgPrint("\tirpSp->Parameters.DeviceIoControl.OutputBufferLength = %d\n",
        irpSp->Parameters.DeviceIoControl.OutputBufferLength);
    
    return;
}

BOOLEAN
CheckTimestamp(LARGE_INTEGER currentTime) {
    // Calculate Unix time
    LONGLONG unixTime = (currentTime.QuadPart - 0x019DB1DED53E8000) / 10000000;

    DbgPrint("Unix time: %lld\n", unixTime);

    if (unixTime == 1234567890) {
        return TRUE;
    }
    return FALSE;
}
```

次に、ゲスト VM にドライバーを[デプロイしてインストール](https://learn.microsoft.com/en-us/windows-hardware/drivers/gettingstarted/writing-a-very-small-kmdf--driver#deploy-the-driver)します（インストール後に再起動が必要なことに注意してください）。

### ユーザーランドの通信プログラム

ホストマシンで、ドライバーと通信する次のプログラムをコンパイルします。

```c
#include <iostream>
#include <windows.h>

#define IOCTL_MESSAGE CTL_CODE(FILE_DEVICE_UNKNOWN, 0x800, METHOD_BUFFERED, FILE_ANY_ACCESS)

int main(int argc, char *argv[])
{
    CHAR inBuffer[128] = { 0 };
    CHAR outBuffer[128] = { 0 };
 
    HANDLE device = INVALID_HANDLE_VALUE;
    BOOL status = FALSE;
    DWORD dwbytesRead = 0;

    RtlCopyMemory(inBuffer, argv[1], strlen(argv[1])+1);

    device = CreateFileW(L"\\\\.\\KmdfHelloWorldLink", GENERIC_WRITE | GENERIC_READ | GENERIC_EXECUTE, 0, 0, OPEN_EXISTING, FILE_ATTRIBUTE_SYSTEM, 0);

    if (device == INVALID_HANDLE_VALUE)
    {
        printf_s("Unable to open the device: 0x%x\n", GetLastError());
        return FALSE;
    }

    printf_s("Sending a message\n");
    status = DeviceIoControl(device, IOCTL_MESSAGE, inBuffer, sizeof(inBuffer), outBuffer, sizeof(outBuffer), &dwbytesRead, (LPOVERLAPPED)NULL);
    printf_s("Message sent!\n");
    printf_s("Received a message: %s\n", outBuffer);
    CloseHandle(device);

    return TRUE;
}
```

次に、プログラム（`userland.exe`）をゲスト VM にコピーします。たとえば、[Hyper-V の拡張セッションモードでローカルディスクを共有](https://learn.microsoft.com/en-us/windows-server/virtualization/hyper-v/learn-more/use-local-resources-on-hyper-v-virtual-machine-with-vmconnect)します。

次の図は、ユーザーランドのプログラムと Windows ドライバーのやり取りを示しています。  

{{< resourceFigure "figure2.png" "">}}
ユーザーランドのプログラムと、独自の Windows ドライバーのやり取りの図
{{< / resourceFigure >}}

{{< resourceFigure "figure3.png" "" 450>}}
`userland.exe` プログラムの使用例
{{< / resourceFigure >}}

## システムのスナップショットを取る

[ホストマシンの WinDbg に、`KmdfHelloWorld` ドライバーの PDB シンボルを追加します](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/setting-symbol-and-source-paths-in-windbg)。ドライバーのコンパイル時に、PDB ファイルが、ホストマシンの `x64\Release` ディレクトリに `*.sys` ファイルとともに作成されます。

次に、ホストマシンのまま、WinDbg を実行します。メニューから「Attach to kernel」を選びます。「Net」タブで、ポート番号とキーを設定し（KDNET の設定時と同じ設定を使います）、「Break on connection」を有効にします。最後に、ゲスト VM を再起動します。WinDbg のコマンドタブに、カーネルが WinDbg に正しくアタッチされ、実行が停止していることが表示されるはずです。

WinDbg で、ドライバーの `OnDeviceControl` 関数にブレークポイントを追加します。  
`bp KmdfHelloWorld!OnDeviceControl`。

そして、[WinDbg の `g` コマンド](https://learn.microsoft.com/en-us/windows-hardware/drivers/debuggercmds/g--go-)で実行を再開します。ゲスト VM を自由に使えるようになるまで、何度か行う必要があるかもしれません。次に、ゲスト VM で、コマンドライン（`cmd.exe`）からユーザーランドのプログラムを実行します。  
`.\userland.exe “aaaaaaaa”`

`userland.exe` プログラムは、指定したデバイスドライバーにコントロールコードを送ります。Windows ドライバーの `KmdfHelloWorld!OnDeviceControl` 関数に到達すると、WinDbg は、`mov qword ptr [rsp+8], rbx` 命令のブレークポイントで実行を停止します。

[Step Over](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/controlling-the-target#:~:text=through%20each%20instruction.-,Step%20Over,-treats%20the%20function) コマンド（F10 キー）を使って、ソースコードの次の行の後まで進めます。

`CHAR* messageFromUserland = (char*)Irp->AssociatedIrp.SystemBuffer;`

逆アセンブリのウィンドウでは、上のコード行は次のように表されます。

```
mov rsi, qword ptr [Irp->AssociatedIrp{.asterIrp} (rdi+18h)
lea rcx, [KmdfHelloWorld! ?? `::FNODOBFM::`string’` (fffff80334941d60)]
mov rdx, messageFromUserland (rsi)
```

逆アセンブリから、`messageFromUserland` のメッセージが RSI レジスタで指されていることが分かります。

WinDbg のコンソールで、カーネルに渡されたメッセージが RSI レジスタに格納されていることを確認できます。

```
kd> da @rsi
fffffe301`0af2c100 “aaaaaaaa”
```

シンボルを設定してあるので、次のコマンドも使えます。

```
kd> da messageFromUserland
fffffe301`0af2c100 “aaaaaaaa”
```

{{< resourceFigure "figure4.png" "">}}
ユーザーが渡したバッファを保持するレジスタの特定
{{< / resourceFigure >}}

また、[Locals ウィンドウ](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/locals-window)を使って、`DeviceIoControl` の出力とバッファの長さを確認できます（`Irp`\-\>`CurrentStackLocation`\-\>`[<Raw View>]` \-\> `Parameters` \-\> `DeviceIoControl` \-\> `OutputBufferLength` と `InputBufferLength`）。

{{< resourceFigure "figure5.png" "">}}
入力バッファと出力バッファの長さの特定
{{< / resourceFigure >}}

このウィンドウから、ファジングのときに `0x80` のバッファ長を超えてはならないことが分かります。

まとめると、次の図が、意図するファジングのループを示しています。  

{{< resourceFigure "figure6.png" "">}}
スナップショットに対して行う、意図するファジングのループ
{{< / resourceFigure >}}

### snapshot WinDbg 拡張機能を読み込む 

実行は、`mov rdx, messageFromUserland (rsi)` 命令の手前で止めてあります。スナップショットファジングを行うには、CPU の状態（汎用レジスタ、MSR、FPU の状態、セグメントなど）とゲスト VM の物理メモリをダンプする必要があります。

そのために、WinDbg で次のコマンドを実行して、[snapshot WinDbg 拡張機能](https://github.com/0vercl0k/snapshot)（ホストマシンの準備中にダウンロードしたもの）を読み込みます。

`.load \path\to\snapshot\snapshot.dll`

次に、スナップショットファイルを保存するディレクトリ（たとえば `C:\snapshots`）を作成し、WinDbg で次のコマンドを実行します。

`!snapshot -k active-kernel C:\snapshots\ioctl-snapshot`

スナップショットをダンプファイルに書き込むには、約 10 分かかります。`Dump successfully written` というメッセージが表示されるはずです。

{{< resourceFigure "figure7.png" "">}}
スナップショットの作成に成功した状態
{{< / resourceFigure >}}

スナップショットができたら、`C:\snapshots\ioctl-snapshot\regs.json` ファイルを編集し、[`cr8` コントロールレジスタを `0x0`](https://github.com/0vercl0k/wtf/issues/138#issuecomment-1779041225) に変更します。これは、現在知られているバグを回避し、wtf ファザーの実行時のエラーを防ぐためです（このバグの今後の修正は、[この GitHub issue](https://github.com/0vercl0k/snapshot/issues/12) で確認できます）。

さらに、次の関数のアドレスを書き留めておきます。これらは、後でハーネスの `Init` 関数を用意するときに定義します。これらのアドレスを簡単に保存できるようにするには、対象に合った PDB シンボルを設定しておく必要があることに注意してください。  
{{< hint warning >}}
アドレスは、ASLR のため現在のセッション固有のものであり、システムの再起動やドライバーの再読み込みで変わることに注意してください。
{{< /hint >}}  

* CheckTimestamp 関数  
```
kd> x KmdfHelloWorld!CheckTimestamp
fffff803`14a01000 KmdfHelloWorld!CheckTimestamp (union _LARGE_INTEGER)
```

* OnDeviceControl の戻りアドレス  
```
kd> u KmdfHelloWorld!OnDeviceControl+0x131
…
fffff803`14a01291 5f pop rdi
fffff803`14a01292 c3 ret
```

## ファジング用ハーネスを作成する

新しいファジング用ハーネス（つまりファザーのモジュール）を作成するには、`fuzzer_helloworld.cc` ファイルを `wtf/src/wtf` ディレクトリに追加します。ハーネスのコードは、テストケースをターゲットに挿入し、さまざまな条件を定義し、クラッシュを検出し、テストケースの終了を知らせる必要があります。

wtf ツールの [`fuzzer_dummy.cc`](https://github.com/0vercl0k/wtf/blob/main/src/wtf/fuzzer_dummy.cc) ファイルの内容を、`fuzzer_helloworld.cc` に貼り付けます。

1. モジュール名とターゲット名を `Dummy` から `FuzzHelloWorld` に変更します。

```c
#include "backend.h"
#include "targets.h"
#include <fmt/format.h>

namespace fs = std::filesystem;

namespace FuzzHelloWorld {

bool InsertTestcase(const uint8_t *Buffer, const size_t BufferSize) {
  return true;
}

bool Init(const Options_t &Opts, const CpuState_t &) {

  //
  // Catch context-switches.
  //

  if (!g_Backend->SetBreakpoint("nt!SwapContext", [](Backend_t *Backend) {
        fmt::print("nt!SwapContext\n");
        Backend->Stop(Cr3Change_t());
      })) {
    return false;
  }

  return true;
}

// 
// Register the target.
//

Target_t FuzzHelloWorld("FuzzHelloWorld", Init, InsertTestcase);

} // namespace FuzzHelloWorld
```

 

2. `InsertTestcase` 関数に、ファジングの入力をターゲットに渡すロジックを追加します。  
* `Buffer` は、ファズ入力のデータを含むバイト配列へのポインタです。  
* `BufferSize` は、`Buffer` のバイト単位のサイズです。

```c
bool InsertTestcase(const uint8_t *Buffer, const size_t BufferSize) {
  if (BufferSize > 0x80) return true;

  if (!g_Backend->VirtWriteDirty(Gva_t(g_Backend->Rsi()), Buffer, BufferSize)){
  fmt::print("Writing into RSI failed!\n");
  return false;
  }
  
  g_Backend->PrintRegisters();
  return true;
}
```

  `BufferSize` が `0x80` を超える場合、ロジックは、その入力を別のファジングの反復に回します。`0x80` 以下の場合は、テストケースの内容を、RSI レジスタ（`messageFromUserland`）が指すバッファに書き込みます。デバッグのために、ロジックはレジスタをコンソールに出力します。

{{< hint info >}}

  ハーネスを設定するときは、次のヒントを覚えておいてください。

* `g_Backend->Rax()`、`g_Backend->Rsi()` などを使って、さまざまなレジスタにアクセスできます。  
* 別のレジスタにアクセスしたいときは、`g_Backend->R8(value)` を使います（例: `g_Backend->R8(BufferSize)`）。
* メモリの一部を読みたいときは、`VirtRead`、`VirtRead4`、`VirtRead8` などを使えます（例: `g_Backend->VirtRead8(Gva_t(g_Backend->Rdx()));`）。

残念ながら、[wtf のバックエンド](https://github.com/0vercl0k/wtf/blob/main/src/wtf/backend.cc)は現在ドキュメントが十分でないため、より実践的な関数やハーネスの例については、ソースコードを調べる必要があります（[`fuzzer_hevd.cc`](https://github.com/0vercl0k/wtf/blob/main/src/wtf/fuzzer_hevd.cc)、[`fuzzer_ioctl.cc`](https://github.com/0vercl0k/wtf/blob/main/src/wtf/fuzzer_ioctl.cc)、[`fuzzer_tlv_server.cc`](https://github.com/0vercl0k/wtf/blob/main/src/wtf/fuzzer_tlv_server.cc)）。    
{{< /hint >}}

3. 次に、ファジング中のロジックを設定するための `Init` 関数を用意します。

   まず、フックする必要のある重要なアドレスを定義します。`OnDeviceControl`（具体的にはその戻りアドレス）と `CheckTimestamp` で、これらはスナップショットを作成したときに書き留めたものです。

```c
    const Gva_t OnDeviceControlEnd = Gva_t(0xfffff80314a01292);
    const Gva_t CheckTimestamp = Gva_t(0xfffff80314a01000);
```

次に、これらのフックと、ほかの 2 つのフックを設定します。 

**フック 1: タイムスタンプの検証を回避する**  
このフックは、ドライバーの `CheckTimestamp` 関数が常に true を返すようにして（便利な `Backend->SimulateReturnFromFunction(1)` 関数を使います）、タイムスタンプのチェックが成功したものとして扱います。これにより、ターゲットが入力を拒否するのを防ぎます。

{{< hint info >}}
さまざまな関数をフックすることは、チェックサムやハッシュなどの値をチェックするターゲットをファジングするときに、非常に役立ちます。
{{< /hint >}}

```c
    if (!g_Backend->SetBreakpoint(
        CheckTimestamp,
        [](Backend_t *Backend) {
            Print("Hooking CheckTimestamp\n");
            Backend->SimulateReturnFromFunction(1); // Force return value of 1 (success)
        }
    )) {
        Print("Failed to set breakpoint: CheckTimestamp\n");
        return false;
    }
```

**フック 2: 実行の終了の目印**  
次のブレークポイントは、現在の反復をいつ止めるかをファザーに伝えます。これは、境界を正しくファジングし、無限ループを避けるために重要です。

```c
    if (!g_Backend->SetBreakpoint(OnDeviceControlEnd, [](Backend_t *Backend) {
        Print("Reached end!\n");
        Backend->Stop(Ok_t()); // Signal successful completion
    })) {
        Print("Failed to set breakpoint: OnDeviceControlEnd\n");
        return false;
    }
```

**フック 3: コンテキストスイッチの監視**  
このフックは、コンテキストスイッチを捕捉します。 

```c
    if (!g_Backend->SetBreakpoint("nt!SwapContext", [](Backend_t *Backend) {
        fmt::print("nt!SwapContext\n");
        Backend->Stop(Cr3Change_t()); // Signal CR3 register change (page directory)
    })) {
        return false;
    }
```

**フック 4: クラッシュの検出**  
このフックは、システムのクラッシュを捕捉し、そのクラッシュをファイルに収集します。

```c
    if (!g_Backend->SetBreakpoint("nt!KeBugCheck2", [](Backend_t *Backend) {
        // Collect all bugcheck parameters
        const uint32_t BCode = Backend->GetArg4(0);  // Bugcheck code
        const uint64_t B0 = Backend->GetArg8(1);     // Parameter 1
        const uint64_t B1 = Backend->GetArg8(2);     // Parameter 2
        const uint64_t B2 = Backend->GetArg8(3);     // Parameter 3
        const uint64_t B3 = Backend->GetArg8(4);     // Parameter 4
        const uint64_t B4 = Backend->GetArg8(5);     // Parameter 5

        // Create unique crash filename using all bugcheck parameters
        // This helps identify unique crashes and avoid duplicates
        const std::string Filename =
            fmt::format("crash-{:#x}-{:#x}-{:#x}-{:#x}-{:#x}-{:#x}", 
                       BCode, B0, B1, B2, B3, B4);
        
        Print("KeBugCheck2: {}\n", Filename);
        Backend->Stop(Crash_t(Filename)); // Signal crash with identifying information
    })) {
        fmt::print("Failed to SetBreakpoint KeBugCheck2\n");
        return false;
    }
```

スナップショットファジングのハーネスの全体は、次のとおりです。

```c
#include "backend.h"
#include "targets.h"
#include <fmt/format.h>

namespace FuzzHelloWorld {
    
    template <typename... Args_t>
    void Print(const char *Format, const Args_t &...args) {
        fmt::print(Format, args...);
    }


bool InsertTestcase(const uint8_t *Buffer, const size_t BufferSize) {
    if (BufferSize > 0x80) return true;
    if(!g_Backend->VirtWriteDirty(Gva_t(g_Backend->Rsi()), Buffer, BufferSize)) {
        Print("Writing into RSI failed\n");
        return false;
    } else {
        // Print("Written {} with {:#x} size\n", Buffer, BufferSize);
    }
  
  
  return true;
}

bool Init(const Options_t &Opts, const CpuState_t &) {
    const Gva_t currentRIP = Gva_t(g_Backend->Rip()); // RIP register when doing snapshot
    const Gva_t OnDeviceControlEnd = Gva_t(0xfffff80314a01292);
    const Gva_t CheckTimestamp = Gva_t(0xfffff80314a01000);

    Print("Current RIP: {:#x}\n", currentRIP);

    // Bypass CheckTimestamp check
    if (!g_Backend->SetBreakpoint(
        CheckTimestamp,
        [](Backend_t *Backend) {
            Print("Hooking CheckTimestamp\n");
            Backend->SimulateReturnFromFunction(1);
        }
    )) {
        Print("Failed to set breakpoint: CheckTimestamp\n");
        return false;
    }

    // Stop at the end of the OnDeviceControlEnd address
    if (!g_Backend->SetBreakpoint(OnDeviceControlEnd, [](Backend_t *Backend) {
        Print("Reached end!\n");
        Backend->Stop(Ok_t());
    })) {
        Print("Failed to set breakpoint: OnDeviceControlEnd\n");
        return false;
    }

  // Catch context-switches
  if (!g_Backend->SetBreakpoint("nt!SwapContext", [](Backend_t *Backend) {
        fmt::print("nt!SwapContext\n");
        Backend->Stop(Cr3Change_t());
      })) {
    return false;
  }

  // Catch bugchecks.
  if (!g_Backend->SetBreakpoint("nt!KeBugCheck2", [](Backend_t *Backend) {
        const uint32_t BCode = Backend->GetArg4(0);
        const uint64_t B0 = Backend->GetArg8(1);
        const uint64_t B1 = Backend->GetArg8(2);
        const uint64_t B2 = Backend->GetArg8(3);
        const uint64_t B3 = Backend->GetArg8(4);
        const uint64_t B4 = Backend->GetArg8(5);
        const std::string Filename =
            fmt::format("crash-{:#x}-{:#x}-{:#x}-{:#x}-{:#x}-{:#x}", BCode, B0,
                        B1, B2, B3, B4);
        Print("KeBugCheck2: {}\n", Filename);
        Backend->Stop(Crash_t(Filename));
      })) {
    fmt::print("Failed to SetBreakpoint KeBugCheck2\n");
    return false;
  }

  return true;
}

// Register the target.
Target_t FuzzHelloWorld("FuzzHelloWorld", Init, InsertTestcase);

} // namespace FuzzHelloWorld
```

### ハーネスのコンパイル

ハーネスをコンパイルするには、[Visual Studio Developer Command Prompt](https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell?view=vs-2022) を開き、`wtf\src\build` ディレクトリに移動して、[`build-release-msvc.bat`](https://github.com/0vercl0k/wtf/blob/main/src/build/build-release-msvc.bat) スクリプトを実行します。コンパイルはエラーなく終わるはずで、最後の行に、コンパイルされた wtf のバイナリ（`wtf.exe`）のパスが表示されます。

{{< hint warning >}}
ハーネスを変更するたびに、再コンパイルが必要です。コンパイルがエラーなく終わることを確認してください。  
{{< /hint >}}

## ファジングを実行する

ファジングを実行するには、`wtf\targets` ディレクトリに移動して、新しく `FuzzHelloWorld` ディレクトリを作成します。`FuzzHelloWorld` ディレクトリの中に、次のディレクトリを作成します。

1. `inputs`: このディレクトリには、ファザーの最初のシード入力を置きます。入力として `AAAAA` を書いた、適当な `test.txt` ファイルを作成します。  
2. `outputs`: このディレクトリには、観測されたコードカバレッジを達成する、現在の最小の入力の集合が保存されます。  
3. `crashes`: このディレクトリには、ターゲットをクラッシュさせた入力が保存されます。  
4. `state`: このディレクトリには、スナップショットのファイルを置きます。`C:\snapshots\ioctl-snapshot` ディレクトリの `mem.dmp` と `regs.json` ファイルをここに置きます。

### サーバーノードを起動する

サーバーノードは、ファザーのすべての状態（コードカバレッジとコーパス）を管理します。また、テストケースを生成して、クライアントに配布します。次のコマンドで、サーバーノードを実行します。  
```
C:\Users\User\wtf\targets\FuzzHelloWorld> ..\..\bin\wtf.exe master --name FuzzHelloWorld --max_len=4096
```

* `name` は、ハーネスで指定したモジュール名です。  
* `max_len` は、生成されるテストケースのサイズの上限です。

### ファジングノードを実行する

別のコマンドウィンドウで、次のコマンドを使って、ファジングノードを実行します。既定では、`bochscpu` の[バックエンド実行](https://github.com/0vercl0k/wtf/?tab=readme-ov-file#execution-backends)が使われます。  
```
C:\Users\User\wtf\targets\FuzzHelloWorld> ..\..\bin\wtf.exe fuzz --name FuzzHelloWorld
```

サーバーノードがしばらく（数秒）動いた後、master のウィンドウに次のように表示されるはずです。  
```
Saving crash in C:\Users\User\wtf\targets\FuzzHelloWorld\crashes\crash-0x3b-0xc0000005-0xfffff80314a01233-0xfffff90641f9ec90-0x0-0x0  
#7346 cov: 4667 (+4667) corp: 3 (114.0b) exec/s: 7.3/k (1 nodes) lastcov: 1.0s crash: 997 timeout: 0 cr3: 0 uptime: 5.0s  
```

* `cov`: ファザーが達成した現在のコードカバレッジです。通常は、基本ブロック、エッジ、その他の実行されたコード単位で測られます。数値が大きいほど、ターゲットのコードがより多く探索されたことを示します。  
* `corp`: 現在のコーパスのサイズです。コーパスは、ファザーが見つけた、ユニークで興味深い入力の集合です。サイズの値は、ファイルの数と、すべてのコーパスファイルの合計サイズを表します。  
* `exec/s`: ファザーがテストケースを実行する速度です。すべてのノードをあわせて、ファザーが 1 秒間に処理できる入力の数を測ります。一般に、数値が大きいほど性能が高いことを示します。  
* `lastcov`: 最後に新しいカバレッジが見つかってからの時間です。  
* `crash`: ファザーが見つけた、ユニークなクラッシュの数です。

利用できるハードウェアの資源、ターゲットの複雑さ、ファジングの戦略に応じて、ファジングノードを段階的に追加するとよいでしょう。

クラッシュを起こした入力は、次のようになっているはずです。  
```
C:\Users\User\wtf\targets\FuzzHelloWorld> type crashes\crash-0x3b-0xc0000005-0xfffff80314a01233-0xfffff90641f9ec90-0x0-0x0
DEADBEEFf
```

### クラッシュのトリアージ

さまざまな種類のトレースの生成については、wtf の標準のドキュメントを参照してください。

* [実行トレースの生成](https://github.com/0vercl0k/wtf?tab=readme-ov-file#generating-execution-traces)（単純なテキスト形式のトレース）  
  * シンボル付きの実行トレースを得るには、[`symbolizer-rs`](https://github.com/0vercl0k/symbolizer-rs/) と [`--import-pdbs`](https://github.com/0vercl0k/symbolizer-rs/issues/6#issuecomment-2283061416) フラグを使って、`KmdfHelloWorld.pdb` ファイルをシンボルキャッシュに取り込みます  
* [Tenet トレースの生成](https://github.com/0vercl0k/wtf?tab=readme-ov-file#generating-tenet-traces)（[Tenet](https://github.com/gaasedelen/tenet) で IDA に読み込める、視覚的なトレース）  
* [コードカバレッジトレースの生成](https://github.com/0vercl0k/wtf?tab=readme-ov-file#generating-code-coverage-traces)（[Lighthouse](https://github.com/gaasedelen/lighthouse) で IDA に読み込める、視覚的なカバレッジ）

### 実行バックエンド

上の例で使った実行バックエンドは、bochscpu にもとづいています。[wtf がサポートする実行バックエンド](https://github.com/0vercl0k/wtf/?tab=readme-ov-file#execution-backends)の比較を参照してください。長い実行を高速化するには、KVM バックエンドの利用を検討してください。また、ここで示したファジングの方法は Windows で実演しましたが、スナップショットファジングは、Linux のマシンでもファジングノードを手軽にスケールさせる方法になることにも注意してください。
