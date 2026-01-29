from __future__ import annotations

import zipfile
from pathlib import Path

from tdnet_xbrl_ingestor.extract.labels import extract_labels


def test_extract_labels_minimal(tmp_path: Path):
    lab_xml = """<?xml version="1.0" encoding="UTF-8"?>
    <link:linkbase xmlns:link="http://www.xbrl.org/2003/linkbase"
                   xmlns:xlink="http://www.w3.org/1999/xlink"
                   xmlns:xml="http://www.w3.org/XML/1998/namespace">
      <link:labelLink xlink:role="http://www.xbrl.org/2003/role/link">
        <link:loc xlink:type="locator" xlink:href="test.xsd#tse-ed-t:NetSales" xlink:label="loc1"/>
        <link:label xlink:type="resource" xlink:label="lab1"
                    xlink:role="http://www.xbrl.org/2003/role/label"
                    xml:lang="ja">売上高</link:label>
        <link:labelArc xlink:type="arc" xlink:from="loc1" xlink:to="lab1"/>
      </link:labelLink>
    </link:linkbase>
    """.encode("utf-8")

    zip_path = tmp_path / "sample.zip"
    inner = "XBRLData/Summary/sample-lab.xml"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr(inner, lab_xml)

    warnings: list[str] = []
    labels = extract_labels(str(zip_path), inner, warnings)

    assert len(labels) == 1
    assert labels[0].concept_name == "tse-ed-t:NetSales"
    assert labels[0].label_text == "売上高"
    assert labels[0].lang == "ja"
