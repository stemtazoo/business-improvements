from __future__ import annotations

import zipfile
from pathlib import Path

from tdnet_xbrl_ingestor.extract.ixbrl_facts import extract_facts_from_ixbrl


def test_extract_ixbrl_facts_minimal(tmp_path: Path):
    # Minimal iXBRL sample
    xhtml = """<?xml version="1.0" encoding="utf-8"?>
    <html xmlns="http://www.w3.org/1999/xhtml"
          xmlns:ix="http://www.xbrl.org/2008/inlineXBRL">
      <body>
        <ix:nonFraction name="tse-ed-t:NetSales" contextRef="C1" unitRef="U1" decimals="0">1,234</ix:nonFraction>
        <ix:nonFraction name="tse-ed-t:OperatingIncome" contextRef="C1" unitRef="U1" decimals="0">(567)</ix:nonFraction>
        <ix:nonNumeric name="tse-ed-t:CompanyName" contextRef="C2"> テスト株式会社 </ix:nonNumeric>
      </body>
    </html>
    """.encode("utf-8")

    zip_path = tmp_path / "sample.zip"
    inner = "XBRLData/Summary/sample-ixbrl.htm"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(inner, xhtml)

    warnings: list[str] = []
    facts = extract_facts_from_ixbrl(str(zip_path), inner, warnings)

    assert len(facts) == 3
    net_sales = next(f for f in facts if f.name.endswith("NetSales"))
    assert net_sales.is_numeric is True
    assert net_sales.value_text == "1234"

    op = next(f for f in facts if f.name.endswith("OperatingIncome"))
    assert op.value_text == "-567"

    company = next(f for f in facts if f.name.endswith("CompanyName"))
    assert company.is_numeric is False
    assert company.value_text == "テスト株式会社"
