# PREREG miso-113 — regulated-PRB committed-run NIGHT-LEVEL floor

Committed BEFORE the ex-ante inertness measurement is run and before any
line of mechanism code is written. Session miso-113, 2026-08-01, branch
`claude/miso-113-coal-prb-floor-wtd8kl`, off `origin/main` at `b948805`
(miso-112 merged as PR #3250, so this branch carries its artifacts).

Successor to miso-111
(`results/calibration/FINDING-miso111-prb-committed-dispatch-2026-07-31.md`,
matrix cell **R**) and miso-112
(`results/calibration/FINDING-miso112-prb-committed-split-2026-08-01.md`,
matrix cell **R**); mechanism-matrix §5.4 queue item 0, the live head, named
in miso-112 §5 as the successor.

## 1. Target

C7 `shape` FAIL on COAL_PRB — MISO's **sole** remaining determination
blocker. Keeper `2026-07-31-miso-109b-hy-level`, D-1 cv_ratio
**0.466 / 0.475 / 0.314** in 2023/2024/2025 against the 0.5 gate;
profile_r 0.97–0.99, so the defect is **amplitude, not phase**.

## 2. Why the offer-side family is closed and a FLOOR is the open form

Both offer-side forms are spent and adjudicated **R**; neither is re-tested
here (DO-NOT-REDO, rule 26a):

- **miso-111**, whole-band repricing (`coal_prb_committed_dispatchable`):
  shape passes 2023/24, C1 COAL_PRB −8.77 / −14.97 TWh vs ±8.
- **miso-112**, the measured per-plant SPLIT (`coal_prb_committed_split`):
  shape **passes** (cv_ratio 0.466→0.738 / 0.475→0.872, 2025 0.314→0.393),
  COAL_BIT untouched, C3a improved, zero D-2 rows — and still fails C1 on
  **2024 COAL_PRB −10.23 TWh** vs ±8.

miso-112 §4 ran the structural test that decides *why*, per plant, over
ONLINE hours only, capacity-weighted across the 26 regulated PRB plants,
model against each plant's own measured `night_p50`:

| year | MEASURED | keeper (control) | split arm |
|---|---|---|---|
| 2023 | 0.434 | 0.483 | 0.407 |
| 2024 | 0.434 | 0.437 | 0.374 |

**The keeper's night LEVEL is already right.** What it gets wrong is
within-day VARIABILITY. A discount-only hold slice has no floor: in
genuinely cheap hours it backs out along with the cycling slice and drives
the level *below* the meter, which is exactly how the split bought CV by
shedding 12 TWh. **The missing object is a floor, not a second price.**

## 3. The mechanism (exact construction, committed before measuring)

One new `ScenarioConfig` bool, **`coal_prb_night_floor`**, default `False`
(rule 24 [R-REGISTRY]; its matrix row lands in the same PR per rule 26c).
It arms the repo's existing **P0-detected-run → `min_gen`** construction —
the same family as the CAISO RA must-offer / ERCOT / NYISO gas bridges,
P1-native, injected at the P0→P1 seam in
`pipeline/solve.py::run_energy_solve`, **no P2 pass** — routed onto the
regulated PRB coal fleet.

- **Scope** (AND-ed): CAMPD-binned coal plant; `coal_supply ∈ {prb,
  subbituminous}` (the COAL_PRB class, miso-111/112 scope verbatim); plant
  ∈ `eia860_selfcommit_scope_plants()` (the regulated set carrying the
  `coal_committed_takeorpay_regulated` discount — a merchant PRB plant
  self-commits on its own economics and is not floored); plant has a
  measured row in the split artifact; coal-CHP plants excluded (their floor
  basis is the steam host).
- **Window** — the plant's own **P0-detected committed run**, and nothing
  else. Offline hours in the model's base-cost pattern are never floored.
- **Level** — each plant's MEASURED within-run night level `night_p50`,
  already committed in
  `data/raw/_processed-legacy/coal_prb_committed_split_MISO.csv` (frozen
  deriver `scripts/data/derive_prb_committed_split.py`). **Not re-derived
  in this session** (rule 23 [R-FROZEN-DERIVE]); any deriver touch would
  have to cite a CAMPD source change, and none is claimed.
- **Placement** — incremental floor `max(0, night_p50 − pct_mr/100) ×
  nameplate`, spread across the plant's tranches in **FILL order**
  (`mustrun → sync → committed → econ`, the order the plant actually
  loads — the `ercot_coal_min_config_floor` precedent, and for the same
  reason: `min_gen` is clipped to the TRANCHE's own `pmax × availability`,
  so pinning a plant-level floor on one slice would silently collapse it).
  By construction `mustrun + floor == night_p50 × nameplate`, so the floor
  never forces a plant above its own measured night level.
- **Zero fitted parameters.** One measured input consumed formulaically.

## 4. Rule 17 [R-FLOOR-WINDOW] declaration

- **(a) Driver** — regulated **self-commitment**: MISO SOM Table 7 puts
  53–56 % of coal starts on self-commitment rather than the market's
  economics. A cost-of-service plant recovers fuel through the rate base
  and stays loaded at its overnight level through cheap nights.
- **(b) Window** — the hours of the plant's own P0-detected committed run,
  no clock-hour rule. A floor binding when the plant's own P0 pattern says
  it is offline is a bug by definition, and this construction cannot
  produce one: the floor is written only inside detected runs.
- **(c) Forward story** — regenerates for any year from that year's P0 run
  pattern plus the frozen measured level; responds to changed conditions
  through the P0 pattern (a plant the forecast retires or leaves offline is
  never floored).

D-2 mechanism id: **`MECH_COAL_SELFCOMMIT_NIGHT`**, with a cited
`D4_WINDOWS` entry added to `scripts/legitimacy_diagnostics.py` **in this
session** (rule 20 [R-FORCED-BUDGET]) — COAL_PRB carries **zero** forced
rows today, so C8 and D-4 become live gates on this class for the first
time in this lane, and no exemption is claimed in advance.

## 5. Ex-ante inertness check — the kill rule, stated before measuring

miso-111 PREREG §8 retired the bridge form as "provably inert". That
verdict was reached on the **LSL** statistic (plant-basis loading-when-on
p5 = **0.182**), which sits below every plant's `_mustrun` band (0.30–0.52)
— a floor under a floor cannot bind. **It does not extend to the night
level** (0.434 plant-basis cap-weighted; 0.62 × HSL on miso-111's class
basis), which sits ABOVE the mustrun band at most plants and is exactly the
level §2 shows neither arm holds. The argument is re-run rather than
quoted, by `scripts/probes/_miso113_floor_inertness.py`:

> **KILL RULE.** If fewer than **5** regulated PRB plants carry a non-zero
> incremental floor (`max(0, night_p50 − pct_mr/100) × nameplate > 0.5 MW`),
> **or** those plants hold under **5 %** of regulated-PRB class nameplate,
> the floor IS inert. Kill the lane ex ante — no LP, no arm — and register
> the finding.

## 6. Pre-registered guards (verdict rules, fixed before the A/B)

| id | guard |
|---|---|
| **G1** | C7 COAL_PRB `cv_ratio ≥ 0.5` in **2023 AND 2024** (2025: see §7). |
| **G2** | C1 **16/16 every year**. *This is the test — it killed both predecessors.* |
| **G3** | COAL_BIT `cv_ratio ≤ 2.0` all years, `profile_r` within 0.05 of the keeper. |
| **G4** | C3a/C3b/C3c no regression vs the keeper. |
| **G5** | COAL_PRB forced share ≤ **30 %** (rule 20 budget) **and** D-4 off-window binding ≤ **5 %**. Live for the first time on this class; no exemption claimed in advance. |
| **G6** | **The structural test, first-class this time.** Per-plant cap-weighted model night level (miso-112 §4 construction, reproduced verbatim) must move **TOWARD** the measured 0.434 — not past it. An arm that passes C7 by overshooting the level is the miso-112 failure again. |

**G2 direction, stated before solving.** Both predecessors *shed* volume
(−8.8 to −15.0 TWh) and breached the −8 floor. A floor pushes volume the
**opposite** way. The control sits at **+2.02 / +1.86 TWh** (2023/2024)
inside a ±8 band, so this arm's risk is the **+8 ceiling**: an over-tight
floor over-generates COAL_PRB. Headroom is ~6 TWh in each year. The
mechanism's own arithmetic bounds it — the floor cannot exceed
`night_p50 × nameplate` in a run hour and cannot create run hours — so the
prediction is a **gain of order +2 to +5 TWh**, landing inside the band but
without much margin in 2023.

## 7. 2025 expectation, stated before solving

**2025 will likely stay under the 0.5 gate** (miso-111 reached 0.411,
miso-112 0.393). The residual there is the overnight **price-formation**
defect — model off-peak p10 $29.71 against actual hub p10 $17.95 — which
belongs to the data-blocked miso-78/79 congestion + sub-hourly-RT lane.
**No lever is stacked on it** (rule 19 [R-ONE-MECH]).

Per the owner grant of 2026-07-31 (on record in the miso-111 session): a
**2023+2024 C7 PASS with 2025 improved, C1 16/16, and G6 clean** is a
rule-1 keeper candidate on structural fidelity even with C7-2025 still
failing. If that path is taken the grant is cited in the promotion note,
the matrix header is re-stamped, and `calibration-keeper-auditor --iso
MISO` runs after promotion.

## 8. Standing constraints

- **Rule 16** — one bundle, `--year 2023 2024 2025`, years sequential.
- **Rule 22** — MISO holds **no** holdout marker; `--year` never leaves
  {2023, 2024, 2025}.
- **Rule 15** — BOTH arms registered on the backcast dashboard in this
  session, rejection included.
- **Rule 26b/c** — `coal_prb_night_floor` carries its **own** matrix row,
  added in the same PR as the field; the `coal_prb_committed_dispatchable`
  and `coal_prb_committed_split` cells are **not** altered (no new evidence
  bears on their R adjudications, and neither form is re-tested).
- **Rule 21** — no free parameter is added; if the arm is promoted its DOF
  ledger entry cites the measured artifact as the identification source.
