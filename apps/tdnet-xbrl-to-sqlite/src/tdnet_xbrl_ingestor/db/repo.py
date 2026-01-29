from __future__ import annotations

import os
import sqlite3
from dataclasses import asdict, dataclass
from typing import Iterable, Tuple

from tdnet_xbrl_ingestor.models.entities import Fact, Label
from tdnet_xbrl_ingestor.models.entities import Fact, Label, Context, Unit

def get_or_create_filing(
    con: sqlite3.Connection,
    zip_path: str,
    zip_sha256: str,
    on_duplicate: str = "skip",
) -> Tuple[int, bool]:
    """
    Returns (filing_id, did_skip).

    - If sha256 already exists:
        - skip: returns existing id and did_skip=True
        - replace: REUSE the same filing_id, delete child rows (facts/contexts/units),
                   update filing metadata, and did_skip=False
    - If sha256 does not exist: create new filing, did_skip=False
    """
    row = con.execute(
        "SELECT id FROM filings WHERE zip_sha256 = ?",
        (zip_sha256,),
    ).fetchone()

    zip_name = os.path.basename(zip_path)

    if row is not None:
        filing_id = int(row["id"])

        if on_duplicate == "skip":
            return filing_id, True

        if on_duplicate != "replace":
            raise ValueError(f"Unknown on_duplicate: {on_duplicate!r}")

        # ✅ replace: keep the same filing_id and clear dependent data
        _clear_filing_children(con, filing_id)

        # update metadata (optional, but useful)
        con.execute(
            """
            UPDATE filings
            SET zip_name = ?,
                ingested_at = datetime('now')
            WHERE id = ?
            """,
            (zip_name, filing_id),
        )

        return filing_id, False

    # new filing
    cur = con.execute(
        """
        INSERT INTO filings (zip_name, zip_sha256)
        VALUES (?, ?)
        """,
        (zip_name, zip_sha256),
    )
    return int(cur.lastrowid), False


def _clear_filing_children(con: sqlite3.Connection, filing_id: int) -> None:
    """
    Delete rows that belong to a filing, without deleting the filing itself.
    This keeps filing_id stable across re-ingests.
    """
    # Delete in child->parent order (safe even with FK)
    con.execute("DELETE FROM facts WHERE filing_id = ?", (filing_id,))
    # If you have contexts/units tables, clear them too:
    try:
        con.execute("DELETE FROM contexts WHERE filing_id = ?", (filing_id,))
    except sqlite3.OperationalError:
        pass
    try:
        con.execute("DELETE FROM units WHERE filing_id = ?", (filing_id,))
    except sqlite3.OperationalError:
        pass

def upsert_facts(
    con: sqlite3.Connection,
    filing_id: int,
    facts: Iterable[Fact],
    *,
    chunk_size: int = 2000,
) -> int:
    """
    Insert facts with UPSERT. Returns number of rows affected (insert+update).

    Notes:
    - SQLite's cursor.rowcount with executemany is not always reliable across drivers.
      We compute affected rows using total_changes delta.
    """
    facts_list = list(facts)
    if not facts_list:
        return 0

    sql = """
    INSERT INTO facts (
      filing_id, name, context_ref, unit_ref,
      decimals, precision, scale, sign,
      value_text, value_num, is_numeric,
      raw_text, source_file, source_locator,
      created_at, updated_at
    )
    VALUES (
      :filing_id, :name, :context_ref, :unit_ref,
      :decimals, :precision, :scale, :sign,
      :value_text, :value_num, :is_numeric,
      :raw_text, :source_file, :source_locator,
      datetime('now'), datetime('now')
    )
    ON CONFLICT(filing_id, name, context_ref, unit_ref, value_text, source_file)
    DO UPDATE SET
      decimals=excluded.decimals,
      precision=excluded.precision,
      scale=excluded.scale,
      sign=excluded.sign,
      value_num=excluded.value_num,
      is_numeric=excluded.is_numeric,
      raw_text=excluded.raw_text,
      source_locator=excluded.source_locator,
      updated_at=datetime('now')
    ;
    """

    def to_params(f: Fact) -> dict:
        # Decimal -> float for SQLite REAL (analysis app can re-parse from value_text if needed)
        value_num = float(f.value_num) if f.value_num is not None else None
        return {
            "filing_id": filing_id,
            "name": f.name,
            "context_ref": f.context_ref,
            "unit_ref": f.unit_ref,
            "decimals": f.decimals,
            "precision": f.precision,
            "scale": f.scale,
            "sign": f.sign,
            "value_text": f.value_text,
            "value_num": value_num,
            "is_numeric": 1 if f.is_numeric else 0,
            "raw_text": f.raw_text,
            "source_file": f.source_file,
            "source_locator": f.source_locator,
        }

    before = con.total_changes

    params = [to_params(f) for f in facts_list]
    for i in range(0, len(params), chunk_size):
        con.executemany(sql, params[i : i + chunk_size])

    after = con.total_changes
    return after - before

def upsert_labels(
    con: sqlite3.Connection,
    labels: Iterable[Label],
    *,
    chunk_size: int = 2000,
) -> int:
    """
    Insert labels with UPSERT. Returns number of rows affected (insert+update).
    """
    labels_list = list(labels)
    if not labels_list:
        return 0

    sql = """
    INSERT INTO labels (
      concept_name, role, lang, label_text,
      created_at, updated_at
    )
    VALUES (
      :concept_name, :role, :lang, :label_text,
      datetime('now'), datetime('now')
    )
    ON CONFLICT(concept_name, role, lang, label_text)
    DO UPDATE SET
      updated_at=datetime('now')
    ;
    """

    def to_params(l: Label) -> dict:
        return {
            "concept_name": l.concept_name,
            "role": l.role,
            "lang": l.lang,
            "label_text": l.label_text,
        }

    before = con.total_changes
    params = [to_params(l) for l in labels_list]

    for i in range(0, len(params), chunk_size):
        con.executemany(sql, params[i : i + chunk_size])

    after = con.total_changes
    return after - before

def upsert_contexts(con: sqlite3.Connection, filing_id: int, contexts: Iterable[Context], *, chunk_size: int = 2000) -> int:
    ctx_list = list(contexts)
    if not ctx_list:
        return 0

    sql = """
    INSERT INTO contexts (
      filing_id, context_ref, entity_scheme, entity_identifier,
      period_type, instant_date, start_date, end_date, dimensions_json,
      created_at, updated_at
    )
    VALUES (
      :filing_id, :context_ref, :entity_scheme, :entity_identifier,
      :period_type, :instant_date, :start_date, :end_date, :dimensions_json,
      datetime('now'), datetime('now')
    )
    ON CONFLICT(filing_id, context_ref)
    DO UPDATE SET
      entity_scheme=excluded.entity_scheme,
      entity_identifier=excluded.entity_identifier,
      period_type=excluded.period_type,
      instant_date=excluded.instant_date,
      start_date=excluded.start_date,
      end_date=excluded.end_date,
      dimensions_json=excluded.dimensions_json,
      updated_at=datetime('now')
    ;
    """

    before = con.total_changes
    params = [
        {
            "filing_id": filing_id,
            "context_ref": c.context_ref,
            "entity_scheme": c.entity_scheme,
            "entity_identifier": c.entity_identifier,
            "period_type": c.period_type,
            "instant_date": c.instant_date,
            "start_date": c.start_date,
            "end_date": c.end_date,
            "dimensions_json": c.dimensions_json,
        }
        for c in ctx_list
    ]
    for i in range(0, len(params), chunk_size):
        con.executemany(sql, params[i : i + chunk_size])
    return con.total_changes - before

def upsert_units(con: sqlite3.Connection, filing_id: int, units: Iterable[Unit], *, chunk_size: int = 2000) -> int:
    unit_list = list(units)
    if not unit_list:
        return 0

    sql = """
    INSERT INTO units (
      filing_id, unit_ref, measures_json,
      created_at, updated_at
    )
    VALUES (
      :filing_id, :unit_ref, :measures_json,
      datetime('now'), datetime('now')
    )
    ON CONFLICT(filing_id, unit_ref)
    DO UPDATE SET
      measures_json=excluded.measures_json,
      updated_at=datetime('now')
    ;
    """

    before = con.total_changes
    params = [
        {
            "filing_id": filing_id,
            "unit_ref": u.unit_ref,
            "measures_json": u.measures_json,
        }
        for u in unit_list
    ]
    for i in range(0, len(params), chunk_size):
        con.executemany(sql, params[i : i + chunk_size])
    return con.total_changes - before

@dataclass(frozen=True, slots=True)
class DbStats:
    filings: int
    facts: int
    contexts: int
    units: int
    labels: int


def get_db_stats(con: sqlite3.Connection) -> DbStats:
    def count(table: str) -> int:
        row = con.execute(f"SELECT COUNT(*) AS c FROM {table}").fetchone()
        return int(row["c"]) if row is not None else 0

    return DbStats(
        filings=count("filings"),
        facts=count("facts"),
        contexts=count("contexts"),
        units=count("units"),
        labels=count("labels"),
    )

@dataclass(frozen=True, slots=True)
class LatestFiling:
    id: int
    zip_name: str
    zip_sha256: str
    ingested_at: str


def get_latest_filing(con: sqlite3.Connection) -> LatestFiling | None:
    row = con.execute(
        """
        SELECT id, zip_name, zip_sha256, ingested_at
        FROM filings
        ORDER BY datetime(ingested_at) DESC, id DESC
        LIMIT 1
        """
    ).fetchone()

    if row is None:
        return None

    return LatestFiling(
        id=int(row["id"]),
        zip_name=str(row["zip_name"]),
        zip_sha256=str(row["zip_sha256"]),
        ingested_at=str(row["ingested_at"]),
    )


@dataclass(frozen=True, slots=True)
class FilingStats:
    filing_id: int
    zip_name: str
    ingested_at: str
    facts: int
    contexts: int
    units: int


def get_stats_by_filing(con: sqlite3.Connection, *, limit: int = 50) -> list[FilingStats]:
    """
    Return per-filing counts for facts/contexts/units.
    labels are global (no filing_id), so excluded here.
    """
    rows = con.execute(
        """
        SELECT
          f.id AS filing_id,
          f.zip_name AS zip_name,
          f.ingested_at AS ingested_at,
          (SELECT COUNT(*) FROM facts    WHERE filing_id = f.id) AS facts,
          (SELECT COUNT(*) FROM contexts WHERE filing_id = f.id) AS contexts,
          (SELECT COUNT(*) FROM units    WHERE filing_id = f.id) AS units
        FROM filings f
        ORDER BY datetime(f.ingested_at) DESC, f.id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    out: list[FilingStats] = []
    for r in rows:
        out.append(
            FilingStats(
                filing_id=int(r["filing_id"]),
                zip_name=str(r["zip_name"]),
                ingested_at=str(r["ingested_at"]),
                facts=int(r["facts"]),
                contexts=int(r["contexts"]),
                units=int(r["units"]),
            )
        )
    return out
