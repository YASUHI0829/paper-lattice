from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DEFAULT_FIELDS = [
    "title",
    "research_question",
    "method",
    "data_or_evidence",
    "limitations",
]


@dataclass(slots=True)
class DomainPack:
    name: str
    path: str | None
    extraction_fields: list[str]


def domain_pack_dir() -> Path:
    return Path(__file__).resolve().parents[2] / "domain_packs"


def parse_list_block(text: str, key: str) -> list[str]:
    lines = text.splitlines()
    values: list[str] = []
    in_block = False
    block_indent: int | None = None
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not in_block:
            if stripped == f"{key}:":
                in_block = True
                block_indent = None
            continue
        indent = len(line) - len(line.lstrip(" "))
        if block_indent is None and stripped.startswith("- "):
            block_indent = indent
        if block_indent is not None and indent < block_indent:
            break
        if not stripped.startswith("- "):
            if indent == 0 and stripped.endswith(":"):
                break
            continue
        values.append(stripped[2:].strip())
    return values


def load_domain_pack(name: str = "general") -> DomainPack:
    if name == "general":
        return DomainPack(name="general", path=None, extraction_fields=DEFAULT_FIELDS)
    path = domain_pack_dir() / f"{name}.yaml"
    if not path.exists():
        return DomainPack(name=name, path=None, extraction_fields=DEFAULT_FIELDS)
    text = path.read_text(encoding="utf-8")
    fields = parse_list_block(text, "extraction_fields")
    return DomainPack(name=name, path=str(path), extraction_fields=fields or DEFAULT_FIELDS)
