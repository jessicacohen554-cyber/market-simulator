# FINDING — caiso-117 LEG 1 EXECUTED: the belly-hour West import cap is structurally correct and fixes the belly VOLUME (import → toward measured, gas +1.9/+2.9/+2.3 TWh across 2023-25, C5a improves) while keeping C3b/C3c intact — but as a STANDALONE single delta it BREAKS C3a in 2025 (+8.6% → +13.2%, over the ±10% gate) by worsening the model's pre-existing belly PRICE over-pricing (gas marginal ~$28 in the belly vs actual solar-marginal ~$15); the belly-volume and belly-price lanes are COUPLED (not, as the handoff feared, belly-volume vs the evening), so the cap cannot be promoted alone — keeper `2026-07-19-caiso-102-hourfix` UNCHANGED; mechanism built + unit-tested + default-OFF for when the belly price-formation defect is co-fixed (2026-07-24)

**Derive-first gate cleared, mechanism built + 6/6 unit tests + full 3-year A/B
solved on this machine, nothing registered as a keeper.** Keeper
`2026-07-19-caiso-102-hourfix` UNCHANGED (NOT-YET, fail {C3c, C4, C5a}). This
session executed the handoff's LEG-1 belly (C5a) lane: one pre-registered single
delta — a belly-hour-scoped import cap at the WEST's measured net-export
capability (`wecc-west-supply`, a West-side physical quantity — rule 13, NOT a
CA-side flow observable). The derive gates cleared cleanly; the solve revealed a
price-side coupling the volume-only derive could not see.

---

## Headline

The belly cap does **exactly** what it was designed to do on **volume**, and the
handoff's fear (that a belly-volume fix would leak into the evening and break
C3a, the caiso-114 L1b failure mode) is **refuted** — the evening is untouched
by construction (`np.inf` cap outside hod 10-15; evening price moves +$0.8/MWh).
But a **different** coupling surfaced: capping the cheap belly imports forces
more belly **gas**, which raises the belly **price**, and because the model
**already over-prices the belly** (gas is marginal at ~$26-30 where the actual
market clears solar at ~$14-15), the cap pushes **C3a over its ±10% gate in
2025** (the one year whose baseline C3a, +8.6%, already sat near the edge). The
belly-VOLUME lane (C5a) and the belly-PRICE lane (C3a) are **coupled** — so a
belly-volume cap cannot be a standalone keeper. This sharpens the caiso-116
redirect: the clean belly path is not "cap the volume in isolation"; it is
"cap the volume **and** fix the belly price formation (marginal supply) jointly."

---

## Inv 1 — the derive gates (pre-registered, cleared before any solve)

`scripts/probes/_caiso117_belly_cap_derive.py` (no LP). Cap CAISO's total belly
(hod 10-15) import at the per-(month × belly-hod) **p90 of the West's measured
net export** (`wecc-west-supply` `net_export_mw`):

| year | West p90 belly cap | current corridor p95 cap | CA measured belly import |
|---|---|---|---|
| 2023 | 2.15 GW | 3.90 GW | 0.65 GW |
| 2024 | 2.17 GW | 4.26 GW | 1.34 GW |
| 2025 | 1.95 GW | 4.41 GW | 1.77 GW |

- **GATE-A (binds):** the West p90 cap (~2 GW) is well below the loose corridor
  p95 ceiling (~4 GW summed) every year → it tightens and cuts the over-import.
- **GATE-B (no over-correct):** the cap is ≥ CA's measured belly import every
  year → it never forces import below the real level. p90 is the *tightest*
  percentile that clears GATE-B for all three years (p75 under-cuts 2024/25).

A refinement the derive exposed: in peak-summer belly hours the West's own AC
load collapses its net export to ~0, so the cap is applied **only where the West
is demonstrably long** (p90 > 0), leaving those hours uncapped rather than
forcing import to 0 and over-correcting (86 % / 100 % / 93 % of belly hours
capped 2023/24/25).

## Inv 2 — the mechanism (built, unit-tested, default-OFF)

`caiso_belly_import_cap` (ScenarioConfig, default False). A belly-scoped
**simultaneous** interface group over BOTH per-hub corridor links, capped hour by
hour at `measured_west_belly_export_cap` (`np.inf` outside the belly, so the
evening is untouched — C3a preserved *by construction* from the evening side).
Constants `CAISO_BELLY_HOURS` (10-15), `CAISO_BELLY_EXPORT_PERCENTILE` (90).
6/6 unit tests pass (`tests/test_caiso_belly_import_cap.py`); existing corridor
tests green; the diff is purely additive and byte-identical off the flag (the
keeper replays digit-for-digit). Solved on this machine via
`scripts/replay_keeper.py … --set caiso_belly_import_cap=true`.

## Inv 3 — the full 3-year A/B (fresh same-machine baseline A = keeper replay)

Scored with `scripts/probes/_score_probe.py` (the calibration_verdict C3a/C3b/C3c
formulas on the committed CAISO bench); belly import + gas from the per-plant
dispatch. **A = belly cap OFF (keeper), B = belly cap ON.**

| year | belly import A→B (measured) | gas TWh A→B | C3a A→B (±10%) | C3b NRMSE A→B (≤0.20) | C3c >$200 A→B (actual) |
|---|---|---|---|---|---|
| 2023 | 3.07 → **2.05** (0.65) | 61.1 → **63.0** | +4.1% → +6.3% **PASS** | 0.068 → 0.089 PASS | 19 → 25 h (80) |
| 2024 | 3.88 → **2.44** (1.34) | 54.8 → **57.7** | +5.5% → +8.7% **PASS** | 0.110 → 0.122 PASS | 0 → 0 h (52) |
| 2025 | 3.74 → **2.22** (1.77) | 47.0 → **49.3** | +8.6% → **+13.2% FAIL** | 0.134 → 0.167 PASS | 0 → 0 h (0) |

Reading:
1. **Belly volume (C5a) — fixed as designed.** Belly import drops ~1.0-1.5 GW
   toward measured every year, never below it (GATE-B holds in the solve); gas
   rises +1.9 / +2.9 / +2.3 TWh, shrinking the gas under-generation that is C5a.
   (The absolute C5a-% needs the BTM-aware CO2 scorer — the model's grid gas
   excludes held-out CHP — but the A→B gas **delta** is BTM-invariant and
   unambiguously reduces the deficit.)
2. **Evening (the handoff's C3a fear) — untouched.** Evening import moves +0.02
   GW, evening price +$0.8/MWh. The L1b evening-over-price failure mode does NOT
   recur; the `np.inf`-outside-belly scoping works.
3. **C3b / C3c — intact.** C3b degrades within tolerance every year (belly
   over-pricing, below); C3c is unchanged (2024/25) or slightly better (2023
   19→25 h toward actual 80). Neither breaks.
4. **C3a — breaks in 2025.** The cap raises annual mean LMP by +2 to +4.6 pp
   (all from the belly). 2023 (+4.1 base) and 2024 (+5.5 base) absorb it; 2025,
   whose baseline C3a already sat at +8.6 %, is pushed to **+13.2 %, over the
   ±10 % gate**.

## Inv 4 — why C3a breaks: the belly is PRICE-over-priced, and the cap worsens it

Model vs actual (DAM, hub-avg, Pacific) intraday price, 2024:

| block | actual | model A (off) | model B (cap) |
|---|---|---|---|
| belly (10-15) | **$14.9** | $26.3 (+77 %) | **$29.6 (+99 %)** |
| evening (17-21) | $54.4 | $43.7 (−20 %) | $44.5 (−18 %) |

The model **compresses** the price distribution — belly far too high, evening
too low (the C3c tail defect). The belly is over-priced **even with** the cheap
imports flooding it: the per-hub intertie prices imports at the measured hub
(~$26 in the belly), so the model's belly marginal unit is a hub-priced import,
not the curtailed solar (~$0-15) that clears the real belly. Capping the imports
forces the next unit — **gas at ~$28** — to the margin, pushing the belly higher
still ($26 → $30). So the belly cap does not *cause* the belly over-pricing; it
**exposes and worsens** a pre-existing belly price-formation defect (the model
lacks cheap marginal supply — curtailable solar / a belly-cheap import — at the
midday margin). This is the rule-#1 signature: a structurally-correct mechanism
makes the fit worse by surfacing a *different* root cause.

## Decision framing

**The belly cap is structurally correct and stays as built (default-OFF).** It is
a West-side physical capability ceiling (rule 13), it fixes the belly volume
(C5a) as designed, and it does not leak into the evening. It is **not promoted**
because as a standalone single delta it breaks C3a in 2025 — and per rule #1 the
fix is NOT to revert the real mechanism but to address the exposed root cause:
the belly **price formation**. The keeper stays `2026-07-19-caiso-102-hourfix`
(byte-identical; the flag is default-off).

**What this changes about the lane (vs the caiso-116 handoff).** The handoff
framed the risk as belly-volume vs the *evening* (C3a broken by an evening
over-price, the L1b mode). This session refutes that: the belly cap keeps the
evening clean and breaks C3a from the **belly** instead. The real coupling is
**belly-volume ↔ belly-price**: you cannot cap the belly import without also
addressing why the model prices the belly ~$12-15 too high. The clean belly lane
is therefore a **joint** delta — the West-physical volume cap (this mechanism)
**plus** a belly price-formation fix that puts cheap curtailable solar (or a
belly-cheap import rung) at the midday margin so the belly clears near its actual
~$15, not gas at ~$28.

### Redirect (caiso-118+)

1. **Belly price-formation fix (the new load-bearing lane).** Give the model
   cheap marginal supply in the belly so gas is not the midday marginal unit:
   curtailable solar offered at ~$0 as the belly marginal rung, and/or the
   per-hub belly import priced at the *actual* low belly hub rather than the
   annual hub basis. Then re-arm `caiso_belly_import_cap`: with the belly
   clearing near actual (~$15), capping the volume no longer inflates C3a, and
   the belly-volume (C5a) + belly-price (C3a) fix jointly. This is the honest
   path and the prerequisite for a belly keeper.
2. **Only after the belly clears correctly** do LEG 2 (evening scarcity, C3c)
   and LEG 3 (net-rev keeper) become admissible — the net-rev form compresses
   the tail, so it needs both ends (belly AND evening) priced right first.

## DO-NOT-REDO (added this session)

- **The belly cap as a STANDALONE single delta** — breaks C3a in 2025 (+13.2 %)
  by worsening belly over-pricing (Inv 3-4). Re-arm it only *jointly* with a
  belly price-formation fix (redirect #1). The mechanism itself is correct and
  stays built (default-off); do not re-derive it.
- **Tightening the CA-side corridor p95 envelope to fix the belly** — that is a
  CA-side flow observable (rule 13 / caiso-107/109 kills). The West-side p90 cap
  is the admissible form and is already built.

Full reproduction: `scripts/probes/_caiso117_belly_cap_derive.py` (derive) +
`scripts/replay_keeper.py results/calibration/caiso102_hourfix_B --set
caiso_belly_import_cap=true --years <Y>` (solve) +
`scripts/probes/_score_probe.py <bundle>` (score).
