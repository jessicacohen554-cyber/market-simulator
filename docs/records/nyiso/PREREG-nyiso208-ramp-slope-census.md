# PRE-REGISTRATION — nyiso-208: the **ramp-slope census**. Do NYISO's four live floor ramp slopes reproduce from the shipped regression, and is the CH cap knot 0.3200 identified?

**Session:** nyiso-208, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-dlfexh`, off `main` `a6e4b6db`. **Date:** 2026-09-06.
**DATA PROFILE:** `nyiso`. **Keeper:** `2026-09-06-nyiso-202-startup-aware` — will not change.

**Committed and pushed BEFORE any number is read.** Nothing below was written after seeing a
measurement. §0 discloses exactly what was read first.

**THERE ARE NO RUBRIC FAILURES TO FIX.** NYISO reads **fails 0**. C3c is the ledgered,
non-downgrading caveat (rubric v3.3 / v3.6) and is **NOT an objective** of this session. No metrics
file, price series, volume residual or scored criterion will be opened at any point. Rule 1
`[R-STRUCT]` forbids selecting a mechanism because a residual moved, and no mechanism is being
selected here at all.

---

## 0. Disclosure — what was read before this document was written

Read: `data/raw/reference/reliability_floor_coeffs_NYISO.csv` (the frozen coefficients and their
`threshold_basis` prose — the object's *definition*), both derive scripts' source, the ramp
interpolation in `model/interchange/core.py`, the ST_GAS roster in
`data/raw/_processed-legacy/bin_assignments_NYISO.csv` (which plants are in the class — again the
object's definition), the nyiso-207 finding + card, and the NYISO keeper shard.

**Not read, and not run:** any CAMPD generation series, any temperature series, any capacity factor,
either derive script's output, or any prior session's slope number (none exists — see §2).

## 1. The object

The **`CH_ST_ev` ramp family**, `reliability_floor_coeffs_NYISO.csv` rows 46–47:

| row | zone | class | driver | threshold | floor_pct | ramp_group | window |
|---|---|---|---|---:|---:|---|---|
| 46 | Capital_Hudson | ST_GAS | tmax | 25.0 | **0.0000** | `CH_ST_ev` | h14–21 |
| 47 | Capital_Hudson | ST_GAS | tmax | 38.0 | **0.3200** | `CH_ST_ev` | h14–21 |

Row 47's own prose: *"ramp cap knot: legacy CH slope 0.0246/C hot-limb to clamp @38C (>CH max 35.6);
measured hot-day CF regression"*. nyiso-207 §5 reported this limb as **the one live NYISO
coefficient its census could not reproduce** (frozen 0.3200 vs a p97 basis of 0.8701) and
**deliberately did not diagnose it**, because its prose names a *regression*, not a percentile —
a different construction, which that census did not evaluate. This session evaluates it.

### 1.1 A derivation, not a measurement — the cap VALUE carries no information beyond the SLOPE

`core.py` composes a ramp family as `np.interp(series, xs, ys)` over the family's knots, clamping
flat outside the range. For `CH_ST_ev` that is `xs=[25.0, 38.0]`, `ys=[0.0, 0.3200]`, so the applied
fraction at driver temperature *T* is

```
frac(T) = 0.3200 × (T − 25) / (38 − 25) = 0.024615 × (T − 25),   clamped to [0, 0.3200]
```

and, since the prose states CH's observed max tmax is 35.6 °C < 38 °C, **the 0.3200 knot is never
reached**: the live quantity is the slope over [25, 35.6], topping out at `0.024615 × 10.6 = 0.2609`.
Conversely `0.0246 × 13 = 0.3198 → 0.320`. **The frozen 0.3200 and the prose slope 0.0246/C are the
same number written two ways.** This is arithmetic on the CSV and the code, verifiable without
touching data, and it means the entire identification question reduces to: **does 0.0246/C reproduce
as the shipped hot-day regression slope?**

## 2. Why this is new work and not a DO-NOT-REDO violation

nyiso-207's census measured `base_ev`, `base_24h` and `cap` — **all percentiles**. **No session has
ever reproduced a ramp SLOPE.** The four live NYISO ramp slopes (NYC_ST 0.0628, LI_ST 0.0424, CH_ST
0.0246 from `derive_nyiso_st_reliability_floor.py`; the pooled-downstate CT 0.0535 from
`derive_nyiso_ct_reliability_floor.py`, carried by both `NYC_CT_ev` and `LI_CT_ev`) are the exact
complement of that census, and CH's is the row nyiso-207 left open. No cell marked `R`/`I`/`G` in
`docs/codebase-site/data/mechanism-matrix/NYISO.js` is re-tested. The four closed reliability-floor
columns (membership, fill order, fill level, coefficient basis) are **not** re-opened: this is the
*identification of a coefficient*, which none of them covers.

## 3. Instrument

**The shipped scripts themselves**, run with `--no-fetch --years 2023 2024 2025` (the derive
scripts' own default span) against the archived `data/raw/nyiso-weather/nyiso_zone_tmax_daily.csv`
and `nyiso_downstate_tmax_daily.csv`. No re-implementation: the printed
`nyiso_st_floor_slope_per_c` / `nyiso_ct_floor_slope_per_c` **is** the shipped construction,

```python
slope = np.polyfit(hot["tmax"] - 25.0, hot["cf"], 1)[0]     # hot = days with tmax >= 25 C
```

A supplementary probe (`scripts/probes/_nyiso208_ramp_slope_census.py`) calls the same shipped
functions by file-path import for the legs the scripts do not print (§4 M3–M6). **Zero LP.**
Rule 29 `[R-SCREEN]` step 0 gates the solve to zero: the only outcomes on the table are a
measurement and possibly a card, **neither of which is an arm**, so no screen year is pre-registered
because there is nothing for a screen to gate.

## 4. Measurements

- **M1 — CH slope.** The printed `nyiso_st_floor_slope_per_c` for Capital_Hudson, pooled 2023–2025.
  *The primary number.*
- **M2 — instrument control.** The same run's NYC and Long_Island slopes vs the prose 0.0628 and
  0.0424, **and** its `base_ev` / `base_24h` / `cap` for both zones vs the frozen CSV values and vs
  nyiso-207's independently-measured M1 column (0.1849 / 0.1749 / 1.0358 NYC; 0.3502 / 0.2623 /
  0.8815 LI). Agreement validates the instrument and shows the extract has not drifted for those
  limbs; disagreement means a CH result is uninformative (§6 verdict X).
- **M3 — CT slope.** `derive_nyiso_ct_reliability_floor.py`'s printed slope vs the prose 0.0535.
  That script normalises by **nameplate with no outage derate**, so it is immune to any
  availability-extract change — the cleanest control available.
- **M4 — CH availability sensitivity.** Recompute the CH slope with `avail = nameplate` (derate
  off), pooled 2023–2025, one change only. If it equals the shipped value, the outage extract does
  not reach CH's plants and **no extract-drift story can explain a CH gap** — this measurement can
  kill this session's own P2 hypothesis, which is why it is declared.
- **M5 — span search (CONDITIONAL, and pre-limited).** *Only if M1 misses.* Re-run the CH slope on
  {2023}, {2024}, {2025}, {2023,2024}, {2024,2025} on the shipped basis. **Declared limitation,
  binding:** this is five extra comparisons against a ±0.0010 window, so a hit is expected by chance
  at a non-trivial rate. **A sub-span hit will be reported as SUGGESTIVE ONLY and never as
  identification**, and will be labelled with this multiple-comparison caveat wherever it appears.
- **M6 — conduct and window (the charter's alternative object, folded in).** Over CH hot days
  (tmax ≥ 25 °C), pooled 2023–2025: (a) the share of hot days whose measured evening when-available
  CF is ≥ the applied `frac(tmax)`; (b) the median when-available CF inside h14–21 vs the median in
  the complementary hours h00–13 + h22–23 (the nyiso-203 §3 block-CF treatment, never applied to
  this zone). Also reported: CH `corr(CF, TMAX)`, hot/mild median CF, hot-day count, and the limb's
  forced energy for context.

## 5. Predictions — signs, magnitudes, and their mutual consistency

**P1 — CH REPRODUCES.** `|M1 − 0.0246| ≤ 0.0010 /°C`. *(This session's preferred answer: the knot
is identified and nyiso-207 §5's open observation is discharged.)*

**P2 — THE PREDICTION THAT CUTS AGAINST P1: CH is guard-stale.** Rows 46–47 carry **no**
*"re-derived 2026-07-26 on the guard-corrected outage extract"* note, while the NYC (rows 7–8) and
LI (rows 25–26) ramp rows both do. The `6a8f285` guard fix un-booked economically laid-up steam from
the outage extract, so the availability **denominator rose and when-available CF fell** — NYC
`base_ev` 0.533 → 0.185 (×0.35), LI 0.572 → 0.35 (×0.61). A slope computed from that same CF should
scale with it. Row 46 (`base_ev = 0.0`) is silent on vintage either way, because 0/x = 0 for any
denominator — which is *why* it needed no re-derivation note and why this hypothesis is coherent
rather than ad hoc. **P2: `M1 < 0.0200 /°C`, most likely in 0.008–0.016** (0.0246 × [0.35, 0.61]).

*P1 and P2 are mutually exclusive* (P1's floor 0.0236 > P2's ceiling 0.0200) and leave a declared
third outcome: anything else is **UNIDENTIFIED**.

**P3 — THE CONTROLS REPRODUCE.** `|M2_NYC − 0.0628| ≤ 0.0025` and `|M2_LI − 0.0424| ≤ 0.0025`
(≈4 % relative, looser than CH's because the values are larger). **This cuts against the session
too:** if P3 fails, nothing can be concluded about CH at all and the deliverable shrinks to "the
NYISO ramp slopes are not reproducible at HEAD". *Named candidate cause if NYC specifically fails:*
the nyiso-192 `-perunitmerit-` outage-extract re-derivation moved the whole steam availability
envelope (106 Astoria windows out, 155 windows in at fifteen other plants), and Astoria 8906 is NYC
ST_GAS. *Consistency with P2:* P2's mechanism does not apply to NYC/LI, whose knots **were**
re-derived post-guard, so **P2-true and P3-true are consistent** — they are claims about different
vintages, not about different data.

**P4 — THE CT SLOPE REPRODUCES.** `|M3 − 0.0535| ≤ 0.0025`. The CT script uses nameplate with no
derate, so neither the guard fix nor the Astoria re-derivation can reach it, and nyiso-207 found
both CT percentiles reproduced. **If P4 fails while P3 holds, this session's whole
availability-basis story is wrong**, and it will be reported as wrong.

**P5 — THE CH FLOOR DOES NOT EXCEED OBSERVED CONDUCT.** M6(a) **> 50 %** of CH hot days have
measured evening CF ≥ the applied `frac(tmax)`. *Cuts against the session:* a failure is a rule-17
`[R-FLOOR-WINDOW]` finding — a floor binding above what its own driver evidence supports — which is
the opposite of the clean "it's fine" answer P1 points at. *Consistency:* **P2-true makes P5 more
likely to fail** (a stale-high slope forces above current conduct) and **P1-true makes P5 more
likely to hold**. The two are not contradictory; the joint pattern is the informative object, and
this linkage is declared here so neither result can be presented as a surprise.

**P6 — THE h14–21 WINDOW SELECTS THE ZONE'S HIGHER-OUTPUT BLOCK.** M6(b): CH's hot-day median
when-available CF inside h14–21 is **≥ 1.5×** its median in the complementary hours. *Cuts against
the session:* a failure means the evening window — inherited by the ST script from the CT script
without a CH-specific justification — is mis-specified for this zone, a rule-17 leg (b) defect.

## 6. Pre-registered verdicts and the decision rule

| verdict | condition | consequence |
|---|---|---|
| **R — IDENTIFIED** | P1 ∧ P3 | The 0.3200 knot is the shipped hot-day regression slope rendered at a 38 °C anchor. nyiso-207 §5's open observation is **DISCHARGED**. No card owed on that point. |
| **S — STALE** | P2 ∧ P3 | The knot is identified **as of a superseded extract**. Unlike nyiso-207's construction question, a rule-23 `[R-FROZEN-DERIVE]` **source-data trigger would exist** — but whether it does is an owner call and the size must be stated. **Owner card. No coefficient is edited.** |
| **U — UNIDENTIFIED** | ¬P1 ∧ ¬P2 ∧ P3 | An unidentified live coefficient on a CALIBRATED ISO. **Owner card. No coefficient is edited.** |
| **X — INSTRUMENT** | ¬P3 | Nothing is concluded about CH; the instrument result is the finding. |

P5 and P6 are reported **in every branch**, pass or fail, and a failure of either is reported as a
finding against this session's preferred reading.

## 7. What this session will NOT do — declared in advance so a clean result cannot become a licence

- **No coefficient is edited and no replacement value is proposed for any limb**, in any branch,
  including S. Rule 23 `[R-FROZEN-DERIVE]` governs whether a re-derivation may land, and that is an
  owner call — the same refusal nyiso-203 §7 and nyiso-207 §7 made. A measured slope is reported as
  *a measurement of the gap*, never as a replacement value.
- **No derive script, `ScenarioConfig` field, CSV row, `src/market_sim/` file or scorer file is
  changed.** Zero DOF, zero registered fields, zero re-derivations into any artifact.
- **No other ISO is measured** (rule 25 `[R-ISO-SCOPE]`). Both scripts have per-ISO siblings; their
  exposure stays unmeasured here, exactly as nyiso-206 §5 and nyiso-207 §7 refused.
- **No `offer_curve_by_group` band multiplier is touched** — owner court under carve-out condition
  (c).
- **No out-of-training year is solved, scored or registered** (rule 22). 2023–2025 only; the
  `NY_2019/2020/2021/2022/2026.parquet` extracts present in this profile will not be read.
- **No marker is touched.** `complete` (WITHDRAWN, Q5) and `frontier` re-entry are owner acts;
  C-19 / Q51 stays PARKED. No keeper promotion, no re-stamp, no registration.
- **The four pending owner rulings are not taken**: nyiso-206 (i), nyiso-207 (ii), nyiso-203 §6
  (iii), `DECISION-CARD-nyiso193` §5/§5.1 (iv). Nothing here rules any of them.
- **Rule 20 `[R-FORCED-BUDGET]` leg (a) stays open**; the unit-grain C8 exposure is untouched.

## 8. Governance

| item | state |
|---|---|
| **LP** | **zero.** Rule 29 step 0 gates it; no arm is on the table, so no screen year is pre-registered |
| **Rule 29(b) G-DRIFT** | re-validated **EMPIRICALLY** at this HEAD before this PREREG was written: `scripts/probes/nyiso198_rebuild_checks.py --year 2024` re-run leaves `git status --porcelain -uno` **EMPTY**. G-CTRL form 4 valid; no control solve owed or spent (nothing is differenced against a solve). *(That probe prints its own `"VERDICT": "STOP"` — the adjudicated nyiso-198 duct-peaking gate, an `R` cell, part of the committed record and **not** a drift signal.)* |
| **Rule 26 `[R-MECH-MATRIX]`** | NYISO shard cell updated in **this** session whatever the verdict, with the key set diffed against `main` before commit |
| **Rule 15 `[R-DASHBOARD]`** | nothing to register — no run, no bundle. Git history + the finding are the record |
| **Rule 29(c)** | no screen or control bundle will exist, so there is nothing to delete before merge |
| **Deliverable** | a measured finding on a named object, plus an owner card **only** under verdicts S or U. **A clean negative — including verdict R with P5 or P6 failing — is a full result.** |

---

*(nyiso-208 pre-registration. Zero LP. Predictions declared with their signs, their magnitudes, the
two that cut against the session's preferred answer, and their mutual consistency checked.)*
