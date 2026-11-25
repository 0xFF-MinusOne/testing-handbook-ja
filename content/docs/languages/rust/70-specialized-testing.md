---
title: "専門的なテスト"
slug: specialized-testing
weight: 70
---

# Rust の専門的なテスト

## 並行処理のテスト

[Shuttle](https://github.com/awslabs/shuttle)

* 健全ではないが、スケールする
* プロパティテストと同じように動く

[Loom](https://docs.rs/loom/latest/loom/)

* 健全だが、遅い
* モデル検査器と同じように動く

## フォールトインジェクション

[MadSim](https://github.com/madsim-rs/madsim)

* `tokio` と `tonic` のクレートを、シミュレーション版に置き換える
* 障害を注入し、ランダム性を高める

[fail-rs](https://github.com/tikv/fail-rs)

* コードに `fail_point!` マクロを手作業で追加する必要がある
