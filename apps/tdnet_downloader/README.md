# TDnet 決算短信 XBRL Downloader

TDnet（適時開示情報閲覧サービス）から
**指定した証券コード（ticker）の「決算短信」XBRLファイルのみを自動ダウンロード**する Python スクリプトです。

* Playwright を使ったブラウザ自動操作
* 表記ゆれ（決算短信 / 四半期決算短信 / 通期決算短信）に対応
* 複数ヒットした場合は **最新1件のみ取得**
* 設定は `config.yaml` で外部管理

---

## 特徴

> 📄 **仕様書（SRS）**  
> 本プロジェクトの詳細な要件・仕様は以下を参照してください。  
> - [`docs/SRS.md`](docs/SRS.md)

* ✅ 複数 ticker を一括処理
* ✅ 決算短信以外（適時開示など）を除外
* ✅ 表記ゆれに強い
* ✅ 途中で失敗しても他の ticker は継続
* ✅ 設定変更は `config.yaml` のみ

---

## ディレクトリ構成

```
tdnet_downloader/
├─ README.md
├─ requirements.txt
├─ config/
│  ├─ config.yaml
│  └─ config.sample.yaml
├─ src/
│  ├─ tdnet_downloader.py
│  └─ __init__.py
├─ downloads/
└─ logs/
```

---

## 動作環境

* Windows / macOS / Linux
* Python 3.9 以上（推奨）
* Google Chrome / Microsoft Edge（Playwright 同梱ブラウザ可）

---

## インストール

### 1. Python パッケージ

```bash
pip install playwright pyyaml
```

### 2. Playwright ブラウザのインストール

```bash
playwright install
```

---

## 設定ファイル（config.yaml）

`config/config.yaml` を編集してください。

```yaml
tdnet:
  date_from: "20251230"
  out_dir: "downloads"
  tickers:
    - "7388"
    - "7203"
    - "6758"

playwright:
  headless: false
  wait_ms: 800
```

### 設定項目の説明

| 項目          | 説明                    |
| ----------- | --------------------- |
| `date_from` | 検索開始日（YYYYMMDD）       |
| `tickers`   | 証券コードのリスト             |
| `out_dir`   | ダウンロード先ディレクトリ         |
| `headless`  | ブラウザ非表示実行（true/false） |
| `wait_ms`   | ticker 処理間の待ち時間（ms）   |

---

## 実行方法

プロジェクト直下で実行します。

```bash
python src/tdnet_downloader.py --config config/config.yaml
```

---

## 実行結果

* 決算短信の XBRL（ZIP）が `downloads/` に保存されます
* ファイル名は `ticker_元のファイル名.zip` 形式になります

例：

```
downloads/
├─ 7388_081220260114533459.zip
├─ 7203_081220260115012345.zip
```

---

## 処理内容の概要

1. TDnet サイトを開く
2. 証券コードで検索
3. 検索結果から

   * 証券コード一致
   * 決算短信（表記ゆれ対応）
4. 最新の1件を選択
5. XBRL ファイルをダウンロード

---

## 注意事項

* TDnet は公式 API を提供していません
  → アクセス頻度には十分注意してください
* 大量 ticker の連続実行は避け、適切な待ち時間を設定してください

---

## 今後の拡張アイデア

* ダウンロード済みファイルのスキップ
* 決算短信が無い場合の PDF フォールバック
* ZIP 自動解凍 → XBRL パース
* EDINET / e-Stat 連携

---

