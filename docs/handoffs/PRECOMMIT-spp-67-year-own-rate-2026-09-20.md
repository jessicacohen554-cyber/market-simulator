# PRECOMMIT — SPP-67. The wind excess is 100 % gross-up headroom, the gross-up rate is a **2023–2025 mean applied to seven years**, and the window that excludes SPP's other published rates is **residue of a rule the owner removed**.

**Lane** SPP-67 · **Mechanism** `vre_reference_rate_year_own` (NEW, shared gate, dataclass default
`False`, SPP-wind-only provider) · **Control** keeper 13's and its rung's **committed** bundles,
differenced, never re-solved (rule 29(b) form 4 — G-DRIFT audit in §6) · **Seven shards, one per
year 2019–2025** (rules 34(c) / 36 `[R-YEAR-ISOLATION]`).

Everything below §5 is written **before any arm is solved**. §5 is the pre-registration.

---

## 1. THE CHARTERED HYPOTHESIS IS FALSIFIED ON THE KEEPER'S OWN SPAN

The charter asked whether SPP's modelled wind CF is too high **at source** — whether the
reference-rate gross-up over-states available wind energy. On 2023–2025 it does not. The in-force
rate is within **1.3 %** of each of those years' own published rate, and using each year's own rate
makes **two of the three years worse**. That half of the card is dead and this lane does not
re-open it.

What phase 0 found instead is a defect the charter did not anticipate, in a different place.

## 2. THE DECOMPOSITION (charter step 1). It closes exactly, and it has one term.

Measured at zero LP on keeper 13's (`spp51_syncfloor_span`, 2023–2025) and its rung's
(`spp51_syncfloor_rung`, 2019–2022) **committed** `hourly/` sidecars and registered payloads.
Probe: `scripts/probes/_spp67_wind_decomposition.py`.

First, the benchmark's basis, reproduced before anything is compared against it — the scored C1
wind benchmark **is** EIA-930 SWPP `WND` on a fixed-CST 8760 index with the 2023 corrupt hour
screened and Feb 29 dropped (max |diff| **0.013 TWh**, which is the payload's own 2-dp rounding).
Traps (e) and (f) are discharged there, not asserted.

| year | model | bench | **EXCESS** | CAPACITY | **CF LEVEL** | SHAPE | −SPENT | sum-chk |
|---|---|---|---|---|---|---|---|---|
| 2019 | 85.2609 | 77.0300 | **+8.2309** | +0.0000 | **+8.2277** | +0.0000 | +0.0007 | +0.0024 |
| 2020 | 90.6257 | 82.0300 | **+8.5957** | +0.0000 | **+8.7627** | +0.0000 | −0.1787 | +0.0116 |
| 2021 | 101.8115 | 92.8600 | **+8.9515** | +0.0000 | **+9.9177** | +0.0000 | −0.9608 | −0.0053 |
| 2022 | 117.7457 | 107.4400 | **+10.3057** | +0.0000 | **+11.4756** | +0.0000 | −1.1713 | +0.0014 |
| 2023 | 113.2333 | 103.0500 | **+10.1833** | +0.0000 | **+11.0066** | +0.0000 | −0.8227 | −0.0006 |
| 2024 | 120.3667 | 109.3200 | **+11.0467** | +0.0000 | **+11.6750** | +0.0000 | −0.6156 | −0.0126 |
| 2025 | 121.6983 | 110.4600 | **+11.2383** | +0.0000 | **+11.7974** | +0.0000 | −0.5529 | −0.0062 |

- **CAPACITY = 0.0000 TWh**, by construction and by measurement. The bound is
  `delivered_cf(t)/(1−r) × capacity` and `delivered_cf` is built as `delivered_MWh/capacity`, so
  capacity cancels identically. The sum-check is the residual of that claim and it is ≤ the
  benchmark's own rounding in all seven years.
- **SHAPE = 0.0000 TWh on energy.** A scalar factor preserves the delivered shape exactly; the
  hourly correlation is **0.953–0.973** and the model/930 ratio is flat at 1.096–1.107.
- **CF LEVEL is 100 % of the residual**, less the 0.00–1.17 TWh the LP re-curtails.

Mean excess over the seven registered years is **+9.7932 TWh**. The charter quotes **+10.144**;
that is SPP-50's number on a **different keeper**, and keeper 13's coal sync floor spends slightly
more of the headroom. The difference is the keeper, not a disagreement.

## 3. THE SOURCE (charter step 3): MEASURED, zero free parameters — and read over a window that a **deleted rule** set

`_spp_wind_reference_curtailment_rate` = **0.0965013** → ×**1.106808**. Both legs measured, from two
independent SPP publications (MMU ASOM average hourly curtailment MW; SPP GenMix 5-minute
`Wind Market` + `Wind Self`). Nothing about the *construction* is wrong.

What is wrong is the **window**. `_SPP_REFERENCE_RATE_YEARS` is frozen at `{2023, 2024, 2025}`, and
its own comment gives the entire reason:

> *"the structural rate must never read a validation or locked-test year (SPP's table also carries
> 2019 and 2022 rows, both holdout years, and both are excluded here by construction rather than by
> discipline)"*

**Rule 22 `[R-HOLDOUT]` was REMOVED by owner instruction on 2026-09-09** (CLAUDE.md rule 22 coda:
*"Any year may now be solved, scored and registered with no authorization"*). The exclusion now
rests on nothing, while still suppressing measurements that sit **in the same committed table, from
the same source documents, on the same average-MW basis**.

SPP's per-year rates, with the delivered leg re-derived from the committed GenMix CSVs on SPP-32's
construction — which **reproduces the committed 2023–2025 rows exactly** (11818.9002 / 12559.0281 /
12583.4630 against 11818.9 / 12559.0 / 12583.5), and that reproduction is what licenses extending
it to the years it never covered:

| year | ASOM MW | GenMix MW | own rate | own 1/(1−r) | in force | ratio | source |
|---|---|---|---|---|---|---|---|
| 2019 | 137 | 8474.9 | **0.015908** | **1.016165** | 1.106808 | **0.9181** | published |
| 2020 | — | 9337.1 | — | — | 1.106808 | 1.0000 | **NOT published** → keeps the reference mean |
| 2021 | — | 10656.2 | — | — | 1.106808 | 1.0000 | **NOT published** → keeps the reference mean |
| 2022 | 1260 | 12206.1 | 0.093568 | 1.103227 | 1.106808 | 0.9968 | published |
| 2023 | 1097 | 11818.9 | 0.084934 | 1.092817 | 1.106808 | 0.9874 | published |
| 2024 | 1483 | 12559.0 | 0.105612 | 1.118083 | 1.106808 | 1.0102 | published |
| 2025 | 1382 | 12583.5 | 0.098958 | 1.109826 | 1.106808 | 1.0027 | published |

**2019 is the object.** SPP's own published rate is **1.591 %** against the **9.650 %** applied — a
factor of **6.1**, worth **6.98 TWh** of phantom wind potential, which is **85 % of that year's
entire +8.23 TWh wind excess**. 2020 and 2021 are **not published** (verified by grep over all three
ASOM transcriptions: only the 2019 and 2022 endpoints of the span are printed), so they keep the
reference-rate path untouched.

**This is a rule 14 `[R-ACCURATE]` repair and nothing else.** The accurate datum exists, is
committed, and is being passed over for an estimate. Rule 14's misalignment exception cannot apply:
the published rate is SPP's own footprint on SPP's own annual basis, which is exactly the boundary
the gross-up applies to.

## 4. WHY IT IS NOT A FITTED LEVER — and the arm that WOULD have been

A single widened cross-year mean over all five published years (0.0797962 → ×1.086711) was
available. It moves **every** year in the helpful direction, by more in total (≈ −13 TWh against
this mechanism's −7.2). **It is refused**, because one constant is less accurate than each year's
own published measurement in every year, and because it is the arm that looks better (rule 1
`[R-STRUCT]`).

The arm that is taken moves **two of the keeper's three years adversely**. That asymmetry is the
evidence, and it is the same argument capx D67 was armed on.

Rule 19 `[R-ONE-MECH]`: one seam, `data.renewables._curtailment_rate_for_year`, read by **both**
uncurtailed constructions — it cannot half-apply, and it **replaces** the rate rather than stacking
on it. It is orthogonal to its two neighbours: the gross-up row sets the FORM,
`vre_curtailment_oversupply_allocation` sets WHERE the energy lands, this sets HOW MUCH there is.

Rule 21 `[R-DOF]`: **zero new free parameters.** No constant introduced, no window chosen; the rate
is the ratio of two published measurements.

Rule 13 `[R-MEASURED]`: **forward-native.** A forecast year has no published rate, so the provider
returns `None` and the reference-rate path — unchanged, and still *the* forecast methodology —
serves it. The reader can only fire in a year the ISO has already published, on the same footing as
an F923 delivered fuel price or a CAMPD outage window. It is also strictly **closer** to the
construction `_forecast_uncurtailed_cf` names as its own reference (the CAISO HSL parquet, built
from the year's OWN measured curtailment) than the cross-year mean it replaces.

**The rule-13 objection, stated rather than hidden.** A curtailment rate is closer to a dispatch
*outcome* than a fuel price is, and `_forecast_uncurtailed_cf`'s docstring deliberately uses a
different source year *"so the potential is never scaled to land delivered output on the target
year's actuals"*. Three things answer it and the owner can weigh them: (a) the quantity being
injected is `delivered + curtailed`, which is the **measured available energy** — a physical fact
about the wind fleet, and in SPP a congestion fact the 2-zone reduction cannot represent; (b) it
cannot pin the output — 2019's model wind would still sit **+1.25 TWh above** the actual, not on it;
(c) the repo's own gold-standard path (CAISO HSL) already uses the year's own measured curtailment.

Rule 23 `[R-FROZEN-DERIVE]`: **nothing is re-derived.** The reference constant
`0.09650131886270663` and the committed 2023–2025 rows are **unchanged and test-pinned**
(`tests/unit/data/test_spp67_year_own_curtailment_rate.py`). The 2019–2022 delivered rows added
alongside are a **coverage** extension — no committed value changes and no source file changed;
those years were simply never paired. The trigger is the **rule removal of 2026-09-09**, which is
neither a residual moving nor a data update; it is named as a third category rather than dressed as
one of the two.

Rule 25 `[R-ISO-SCOPE]`: **no per-ISO number is transferred.** `_YEAR_OWN_RATE_PROVIDERS` carries
`("SPP","wind")` and nothing else, so an armed run leaves every other ISO-fuel on the reference-rate
path — proven by test, and by the census in §6. **MISO's `_MISO_REFERENCE_RATE_YEARS` carries the
identical residue** (*"The 2023-2025 restriction keeps it clear of every holdout year (#22)"*); that
is **reported, not acted on** — MISO's lane's call (rule 28(d)).

## 5. PRE-REGISTERED PREDICTIONS — written before any solve

SPP-66 scored 3 of 7 of its own predictions wrong on sign and said so. Same discipline here.

**P1 — Δ model wind TWh.** Midpoint of a two-sided bracket (the LP holds the same re-curtailment
MWh / the same *fraction* of the headroom); band ±20 % on each non-zero entry.

| 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **−6.98** | **0.0000** | **0.0000** | **−0.37** | **−1.39** | **+1.20** | **+0.33** |

**P2 — 2020 and 2021 are a HARD STOP and this lane's own free control.** Neither year has a
published rate, so the reader falls through and both must reproduce the rung's committed numbers
**exactly** — every class TWh at ±0.0000 and the price series identical. Any movement means the
gate leaked, and the shard stops without pushing. Because those two years are solved at **my** pin
against a control solved at `f80de3e1`, they also **validate the §6 G-DRIFT audit at zero extra
cost**: if drift were live, they would move.

**P3 — Δ model load-weighted price: opposite sign to Δwind in every year.** UP in 2019 / 2022 /
2023, DOWN in 2024 / 2025, exactly 0.0000 in 2020 / 2021. Magnitude 2019 **+1.0 to +6.0 $/MWh** on a
$22.11 base; every other year **|Δ| < 1.5 $/MWh**. Stated as the *model's own* price change, not as
a C3a error: this lane could not reproduce the scorer's C3a from committed artifacts (my own
load-weighted reconstruction against the committed RT sidecar reads −2.48 / −2.21 / −0.62 % for
2023–2025 where keeper 13's note reads +2.43 / +3.54 / +5.17 %), so C3a is left to the shard's
scorer and no C3a number is asserted here.

**P4 — Δ thermal by class, 2019, where the energy goes.** The −6.98 TWh must be served, spread over
all 8,760 hours in proportion to wind output. COAL_PRB **+2.0 to +4.0**, CC_REGULAR **+1.5 to
+3.5**, CT_PEAKER **+0.2 to +1.0**, COAL_LIGNITE **+0.1 to +0.8**, ST_GAS **+0.0 to +0.5**; hydro
and nuclear ≈ 0 (energy-limited / must-run); thermal sum **+6.98 ± 0.3** by energy conservation.
**This is the prediction most likely to be wrong** — SPP-66's split predictions were its worst — and
the split, not the total, is what I expect to miss.

**P5 — gate status.** NO C1/C3a/C3b status flip in any keeper year (every move is ≤1.4 TWh on a
~110 TWh class). The rung's 2019 C1 improves materially; the rung **stays NOT-YET**, because
2020/2021 are unmoved by construction and 2022 moves by 0.37 TWh.

**P6 — what would make me call it a failure.** 2020 or 2021 moving at all; 2019's wind not falling
by at least 5.5 TWh; or the displaced energy landing in slack/dump rather than thermal.

## 6. G-DRIFT — rule 29(b) form 4 is VALID, so no control is solved

Keeper 13 solved at `f80de3e1`. SPP-66 already audited `f80de3e1 → 17a8a14c` by measurement (128
changed files, all INERT, every LP input array identical). This lane audits only the increment
`17a8a14c → HEAD`: **9 changed files on the solve path**, classified —

| file | verdict | reason |
|---|---|---|
| `reference/nyiso_offer_surface_positional.json` | INERT | per-ISO artifact SPP does not have |
| `config/constants.py` (+14) | INERT | **purely additive** (zero removed lines); an NWPP VRE region table |
| `config/fuel_trajectories.py` (+62) | INERT | read only under `gas_basis_differential_measured_by_year`, default-off and absent from both recipes |
| `config/scenarios.py` (+96) | INERT | two new default-off fields, both declared at their default |
| `config/solve_surface_declared.py` (+1) | INERT | one entry, `{"SOCO": …}` — SOCO-scoped |
| `data/fuel/basis/miso.py` | INERT | MISO's branch plus a default-off kwarg |
| `data/fuel/hubs.py` (+79) | INERT | gated by the same default-off flag; callers pass `prior_year_dated=None` |
| `data/fuel/trajectories.py` (+17) | INERT | same gate |
| `pipeline/backcast_config.py` (+49) | INERT | the one non-comment change is `coal_takeorpay_from_data=(iso.upper() in ("MISO","NWPP"))` — **SPP is neither**, so it resolves `False` exactly as before |

**All INERT ⇒ form 4 valid, keeper 13's committed bundle is the control, no control solve is spent.**

Reported rather than smoothed: SPP's `solve_surface` fingerprint **does** move,
`7ab7e3b0c4741dc3 → 12114955918da369`, because the row count goes **182 → 184**. The load-bearing
field is `moved: {}` — **zero existing SPP surface values changed**; the two added rows are new
names neither recipe consults. P2 turns this from an argument into a measurement.

## 7. FOOTPRINT — proven before the solve, not after

- **Cache keys: 0 of 46 committed run configs move** when the field is present at its default,
  across 9 ISOs (ERCOT 9, SPP 9, NEISO 8, MISO 7, NWPP 5, PJM 3, NYISO 2, SOCO 2, CAISO 1). The
  armed key **is** distinct (`989da50bbf0f99d8 → a53470db758313d2`).
- **Registered in the same commit** as the field, in both `_CACHE_KEY_OPTIONAL_FIELDS` and
  `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` (rule 28).
- **Matrix**: base row `vre_reference_rate_year_own` plus a cell in **all nine** ISO shards
  (rule 28(c)). SPP `U` until an arm lands; MISO `U` with the shared-defect note; ERCOT/CAISO `U`
  and inert; NEISO/NYISO/PJM `.`; NWPP/SOCO `U` and inert.
- **Tests**: 62 in `tests/unit/data/test_spp67_year_own_curtailment_rate.py`, pinning the reference
  constant to `0.09650131886270663`, the seam's identity to `_reference_curtailment_rate` when off,
  the registry's SPP-wind-only membership, and the 2020/2021 fall-through.
- `check_cache_key_registration.py` fails with **the identical 2-name failure set on clean
  `origin/main`** (`PPA_COST_RECOVERY_YR`, `REGIONAL_RENEWABLE_CF`) — pre-existing, another lane's,
  untouched here.

## 8. THE ARM, and the shard recipe

Keeper years (2023/2024/2025) replay `spp51_syncfloor_span`; rung years (2019–2022) replay
`spp51_syncfloor_rung`. **Trap (n): the two differ on `mid_vintage_exit_carry`** (`False` / `True`)
and each shard hard-stops on its own expected value. One year per shard (rule 36), full bundle
pushed including `dispatch/<year>_P1.parquet` (rule 34(a)).

```
python3 scripts/replay_keeper.py results/calibration/<span|rung> \
  --years <YEAR> --set vre_reference_rate_year_own=true \
  --out-dir results/calibration/spp67_yearown_<YEAR>
```

## 9. RETENTION (rule 31 `[R-RETAIN]`)

Nothing is deleted. Every shard pushes its full bundle to its own branch; the parent composes and
states retrievability in the RESULT. The promotion question is asked explicitly before the session
ends.
