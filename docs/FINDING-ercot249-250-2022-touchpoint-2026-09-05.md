# FINDING — ERCOT 2022 validation touchpoint, both keeper configs (ercot-249 / ercot-250)

> Status: RECORD of a rule-22 `[R-HOLDOUT]` **validation-tier touchpoint**, 2026-09-05, branch
> `claude/ercot-2022-validation-touchpoint-b9z5oz`. ERCOT holds a `complete` marker (declared
> 2026-08-31), which authorizes the validation ladder (2020–2022) to be solved, scored and
> registered. **The locked test (2019 / H1-2026) was not touched** and stays frozen for every ISO
> under the tier-scoped holdout freeze.
>
> **NEITHER ARM IS A KEEPER OR A KEEPER CANDIDATE.** No parameter was changed, no `ScenarioConfig`
> field minted, no mechanism tested, no mechanism-matrix cell touched. Because the validation tier
> is iterated against, these numbers are **model-SELECTION evidence** and are **never** quotable as
> certified out-of-sample skill numbers — only 2019, spent once at the end, is that.
>
> Keeper at measurement: `2026-09-05-ercot248-two-config-keeper` (unchanged by this session).

## 0. What was run

Both halves of the two-config keeper, replayed VERBATIM on 2022 via `--replay-bundle`
(which takes every flag from the source bundle's `meta.json`) with `--holdout-authorized`:

| arm | run id | source bundle | config |
|---|---|---|---|
| **ercot-249 FORWARD** | `2026-09-05-run249-2022-touchpoint-forward` | `ercot234_eastex_identity` | the 2024–2025 configuration — zero fitted scalars, repaired EASTEX crosswalk |
| **ercot-250 CARVE-OUT** | `2026-09-05-run250-2022-touchpoint-carveout` | `ercot236_k33_clip` | the 2023 ECRS-era configuration — `ercot_offer_swcap_clip` + k_peak 33 |

Solved in-session, never on CI (CLAUDE.md GitHub Actions rule). Rule 12 `[R-PARALLEL]`: the two
invocations were run **sequentially, not concurrently** — see §5, the environment note.

## 1. Result — in-sample vs 2022, criterion by criterion

Keeper in-sample determination on its designated span (2023–2025): **CALIBRATED**.
Both arms on 2022: **NOT-YET**, on the *same three* criteria.

| criterion | tier | keeper in-sample | **249 FORWARD 2022** | **250 CARVE-OUT 2022** | verdict |
|---|---|---|---|---|---|
| C1 fuel-mix | load-bearing | PASS | **FAIL** CC_REGULAR −10.59 TWh (121.49 vs 132.09), share −2.4pp | **FAIL** CC_REGULAR −10.39 TWh (121.69 vs 132.09), share −2.4pp | **degraded** |
| C2 system volume | load-bearing | PASS | PASS (gas 166.17 / coal 75.53) | PASS (gas 166.47 / coal 75.54) | held |
| C3a mean LMP | load-bearing | PASS | **PASS −1.5 %** ($61.38 vs $62.30) | **PASS +0.0 %** ($62.30 vs $62.30) | held |
| C3b price shape | load-bearing | PASS | **FAIL** NRMSE 0.250 (≤0.20) | **FAIL** NRMSE 0.220 (≤0.20) | **degraded** |
| C3c price tail | supporting | CAVEAT (ledgered) | **FAIL** 38 h vs 196 h (**0.19×**) | **FAIL** 64 h vs 196 h (**0.33×**) | **carried** |
| C4 dispatch corr | supporting | PASS | PASS gas r=0.991 / coal r=0.785 | PASS gas r=0.991 / coal r=0.785 | held |
| C6 governance | protective | PASS | PASS | PASS | held |
| C8 forced share | protective | PASS | PASS (CC 3.6 %, COAL 1.8 %, ST_GAS 27.2 %) | PASS (CC 3.5 %, COAL 1.8 %, ST_GAS 27.0 %) | held |
| C5a CO2 *(reported-only)* | — | — | +0.2 % | +0.1 % | — |

Grade summary both arms: `scored 8, target_grade 5, commercial_grade 0, ledgered 0, fails 3`.
C3c does **not** reclassify under the C3c standing rule: guard (a) requires it to be the **lone**
failure, and C1 and C3b also fail. The rule working as designed, not a defect.

### 1.1 The three results that matter

1. **C3a is the headline, and it is a good one.** The forward config lands 2022 mean LMP at
   **−1.5 %**, and the carve-out at **+0.0 %** — against the same config's **−39.7 %** on 2023.
   The keeper's registered 3-year NOT-YET rests on C3a-2023 and C3b-2023, both 2023-only. 2022
   independently corroborates that reading: **the C3a failure is a 2023-regime phenomenon, not a
   defect in the forward configuration.** This is the strongest evidence the two-config partition
   has received from outside its training window.
2. **C1 is the new failure and it is an INPUT gap, not a model defect** (§2).
3. **C3c is a known limitation travelling**, but 2022 sharpens *which* half is broken (§3).

## 2. Diagnosed object #1 — the absent ERCOT HSL 2022 archive owns the C1 miss

**Standing gap 1, case B applied**: no `data/raw/ercot-hsl/np6/2022/` archives were present, so
`build_ercot_hsl.py --year 2022` was not run. Both solves logged, verbatim:

```
WARNING: ercot_gtc_limits_measured: 2022 has no measured HSL potential
         (renewables ride delivered-as-CF) — measured GTC limits skipped for this year
WARNING: ercot_wtx_curtailment_driver: 2022 has no measured HSL potential
         (renewables ride delivered-as-CF) — curtailment ceiling skipped
```

So 2022 renewables ride `RENEWABLE_BOUND_FORECAST_UNCURTAILED` **and** lose both curtailment
ceilings. The measured consequence (forward arm):

| fuel | model TWh | actual TWh | Δ | r | NRMSE |
|---|---|---|---|---|---|
| wind | 112.23 | 107.38 | **+4.85** | 0.999 | 0.052 |
| solar | 25.24 | 23.67 | **+1.57** | 1.000 | 0.111 |
| **renewable total** | | | **+6.42** | | |
| CC_REGULAR | 121.49 | 132.09 | **−10.59** | | |

The energy balance closes on it: gas family **−10.09**, coal **+4.31**, renewables **+6.42**,
nuclear **−0.78** ⇒ ≈ 0. **The +6.4 TWh of unbounded zero-MC renewable energy displaces gas CC
almost exactly.** Correlations of 0.999 / 1.000 say the renewable *shape* is right and only the
*level* is unbounded — the signature of a missing curtailment haircut, not a profile error.

**Why this cannot appear in-sample.** In 2023–2025 the L1 delivered-CF bound pins wind and solar
to measured delivered output. `legitimacy_diagnostics` D-10 records the difference explicitly:

```
2022 | wind  | forecast_uncurtailed | pinned False | free
2022 | solar | forecast_uncurtailed | pinned False | free
_ERCOT: 0/2 wind/solar rows ride the L1 delivered-outcome bound_
```

In one respect this makes 2022 a **harder and more honest test** than any training year — the
renewable rows are free rather than pinned, so C1 scores model skill there rather than plumbing.
The cost is that the C1 CC_REGULAR failure is not attributable to the dispatch model at all.

**The object is an owner-side data upload**, not a parameter: drop the NP4-732-CD / NP4-737-CD
(or NP4-742/745) 2022 archives into `data/raw/ercot-hsl/np6/2022/`, run
`python scripts/data/build_ercot_hsl.py --year 2022`, and re-run this touchpoint. Until then the
2022 C1/C2 rows should be read as **not discriminating**.

## 3. Diagnosed object #2 — C3c is a price-function failure, not a selection failure

The committed `hourly/reserve_family_2022.parquet` sidecar (forward arm) is decisive:

| family | requirement mean MW | held mean MW | shortfall hours | max shortfall MW | dual p99 | dual max |
|---|---|---|---|---|---|---|
| `ercot_ordc_total` | 10,700 | 10,665 | **200** | 5,217 | **$0.15** | $374.40 |
| NonSpin | 3,898 | 4,596 | 8 | 2,483 | $0.00 | $2,500 |
| RRS_withheld | 2,863 | 3,479 | 0 | 0 | $0.00 | $2,500 |
| RegUp_withheld | 359 | 1,428 | 0 | 0 | $0.00 | $2,500 |
| ECRS | **0** | 1,162 | 0 | 0 | $0.00 | $0.00 |

**The model goes ORDC-short in 200 hours against an actual tail of 196 hours.** The *selection*
of scarce hours is essentially exact. But the dual on those hours is ~zero (p99 **$0.15**), so
only 38 hours clear $200. **The open object is the ORDC price function at shortfall, not the
shortfall detector.**

This reproduces, on 2022 itself, the M-3 result of
`docs/RESEARCH-ercot221prep-2022-regime-point-2026-08-19.md` §3 ("the *selection* instrument …
already exists inside the model … the open object is purely the **price function** on the
selected hours"), and it is exactly what that doc's §1 regime table predicts 2022 would test:

| | 2022 tail (196 h) | 2023 tail (181 h) |
|---|---|---|
| PRC at tail, p50 | **3,768 MW** | 5,794 MW |
| RTORPA at tail, p50 / p90 | **$34 / $493** | $0.72 / $55 |
| adder share of price, p50 | **15.3 %** | 0.5 % |

2022's scarcity is *administratively priced at real tightness* — the ORDC genuinely firing. The
model is short in the right hours and prices them at nothing. That the carve-out's pure offer-side
lever (`ercot_offer_swcap_clip` + k_peak 33) lifts the tail from **0.19× to 0.33×** without moving
C1 confirms the residual is on the **price** side of these hours, not the quantity side.

One further 2022-specific input note: `ERCOT adaptive-expectation offer (2022): pass-1 model spike
days 1, P_hat max 0.073` — the storage adaptive-expectation mechanism, identified on the post-Uri
2023 conduct regime, is very nearly inert in 2022 (one model spike day). It is not a candidate
owner of the 2022 tail.

## 4. Standing gap 2 — one gate is out of step with the data on disk

Exactly one of the four `*_from_year` gates is stale relative to what is actually present:

| gate | recipe value | 2022 measured series | assessment |
|---|---|---|---|
| `ercot_reserve_supply_cap` | `True`, `from_year 2023` | **`data/raw/ercot/ercot_2022_ordc_reserves_hourly.parquet` EXISTS** (also 2020, 2021) | **STALE GATE.** The from_year was set because the series was believed to begin in 2023; it begins in 2020. The RTOLCAP cap limits how much reserve may be held, i.e. it *deepens* the shortfall that prices the ORDC — the precise quantity §3 finds silent. |
| `ercot_load_resource_reserve` | `True`, `from_year 2023` | `ercot_2022_as_up_mw.parquet` **absent** (2023–25 only) | gate is data-honest; buildable from back-year 60-Day DAM AS awards |
| `ercot_storage_as_deployment` | `True`, `from_year 2023` | `ercot_2022_storage_as_products_hourly.parquet` **absent** | gate is data-honest |
| `ercot_ecrs_requirement` | `False`, `from_year 2023` | n/a | **structurally correct** — ECRS launched June 2023; requirement measured at 0 MW mean, as it must be |

**Raised, not changed** (per the session's standing instruction): arming `ercot_reserve_supply_cap`
in 2022 is an owner recipe decision. It is, however, the one candidate on this board that is both
(a) supported by measured data already committed, and (b) pointed at §3's diagnosed object. Rules
14 `[R-ACCURATE]` and 22 ("what is held out is the *score*, never the *data*") both point the same
way. **No parameter would be tuned by it** — the series is measured input.

## 5. Standing gap 3 and the year-scoped conduct tables (recorded, not extendable)

Measured 2022 behaviour, from the solve logs: fast-start pool **inert** ("year 2022 absent from
the pool artifact — every surface byte-identical"); coal peak-tranche YEAR level **static**
fall-through (table carries 2023 only); coal per-plant YEAR-windowed curves **static**;
cleared-share offer boundary on the **pooled** year table. The RT cleared-share basis **does**
carry a 2022 table (651 rows, classes CC/CT), as does the SCED offer wall. Full-year 2022 SCED
60-day disclosures are **past MIS retention** (`data/raw/ercot/SCED/` starts 2023-03), so these
tables cannot be extended — this is a permanent limitation of any 2022 (or earlier) touchpoint and
should be read as a standing discount on 2022 conduct-side fidelity. Storage AS product parquets
are likewise absent and read zeros (inert, and moot while the from_year gates hold).

## 6. G-DRIFT audit (rule 26 `[R-SCREEN]` (b)) — form 4 valid

Keeper source shas: forward `0207d69` (2026-08-25), carve-out `17ab9e5`. Audit of
`git diff 0207d69 HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib data/raw/_validation-source data/raw/reference`
(95 files). **Every hunk classifies INERT for an ERCOT backcast**, on three independent grounds:

1. **Gate census (decisive for new code).** 47 `ScenarioConfig` fields were **added** since
   `0207d69`. **Zero** appear in the forward keeper's 752-key recorded recipe. The carve-out's
   754-key recipe carries exactly two — `ercot_offer_swcap_clip=True` (its own defining mechanism,
   present at its own later sha) and `unit_outage_fleet_status_scope=False` (explicit default-off).
   All code reachable only through a new gate is therefore inert by construction. Two fields were
   removed (`caiso_bidir_intertie`, `renewable_buildout_pace`); both appear in the recipes at
   CAISO-default / forecast-only values and the replay path filters them.
2. **The codebase's own same-key invalidation ledger** (`results/cache.py`). Four epochs postdate
   2026-08-25 — 08-31 (R-A storage entry), 09-02 (capx D41), 09-03 (capx D44), 09-05 (capx D60) —
   and **every one is forecast-lane**. The 09-05 entry states the class in terms: "every BACKCAST
   … is byte-identical", because `apply_ccs_retrofit` returns at `year < ccs_retrofit_available_year`
   (2028). **No backcast-invalidating epoch exists since the keeper's sha.**
3. **Per-file classification.** The changed shared modules are dominated by other-ISO branches
   (`offer_curves.py` gated on `miso_intermediate_gas_offer_margin` AND `iso=="MISO"`;
   `zone_assignment.py` / `interchange/caiso.py` / `ps_water_state` / `ra_import_allocations` /
   `gas_ofo_events` CAISO; `campd.py` / `loss_surface.py` NYISO), forecast-only
   `capacity_evolution/` + `capacity_market.py`, and pure timing/diagnostics accounting
   (`pipeline/solve.py`'s PERF-B markup attribution, `pipeline/timing.py`). The new
   `data/outages.py` path variants are selected by `campd_per_unit_attribution` /
   `campd_outage_merit_order_guard`, both new, both default-`False`, both absent from both recipes,
   so both resolve to the incumbent artifact. `ST_GAS_*_MEASURED_HR_MULT_BY_ISO` carries CAISO
   entries only. `ERCOT_SCED_INTERVALS_PER_HOUR` and `ERCOT_DC_TIE_CAPABILITY_MW` were **deleted**
   at `677b605a` with **zero** remaining references in `src/`, `scripts/` or `tests/` — dead-code
   removal, rule 26 `[R-DELETE]` housekeeping.

**Solve provenance.** Both arms were solved at `49647dd6` (recorded in each bundle's
`meta.json` as `git_sha`); the branch was fast-forwarded to `9b62c6de` afterwards, for
publication only — no artifact was re-solved across the move, and
`scripts/calibration_verdict.py` is stdlib-only over committed artifacts, so both
determinations reproduce byte-for-byte at either sha (re-verified after the fast-forward).

**Conclusion: the incumbent keeper's committed bundle is a valid control (form 4).** No control
solve was spent. *Granularity disclosure:* grounds (1) and (2) are exhaustive and mechanical;
ground (3) is a module-level classification, not a hunk-by-hunk read of all 110k changed lines.
It is offered as corroboration of (1)+(2), which are the load-bearing legs.

### 5.1 / 6.1 Environment note — why the arms ran sequentially

Rule 12 `[R-PARALLEL]` permits two concurrent per-plant invocations; this container cannot host
them. A single ERCOT 2022 plant-level solve peaks at **~12 GB** and the memcg ceiling is
**~14 GB** (three runs were OOM-killed at an identical 13.95 GB anon-RSS, each in the same place:
the adaptive-expectation **pass-2** P1 cold rebuild, which is the scored pass). The arms were
therefore run one after the other, and 8 GB of swap was added as headroom.

**The scored runs use the stock solve path with no deviation.** `MARKET_SIM_HIGHS_THREADS=2` and
`=1` were tried first and are *not* the lever — both died at the same ceiling — so the completing
runs were launched at the shipped default thread count with no `MARKET_SIM_*` override.
`MARKET_SIM_P1_FLOOR_INPLACE` was deliberately **not** used despite the log reporting it "would
have been ACCEPTED" for pass 2: warm-solving from the retained P0 basis can land on a different
degenerate vertex and move the duals, which are the prices these arms are scored on. Nothing about
the environment confounds the comparison in §1.

## 7. What this session did NOT do

- **No parameter was tuned, on 2022 or anywhere.** Per the rule-22 touchpoint loop, steps 1–2 only
  (run the frozen recipe; diagnose the object). Steps 3–4 — re-train on 2023–2025 around the
  diagnosed object, then re-test 2022 — belong to a later session, and the training window is the
  only place fitting ever happens.
- **No mechanism was tested**, so no cell in `docs/codebase-site/data/mechanism-matrix/ERCOT.js`
  changed (rule 26 `[R-MECH-MATRIX]` duty (b) is not triggered). The matrix was consulted and is
  cited here; both arms are replays of already-adjudicated cells.
- **No keeper changed.** `2026-09-05-ercot248-two-config-keeper` stands, and the `complete`
  marker's `keeper` field is untouched (rule 22 D-5(b) re-keying applies to *promotions*, and
  there was none).
- **The locked test was not touched.** No 2019 or H1-2026 artifact was read, solved or scored.

## 8. Recommended next steps, in priority order

1. **Upload the ERCOT HSL 2022 archives** (owner-side, Data Access Portal) and re-run both arms.
   Until then 2022's C1/C2 rows are not discriminating, and C3b/C3c carry an unquantified share of
   the same +6.4 TWh contamination.
2. **Owner decision on `ercot_reserve_supply_cap_from_year`** (§4). The measured series exists back
   to 2020; the gate excludes it on a premise the data contradicts. This is the one lever on this
   board aimed at §3's diagnosed object that costs zero DOF.
3. **The C3c price function remains THE open ERCOT object**, now with a second regime's evidence:
   the model selects the scarce hours correctly in *both* the conduct-priced 2023 regime and the
   administratively-priced 2022 regime, and prices them at ~nothing in both. Any Phase-0 on it must
   pre-register its statistic, grain and gates (the ercot-210 precommit pattern) and identify
   **only** on 2023–2025.
4. Consider extending the ladder to 2021 and 2020 once (1) lands — both years have GTC raws,
   `actual_tail.json` rows and ORDC reserve series already committed.
