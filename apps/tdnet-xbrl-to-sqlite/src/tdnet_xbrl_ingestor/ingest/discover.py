from __future__ import annotations

from dataclasses import dataclass
import zipfile


@dataclass(frozen=True, slots=True)
class DiscoverResult:
    ixbrl_files: list[str]
    label_files: list[str]


def discover_targets(zip_path: str) -> DiscoverResult:
    """Discover iXBRL (.htm/.xhtml) and label linkbase (*-lab.xml) inside TDnet ZIP."""
    ixbrl: list[str] = []
    labels: list[str] = []

    with zipfile.ZipFile(zip_path) as zf:
        for name in zf.namelist():
            low = name.lower()

            if (low.endswith(".htm") or low.endswith(".xhtml")) and "ixbrl" in low:
                ixbrl.append(name)
                continue

            if low.endswith("-lab.xml"):
                labels.append(name)

    ixbrl.sort()
    labels.sort()
    return DiscoverResult(ixbrl_files=ixbrl, label_files=labels)
