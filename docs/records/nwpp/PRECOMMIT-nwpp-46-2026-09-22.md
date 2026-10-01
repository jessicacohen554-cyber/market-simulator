# PRECOMMIT — nwpp-46: C4 is not a coal-offer defect. It is hydro over-flexibility.

**Lane:** NWPP-46 · **Date:** 2026-09-22 · **Branch:** `claude/nwpp-46-coal-amplitude-rt7r9y`
**Base SHA:** `8f3db10e81a35254730ba6311b387fcdd8aca9e5`
**Keeper / control:** `2026-09-20-nwpp-44-measured-take`, bundle `results/calibration/nwpp44_takeorpay_reg`
**LP spent by this session: ZERO** (rule 32 `[R-SHARD]` (a)). Every number below is zero-LP.
**OFF-QUEUE, declared (rule 28 `[R-MECH-MATRIX]` (a)):** NWPP's lever queue
(`docs/mechanism-testing-matrix.md` §5.9, NWPP-55..59) is forecast/topology work and
carries no C4 item. This lane goes off-queue on the charter's instruction.

---

## 0. The one-paragraph version

The charter ruled C4's amplitude defect IN on "the coal offer stack's VERTICAL EXTENT."
**NWPP's own data falsifies that, twice, and phase 0 re-routes the defect.** (1) The
shelf is not flat within a plant — `econlo == econhi == peak` **exactly** at all 17
coal plants, because `backcast_config` deep-merges `_SPP_OFFER_CURVE`, the
**identity**, for NWPP; the `$0.51/MWh` in the record is a fleet **mix** artifact, not a
within-plant slope. (2) Correcting it to NWPP's own measured CAMPD marginal heat rate
would buy a **10.4 %** ladder (~$3/MWh) — and it would be **inert anyway**, because the
price coal faces has no intra-day variation to respond to: **three of NWPP's five zones
carry exactly TWELVE distinct prices for the entire year**, one per month. The marginal
unit is hydro, its monthly-budget dual is a month-constant water value, and the model's
hydro does **114–138 %** of the real diurnal swing while coal does 4–10 % and gas 65–69 %.
On the additive h19−h11 ramp metric, hydro's excess ramp accounts for **69 / 87 / 102 %**
of the coal+gas ramp deficit. The lever is therefore the **two-sided measured hydro
capability envelope** (`hydro_dispatch_envelope` + `hydro_min_flow_floor`) — one
mechanism, two mirrored halves, **zero free parameters**, built from NWPP's own EIA-930
`NG: WAT` meter. It is pre-registered below with a two-sided kill condition, and it is
predicted **NOT** to clear C4's 0.70 floor in any year.

---

## 1. Lever (C) is decided by the committed diagnostics, and it is ruled OUT

The charter said to run the D-2/D-4 attribution first because it is free and may decide
the question. It did. From the keeper's committed `legitimacy_diagnostics.json`:

| year | class | mechanism | forced TWh | share |
|---|---|---|---|---|
| 2023/24/25 | **COAL** | — | **0.0** | **0.0** |

D-2 carries exactly two floor mechanisms in NWPP — `nuclear_mustrun` and `chp_steam` —
and **D-4 has no coal row at all**. There is no coal commitment floor in this keeper, so
there is no floor "binding in hours its own driver says the class is offline" (rule 17
`[R-FLOOR-WINDOW]`). Coal is price-insensitive because it is priced below anything the
day ever rejects, not because it is forced. **Lever (C) is closed on measurement.**

D-1 corroborates the defect from a second instrument: coal's off-peak CV ratio is
**0.022–0.147** against a 0.50 floor (model CV 0.002–0.005, actual 0.029–0.106), failing
in all three years for all three coal ranks. The model's coal is a near-constant.

## 2. Lever (A) is falsified on NWPP's own data — the premise is a mix artifact

`scripts/probes/_nwpp46_coal_stack_phase0.py` rebuilds the keeper fleet through the
sanctioned `replay_keeper` path (`run_year(..., fleet_only=True)`) and reads the
assembled P0 `mc_base` the LP is handed. **Per plant, `econlo == econhi == peak` to the
cent, at every one of the 17 plants** (2023 shown; 2024/2025 identical in structure):

| plant stem | mustrun | committed | econlo | econhi | peak | dispatchable spread |
|---|---|---|---|---|---|---|
| `COAL_NWPP-EAST_p8066` | 4.50 | 4.50 | 42.62 | 42.62 | 42.62 | $38.12 |
| `COAL_NWPP-EAST_p6165` | 5.04 | 5.04 | 33.96 | 33.96 | 33.96 | $28.92 |
| `COAL_NWPP-NW_p3845`   | 4.50 | 35.95 | 35.95 | 35.95 | 35.95 | $0.00 |
| *(14 more, same signature)* | | | | | | |

Fleet cap-weighted: `mustrun` $5.79 · `committed` $12.27 · `econlo` $34.80 · `econhi`
$34.80 · `peak` $33.23. **The econ-range spread is $0.00/MWh.** The `$0.51` NWPP-43 §4.1
reported is the difference between *fleet averages over different plant mixes*, not a
slope any plant offers. The cause is structural and traceable:
`backcast_config.py:2372` deep-merges `_SPP_OFFER_CURVE` for `iso in ("SPP","NWPP")`, and
its `_SPP_COAL_IDENTITY_BANDS` are **1.0 on every band** — a posture declared by lane
NWPP-20 before any NWPP solve existed, to avoid transplanting ERCOT's fitted bands under
rule 25 `[R-ISO-SCOPE]`. The generic base (`GENERIC_BASE_OFFER_CURVE["COAL_BIT"]`) is
sloped (econ_low 0.95 → econ_high 1.10 → peak 1.45); NWPP overrides it to flat.

### 2.1 And correcting it measures out at 10.4 %, not 53 %

`scripts/probes/_nwpp46_marginal_hr_phase0.py` reproduces the shared WP-3 construction of
`scripts/data/derive_campd_marginal_hr.py` **band for band** (same steady-state screen,
same LSL/HSL p3/p97, same band edges, same normalized-quadratic I/O fit), over 511,855
steady-state coal unit-hours from NWPP's own CEMS, 2023–2025. Two declared departures:
the class map comes from NWPP's own rebuilt fleet (`bin_assignments_NWPP.csv` does not
exist — owner ruling N8, established by NWPP-43), and it reports per plant as well as per
class. Fuel identification reads `primaryFuelInfo`, NWPP-42's own declared departure.

| band | measured multiplier (cap-wtd, own-HR basis) |
|---|---|
| `marg_committed` | 0.821 |
| `marg_econ_low` | 0.932 |
| `marg_econ_high` | 1.004 |
| `marg_peak` | 1.029 |

`econ_high / econ_low` = **1.077** (p25 1.052 · p50 1.082 · p75 1.123; 17 of 24 units
above 1.05). That ratio is basis-independent — the normalization cancels — so it stands
whatever HR basis is chosen. **NWPP's coal does meter a rising incremental cost, and it
is 7.7 % across the economic range, 10.4 % across the whole dispatchable range** (~$3/MWh
on a $35 offer). That is a real correction and it is **not** the 0.9–1.7 GW of missing
diurnal swing.

## 3. Why no coal offer lever could have worked — the price has no intra-day variation

The decisive measurement. Model P1 zonal price, from the keeper's own committed
`hourly/system_<year>.parquet`:

| year | zone | distinct prices / YEAR | median distinct / day | mean dayMax−dayMin |
|---|---|---|---|---|
| 2023 | NWPP-INLAND / NW / OR | **12** | **1** | **$0.00** |
| 2024 | NWPP-NW / OR | **12** | **1** | **$0.00** |
| 2025 | NWPP-INLAND / NW / OR | **12** | **1** | **$0.00** |
| 2023–25 | NWPP-EAST | 84 / 187 / 218 | 1 / 3 / 4 | $1.74 / $2.56 / $4.06 |
| 2023–25 | NWPP-SNV | 191 / 226 / 268 | 6 / 6 / 7 | $46.13 / $42.85 / $5.78 |

**Twelve distinct prices for a whole year is one per month.** In three of five zones the
LP price is a monthly step function, literally constant within the month, while the
*annual* spread is wide (p10 $21.74 → p90 $52.50 in 2023). A coal plant facing a
within-month-constant price runs flat-out or not at all for the whole month, whatever
ladder its offer carries. **A $3/MWh ladder against a price with zero intra-day variance
is inert by construction** — which is why NWPP-44's volume fix moved `r` by only 0.035.

This also explains the C4 decomposition NWPP-45 measured and could not attribute:
`r_monthly` 0.686–0.866 (the price moves monthly, so the model gets the month right),
`r_daily` 0.645–0.715, `r_intraday` **0.218–0.425** (the price does not move intra-day, so
the model cannot get the hour right).

## 4. What it IS — hydro absorbs the diurnal duty, measured on both sides

Mean diurnal profile, peak-to-trough, model vs the same EIA-930 series the scorer uses:

| class | 2023 model / actual (ratio) | 2024 | 2025 |
|---|---|---|---|
| COAL | 0.090 / 0.892 (**0.10**) | 0.068 / 1.302 (**0.05**) | 0.063 / 1.683 (**0.04**) |
| **HYDRO** | 6.272 / 5.511 (**1.14**) | 6.256 / 5.214 (**1.20**) | 6.192 / 4.477 (**1.38**) |
| GAS | 1.868 / 2.711 (0.69) | 2.052 / 3.141 (0.65) | 2.311 / 3.491 (0.66) |
| SOLAR | 3.776 / 3.773 (1.00) | 4.919 / 4.914 (1.00) | 5.831 / 5.820 (1.00) |
| WIND | 0.520 / 0.578 (0.90) | 0.549 / 0.544 (1.01) | 0.710 / 0.710 (1.00) |

Hydro mean **level** is right (12.200 / 12.315 / 12.908 GW against 11.899 / 11.991 /
12.588). Solar and wind match at ratio 1.00, so this is not a renewables-shape artifact.
It is a pure **shape redistribution**: hydro is doing the diurnal duty coal and gas
should be sharing. And the ratio **worsens** year on year (1.14 → 1.38) exactly as real
hydro flexibility falls (5.511 → 4.477 GW) while the model's stays pinned near 6.2 —
with coal's ratio worsening 0.10 → 0.04 in lockstep. Two sides of one object.

On the **additive** h19−h11 evening-ramp metric (max−min occurs at different hours per
class, so it does not sum; h19−h11 does):

| year | coal gap | gas gap | **hydro excess** | share of coal+gas gap explained |
|---|---|---|---|---|
| 2023 | +0.830 | +0.858 | **−1.170** | **69 %** |
| 2024 | +1.234 | +0.919 | **−1.875** | **87 %** |
| 2025 | +1.623 | +0.968 | **−2.652** | **102 %** |

The residual (0.583 / 0.617 / 0.429 GW) sits on `other` (biomass/geothermal, which the
model runs at 0.000 swing) and the battery/interchange legs. Named, not absorbed.

**Mechanism:** the hydro budget row is `min ≤ Σ_month P ≤ energy` (`model/lp/rows.py:445`)
— an energy cap with no intra-month shape constraint. The LP may reallocate a whole
month's water with perfect foresight at a constant water value. So it shapes hydro to
load, the price flattens to the water value, and every thermal class loses its signal.

## 5. THE LEVER, pre-registered

**`hydro_dispatch_envelope=true` + `hydro_min_flow_floor=true`, NWPP, backcast.**

This is **ONE mechanism, TWO MIRRORED HALVES**, never armed apart — the repo states it
in the constants themselves: `HYDRO_MIN_FLOW_PERCENTILE = 100.0 - HYDRO_ENVELOPE_PERCENTILE`,
and *"It is the exact MIRROR of HYDRO_ENVELOPE_PERCENTILE (95 → 5), so the floor adds NO
new free parameter — the two-sided envelope is identified by the one percentile the
ceiling already carries (DOF ledger: 0 new DOF)."* Read as an exceedance level the floor
is **Q95**, the standard hydrological low-flow index FERC-licence minimum-flow conditions
are themselves written against.

* **Ceiling** (caiso-72): cap the fleet's hourly dispatch at the measured p95 of NWPP's
  own EIA-930 `NG: WAT` in that (month × hour-of-day) bucket — the head/flow/scheduling
  deliverability ceiling nameplate `pmax` ignores.
* **Floor** (caiso-124): hold each plant at a **month-constant** pro-rata share of the
  fleet's measured monthly Q95 sustained level. The bucket is the month ALONE, never
  (month × hour-of-day) — a floor carrying the measured diurnal shape would pin dispatch
  to the measured outcome (rule 13 `[R-MEASURED]`); a month-constant level leaves the LP
  free to choose *when* to generate above it.

**Rule 25 `[R-ISO-SCOPE]`: NOTHING is transferred from CAISO.** The envelope is built
from NWPP's own meter; the percentile is the shared structural convention carried in
`constants.py`, not an ISO-fitted number. NWPP's cells are `U` in the matrix shard, so
rule 28(a) DO-NOT-REDO does not bind.

**Rule 21 `[R-DOF]` / 24 `[R-REGISTRY]`: ZERO new free parameters, ZERO code change.**
Both flags are existing `ScenarioConfig` fields on the calibration CLI
(`--hydro-dispatch-envelope`, `--hydro-min-flow-floor`, tri-state) and are recorded in
`run_config.json`. No `src/` or `scripts/` edit is required to arm this.

**Rule 17 `[R-FLOOR-WINDOW]`, for the floor half.** (a) Driver: run-of-river inflow that
cannot be stored, plus the environmental / FERC-licence minimum releases every licensed
project must pass. (b) Window: all 24 hours — inflow and licence releases are
around-the-clock, the opposite of the CT overnight-offline signature; it binds where the
economic solution would sink below the sustained level. (c) Forward story: re-derives from
the same EIA-930 `NG: WAT` history (the solve year's own series in a backcast, the pooled
`HYDRO_CLIMATOLOGY_YEARS` per-month percentile forward) and responds to the water year
through the budget it is clipped against.

**C8 is not at risk:** `MECH_HYDRO_MIN_FLOW` is classed NON-THERMAL forcing —
*"reported by D-2 but excluded from the merchant thermal forced-share arithmetic"*.

### 5.1 Where it binds, measured exactly (`_nwpp46_hydro_envelope_phase0.py`)

| year | ceiling breach | energy above | concentration | floor underrun | energy below | concentration |
|---|---|---|---|---|---|---|
| 2023 | 21.7 % of h | 1.864 TWh | h16–h21 (29–35 %) | 10.4 % of h | 0.866 TWh | h12–h14, h1–h3 |
| 2024 | 23.7 % of h | 2.359 TWh | h17–h22 (34–40 %) | 12.9 % of h | 1.185 TWh | h11–h14, h1–h2 |
| 2025 | 23.4 % of h | 2.684 TWh | h17–h22 (35–47 %) | 14.0 % of h | 1.526 TWh | h9–h14 |

The two halves bind in **disjoint hours** and in the hours their own drivers name: the
ceiling on the evening ramp (the hoarding), the floor in the solar belly and overnight
shoulder — exactly what the caiso-124 field docs predict. That disjointness is the
rule-19 `[R-ONE-MECH]` evidence that they are one reconciled family, not a stack.

## 6. PREDICTIONS, ex ante, in C4's own currency

From the static two-sided clip of the keeper's own hourly hydro. **These are predictions
from a clip, not solve results**: the budget row reallocates the clipped energy and the
LP re-prices, neither of which a clip models.

**(a) HYDRO amplitude ratio — the mechanism's OWN signature, computed exactly:**

| year | now | ceiling only | **predicted two-sided** |
|---|---|---|---|
| 2023 | 1.14 | 1.10 | **1.05** |
| 2024 | 1.20 | 1.16 | **1.10** |
| 2025 | 1.38 | 1.26 | **1.16** |

**(b) Duty released to thermal (h19−h11):** **0.351 / 0.566 / 0.957 GW** = **21 / 26 /
37 %** of the measured coal+gas ramp gap.

**(c) COAL amplitude ratio.** A static merit screen over the evening hours (h17–h22)
puts coal at **12–21 %** of the capacity within $2–$10/MWh above the clearing price, gas
at the rest. Applying that share to (b):

| year | coal amplitude ratio now | **predicted** |
|---|---|---|
| 2023 | 0.10 | **0.15 – 0.18** |
| 2024 | 0.05 | **0.11 – 0.14** |
| 2025 | 0.04 | **0.10 – 0.16** |

i.e. the ratio roughly **doubles to triples** and remains far below 1.0.

**(d) C4 metrics. THE LEVER IS PREDICTED NOT TO CLEAR THE GATE.**

| year | `r` now | **predicted `r`** | NRMSE now | **predicted NRMSE** |
|---|---|---|---|---|
| 2023 | 0.605 | **0.61 – 0.66** | 0.260 | 0.24 – 0.28 |
| 2024 | 0.595 | **0.60 – 0.65** | 0.246 | 0.23 – 0.27 |
| 2025 | 0.610 | **0.62 – 0.67** | 0.284 | 0.26 – 0.30 |

**C4 is predicted to remain a FAIL in all three years.** Tripling one-twentieth of the
real amplitude is still a small fraction of it. Per the charter and rule 1 `[R-STRUCT]`,
**C4 is not a promotion criterion in either direction**: this lever is admissible because
a head/flow deliverability ceiling and a licence minimum-flow release are real features of
how this fleet operates, not because `r` moves.

**(e) C1 rows expected to move, direction stated BEFORE the solve.**

* **2023 `CC_REGULAR` — the one failing C1 row** (47.996 vs 56.215, −8.219 TWh, band
  ±8.00, **miss 0.219 TWh**). I expect it to **IMPROVE** (move up toward actual). Reason:
  the budget row's upper bound is a **cap, not an equality**, so water the ceiling refuses
  in the evening need not all be re-placed; any hydro energy not recovered falls to the
  marginal class, which is `CC_REGULAR`. **I do not predict it clears** — only 0.219 TWh
  is needed, but how much hydro energy is actually lost is a solve question.
* **2023 `COAL_BIT` — the named C1 RISK** (+3.670 TWh over actual, band ±8.00). Coal
  gaining evening duty pushes it further over. This is the row to watch.
* **Gas rows generally** gain more than coal (79–88 % of the release by the §6c screen).

## 7. KILL CONDITION — two-sided, pre-registered, NOT renegotiable after the fact

Denominated in quantities computed exactly above, from artifacts the solve will produce.

* **INERT limb ⇒ verdict `I`.** If the solved **hydro** amplitude ratio does not fall by
  at least **0.03** in *every* year — i.e. if 2023 ≥ **1.11**, 2024 ≥ **1.17**, or 2025 ≥
  **1.35** — the mechanism did not do what its own exactly-computed signature says it
  must, and the arm reads INERT whatever C4 does.
* **OVERSHOOT limb ⇒ verdict `R`.** Any one of:
  (a) the solved hydro amplitude ratio falls **below 0.90** in any year (the model now
  under-swings hydro — a ceiling that over-binds);
  (b) any C1 **COAL** row leaves its ±8.00 TWh band;
  (c) NWPP hydro **annual energy** moves by more than **5.0 TWh** in any year
  (106.872 / 107.879 / 113.077 TWh now) — the envelope is a shape constraint and must not
  become a volume mechanism.

A C4 `r` that fails to clear 0.70 is **not** a kill limb, by §6d and rule 1.

## 8. G-DRIFT (rule 29 `[R-SCREEN]` (b) form 4) — the keeper IS the control, no control solve

Keeper `git_sha` `ee276d87` → base `8f3db10e`. 29 files changed on the solve path
(5,983 insertions). Rather than classify 5,983 lines by hand, this lane ran the
**mechanical** test: a `git worktree` at `ee276d87`, the keeper's own recipe rebuilt
through `replay_keeper` on both trees, and the LP input arrays diffed.

| array | 2023 | 2025 |
|---|---|---|
| `unit_ids` | IDENTICAL (646 rows) | IDENTICAL (642 rows) |
| `mc` (646 × 8760) | max\|Δ\| **0** | max\|Δ\| **0** |
| `pmax` / `pmin` / `heat_rate` / `vom` / `availability` | max\|Δ\| **0** | max\|Δ\| **0** |
| `demand` | max\|Δ\| **0** (270.460804 TWh) | max\|Δ\| **0** (288.698368 TWh) |

**Every LP input is bit-identical across the drift**, which covers all 29 changed files on
the input path at once. The remaining surface is the LP build/solve itself, classified by
hunk: `rows.py` is a pure `_add_bounds` accumulator refactor carrying an explicit
promotion-equivalence claim; `model.py`/`lp/__init__.py` add `full_extract`, which skips
**P0** diagnostic extraction only and *"does not change a single LP row, coefficient, bound
or objective entry, nor touch HiGHS at all"*; `solve.py` un-nests the same-year P1 basis
seed — **the one hunk worth naming** — but `resolve_p1_basis_seed_default` still defaults
**OFF** (precedence rule 3), and `replay_keeper.py` pins `MARKET_SIM_P1_BASIS_SEED=0` and
`MARKET_SIM_WARMSTART_XYEAR=0` regardless (rule 36 `[R-YEAR-ISOLATION]` (d)). **All hunks
INERT ⇒ form 4 is valid and no control solve is spent.**

## 9. How it will be solved

Three **year-isolated** shards (rule 36 `[R-YEAR-ISOLATION]`), own container, own
`--out-dir`, pinned to a full 40-char SHA. Each runs, unmodified:

```
python3 scripts/replay_keeper.py results/calibration/nwpp44_takeorpay_reg \
  --out-dir results/calibration/nwpp46_hydroenv_<YEAR> \
  --years <YEAR> \
  --set hydro_dispatch_envelope=true \
  --set hydro_min_flow_floor=true \
  --note "nwpp-46: two-sided measured hydro capability envelope"
```

`replay_keeper` is used **instead of a hand-built `run_calibration_full` CLI**
deliberately: it replays the keeper's own `meta.json`, which is what carries
`hydro_backfill_year=2024` — the loader kwarg whose omission silently invalidated
NWPP-44's entire first shard wave (`ADDENDUM-nwpp-44-hydro-backfill-2026-09-20.md` §4:
*"A keeper's recipe is NOT fully described by its ScenarioConfig"*). Verified before
launch: `meta.json` carries `coal_prb_sigmoid_overrides {"hydro_cascade_coupling": true}`,
`replay_keeper` maps that key to `prb_overrides` (line 65), and `--set` **merges** into it
via `setdefault` + item-assign (lines 1003–1004), so the keeper's armed cascade coupling
**survives the arm**. `EIA930_PS_FOLDED_INTO_WAT = {MISO, PJM}` does not contain NWPP, so
neither half is refused.

Each shard pushes its FULL bundle including `dispatch/<year>_P1.parquet` (rule 34
`[R-SHARD-PROMOTABLE]` (a)) via a `.gitignore` NEGATION + a PLAIN `git add`. The parent
runs ZERO LP, composes, scores, registers and lands the composite on `main` before this
PR merges (rule 33 `[R-SHARD-ARCHIVE]` (f)).

## 10. Carried, absorbed nowhere

* Every NWPP-40/41/42/44/45 disclosure is inherited verbatim, including the **−10.02 TWh
  2025 energy balance** against a ±3.0 tol and the C1 demand-basis gap of
  **−9.645 / −12.144 / −9.107 TWh** whose three framings are an **OPEN OWNER DECISION**
  (`FINDING-nwpp-45` §8). This lane does not touch the demand construction.
* **NWPP is PRICE UNSCORED** (rubric v3.8): C3a/b/c are not scored in any year. §3's price
  measurements are used as *evidence about the model's own price formation*, never as a
  claim about NWPP's real prices. `authorized_price_tuning = NONE` — no
  `offer_curve_by_group` band multiplier is touched.
* **The coal offer identity stays as it is, and that is now a KNOWN, MEASURED
  understatement.** §2.1 measures the correct ladder at committed 0.821 / econ_low 0.932 /
  econ_high 1.004 / peak 1.029. It is **not armed here** because §3 shows it would be inert
  against a month-constant price, and arming an inert mechanism would spend LP to learn
  nothing. It is routed as a successor question *after* the price acquires intra-day
  variation, not dismissed.
* **C5a CO2** remains a reported-only FAIL. **Chief Joseph's pond dual** (−325.17
  $/kcfs·h for 5,808 h of 2025) is untouched — and note it sits in the same family as this
  arm; any interaction is reportable.
* **EIA-930 2025 hydro carries a −44,969 MW hour** in the benchmark series. It does not
  affect the p95 ceiling (robust) but it is on the record as a benchmark-side defect.
* **`Jim Bridger` absent from `thermal_tranches_NWPP.csv`**; the NWPP-40/41/42 attestation
  corrections (`use_campd_bins` is NOT inert, `thermal_tranches_NWPP.csv` IS read) are
  **still owed** and are not discharged here.
* Pre-existing test failures belong to other lanes. This lane's
  `git diff --name-status origin/main...HEAD -- src scripts` carries **no `M` rows under
  `src/`** — only added probe files, which no module imports.

## 11. Reproduction

```
PYTHONPATH=.:src python3 scripts/probes/_nwpp45_c4_decomposition.py
PYTHONPATH=.:src python3 scripts/probes/_nwpp46_coal_stack_phase0.py
PYTHONPATH=.:src python3 scripts/probes/_nwpp46_marginal_hr_phase0.py
PYTHONPATH=.:src python3 scripts/probes/_nwpp46_hydro_envelope_phase0.py
```

All four need the restored shared store:
`python3 scripts/run_calibration_full.py --restore-shared-inputs results/calibration/nwpp44_takeorpay_reg`
