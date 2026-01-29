from __future__ import annotations

from decimal import Decimal
from typing import List

from lxml import etree

from tdnet_xbrl_ingestor.ingest.normalize import normalize_non_numeric, normalize_numeric
from tdnet_xbrl_ingestor.models.entities import Fact
from tdnet_xbrl_ingestor.utils.zipreader import read_bytes


IX_NS = "http://www.xbrl.org/2008/inlineXBRL"


def extract_facts_from_ixbrl(
    zip_path: str,
    ixbrl_inner_path: str,
    warnings: list[str] | None = None,
) -> List[Fact]:
    """
    Extract facts from a single iXBRL XHTML file inside a ZIP.

    - Extracts ix:nonFraction (numeric) and ix:nonNumeric (non-numeric)
    - Does NOT require external taxonomy resolution
    - Keeps raw_text and source_file for traceability
    """
    if warnings is None:
        warnings = []

    data = read_bytes(zip_path, ixbrl_inner_path)

    parser = etree.XMLParser(
        recover=True,         # tolerate minor XHTML issues
        huge_tree=True,       # large files
        remove_comments=False,
        remove_pis=False,
        ns_clean=True,
        encoding="utf-8",
    )

    try:
        root = etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError as e:
        warnings.append(f"[ixbrl] XML parse failed: {ixbrl_inner_path}: {e}")
        return []

    ns = dict(root.nsmap or {})
    # Ensure we can address ix namespace even if prefix differs
    ns.setdefault("ix", IX_NS)

    facts: list[Fact] = []

    # Numeric facts
    for el in root.xpath("//ix:nonFraction", namespaces=ns):
        facts.append(_fact_from_element(el, ixbrl_inner_path, is_numeric=True, warnings=warnings))

    # Non-numeric facts
    for el in root.xpath("//ix:nonNumeric", namespaces=ns):
        facts.append(_fact_from_element(el, ixbrl_inner_path, is_numeric=False, warnings=warnings))

    # Filter out broken ones missing name (rare but possible with recover=True)
    facts = [f for f in facts if f.name]

    return facts


def _fact_from_element(
    el: etree._Element,
    source_file: str,
    *,
    is_numeric: bool,
    warnings: list[str],
) -> Fact:
    """
    Convert a single ix:* element into Fact.
    """
    # Attributes (iXBRL)
    name = (el.get("name") or "").strip()
    context_ref = (el.get("contextRef") or "").strip() or None
    unit_ref = (el.get("unitRef") or "").strip() or None

    decimals = (el.get("decimals") or "").strip() or None
    precision = (el.get("precision") or "").strip() or None
    scale = (el.get("scale") or "").strip() or None
    sign = (el.get("sign") or "").strip() or None

    # Locator (best effort)
    locator = (el.get("id") or "").strip() or None

    # raw text: include nested nodes
    raw_text = "".join(el.itertext())
    raw_text = raw_text.replace("\u00a0", " ").strip()

    if not name:
        warnings.append(f"[ixbrl] Missing @name in fact element in {source_file} (id={locator})")

    if is_numeric:
        norm = normalize_numeric(raw_text, sign_attr=sign, scale_attr=scale)
        if norm.warning:
            warnings.append(f"[ixbrl] {source_file} ({name}) {norm.warning}")
        value_text = norm.value_text
        value_num: Decimal | None = norm.value_num
    else:
        norm = normalize_non_numeric(raw_text)
        value_text = norm.value_text
        value_num = None

    return Fact(
        name=name,
        context_ref=context_ref,
        unit_ref=unit_ref,
        decimals=decimals,
        precision=precision,
        scale=scale,
        sign=sign,
        is_numeric=is_numeric,
        value_text=value_text,
        value_num=value_num,
        raw_text=raw_text,
        source_file=source_file,
        source_locator=locator,
    )
