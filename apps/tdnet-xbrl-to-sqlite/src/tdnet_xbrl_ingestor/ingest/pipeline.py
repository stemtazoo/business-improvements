from __future__ import annotations

from dataclasses import dataclass

from tdnet_xbrl_ingestor.utils.hashing import sha256_file
from tdnet_xbrl_ingestor.ingest.discover import discover_targets

from tdnet_xbrl_ingestor.extract.ixbrl_facts import extract_facts_from_ixbrl
from tdnet_xbrl_ingestor.extract.labels import extract_labels
from tdnet_xbrl_ingestor.extract.xbrl_contexts import extract_contexts_from_ixbrl
from tdnet_xbrl_ingestor.extract.xbrl_units import extract_units_from_ixbrl

from tdnet_xbrl_ingestor.db.connect import connect
from tdnet_xbrl_ingestor.db.schema import ensure_schema
from tdnet_xbrl_ingestor.db.repo import (
    get_or_create_filing,
    upsert_facts,
    upsert_labels,
    upsert_contexts,
    upsert_units,
)


@dataclass
class IngestResult:
    filing_id: int
    facts: int
    contexts: int
    units: int
    labels: int
    warnings: list[str]


def run_pipeline(zip_path: str, db_path: str, on_duplicate: str = "skip") -> IngestResult:
    warnings: list[str] = []

    zip_hash = sha256_file(zip_path)

    with connect(db_path) as con:
        ensure_schema(con)

        filing_id, skipped = get_or_create_filing(
            con,
            zip_path=zip_path,
            zip_sha256=zip_hash,
            on_duplicate=on_duplicate,
        )

        if skipped:
            return IngestResult(
                filing_id=filing_id,
                facts=0,
                contexts=0,
                units=0,
                labels=0,
                warnings=["Skipped duplicate ZIP"],
            )

        targets = discover_targets(zip_path)

        # ✅ contexts / units first
        all_contexts = []
        all_units = []
        for ixbrl_path in targets.ixbrl_files:
            all_contexts.extend(extract_contexts_from_ixbrl(zip_path, ixbrl_path, warnings))
            all_units.extend(extract_units_from_ixbrl(zip_path, ixbrl_path, warnings))

        ctx_count = upsert_contexts(con, filing_id, all_contexts)
        unit_count = upsert_units(con, filing_id, all_units)

        if ctx_count == 0:
            warnings.append("[context] No contexts extracted from any iXBRL file.")
        if unit_count == 0:
            warnings.append("[unit] No units extracted from any iXBRL file.")

        # ✅ facts
        all_facts = []
        for ixbrl_path in targets.ixbrl_files:
            all_facts.extend(extract_facts_from_ixbrl(zip_path, ixbrl_path, warnings))
        fact_count = upsert_facts(con, filing_id, all_facts)

        # ✅ labels
        all_labels = []
        for lab_path in targets.label_files:
            all_labels.extend(extract_labels(zip_path, lab_path, warnings))
        label_count = upsert_labels(con, all_labels)

        return IngestResult(
            filing_id=filing_id,
            facts=fact_count,
            contexts=ctx_count,
            units=unit_count,
            labels=label_count,
            warnings=warnings,
        )
