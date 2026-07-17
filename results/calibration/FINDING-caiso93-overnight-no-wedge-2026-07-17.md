# FINDING (caiso-93): the overnight no-wedge admissibility gate PASSES — the measured overnight (hod 0-5) CAISO−PaloVerde spread carries NO carbon wedge — and SHARPENS the lane: the no-wedge state is UNCONDITIONAL overnight, the caiso-87 hub-state trigger is coverage-starved there, and the admissible construction is an hod-scoped clean depth whose frozen estimation gates PASS; NO build this session (owner authorization required)

**Session 2026-07-17 (CC-overnight lane, import-side redirect — the
FINDING-caiso92b §6 precondition). Derive-first, NO LP solved; keeper
unchanged (caiso-92); nothing registered. Scripts:
`scripts/derive_caiso_overnight_wedge.py` (the pre-registered gate) +
`scripts/derive_caiso_overnight_clean_depth.py` (the post-hoc companion,
sequencing disclosed below). Data: committed loaders only —
`wecc_intertie_lmp_hourly_CAISO.parquet` (PALOVRDE DA), EIA-930 CISO DIBAs
via `derive_caiso_import_tranches.corridor_net_import`,
`pge_socal_citygate_weekly.csv` via `fuel.socal_citygate_weekly_hourly`,
`actual_lmp_hourly_CAISO.parquet` (DA+RT).**

## 1. The question and the pre-registered gate

FINDING-caiso92b established that the overnight (hod 0-5) CC over-run
(+1.39/+2.11/+2.61 TWh) ≈ the import under-run (−1.36/−1.70/−3.03 TWh) and
chartered the import-side redirect on one load-bearing admissibility gate:
**does the MEASURED overnight CAISO−hub spread show NO carbon wedge in
overnight surplus-West hours, for the DSW/Palo Verde SOUTH corridor
specifically?** If the overnight DSW is fossil-marginal-with-wedge, the
model's +$12–15 unspecified-import CARB rung is CORRECT overnight and the
redirect is wrong.

Gate design (frozen in the script docstring before results were seen; every
leg inherited from a COMMITTED construction, sliced to hod 0-5 — the
caiso-86b "don't tune the method to the gate" prohibition):

- **trigger** (caiso-87, `inject_caiso_dsw_surplus_clean`):
  `PALOVRDE < 6.97 × SoCal_citygate_weekly + $2.5`, measured hub hours only.
- **spread** (caiso-82 §1 parity, `DSW_CCGT` delivery basis):
  `actual − (PALOVRDE × 1.03 + $4)`; DA gated (basis-matched to the DA hub
  series), RT reported. Wedge reference = 0.428 × CARB allowance =
  $14.1/$15.1/$12.0 (2023/24/25).
- **G1 no-wedge:** per-year overnight trigger-ON median DA spread ≤ +$4 (the
  top of the caiso-82 §1 measured parity band). **G2** depth CV ≤ 0.20;
  **G3** depth LOYO ≤ 25% (p95 DSW net import over overnight trigger-ON
  hours; the caiso-88 template).

*Implementation-bug disclosure:* the first execution mis-implemented parity
as `PV × 0.03 + 4` (the delivery-basis tuple's loss FRACTION used as the
multiplier), printing nonsense +$40 spreads; the code was corrected to the
docstring's stated `× 1.03 + $4` construction and re-run. The fix aligned
the code to the pre-registered construction — no gate or threshold moved.

## 2. Gate results — ALL PASS

| year | ON share of overnight | ON median DA spread [p25,p75] | parity-consistent (≤+4) | wedge-consistent (≥wedge−2) | G1 |
|---|---|---|---|---|---|
| 2023 | 26.4% (443 h) | **−4.8** [−6.6, −1.6] | 90.1% | 3.2% | PASS |
| 2024 | 1.2% (27 h) | **−4.5** [−4.6, −4.4] | 100.0% | 0.0% | PASS |
| 2025 | 3.6% (78 h) | **−4.8** [−5.0, −4.5] | 98.7% | 0.0% | PASS |

RT spreads are the same story (−8.8/−5.0/−6.7 ON medians). G2 CV = 0.093
PASS; G3 LOYO worst 17.3% PASS (ON-conditioned depths 6,158/5,929/7,305 MW).
**The formal precondition answer is YES — the redirect is admissible.**

## 3. The load-bearing refinement: the no-wedge state overnight is UNCONDITIONAL — the trigger, not the wedge, is what fails overnight

The trigger-OFF rows carry the real discovery. The spread sits at parity in
the 96–99% of overnight hours where the caiso-87 trigger does NOT fire, too
(OFF medians DA −4.7/−4.5/−5.2), with 4.6/4.6/4.8 GW of measured DSW flow.
Unconditional overnight spread (ALL overnight measured-hub hours):

| year | DA med [p25,p75] | ≤+4 share | ≥wedge−2 share | RT med |
|---|---|---|---|---|
| 2023 | −4.7 [−6.3, −3.0] | 92.9% | 2.2% | −7.3 |
| 2024 | −4.5 [−5.4, −3.6] | 98.2% | 0.1% | −5.9 |
| 2025 | −5.1 [−6.3, −4.4] | 98.7% | 0.0% | −7.1 |

CAISO clears overnight at ≈ the RAW Palo Verde hub price (the ~$4.7 discount
to delivered parity ≈ the ×1.03+$4 wheel itself) — essentially EVERY
overnight hour, all three years, both bases. Three consequences:

1. **The handoff's dichotomy was a false dichotomy.** The overnight DSW hub
   IS fossil-marginal (PV sits at/above its remote-CCGT gas floor 96–99% of
   2024/25 overnight hours) AND the transfer into CAISO is un-wedged anyway.
   What is marginal AT the hub and how the WEIM/EDAM GHG attribution assigns
   resources to the CAISO transfer are different axes: overnight the West
   carries surplus non-emitting supply (NW hydro + wind — the PNW hub's
   negative overnight prints) and the attribution assigns it to CAISO
   transfers, so the marginal import pays no border carbon even while gas
   sets the HUB price. A carbon-paying marginal import (specified CCGT
   ≈ 0.37 × allowance ≈ $12–13, unspecified 0.428 × ≈ $12–15) would print a
   spread the measured record shows in ≤3% of overnight hours.
2. **A caiso-87-trigger-conditioned overnight extension is coverage-starved
   by construction.** ON = 27/78 overnight hours in 2024/25 against a
   2,190-hour, +2.1/+2.6 TWh over-run window — the conditional variant
   cannot carry the phenomenon regardless of its (passing) depth gates. The
   2023 26.4% ON share is the known SoCal-citygate misalignment (rule-14
   documented): the 2023 gas spike inflates the floor, classifying
   ordinary-priced hub hours as "surplus" — the caiso-88 misalignment
   signature. Iterating alternative gas series is pointless AND would be
   gate-shopping: the state test itself is the wrong axis overnight, because
   the measured no-wedge state is unconditional in-sample.
3. **The admissible construction is hod-scoped, not hub-state-scoped.** The
   overnight clean-transfer state is persistent market structure (like the
   firm blocks), not a price-triggered event.

## 4. The unconditional overnight clean depth — frozen gates PASS

`derive_caiso_overnight_clean_depth.py` — **disclosed sequencing:** this
construction was identified AFTER the §3 ON/OFF contrast was seen (not
pre-registered). What is frozen and NOT iterated: the gate thresholds
(CV ≤ 0.20, LOYO ≤ 25%), the depth statistic (p95, caiso-87's), the corridor
series (EIA-930 CISO DIBAs), and the hod 0-5 window (fixed by
FINDING-caiso91c/92b before any spread was measured).

    depth[y] = p95 of measured WECC_DSW net import over ALL overnight hours
    2023: 5,870 MW   2024: 6,205 MW   2025: 6,487 MW
    CV 0.041 (≤0.20 PASS); LOYO worst 8.1% (≤25% PASS)

Tighter than the promoted caiso-87 midday depth's own gates (CV 0.056, LOYO
12.5%). Overnight means are 4.5/4.6/4.9 GW — reality runs the south corridor
hard every night; the measured levels rise monotonically toward 2025,
matching the −1.4→−3.0 TWh import under-run trend.

## 5. What a build would be (NOT built — owner authorization required)

The caiso-87 injector pattern with an overnight leg: a zero-EF
`DSW_surplus_clean`-class capability whose hourly cap is
`overnight[t] × max(0, depth_ov[year] − firm_south_capability[t])`, priced
off the measured PV hub by the existing per-hub injector, P1-native, pmin 0
(capability, not a floor — no D-2 row), corridor ATC envelope still caps
delivered flow, fossil rungs unchanged beyond the clean depth. Zero fitted
scalars: measured depth + published attribution structure + an hod window
fixed upstream by the phenomenon's own charter. Expected direction: the LP
substitutes ~hub-parity imports for wedge-parity CC overnight → the CC
over-run closes ECONOMICALLY and overnight λ falls toward actual — one
structural fix, both symptoms (rule 19).

**Disclosed build questions (owner decides at authorization):**

- **Pricing basis of the overnight leg.** The measured overnight clear is
  ≈ RAW hub (spread ≈ −$4.7 vs delivered parity): WEIM/EDAM transfers do not
  pay the Path-46 wheel the scheduled-import delivery basis carries. Keeping
  caiso-87's (×1.03, +$4) basis leaves the mechanism ~$4–5 above the
  measured overnight clearing level (may under-close the +3.4/+3.6 legs);
  pricing the leg at raw hub is more faithful to the measured transfer
  economics but diverges from the existing tranche's basis — needs its own
  short doc trail either way.
- **C2 gas-sign risk (the principal probe gate).** Displacing +1.4/+2.1/+2.6
  TWh of overnight CC pushes total model gas DOWN; CAISO C2-2025 already
  reads −2.3% (caiso-87 log). The caiso-87 session's identical disclosed
  tension did NOT materialize at ~⅓ this magnitude; at full magnitude it
  may. If the structure is right and C2 flips, that exposes the OTHER half
  of the C1 cluster (CT_PEAKER/CHP under-runs), not a reason to bury the
  import fix (rules 1/14) — but it is the probe's headline risk.
- **2024 overshoot watch.** The 2024 overnight over-price is only +1.8;
  a full reprice to hub parity could push 2024 overnight λ slightly UNDER.
- **Scope guards (per FINDING-caiso92b):** hod 0-5 only; the caiso-87 midday
  trigger and depth are UNTOUCHED; belly (hod 10-14) and evening untouched
  by construction; the CLOSED autumn-2025 lane is not reopened (this is an
  hod-window mechanism, not an autumn mechanism — autumn OVERNIGHT hours are
  covered exactly like every other night; Sep–Dec-2025 stay WATCH months in
  the probe report-back, along with C3a 2024/2025 +10.4/+14.3 must-not-
  inflate and Feb-2023/Apr-2023/Jan-2024).
- **Measured p95 depth (5.9–6.5 GW) sits near/above the corridor's ~5.2 GW
  median ATC envelope** — the envelope still caps delivered flow, so part of
  the depth may be envelope-clipped in some hours; report the binding split
  in the probe.

## 6. Disposition

- **Precondition: PASSED — the import-side redirect is admissible.** The
  measured overnight CAISO−hub spread shows NO carbon wedge (pre-registered
  G1/G2/G3 all PASS), and the sharpened form: the no-wedge state is
  unconditional overnight, with a year-stable unconditional clean depth
  (CV 0.041, LOYO ≤8.1%).
- **Do NOT redo:** the caiso-87-trigger-conditioned overnight extension
  (coverage-refuted §3); alternative gas-series overnight hub-state triggers
  (wrong axis §3); everything already on the FINDING-caiso92b do-not-redo
  list.
- **NO build, NO solve this session.** Lever build authorization is the
  owner's (RUN DISCIPLINE); the evidence above is the ask. If authorized,
  the probe is a `_caiso92_measured_offer_surface_ab.py` clone (A-leg
  `_caiso92_repro_A.py`) + the single overnight-depth delta, 2023+2024+2025
  one invocation, report-back per the FINDING-caiso92b charter (C1 grid, hod
  λ ladder with the overnight leg +3.4/+1.8/+3.6 required to CLOSE, the
  who-serves-the-night re-run with imports RISING toward measured, C3c DA
  counts, C3a 2024/2025, C2 gas sign, WATCH months, C5a/C6, determination).
