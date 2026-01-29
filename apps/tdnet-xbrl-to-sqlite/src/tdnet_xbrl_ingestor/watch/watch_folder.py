from __future__ import annotations

import time
from pathlib import Path
from typing import Iterable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tdnet_xbrl_ingestor.ingest.pipeline import run_pipeline


class ZipIngestHandler(FileSystemEventHandler):
    def __init__(self, watch_dir: Path, db_path: Path, *, on_duplicate: str = "skip"):
        self.watch_dir = watch_dir
        self.db_path = db_path
        self.on_duplicate = on_duplicate

    def on_created(self, event):
        if event.is_directory:
            return

        path = Path(event.src_path)
        if path.suffix.lower() != ".zip":
            return

        # wait until file is fully written
        time.sleep(1.0)

        try:
            result = run_pipeline(
                zip_path=str(path),
                db_path=str(self.db_path),
                on_duplicate=self.on_duplicate,
            )
            print(
                f"[WATCH] ingested {path.name}: filing_id={result.filing_id} facts={result.facts} contexts={result.contexts} units={result.units}"
            )
        except Exception as e:
            print(f"[WATCH][ERROR] failed to ingest {path}: {e}")


def watch_folder(
    watch_dir: str | Path,
    *,
    db_path: str | Path,
    on_duplicate: str = "skip",
) -> None:
    watch_dir = Path(watch_dir).resolve()
    db_path = Path(db_path).resolve()

    handler = ZipIngestHandler(watch_dir, db_path, on_duplicate=on_duplicate)
    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)

    observer.start()
    print(f"[WATCH] watching {watch_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[WATCH] stopping...")
        observer.stop()
    observer.join()
