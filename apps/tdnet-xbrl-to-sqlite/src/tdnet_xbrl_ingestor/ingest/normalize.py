from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


_WS_RE = re.compile(r"\s+", re.UNICODE)

# 「数値っぽい部分」を抜く（例: "1,234" / "1,234.56" / "-123"）
_NUM_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


@dataclass(frozen=True, slots=True)
class NormalizedValue:
    value_text: str
    value_num: Optional[Decimal]
    is_numeric: bool
    warning: str | None


def normalize_non_numeric(raw: str) -> NormalizedValue:
    raw0 = raw or ""
    txt = _WS_RE.sub(" ", raw0.replace("\u00a0", " ")).strip()
    return NormalizedValue(value_text=txt, value_num=None, is_numeric=False, warning=None)


def normalize_numeric(
    raw: str,
    *,
    sign_attr: str | None = None,
    scale_attr: str | None = None,
) -> NormalizedValue:
    """
    Normalize iXBRL numeric text into Decimal when possible.
    Handles:
      - commas, NBSP
      - parentheses () / （）
      - triangle negative markers: △ ▲
      - @sign='-' attribute
      - @scale (10^scale)
    """
    raw0 = raw or ""
    s = raw0.replace("\u00a0", " ").strip()

    if s == "":
        return NormalizedValue("", None, True, "Empty numeric fact value.")

    neg = False

    # sign attribute
    if sign_attr and sign_attr.strip() == "-":
        neg = True

    # triangle markers
    if s[:1] in ("△", "▲"):
        neg = True
        s = s[1:].strip()

    # parentheses (ascii / full-width)
    if (s.startswith("(") and s.endswith(")")) or (s.startswith("（") and s.endswith("）")):
        neg = True
        s = s[1:-1].strip()

    # remove commas / spaces
    s = s.replace(",", "")
    s = _WS_RE.sub("", s)

    # some disclosures use "－" etc as placeholder
    if s in ("-", "－", "―", "—"):
        return NormalizedValue("", None, True, "Placeholder dash numeric value.")

    # best-effort: if unexpected chars exist, try to extract a clean number
    # (avoid being too aggressive; we keep warning)
    warning = None
    if not _NUM_RE.match(s):
        # strip common full-width digits? (rare) -> keep simple; warn and fail parse
        warning = f"Unparseable numeric token: {s!r}"
        return NormalizedValue(value_text=s, value_num=None, is_numeric=True, warning=warning)

    try:
        d = Decimal(s)
        if neg:
            d = -d

        if scale_attr is not None and scale_attr != "":
            try:
                scale = int(scale_attr)
                if scale != 0:
                    d = d * (Decimal(10) ** Decimal(scale))
            except ValueError:
                # ignore invalid scale, but warn
                warning = f"Invalid scale attribute: {scale_attr!r}"

        return NormalizedValue(value_text=str(d), value_num=d, is_numeric=True, warning=warning)

    except (InvalidOperation, ValueError) as e:
        return NormalizedValue(
            value_text=s,
            value_num=None,
            is_numeric=True,
            warning=f"Decimal parse failed: {e}",
        )
