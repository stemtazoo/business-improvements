# Business Improvements

Pythonを用いた業務改善ツール・アプリケーション<br>

[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

## 📌 概要

本リポジトリは、Python を活用した業務改善のコードやアプリケーションを管理するためのものです。
業務で発生する様々な課題を解決するために作成したスクリプトやアプリケーション、関連ドキュメントを一元管理し、再利用性や保守性を高めることを目的としています。

## 📂 リポジトリ構造

| ディレクトリ       | 説明                                                                 |
|--------------------|----------------------------------------------------------------------|
| `apps/`            | 個別アプリケーション（各アプリは独立した環境を想定）                 |
| `libs/`            | 共通で使用するユーティリティ関数/クラス                              |
| `docs/`            | 技術ドキュメント・改善事例の記録                                     |
| `notebooks/`       | 実験用Jupyterノートブック                                            |

### ✅ 追加済みアプリケーション一覧

- `apps/excel-sheet-splitting/` : Excelファイル内の各シートを個別ファイルに分割保存するGUIアプリ（[Flet](https://flet.dev)使用）

## ✨ 目的

- 業務プロセスの効率化
- データ駆動の意思決定支援
- 繰り返し作業の自動化
- 技術的ナレッジの蓄積と共有

## 🚀 セットアップ

1. リポジトリをクローン
   ```bash
   git clone https://github.com/stemtazoo/business-improvements.git
   ```
2. 依存パッケージのインストール
   リポジトリ全体で使用する依存パッケージをインストールします。
   ```bash
   cd business-improvements
   pip install -r requirements.txt
   ```
3. アプリ単位のパッケージインストール（必要に応じて）
   もし `apps/xxx/requirements.txt` のようにアプリごとに依存関係がある場合は、それぞれのディレクトリでインストールしてください。
   ```bash
   cd apps/excel-sheet-splitting
   pip install -r requirements.txt
   ```
4. 各アプリケーションの`README.md`を確認

## 📚 使い方

### ドキュメント (`docs/`)
プロジェクト全体の詳細説明や、使用しているユーティリティなどをまとめています。今後、機能追加や利用例に合わせて更新予定です。

### アプリ (`apps/`)
実際の業務改善アプリケーションを配置する場所です。すでに `excel-sheet-splitting` アプリが追加されています。

### ノートブック (`notebooks/`)
データ探索や PoC (Proof of Concept) を行うための Jupyter Notebook を配置しています。開発の初期段階やアイデア検証などに活用してください。

## 📄 License

本リポジトリは[MITライセンス](LICENSE)の下で公開されています。

## 🧑‍💻 作者

stemtazoo（Python・業務改善エンジニア）

---

"ANYTHING IS POSSIBLE" 🚀