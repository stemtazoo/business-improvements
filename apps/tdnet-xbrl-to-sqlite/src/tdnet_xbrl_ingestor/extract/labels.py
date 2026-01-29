from __future__ import annotations

from typing import List

from lxml import etree

from tdnet_xbrl_ingestor.models.entities import Label
from tdnet_xbrl_ingestor.utils.zipreader import read_bytes


LINK_NS = "http://www.xbrl.org/2003/linkbase"
XLINK_NS = "http://www.w3.org/1999/xlink"


def extract_labels(
    zip_path: str,
    lab_inner_path: str,
    warnings: list[str] | None = None,
) -> List[Label]:
    """
    Extract concept labels from XBRL linkbase label files (*-lab.xml).

    Typical structure:
      <link:labelLink>
        <link:loc xlink:href="...#ConceptName" xlink:label="loc1" />
        <link:label xlink:label="lab1" xlink:role="..." xml:lang="ja">売上高</link:label>
        <link:labelArc xlink:from="loc1" xlink:to="lab1" />
      </link:labelLink>

    We map:
      concept_name = fragment part after '#'
      role = xlink:role (optional)
      lang = xml:lang (optional)
      label_text = text
    """
    if warnings is None:
        warnings = []

    data = read_bytes(zip_path, lab_inner_path)

    parser = etree.XMLParser(
        recover=True,
        huge_tree=True,
        ns_clean=True,
        encoding="utf-8",
    )

    try:
        root = etree.fromstring(data, parser=parser)
    except etree.XMLSyntaxError as e:
        warnings.append(f"[lab] XML parse failed: {lab_inner_path}: {e}")
        return []

    ns = dict(root.nsmap or {})
    ns.setdefault("link", LINK_NS)
    ns.setdefault("xlink", XLINK_NS)

    # 1) loc label -> concept name mapping
    loc_map: dict[str, str] = {}
    for loc in root.xpath("//link:loc", namespaces=ns):
        loc_label = (loc.get(f"{{{XLINK_NS}}}label") or "").strip()
        href = (loc.get(f"{{{XLINK_NS}}}href") or "").strip()
        if not loc_label or not href:
            continue
        concept = _concept_from_href(href)
        if concept:
            loc_map[loc_label] = concept

    # 2) label resource mapping: label_id -> (text, role, lang)
    res_map: dict[str, tuple[str, str | None, str | None]] = {}
    for lab in root.xpath("//link:label", namespaces=ns):
        lab_id = (lab.get(f"{{{XLINK_NS}}}label") or "").strip()
        if not lab_id:
            continue
        role = (lab.get(f"{{{XLINK_NS}}}role") or "").strip() or None
        lang = (lab.get("{http://www.w3.org/XML/1998/namespace}lang") or "").strip() or None
        text = "".join(lab.itertext()).strip()
        if text:
            res_map[lab_id] = (text, role, lang)

    # 3) arcs connect loc -> label
    out: list[Label] = []
    for arc in root.xpath("//link:labelArc", namespaces=ns):
        frm = (arc.get(f"{{{XLINK_NS}}}from") or "").strip()
        to = (arc.get(f"{{{XLINK_NS}}}to") or "").strip()
        if not frm or not to:
            continue
        concept = loc_map.get(frm)
        res = res_map.get(to)
        if not concept or not res:
            continue
        text, role, lang = res
        out.append(Label(concept_name=concept, role=role, lang=lang, label_text=text))

    if not out:
        warnings.append(f"[lab] No labels extracted: {lab_inner_path}")

    return out


def _concept_from_href(href: str) -> str | None:
    """
    href examples:
      'tse-ed-t-...-xsd-2024-01-01.xsd#NetSales'
      '../xxx.xsd#tse-ed-t:NetSales'  (rare)
    We return fragment after '#', preserving prefix if present.
    """
    if "#" not in href:
        return None
    frag = href.split("#", 1)[1].strip()
    return frag or None
