from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True, slots=True)
class Fact:
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
    source_locator: str | None


@dataclass(frozen=True, slots=True)
class Label:
    concept_name: str
    role: str | None
    lang: str | None
    label_text: str


@dataclass(frozen=True, slots=True)
class Context:
    context_ref: str
    entity_scheme: str | None
    entity_identifier: str | None
    period_type: str
    instant_date: str | None
    start_date: str | None
    end_date: str | None
    dimensions_json: str


@dataclass(frozen=True, slots=True)
class Unit:
    unit_ref: str
    measures_json: str
