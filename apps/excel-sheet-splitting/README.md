# Excel Sheet 分割アプリ

このアプリケーションは、1つの Excel ファイルに含まれる各シートを、別々のファイルとして保存する Python アプリです。GUI フレームワークとして [Flet](https://flet.dev) を使用しています。

---

## ✅ 主な機能

- Excel ファイル（.xlsx, .xlsm）の読み込み
- 各シートを個別のファイルに分割して保存
- GUI 上でのファイル選択／フォルダ選択
- シート名をファイル名に使用（必要に応じてファイル名を安全に変換）
- 保存先は指定可能（未指定時は元ファイルと同じフォルダ）

---

## 🖥️ アプリの起動方法

### 1. 依存パッケージのインストール

```bash
pip install -r requirements.txt
```

### 2. アプリを起動

```bash
flet run src/main.py
```

Flet により、ブラウザで GUI が起動します。

---

## 📁 ディレクトリ構成

```plaintext
apps/
└── excel-sheet-splitting/
    ├── README.md              # ← このファイル
    ├── requirements.txt       # 必要なパッケージ一覧
    ├── src/
    │   └── main.py            # アプリ本体
    ├── tests/
    │   └── test_main.py       # テストコード
    └── config/
        └── app1_config.yaml   # シート分割用の設定ファイル
```

---

## ⚙️ 設定ファイル（app1_config.yaml）

```yaml
sheet_filename_format: "{sheet_name}.xlsx"
```

ファイル名の命名パターンを変更したい場合、ここを修正してください。使えない文字は自動で置換されます。

---

## 🧪 テスト実行方法

以下のコマンドでテストできます。

```bash
pytest tests/test_main.py
```

---

## 📝 補足

- 対応ファイル形式: `.xlsx`, `.xlsm`, `.xltx`, `.xltm`
- ファイル名に使えない文字（`:`, `*`, `?`など）は `_` に変換されます
- Python 3.10 以上推奨

---

## ✨ 今後の拡張案（アイデア）

- `.csv` や `.tsv` 形式への出力対応
- プログレスバーやログ出力機能
- 複数ファイル同時処理
- 保存済みファイルをZIPにまとめる

---

## 🧑‍💻 作者

stemtazoo（Python・業務改善エンジニア）

---

"ANYTHING IS POSSIBLE" 🚀
