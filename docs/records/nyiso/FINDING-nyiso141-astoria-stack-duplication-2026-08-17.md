# FINDING nyiso-141 — the downstate ST_GAS under-production has a **measurement** component: Astoria's CEMS reports one generator's output **twice**, and in 2025 that doubled number *is* the benchmark

**Session nyiso-141, 2026-08-17.** Takes up job (A) of the nyiso-141 prompt — the
successor named by `FINDING-nyiso140-li-st-floor-membership-2026-08-16.md` §7,
the downstate ST_GAS under-production that nyiso-140's removal of 1.87 TWh of
manufactured Port Jefferson energy exposed.

**Identification only — no solve was spent, no mechanism was written, no
`ScenarioConfig` field was added.** Measured entirely from source data: the EPA
CAMPD unit-level extracts, EIA-923 Page 1, and the committed benchmark
sidecars. No price or volume residual was used to *find* the object; the
residual is used only in §6 to state, honestly, how much of it this accounts
for and how much it does not.

Reproducible: `.venv/bin/python scripts/probes/_nyiso141_astoria_stack_duplication.py`.

---

## 1. THE QUESTION AS INHERITED

nyiso-140 left ST_GAS at **−0.916 TWh (2024)** and **−3.737 TWh (2025)** against
actuals, and named the root cause as the successor. The prompt's candidate list
was: Barrett/Northport loading, a missing unit, heat rates, downstate gas basis,
or the LI import bound.

The first measurement rules most of that list out. Decomposing the **actual**
ST_GAS rise by plant (bench `c_ann`, 2023 → 2025):

| plant | zone | MW | 2023 | 2024 | 2025 | Δ25−23 |
|---|---|---:|---:|---:|---:|---:|
| Northport | Long_Island | 1564 | 2.558 | 3.915 | 4.307 | **+1.748** |
| Astoria Generating Station | NYC | 1345 | 1.546 | 1.850 | 2.672 | **+1.126** |
| Bowline Point | Capital_Hudson | 1242 | 0.976 | 1.353 | 2.061 | **+1.085** |
| Arthur Kill | NYC | 878 | 1.119 | 1.353 | 2.160 | **+1.041** |
| Roseton | Capital_Hudson | 1242 | 0.209 | 0.256 | 0.725 | +0.516 |
| Ravenswood ST | NYC | 1828 | 0.857 | 0.682 | 1.070 | +0.214 |
| E F Barrett | Long_Island | 376 | 1.386 | 1.137 | 1.035 | −0.351 |
| Port Jefferson | Long_Island | 376 | 0.325 | 0.288 | 0.309 | −0.016 |

The rise is **broad-based across six large steam plants in three zones**, not a
missing unit and not a Long Island story — so it is not the LI import bound and
not Barrett/Northport loading. **Fuel switching is refuted directly:** implied
CO₂ per MMBtu stays at ~53.9–54.1 (pure pipeline gas) at Arthur Kill, Astoria
and Bowline across all three years; only Roseton (57.3) and, mildly, Northport
(55.7) show any oil. The plants that doubled did it on gas.

And the model does not reproduce the *trend* at all:

| Δ 2023→2025 | actual | model (keeper) |
|---|---:|---:|
| ST_GAS | **+7.299** | **+1.299** |
| CC_REGULAR | +0.119 | +4.852 |
| CC_CHP | +1.352 | +4.115 |
| hydro | −3.927 | −7.335 |

Reality replaced a falling hydro year with **steam**; the model replaced it with
**combined cycle**. That is the shape of the object — and part of it turns out
not to be a dispatch fact at all.

## 2. THE OBJECT — Astoria files one generator's output on two rows

Astoria Generating Station (ORIS **8906**, NYC, ST_GAS, the #2 riser above)
reports six CEMS "units". Four of them are two **reheat/superheat pairs**:

| unit | 2025 MWh | max MW | HR **counted alone** |
|---|---:|---:|---:|
| 20 | 45,674 | 140 | 13,292 |
| **31RH** | 606,233 | 382 | **5,512** |
| **32SH** | 606,110 | 382 | **5,253** |
| **51RH** | 707,025 | 387 | **5,264** |
| **52SH** | 707,025 | 387 | **5,172** |
| CT0001 | 90 | 15 | 6,534 |

`31RH`/`32SH` and `51RH`/`52SH` are **one generating unit each, monitored on two
flue paths**. CAMPD repeats the generator's **full `grossLoad` on both rows**
while **splitting `heatInput` and the emission masses** between them. Summing
the facility's units therefore double-counts generation while heat and mass sum
correctly — halving every intensity derived from the pair.

### Three independent channels, none of them a residual

**1 — INTERNAL (the extract contradicts itself).** In 2025, `51RH` and `52SH`
`grossLoad` are identical in **100.00 %** of their 4,327 fired hours, maximum
absolute difference **exactly 0.000**, correlation **1.000000**; `31RH`/`32SH`
in 99.98 %. Heat input, by contrast, splits ~50/50 (sum ratios 1.018 and 1.050).

This is **not** what genuine twin units dispatched in lockstep look like, and
the fleet contains the control group to prove it: the Gowanus, Narrows,
Holtsville and E F Barrett peaker banks all reach 95–100 % identical hours, yet
**each of those rows carries its own full heat input** at a plausible standalone
rate (10,779–17,760 Btu/kWh). Identity of output alone is not the signature —
identity of output *with split heat* is.

**2 — PHYSICAL (the implied heat rate is impossible).** Counted separately each
Astoria row implies **5,172–5,512 Btu/kWh** — better than a modern combined
cycle, and flatly impossible for a dry-bottom wall-fired or tangentially-fired
**boiler**. Counted once against the pair's summed heat input it is
**10,436–10,764**, exactly where its NYISO gas-steam peers sit (Arthur Kill
10,033, Northport 9,983, Bowline 9,665, Port Jefferson 10,432).

**3 — EXTERNAL (EIA-923 says one half).** Net generation over CAMPD gross:

| plant | 2023 | 2024 |
|---|---:|---:|
| Arthur Kill | 0.933 | 0.938 |
| E F Barrett | 0.936 | 0.944 |
| Northport | 0.934 | 0.945 |
| Bowline | 0.959 | 0.946 |
| Roseton | 0.923 | 0.924 |
| Danskammer | 0.956 | 0.961 |
| Port Jefferson | 0.888 | 0.882 |
| **Astoria (raw)** | **0.472** | **0.471** |
| **Astoria (duplicate dropped)** | **0.935** | **0.937** |

Every genuine gas-steam plant reconciles at 0.88–0.96. Astoria alone lands at
~0.47 — one half — and dropping the duplicate `grossLoad` puts it **inside the
peer band**. Two entirely independent measurement systems (EPA CEMS and EIA-923
Page 1) agree on the factor of two.

**A guard already caught this and papered over it.** 0.472 is outside
`campd._PARASITIC_MIN`..`_PARASITIC_MAX` (0.80–1.00), so
`compute_parasitic_factors` flagged the plant as implausible and substituted the
ST_GAS **class default** — detecting the anomaly and then discarding the
evidence. (This is moot for NYISO in practice: `parasitic_load_factors.parquet`
carries ERCOT plants only, so NY falls back to 1.0 / gross==net.)

## 3. BLAST RADIUS

**(a) The class benchmark, in any year EIA-923 has not yet published the plant.**
`run_calibration_full._backfill_eia923_with_campd` replaces EIA-923 with CAMPD
net for a model plant EIA-923 reports below 50 GWh while CAMPD is above it. The
committed bench sidecars show it firing on exactly one of the three years:

| year | Astoria `e_ann` (benchmark) | `c_ann` (CAMPD) | backfilled? |
|---|---:|---:|---|
| 2023 | 0.7298 | 1.5463 | no — EIA-923 present |
| 2024 | 0.8709 | 1.8500 | no — EIA-923 present |
| **2025** | **2.6722** | **2.6722** | **YES — identical, EIA-923 absent** |

So in **2023 and 2024 the ST_GAS benchmark is correct** (it used the metered
EIA-923 value all along, and the duplication never reached it), and in **2025 it
carries the doubled number**: **2.672 TWh where the corrected CEMS series gives
1.359**. The 2025 ST_GAS actual of 16.003 TWh is overstated by ≈ **1.31 TWh**.

**(b) The unit-level CEMS emission rates that feed dispatch.**
`plant_emission_rates_v2.parquet` is keyed per unit, so each half of a pair
carries *half the mass over the full MWh*:

| | co2_kg_per_mwh_net |
|---|---:|
| Astoria 31RH / 32SH / 51RH / 52SH (2025) | 300 / 286 / 284 / 279 |
| genuine NY gas-steam peers (2024) | **520 – 575** |

A fired gas boiler cannot emit 280 kg CO₂/MWh — that is better than a modern
combined cycle. Under RGGI this understates Astoria's marginal cost by roughly
**$6/MWh**, i.e. it is priced into the merit order about that much too cheap.

**(c) Anything else derived from plant-level CAMPD gross** — the parasitic
reconciliation above, and the plant-grain series used by the CAMPD binning.

**Not affected**, checked and cleared: heat rates (sourced from eGRID/EIA-860,
not CAMPD gross); `retiree_availability_caps` (retirees only, and it clips to
1.0); the `nyiso_gas_commitment_bridge` `min_load_frac`s (a p5/p99.5 **ratio**,
so invariant to a uniform scaling of one plant's series).

## 4. THE CORRECTION

Both data seams, keyed on the same identification table
(`campd.CAMPD_STACK_DUPLICATE_UNITS = {8906: {"32SH": "31RH", "52SH": "51RH"}}`):

* **Plant grain** (`campd._normalize_campd`) — drop the duplicate row's
  `grossLoad`; keep its heat and masses, which are genuinely per-path and must
  keep summing.
* **Unit grain** (`curate_emissions_unit_annual._normalize_unit_hourly`) —
  additionally re-label the duplicate onto its primary, so the group-by sums
  the pair into the one generator it physically is.
* **Facility-level extracts** (`load_campd_hourly`) — NY's preferred extract is
  `campd-facility-level/`, which has the double-count **already baked in and no
  unit identity to see it with**. The loader's existing split-plant substitution
  is generalised to `_FACILITIES_NEEDING_UNIT_ROWS`, so a stack-duplicate
  facility is likewise rebuilt from its unit-level companion.

**Zero new degrees of freedom** (rule 21 `[R-DOF]`): no parameter, no
coefficient, no threshold. It is a row-identity correction, of exactly the kind
`CAMPD_UNIT_PLANT_REMAP` already carries for CAISO's El Segundo
(`PRECHECK-caiso196-elsegundo-remap-2026-08-15.md`).

Verified at the seam — Astoria plant-level gross becomes 780,293 / 929,474 /
1,359,022 (matching the hand computation exactly), heat unchanged, and the
implied intensities land at 10,678–11,176 Btu/kWh and 578–625 kg CO₂/MWh.
Regression tests: `tests/curation/test_campd.py::TestStackDuplicateCorrection`.

### 4.1 The corrected values, so the next session can verify its regeneration

`data/clean/emissions-unit-annual/` was rebuilt with the fix in this session and
gives the target rows exactly. Plant gross falls to the hand-computed values and
the two real generators' CO₂ intensity roughly doubles into the peer band:

| year | plant gross, old → new | `co2_kg_per_mwh_net`, old → new |
|---|---|---|
| 2023 | 1,546,300 → **780,293** | 31RH 308.4 → **603.8** · 51RH 319.5 → **641.2** |
| 2024 | 1,849,996 → **929,474** | 31RH 302.7 → **591.4** · 51RH 292.5 → **591.8** |
| 2025 | 2,672,157 → **1,359,022** | 31RH 299.6 → **585.4** · 51RH 284.0 → **563.0** |

`32SH`/`52SH` disappear (merged onto their primaries), and **units `20` and
`CT0001` are byte-identical before and after** — the scope check that the
correction touches only the pair.

### 4.2 HAZARD — `plant_emission_rates_v2.parquet` must NOT be regenerated on the default path

Deliberately **not** regenerated in this session, and the next session must not
regenerate it naively either. The committed artifact carries **2018–2026**
including 2022 and 2026, and those quarantined-year rows exist only via
`--holdout-intake`, whose own guard says it "may only run once (rule 22)". The
default path is a **replace**, not a merge (`out = derive(args.years, isos)`), so
`derive_plant_emissions_v2.py --iso … --years …` would silently drop:

* every **2018** row — 2018 is no longer built by `regenerate_clean` (CLAUDE.md
  rule 22: 2018 and earlier are DROPPED), so it cannot be rebuilt; and
* the **2022 / 2026** holdout-intake rows, which are **unrepeatable by
  construction**.

The A/B therefore needs either a surgical update of the eight `(8906, unit,
year)` rows against the targets in §4.1, or an owner decision on the
regeneration path. This is a **pre-existing artifact-lifecycle hazard** that this
session merely surfaced — it is not created by the correction, and it applies to
any future change touching that artifact.

## 5. WHY THE GOVERNANCE DIAGNOSTICS DID NOT CATCH IT

Nothing in the gate set inspects the benchmark's own construction. C1–C3 score
the model *against* the actuals; an error *in* the actuals is invisible to them
by construction, and moves the target rather than the score. The one check that
did see something — the parasitic band — reported "implausible" and then
substituted a class default, which is a fallback designed for a *missing*
measurement, not a *wrong* one. A silent fallback on a tripped plausibility
guard is the failure mode worth generalising from here.

## 6. WHAT THIS DOES AND DOES NOT EXPLAIN — stated against my own result

Astoria's benchmark entry falls 2.672 → 1.359 TWh in 2025 only. Carrying that
through at face value:

| year | ST_GAS actual (as scored) | corrected | model (keeper) | err as scored | err corrected |
|---|---:|---:|---:|---:|---:|
| 2023 | 8.704 | 8.704 | 10.967 | **+2.263** | **+2.263** |
| 2024 | 11.071 | 11.071 | 10.155 | **−0.916** | **−0.916** |
| 2025 | 16.003 | ≈ **14.69** | 12.266 | **−3.737** | ≈ **−2.42** |

**This accounts for roughly 35 % of the 2025 under-production and none of 2023
or 2024.** The remaining ≈ −2.4 TWh in 2025, the +2.26 over-production in 2023,
and the CC-for-steam substitution documented in §1 are **all still open** and
are still the successor object. This finding removes a measurement artifact
from the target; it does not close the residual, and it must not be quoted as
having done so.

Two honest caveats on the number itself:

1. The exact `classFull` delta is produced when the benchmark is rebuilt at
   solve time — the per-plant sum of `e_ann` does not equal `classFull` (8.340
   vs 8.704 in 2023) because mixed plants are class-split downstream. The
   ≈1.31 TWh is Astoria's own entry moving; treat the classFull figure as
   approximate until a rebuild lands.
2. With NY carrying no parasitic factors, the backfill will now put Astoria's
   corrected **gross** (1.359) on the books as net, still ~7 % high against its
   measured 0.935 factor. That is a **pre-existing, fleet-wide NY gap** in the
   backfill's net basis, not something this correction introduces — logged as
   an open item, not fixed here (it would be a second, independent change).

## 7. THE DIRECTION OF THE FIT IS NOT THE POINT

Rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`: the correction is justified by
the measurement's own internal contradiction and by an independent metered
source, not by what it does to a residual — and it is adopted whatever it does
to one. It happens to *reduce* summed |error| here (6.92 → ≈5.60 TWh), but that
is a consequence and not the argument; had it gone the other way the correction
would stand unchanged, exactly as nyiso-140's did.

The one place the direction genuinely matters is a governance point worth
stating plainly: because 2025's benchmark falls, **every NYISO run ever scored
on 2025 was scored against an inflated ST_GAS target**, keeper included. Re-runs
are not comparable to the committed 2025 numbers across this change.

## 8. WHAT IS UNCHANGED

Keeper `2026-08-16-nyiso-140-layup-exclusion` is untouched and remains the
designated NYISO keeper. NYISO holds `complete` (validation only), is absent
from `final`, its frontier stays CLEARED, and the **holdout spend freeze is
ACTIVE and untouched** — this session solved nothing and scored nothing, and
touched no year outside 2023–2025. The nyiso-140 membership exclusion, the
nyiso-139 RT interval convention, and the deferred Zone-K joint lever are all
left exactly as they were.

**The A/B is pre-registered but NOT executed** — see
`PREREG-nyiso141-astoria-stack-duplication-2026-08-17.md`, written before any
solve so its ex-ante predictions cannot be fitted after the fact. It was not run
here because the session could not complete a control + arm pair (6 year-solves
at `plant_level_fleet=True`) on 4 cores with the clean-tree rebuild holding most
of 15 GB, and starting a pair it could not finish would have left a half-registered
bundle — which rule 15 forbids more firmly than it requires the solve. Nothing
is registered on the dashboard by this session, and nothing needed to be: no run
was produced. What the next session inherits is the correction, the target values
(§4.1), the regeneration hazard (§4.2) and the pre-registration.

Scope note (rule 25 `[R-ISO-SCOPE]`): the duplicate-reporting **pattern** is a
CEMS filing convention and is not inherently NYISO-specific, but this session
scanned **NY only** and the correction table carries **one facility**. Whether
any other ISO's fleet contains a common-generator stack pair is that lane's
measurement and is deliberately not adjudicated here.
