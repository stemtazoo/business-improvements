import argparse
import sys
from tdnet_xbrl_ingestor.ingest.pipeline import run_pipeline

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="tdnet-xbrl-ingest")
    p.add_argument("--zip", required=True, help="Path to TDnet XBRL ZIP")
    p.add_argument("--db", default="tdnet_xbrl.sqlite", help="SQLite DB file path")
    p.add_argument("--on-duplicate", choices=["skip", "replace"], default="skip",
                   help="Behavior when the same zip (sha256) is ingested again.")
    args = p.parse_args(argv)

    result = run_pipeline(zip_path=args.zip, db_path=args.db, on_duplicate=args.on_duplicate)
    print(f"[OK] filing_id={result.filing_id} facts={result.facts} contexts={result.contexts} units={result.units} labels={result.labels}")
    if result.warnings:
        print(f"[WARN] warnings={len(result.warnings)}")
        for w in result.warnings[:20]:
            print(f"  - {w}")
        if len(result.warnings) > 20:
            print("  ...")
    return 0

if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
