#!/usr/bin/env python
"""One-shot server-side edit script for the NYISO C8 ST_GAS grounding.

Applies the four hand-edits of the change (D4_WINDOWS entry, calibration-log
entry, G-05 handoff addendum, attestation + registry-sidecar dated notes) as
anchored insertions/appends — run by .github/workflows/apply-nyiso-c8-files.yml
because the agent sandbox cannot `git push` (HTTP 413). Each edit is
idempotent (guarded on its own marker) and fails loudly if its anchor is
missing. The machine artifacts (nyiso-56 legitimacy_diagnostics.json,
status.js) are NOT edited here — the workflow regenerates them from source so
they stay CI-reproducible by construction.
"""

from __future__ import annotations

import json
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]

# --- 1. scripts/legitimacy_diagnostics.py: D4_WINDOWS entry -----------------

D4_ANCHOR = (
    "    # Midday NG:NG slab window (h9-16) — the probe's own gate\n"
    "    # (transmission.inject_caiso_gas_commitment_floor).\n"
    "    (MECH_CAISO_GAS_COMMITMENT_FLOOR, None): (9, 17),"
)
D4_BLOCK = """\
    # reliability_floor × ST_GAS: the driver-justified window is ALL 24 hours.
    # Live blast radius is NYISO-only: the NYC/LI persistent-24h base limbs
    # (reliability_floor_coeffs_NYISO.csv, threshold −50 °C ⇒ always flagged,
    # no sub-daily window) are the only ENABLED ST_GAS limbs a keeper's floor
    # still owns — PJM's enabled ST_GAS limbs are drag-owned in its keeper
    # (gas_st_netload_drag drops them via iso_configs.
    # drop_drag_owned_reliability_specs) and every other ISO's are disabled.
    # Evidence base (G-05 adjudication, docs/handoffs/g05-forced-energy-caiso-
    # ct-nyiso-stgas-2026-07.md): measured CAMPD 2023-25 downstate steam is
    # online 100 % of the year with overnight CF 0.11-0.20 — there is NO hour
    # the class's own driver evidence says it is offline (the opposite of the
    # CT overnight-offline signature), so the persistent base binds nowhere
    # off-window by measurement; D-1 diurnal shape passes every year (profile
    # r 0.95-0.96, cv_ratio 0.69-0.90). The all-hours gas_st_netload_drag
    # alternative (the ERCOT-46/PJM-94 keeper mechanism, which post-dates
    # G-05's windowed-[15,22) rejection premise) was re-evaluated 2026-07-09
    # and REJECTED on its own honesty gates
    # (scripts/derive_nyiso_st_gas_netload_drag.py): the downstate base is
    # flat vs net-load below ~15 GW and its level drifts across years at
    # equal net-load (overnight Spearman rho 0.32/0.39/0.72 class-wide,
    # 0.30/0.28/0.57 NYC+LI-only — not year-stable), and the pooled hinge
    # overshoots the 2023 measured class energy (142 %). The commitment is an
    # UNCONDITIONAL local-reliability base (downstate DARU/SRE commitments +
    # steam-boiler min-run blocks), not a net-load-hinged one, so the
    # persistent reliability_floor remains the class's single grounded
    # mechanism (rule 19) and this row exists so rubric-v2.2 over-budget
    # escalation scores it on evidence rather than failing it for a missing
    # declaration (rule 12).
    (MECH_RELIABILITY_FLOOR, "ST_GAS"): (0, 24),
"""


def edit_d4_windows() -> None:
    """Insert the reliability_floor × ST_GAS window before the CAISO row."""
    p = REPO / "scripts" / "legitimacy_diagnostics.py"
    text = p.read_text()
    if '(MECH_RELIABILITY_FLOOR, "ST_GAS"): (0, 24)' in text:
        print("D4_WINDOWS: already applied, skipping")
        return
    assert D4_ANCHOR in text, "D4 anchor not found in legitimacy_diagnostics.py"
    p.write_text(text.replace(D4_ANCHOR, D4_BLOCK + D4_ANCHOR, 1))
    print("D4_WINDOWS: inserted")


# --- 2. docs/calibration-log.md: session entry (append) ---------------------

LOG_HEADER = (
    "## 2026-07-09 — NYISO C8 ST_GAS protective caveat CLEARED via rubric-v2.2 "
    "grounding (scorer-only; keeper stays nyiso-56); all-hours "
    "`gas_st_netload_drag` re-adjudicated for NYISO and REJECTED on its own "
    "honesty gates"
)
LOG_ENTRY = f"""
{LOG_HEADER}

**Trigger.** The nyiso-56 keeper's one protective caveat was C8 ST_GAS: "above
the 30% cap and NOT grounded … no declared D-4 window: reliability_floor" — a
provenance gap, not a shape miss (D-1 passes r 0.95–0.96 / cv_ratio 0.69–1.04
every year). Rubric v2.2's grounded-above-budget escalation (rule 19) names
the fix: a cited `D4_WINDOWS` entry + bundle regen, no re-solve.

**Drag re-adjudication (the G-05 stale premise).** G-05 rejected switching
NYISO ST_GAS onto `gas_st_netload_drag` when the drag was windowed [15,22);
the ERCOT-46/PJM-94 keepers have since made it ALL-HOURS — worth re-testing.
Built `scripts/derive_nyiso_st_gas_netload_drag.py` (PJM-construction-
faithful: EIA-930 NYIS net-load, CAMPD overnight CF of the 7 pure-play
6.38-GW ST_GAS plant set, hinge fit). It FAILS its own pre-registered honesty
gates: overnight Spearman rho 0.32/0.39/0.72 class-wide (0.30/0.28/0.57
NYC+LI-only) — not year-stable; binned overnight CF FLAT vs net-load below
~15 GW with the base level drifting across years at equal net-load (11 GW:
0.087→0.140→0.136); pooled hinge overshoots 2023 measured class energy
(142%). The downstate commitment is an UNCONDITIONAL local-reliability base
(DARU/SRE + boiler min-run), not net-load-hinged — the drag is the wrong
driver for NYISO (rule 1: no run attempted with a mechanism the measurement
rejects). G-05's mechanism choice stands on measured grounds that no longer
depend on the stale window premise; dated addendum appended to the G-05
handoff.

**Grounding applied.** `D4_WINDOWS[(MECH_RELIABILITY_FLOOR, "ST_GAS")] =
(0, 24)` with the G-05 evidence cited in place (NYC/LI steam online 100% of
year, overnight CF 0.11–0.20 — no hour the class's own driver evidence says
it is offline; same construction as the (MECH_ST_NETLOAD_DRAG, None) row).
Live blast radius NYISO-only (PJM's enabled ST_GAS limbs are drag-owned in
its keeper and dropped; all other ISOs' are disabled). nyiso-56's committed
`legitimacy_diagnostics.json` regenerated (payload path, the CI-reproducible
convention) — this also refreshed the D-2 denominators onto the HEAD CHP
re-classing (ST_GAS class total 10.4/10.9/13.3 → 8.0/8.6/10.6 TWh; forced
share 30.5/44.6/38.2% → 36.4/53.8/44.8%), curing a latent G-06 staleness the
07-07 artifact had accrued. New D-4 rows: `reliability_floor × ST_GAS`
off-window 0.0% all years, PASS.

**Result (build_status).** C8 → clean PASS, classified GROUNDED ABOVE BUDGET
all three years, surfaced as report notes (never a caveat, per the owner
amendment); protective caveat bucket now EMPTY; grade summary 7→8
target-grade, ledgered 2→1. Determination stays CALIBRATED-WITH-CAVEATS on
the two remaining non-protective caveats: ledgered C3c (DA-expressible tail;
#1344 Ask-B + Iroquois Ask-C data-blocked) and commercial-band C5a CO2 2024
(−7.3%). Those are data-ask-gated, not forced-floor items. Attestation
`forced_share` exceptions retired with a dated note; registry sidecar
definition appended. Keeper unchanged; no solve run; LOYO n/a (no mechanism
change — scorer-only declaration per rule 19).

**Holdouts.** No solve/score/intake anywhere (scorer-only session); rule 22
untouched.
"""


def edit_calibration_log() -> None:
    """Append the session entry to docs/calibration-log.md."""
    p = REPO / "docs" / "calibration-log.md"
    text = p.read_text()
    if LOG_HEADER in text:
        print("calibration-log: already applied, skipping")
        return
    p.write_text(text + LOG_ENTRY)
    print("calibration-log: appended")


# --- 3. docs/handoffs/g05-…md: dated addendum (append) ----------------------

G05_HEADER = (
    "## Addendum 2026-07-09 — ST_GAS grounded under rubric v2.2 "
    "(drag re-adjudicated, rejected again)"
)
G05_ADDENDUM = f"""
{G05_HEADER}

Two things changed after this memo was written: (a) rubric v2.2 added the
grounded-above-budget C8 escalation (above-cap passes iff every binding
mechanism clears a **declared** D-4 window and D-1 shape clears), under which
the nyiso-56 keeper's ST_GAS scored "above cap, NOT grounded — **no declared
D-4 window: reliability_floor**" (a provenance gap, not a shape miss — D-1
passes r 0.95-0.96 / cv_ratio 0.69-0.90 every year); and (b) the
`gas_st_netload_drag` this memo rejected on its **windowed [15,22)** premise
became ALL-HOURS (`ramp_window=None`, the ERCOT-46 / PJM-94 keeper mechanism),
making that premise stale and the drag worth re-testing as an all-hours base
whose level flexes with net-load.

**Re-adjudication result: the drag is rejected again, now on measurement.**
`scripts/derive_nyiso_st_gas_netload_drag.py` (new, PJM-construction-faithful:
EIA-930 NYIS net-load, CAMPD overnight CF, hinge fit) fails its own
pre-registered honesty gates: overnight Spearman rho 0.32/0.39/0.72
(class-wide) and 0.30/0.28/0.57 (NYC+LI-only) — not year-stable; the binned
overnight CF is FLAT vs net-load below ~15 GW (a base, not a hinge) with the
base level drifting up across years at equal net-load (11 GW: 0.087 → 0.140 →
0.136); and the pooled hinge overshoots the 2023 measured class energy
(142 %). The downstate commitment is an **unconditional** local-reliability
base (DARU/SRE + boiler min-run blocks), not net-load-hinged — so this memo's
mechanism choice stands: the persistent-24h `reliability_floor` remains the
class's single grounded mechanism (rule 19), for a measured reason that no
longer depends on the stale window premise.

**Deliverable (same pattern as the CT_PEAKER window fix above):**
`D4_WINDOWS[(reliability_floor, ST_GAS)]` → (0, 24), citing this memo's
measured table (NYC/LI online 100 % of year, overnight CF 0.11-0.20 — no hour
the driver evidence says the class is offline) plus the drag-rejection
derivation; nyiso-56's committed `legitimacy_diagnostics.json` regenerated
(payload path) so the D-4 row exists; status rebuilt. Under rubric v2.2 the
C8 ST_GAS protective caveat escalates to **GROUNDED ABOVE BUDGET — a clean
PASS surfaced as a report note**. Blast radius NYISO-only (PJM's enabled
ST_GAS limbs are drag-owned in its keeper and dropped; every other ISO's are
disabled). Scorer-only: no re-solve, no mechanism change, keeper stays
nyiso-56.
"""


def edit_g05_handoff() -> None:
    """Append the dated addendum to the G-05 handoff memo."""
    p = REPO / "docs" / "handoffs" / "g05-forced-energy-caiso-ct-nyiso-stgas-2026-07.md"
    text = p.read_text()
    if G05_HEADER in text:
        print("G-05 handoff: already applied, skipping")
        return
    p.write_text(text + G05_ADDENDUM)
    print("G-05 handoff: appended")


# --- 4. attestation + registry sidecar: dated notes --------------------------

GROUND = (
    " [2026-07-09 UPDATE — GROUNDED, exception retired: under rubric v2.2 the "
    "above-cap ST_GAS forcing now escalates to a clean PASS (GROUNDED ABOVE "
    "BUDGET): D4_WINDOWS gained the cited (reliability_floor, ST_GAS) = (0,24) "
    "window (G-05 measured evidence — NYC/LI steam online 100% of year, "
    "overnight CF 0.11-0.20, no hour the driver evidence says the class is "
    "offline) and the bundle's legitimacy_diagnostics.json was regenerated "
    "(payload path) so the D-4 row exists; D-1 shape already passed (r "
    "0.95-0.96). The all-hours gas_st_netload_drag alternative was "
    "re-adjudicated and REJECTED on its own honesty gates "
    "(scripts/derive_nyiso_st_gas_netload_drag.py: rho not year-stable, base "
    "flat vs net-load, 2023 energy overshoot 142%) — the persistent "
    "reliability_floor stays the class's single mechanism (rule 19). "
    "Scorer-only; no re-solve; see the G-05 handoff 2026-07-09 addendum. "
    "Regenerated D-2 shares are 36.4/53.8/44.8% on the HEAD CHP-re-classed "
    "denominators (class total 8.0/8.6/10.6 TWh).]"
)

SIDECAR_NOTE = (
    " || 2026-07-09: C8 ST_GAS protective caveat CLEARED — grounded under "
    "rubric v2.2 (GROUNDED ABOVE BUDGET, clean PASS all years). "
    "D4_WINDOWS[(reliability_floor, ST_GAS)] = (0,24) declared with the G-05 "
    "measured evidence; diagnostics regenerated at HEAD (CHP re-class "
    "refreshed the D-2 denominators: ST_GAS 36.4/53.8/44.8% forced of "
    "8.0/8.6/10.6 TWh class). The all-hours gas_st_netload_drag (ERCOT-46/"
    "PJM-94 mechanism) was re-adjudicated for NYISO and rejected on its own "
    "honesty gates (derive_nyiso_st_gas_netload_drag.py — downstate base is "
    "unconditional local-reliability commitment, not net-load-hinged). "
    "No re-solve; keeper unchanged. Remaining caveats: ledgered C3c "
    "(DA-expressible tail, #1344 data-blocked) + commercial-band C5a CO2 2024."
)


def edit_attestation() -> None:
    """Retire the three forced_share exceptions with the dated grounding note."""
    p = (
        REPO
        / "results"
        / "calibration"
        / "nyiso56_measuredshares"
        / "calibration_attestation.json"
    )
    d = json.load(open(p))
    n = 0
    for e in d["exceptions"]:
        if e["criterion"] == "forced_share":
            if "[2026-07-09 UPDATE" in e.get("reason", ""):
                continue
            e["reason"] = e.get("reason", "") + GROUND
            n += 1
    if n:
        json.dump(d, open(p, "w"), indent=1)
    print(f"attestation: {n} forced_share exceptions updated")


def edit_sidecar() -> None:
    """Append the dated grounding note to the keeper's registry definition."""
    p = (
        REPO
        / "frontend"
        / "data"
        / "backcast"
        / "registry"
        / "2026-07-07-nyiso-56-measured-zonal.json"
    )
    d = json.load(open(p))
    if "2026-07-09: C8 ST_GAS protective caveat CLEARED" in d["definition"]:
        print("sidecar: already applied, skipping")
        return
    d["definition"] += SIDECAR_NOTE
    json.dump(d, open(p, "w"), indent=1)
    print("sidecar: appended")


if __name__ == "__main__":
    edit_d4_windows()
    edit_calibration_log()
    edit_g05_handoff()
    edit_attestation()
    edit_sidecar()
