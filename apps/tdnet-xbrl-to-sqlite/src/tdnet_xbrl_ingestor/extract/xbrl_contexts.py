from __future__ import annotations

import json
from typing import List

from lxml import etree

from tdnet_xbrl_ingestor.models.entities import Context
from tdnet_xbrl_ingestor.utils.zipreader import read_bytes


XBRLI_NS = "http://www.xbrl.org/2003/instance"
XBRLDI_NS = "http://xbrl.org/2006/xbrldi"


def extract_contexts_from_ixbrl(
    zip_path: str,
    ixbrl_inner_path: str,
    warnings: list[str] | None = None,
) -> List[Context]:
    if warnings is None:
        warnings = []

    data = read_bytes(zip_path, ixbrl_inner_path)

    parser = etree.XMLParser(recover=True, huge_tree=True, ns_clean=True, encoding="utf-8")
    try:
        root = etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError as e:
        warnings.append(f"[context] XML parse failed: {ixbrl_inner_path}: {e}")
        return []

    # ✅ drop None key
    ns = {k: v for k, v in (root.nsmap or {}).items() if k}
    ns.setdefault("xbrli", XBRLI_NS)
    ns.setdefault("xbrldi", XBRLDI_NS)

    out: list[Context] = []
    for ctx in root.xpath("//xbrli:context", namespaces=ns):
        cid = (ctx.get("id") or "").strip()
        if not cid:
            continue

        entity_scheme = None
        entity_identifier = None
        ident = ctx.find(f".//{{{XBRLI_NS}}}entity/{{{XBRLI_NS}}}identifier")
        if ident is not None:
            entity_scheme = (ident.get("scheme") or "").strip() or None
            entity_identifier = (ident.text or "").strip() or None

        period = ctx.find(f".//{{{XBRLI_NS}}}period")
        period_type = "unknown"
        instant_date = start_date = end_date = None
        if period is not None:
            inst = period.find(f"{{{XBRLI_NS}}}instant")
            if inst is not None and (inst.text or "").strip():
                period_type = "instant"
                instant_date = (inst.text or "").strip()
            else:
                st = period.find(f"{{{XBRLI_NS}}}startDate")
                ed = period.find(f"{{{XBRLI_NS}}}endDate")
                if st is not None and ed is not None:
                    period_type = "duration"
                    start_date = (st.text or "").strip() or None
                    end_date = (ed.text or "").strip() or None

        dims = []
        for mem in ctx.xpath(".//xbrldi:explicitMember", namespaces=ns):
            dim = (mem.get("dimension") or "").strip()
            val = (mem.text or "").strip()
            if dim or val:
                dims.append({"type": "explicit", "dimension": dim, "member": val})

        for mem in ctx.xpath(".//xbrldi:typedMember", namespaces=ns):
            dim = (mem.get("dimension") or "").strip()
            inner = "".join([etree.tostring(ch, encoding="unicode") for ch in mem])
            dims.append({"type": "typed", "dimension": dim, "value_xml": inner})

        out.append(
            Context(
                context_ref=cid,
                entity_scheme=entity_scheme,
                entity_identifier=entity_identifier,
                period_type=period_type,
                instant_date=instant_date,
                start_date=start_date,
                end_date=end_date,
                dimensions_json=json.dumps(dims, ensure_ascii=False),
            )
        )

    return out
