"""Apply the caiso-166 `zonal_loss_surface` matrix-cell update (rule 28 duty b).

**Why this exists instead of the edit being committed directly.** `git push` was
unusable in the caiso-166 session — the origin returned HTTP 413 for *every*
push, including a no-op ref advance whose request body was 4 bytes, because git
sends the receive-pack RPC with `Transfer-Encoding: chunked` and the origin
rejects any chunked body. The working transport, `mcp__github__push_files`, is
text-only with a ~457 KB cap, and
`docs/codebase-site/data/mechanism-matrix.js` is **843 KB**, so the file itself
could not be pushed whole. This script carries the edit instead: it is small,
anchored, idempotent and self-verifying.

The edit is the one rule 28(b) requires of the session that tested a mechanism:
caiso-166 re-derived the **input data** of `caiso_zonal_loss_surface`, so the
cell's **verdict is UNCHANGED at `K`** (the mechanism itself was not re-tested)
and only the `note` + `ev.C` citation gain the caiso-166 outcome.

Run from the repo root::

    python results/calibration/_caiso166_apply_matrix_cell.py

Exit 0 = applied (or already applied). Non-zero = an anchor did not match
exactly once, which means the file drifted and the edit needs re-siting by hand
rather than being force-fitted.
"""

from __future__ import annotations

import sys
from pathlib import Path

MATRIX = Path("docs/codebase-site/data/mechanism-matrix.js")

# Anchor 1 — the tail of the row's `note`, immediately before the `ev:` key.
NOTE_ANCHOR = 'results/calibration/_caiso165_intra_sp15.json.",\n      ev: { M: "miso-76'

NOTE_ADDITION = (
    " CAISO-166 (2026-08-04) re-derived this mechanism's INPUT DATA on that "
    "intake and the cell is UNCHANGED at K: the MECHANISM was not re-tested, "
    "only the surface it reads. LA_BASIN -> DLAP_SCE-APND and SDGE -> "
    "DLAP_SDGE-APND replace the TH_SP15_GEN GENERATION-hub deviation both LOAD "
    "pockets inherited (rule 14 [R-ACCURATE]; rule 23 licence is the SOURCE-DATA "
    "change, no residual consulted). ZERO config delta between arms -- "
    "caiso_zonal_loss_surface is True in BOTH, so the only object that differs "
    "is the CSV, and the 2023 PLACEBO year (identical rows both arms) reproduces "
    "to EXACTLY 0.0 on price, class dispatch AND flows. Derive acceptance 12/12 "
    "in band with the four pre-existing pair-years reproducing caiso-164's "
    "1.04-1.06x exactly; the three hub zones bit-identical across all 96 rows "
    "each; 48/240 rows change. ARM A IS **NOT PROMOTED** on TWO pre-registered "
    "gates, neither relaxed after firing: (1) gate S3 adversarial ceiling "
    "BREACHED at 2025 LA_BASIN-SP15_rest, delta +1.0205 vs measured dMCL +0.9686 "
    "= 105.4% of ceiling; (2) C3a mean LMP regresses 2024 PASS -> FAIL (+9.5% -> "
    "+11.5% on a +/-10% band), undocumented because the incumbent's ledgered "
    "price_mean exception covers 2025 only. Determination NOT-YET. THE S3 BREACH "
    "IS A GATE-SPECIFICATION DEFECT, NOT A MECHANISM ONE, and the decomposition "
    "proves it: the LP tracks the surface-implied separation at 0.914-1.011x "
    "(never meaningfully above it), while the surface itself sits 1.038-1.042x "
    "above measured dMCL -- the MCE-weighted estimator's own positive bias, the "
    "same +4% the derive's [0.5x,1.5x] acceptance band ACCEPTS. 105.4% = 1.042 x "
    "1.011. A ceiling at exactly 1.00x holds the LP TIGHTER than the derive's own "
    "accepted tolerance; re-charter it PROSPECTIVELY or not at all. The measured "
    "surface is KEPT REGARDLESS (rule 14, pre-committed): losses consume MWh so "
    "lambda MUST rise (+1.82%/+2.06%), and CAISO's level was ALREADY +9.5%/+12.1% "
    "hot vs RT -- the arm pushed a pre-existing bias across a line it was already "
    "touching, which is a discovered bug elsewhere, never grounds to revert. OPEN "
    "FOR OWNER: the committed surface and the caiso-164 keeper (solved on the old "
    "surface) now disagree, so the keeper no longer reproduces from the repo. "
    "Evidence: FINDING-caiso166-measured-loss-zones-2026-08-04.md, "
    "PRECHECK-caiso166-measured-loss-zones-2026-08-04.md, "
    "scripts/gen_caiso166_attestation.py."
)

# Anchor 2 — the tail of the row's `ev.C` citation.
EV_ANCHOR = 'caiso164_wiring_probe.py)" } },'

EV_ADDITION = (
    "caiso164_wiring_probe.py); caiso-166 (2026-08-04, DATA re-derive of this "
    "mechanism's INPUT, mechanism verdict UNTOUCHED and NOT re-tested — "
    "PRECHECK-caiso166-measured-loss-zones-2026-08-04 pushed at 6c2dbfd5 BEFORE "
    "either arm solved, FINDING-caiso166-measured-loss-zones-2026-08-04, arms "
    "2026-08-04-caiso-166-measured-dlap / "
    "2026-08-04-caiso-166-control-hubsurface. NOT PROMOTED: keeper stays "
    "2026-08-04-caiso164-zonal-loss-surface)\" } },"
)

SENTINEL = "CAISO-166 (2026-08-04) re-derived this mechanism's INPUT DATA"


def main() -> int:
    """Apply both anchored edits; return 0 on success or if already applied."""
    if not MATRIX.is_file():
        print(f"FATAL: {MATRIX} not found — run from the repo root", file=sys.stderr)
        return 2
    src = MATRIX.read_text()

    if SENTINEL in src:
        print("already applied — nothing to do")
        return 0

    for label, anchor in (("note", NOTE_ANCHOR), ("ev.C", EV_ANCHOR)):
        n = src.count(anchor)
        if n != 1:
            print(
                f"FATAL: the {label} anchor matched {n} times, expected exactly 1 "
                "— mechanism-matrix.js has drifted. Re-site the caiso-166 cell "
                "edit by hand (see FINDING-caiso166-measured-loss-zones-2026-08-04"
                ".md); do NOT force-fit it.",
                file=sys.stderr,
            )
            return 1

    src = src.replace(
        NOTE_ANCHOR,
        'results/calibration/_caiso165_intra_sp15.json.'
        + NOTE_ADDITION
        + '",\n      ev: { M: "miso-76',
    )
    src = src.replace(EV_ANCHOR, EV_ADDITION)
    MATRIX.write_text(src)
    print(f"applied the caiso-166 zonal_loss_surface cell update to {MATRIX}")
    print("cell verdict UNCHANGED at K; note + ev.C citation extended")
    print("now re-run: python3 scripts/check_mechanism_matrix.py --base origin/main")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
