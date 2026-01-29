# architecture.md

本ドキュメントは **TDnet 決算短信 XBRL Downloader** の処理フロー（図レベル）と、主要コンポーネントの責務をまとめます。

---

## 1. 全体像

* 入力：`config/config.yaml`
* 処理：Playwright で TDnet を検索し、決算短信（表記ゆれ対応）の **最新1件** の XBRL（ZIP）をダウンロード
* 出力：`downloads/{ticker}_{suggested_filename}.zip`

---

## 2. コンポーネント構成

### 2.1 論理コンポーネント

* **CLI（tdnet_downloader.py）**

  * `--config` で設定ファイルのパスを受け取る
  * 設定ロード → ダウンロード処理呼び出し → 結果サマリ出力

* **Config Loader**

  * YAML を読み込み、`tdnet` / `playwright` 設定を取り出す

* **Downloader（Playwright）**

  * TDnet へアクセス
  * 検索フォーム iframe を操作
  * 結果一覧 iframe（mainlist）を解析
  * 決算短信（表記ゆれ）に合致する行の XBRL をクリックしダウンロード

* **Storage（File System）**

  * `downloads/` に保存
  * ticker をファイル名に付与して上書き防止

---

## 3. 処理フロー（概要）

### 3.1 フロー図（Mermaid）

```mermaid
flowchart TD
  A[Start] --> B[Load config.yaml]
  B --> C[Launch Playwright Browser]
  C --> D[Open TDnet URL]
  D --> E[Get search iframe]
  E --> F[Set date_from]
  F --> G{for each ticker}

  G --> H[Fill ticker]
  H --> I[Click Search]
  I --> J[Get mainlist iframe]
  J --> K[Wait rows appear]
  K --> L[Filter rows by keywords
  決算短信/四半期決算短信/通期決算短信]
  L --> M{match found?}

  M -- No --> N[Record None & continue]
  M -- Yes --> O[Pick latest row (first)]
  O --> P[Click XBRL link]
  P --> Q[Expect download]
  Q --> R[Save as downloads/{ticker}_*.zip]
  R --> S[Wait wait_ms]
  S --> G

  N --> G
  G -->|done| T[Close context/browser]
  T --> U[Print summary]
  U --> V[End]
```

> 補足：TDnet の検索結果は通常「新しい順」に並ぶ想定のため、フィルタ後の `.first` を **最新** として扱います。

---

## 4. 詳細フロー（ticker 1件分）

1. 検索フォーム iframe 内の `#freewordtxt` に ticker を入力
2. `#searchbtn` をクリック
3. 結果一覧 iframe（`iframe[name="mainlist"]`）を取得
4. `tr` 行を ticker で絞る
5. 行テキストに決算短信キーワード（表記ゆれ）を含むものを探す
6. 該当が複数の場合、先頭（最新）を採用
7. 行内の `XBRL` リンクをクリックし、`expect_download` でダウンロードイベントを待つ
8. `downloads/` に `ticker_` プレフィックス付きで保存

---

## 5. フレーム構造（TDnet UI）

TDnet は iframe を含む構造のため、操作対象を明確にします。

* **トップページ**

  * `iframe`：検索フォーム（日付選択・キーワード・検索ボタン）

    * その内側に `iframe[name="mainlist"]`：検索結果一覧

処理では以下の順で frame を取得します。

1. `page.locator("iframe").content_frame` → **検索フォーム**
2. `frame.locator('iframe[name="mainlist"]').content_frame` → **結果一覧**

---

## 6. 待機（wait）設計

* **基本方針**：`sleep` ではなく、要素の可視化やダウンロードイベントを根拠に待つ

主な待機ポイント：

* 検索結果が出たこと：`rows.first.wait_for(timeout=15000)`
* XBRL リンクが押せること：`xbrl.wait_for(state="visible")`
* ダウンロード開始：`page.expect_download(timeout=20000)`
* 次 ticker 前の小休止：`page.wait_for_timeout(wait_ms)`

---

## 7. 例外・リカバリ方針

* 決算短信行が見つからない：`None` を記録して継続
* タイムアウト：`None` を記録して継続
* その他例外：例外内容を出力し `None` を記録して継続

> 方針：**1社の失敗で全体を止めない**

---

## 8. 設定（config.yaml）との対応

例：

```yaml
tdnet:
  date_from: "20251230"
  out_dir: "downloads"
  tickers:
    - "7388"

playwright:
  headless: false
  wait_ms: 800
```

* `tdnet.date_from`：検索開始日（検索フォームの t0）
* `tdnet.tickers`：処理対象の ticker 群
* `tdnet.out_dir`：保存先
* `playwright.headless`：ブラウザ表示/非表示
* `playwright.wait_ms`：ticker 間の待ち

---

## 9. 今後の拡張ポイント

* **ダウンロード済みスキップ**：保存済みファイルの存在チェック
* **PDFフォールバック**：決算短信行はあるが XBRL 無い場合に PDF を取得
* **ZIP自動解凍 + XBRL解析**：取得後に解析パイプラインへ接続
* **ログ出力強化**：`logs/` へのファイルログ（ローテーション含む）
