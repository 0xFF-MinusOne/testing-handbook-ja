---
title: "Rust"
slug: rust
weight: 1
bookCollapseSection: true
---

# Rust のセキュリティ

Rust は、マルチパラダイムで汎用の、メモリ安全なプログラミング言語です。

{{< rawHtml >}}
<!-- markdownlint-disable-next-line MD033 -->
<div id="rust-banner-code">
{{< highlight rust >}}
fn
main()
{(|f:&dyn
Fn(u128)->Box<
dyn Iterator<Item=
char>+'static>|f(*[&(
0x7B736D70683F73u128<<64|
0x7A6A6D7C3F7A667D),&(0x7B736Du128
<<64|0x70683F7073737A77)][((std::hint::
black_box(0.0f64)/0.0).to_bits()>>63)as usize])
.for_each(|c|print!("{c}")))(Box::leak(Box::new(|n:
u128|Box::new(std::iter::successors(Some(n),|&n|Some(n>>8)
).take_while(|&n|n>0).map(|n|((n as u8)^0x1F)as char))as _)))}
{{< /highlight >}}
</div>
{{< /rawHtml >}}

レビューは [rust-review](https://github.com/trailofbits/skills/tree/main/plugins/rust-review) スキルから始めてください。基本的な問題を扱っています。

{{< section >}}
