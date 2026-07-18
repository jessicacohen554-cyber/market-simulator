"""Turn human-friendly offer-curve tweak lines into delta JSON.

So a calibration run never needs hand-written JSON: an operator types up to a
handful of ``CLASS.BAND <delta>`` entries and this emits the
``{class: {band: delta}}`` object that ``run_calibration_full.py
--offer-curve-delta-json`` consumes. Each delta is RELATIVE — added to the
current calibrated value — so ``CT_PEAKER.committed +0.05`` nudges a 1.40
multiplier to 1.45 and ``-0.05`` to 1.35, with no need to remember the prior
absolute.

Entry syntax (very forgiving): one entry per line, or separated by commas or
semicolons. Within an entry the class and band may be joined by ``.`` or a
space, and the delta follows after ``=``, ``:`` or whitespace::

    CT_PEAKER.committed +0.05
    COAL_PRB committed=-0.05; ST_GAS.peak 0.5

Class/band names are validated against the live default offer curve (so a typo
fails fast with the valid options listed). The compact delta JSON is printed to
stdout; a human-readable ``default -> result`` summary goes to stderr.

Usage:
    python scripts/data/build_offer_curve_overrides.py --iso ERCOT \
        --tweaks "CT_PEAKER.committed +0.05, COAL_PRB.committed -0.05"
    python scripts/data/build_offer_curve_overrides.py --iso ERCOT --list
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))


def _default_offer_curve(iso: str) -> dict[str, dict[str, float]]:
    """Return the calibrated default offer_curve_by_group for ``iso``.

    Loaded by importing run_calibration and building a throwaway config; the
    offer curve is ISO-independent today but we pass the ISO through so this
    keeps working if that changes.
    """
    spec = importlib.util.spec_from_file_location(
        "rc", str(REPO / "scripts" / "run_calibration.py")
    )
    rc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rc)
    return rc._calibration_config(2024, iso, 10, 3.0).offer_curve_by_group


def _parse_tweaks(text: str, defaults: dict[str, dict[str, float]]) -> dict:
    """Parse the free-text tweak entries into a ``{class:{band:delta}}`` dict.

    Validates every class/band against ``defaults`` and that the delta is a
    number, raising ``SystemExit`` with the valid options on any miss. Repeated
    class/band entries sum (two ``+0.05`` lines = ``+0.10``).
    """
    if not text or not text.strip():
        return {}
    # Entries may be separated by commas, semicolons, newlines OR plain spaces.
    # GitHub Actions workflow_dispatch string inputs are single-line, so a
    # multi-line paste arrives space-flattened ("A.b -0.1 C.d +0.2 ..."); we
    # scan for every CLASS.BAND <delta> triple anywhere in the text rather than
    # pre-splitting, so all of those forms work.
    # CLASS [. or space] BAND [= : or space] DELTA(signed float). The delta is
    # the trailing number, so the '.' in e.g. +0.05 is never mistaken for the
    # class/band separator, and a following CLASS token starts the next match.
    pat = re.compile(r"([A-Za-z_]+)[.\s]+([A-Za-z_]+)[\s=:]+([+-]?[0-9]*\.?[0-9]+)")
    matches = list(pat.finditer(text))
    # Anything left over once the matches and separators are removed is a
    # malformed token (a typo, a missing delta) — fail loudly rather than
    # silently dropping it.
    covered = bytearray(len(text))
    for m in matches:
        covered[m.start() : m.end()] = b"\x01" * (m.end() - m.start())
    leftover = "".join(
        ch
        for i, ch in enumerate(text)
        if not covered[i] and not ch.isspace() and ch not in ",;"
    ).strip()
    if leftover:
        raise SystemExit(
            f"offer-curve tweaks: could not parse near {leftover!r}; each entry "
            "must be 'CLASS.BAND <delta>' (e.g. 'CT_PEAKER.committed +0.05')."
        )
    if not matches:
        raise SystemExit(
            "offer-curve tweaks: no 'CLASS.BAND <delta>' entries found "
            "(e.g. 'CT_PEAKER.committed +0.05')."
        )
    deltas: dict[str, dict[str, float]] = {}
    for m in matches:
        entry = m.group(0).strip()
        cls, band, raw_delta = m.group(1), m.group(2), m.group(3)
        cls = cls.upper()
        if cls not in defaults:
            raise SystemExit(
                f"offer-curve tweak {entry!r}: unknown class {cls!r}; valid "
                f"classes: {', '.join(sorted(defaults))}."
            )
        if band not in defaults[cls]:
            raise SystemExit(
                f"offer-curve tweak {entry!r}: unknown band {cls}.{band}; "
                f"{cls} bands: {', '.join(sorted(defaults[cls]))}."
            )
        try:
            delta = float(raw_delta)
        except ValueError:
            raise SystemExit(
                f"offer-curve tweak {entry!r}: delta {raw_delta!r} is not a "
                "number (use e.g. +0.05, -0.05, 0.5)."
            )
        deltas.setdefault(cls, {})[band] = deltas.get(cls, {}).get(band, 0.0) + delta
    return deltas


def _print_summary(deltas: dict, defaults: dict) -> None:
    """Log each tweak as ``CLASS.BAND: default <op> delta -> result`` to stderr."""
    for cls in sorted(deltas):
        for band in sorted(deltas[cls]):
            base = defaults[cls][band]
            d = deltas[cls][band]
            print(
                f"  {cls}.{band}: {base:g} {'+' if d >= 0 else '-'} "
                f"{abs(d):g} -> {base + d:g}",
                file=sys.stderr,
            )


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--iso", default="ERCOT")
    ap.add_argument(
        "--tweaks",
        default="",
        help="Free-text 'CLASS.BAND <delta>' entries (newline/comma/"
        "semicolon separated).",
    )
    ap.add_argument(
        "--list", action="store_true", help="Print the valid class/band menu and exit."
    )
    args = ap.parse_args()

    defaults = _default_offer_curve(args.iso)
    if args.list:
        print(
            f"Offer-curve classes and bands (defaults for {args.iso}):", file=sys.stderr
        )
        for cls in sorted(defaults):
            bands = ", ".join(f"{b}={defaults[cls][b]:g}" for b in defaults[cls])
            print(f"  {cls}: {bands}", file=sys.stderr)
        print("{}")
        return

    deltas = _parse_tweaks(args.tweaks, defaults)
    if deltas:
        print(f"Offer-curve tweaks ({args.iso}):", file=sys.stderr)
        _print_summary(deltas, defaults)
    else:
        print("No offer-curve tweaks given.", file=sys.stderr)
    # Compact JSON on stdout for the workflow / solver to consume.
    print(json.dumps(deltas, separators=(",", ":")))


if __name__ == "__main__":
    main()
