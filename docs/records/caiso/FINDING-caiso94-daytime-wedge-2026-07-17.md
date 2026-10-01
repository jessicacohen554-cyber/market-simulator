# FINDING (caiso-94): the DAYTIME no-wedge admissibility gate PASSES — the measured no-wedge structure that admitted caiso-93 OVERNIGHT extends to the daytime trigger-OFF hours — and RESOLVES the C3a-2025 charter's fork: an admissible caiso-93-style clean-import extension exists on the AUTUMN daytime trigger-OFF hours (morning ramp + evening peak, the load-bearing cells), the belly-midday over-price mass is caiso-87/battery territory (off-limits / separate storage charter), and the gate proves ADMISSIBILITY ONLY — a diagnostic solve is required to settle inertness/overshoot; NO build this session (owner authorization required)

**Session 2026-07-17 (C3a-2025 daytime lane — the caiso-93 promotion handoff's
next charter). Derive-first, NO LP solved; keeper unchanged
(caiso-93); nothing registered. Scripts:
`scripts/derive_caiso_daytime_wedge.py` (the pre-registered daytime gate,
cloned from the frozen `derive_caiso_overnight_wedge.py`) +
`scripts/derive_caiso_daytime_finegrain.py` (the post-hoc fine-grain
companion, sequencing disclosed §4). Data: committed loaders only —
`wecc_intertie_lmp_hourly_CAISO.parquet` (PALOVRDE DA), EIA-930 CISO DIBAs via
`derive_caiso_import_tranches.corridor_net_import`, `pge_socal_citygate_weekly.csv`
via `fuel.socal_citygate_weekly_hourly`, `actual_lmp_hourly_CAISO.parquet`
(DA+RT). Adversarially verified — 5 independent lenses, from-scratch
re-derivation of all 18 cells matched every digit (§6).**

## 1. The question and the pre-registered gate

caiso-93 closed the OVERNIGHT (hod 0-5) leg of the C1 CC-overnight cluster:
the measured overnight CAISO−PaloVerde spread carries NO carbon wedge
unconditionally, and an hod-scoped clean-import depth flipped C1 12/12 +
C3a-2024 PASS (promoted keeper). The deciding remaining criterion is
**C3a-2025 (+13.3%)**, whose mass the 2026-07-16 autumn-2025 diagnosis located
in the DAYTIME hours the overnight mechanism does not touch: (a) autumn
Sep-Dec-2025 (+7.5/+10.6/+7.2/+7.9 monthly resid) and (b) the belly hod 10-14
(+11.6/+10.2/+8.9, all years). That diagnosis named two distinct daytime
mechanisms — the south-corridor UNWEDGED-PARITY import regime OUTSIDE the
caiso-87 trigger window (the daytime analogue of what caiso-93 fixed
overnight), and a midday BATTERY-CHARGE-MARGINAL sub-regime — but armed
nothing. This gate asks the measured record, per daytime regime, **which
mechanism is in play**, WITHOUT any LP (the caiso-86b/88/93 derive-first
discipline).

Gate design (frozen in the script docstring before results were seen; every
leg inherited from the committed caiso-93 construction, sliced to the daytime
blocks — the caiso-86b "don't tune the method to the gate" prohibition):

- **regimes:** `morning_ramp` hod 6-9, `belly` hod 10-14, `afternoon_eve`
  hod 15-21; each × {autumn Sep-Dec, non_autumn}.
- **trigger** (caiso-87): `PALOVRDE < 6.97 × SoCal_citygate_weekly + $2.5`,
  measured-hub hours only.
- **parity** (caiso-82 §1, `DSW_CCGT` basis = ×1.03 + $4):
  delivered-DA spread `= actual − (PALOVRDE × 1.03 + 4)`.
- **raw-hub** discriminator (the caiso-93 §3 axis, no wheel):
  `actual − PALOVRDE`.
- Wedge reference = `0.428 × CARB allowance` = $14.1/$15.1/$12.0.
- **Scope:** gates + depth scored on the caiso-87 **trigger-OFF** slice
  (distinct from caiso-87's trigger-ON midday mechanism — the netting
  principle at the derivation stage; daytime caiso-87 is coverage-RICH, unlike
  overnight where it was coverage-starved, so the daytime leg is trigger-OFF,
  NOT caiso-93's unconditional pattern).

Pre-registered gates (the caiso-93 thresholds, unchanged): **G1 no-wedge** =
per-year OFF median delivered-DA ≤ +$4; **G2** depth CV ≤ 0.20; **G3** depth
LOYO ≤ 25% (p95 measured WECC_DSW net import over OFF hours).

## 2. Gate results — G1 no-wedge PASSES in every daytime cell

| regime × season | OFF median delivered-DA (23/24/25) | raw-hub median | parity ≤+4 | wedge-consistent | depth p95 MW | G2 CV | G3 LOYO | disposition |
|---|---|---|---|---|---|---|---|---|
| morning_ramp × autumn | −4.7/−4.0/−5.1 | +1.0/+1.2/+0.4 | 97/97/97% | 0/0/0% | 5198/6126/6102 | 0.074 | 17.6% | **IMPORT-LEVER** |
| morning_ramp × non_autumn | −14.3/−6.6/−10.3 | −9.2/−1.5/−4.9 | 100/97/95% | 0/2/2% | 4908/4642/5387 | 0.062 | 11.4% | MIXED (raw-hub neg) |
| belly × autumn | −2.3/−1.9/−4.1 | +2.7/+3.0/+1.1 | 96/90/95% | 0/1/0% | 5336/5705/5618 | 0.028 | 6.1% | IMPORT-LEVER (thin) |
| belly × non_autumn | −1.7/−3.6/−3.6 | +3.6/+1.3/+1.6 | 90/94/98% | 2/3/0% | 2400/4312/4657 | **0.262** | **86.8%** | depth-UNSTABLE (excl.) |
| afternoon_eve × autumn | −4.8/−3.2/−4.0 | +1.1/+2.2/+1.4 | 89/87/96% | 5/6/2% | 5641/6353/6494 | 0.061 | 13.9% | **IMPORT-LEVER** |
| afternoon_eve × non_autumn | −9.2/−4.7/−3.3 | −3.2/+1.0/+2.1 | 73/86/88% | 13/4/2% | 5508/5259/5736 | 0.035 | 6.9% | IMPORT-LEVER (thr-sensitive) |

**G1 no-wedge PASSES every cell, every year; wedge-consistent share ≈ 0–6%
(the tight afternoon aside, §4).** The measured no-wedge structure that
admitted the caiso-93 overnight leg is NOT overnight-specific — it holds
across the daytime trigger-OFF hours too. The model's +$12–15 south-corridor
carbon wedge on incremental daytime imports is measured-inconsistent well
beyond overnight.

## 3. The load-bearing sharpening: the daytime is heterogeneous — G1 is one-sided, the raw-hub discriminator does the work

G1 (delivered-DA median ≤ +$4) is a **one-sided** test: it fails only when
actual clears ABOVE hub-delivered-parity (i.e. at the wedge). It PASSES both
an import-at-hub cell AND a battery-floor cell. The **raw-hub discriminator**
(`actual − PALOVRDE`) is the second axis (verified sound, §6):

- **raw-hub ≈ 0 to +3** → actual clears at the raw hub → a no-wheel clean
  import CAN be the daytime margin → **IMPORT-LEVER admissible** (the caiso-93
  overnight situation). The three AUTUMN cells + afternoon-non_autumn.
- **raw-hub strongly negative** → actual clears BELOW even the raw hub → no
  import (even no-wheel) can set that price → a battery-charge / solar-ramp
  floor does → NOT an import lever (morning-non_autumn 2023 at −9.2).
- **wedge-consistent share material** → reality's marginal IS a carbon-paying
  import → the model's wedge is CORRECT → leave alone (rule 1) — the tight
  afternoon, §4.

## 4. Fine-grain refinement (`derive_caiso_daytime_finegrain.py` — disclosed sequencing)

**Sequencing DISCLOSED (the caiso-93 `derive_caiso_overnight_clean_depth.py`
precedent):** both refinements below were identified AFTER the coarse §2
results; every frozen threshold is untouched — this only re-slices the SAME
measured spreads for interpretation.

**A. The `afternoon_eve` (hod 15-21) coarse block straddles two regimes.**
Splitting it:

| sub-block × season | raw-hub median (23/24/25) | wedge-consistent |
|---|---|---|
| afternoon 15-17 × autumn | +2.4/+4.6/+2.1 | **13/16/5%** |
| afternoon 15-17 × non_autumn | +9.1/+3.6/+5.7 | **19/6/5%** |
| evening peak 18-21 × autumn | +0.1/+1.4/+1.1 | 0/0/0% |
| evening peak 18-21 × non_autumn | −7.9/+0.2/+1.3 | 10/3/1% |

- **Afternoon 15-17** carries a REAL wedge (13–19% wedge-consistent in the
  tight cells, actual ABOVE raw hub) — the tightest daytime hours where
  reality prices some scarcity/unspecified-import premium. **Leave alone**
  (rule 1) — the wedge is correct structure there.
- **Evening peak 18-21 × autumn** is measured-CLEAN (raw-hub ≈ 0, 0% wedge)
  AND the model OVER-prices it (+7–12 per the autumn diagnosis) → **the
  strongest import-lever sub-lane** (large OFF population, 474–488 h/yr).
- **Evening peak 18-21 × non_autumn** is measured-clean but the model
  UNDER-prices the peak (annual hod-ladder −5.8/−4.1/−1.2) → a clean-import
  lever there would OVERSHOOT (push λ further below actual) → **exclude**.
  (Mitigant: the leg is priced at raw hub, so it cannot pull λ below raw hub;
  where the model already prices below hub it simply does not clear — the LP
  self-scopes. The solve settles the net direction.)

**B. The `belly` (hod 10-14) mass is caiso-87 / battery territory.** The belly
is 66–90% caiso-87 trigger-ON. In those trigger-ON hours the HUB ITSELF is
cheap (p50 $0.7–20) — the West-wide solar glut — and actual clears slightly
ABOVE the cheap hub (`da−hub` +2 to +9). So reality's midday floor tracks the
cheap hub, and the battery-charge / low-hub sub-regime lives HERE, in the
trigger-ON belly (caiso-87 territory, off-limits by the hard constraint; a
separate storage charter). Only the thin trigger-OFF belly slice (20–33% of
belly, 125–203 h/yr) clears at raw-hub parity and is import-relevant — so
**the belly should NOT carry the C3a-2025 story** (its named +11.6 mass is the
trigger-ON battery sub-regime, not this import lane).

## 5. Disposition per regime (the charter's three-way fork, resolved)

- **IMPORT-LEVER admissible (caiso-93 pattern):** the AUTUMN daytime
  trigger-OFF hours — **morning ramp × autumn** and **evening peak 18-21 ×
  autumn** are the load-bearing cells (rich OFF coverage, raw-hub parity,
  0% wedge, tight depth gates); belly × autumn OFF is admissible but
  coverage-thin. This is the daytime analogue of caiso-93 and directly
  targets the C3a-2025 autumn mass (a).
- **WEDGE-REAL — leave alone (rule 1):** the tight afternoon 15-17 (13–19%
  wedge-consistent) — reality genuinely prices a premium there.
- **BATTERY / STORAGE — separate charter (do NOT fold in):** the belly-midday
  trigger-ON core (the low-hub solar-glut regime, the diagnosis' named
  battery-charge-marginal sub-regime) — a storage-side identification, out of
  this import lane by the hard constraint.
- **EXCLUDE (model under-price / overshoot):** evening peak × non_autumn
  (model under-prices), morning × non_autumn (solar-ramp MIXED), belly ×
  non_autumn (depth fails G2/G3).

## 6. Adversarial verification — 5 lenses, ALL CONFIRMED, no defects

A 5-lens workflow (each lens re-deriving independently from committed loaders,
not importing the script):

1. **Construction/basis** — CONFIRMED. The ×0.03-vs-×1.03 parity bug (which
   bit caiso-93 once) is **definitively absent** (parity = PV×1.03+4, verified
   by code AND the raw-above-delivered sign relationship). Wedge/trigger/
   masking/net-import-sign all correct.
2. **Masking/slicing** — CONFIRMED. hod blocks, MONTH_OF_HOUR (len 8760, Sep
   at hour 5832), autumn tail, trigger partition all reconstruct exactly; the
   2023 Jan-Feb OASIS gap masks correctly (non_autumn n drops ~340 h).
3. **Independent stat re-derivation** — CONFIRMED. All 18 cells reproduce
   byte-for-digit (medians <0.05, shares <0.05%, CV <0.0005, LOYO <0.02%).
4. **Interpretation/doctrine** — CONFIRMED. IMPORT-LEVER mirrors caiso-93's
   three-legged admit; trigger-OFF correctly excludes the battery sub-regime;
   hard constraints respected (disjoint from caiso-87, north corridor
   untouched, read-only NO-LP session — C1/overnight-λ untouched, no holdout
   leakage). The raw-hub discriminator is the correct, correctly-ordered
   second axis.
5. **Devil's advocate** — CONFIRMED (attacks defused). belly-autumn is NOT a
   battery false-positive (actual +3 ABOVE hub); depths are physically-realized
   flows (p95 < measured corridor max 5.9–7.8 GW — the "5.2 GW ATC" figure is
   stale); the three clean tranches (caiso-87 trigger-ON, caiso-93 hod 0-5,
   this hod 6-21 trigger-OFF) partition **disjoint hour-sets** — no within-hour
   double-count.

**Two load-bearing caveats surfaced by lenses 4 & 5 (advisory, for the owner):**

1. **ADMISSIBILITY ONLY.** The gate is scored entirely on the MEASURED record.
   It does NOT establish that the model over-prices these specific trigger-OFF
   hours — so it cannot prove the lever helps C3a-2025. **Inertness** (the
   lever does nothing, à la the caiso-86 partial-ladder refutation) is a live
   risk that ONLY a diagnostic solve settles.
2. **Depth is TOTAL, not incremental.** p95 is total measured net import over
   OFF hours; a build must net it against the firm/surplus/overnight
   capability (the caiso-93 §5 `max(0, depth − firm[t])` pattern), else it
   risks **overshoot** (λ below actual). Daytime depths (5–6.5 GW) exceed the
   prior CAISO clean-depth bases — the solve must check for over-importing,
   not just under.

## 7. What a build would be (NOT built — owner authorization required)

The caiso-93 injector pattern with a daytime leg: a zero-EF
`DSW_daytime_clean`-class capability whose hourly cap is
`daytime_OFF[t] × max(0, depth_day[year] − firm_south[t] − surplus[t] −
overnight[t])` (net of ALL sibling tranches so clean depth never
double-carries), armed on measured-hub trigger-OFF daytime hours, EF 0, priced
at the RAW measured Palo Verde hub with NO wheel (the caiso-93 basis; the
measured daytime OFF raw-hub spread ≈ 0 corroborates), P1-native, pmin 0
(capability, no D-2 row), corridor ATC envelope still caps delivered flow.
Zero fitted scalars.

**Disclosed build questions (owner decides at authorization):**

- **Season scoping.** The no-wedge STRUCTURE holds year-round, but the safe
  APPLICATION is where the model over-prices (autumn daytime); non-autumn
  evening is model-UNDER-priced (overshoot risk). Recommend the FIRST solve be
  **UNCONDITIONAL daytime trigger-OFF** (structurally honest, no calendar
  gate — a season gate would be residual-fitting per rule 1) with the
  report-back WATCHING the non-autumn evening for overshoot; the raw-hub
  pricing self-scopes the lever to over-priced hours (it cannot clear where
  the model already prices below hub). If overshoot materializes, THEN a
  principled hod-window restriction (drop the evening peak 18-21) is the fix,
  not a calendar gate.
- **Afternoon 15-17 exclusion.** The tight afternoon carries a real wedge
  (§4A) — the leg should not clean-import there. The trigger-OFF scope already
  excludes the tightest (trigger-ON) afternoon hours; whether to further
  hod-exclude 15-17 is a build refinement the solve informs.
- **Inertness is the principal probe risk.** If the model already prices the
  daytime OFF hours near actual, the lever is inert (caiso-86 outcome) and the
  C3a-2025 daytime residual is a MODEL-SIDE problem (scarcity/battery), not the
  import wedge — a legitimate finding, not a reason to force the mechanism.
- **Overshoot + depth-netting** (caveat 2 above).
- **Protected results are gates:** C1 12/12, the overnight λ closure
  (+1.9/+0.4/+1.9), and the caiso-93 keeper must not degrade — any lever that
  moves them fails its probe.

## 8. Disposition

- **Precondition: PASSED — a daytime clean-import extension is ADMISSIBLE.**
  The measured daytime trigger-OFF CAISO−hub spread shows NO carbon wedge
  (G1 all cells), the autumn daytime cells clear at raw-hub parity with
  year-stable depths (G2/G3 pass), and the construction is disjoint from
  caiso-87 and never touches the north corridor. The charter's three-way fork
  is resolved (§5): import-lever on the autumn daytime OFF hours; wedge-real
  (leave alone) on the tight afternoon; battery/storage (separate charter) on
  the belly-midday core.
- **BUT the gate proves ADMISSIBILITY only** (§6 caveat 1). Whether the lever
  moves C3a-2025 (vs inert) and whether it overshoots are unresolved and can
  ONLY be settled by a diagnostic solve.
- **Do NOT redo:** the caiso-87 midday mechanism (do not widen/re-trigger);
  the belly-midday battery sub-regime as an import lever (§4B — separate
  storage charter); the north-corridor depth (caiso-88, closed); a calendar
  season gate as the mechanism (residual-fitting, §7).
- **NO build, NO solve this session.** The evidence above is the ask. If
  authorized, the recommended first step is a **DIAGNOSTIC** solve (a
  `_caiso93_overnight_clean_ab.py` clone + the daytime-depth delta, 2023+2024+
  2025 one invocation, sequential per the memory limit) — authorize the solve
  as a diagnostic, NOT the mechanism as a keeper. Report-back per the caiso-93
  charter (C3a all three years, the C1 grid MUST hold 12/12, the hod λ ladder
  with belly/evening WATCH, the who-serves-the-night re-run, C3c, C2 sign,
  WATCH months, C4/C5a, determination).
