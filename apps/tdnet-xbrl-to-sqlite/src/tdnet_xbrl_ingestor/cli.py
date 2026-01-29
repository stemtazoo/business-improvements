import argparse
import sys
from tdnet_xbrl_ingestor.ingest.pipeline import run_pipeline

from tdnet_xbrl_ingestor.db.connect import connect
from tdnet_xbrl_ingestor.db.schema import ensure_schema
from tdnet_xbrl_ingestor.db.repo import get_db_stats

def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="tdnet-xbrl-ingest")
    p.add_argument("--zip", help="Path to TDnet ZIP file.")
    p.add_argument("--db", default="tdnet_xbrl.sqlite", help="SQLite DB file path")
    p.add_argument("--on-duplicate", choices=["skip", "replace"], default="skip",
                   help="Behavior when the same zip (sha256) is ingested again.")
    p.add_argument("--stats", action="store_true", help="Show DB stats and exit (no ingestion).")
    p.add_argument("--by-filing", action="store_true", help="Show per-filing counts in --stats output.")
    p.add_argument("--limit", type=int, default=20, help="Limit rows for --stats --by-filing (default: 20).")
    args = p.parse_args(argv)

    if args.stats:
        from tdnet_xbrl_ingestor.db.repo import get_db_stats, get_latest_filing
        from tdnet_xbrl_ingestor.db.repo import get_db_stats, get_latest_filing, get_stats_by_filing
        with connect(args.db) as con:
            ensure_schema(con)
            s = get_db_stats(con)
            latest = get_latest_filing(con)

        base = f"[STATS] filings={s.filings} facts={s.facts} contexts={s.contexts} units={s.units} labels={s.labels}"

        if latest is None:
            print(base + " latest=(none)")
        else:
            print(
                base
                + f" latest_filing_id={latest.id}"
                + f" zip_name={latest.zip_name}"
                + f" ingested_at={latest.ingested_at}"
            )

        if args.by_filing:
            rows = get_stats_by_filing(con, limit=args.limit)
            print("[STATS] by_filing:")
            for r in rows:
                print(
                    f"  id={r.filing_id} "
                    f"facts={r.facts} contexts={r.contexts} units={r.units} "
                    f"zip_name={r.zip_name} "
                    f"ingested_at={r.ingested_at}"
                )
        
        return 0

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
