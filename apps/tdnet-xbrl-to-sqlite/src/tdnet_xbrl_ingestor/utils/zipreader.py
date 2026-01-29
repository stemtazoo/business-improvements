from __future__ import annotations

import zipfile


def read_bytes(zip_path: str, inner_path: str) -> bytes:
    with zipfile.ZipFile(zip_path) as zf:
        return zf.read(inner_path)


def read_text(zip_path: str, inner_path: str, encoding: str = "utf-8") -> str:
    data = read_bytes(zip_path, inner_path)
    # TDnetはUTF-8が多い。念のためBOM除去。
    text = data.decode(encoding, errors="replace")
    return text.lstrip("\ufeff")
