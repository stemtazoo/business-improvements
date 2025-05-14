#!/usr/bin/env python3
import os
import json
import subprocess
from datetime import datetime

# 設定ファイルやスクリプトのパスを動的に取得
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(BASE_DIR, 'config', 'watchers.json')

# ----------------------------------
# ヘルパー関数
# ----------------------------------

def load_state(path):
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_state(path, state):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def scan_folder(folder):
    """フォルダ内の相対パスと最終更新時刻を取得"""
    state = {}
    for root, _, files in os.walk(folder):
        for fn in files:
            full_path = os.path.join(root, fn)
            rel_path = os.path.relpath(full_path, folder)
            mtime = os.path.getmtime(full_path)
            state[rel_path] = mtime
    return state


def detect_changes(old, new):
    added   = [f for f in new if f not in old]
    updated = [f for f in new if f in old and new[f] != old[f]]
    return added, updated

# ----------------------------------
# メイン処理
# ----------------------------------
def main():
    # 設定ファイル読み込み
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        watchers = json.load(f)

    for w in watchers:
        old = load_state(w['state_file'])
        new = scan_folder(w['watch_dir'])
        added, updated = detect_changes(old, new)

        if added or updated:
            # 実行スクリプト＋変更リストを引数で渡す
            cmd = w['notification']['command'] + added + updated
            subprocess.run(cmd)

        # 新しい状態を保存
        save_state(w['state_file'], new)


if __name__ == '__main__':
    main()
