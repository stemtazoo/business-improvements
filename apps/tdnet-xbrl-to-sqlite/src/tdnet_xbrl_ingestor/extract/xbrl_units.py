from __future__ import annotations

import json
from typing import List

from lxml import etree

from tdnet_xbrl_ingestor.models.entities import Unit
from tdnet_xbrl_ingestor.utils.zipreader import read_bytes


XBRLI_NS = "http://www.xbrl.org/2003/instance"


def extract_units_from_ixbrl(
    zip_path: str,
    ixbrl_inner_path: str,
    warnings: list[str] | None = None,
) -> List[Unit]:
    if warnings is None:
        warnings = []

    data = read_bytes(zip_path, ixbrl_inner_path)

    parser = etree.XMLParser(recover=True, huge_tree=True, ns_clean=True, encoding="utf-8")
    try:
        root = etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError as e:
        warnings.append(f"[unit] XML parse failed: {ixbrl_inner_path}: {e}")
        return []

    # ✅ drop None key
    ns = {k: v for k, v in (root.nsmap or {}).items() if k}
    ns.setdefault("xbrli", XBRLI_NS)

    out: list[Unit] = []
    for u in root.xpath("//xbrli:unit", namespaces=ns):
        uid = (u.get("id") or "").strip()
        if not uid:
            continue

        measures = [((m.text or "").strip()) for m in u.xpath(".//xbrli:measure", namespaces=ns)]
        measures = [m for m in measures if m]

        out.append(Unit(unit_ref=uid, measures_json=json.dumps(measures, ensure_ascii=False)))

    return out
