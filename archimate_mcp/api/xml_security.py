"""Bounded parser for untrusted ArchiMate exchange documents."""

from __future__ import annotations

from pathlib import Path

from defusedxml import ElementTree as DefusedET
from defusedxml.common import DefusedXmlException

MAX_EXCHANGE_BYTES = 32 * 1024 * 1024
MAX_EXCHANGE_DEPTH = 96
MAX_EXCHANGE_ELEMENTS = 500_000


class ExchangeXmlError(ValueError):
    """An exchange document crossed a parser security boundary."""


def parse_exchange_root(path: str):
    """Read and parse a regular, bounded XML file without DTD/entity support."""

    candidate = Path(path)
    try:
        if candidate.is_symlink() or not candidate.is_file():
            raise ExchangeXmlError("exchange document is not a regular file")
        size = candidate.stat().st_size
        if size <= 0 or size > MAX_EXCHANGE_BYTES:
            raise ExchangeXmlError("exchange document exceeds its safe size boundary")
        with candidate.open("rb") as stream:
            payload = stream.read(MAX_EXCHANGE_BYTES + 1)
    except ExchangeXmlError:
        raise
    except OSError:
        raise ExchangeXmlError("exchange document is unavailable") from None
    if len(payload) != size or len(payload) > MAX_EXCHANGE_BYTES:
        raise ExchangeXmlError("exchange document changed while being read")
    try:
        root = DefusedET.fromstring(
            payload,
            forbid_dtd=True,
            forbid_entities=True,
            forbid_external=True,
        )
    except (DefusedET.ParseError, DefusedXmlException, ValueError):
        raise ExchangeXmlError("exchange document is invalid") from None

    count = 0
    stack = [(root, 1)]
    while stack:
        element, depth = stack.pop()
        count += 1
        if count > MAX_EXCHANGE_ELEMENTS or depth > MAX_EXCHANGE_DEPTH:
            raise ExchangeXmlError("exchange document exceeds its structure boundary")
        stack.extend((child, depth + 1) for child in element)
    return root
