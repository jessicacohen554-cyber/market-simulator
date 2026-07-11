#!/usr/bin/env python3
"""Apply the G-61(b) decision-closure doc edits (owner decision 2026-07-11).

Transport script for the apply-g61b-decision-docs workflow: the session's
calibration-log.md is too large to relay whole through push_files (ercot57/
pjm97/caiso7475 patch-transport precedent), and raw .patch transport is
fragile against trailing-whitespace stripping, so the three edits are
reproduced programmatically. Idempotent: each edit is skipped when its text
is already present. Exits non-zero if an anchor is missing and the edit has
not already been applied.
"""

import sys

LOG = "docs/calibration-log.md"
REG = "docs/gap-register-2026-07.md"
BRIEF = "docs/handoffs/owner-decision-briefs-2026-07-08.md"

LOG_ANCHOR = "## Runs\n\n### 2026-07-11 — CAISO — caiso-76 (measured 2025 hydro budget correction)"

LOG_ENTRY = """### 2026-07-11 — CAISO — owner decision G-61(b) EXECUTED: startup-aware RA bridge ADOPTED — already shipped in keeper caiso-76; verified, no re-solve; keeper stays caiso-76

Owner decision G-61(b) (owner-decision-briefs-2026-07-08.md Decision 1, decided
2026-07-11): ADOPT `caiso_ra_bridge_startup_aware` on the current keeper config
(caiso-76), not the old caiso-65 base. Execution session found the requested run
**already exists as the keeper itself** — no new solve or registration:

- **Lineage**: the flag entered the calibration line as caiso-70's pre-registered
  single delta (2026-07-10, G-61b de-crowding probe) and was carried through
  caiso-72 → caiso-73 → caiso-75 → caiso-76; `2026-07-11-caiso-76-hydro-budget`
  (promoted to keeper 2026-07-11, commit 295510c, years 2023–2025 in one bundle
  per rule 16, zero-forcing ablation twin registered per rule 20) has
  `caiso_ra_bridge_startup_aware=True` in `run_config.json` and the bridge listed
  in its attestation DOF-ledger note (zero free parameters). Replaying caiso-76's
  config with the flag enabled is config-identical to caiso-76 — a duplicate
  bundle would add zero information and clutter top-15 retention, so none was
  produced.
- **Mechanism engaged in the keeper**: D-2 attributes `ra_mustoffer_bridge`
  forced CC_REGULAR at 2.38/2.26/1.73 TWh 2023/24/25 (3.8/3.6/3.0% of class,
  C8 PASS) — the startup-aware level, vs 3.5–4.0 TWh under the unconditional
  floor (caiso-63/66 baseline). Phantom belly anchoring (~1.5–1.7 TWh/yr) is out.
- **λ attribution (per the brief)**: the caiso-66 transplant's predicted
  +$0.30–0.46 λ regression did NOT materialize on the shipped base — the
  caiso-70 vs caiso-69 A/B (SP15-split, drag-off) shows hub means essentially
  unchanged (LA_BASIN 70.05/47.65/51.45 vs 70.18/47.82/51.26) with a small 2023
  tail uptick (530→540 h). The keeper's remaining C3a body miss stays attributed
  to the documented belly under-commitment gap (measured CAISO runs 3.1–5.2 GW
  more belly gas than the model — `FINDING-caiso-seam-tz-correction-2026-07-07.md`
  §4.3), owned by the G-15 belly-grounding lane. Per the brief, the unconditional
  floor is NOT a fallback: phantom anchoring is a real defect (rules 1/11).
- **Governance re-verified this session**: `keepers.json` unchanged (already
  caiso-76); `build_status.py --check` in sync (6 keepers);
  calibration-keeper-auditor PASS (`audit_keepers.py --iso CAISO` clean —
  keeper id, v2.4 verdict fields, registry sidecar, twin, and the
  startup-aware flag all confirmed against the bundle). Gap-register G-61 row
  updated to ADOPTED; decision brief annotated RESOLVED.

"""

REG_OLD_TAIL = "Full record: D-8 closure §8. | docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §7–8; results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md; registry `2026-07-07-caiso-63-g61b-startup.json` / `2026-07-07-caiso-64-g61c-curtail.json`; constants.CAISO_RA_MUSTOFFER_GAS_MW | B | blocks-claim (C1/C4 CC over-run) | open, re-adjudicated (adopt-(b) owner decision now carries the W3a belly caveat; (c) blocked on belly-commitment grounding, not the seam) |"

REG_NEW_TAIL = "Full record: D-8 closure §8. **(b) ADOPTED — OWNER DECISION G-61(b), 2026-07-11** (owner-decision-briefs-2026-07-08.md Decision 1): ship the startup-aware bridge on the current keeper config. Executed by verification, not a re-solve: the current keeper `2026-07-11-caiso-76-hydro-budget` (promoted 295510c the same day, all three years + zero-forcing twin) already carries `caiso_ra_bridge_startup_aware=True` — it entered the calibration line as caiso-70's pre-registered single delta (2026-07-10) and was carried through caiso-72 → 73 → 75 → 76, so the decision's requested replay is config-identical to the keeper itself (no duplicate bundle registered; top-15 retention). Keeper D-2 confirms the mechanism engaged: `ra_mustoffer_bridge` forces CC_REGULAR 2.38/2.26/1.73 TWh 2023/24/25 (3.8/3.6/3.0% of class, C8 PASS) vs the unconditional floor's 3.5–4.0 TWh. λ: the caiso-63/66 probes' predicted +$0.30–0.46 regression did NOT materialize on the shipped base (caiso-70 vs caiso-69 A/B: LA_BASIN means 70.05/47.65/51.45 vs 70.18/47.82/51.26; 2023 tail 530→540 h); the residual C3a body miss remains attributed to the belly under-commitment gap (tz-correction FINDING §4.3), owned by G-15 — per the brief, the unconditional floor is NOT a fallback (phantom anchoring is a real defect). | docs/handoffs/caiso-ct-drag-d8-closure-2026-07.md §7–8; docs/handoffs/owner-decision-briefs-2026-07-08.md Decision 1; results/calibration/FINDING-caiso-seam-tz-correction-2026-07-07.md; registry `2026-07-07-caiso-63-g61b-startup.json` / `2026-07-07-caiso-64-g61c-curtail.json` / `2026-07-11-caiso-76-hydro-budget.json`; constants.CAISO_RA_MUSTOFFER_GAS_MW | B | blocks-claim (C1/C4 CC over-run) | (b) ADOPTED in keeper caiso-76 (owner decision 2026-07-11); residual belly grounding owned by G-15; (c) blocked on belly-commitment grounding, not the seam |"

BRIEF_ANCHOR = "## Decision 1 — G-61(b): adopt the CAISO startup-aware RA bridge (`caiso-66`)?\n\n**The mechanism.**"

BRIEF_NOTE = """> **RESOLVED — ADOPTED (owner decision, 2026-07-11).** Ship on the current keeper config
> (`2026-07-11-caiso-76-hydro-budget`), not the caiso-65 base. Executed by verification:
> the caiso-76 keeper already carries `caiso_ra_bridge_startup_aware=True` — it entered
> the line as caiso-70's pre-registered single delta (2026-07-10) and was carried through
> caiso-72 → 73 → 75 → 76, promoted to keeper 2026-07-11 (commit 295510c) with all three
> years and the zero-forcing ablation twin. The decision's requested replay is therefore
> config-identical to the keeper itself; no duplicate bundle was solved or registered.
> Mechanism engaged in the keeper (D-2 `ra_mustoffer_bridge` CC_REGULAR 2.38/2.26/1.73 TWh,
> C8 PASS). The predicted λ regression did not materialize on the shipped base (caiso-70 vs
> caiso-69 A/B: hub means ~unchanged, 2023 tail 530→540 h); the residual C3a body miss is
> attributed to the belly under-commitment gap (tz-correction FINDING §4.3 / G-15 lane) —
> the unconditional floor is not a fallback. Closure record: calibration-log 2026-07-11
> G-61(b) entry; gap-register G-61 row updated."""


def edit(path, old, new, marker):
    """Replace old with new in path unless marker already present."""
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    if marker in text:
        print(f"{path}: already applied - skipping")
        return
    if text.count(old) != 1:
        sys.exit(f"{path}: anchor not found exactly once ({text.count(old)}x)")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text.replace(old, new))
    print(f"{path}: applied")


def main():
    edit(
        LOG,
        LOG_ANCHOR,
        "## Runs\n\n" + LOG_ENTRY + LOG_ANCHOR[len("## Runs\n\n") :],
        "owner decision G-61(b) EXECUTED",
    )
    edit(
        REG,
        REG_OLD_TAIL,
        REG_NEW_TAIL,
        "(b) ADOPTED — OWNER DECISION G-61(b), 2026-07-11",
    )
    edit(
        BRIEF,
        BRIEF_ANCHOR,
        BRIEF_ANCHOR[: -len("**The mechanism.**")]
        + BRIEF_NOTE
        + "\n\n**The mechanism.**",
        "RESOLVED — ADOPTED (owner decision, 2026-07-11)",
    )


if __name__ == "__main__":
    main()
