# PREREG — miso-160: replace `SUMMER_WEFOR_SHARE = 0.30` with the **measured seasonal forced-outage shape** from MISO's published outage record (`summer_wefor_share_override`)

**Session** miso-160 · **ISO** MISO · **Date** 2026-08-16 ·
**Keeper at charter** `2026-08-15-miso-159-cod-vintage` (`miso159_cod_B`).

This document is pushed and byte-verified against the fetched remote ref
**BEFORE any construction is built, any derive statistic is computed, or any
solve is launched** (rule 27 `[R-PUSH]` protocol; the miso-155/156/157/159
discipline). Its §5 priors, §6 triggers and §7 decision rule bind the session.

---

## 1. Charter and provenance (rule 28(a))

**Queue provenance.** The miso-159 queue stamp names exactly one un-adjudicated
lever bearing on the 2025 cushion: `SUMMER_WEFOR_SHARE = 0.30`, "gated on the
OWNER's data-provenance decision (miso-157 §11 item 2: which measured record
adjudicates a forced-outage seasonal shape)". **That decision is now TAKEN
(owner, 2026-08-16, this session):** MISO's published outage record — the
daily MOM `OUTAGE` sheet, ticket-based offline MW by region × cause — is the
admissible seasonal-shape source; the CAMPD per-unit extract is ruled
inadmissible for outage measurement (output-derived, the standing data ask's
§2A ground; documented phantom-outage bias, miso-157 §5; **zero** `CT_PEAKER`
windows). The standing data ask's §2a is amended by the same decision to accept
**fleet-level grain** for this one deliverable — replacing a fleet-uniform
scalar invents no unit/class attribution, so the miso-85/87 closures are
untouched. Record: `docs/handoffs/miso-outage-grain-data-ask-2026-07.md` §9.

**The object.** `SUMMER_WEFOR_SHARE = 0.30`
(`config/fuel_trajectories.py:924`) applies 30 % of each unit's WEFOR in
Jun–Sep and redistributes the displaced 70 % into the shoulder months. Its own
declaration says: *"SOURCE: NONE — this is an UNCITED A-PRIORI HEURISTIC"*,
and records the physics tension — for FORCED outages the reallocation runs
**opposite** to the physical sign (forced outages correlate positively with
heat and load). It sits in the MISO keeper's DOF ledger under identification
`residual` — an open root cause (rule 21 `[R-DOF]`). Its declaration names its
sole exit: *"It may be REPLACED ONLY by a measured seasonal forced-outage
shape clearing the acceptance test in
`docs/handoffs/miso-outage-grain-data-ask-2026-07.md`"* — which the owner
decision above now unblocks at the parameter's own grain.

**Why this lever, stated before the solve.** miso-156 established that MISO's
C3a-2025 miss (−13.1 % on the current keeper) is **marginal-unit identity in
the upper tail of hours** — the model reaches the right class (CT_PEAKER
marginal in 74.1 % of top-200 zone-hours) but stops less than half-way up it,
with 6.31 GW of CT idle within $20/MWh of the 2025 clearing price. The share
governs the summer availability of **all six non-coal thermal classes** and is
the largest un-adjudicated quantity bearing on that cushion (miso-157 leg 2:
CT_PEAKER alone ~1.25 GW at model WEFOR, ~1.66 GW at the true vintages the
keeper now carries). Adoption grounds are rules 1 `[R-STRUCT]` / 14
`[R-ACCURATE]` — a measured, owner-adjudicated input replacing an uncited
heuristic on the price-setting availability path — **never the residual**.

**Rule 22 `[R-HOLDOUT]`.** 2023 / 2024 / 2025 only, both arms, one
`--year 2023 2024 2025` invocation each. MISO holds neither `complete` nor
`final`; no out-of-training year is read, solved, scored or registered. The
holdout spend freeze is untouched.

---

## 2. The construction

**One new `ScenarioConfig` field** (rule 24 `[R-REGISTRY]`):

```
summer_wefor_share_override: float | None = None
```

- **Default `None` → byte-inert:** every share site falls back to the module
  constant `SUMMER_WEFOR_SHARE = 0.30`, byte-identical to HEAD. Registered in
  `_CACHE_KEY_OPTIONAL_FIELDS` (dropped from the hash at its default) **and**
  the pinned-defaults ledger **in the same commit** (the nyiso-119 / miso-159
  discipline). An armed run hashes distinctly (different availability arrays).
- **Read sites, exhaustive:** the two share applications in
  `data/fleet/arrays.py::_apply_thermal_availability` (the `is_cc_np`
  statistical branch and the default branch), and the mirrored composition in
  `results/scarcity.py` (forecast-machinery variance pro-forma, whose
  docstring promises "the SAME composition the availability builder applies").
  No other consumer of `_SUMMER_WEFOR_SHARE` exists at HEAD
  (`fleet/__init__.py` re-exports it; probes read it read-only).
- **Mechanism unchanged, re-parameterized** (rule 19 `[R-ONE-MECH]`): summer
  gets `share × wefor`; the shoulder absorbs `(1 − share) × wefor ×
  summer_to_shoulder`; winter keeps flat WEFOR; per-unit annual mean is
  conserved by construction for ANY share, including share > 1 (summer above
  annual, shoulder below annual — the sign the record's physics implies).
  POF, DERATE, overlays, floors: untouched.
- **Rule 25 `[R-ISO-SCOPE]`:** armed for MISO only (this A/B; the promoted
  config if §7(a) clears). The generic default stays `None` → 0.30 for every
  other ISO. Other ISOs' matrix cells enter `U`; each lane derives its own
  value from its own record or leaves the cell untested. The matrix gains the
  field's base row + a cell line in every shard in the same PR (rule 28(c)).

**The derived value (rule 23 `[R-FROZEN-DERIVE]`: cites the data, never a
residual).** Computed by probe `scripts/probes/_miso160_wefor_shape_instrument.py`
through the **production loader**
`market_sim.data.miso_outages.miso_outage_mw_series` (T-8 discipline — no
re-implementation), and FIXED here before it is computed:

- **Statistic:** `R*_y = mean(offline MW, Jun–Sep) ÷ mean(offline MW, annual)`
  per year `y`, region `"MISO"` (system total), cause types
  `UNPLANNED_CAUSE_TYPES = ("Derated", "Forced", "Unplanned")` — the module's
  established composition (the miso-85 composition decision, and miso-157's
  pre-registered adjudicating basis). **Pooled value
  `R* = mean(R*_2023, R*_2024, R*_2025)`**, unweighted (years are equal design
  points), rounded to 4 decimals. **The armed override value is exactly this
  number.** No sweep, no alternative bases tried-and-picked: the basis is
  fixed in this paragraph.
- **Companions, reported never adjudicating:** per-bucket ratios
  (`forced_only`, `unplanned_only`, `derated_only`), the Jun+Jul window
  (T-29), per-year coverage day counts, and the same statistic on each
  operating region (North/Central/South).
- **Basis note, disclosed:** the composite includes the `Derated` bucket. The
  model's WEFOR table is a GADS EFOR-family rate, which by definition includes
  equivalent derated hours, so the composite is the like-for-like basis. The
  ambient component of summer deratings may partly overlap the net-summer
  pmax rating basis; the `forced_only` companion puts that sensitivity on the
  record (miso-157 published 2025 `Forced` 1.073 vs composite 1.109 — the
  overlap bounds ~0.04 of the ratio).

**Population on this keeper, stated from the committed config before the
build:** `cc_nameplate_summer_derate = False` → no unit takes the `is_cc_np`
branches; `coal_drop_pof = True` → coal bypasses (summer WEFOR dropped
outright — unchanged); `wefor_residual = None` → **no residual cap: all six
non-coal thermal classes carry their full statistical WEFOR through the
share**; reliability-floor CTs and coal sync tranches keep their existing
bypasses. So the override reaches exactly the population the 0.30 reaches
today, at full magnitude.

**Zero continuous degrees of freedom added.** The field carries one derived
constant whose identification is the cited record + the fixed procedure above.
The MISO keeper's DOF ledger entry for `SUMMER_WEFOR_SHARE` re-identifies from
`residual` to measured/derived; the ledger's residual count falls 2 → 1.

---

## 3. Naming

- Runs: `2026-08-16-miso-160-control` (bundle `miso160_wefor_A`, zero-delta
  same-HEAD replay of the keeper config) and `2026-08-16-miso-160-wefor-shape`
  (bundle `miso160_wefor_B`, the keeper config + the armed override — THE
  SINGLE DELTA).
- Probe: `scripts/probes/_miso160_wefor_shape_instrument.py`; record:
  `results/calibration/_miso160_wefor_shape_instrument.json`.
- Unit tests: `tests/test_miso160_summer_wefor_override.py`.

---

## 4. Validity gates — all run before any adjudicating statistic is read

| gate | condition |
|---|---|
| **V1** — the derive reproduces miso-157 | per-year composite `R*_y` reproduces the published **1.104 / 0.967 / 1.109** to **±0.01** each. A miss stops the session (S-DERIVE §6). |
| **V2** — the control reproduces the committed keeper | C3a per year within **±0.1 pp** of −0.1 / −5.4 / −13.1 %; C3b NRMSE within **±0.005** of 0.080 / 0.113 / 0.200; **every criterion verdict identical**. A miss is K0-class drift: stop, diagnose, disclose before reading the arm. |
| **V3** — the keeper's fleet, both arms | `n_gen` 2929 / 2923 / 2923; **6** carry zones; import nodes excluded from aggregates (T-5). |
| **V4** — pure seasonal reallocation (T-27) | Rebuilt share-term composition per unit (pre-overlay, the miso-157 leg-2 instrument): annual-mean availability invariant to **≤ 1e−9** for every unit in the share population, at the armed `R*`. The FINAL arrays' arm−control annual-mean deviation is **reported** (the multiplicative overlay interaction makes exact zero impossible there) but not gated. |
| **V5** — off-arm byte-inertness | With the field at `None`, availability arrays byte-identical to HEAD; cache-key flip guard: default key unmoved, armed key distinct (S-CACHE). |

---

## 5. Priors — registered before any number is computed

- **P-1, the derived value.** Per-year composite = the published
  1.104 / 0.967 / 1.109 (this is V1). Pooled **`R*` = 1.060, band
  [1.04, 1.08]** (arithmetic of the published values ± day-count/rounding).
- **P-2, reach** (probe, production arrays, arm − control, 2025): summer
  (Jun–Sep) thermal capability removed, non-coal classes, **3.0–6.5 GW,
  centre 4.7** (miso-91's share-lever census re-scaled to the 0.30 → ~1.06
  swing at the keeper's true vintages); `CT_PEAKER` component **1.2–1.9 GW,
  centre 1.55** (miso-157 leg 2: 1.248 GW at r* = 1.109 on model WEFOR,
  ×1.327 on true WEFOR, re-scaled to the pooled swing). 2023/2024 same order,
  slightly smaller.
- **P-3, price direction — DISCLOSED IN ADVANCE, against the failing gate.**
  Demand-weighted prices move **UP in all three years**, summer-concentrated:
  2025 **+2.5 to +9 %** (centre +5); 2024 **+1 to +5 %**; 2023
  **+0.5 to +4.5 %**. The shoulder leg moves the other way (shoulder
  availability rises), so annual nets are below the summer-window moves. Per
  the standing discipline (miso-159 P-2): **none of any residual improvement
  is claimed as calibration skill**; adoption is on rules 1/14.
- **P-4, C3a outcomes** (arm): 2025 −13.1 % + P-3 → **−4 to −10.5 %** — a
  PASS is plausible and NOT presumed; 2024 −5.4 % → −0.4 to −4.4 % (PASS
  holds); 2023 −0.1 % → +0.4 to +4.4 % (PASS holds; gate ±10 %).
- **P-5, C3b-2025** (knife-edge 0.200): two-sided. Expected to **improve**
  (the underpriced summer peak is the dominant seasonal shape error), but a
  regression past the gate is a PASS→FAIL flip and blocks promotion (§7(b))
  — pre-accepted, not arguable after the fact.
- **P-6, C1:** CT_PEAKER energy falls ~0.5–2 TWh (capability removed at its
  own margin), backfilled by ST_GAS / CC / imports; 16/16 expected to hold;
  any C1 flip blocks promotion (§7(b)).
- **P-7, C8:** floors byte-unchanged; forced shares move only through class
  denominators. Expected PASS both arms; a flip blocks promotion (§7(b)).

---

## 6. Triggers — each with its consequence fixed now

- **S-DERIVE:** pooled `R*` outside **[1.00, 1.12]**, or V1 misses → STOP
  before any implementation is armed: the basis is re-examined in a written
  disclosure, nothing is solved, and the session ends with the derive record
  and the finding. No re-basis is tried in the same session (that would be a
  sweep).
- **S-CONSERVE:** V4 fails → stop, debug, disclose; no adjudicating statistic
  is quoted until resolved (the miso-156/157 "stop, debug, disclose" clause).
- **S-2023 (against-interest brake):** the arm's 2023 demand-weighted price
  lift exceeds **+6 %** OR the arm's C3a-2023 lands above **+5.0 %** → even
  if §7(a) is otherwise met, promotion ESCALATES to the owner instead of
  proceeding (2023 is the year the keeper prices essentially exactly; a large
  2023 move is evidence the mechanism is not summer-scoped the way its
  arithmetic claims).
- **S-TAIL:** 2025 hours > $200/MWh jump past **20 h** (control: 1 h; actual:
  88 h) → reported at full magnitude; the C3c ledger is NOT touched, no tail
  mechanism is proposed, nothing is tuned to the tail.
- **S-CACHE:** flip guard fails (default key moves, or armed key collides) →
  stop-the-line, fix before any solve.
- **T-3 standing:** any exact constant or clean zero in the instrument gets a
  second derivation before it is believed (the trap that has paid four
  consecutive MISO sessions).

---

## 7. Decision rule — fixed before any solve

**(a) PROMOTE, no escalation**, iff ALL of:
1. **No criterion-year PASS→FAIL flip** (every criterion-year passing in the
   control passes in the arm — C1 classes, C2, C3a-2023/2024, C3b all years,
   C4, C6 attested, C8);
2. **C3a-2025 improves by ≥ 0.5 pp** (the noise floor is ~0: the control
   protocol reproduces the keeper at the gated grain);
3. V1–V5 all PASS and S-2023 did **not** fire.

Promotion grounds recorded now: rules 1/14 — a measured, owner-adjudicated
input replaces a self-declared uncited heuristic on the price-setting
availability path, and the DOF ledger strictly improves (residual count
2 → 1). The fail set staying {C3a-2025} does NOT block promotion under (a);
if C3a-2025 itself flips to PASS, the determination moves to
CALIBRATED-WITH-CAVEATS and the `complete`-marker question goes to the owner
(never taken by this session).

**(b) otherwise** (any PASS→FAIL flip, S-2023 fired, C3a-2025 improvement
< 0.5 pp, or any validity gate failed): **DO NOT promote.** Register both
runs anyway (rule 15), stamp the matrix cell with the measured outcome
(rejections included, rule 28(b)), write the FINDING, escalate to the owner.

**(c) in every branch:** both runs are registered, the FINDING is written,
the calibration log and the MISO matrix shard are updated in this session.

---

## 8. Rule-compliance block

- **Rule 13 `[R-MEASURED]`:** the record is a published physical availability
  quantity (ticket-based offline MW), never a price or outcome; the
  admissibility test is met — a forward year regenerates the seasonal shape
  from the same multi-year record (the pooled ratio is the forward analogue,
  exactly like `MAINTENANCE_MONTHLY_SHAPE`), and it responds to changed
  conditions through the fleet's own WEFOR levels. Nothing is rescaled so
  output lands on actuals.
- **Rule 14 `[R-ACCURATE]`:** a measured seasonal shape replaces an uncited
  a-priori heuristic; if the fit worsens the input is kept and the residual
  becomes a discovered-bug signal (pre-accepted).
- **Rule 19 `[R-ONE-MECH]`:** the share mechanism is re-parameterized, not
  duplicated; no other mechanism sets summer WEFOR shape; POF/DERATE/overlays
  untouched.
- **Rules 20/21/23/24:** no new tunable (one derived constant, identification
  cited); registry-visible field recorded in `run_config.json`; the derive
  commit cites the data, never a residual.
- **Rule 12 `[R-PARALLEL]`:** years sequential within each invocation; the
  two arms run sequentially (per-plant MISO LP memory).
- **Rule 15 `[R-DASHBOARD]` / 16 `[R-ALLYEARS]`:** both runs registered, all
  three years in one bundle each.
