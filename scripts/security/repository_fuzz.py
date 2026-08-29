#!/usr/bin/env python3
# ruff: noqa: I001 -- synchronized across repositories with different import policies
"""Bounded, dependency-free fuzz smoke test for repository config parsers."""

from __future__ import annotations

import itertools
import json
import sys
import tomllib
from pathlib import Path


MAX_FILES = 16
MAX_SOURCE_BYTES = 1024 * 1024


def _corpus(root: Path) -> list[tuple[str, bytes]]:
    values: list[tuple[str, bytes]] = []
    try:
        candidates = sorted(
            path
            for path in root.iterdir()
            if path.suffix.casefold() in {".json", ".toml"}
        )[:MAX_FILES]
    except OSError:
        candidates = []
    for path in candidates:
        suffix = path.suffix.casefold()
        try:
            size = path.stat().st_size
            if path.is_symlink() or not 0 < size <= MAX_SOURCE_BYTES:
                continue
            values.append((suffix, path.read_bytes()))
        except OSError:
            continue
    return values


def _mutations(payload: bytes) -> tuple[bytes, ...]:
    midpoint = max(1, len(payload) // 2)
    return (
        payload[:midpoint],
        payload + b"\x00",
        b"{" * 128 + payload[:64],
        b"[" * 128 + payload[:64],
        payload[:32] + b"\xff\xfe" + payload[32:64],
        b"null trailing",
        b"key = [1, 2,",
        b"\n" * 4096 + payload[:128],
    )


def _exercise(suffix: str, payload: bytes) -> None:
    text = payload.decode("utf-8")
    if suffix == ".json":
        json.loads(text)
    else:
        tomllib.loads(text)


_MAX_CASES = 64


def _is_crash(suffix: str, payload: bytes) -> bool:
    """Return whether exercising ``payload`` raised an unexpected exception."""
    try:
        _exercise(suffix, payload)
    except (UnicodeDecodeError, json.JSONDecodeError, tomllib.TOMLDecodeError):
        return False
    except Exception:
        return True
    return False


def _run_fuzz_cases(
    corpus: list[tuple[str, bytes]], limit: int = _MAX_CASES
) -> tuple[int, int]:
    """Exercise mutations of ``corpus`` up to ``limit`` cases; return (cases, crashes)."""
    cases = 0
    crashes = 0
    for suffix, payload in itertools.cycle(corpus):
        for mutation in _mutations(payload):
            if _is_crash(suffix, mutation):
                crashes += 1
            cases += 1
            if cases >= limit:
                return cases, crashes
    return cases, crashes


def _write_fuzz_report(output: Path, cases: int, crashes: int) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {
                "version": 1,
                "kind": "fuzz",
                "passed": crashes == 0,
                "cases": cases,
                "failures": 0,
                "crashes": crashes,
            },
            sort_keys=True,
        ),
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        return 2
    corpus = _corpus(Path.cwd()) or [(".json", b'{"seed": true}')]
    cases, crashes = _run_fuzz_cases(corpus)
    _write_fuzz_report(Path(sys.argv[1]), cases, crashes)
    return 0 if crashes == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
