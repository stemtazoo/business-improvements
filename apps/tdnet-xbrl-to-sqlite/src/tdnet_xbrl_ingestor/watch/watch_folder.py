from __future__ import annotations

import shutil
import time
from dataclasses import dataclass
from pathlib import Path

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from tdnet_xbrl_ingestor.ingest.pipeline import run_pipeline


def _wait_until_stable(path: Path, *, timeout_sec: float = 60.0, interval_sec: float = 0.5) -> bool:
    """Wait until file size stops changing (Windows copy/download completion guard)."""
    start = time.time()
    last_size = -1

    while time.time() - start < timeout_sec:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            time.sleep(interval_sec)
            continue

        if size > 0 and size == last_size:
            return True

        last_size = size
        time.sleep(interval_sec)

    return False


def _unique_dest(dest: Path) -> Path:
    """Avoid overwriting existing files by appending a timestamp."""
    if not dest.exists():
        return dest

    stem = dest.stem
    suf = dest.suffix
    ts = time.strftime("%Y%m%d-%H%M%S")

    i = 1
    while True:
        cand = dest.with_name(f"{stem}.{ts}.{i}{suf}")
        if not cand.exists():
            return cand
        i += 1


@dataclass(frozen=True, slots=True)
class MovePolicy:
    processed_dir: Path | None
    failed_dir: Path | None

    def ensure_dirs(self) -> None:
        if self.processed_dir is not None:
            self.processed_dir.mkdir(parents=True, exist_ok=True)
        if self.failed_dir is not None:
            self.failed_dir.mkdir(parents=True, exist_ok=True)


class ZipIngestHandler(FileSystemEventHandler):
    def __init__(
        self,
        watch_dir: Path,
        db_path: Path,
        *,
        on_duplicate: str = "skip",
        move_policy: MovePolicy | None = None,
        stable_timeout_sec: float = 60.0,
    ):
        self.watch_dir = watch_dir
        self.db_path = db_path
        self.on_duplicate = on_duplicate
        self.move_policy = move_policy or MovePolicy(None, None)
        self.stable_timeout_sec = stable_timeout_sec
        self.move_policy.ensure_dirs()

    # Some apps write via temp file then rename; handle both.
    def on_created(self, event):
        self._maybe_ingest(Path(event.src_path), is_dir=event.is_directory)

    def on_moved(self, event):
        # event.dest_path exists after rename
        self._maybe_ingest(Path(event.dest_path), is_dir=event.is_directory)

    def _maybe_ingest(self, path: Path, *, is_dir: bool) -> None:
        if is_dir:
            return

        if path.suffix.lower() != ".zip":
            return

        # Ignore files already in processed/failed dirs (if those are inside watch_dir)
        try:
            rel = path.resolve().relative_to(self.watch_dir)
            if rel.parts and rel.parts[0].lower() in {"processed", "failed"}:
                return
        except Exception:
            pass

        # Wait for copy/download completion
        if not _wait_until_stable(path, timeout_sec=self.stable_timeout_sec):
            print(f"[WATCH][WARN] file not stable (timeout): {path}")
            return

        try:
            result = run_pipeline(
                zip_path=str(path),
                db_path=str(self.db_path),
                on_duplicate=self.on_duplicate,
            )
            print(
                f"[WATCH] ingested {path.name}: filing_id={result.filing_id} facts={result.facts} contexts={result.contexts} units={result.units}"
            )

            # Move to processed
            if self.move_policy.processed_dir is not None:
                dest = _unique_dest(self.move_policy.processed_dir / path.name)
                shutil.move(str(path), str(dest))
                print(f"[WATCH] moved to processed: {dest.name}")

        except Exception as e:
            print(f"[WATCH][ERROR] failed to ingest {path}: {e}")

            # Move to failed
            if self.move_policy.failed_dir is not None:
                try:
                    dest = _unique_dest(self.move_policy.failed_dir / path.name)
                    shutil.move(str(path), str(dest))
                    print(f"[WATCH] moved to failed: {dest.name}")
                except Exception as move_err:
                    print(f"[WATCH][ERROR] failed to move into failed/: {move_err}")


def watch_folder(
    watch_dir: str | Path,
    *,
    db_path: str | Path,
    on_duplicate: str = "skip",
    processed_dir: str | Path | None = "processed",
    failed_dir: str | Path | None = "failed",
    stable_timeout_sec: float = 60.0,
) -> None:
    """Watch a folder for new ZIPs and ingest them.

    By default, successfully ingested ZIPs are moved into `processed/` and failures into `failed/`.

    - If `processed_dir`/`failed_dir` are relative paths, they are created under `watch_dir`.
    - Pass None to disable moving.
    """

    watch_dir = Path(watch_dir).resolve()
    db_path = Path(db_path).resolve()

    def _resolve_under_watch(p: str | Path | None) -> Path | None:
        if p is None:
            return None
        pp = Path(p)
        return (watch_dir / pp).resolve() if not pp.is_absolute() else pp.resolve()

    move_policy = MovePolicy(
        processed_dir=_resolve_under_watch(processed_dir),
        failed_dir=_resolve_under_watch(failed_dir),
    )

    handler = ZipIngestHandler(
        watch_dir,
        db_path,
        on_duplicate=on_duplicate,
        move_policy=move_policy,
        stable_timeout_sec=stable_timeout_sec,
    )

    observer = Observer()
    observer.schedule(handler, str(watch_dir), recursive=False)

    observer.start()
    print(f"[WATCH] watching {watch_dir}")
    if move_policy.processed_dir is not None:
        print(f"[WATCH] processed_dir={move_policy.processed_dir}")
    if move_policy.failed_dir is not None:
        print(f"[WATCH] failed_dir={move_policy.failed_dir}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("[WATCH] stopping...")
        observer.stop()
    observer.join()
