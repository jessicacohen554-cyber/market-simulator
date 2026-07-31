# PREREG (pjm-143): PJM's hydro LEVEL moves to EIA-923 `HY` — the PS-fold
# refusal (miso-109/110 machinery) armed at PJM, pre-registered BEFORE any solve

**Session:** pjm-143 (the miso-109 §7 / miso-110 §9.2 hand-back — PJM's own lane)
**Date:** 2026-07-31
**Status:** committed and pushed BEFORE the first solve of either arm.
**Rule 25:** every number below re-derived from PJM's own data this session
(`scripts/probes/_miso109_hydro_level_audit.py --iso PJM`,
`scripts/probes/_miso110_forward_level_audit.py`); no MISO verdict transferred.

---

## 1. The defect, re-measured on PJM's own data (this session, from source)

The LP's hydro units are EIA-923 prime mover `HY` — conventional inflow hydro
alone. The PJM keeper (`2026-07-30-pjm-140-rampenv`, `hydro_eia930_monthly=True`,
`hydro_backfill_year=2024`) pins those units' monthly energy LEVEL to EIA-930
`NG: WAT`. PJM files **no `NG: PS` column**, so its `NG: WAT` carries
pumped-storage gross discharge on top of conventional hydro.

Three signatures, each re-derived:

| signature | measurement (this session) |
|---|---|
| (a) no `NG: PS` column | PJM's extract carries `COL, NG, NUC, WAT, SUN, WND, OIL, OTH` — PS has nowhere to go |
| (b) breaches its own nameplate | `NG: WAT` peaks **6,633 / 6,383 MW** (2023 / 2024) against **3,334.2 MW** of conventional `HY` nameplate — **1,437 / 1,572 h/yr** above it (range 1,249–1,612 across 2019–2025), beside a **5,046.1 MW** PS fleet (Bath County 2,862.0, Muddy Run 1,072.0, Yards Creek 453.0, Seneca 411.8, Smith Mountain 247.3) |
| (c) never negative | **zero** negative-`WAT` hours in every year 2019–2025, so pumping is not netted and the contamination is one-way gross discharge. EIA-923 `PS` net generation is **negative** every year (−2.525 / −2.673 TWh in 2023/24 — the round-trip loss), the opposite sign |

Coverage-gated per-year level gap (the defensible fold numbers — never the
climatology delta):

| year | 930 `NG: WAT` (pinned) | 923 `HY` (the units) | gap |
|------|--------------:|---------:|----:|
| 2023 | 15.451 TWh | 8.976 TWh (76 plants) | **+6.475 TWh / +72.1 %** |
| 2024 | 15.819 TWh | 8.861 TWh (76 plants) | **+6.957 TWh / +78.5 %** |
| 2025 | 15.506 TWh | *early release, 13 plants vs modal 77 — **not differenced*** | — |

Two corrections to the handoff's numbers, from re-derivation: 2024's 923 `HY`
is **8.861** TWh (not 8.864), and the 2025 early release carries **13 plants
against a modal 77** on the raw census (10 against 74 LP-visible) — the task
memo's 10-vs-72 was the LP-visible count against a different modal convention.

**What the LP will actually see** (budget builder, `backfill_year=2024`, no-LP):

| year | control level (pinned) | candidate level (923 `HY`) | delta |
|------|---:|---:|---:|
| 2023 | 15.4508 TWh | 8.9766 TWh | **−6.474 TWh** |
| 2024 | 15.8187 TWh | 8.8639 TWh | **−6.955 TWh** |
| 2025 | 15.5060 TWh | 8.4667 TWh | **−7.039 TWh** |

(2025's candidate level is the 2025 early-release plants at their own filing
plus the 2024 backfill for the rest — the same population construction every
backcast year already uses; the *pin* is the only thing removed.)

Forward lane (miso-110 machinery, arms automatically with the same registry
line): PJM's forecast climatology moves **15.875 TWh → 9.254 TWh** (930 window
2021–2025 vs coverage-gated 923 window 2021–2024; naive **+71.5 %**,
window-matched **+72.5 %**, per-year +61.7/+79.6/+72.1/+78.5 %). Realised 923
census 74/74/72/72, 2025 (10) gated out. No forecast run is owed (no PJM
forecast run is registered anywhere; `program-status.json` gates all ISOs
below the full-solve line).

## 2. The fix, and its deliberate non-fixes

**The fix is one line:** add `"PJM"` to `constants.EIA930_PS_FOLDED_INTO_WAT`,
plus the citation block's PJM signatures. Both lanes (miso-109 backcast
refusal, miso-110 forecast 923 climatology) gate on that registry, so both arm
at once. **Zero new parameters**; it removes a mechanism (the level pin) rather
than adding one.

**No 930→923 reconciliation factor, and the honest identification statement.**
PJM's conventional share of `NG: WAT` drifts **0.654 → 0.556** across 2019–2024
(spread 0.097): a factor fitted on any one year misstates another by up to
~17 % relative. **Unlike MISO, PJM's monthly gap never changes sign** (0 sign
changes in all six complete years; every month +166 to +984 GWh — Bath County
cycles daily year-round). The refusal therefore rests on the share drift, the
3–6× seasonal range of the gap (Jul/Aug ~900–980 GWh vs Oct ~170–300 GWh —
not one scalar), and rule 13's forward-story test — NOT on the sign-change
argument, which is MISO's and does not transfer (rule 25). A fitted constant
remains a free parameter with no forward story (rules 5/13/22).

**Not touched:** NEISO (time split, needs a per-window treatment);
`hydro_dispatch_envelope` / `hydro_min_flow_floor` (hourly-`NG: WAT`-derived,
inherit the contamination, default-off — separate charter); the benchmark's
`classFull.hydro` actual (which is itself the PS-inclusive 930 series,
15.47/15.86/15.51 TWh — see §5); every holdout year (§6).

**Predicted side effect, measured no-LP before any solve:**
`hydro_budget_nameplate_aware` — **armed in PJM's keeper** (matrix cell K,
pjm-133) — goes **inert by construction** once the pin is refused: with no
level target there is nothing to re-allocate. Measured: on the corrected level
the budgets are **identical** (L1 = 0.000 GWh exactly, all three years); under
the pinned level the mechanism was moving **1,703 / 1,147 / 2,085 GWh** of
plant-months per year. As at MISO (miso-109 §6), the mechanism's entire
apparent signal at PJM was the defect — the plant-months it was "fixing" were
pushed above their own nameplate ceilings by pumped-storage energy that never
belonged in the level.

## 3. The A/B, pre-registered

Two arms, both at THIS session's HEAD (the miso-106 G3 lesson: the keeper's
registration commit is 20+ src-files stale; a bit-equality control against the
committed bundle is NOT expected and NOT pre-registered — control-at-HEAD vs
candidate-at-HEAD, single delta):

* **control** `pjm143_control_A` — `replay_keeper.py` on
  `results/calibration/pjm140_rampenv_B` at HEAD **before** the registry edit
  (pin armed, exactly the keeper recipe).
* **candidate** `pjm143_hy_level_B` — the same replay at the same HEAD **after**
  the one-line registry edit (pin refused, level = 923 `HY`).

The single delta between the two trees is the registry line (plus its citation
comment and tests, none of which touch the solve path for any other ISO).
Rule 16: `--years 2023 2024 2025`, one bundle per arm. Rule 12: years solved
sequentially, one fresh process per year, chained with `--reuse-solved`
(the `_miso109_chain.sh` pattern); arms sequential (peak RSS ~15.5 GB against
15 GB + 12 GB swap — swap re-asserted before every arm per keeper note 14).
Both arms registered on the backcast dashboard in this session (rule 15).

## 4. E1 — sign and magnitude, declared BEFORE the first solve

**Direction.** The fix removes 6.47 / 6.96 / 7.04 TWh/yr of zero-marginal-cost
energy from the LP (~0.8–0.9 % of PJM's ~810 TWh load). That energy must be
re-served by the marginal stack, so in every year: **hydro dispatch falls to
the corrected budget, fossil volume and imports rise, and the load-weighted
LMP rises.** The fold is summer-peaked (Jul/Aug gaps ~900–980 GWh/mo) and
diurnally peak-shaped (the contaminated series swings 5.3× overnight→HE18), so
the price effect concentrates in summer afternoon/evening hours.

**Magnitude.** MISO's 1.1–1.5 TWh/yr move (~0.5 % of load) bought
+0.05–0.09 $/MWh (+0.13–0.30 %). PJM's move is ~5× larger absolute and ~1.7×
larger as a load share, and lands disproportionately in tighter hours;
predicted mean-LMP rise **order +0.3 to +1.5 $/MWh (~+1 to +4 %)** — material,
unlike MISO's.

**Against the keeper's scored position** (model load-weighted vs bench DA
load-weighted: 2023 **+2.0 %** over, 2024 **−2.2 %** under, 2025 **−9.9 %**
under; C1 16/16 with CT_PEAKER carrying a −2.1/−3.6/−3.3 TWh deficit note):

* C3a 2024 and 2025 are predicted to move **toward** actual; **C3a 2023 is
  predicted to move AWAY from actual** (it starts over-priced). A 2023 C3a
  flip is the single most likely gate casualty.
* C3c (tail hours, floor 0.5×, passing by ~1 h in 2024 / ~2.5 h in 2025) moves
  **away from the floor** (more scarcity hours), i.e. the thin margin widens —
  helpful or neutral, not a predicted casualty.
* C1 fossil rows: the CC/CT deficits narrow; COAL classes may overshoot
  (MISO's COAL_PRB did). C2 gas/coal family volumes rise toward or past their
  bands.
* C7/C8: no floor or forcing mechanism changes; CT_PEAKER's grounded C8 share
  is computed against its own energy, which rises — share direction ambiguous,
  no flip predicted.

**This prediction is a hazard, not a justification** (miso-109 §4): the sign
was written down first precisely so a favourable move cannot be read as the
reason for the change, and an unfavourable one cannot be read as a reason to
revert it.

## 5. KILL/KEEP RULE — declared before any result exists

**The accurate input stays in, whatever the gates do** (rules 1/14). If any
criterion — C3a 2023 above all — flips to FAIL in the candidate:

1. the registry line is **NOT reverted**;
2. **no adder, haircut, uplift, reconciliation factor, or offer re-tune** is
   introduced in this session to offset it;
3. the regression is recorded in the FINDING as a **discovered root-cause
   issue** — the leading hypothesis, stated now: PJM's offer-curve calibration
   (gas margin anchor 3.3483, class multipliers) was fitted on a supply stack
   carrying +6.5–7.0 TWh/yr of phantom zero-MC energy, i.e. the tuned level
   was silently compensating for the defect exactly as rule 14 anticipates;
   re-identification of those curves on the corrected stack is a successor
   charter, not this session's;
4. both arms are registered on the dashboard regardless of outcome, and the
   mechanism-matrix cell `hydro_level_923_hy` PJM is stamped with the honest
   verdict either way.

There is no outcome in which this session reverts to the contaminated level,
and no outcome in which it tunes anything against the residual. Keeper
promotion is a separate decision from landing the fix: the candidate is
promotable iff its determination is not degraded below the control's in a way
the owner has not adjudicated — if gates flip, the promotion call is
explicitly flagged to the owner (the miso-109b precedent: promotion was an
owner call the following day).

## 6. Governance boundaries

* **Rule 22:** PJM holds `complete` (validation tier) but NOT `final`. This
  session solves and scores **2023–2025 only**. 2022 is spendable in principle
  but is a separate, deliberate decision — **not spent here**. 2019/H1-2026
  are locked and untouched.
* **Rule 23:** no derive script re-runs; `HYDRO_CLIMATOLOGY_YEARS` and the
  0.50 census gate unchanged.
* **Rule 26:** duty (b) — `hydro_level_923_hy` PJM cell updated with citation
  this session, whatever the outcome; `hydro_budget_nameplate_aware` PJM cell
  annotated with the measured inertness (flip K→I only on promotion, since the
  live keeper still runs the pinned level until then). Duty (c) — no new
  `ScenarioConfig` field; `check_mechanism_matrix.py` run before push.
* **Rule 27:** Fable session; constants.py edited locally via the Edit tool;
  every pushed file ≥300 lines blob-verified.
