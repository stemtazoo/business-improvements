# 画像リサイズアプリ

このアプリケーションは、指定したフォルダ内の画像を一括でリサイズし、別のフォルダに保存できる Python GUI アプリです。GUI フレームワークには [Flet](https://flet.dev) を使用しています。

---

## ✅ 主な機能

- 入力フォルダ内の画像（.jpg, .png, .bmp, .gifなど）を一括リサイズ
- リサイズ方法は以下から選択：
  - パーセント指定（例：50%）
  - 幅と高さのサイズ指定（例：640 x 480）
- リサイズ後の画像は出力フォルダに保存
- GUI 上で入力フォルダ／出力フォルダを簡単に選択可能
- 元画像と同じファイル名で保存（上書き回避可能）

---

## 🖥️ アプリの起動方法

### 1. 依存パッケージのインストール

```bash
pip install flet Pillow
```

### 2. アプリを起動

```bash
flet run src/main.py
```

Flet により GUI が起動します。

---

## 📁 ディレクトリ構成

```plaintext
resize-image/
├── src/
│   ├── assets/               # アイコンやスプラッシュ画像
│   ├── storage/              # 保存用ディレクトリ
│   │   ├── data/
│   │   └── temp/
│   └── main.py              # アプリ本体
├── .gitignore
├── pyproject.toml           # Poetry や依存管理用
└── README.md                # ← このファイル
```

---

## 📌 注意事項

- 入力フォルダには画像ファイルのみを入れてください
- 出力フォルダに同名ファイルがある場合は上書きされます
- 対応画像形式：`.jpg`, `.jpeg`, `.png`, `.bmp`, `.gif`
- Python 3.9 以上推奨

---

## ✨ 今後の拡張案

- リサイズ進捗のプログレスバー表示
- 出力形式（PNG, JPEGなど）の変換機能
- ファイル名変更ルールの設定機能
- サブフォルダの再帰処理対応
- 参考：[Getting Started Guide](https://flet.dev/docs/getting-started/).

---

## 🧑‍💻 作者

stemtazoo（Python・業務改善エンジニア）

---

"ANYTHING IS POSSIBLE" 🚀

