# フォルダ監視アプリ (Folder Watcher)

このプロジェクトは、指定した複数のフォルダを定期的に走査し、新規ファイルや更新ファイルを検知した際に任意のスクリプトやコマンドを実行するシンプルなフォルダ監視ツールです。

---

## 📂 ディレクトリ構成

```
apps/
└── folder-watcher/
    ├── .gitignore
    ├── README.md
    ├── requirements.txt
    ├── config/
    │   └── watchers.json
    ├── src/
    │   └── watch_folder.py
    ├── scripts/
    │   ├── process_backup.sh
    │   └── process_logs.sh
    ├── state/
    │   ├── backups_state.json
    │   └── logs_state.json
    └── logs/
        └── watcher.log
```

* **config/watchers.json**: 監視対象フォルダと通知（実行）設定を記述
* **src/watch\_folder.py**: メインの監視スクリプト
* **scripts/**: 検知時に実行される外部スクリプトを配置
* **state/**: 各フォルダの最終走査結果（JSON形式）を保存
* **logs/**: 実行ログを出力

---

## ⚙️ 前提条件

* Python 3.6 以上
* (必要に応じて) `requests` ライブラリなどのインストール

---

## 🛠️ セットアップ

1. リポジトリをクローン／ダウンロード

   ```bash
   git clone https://github.com/stemtazoo/business-improvements.git
   cd business-improvements/apps/folder-watcher
   ```

2. 仮想環境を作成・有効化 (任意)

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # Windows: .\.venv\Scripts\activate
   ```

3. 依存ライブラリをインストール

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ 設定 (config/watchers.json)

```json
[
  {
    "name": "backups",
    "watch_dir": "backups",
    "state_file": "state/backups_state.json",
    "notification": {
      "type": "run",
      "command": ["scripts/process_backup.bat"]
    }
  },
  {
    "name": "logs",
    "watch_dir": "logs",
    "state_file": "state/logs_state.json",
    "notification": {
      "type": "run",
      "command": ["scripts/process_logs.bat"]
    }
  },
  {
    "name": "reports",
    "watch_dir": "reports",
    "state_file": "state/reports_state.json",
    "notification": {
      "type": "run",
      "command": ["python", "scripts/process_reports.py"]
    }
  }
]

```

* `name`: 任意の識別子
* `watch_dir`: 監視対象フォルダのパス
* `state_file`: 前回走査結果を保存する JSON ファイルのパス
* `notification.type`: `run` / `email` / `webhook` など将来的に拡張可能
* `notification.command`: 検知時に実行するコマンド（リスト形式）

---

## 🚀 実行方法

```bash
cd apps/folder-watcher/src
python watch_folder.py
```

### 定期実行設定例

* **Linux/macOS (cron)**

  ```cron
  # 毎時 5 分後に実行
  5 * * * * /usr/bin/python3 /path/to/apps/folder-watcher/src/watch_folder.py >> /path/to/apps/folder-watcher/logs/watcher.log 2>&1
  ```

* **Windows (タスクスケジューラ)**

  1. タスク スケジューラを起動
  2. 新しいタスクを作成し、トリガーを「毎日 → 1時間ごとに繰り返す」に設定
  3. 操作で `python C:\path\to\apps\folder-watcher\src\watch_folder.py` を指定
  4. 標準出力／エラーを `logs\watcher.log` にリダイレクト（必要に応じて）

---

## 📝 ログとトラブルシュート

* `logs/watcher.log` に実行結果やエラーを出力します。
* state ファイルが壊れた場合、削除すると初回走査として扱われます。

---

## 🤝 貢献

プルリクエストや Issue 大歓迎です！

---

## 📝 ライセンス

MIT License
