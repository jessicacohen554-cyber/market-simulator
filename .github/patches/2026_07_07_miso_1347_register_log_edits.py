"""MISO #1347 carrier: apply the session's gap-register (+ calibration-log) edits.

Run by .github/workflows/apply-miso-1347-edits.yml. The register rows being
edited are multi-kilobyte single lines, so a full-file push through the agent
sandbox's text-only MCP write path would mean hand-transcribing giant
mechanical lines — the corruption risk the apply-export-cap.yml /
apply-w3a-seam-clock.yml precedents exist to avoid. Each edit is addressed by
a SHORT literal anchor and spliced in place. Idempotent: an edit whose new
text is already present is skipped, so the carrier workflow can re-run freely.

Session context: the #1347 rule-23 trigger audit (MISO coal sigmoids).
The F923 2025 annual Early Release was intaken (carrier
.github/workflows/f923-2025er-intake.yml on this branch) and measured to be a
strict MISO-coal no-op; EIA's historical coal spot prices are S&P-proprietary.
Re-derivation therefore stays blocked; these edits record that verified state.
"""

from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
REGISTER = REPO / "docs" / "gap-register-2026-07.md"


def replace_once(text: str, old: str, new: str, key: str) -> str:
    """Replace the unique ``old`` with ``new``; ``key`` is the idempotency probe."""
    if key in text:
        print(f"  skip (already applied): {key[:60]!r}")
        return text
    if text.count(old) != 1:
        raise SystemExit(f"anchor not unique/absent ({text.count(old)}x): {old[:80]!r}")
    return text.replace(old, new)


def main() -> None:
    text = REGISTER.read_text()

    # G-26 row: record the rule-23 trigger-audit outcome on the coal-sigmoid item.
    text = replace_once(
        text,
        "coal sigmoids (#1347),",
        "coal sigmoids (#1347 — MISO rule-23 trigger audit 2026-07-07: F923 2025 "
        "annual ER intaken = strict MISO-coal no-op, EIA coal spot history "
        "S&P-proprietary → re-derivation stays blocked, data-ask on the issue),",
        key="MISO rule-23 trigger audit 2026-07-07: F923 2025",
    )

    # L-14 MISO row, backlog cell: the ask is now a verified BLOCK with named triggers.
    text = replace_once(
        text,
        "coal sigmoids → #1347 (source-data ask)",
        "coal sigmoids → #1347 (**BLOCKED 2026-07-07**, rule-23 trigger audit: "
        "F923 2025 annual ER intaken and a strict MISO-coal no-op — 0 new "
        "plant-months, byte-identical takeorpay re-derive; EIA coal spot history "
        "S&P-proprietary; data-ask on the issue — next triggers F923-2025-final / "
        "ACR-2025 f.o.b.-by-basin, both ~Oct 2026, or the F923-2026 fourth gas "
        "regime)",
        key="BLOCKED 2026-07-07**, rule-23 trigger audit",
    )

    # L-14 MISO row, notes cell: name the rule-24 wart the eventual re-derivation
    # must also fix (floor/gas_mid/gas_slope are ERCOT byte-copies).
    text = replace_once(
        text,
        "(#1347, no refit without new source data).",
        "(#1347, no refit without new source data — and the sigmoid family's "
        "floor/gas_mid/gas_slope are ERCOT byte-copies, a rule-24 wart the "
        "eventual re-derivation must also fix).",
        key="ERCOT byte-copies, a rule-24 wart",
    )

    REGISTER.write_text(text)
    print(f"applied register edits -> {REGISTER}")


if __name__ == "__main__":
    main()
