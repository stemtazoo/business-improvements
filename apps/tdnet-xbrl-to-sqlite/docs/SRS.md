# ソフトウェア要件仕様書（SRS）

* 対象システム名: **TDnet 決算短信 XBRL 取込・DB化アプリ（CLI）**
* 版: 1.0
* 作成日: 2026-01-29
* 作成者: （ユーザー）/ ChatGPT
* 準拠: IEEE 830 / ISO/IEC/IEEE 29148

---

## 1. 序文

### 1.1 目的

本仕様書は、TDnetからダウンロードした「決算短信」XBRL（ZIP）を解析し、抽出したデータをSQLiteに保存するPythonアプリケーション（以下「本システム」）の要件を定義する。

### 1.2 範囲

本システムは、以下を実現する。

* 入力: TDnet提供の「決算短信」XBRL ZIP
* 処理: ZIPからXBRL/iXBRL関連ファイルを読み取り、事実（facts）・コンテキスト（contexts）・単位（units）・ラベル（labels）等を抽出
* 出力: 抽出結果をSQLiteデータベースへ永続化

本システムは、DBに保存するまでを責務とし、保存後の分析・可視化・指標算出は別アプリケーションで実施する。

対象範囲は **Summary と Attachment（BS/PL/CF等）を含む全て** とし、処理対象ファイルを複数に分けて実装してもよい。

運用は当初 **単発CLI取込** を基本とし、将来拡張として **フォルダ監視による自動取込** を可能とする。

### 1.3 用語・略語

* TDnet: 東京証券取引所の適時開示情報伝達システム
* XBRL: eXtensible Business Reporting Language
* iXBRL: Inline XBRL（XHTMLにXBRLのタグを埋め込む形式）
* fact: XBRLで定義された財務値・文字情報（数値/非数値）
* context: factの適用期間・識別子・次元（軸）
* unit: 通貨（JPY等）や比率（pure）などの単位
* taxonomy: 勘定科目等の概念定義（名前空間や要素）

### 1.4 参照文書

* IEEE Std 830（Software Requirements Specifications）
* ISO/IEC/IEEE 29148（Requirements Engineering）
* TDnetのXBRL仕様（ユーザーが保有/参照可能な範囲）

### 1.5 文書構成

本仕様書は、製品概要、外部インタフェース、機能要件、非機能要件、データ要件、品質・制約、付録・トレーサビリティから構成される。

---

## 2. 全体的記述

### 2.1 製品展望

本システムは、TDnetの決算短信XBRLをDBに蓄積する「取込基盤」として機能する。複数企業・複数期の継続取込を想定し、データの正規化と再現性（同一入力→同一出力）を重視する。

### 2.2 製品機能（要約）

* ZIP入力（単発）
* ZIP内ファイル検出（Summary/Attachment）
* iXBRL/XBRLからfacts/contexts/units抽出
* ラベル（日本語）抽出と概念名への紐付け
* SQLiteへUPSERT保存（重複回避、再実行耐性）
* ログ出力（処理件数、警告、エラー）

### 2.3 ユーザ特性

* ユーザはPythonの基本操作およびCLI実行が可能
* XBRLの詳細知識は必須としない（ただし拡張時に参照可能）

### 2.4 運用環境

* OS: Windows / macOS / Linux（開発優先は問わない）
* Python: 3.11+（推奨）
* DB: SQLite（ファイルベース）

### 2.5 設計・実装制約

* 取込対象はTDnet決算短信XBRL ZIP
* 初期はCLI単発取込
* 将来のフォルダ監視拡張を阻害しないモジュール分割（入出力の抽象化）

### 2.6 前提・依存関係

* 入力ZIPはTDnetから正規に取得されたもの
* ZIP内構成はTDnetの標準に概ね準拠（例: XBRLData/Summary, XBRLData/Attachment 等）
* 例外的構成（欠損ファイル、命名差異）があり得るため、耐性を持つ

---

## 3. 外部インタフェース要件

### 3.1 ユーザインタフェース

* CLIのみ
* 標準出力: 処理サマリー（filing数、fact数、警告数、処理時間）
* 標準エラー: エラー内容

### 3.2 ハードウェアインタフェース

* なし

### 3.3 ソフトウェアインタフェース

* SQLite（標準: sqlite3、またはSQLAlchemy）
* ZIP読み取り: Python標準 `zipfile`
* XML/XHTML解析: `lxml`（推奨）または `xml.etree.ElementTree`

### 3.4 通信インタフェース

* なし（ネットワークアクセス不要）

---

## 4. 機能要件

### 4.1 入力ZIP受付（FR-1）

**概要**: ユーザが指定したZIPファイルを入力として受け付ける。

* 入力: `--zip <path>`
* 出力: 処理開始ログ
* 例外: ファイル無し/読めない場合はエラー終了（終了コード≠0）

**受入基準**:

* 指定ZIPが存在し読み取り可能なら処理が開始される。

---

### 4.2 ZIP内コンテンツ検出（FR-2）

**概要**: ZIP内の構成を走査し、処理対象ファイル（iXBRL/XBRL、lab等）を特定する。

* 期待されるパス例:

  * `XBRLData/Summary/*-ixbrl.htm`
  * `XBRLData/Attachment/*-ixbrl.htm`
  * `XBRLData/**/**/*-lab.xml` など
* 動作:

  * Summary/AttachmentのiXBRLを優先
  * lab.xmlがあれば読み取り対象に含める

**受入基準**:

* 少なくとも1つのiXBRL/HTMLが見つかれば抽出処理へ進む。
* 想定外構成でも、可能な範囲で検出し、致命的でなければ継続する。

---

### 4.3 iXBRLからfacts抽出（FR-3）

**概要**: iXBRL（XHTML）から `ix:nonFraction`（数値）と `ix:nonNumeric`（非数値）を抽出し、factレコードに変換する。

* 抽出項目（最小）:

  * `name`（QName/要素名）
  * `contextRef`
  * `unitRef`（数値のみ）
  * `decimals` / `precision`（存在する場合）
  * `sign`（負符号や括弧表現の正規化）
  * `value`（正規化後の値: 数値/文字列）
  * `raw`（元テキスト）
  * `source_file`（ZIP内パス）
  * `source_fragment`（任意: 参照用の短い抜粋 or element id）

* 正規化:

  * 数値のカンマ除去
  * 括弧（△、( )）や `sign` 属性を考慮した符号統一
  * 空白や改行のトリム

**受入基準**:

* iXBRL内の対象タグがfactとしてDBに保存される。
* パースできない値があっても、該当factを警告扱いにして継続できる（設定可能）。

---

### 4.4 contexts抽出（FR-4）

**概要**: XBRLインスタンス（またはiXBRLに埋め込まれたcontext定義）から `xbrli:context` を抽出する。

* 抽出項目:

  * `context_id`
  * entity識別子（scheme, identifier）
  * 期間（instant または startDate/endDate）
  * 次元（xbrldi:explicitMember / typedMember）

**受入基準**:

* factの `contextRef` に対応するcontextが保存される（見つからない場合は警告）。

---

### 4.5 units抽出（FR-5）

**概要**: `xbrli:unit` を抽出し、unitレコードに変換する。

* 抽出項目:

  * `unit_id`
  * measure（例: iso4217:JPY, xbrli:pure）

**受入基準**:

* 数値factの `unitRef` が参照できるunitが保存される（見つからない場合は警告）。

---

### 4.6 labels抽出（FR-6）

**概要**: `*-lab.xml` 等からラベルを抽出し、概念名（QName）へ紐付ける。

* 抽出項目:

  * `concept_name`（QName/要素名）
  * `label_role`（標準/冗長/短い等）
  * `language`（例: ja）
  * `label_text`（日本語ラベル）

**受入基準**:

* 日本語ラベルがDBに格納され、factのnameと結合可能になる。

---

### 4.7 filingメタデータ登録（FR-7）

**概要**: 取込単位（ZIP）を1つのfilingとして登録し、以後のレコードと関連付ける。

* 抽出/生成:

  * `filing_id`（内部ID）
  * `source_zip_name`
  * `source_zip_sha256`
  * `ingested_at`
  * 任意: 提出会社コード/提出日/会計期間（抽出可能なら）

**受入基準**:

* 同一ZIP（同一sha256）を再投入しても二重登録を回避し、既存filingへ紐付く（挙動は設定で上書き/スキップ）。

---

### 4.8 SQLiteへの保存（FR-8）

**概要**: 抽出したfacts/contexts/units/labelsをSQLiteへ保存する。

* 要件:

  * トランザクションで整合性を保つ
  * 再実行耐性（UPSERT）
  * インデックス作成（検索のため）

**受入基準**:

* 取込後、DBにfilingと関連レコードが存在する。
* 途中で失敗した場合、ロールバックされDBが中途半端な状態にならない。

---

### 4.9 ログ・レポート（FR-9）

**概要**: 取込結果をログで確認できる。

* 最小出力:

  * 取込ZIP名
  * 検出した対象ファイル数
  * 保存したfact/context/unit/label件数
  * 警告件数（欠損参照、値パース不可等）

**受入基準**:

* CLI実行後、件数が確認できる。

---

### 4.10 将来拡張: フォルダ監視取込（FR-10 / Future）

**概要**: 監視フォルダにZIPが置かれたら自動で取込する。

* 初期版では「設計考慮（モジュール分離）」のみ必須
* 将来: `watchdog` 等で実装

---

## 5. データ要件

### 5.1 データモデル（論理）

* filing 1 — N facts
* filing 1 — N contexts
* filing 1 — N units
* filing 1 — N labels（またはtaxonomy単位で共有可能だが、初期はfiling紐付けでよい）

### 5.2 SQLiteスキーマ（提案）

* `filings`

  * `id` PK
  * `zip_name`
  * `zip_sha256` UNIQUE
  * `ingested_at`
  * `company_code` NULL可
  * `period_start` NULL可
  * `period_end` NULL可
  * `doc_type` NULL可
* `contexts`

  * `id` PK
  * `filing_id` FK
  * `context_ref`
  * `entity_scheme` NULL可
  * `entity_identifier` NULL可
  * `period_type`（instant/duration）
  * `instant_date` NULL可
  * `start_date` NULL可
  * `end_date` NULL可
  * `dimensions_json`（JSON文字列）
  * UNIQUE(`filing_id`,`context_ref`)
* `units`

  * `id` PK
  * `filing_id` FK
  * `unit_ref`
  * `measures_json`（JSON文字列）
  * UNIQUE(`filing_id`,`unit_ref`)
* `facts`

  * `id` PK
  * `filing_id` FK
  * `name`
  * `context_ref`
  * `unit_ref` NULL可
  * `decimals` NULL可
  * `precision` NULL可
  * `value_text`（正規化後の文字列）
  * `value_num` NULL可（数値化できた場合）
  * `is_numeric`（0/1）
  * `sign` NULL可
  * `raw_text` NULL可
  * `source_file`
  * `source_locator` NULL可
  * UNIQUE(`filing_id`,`name`,`context_ref`,`unit_ref`,`value_text`,`source_file`)
* `labels`

  * `id` PK
  * `filing_id` FK NULL可（共有するならNULL運用も可）
  * `concept_name`
  * `role` NULL可
  * `lang` NULL可
  * `label_text`
  * UNIQUE(`concept_name`,`role`,`lang`,`label_text`)

注: SQLiteではJSONはTEXTとして保持し、必要なら別アプリ側でパースする。

---

## 6. 非機能要件

### 6.1 性能

* 1ZIPあたり数千〜数万fact規模を想定
* 目標: 1ZIPの取込が一般的な開発PCで実用時間内（例: 数十秒〜数分）

### 6.2 信頼性・可用性

* 再実行しても重複しない（sha256やUNIQUE制約で担保）
* 失敗時はロールバック

### 6.3 保守性

* 解析（extract）と保存（load）を分離
* ファイル検出、パース、DB層をモジュール化
* 将来のフォルダ監視追加が容易

### 6.4 移植性

* OS非依存（パス・エンコーディングの注意）

### 6.5 セキュリティ

* 外部通信なし
* 入力ZIPはローカルファイル
* ZIPスリップ対策（展開しない/展開する場合はパス検証）

### 6.6 監査性

* 取込ログにZIPハッシュ、件数、警告を残す

---

## 7. 品質属性と検証

### 7.1 テスト要件

* 単体: 数値正規化（符号/カンマ/括弧）、タグ抽出
* 結合: 1ZIPを通しで取込→件数一致、制約違反なし
* 回帰: 同一ZIP再投入で件数が増えない（設定がスキップの場合）

### 7.2 受入テスト（例）

* AT-1: 添付ZIP（代表例）を投入し、factsが0件ではない
* AT-2: SummaryとAttachment双方のsource_fileがfactsに混在
* AT-3: DBにfilingsが1件、facts/contexts/units/labelsが妥当件数
* AT-4: 再投入してもfilingsが増えない（sha256一意）

---

## 8. 変更容易性（拡張）

### 8.1 フォルダ監視

* 監視→キュー→取込ジョブ（同一ETLを再利用）

### 8.2 DB差し替え

* 永続化層をインタフェース化してPostgreSQLへ拡張可能

---

## 9. 付録

### 9.1 入力ファイル想定（参考）

* `XBRLData/Summary/*-ixbrl.htm`
* `XBRLData/Attachment/*-ixbrl.htm`
* `XBRLData/**/**/*-lab.xml`, `*-def.xml`, `*-pre.xml`, `*-cal.xml`, `*.xsd`
* `manifest.xml`, `index.txt`, `qualitative.htm`

### 9.2 エラー分類（例）

* E100: ZIPが読めない
* E200: iXBRLが見つからない
* W300: contextRef未解決
* W301: unitRef未解決
* W400: 値パース不可（raw保持）

### 9.3 追跡性マトリクス（要件→テスト）

| 要件ID  | 要件名         | テストID      |
| ----- | ----------- | ---------- |
| FR-1  | 入力ZIP受付     | AT-1       |
| FR-2  | ZIP内コンテンツ検出 | AT-1, AT-2 |
| FR-3  | facts抽出     | AT-1, AT-2 |
| FR-4  | contexts抽出  | AT-3       |
| FR-5  | units抽出     | AT-3       |
| FR-6  | labels抽出    | AT-3       |
| FR-7  | filingメタ登録  | AT-3, AT-4 |
| FR-8  | SQLite保存    | AT-3, AT-4 |
| FR-9  | ログ・レポート     | AT-1, AT-3 |
| FR-10 | フォルダ監視（将来）  | （将来）       |

### 9.4 関連文書

* docs/architecture.md（アーキテクチャ）
* docs/db_schema.md（DB設計詳細）
* docs/etl_spec.md（抽出・正規化規則）

---

## 10. 承認

* 承認者: （ユーザー）
* 承認日: （未定）
