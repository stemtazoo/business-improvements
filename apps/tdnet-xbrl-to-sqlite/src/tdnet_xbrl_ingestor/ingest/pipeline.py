from dataclasses import dataclass
from tdnet_xbrl_ingestor.utils.hashing import sha256_file
from tdnet_xbrl_ingestor.ingest.discover import discover_targets
from tdnet_xbrl_ingestor.extract.ixbrl_facts import extract_facts_from_ixbrl
from tdnet_xbrl_ingestor.extract.labels import extract_labels
from tdnet_xbrl_ingestor.db.connect import connect
from tdnet_xbrl_ingestor.db.schema import ensure_schema
from tdnet_xbrl_ingestor.db.repo import (
    get_or_create_filing, upsert_facts, upsert_labels
)
from tdnet_xbrl_ingestor.extract.xbrl_contexts import extract_contexts_from_ixbrl
from tdnet_xbrl_ingestor.extract.xbrl_units import extract_units_from_ixbrl
from tdnet_xbrl_ingestor.db.repo import upsert_contexts, upsert_units


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
    zhash = sha256_file(zip_path)

    with connect(db_path) as con:
        ensure_schema(con)
        filing_id, did_skip = get_or_create_filing(con, zip_path, zhash, on_duplicate)
        if did_skip:
            return IngestResult(filing_id, 0, 0, 0, 0, ["Skipped duplicate ZIP by sha256."])

        targets = discover_targets(zip_path)
        # NOTE: まずfacts/labelsから。contexts/unitsは次工程で追加する（モジュールは用意しておく）
        all_facts = []
        for ixbrl_path in targets.ixbrl_files:
            all_facts.extend(extract_facts_from_ixbrl(zip_path, ixbrl_path, warnings))

        fact_count = upsert_facts(con, filing_id, all_facts)

        all_labels = []
        for lab_path in targets.label_files:
            all_labels.extend(extract_labels(zip_path, lab_path, warnings))
        label_count = upsert_labels(con, all_labels)

        # contexts/unitsは次のコミットで実装
        return IngestResult(filing_id, fact_count, 0, 0, label_count, warnings)
