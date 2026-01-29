import argparse
from pathlib import Path

import yaml
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeoutError

TDNET_URL = "https://www.release.tdnet.info/index.html"

KESSAN_KEYWORDS = [
    "決算短信",
    "四半期決算短信",
    "通期決算短信",
]


# -----------------------------
# 設定読み込み
# -----------------------------
def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


# -----------------------------
# メイン処理
# -----------------------------
def download_latest_kessan_tanshin_xbrl_for_tickers(
    tickers: list[str],
    date_from: str,
    out_dir: str,
    headless: bool = False,
    wait_ms: int = 800,
):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    results: dict[str, Path | None] = {}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        page.goto(TDNET_URL, wait_until="domcontentloaded")

        # 検索フォームの iframe
        frame = page.locator("iframe").content_frame
        if frame is None:
            raise RuntimeError("トップの iframe が取得できませんでした")

        frame.locator('select[name="t0"]').select_option(date_from)

        for ticker in tickers:
            print(f"\n=== processing ticker {ticker} ===")

            try:
                # 入力 → 検索
                frame.locator("#freewordtxt").fill(str(ticker))
                frame.locator("#searchbtn").click()

                # 結果一覧 iframe
                mainlist = frame.locator('iframe[name="mainlist"]').content_frame
                if mainlist is None:
                    raise RuntimeError("mainlist iframe が取得できませんでした")

                # ticker 行が出るまで待つ
                rows = mainlist.locator("tr", has_text=str(ticker))
                rows.first.wait_for(timeout=15000)

                # 決算短信（表記ゆれ対応）でフィルタ
                target_row = None
                for kw in KESSAN_KEYWORDS:
                    cand = rows.filter(has_text=kw)
                    if cand.count() > 0:
                        target_row = cand.first  # TDnetは新しい順
                        break

                if target_row is None:
                    print("✖ 決算短信が見つかりません（スキップ）")
                    results[ticker] = None
                    continue

                # XBRL クリック
                xbrl = target_row.get_by_role("link", name="XBRL").first
                xbrl.wait_for(state="visible", timeout=15000)

                with page.expect_download(timeout=20000) as dl_info:
                    xbrl.click()
                download = dl_info.value

                save_path = out / f"{ticker}_{download.suggested_filename}"
                download.save_as(save_path)

                results[ticker] = save_path
                print(f"✔ downloaded: {save_path.name}")

                page.wait_for_timeout(wait_ms)

            except PWTimeoutError:
                print("✖ timeout (決算短信/XBRLが見つからない)")
                results[ticker] = None
            except Exception as e:
                print(f"✖ error: {e}")
                results[ticker] = None

        context.close()
        browser.close()

    return results


# -----------------------------
# CLI
# -----------------------------
def parse_args():
    parser = argparse.ArgumentParser(description="TDnet 決算短信 XBRL downloader")
    parser.add_argument(
        "--config",
        required=True,
        help="config.yaml のパス",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    config = load_config(args.config)

    tdnet_cfg = config["tdnet"]
    pw_cfg = config.get("playwright", {})

    result = download_latest_kessan_tanshin_xbrl_for_tickers(
        tickers=tdnet_cfg["tickers"],
        date_from=tdnet_cfg["date_from"],
        out_dir=tdnet_cfg["out_dir"],
        headless=pw_cfg.get("headless", False),
        wait_ms=pw_cfg.get("wait_ms", 800),
    )

    print("\n=== summary ===")
    for ticker, path in result.items():
        print(ticker, "->", path)
