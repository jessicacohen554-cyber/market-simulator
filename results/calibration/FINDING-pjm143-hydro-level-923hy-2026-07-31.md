# FINDING (pjm-143): PJM's hydro LEVEL now comes from EIA-923 `HY` — the
# largest pumped-storage fold of the six ISOs, closed on a CALIBRATED keeper

**Session:** pjm-143 (the miso-109 §7 / miso-110 §9.2 hand-back — PJM's own lane)
**Date:** 2026-07-31
**Verdict:** LEVEL FIX **landed** (rule 14 `[R-ACCURATE]`) and the candidate is
**CALIBRATED with every criterion passing** — 9/9 target grade, C1 16/16 with
free 12/12, identical determination to the control, **no gate flipped in either
direction**. Promoted to PJM keeper (owner authorization on record in-session).
`hydro_level_923_hy` PJM **`U` → `K`**; `hydro_budget_nameplate_aware` PJM
**`K` → `I`** (provably inert on the corrected level, §3).
**Rule 25:** every parameter and every signature re-derived from PJM's own data
this session; no MISO verdict transferred, and one half of the MISO argument is
explicitly shown NOT to transfer (§2).
**Runs:** `pjm143_control_A` (keeper recipe at HEAD, contaminated level) and
`pjm143_hy_level_B` (same HEAD, corrected level) — a single-delta A/B, both
registered (rule 15).
**Pre-registration:** `PREREG-pjm143-hydro-level-923hy-2026-07-31.md`, committed
and pushed **before either arm solved** (commit `ea4698e`).

---

## 1. The defect, re-measured on PJM's own data

miso-109 screened all six ISOs and measured PJM as the worst offender, then
deliberately left it for this lane. This session re-derived every number from
the raw sources before touching code
(`scripts/probes/_miso109_hydro_level_audit.py --iso PJM`,
`scripts/probes/_miso110_forward_level_audit.py`).

The LP's hydro units are EIA-923 prime mover `HY` — conventional inflow hydro
alone; `data/hydro.py` excludes `PS` because pumped storage is a storage
resource, not inflow. The PJM keeper (`2026-07-30-pjm-140-rampenv`,
`hydro_eia930_monthly=True`, `hydro_backfill_year=2024`) pinned those units'
monthly energy **level** to EIA-930 `NG: WAT`. PJM files **no `NG: PS` column**,
so its `NG: WAT` is a conventional-hydro **plus pumped-storage-discharge**
series.

Three signatures, each independently checkable:

| signature | measurement |
|---|---|
| (a) no `NG: PS` column | PJM's extract carries `COL, NG, NUC, WAT, SUN, WND, OIL, OTH` — PS has nowhere to go |
| (b) breaches its own nameplate | `NG: WAT` peaks **6,633 / 6,383 MW** (2023 / 2024) against **3,334.2 MW** of conventional `HY` nameplate — **1,437 / 1,572 h/yr** above it (1,249–1,612 across 2019–2025) — beside a **5,046.1 MW** PS fleet (Bath County 2,862.0, Muddy Run 1,072.0, Yards Creek 453.0, Seneca 411.8, Smith Mountain 247.3) |
| (c) never negative | **zero** negative-`WAT` hours in any year 2019–2025, so pumping is not netted and the contamination is one-way gross discharge. EIA-923 `PS` net generation is **negative** every year (−2.525 / −2.673 TWh in 2023/24 — the round-trip loss), the opposite sign |

The gap against what the units actually are — **coverage-gated**, so an
early-release filing is never differenced against a full one:

| year | 930 `NG: WAT` (pinned level) | 923 `HY` (the units) | gap |
|------|--------------:|---------:|----:|
| 2023 | 15.451 TWh | 8.976 TWh (76 plants) | **+6.475 TWh / +72.1 %** |
| 2024 | 15.819 TWh | 8.861 TWh (76 plants) | **+6.957 TWh / +78.5 %** |
| 2025 | 15.506 TWh | *early release, 13 plants vs a modal 77 — **not differenced*** | — |

**Two restatements of the handoff's figures, both deliberate.** (i) 2024's 923
`HY` is **8.861** TWh, not 8.864. (ii) The 2025 early release carries **13
plants against a modal 77** on the raw census (10 against 74 LP-visible) — the
handoff's "10 vs 72" mixed the two counting conventions. Same population, two
conventions; the energy totals agree exactly.

**What the LP actually saw** (budget builder, `backfill_year=2024`, measured
no-LP before either solve):

| year | control level (pinned) | candidate level (923 `HY`) | delta |
|------|---:|---:|---:|
| 2023 | 15.4508 TWh | 8.9766 TWh | **−6.474 TWh** |
| 2024 | 15.8187 TWh | 8.8639 TWh | **−6.955 TWh** |
| 2025 | 15.5060 TWh | 8.4667 TWh | **−7.039 TWh** |

The control run's own solve log states the defect outright:
`PJM 2023 hydro budget pinned to monthly target total 15450.8 GWh (was 8976.6
GWh)`, and its dispatched hydro is **15.451 / 15.819 / 15.506 TWh** — the pin
binds fully, so roughly **70–80 % of PJM's real hydro budget** was phantom
zero-marginal-cost energy.

## 2. What the fix is, what it is NOT, and where MISO's argument does not transfer

**The fix.** `"PJM"` added to `constants.EIA930_PS_FOLDED_INTO_WAT`. A BA in
that registry has its `NG: WAT` level pin **refused** (and logged); its monthly
hydro level stays on **EIA-923 `HY`** — the same series, and the same plant
population, the per-plant budget is already built from. Level and units become
one population. **Zero free parameters**: this *removes* a mechanism rather than
adding one, so the DOF ledger improves. Both lanes arm at once, because the
backcast refusal (miso-109) and the forecast climatology (miso-110) both gate on
the same registry — PJM's forward level moves **15.875 → 9.254 TWh**.

**No reconciliation factor — and the honest identification statement.** The
alternative (keep `NG: WAT` for monthly *shape*, rescale to the 923 level) needs
a reconciliation constant, and none is identifiable at PJM:

* PJM's conventional share of `NG: WAT` **drifts 0.654 → 0.556** across
  2019–2024 (spread 0.097) — a factor fitted on one year misstates another by up
  to ~17 % relative.
* The gap's **seasonal range is 3–6×** (Jul/Aug ~900–980 GWh/mo against Oct
  ~170–300), so a single scalar cannot represent it.

**Where MISO's argument does NOT transfer (rule 25).** miso-109 also refused the
rescale because MISO's monthly gap *changes sign by month*. **PJM's never
does** — 0 sign changes in all six complete-filing years, every month +166 to
+984 GWh, because Bath County cycles daily year-round rather than seasonally.
The PJM refusal therefore rests on the share drift, the seasonal range, and
rule 13's forward-story test — **not** on the sign-change argument. Stating this
explicitly is the point of rule 25: a transferred verdict would have imported a
premise that is false here.

**Not touched:** NEISO (files `NG: PS` from Nov 2024 — a time split needing a
per-window treatment, not this switch); `hydro_dispatch_envelope` /
`hydro_min_flow_floor` (built from hourly `NG: WAT`, inherit the contamination,
both default-off — a separate charter, and EIA-923 is monthly so it offers no
hourly substitute); every holdout year (§6).

## 3. Rule 19 `[R-ONE-MECH]` — what else acts on this phenomenon

Enumerated before changing anything. The keeper carries
`hydro_dispatch_envelope=False`, `hydro_min_flow_floor=False`,
`hydro_ror_split=False`. The monthly level pin was therefore the **only**
mechanism setting PJM's hydro energy level, and the fix **replaces** it in place
rather than layering on its residual.

**One mechanism IS armed and goes inert — disclosed, not discovered late.**
Unlike MISO, PJM's keeper runs `hydro_budget_nameplate_aware=True` (pjm-133,
matrix cell `K`). With the pin refused there is no level *target*, so there is
nothing to re-allocate and the mechanism is inert **by construction**. Measured
no-LP, all three years:

| year | corrected level (923 `HY`) | with the pinned level (930 `NG: WAT`) |
|------|---|---|
| 2023 | 8.9766 TWh — **identical**, L1 **0.000 GWh** | 15.4508 TWh — differs, L1 **1,702.9 GWh** |
| 2024 | 8.8639 TWh — **identical**, L1 **0.000 GWh** | 15.8187 TWh — differs, L1 **1,146.7 GWh** |
| 2025 | 8.4667 TWh — **identical**, L1 **0.000 GWh** | 15.5060 TWh — differs, L1 **2,084.6 GWh** |

The right-hand column is the interesting half, and it reproduces miso-109 §6 on
PJM's own data: **the mechanism's entire apparent signal at PJM was the
defect** — up to 2.1 TWh/yr of plant-months pushed above their own
`nameplate × hours` ceiling by pumped-storage energy that never belonged in the
level. Fix the level and the symptom disappears with it.

## 4. E1 sign statement — declared BEFORE the solve

*(PREREG §4, reproduced here verbatim in substance; the check is §5.)* The fix
removes **6.47 / 6.96 / 7.04 TWh/yr** of zero-marginal-cost energy (~0.8–0.9 %
of PJM's ~810 TWh load), so **hydro falls to the corrected budget, fossil volume
and imports rise, and the load-weighted LMP rises**, concentrated in summer
afternoon/evening hours (the fold is Jul/Aug-peaked and the contaminated series
swings 5.3× overnight→HE18). Magnitude predicted **+0.3 to +1.5 $/MWh
(~+1 to +4 %)** — materially larger than MISO's +0.05–0.09, because PJM's move
is ~5× larger absolute and ~1.7× larger as a load share.

Against the keeper's scored position (model load-weighted vs bench DA
load-weighted: 2023 **+2.05 %** over, 2024 **−2.21 %** under, 2025 **−9.87 %**
under), C3a-2024/2025 were predicted to improve and **C3a-2023 to worsen** — the
single most likely gate casualty, since 2023 starts over-priced.

**This prediction is a hazard, not a justification.** Rule 14 mandates the
accurate input whichever way the residual moves; the sign was written down first
precisely so a favourable result could not be read as the reason.

## 5. The A/B

Two runs, same tree, single delta — both registered (rule 15):

* **control** `2026-07-31-pjm-143a-control-930pin` (`pjm143_control_A`) — the
  keeper recipe with the pin still armed. **Noise floor exactly zero**: it
  reproduces the committed keeper's load-weighted prices to the third decimal
  (31.134 / 30.902 / 41.985) and its C8 notes to the digit, so every arm-B
  movement below is attributable to the single registry line.
* **candidate** `2026-07-31-pjm-143b-hy-level` (`pjm143_hy_level_B`) — the same
  recipe with the corrected level. **Promoted keeper.**

Instrument: `scripts/probes/_pjm143_hydro_level_ab.py` (validated
control-vs-itself at exact zeros before use).

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| hydro dispatched (TWh) | 15.451 → **8.903** (−6.548) | 15.819 → **8.861** (−6.958) | 15.506 → **8.464** (−7.042) |
| fossil total (TWh) | +5.186 | +5.636 | +5.648 |
| imports (TWh) | +0.624 | +0.448 | +0.506 |
| load-weighted LMP ($/MWh) | 31.134 → 31.421 (**+0.287**, +0.92 %) | 30.902 → 31.194 (**+0.293**, +0.95 %) | 41.985 → 42.368 (**+0.383**, +0.91 %) |
| C3a vs DA-lw actual | +2.05 % → **+2.99 %** (away) | −2.21 % → **−1.28 %** (toward) | −9.87 % → **−9.04 %** (toward) |
| C3c hours > $200 (vs actual) | 3 vs 6 (**unchanged**) | 10 vs 18 (**unchanged**) | 32 vs 59 (**unchanged**) |

**The §4 sign prediction holds on every limb in every year**: hydro falls to
the corrected budget (the dispatched delta tracks the no-LP budget delta to
within 0.08 TWh), fossil and imports pick it up — CC_REGULAR the largest
(+2.4 to +2.7 TWh), then **CT_PEAKER +0.99 / +1.24 / +1.51 TWh**, narrowing
the keeper's standing CT_PEAKER C1 deficit — and the price rises ~+0.9 % in
all three years. The effect is **summer-peaked exactly where the fold lived**
(Jun–Sep mean delta +0.39 / +0.40 / +0.53 $/MWh against +0.23 / +0.23 / +0.29
elsewhere, July the largest single month at +0.41 / +0.53 / +0.84), the
Jul/Aug PS-cycling signature §1 measured in the source data.

**The magnitude band is REFUTED in two of three years, recorded rather than
re-written** (the pjm-137/140 precedent): declared +0.3..+1.5 $/MWh, measured
+0.287 (2023) and +0.293 (2024) — below the floor by $0.013 and $0.007 — and
+0.383 (2025) inside it. The direction and order of magnitude were right; the
band's floor was set a hair too high.

**Scored outcome: CALIBRATED with every criterion passing, in BOTH arms.**
No criterion flips in either direction; C1 stays 16/16 (free 12/12); C3c's
model tail counts are **byte-identical** between arms (the +0.3 $/MWh mean
rise adds no >$200 hours), so the keeper's thinnest margin — C3c-2024/2025
passing by ~1 h / ~2.5 h against the 0.5× floor — is untouched. The C8
CT_PEAKER grounded share *improves* 16.3/16.9/17.1 % → **15.2/15.4/15.8 %**
(the class's energy grew while its floors didn't), with all grounding gates
still clear. The pre-declared C3a-2023 casualty did move away from actual
(+2.05 → +2.99 %) but stays well inside its band.

**One prediction from the PREREG did not materialize, disclosed**: the
kill/keep rule's discovered-bug branch was never entered — no gate flipped, so
no root-cause investigation is owed. The offer-calibration-absorbed-the-fold
hypothesis (PREREG §5.3) stands untested and should be remembered if PJM's
2023 over-pricing (+2.99 % post-fix) ever becomes a target: ~$0.29/MWh of it
is newly exposed by removing the phantom hydro that was suppressing it.

## 6. Governance

* **Rule 12 `[R-PARALLEL]`** — years solved **sequentially**, one fresh year per
  process, chained with `--reuse-solved` (`scripts/probes/_pjm143_chain.sh`);
  PJM's per-plant LP with ramp rows peaks ~15.5 GB against a 15 GB box, so a
  12 GB swapfile was asserted before every arm (keeper note 14).
* **Rule 16 `[R-ALLYEARS]`** — both arms cover **2023, 2024, 2025**, one bundle
  each. No single-year keeper.
* **Rule 22 `[R-HOLDOUT]`** — only 2023–2025 solved or scored. PJM holds the
  `complete` (validation) marker but not `final`; **2022 was deliberately NOT
  spent** — that is a separate decision, and a validation number is selection
  evidence, never a certified out-of-sample skill number. 2019/H1-2026 untouched.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive script re-run;
  `HYDRO_CLIMATOLOGY_YEARS` and the 0.50 census gate unchanged.
* **Rule 15 `[R-DASHBOARD]`** — both arms registered in-session, keeper bundle
  with its `hourly/` sidecars.
* **Rule 26 `[R-MECH-MATRIX]`** duty (b) — `hydro_level_923_hy`'s PJM cell
  updated with its evidence citation in this session, and
  `hydro_budget_nameplate_aware`'s PJM cell annotated with the measured
  inertness above. Duty (c) does not bite: no new `ScenarioConfig` field
  (registry membership only); `scripts/check_mechanism_matrix.py` passes.
* **Same-HEAD control, not the committed keeper.** `git diff` from the keeper's
  registration commit to HEAD touches files under `src/`, so a bit-equality
  control against the committed bundle was never pre-registered (the miso-106 G3
  lesson). The A/B is control-at-HEAD vs candidate-at-HEAD, single delta. The
  control reproduces the committed keeper's load-weighted prices to the third
  decimal (**31.134 / 30.902 / 41.985**).
* **Rule 27 `[R-PUSH]`** — Fable session (scope writes
  `src/market_sim/config/constants.py`); edits made locally with the Edit tool
  and blob-verified after push (both files MATCH).
* **Branch provenance.** The owner merged the session branch continuously
  (PRs #3206/#3215/#3216 took the PREREG, the registry fix, the instrument and
  the FINDING skeleton mid-session), so the deliverable commits were rebased
  onto the post-merge `main` as they landed. Both arms were solved at pre-merge
  trees (control `1950b72`, candidate `7bfaa73`) whose only difference is the
  one-line registry change; `main`'s later `src/` drift (miso-111's
  `coal_prb_committed_dispatchable`, `bool = False`) is default-off and does
  not touch PJM's solve path.

## 7. Open, not actioned

1. **NEISO** still needs a per-window treatment (PS split out from Nov 2024), not
   this switch.
2. **Hazard:** the hourly envelope / min-flow floor remain `NG: WAT`-derived at
   registry ISOs. Separate charter; no hourly EIA-923 substitute exists.
3. **Data-intake item (carried from miso-110 §9.3):** rebuild
   `data/raw/eia-930-hourly/{MISO,CISO} hourly.parquet` to cover 2022 (7 and 9
   rows against 8760, while the per-year long-form sources are present and
   complete). PJM is unaffected — after this fix it no longer reads the 930 side
   for its level at all.
