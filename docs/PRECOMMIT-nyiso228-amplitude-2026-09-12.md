# PRECOMMIT — nyiso-228: the 2022 LMP miss and the fleet-`r` decay are ONE object (an absent upper price tail), and three spans test it

**Session:** nyiso-228 · **ISO:** NYISO · **Date:** 2026-09-12
**Branch:** `claude/2022-lmp-fleet-correlation-7zr8n0`
**Owner instruction (verbatim, this session):** *"Do a comprehensive assessment of 2022 LMP miss
for NYISO and bad fleet r correlation, diagnose, and run an LP solve with shards for each years
including holdouts to move all years toward calibrated. Run more than one solve and launch parallel
shards on it if you can diagnose multiple issues with separate variables."*

**Incumbent keeper:** `2026-09-09-nyiso-221-fuelvintage-span`
(bundles `results/calibration/nyiso_fuelvintage_A` 2023–2025 + `nyiso_fuelvintage_H2` 2022).
**Rule 32 `[R-SHARD]`:** the parent runs **ZERO LP**. Everything below §6 is phase-0, read or
recomputed from committed artifacts only.

---

## 1. THE ASSESSMENT — what is actually wrong, measured

Every number in this section is new to this session and comes from the committed keeper hourly
sidecars (`results/calibration/nyiso_fuelvintage_A/hourly/`), the committed run payload's
`lmpDeltaHr` (`model − actual RT`, load-weighted) and the committed bench parts.

### 1.1 The 2022 price miss is a WINTER miss, and it is NOT a 2022 problem

Monthly mean `model − actual` load-weighted LMP ($/MWh), all four years:

| | Jan | Feb | Mar | Apr | May | Jun | Jul | Aug | Sep | Oct | Nov | Dec | **year** |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **2022** | **−24.0** | **−23.4** | −6.6 | −4.3 | +5.8 | −8.0 | +2.1 | −3.1 | −0.9 | −5.7 | −6.4 | **−40.9** | **−9.55** |
| 2023 | +2.0 | −4.3 | +7.4 | +2.9 | −0.4 | +3.2 | +4.2 | +2.0 | −0.8 | +0.2 | +1.7 | +6.2 | +2.07 |
| 2024 | +11.1 | +4.0 | +6.8 | +5.2 | +4.8 | +5.3 | −0.7 | +5.6 | +5.0 | +2.1 | −1.3 | **−15.4** | +2.74 |
| 2025 | **−13.3** | **−17.8** | +2.7 | +1.6 | +3.1 | −10.9 | −6.3 | +6.2 | +4.2 | +1.4 | +0.7 | +0.5 | −2.21 |

**Jan + Feb + Dec carry 77 % of 2022's entire annual miss** ((−24.0−23.4−40.9)/12 = −7.36 of −9.55).
Worst days: **2022-12-24 −669.8**, 12-23 −267.3, 01-16 −189.6, 12-26 −144.0, 12-25 −95.7 — Winter
Storm Elliott and the mid-January cold snap. **Those four Elliott days alone are 34 % of the annual
miss.**

**The same months fail in the TRAINING years.** 2025 Jan −13.3 / Feb −17.8; 2024 Dec −15.4. 2022 is
not a holdout-year anomaly — it is the **severe instance of a standing winter defect that 2023's mild
winter hid**. That reframing is the single most important result of this phase 0: closing it moves
2025 and 2024 as well, which is exactly the owner's "move all years toward calibrated".

### 1.2 The mechanism: the model has NO UPPER TAIL. Its price ceiling is ~$200–315.

From the keeper's own `system_<yr>.parquet` (load-weighted over the five load zones) against the
actual reconstructed as `model − lmpDeltaHr`:

| | model h>300 | actual h>300 | model max | actual max | model p99 | actual p99 |
|---|---|---|---|---|---|---|
| 2023 | 0 | 10 | **214** | 1,175 | 63 | 118 |
| 2024 | 0 | 13 | **204** | 1,064 | 116 | 139 |
| 2025 | 3 | 42 | **314** | 1,982 | 177 | 220 |
| 2022 | 10 | 101 | — | — | — | — |

**In the top-100 actual-price hours the model is short by $137 / $137 / $274 per hour** (actual mean
204 / 217 / 419 vs model 64 / 80 / 145). Those 100 hours carry **−77 % / −57 % / +142 %** of the
whole annual price gap — i.e. the annual C3a number is a small residue of a large, one-signed tail
error, and in 2023/2024 the model is *above* actual for the rest of the year to compensate.

### 1.3 The scarcity machinery fires, and prices it at $25

Keeper `reserve_family_<yr>.parquet`, P1, all nine NYISO families, three years:

| family | published penalty | hours dual>0 (23/24/25) | **max dual reached** |
|---|---|---|---|
| `nyca_30min_total` | $750 | **0 / 0 / 0** | **0.00** |
| `nyca_10min_total` | $750 | **0 / 0 / 0** | **0.00** |
| `nyca_10min_spin` | $775 | **0 / 0 / 0** | **0.00** |
| `east_10min_total` | $775 | 0 / 3 / 2 | **32.69** |
| `seny_30min_total` | $500 (+$40 increment) | 4 / 1 / 8 | **40.00** |
| `nyc_10min_total` | $25 | 21 / 22 / 48 | **25.00** |
| `nyc_30min_total` | $25 | 15 / 9 / 25 | **25.00** |
| `li_10/30min_total` | $25 | 0 / 0 / 0 | **0.00** |

**The three NYCA-wide families — the only ones whose published penalty is in the $750–775 range —
NEVER bind in any hour of any year.** Energy slack never binds either (0 h, all years). So the
model's ceiling is set entirely by its own offer stack plus a $25–40 locational adder, against a
market whose own NYCA-wide reserve price averages **$306.74 / $31.74 / $393.31** in its C3c tail
hours (measured at nyiso-144 §1.4, quoted in the matrix cell `nyiso_spin_reserve_online`).

**Every structural route into that NYCA tail is already adjudicated shut and stays shut** —
`nyiso_spin_reserve_online` **I** (inert; ρ* 0.3426/0.3635/0.4619 and hydro's 10-minute headroom is a
coverage gap, nyiso-144), `nyiso_synchronised_reserve` **G** (ρ unidentified, owner card refused at
nyiso-145), `nyiso_east_reserve_families` **I**, `measured_ramp_capability` **I** (the ramp10 ceiling
clears every NYCA requirement 4.9–10×), `temp_dependent_derate` **G**. **This session opens none of
them.** What remains live is the offer surface.

### 1.4 The "bad fleet r" is the SAME object, and that was already measured

Payload `fuelRows`:

| | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **interchange r** | 0.794 | 0.660 | 0.679 | **0.473** |
| **gas r** | 0.910 | 0.942 | 0.895 | **0.841** |
| nuclear r | 0.971 | 0.873 | 0.943 | 0.857 |
| **D-A price amplitude, % of measured** | **62.7** | **61.2** | **52.6** | **41.8** |

The amplitude column and the interchange column fall together. nyiso-99 already identified why, and
refused the shape lever for it: *"the model's internal price swing is 0.58/0.52/0.46 of the real one
while the measured seam price is correct"* — a correctly-priced seam against a too-flat internal
price cannot allocate imports to the right hours. **The interchange `r` is a symptom of §1.2, not an
independent defect.** C4 still PASSES (it gates gas+coal only, floors r≥0.70); the decay is real and
reported, and it is the same object.

### 1.5 What is NOT the cause — closed here, so nothing re-tests them

* **Availability**: nyiso-227 measured the sub-5-day gas outage family NEAR-INERT and closed every
  availability-side ST_GAS lever; `unit_outage_short_windows_gas` **I**.
* **Topology**: nyiso-225 closed the Total-East cutset split at phase 0 on three independent legs;
  `nyiso_total_east_cutset_ttc` **R**.
* **Gas daily gap fill**: nyiso-223 closed 2.3 % of the Dec 22–31 2022 window and made C3a **worse**
  (−13.8 → −13.9 %); `nyiso_hub_gap_month_level` **R**.
* **A uniform offer lift**: nyiso-222's ×1.05 on all four bands moved C3a +4.0/+3.6/+2.6 pp and left
  C3c **unchanged at 2 / 0 / 3** — because the gate counts hours >$300 and the model's 2024 maximum
  was $226.8. A uniform lift raises the mean without building a tail. **That is the measured reason
  this session moves the PEAK band and only the peak band.**

---

## 2. G-DRIFT (rule 29(b)) — a **LIVE** hunk exists, so a CONTROL SOLVE IS EARNED

Base = `results/calibration/nyiso223_gapfill_span` meta `git_sha` **`7689d59a`** (resolves; the
keeper's own `da2e7076` is a squash-merged branch sha and its bundle is recorded `dirty:true`).

`git diff 7689d59a HEAD -- src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py
scripts/lib scripts/replay_keeper.py data/raw/_validation-source data/raw/reference` → 20 files.

**LIVE for NYISO backcast — one hunk, and it is decisive:**

* **`data/raw/reference/reliability_floor_coeffs_NYISO.csv` (1 line changed)** — the nyiso-226/227
  **NYC ST_GAS persistent-base re-basing** (0.1750 → 0.1663) landed on `main` at `8aa5eadc` as an
  artifact with no flag. It is on the NYISO backcast solve path, it moves ST_GAS dispatch and price,
  and the keeper's committed bundle **predates it**. G-CTRL form 4 is therefore **FALSIFIED** for this
  session: the committed keeper is not a valid control.

**INERT for NYISO backcast, with reason:** `spp_curtailment_share.csv` + `scripts/lib/spp63_g5.py` +
`data/curtailment_share.py` (SPP-only artifact/branch); `interchange/caiso.py` (another ISO's
branch); `forecast_parity_registry.py` (forecast namespace, a `mode="backcast"` run never enters it);
`scenarios.py`/`constants.py` additions (new default-off fields absent from the keeper recipe —
re-verified: the keeper `run_config.json` gains **zero** new armed fields at HEAD);
`solve_surface_declared.py` (+4 declared drops, no NYISO row re-keyed); `lp/model.py` (the
`ee40acd2` memory-hygiene release of the cost vector — allocation only, no coefficient);
`pipeline/ttc.py`, `fleet/arrays.py`, `data/outages.py`, `data/renewables.py`, `runner.py`,
`run_calibration*.py`, `replay_keeper.py` (new gated paths, all default-off and absent from the
recipe).

**Consequence, declared before any solve: arm C below is a real control solve, earned by a named
LIVE hunk, not a habit.** It is also the deliverable the owner asked for in its own right — the
keeper recipe on **all four years at HEAD**.

---

## 3. THE THREE ARMS — two separate variables plus their control

| arm | bundle | variable | one-line claim |
|---|---|---|---|
| **C — CONTROL** | `nyiso228_control_span` | none (keeper recipe at HEAD) | the 2022–2025 baseline the LIVE hunk requires, and the "all years" run |
| **A — TAIL** | `nyiso228_tail_span` | `offer_curve_by_group[*].peak` **×1.50** | the absent upper tail is an offer-surface object; steepen only the peak band |
| **B — SEAM-R** | `nyiso228_seamr_span` | `nyiso_import_reconciliation` **True → False** | falsify nyiso-99's standing caveat that the reconciled monthly import quota is met at the WRONG HOURS |

All three are solved on **2022 · 2023 · 2024 · 2025**, each as ONE recipe into ONE bundle
(rule 16 `[R-ALLYEARS]`), each in its own container (rule 32).

**Base command (identical for all three, arm delta appended):**

```
python3 scripts/replay_keeper.py results/calibration/nyiso223_gapfill_span \
  --set nyiso_hub_gap_month_level=false \
  --out-dir results/calibration/<arm bundle> --years <YEAR> [--reuse-solved <same dir>]
```

`--set nyiso_hub_gap_month_level=false` returns the gapfill base to the **keeper recipe exactly** —
measured, zero-LP: the only two `scenario_config` differences between `nyiso223_gapfill_span` and the
keeper `nyiso_fuelvintage_A` are `weather_year` (2023 vs 2022) and `gas_price_override` (2.54 vs
6.45), both of which are the *first solved year's* resolved values and not recipe deltas, plus the
two keys the gapfill bundle adds (`nyiso_hub_gap_month_level`,
`ercot_ep_gas_basis_receipts_fallback`, the latter an ERCOT field). **One field is disarmed; nothing
else moves.**

### 3.1 ARM A — the authorized channel, declared

**Channel:** `offer_curve_by_group` band multipliers, **`peak` ONLY**. This is rule 1
`[R-STRUCT]`'s 2026-09-05 owner carve-out, and every condition is met and stated here:

* **(a)** the `peak` band alone. **NEVER** `phys_committed` / `phys_econ_low` / `phys_econ_high` /
  `phys_peak` (measured physics), **NEVER** `econ_low_share` / `pct_peaking` (structural shares), and
  no adder, offset, haircut, proxy or rescaled measured input. `committed` / `econ_low` / `econ_high`
  are **untouched** — that is what separates this from nyiso-222.
* **(b)** **ONE config across EVERY scored year.** The same file is used for 2022, 2023, 2024, 2025.
  No per-year value exists or will be created.
* **(c)** **Set ex ante, declared here, NEVER swept.** The factor is **×1.50**, fixed before the first
  LP, and **it will not be re-cut to make any gate pass** — that is the fitted-mechanism selection the
  rule forbids, and if ×1.50 misses, the RESULT says so and the arm is reported as it landed.
* **(d)** merit-order movement across classes is an **intended** effect.
* **(e)** the run declares `authorized_price_tuning` in its attestation and carries the factor as a
  **free parameter in the DOF ledger** (rule 21 `[R-DOF]`), identification source
  **"price residual, authorized channel (rules 1/13 amendment 2026-09-05)"** — the rule-20 cross-ref's
  own wording, not a measured source.

**SIZING, ex ante (rule 20 cross-ref: the price residual IS the authorized identification for this
channel).** The actual/model ratio at **p99** — the statistic closest to the band being moved and
*not* any gate — is 118/63 = **1.87** (2023), 139/116 = **1.20** (2024), 220/177 = **1.24** (2025);
mean **1.44**, rounded to **1.50** so 2022's larger gap is also carried. It is deliberately far below
the top-100-hour ratio (2.7–3.2×), because the peak band prices only the top tranche and a move
sized on the whole tail would blow C3a. **This number is now frozen.**

**Scope — generated deterministically from the keeper's own `run_config.json`, never hand-typed**
(`results/calibration/nyiso228_peak_x150.json`, committed with this doc): the 10 router-valid classes
that carry a `peak` entry.

```
CC_CHP 2.25→3.375 · CC_REGULAR 2.25→3.375 · COAL 1.45→2.175 · COAL_BIT 1.45→2.175
COAL_LIGNITE 1.55→2.325 · COAL_PRB 1.48→2.22 · COAL_WC 1.2→1.8 · CT_CHP 1.0→1.5
CT_PEAKER 4.0→6.0 · ST_GAS 4.2→6.3
n_classes 10   n_bands 10   every ratio exactly 1.5000000000
```

Excluded and why: `CC_INTERMEDIATE` / `CT_INTERMEDIATE` / `ST_GAS_INTERMEDIATE` are refused by the
offer-curve router **and** dead for NYISO (`cc_intermediate_split` / `ct_intermediate_split` /
`st_gas_intermediate` all False). `ST_CHP` is router-valid and genuinely dispatched but has **no
registered `peak` band** — inventing one would be a NEW value, which rule 1(a) forbids; its absence
is a known limit on the channel's reach, not an oversight. The keeper's `offer_curve_overrides` is
`{}`, so `--offer-curve-json` replaces nothing.

**Delta:** `--offer-curve-json results/calibration/nyiso228_peak_x150.json`

### 3.2 ARM B — a DIAGNOSTIC, and it is declared as one

`nyiso_import_reconciliation` bands the priced import node's **monthly** net interchange to the
measured EIA-930 monthly total. Its own matrix row carries nyiso-99's **STANDING CAVEAT**: *"the
reconciled monthly quota is met at the WRONG HOURS."* No session has ever measured that claim by
removing the band. This arm does exactly that and nothing else.

**It is NOT a promotion candidate** unless **both** hold: (i) `interchange` hourly `r` improves in
**≥3 of 4** years, **and** (ii) annual net interchange stays within **±5 %** of the measured EIA-930
total in **every** year. Rule 14 `[R-ACCURATE]` is why the bar is two-sided: the band is a measured
input, and trading a measured annual level for a better hourly `r` is not automatically an
improvement. If either leg fails, the arm's result is a **measurement that closes the question**, the
bundle is gitignored and the cell is stamped, exactly as rule 15 and rule 29(c) direct.

**Delta:** `--set nyiso_import_reconciliation=false`

---

## 4. PRE-REGISTERED GATES — STOP-ONLY, STRUCTURAL, AND NONE READS THE TARGET RESIDUAL

Rule 29 `[R-SCREEN]`: a gate **may kill an arm; it may never promote one**.

**Screen years, named BEFORE the solve, on each mechanism's OWN measured footprint (never the
residual):**

* **ARM A → 2025.** The peak band's own energy is largest there: `CC_REGULAR` peak
  **1.1316 TWh / 3.26 %** of the class (vs 0.4122/1.23 % in 2023, 0.5293/1.45 % in 2024, 0.2309/0.64 %
  in 2022 — `_nyiso210_cc_overrun_attribution.json`), and `CT_PEAKER` 1.343 TWh (vs 0.397/0.368).
  The arm shard therefore solves **2025 first**.
* **ARM B → 2023.** The band's own correction is largest there: the un-banded priced node clears a
  near-flat 18.5–21.6 TWh against a 2023 measured schedule of **23.45 TWh**, the widest of the four
  years (2024 20.35, 2025 19.09). The arm shard solves **2023 first**.

| gate | arm | test, on the screen year | STOP if |
|---|---|---|---|
| **G-CONF** | A | zero-LP, before the solve: diff arm vs control `run_config.scenario_config.offer_curve_by_group`. Exactly 10 values move; every one is a `peak`; every ratio is 1.5 to 10 dp; `phys_*`, `econ_low_share`, `pct_peaking`, `committed`, `econ_low`, `econ_high` byte-identical | any other key moves |
| **G-DIR** | A | model load-weighted **p99** price rises | p99 falls or is unchanged |
| **G-MAG** | A | model p99 rises by **$5–$120** | outside that band (a 1.5× on the top tranche cannot move p99 by more than ~$120, and a move below $5 means the band is inert) |
| **G-ENERGY** | A, B | total ISO model energy conserved within **0.05 TWh** of control | outside |
| **G-CLASS** | A | no class outside the 10 moved ones moves more than **1.0 TWh** | outside |
| **G-NONTARGET** | A | C1 and C2 (the non-target load-bearing criteria) do not flip PASS→FAIL | either flips |
| **G-LIVE** | B | the priced node's monthly net interchange departs from the measured series by more than the band width in **≥1 month** | no month departs → the arm is **INERT**, report and stop |

**The target criteria — C3a, C3b, C3c, D-A amplitude, interchange `r` — are NOT gates.** They are
what the arms are being measured on, and reading them as a pass/fail screen is precisely the
fitted-mechanism selection rule 1 `[R-STRUCT]` (c) forbids.

**Rule 29(a) ordering, stated rather than quietly skipped.** The rule asks for a one-year screen
before the full span. NYISO solves at **~4.5 min/year** (nyiso-227: 2023–2025 in 13 m 35 s), so a
four-year span is ~18 min of LP — screening serially and *then* spanning costs more wall-clock than it
saves. The owner's instruction this session is explicit ("shards for each years including holdouts …
launch parallel shards"). **Resolution:** each arm's shard solves its named screen year **FIRST**,
evaluates the STOP gates on it, and **aborts the remaining three years and reports if any gate
trips** — the screen's kill power is preserved in full, inside one container, at no extra cost.

---

## 5. PREDICTIONS — falsifiable, and the risks stated BEFORE the solve

**ARM A:**

1. Model p99 LW price rises in **every** year, by **$5–$120**.
2. C3c model h>$300: 2023 **2 → 2–10**; 2024 **0 → 0–4** (the model's 2024 max is $204; a 1.5× on a
   band carrying 1.45 % of CC energy may still not bridge a 47 % gap — **I expect 2024 to stay at or
   near 0 and I say so now**); 2025 **3 → 8–35**; 2022 **10 → 14–45**.
3. C3a rises in every year, by **+1 to +5 pp**: 2023 +4.3 → **+5 to +9 %**; 2024 +5.3 → **+6 to
   +10 %**; 2025 −7.1 → **−6 to −2 %**; 2022 −13.9 → **−12 to −8 %**.
4. **DECLARED RISK, not a surprise if it lands: 2024 C3a can breach +10 % and FAIL, and 2024 C3b
   (0.179, the tightest in the keeper) can breach 0.20 and FAIL.** If either happens the arm is
   reported as failing and is **not** re-cut — condition (c).
5. D-A amplitude rises **2–10 pp** in every year.
6. Interchange hourly `r` rises in **≥2** of the four years (the nyiso-99 chain predicts it; if it
   does not, that chain is wrong and I will say so).
7. C8 forced share moves **< 1.5 pp** and crosses no cap; C1 total energy moves **< 0.05 TWh**.

**ARM B:**

1. Net annual interchange departs from measured by **1–4 TWh** in 2023 (under-import) and **0–3 TWh**
   the other way in 2024/2025.
2. Interchange hourly `r` moves by **≥0.03** in at least one year. **Direction NOT predicted** — that
   is the question.
3. C1/C2 gas volume moves **1–3 TWh**; C2 may FAIL. That is the cost of the diagnostic and is
   expected, not a defect.

**ARM C:** reproduces the keeper's committed 2023–2025 C3a to within **$0.30/MWh**, except in NYC
`ST_GAS`, where the LIVE `reliability_floor_coeffs_NYISO.csv` hunk should reproduce nyiso-227's
measured span deltas (C1 ST_GAS 1.669→1.591 in 2023, 1.369→1.410 in 2024; C3a +$0.026 / +$0.028 /
+$0.025; C3b +0.00045 / +0.00019 / −0.00023). **If arm C does NOT reproduce those, the G-DRIFT audit
above is wrong and every comparison in this session is re-based on arm C rather than on the keeper.**

---

## 6. SHARD TABLE — every shard launched is listed here (protocol §9)

| shard | branch | bundle | year order | registerable |
|---|---|---|---|---|
| **C** | `claude/nyiso228-control-span` | `results/calibration/nyiso228_control_span` | 2022 2023 2024 2025 | **yes** |
| **A** | `claude/nyiso228-tail-span` | `results/calibration/nyiso228_tail_span` | **2025** 2022 2023 2024 | yes, if gates hold |
| **B** | `claude/nyiso228-seamr-span` | `results/calibration/nyiso228_seamr_span` | **2023** 2022 2024 2025 | only on §3.2's two-legged bar |

**Disjoint write sets (protocol §5).** Each shard writes **only** its own bundle dir and its own
`docs/SHARDREPORT-nyiso228-<arm>.md`. **NO shard** writes: `.gitignore`, this PRECOMMIT, `CLAUDE.md`,
anything under `src/` or `scripts/`, `frontend/data/backcast/**` (bench included — the NYISO bench
parts for 2022–2025 are already committed and no shard needs to rewrite them), the mechanism matrix,
the calibration log, or any other shard's files. **The parent alone** registers, scores, stamps the
matrix and puts the promotion question (rule 32(d)).

**Rule 22 `[R-HOLDOUT]` is REMOVED** (CLAUDE.md coda, owner 2026-09-09): 2022 needs no marker, no
`--holdout-authorized`, no one-shot. What that costs is stated rather than hidden — **no year in this
program is a certified out-of-sample number, 2022 included**, and nothing here will be quoted as one.

**Rule 31 `[R-RETAIN]`:** nothing is deleted. All three bundles stay on local disk until the owner
rules on promotion, and the promotion question is put explicitly in the final report.

