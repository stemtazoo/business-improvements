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


@dataclass(frozen=True, slots=True)
class Label:
    """
    Label mapping for a concept (QName).
    """
    concept_name: str
    role: str | None
    lang: str | None
    label_text: str


@dataclass(frozen=True, slots=True)
class Context:
    context_ref: str
    entity_scheme: str | None
    entity_identifier: str | None
    period_type: str  # "instant" or "duration" or "unknown"
    instant_date: str | None
    start_date: str | None
    end_date: str | None
    dimensions_json: str  # JSON string


@dataclass(frozen=True, slots=True)
class Unit:
    unit_ref: str
    measures_json: str  # JSON string
