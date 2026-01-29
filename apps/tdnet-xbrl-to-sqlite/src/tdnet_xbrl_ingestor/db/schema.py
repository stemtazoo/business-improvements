from __future__ import annotations

import sqlite3


def ensure_schema(con: sqlite3.Connection) -> None:
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS filings (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          zip_name TEXT NOT NULL,
          zip_sha256 TEXT NOT NULL UNIQUE,
          ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
          company_code TEXT,
          period_start TEXT,
          period_end TEXT,
          doc_type TEXT
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS contexts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filing_id INTEGER NOT NULL,
          context_ref TEXT NOT NULL,
          entity_scheme TEXT,
          entity_identifier TEXT,
          period_type TEXT NOT NULL,
          instant_date TEXT,
          start_date TEXT,
          end_date TEXT,
          dimensions_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
          UNIQUE(filing_id, context_ref)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS units (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filing_id INTEGER NOT NULL,
          unit_ref TEXT NOT NULL,
          measures_json TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
          UNIQUE(filing_id, unit_ref)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS facts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          filing_id INTEGER NOT NULL,
          name TEXT NOT NULL,
          context_ref TEXT,
          unit_ref TEXT,
          decimals TEXT,
          precision TEXT,
          scale TEXT,
          sign TEXT,
          value_text TEXT NOT NULL,
          value_num REAL,
          is_numeric INTEGER NOT NULL,
          raw_text TEXT,
          source_file TEXT NOT NULL,
          source_locator TEXT,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          FOREIGN KEY (filing_id) REFERENCES filings(id) ON DELETE CASCADE,
          UNIQUE (filing_id, name, context_ref, unit_ref, value_text, source_file)
        );
        """
    )

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS labels (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          concept_name TEXT NOT NULL,
          role TEXT,
          lang TEXT,
          label_text TEXT NOT NULL,
          created_at TEXT NOT NULL DEFAULT (datetime('now')),
          updated_at TEXT NOT NULL DEFAULT (datetime('now')),
          UNIQUE(concept_name, role, lang, label_text)
        );
        """
    )

    con.execute("CREATE INDEX IF NOT EXISTS idx_facts_filing ON facts(filing_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_facts_name ON facts(name);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_facts_context ON facts(context_ref);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_facts_unit ON facts(unit_ref);")

    con.execute("CREATE INDEX IF NOT EXISTS idx_contexts_filing ON contexts(filing_id);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_units_filing ON units(filing_id);")

    con.execute("CREATE INDEX IF NOT EXISTS idx_labels_concept ON labels(concept_name);")
    con.execute("CREATE INDEX IF NOT EXISTS idx_labels_lang ON labels(lang);")
