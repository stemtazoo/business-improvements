from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Optional


_WS_RE = re.compile(r"\s+", re.UNICODE)
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
    """Normalize iXBRL numeric text into Decimal when possible."""

    raw0 = raw or ""
    s = raw0.replace("\u00a0", " ").strip()

    # ✅ Empty numeric values are common (e.g., "未定"). Treat as missing silently.
    if s == "":
        return NormalizedValue("", None, True, None)

    neg = False

    if sign_attr and sign_attr.strip() == "-":
        neg = True

    if s[:1] in ("△", "▲"):
        neg = True
        s = s[1:].strip()

    if (s.startswith("(") and s.endswith(")")) or (s.startswith("（") and s.endswith("）")):
        neg = True
        s = s[1:-1].strip()

    s = s.replace(",", "")
    s = _WS_RE.sub("", s)

    if s in ("-", "－", "―", "—"):
        return NormalizedValue("", None, True, None)

    warning = None
    if not _NUM_RE.match(s):
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
                warning = f"Invalid scale attribute: {scale_attr!r}"

        return NormalizedValue(value_text=str(d), value_num=d, is_numeric=True, warning=warning)

    except (InvalidOperation, ValueError) as e:
        return NormalizedValue(value_text=s, value_num=None, is_numeric=True, warning=f"Decimal parse failed: {e}")
