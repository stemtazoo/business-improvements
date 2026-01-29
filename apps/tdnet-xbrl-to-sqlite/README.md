# tdnet-xbrl-to-sqlite

TDnetの「決算短信」XBRL（iXBRLを含む ZIP）を解析し、
**facts / contexts / units / labels** を正規化して **SQLite データベースに保存**するための Python CLI アプリです。

This is a Python CLI tool that ingests TDnet earnings report XBRL/iXBRL ZIP files and stores normalized data into SQLite.

---

## 🎯 Purpose / 目的

* TDnetから取得した決算短信XBRLを **機械可読な形で永続化** する
* 複数企業・複数期のデータを **安全に蓄積** する
* 分析・可視化・指標計算は **別アプリに委譲** する（本アプリはETL専用）

---

## ✨ Features

* CLIによる単発ZIP取込（初期実装）
* iXBRL（XHTML）からの fact 抽出

  * `ix:nonFraction`（数値）
  * `ix:nonNumeric`（非数値）
* 数値正規化（カンマ除去、括弧・符号処理）
* SQLite への UPSERT 保存（再実行耐性あり）
* ZIP の sha256 による重複取込防止
* Summary / Attachment（BS・PL・CF 含む）すべて対応
* 将来拡張：フォルダ監視による自動取込

---

## 🧱 Architecture Overview

```
ZIP
 └─ discover (ZIP内構造検出)
     └─ extract
         ├─ ixbrl facts
         ├─ contexts
         ├─ units
         └─ labels
             ↓
         normalize
             ↓
         SQLite (facts / contexts / units / labels / filings)
```

* **extract（抽出）** と **db（保存）** を分離
* ZIPは原則展開せずに直接読み取り
* 将来 `watchdog` 等を追加しても ingest pipeline を再利用可能

---

## 📦 Requirements

* Python **3.11+**
* SQLite（Python標準で利用可）
* lxml

---

## 📥 Install

```bash
pip install -e .
```

または依存関係のみ：

```bash
pip install -r requirements.txt
```

---

## ▶️ Usage

```bash
tdnet-xbrl-ingest \
  --zip path/to/tdnet_xbrl.zip \
  --db tdnet_xbrl.sqlite
```

### Options

* `--zip` : TDnet決算短信XBRLのZIPファイル（必須）
* `--db` : SQLite DBファイルパス（デフォルト: `tdnet_xbrl.sqlite`）
* `--on-duplicate` : 同一ZIP再投入時の挙動

  * `skip`（デフォルト）
  * `replace`

---

## 🗄 Database Schema (Summary)

主要テーブル：

* `filings` : 取込単位（ZIP）
* `facts` : XBRL facts（数値・非数値）
* `contexts` : 会計期間・次元
* `units` : 通貨・単位
* `labels` : 勘定科目ラベル（日本語）

詳細は以下を参照：

* `docs/db_schema.md`

---

## 🧪 Development & Test

```bash
pytest
```

推奨テスト：

* 数値正規化（符号・括弧）
* iXBRL fact 抽出
* 同一ZIP再投入時の重複防止

---

## 🚧 Roadmap

* [x] CLI 単発取込
* [x] facts / labels 保存
* [ ] contexts / units 抽出
* [ ] フォルダ監視による自動取込
* [ ] PostgreSQL 対応（任意）

---

## 📄 Docs

* `docs/SRS.md` : 要件定義（IEEE 830 / ISO/IEC/IEEE 29148）
* `docs/architecture.md`
* `docs/db_schema.md`
* `docs/etl_spec.md`

---

## ⚠️ Notes

* 本アプリは **ETL専用** です。分析・可視化は別アプリで行ってください。
* TDnet XBRL の構成差異に耐えるため、警告ログを出して処理継続します。

---

## 📜 License

TBD
