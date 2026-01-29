from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True, slots=True)
class Fact:
    """
    A normalized representation of an iXBRL fact.
    """
    name: str
    context_ref: str | None
    unit_ref: str | None

    decimals: str | None
    precision: str | None
    scale: str | None
    sign: str | None

    is_numeric: bool
    value_text: str
    value_num: Optional[Decimal]

    raw_text: str
    source_file: str
    source_locator: str | None  # e.g., element @id
