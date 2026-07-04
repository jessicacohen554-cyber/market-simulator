# Out-of-sample results (2026-07) — S4 / audit D-6 + D-8

**Scope of this session.** The assigned task (legitimacy audit §5.3, §7 D-6/D-8;
`docs/legitimacy-scrub-prompts-2026-07.md` S4 item 2–3) was to (1) score the
designated untrained holdouts — **2022** and **H1-2026** — once each with the
FROZEN current keeper configs, and (2) run the D-8 frozen-coefficient stability
checks. During the session the owner instructed: *"Don't run any 2022 or 2026
model runs. These are holdout years to avoid overtraining."* Per that
instruction **no holdout LP solve was run** (D-6 steps 1–2 not executed). What
this document delivers:

- **D-6 (holdout scoring): NOT RUN.** Both because of the owner's instruction
  and — established independently below — because the **scoring-target and
  fleet-overlay data for 2022 / H1-2026 are not in the repository**, so the
  holdout is un-scorable from repo data today regardless of the run decision.
- **D-8 (frozen-coefficient stability): RUN, in full.** Uses only the 2023–2025
  in-sample CAMPD / EIA-930 data the coefficients were fitted on — no holdout
  year is touched. This is the one out-of-sample-*discipline* number this
  session can honestly produce.

> **Methodological note (recorded, not a challenge to the instruction).** The
> D-6 protocol — solve a frozen config on a held-out year *once*, score once,
> and never re-tune against the result — is the standard technique for
> *measuring* overfit without causing it; overtraining would arise only if the
> configs were subsequently tuned to the holdout, which the protocol forbids.
> "Score the holdout once" and "avoid overtraining" are not in conflict under
> that discipline. The instruction is respected here in full; this note simply
> records why the D-6 table is absent so a future session can re-open it if the
> owner chooses.

---

## 1. Holdout data-coverage assessment (why D-6 is un-scorable from repo data)

A holdout score needs three things for the target year: **driver inputs**
(demand, fuel), **fleet + overlay inputs** (CAMPD unit-level binning, outages,
delivered fuel), and — decisively — **bench actuals to score against**
(EIA-930 fuel-mix, CAMPD generation). Coverage of the repo's `data/raw/` for the
two holdout windows:

> **Coverage table updated by the 2026-07-04 intake (see §1.1) — ERCOT and PJM
> only.** The original (pre-intake) assessment is preserved in the conclusion
> paragraph below; the table shows the coverage as of 2026-07-04.

| Input | Datatype / path | 2022 | H1-2026 | Role |
|---|---|:--:|:--:|---|
| Demand (hourly) | `eia-930-hourly/*.parquet` | ✅ 2015–2026 (ERCO), ✅ 2022–2026 (PJM) | ✅ through 2026-06-30 | driver |
| Demand (ERCOT native, zonal) | `zone-specific-demand/…`, `ercot/ACTUALSYSLOAD*` | ✅ | ✅ | driver |
| Demand (model profiles) | `eia-930/eia_demand_profiles{,_meta}.parquet` | ✅ 2021–2025 | ❌ no 2026 (full-8760 contract; partial year unbuildable) | driver |
| Gas — Henry Hub | `gas-prices/henry_hub_{daily,monthly}.csv` | ✅ 1997–2026 | ✅ through 2026-06 | driver |
| Gas — delivered-to-EP (EIA N3045) | `ercot_electric_power_gas_price.csv`, `pjm_zonal_gas_hub.csv`, `gas_basis_by_iso_month.csv` | ✅ | ⚠️ Jan–Apr only (EIA lag) | driver (backcast) |
| Gas — ERCOT zonal hub (F923 Sch5 / Waha) | `ercot_zonal_gas_hub.csv` | ❌ 2023–2025 only | ❌ | driver (backcast; ercot32 keeper enables it — **follow-up F1**) |
| **Fleet — CAMPD unit-level (binning)** | `campd-unit-level/{ST}_{YEAR}.parquet` | ✅ TX + 14 PJM states | ⚠️ Q1 only (Q2 unposted) | fleet build |
| Outages (CAMPD unit overlay) | `campd-unit-outages.csv`, `campd-unit-outages-PJM.csv` | ✅ | ⚠️ windows through 2026-03-31 | overlay (backcast) |
| **Bench — EIA-930 fuel-mix actuals** | `eia-930/{BA}_fueltype_{YEAR}.parquet`, `eia-930/*BALANCE*`, wide extracts | ✅ | ✅ through 2026-06-30 | **scoring target** |
| **Bench — CAMPD generation actuals** | `campd-unit-level/*` | ✅ | ⚠️ Q1 only | **scoring target** |

**Conclusion (original 2026-07 assessment, pre-intake).** Only the *driver*
series (demand, Henry Hub) reached back to 2022 and forward to 2026. Every
**scoring target** (EIA-930 fuel-mix and CAMPD generation) and every
**fleet/overlay** input (CAMPD unit-level binning, delivered gas, outage
windows) was present **only for 2023–2025**, so a 2022 or H1-2026 backcast
could be *driven* but **not scored**. The 2026-07-04 intake (§1.1) cleared
this for **ERCOT and PJM**; the gap remains for CAISO / MISO / NYISO / NEISO.

### 1.1 Intake 2026-07-04 — 2022 + H1-2026 source data, ERCOT + PJM

Executed under the owner's explicit intake-only instruction ("data intake
only, no model solve — unblocks D-6"); **no 2022/2026 LP was constructed,
solved, or scored**, and no calibration-complete marker was set. Note the
tension with the strict reading of CLAUDE.md rule 22 (intake at
validation time): the owner's task authorizes decoupling the *intake* from the
*one-shot scoring*, which remains quarantined and separately authorized.
Verification: `python scripts/verify_holdout_intake.py` (loader dry-run,
prints shapes/nonzeros; no LP).

Per-ISO / per-datatype / per-year — landed vs unpublished (retrieval date
2026-07-04):

| Datatype | Year | ERCOT | PJM | Provenance |
|---|---|---|---|---|
| EIA-930 fuel-mix + demand (tidy long) | 2022 | ✅ 61,320 fuel + 35,040 region rows | ✅ 70,065 fuel + 34,994 region rows | `api.eia.gov/v2/electricity/rto/{fuel-type,region}-data` via `scripts/fetch_eia930_long.py` → `data/raw/eia-930/{BA}_{fueltype,region}_2022.parquet` |
| | H1-2026 | ✅ 34,800 + 17,400 rows (Jan 1–Jun 30) | ✅ 34,792 + 17,351 rows | same, `…_2026.parquet`; pull closed on the local Jun-30 boundary |
| EIA-930 wide extracts (loader/bench path) | 2022 | ✅ already present (2015–2026 file) | ✅ 8,760 h rebuilt in | `scripts/build_eia930_hourly_from_raw.py` (PJM rebuilt from long union; ERCO extended **append-only**, all 95,376 pre-existing rows byte-identical) |
| | H1-2026 | ✅ 4,343 h through Jun 30 hr 24 | ✅ 4,343 h | same |
| EIA-930 BALANCE six-month bulk | 2022 | ✅ 273,621 + 275,330 rows (63 BAs, both halves) | (all-BA files) | `www.eia.gov/electricity/gridmonitor/sixMonthFiles/` via `scripts/fetch_eia930_balance.py`; 2022 in EIA's legacy 44-col taxonomy, 2026 in the 65-col taxonomy — matching how EIA serves each archived half-year |
| | H1-2026 | ✅ 260,590 rows (62 BAs, Jan_Jun) | (same file) | same |
| CAMPD unit-level hourly | 2022 | ✅ TX: 3,502,152 rows (130 fac / 408 units) | ✅ 14 states: 12,081,216 rows | `api.epa.gov/easey/bulk-files/emissions/hourly/state/…` via `scripts/fetch_campd_unit_level.py`; arrow schema verified == sibling per file |
| | 2026 | ⚠️ **Q1 only** — TX: 913,680 rows (Jan 1–Mar 31) | ⚠️ **Q1 only** — 2,680,560 rows | `…/emissions/hourly/quarter/emissions-hourly-2026-q1.csv` (posted 2026-07-03); **Q2-2026 not yet published by EPA** |
| Unit-outage overlay (derived) | 2022 | ✅ 569 windows | ✅ 1,103 windows | `scripts/derive_campd_unit_outages.py --years 2022 2023 2024 2025 2026`; see re-derivation note below |
| | 2026 | ⚠️ 220 windows, clipped at 2026-03-31 | ⚠️ 261 windows, clipped | publication-horizon clipping added to the derive script (see note) |
| Delivered gas (EIA N3045 monthly) | 2022 | ✅ 12 months (`N3045TX3`) | ✅ 8 zones (annual basis) | `scripts/fetch_eia_delivered_gas.py`; `--validate` reproduces every committed 2023–2025 PJM zonal value to ±0.001 |
| | 2026 | ⚠️ Jan–Apr only (EIA ~3-month lag) | ⚠️ Jan–Apr, rows flagged `PARTIAL YEAR … winter-weighted` (WV: 1 month, proxied to OH+PA per the committed WV-2025 convention) | May-2026+ unpublished; re-extend when EIA posts them |
| Citygate basis (pre-existing) | 2022 / 2026 | ✅ 12 mo / ⚠️ Jan–Feb | ✅ 12 mo / ⚠️ Jan + Mar | `gas_basis_by_iso_month.csv` already extended by the fetch workflow; 2026 gaps are EIA-withheld months |

**Re-derivation note (unit-outage overlay).** Re-deriving with the new years
left ERCOT's 2023–2025 windows **byte-identical** and changed exactly **4 PJM
2024 windows** (Red Oak 1–3, Garrison Energy Center — dropped): the rebuilt
PJM wide extract restored 24/22/6 EIA-930 hours that the old extract was
missing in 2023/2024/2025, and the per-year revealed-availability mask now
sees those hours. This is a measured-data completeness correction (rule 13),
**not** holdout leakage — detection and masks are strictly per-year, and
2022/2026 data cannot influence 2023–2025 windows. Flagged for the PJM
calibration owner: the pjm-76 keeper's committed bundle is unchanged, but a
re-solve of its recipe would see the corrected overlay. The derive script also
gained **publication-horizon clipping**: an in-progress year's clock now ends
at the last published CAMPD date, so the unpublished Q2–Q4 2026 no longer
reads as a phantom Apr–Dec outage on every unit (pre-fix it did).

**Still unpublished (honesty note).** (a) EPA CAMPD hourly **Q2-2026** (Apr–Jun)
— not posted as of 2026-07-04, so H1-2026 CAMPD-side bench/fleet/outage
coverage is **Jan–Mar only**; (b) EIA delivered-gas months **May-2026+**;
(c) scattered EIA-withheld citygate/N3045 months (WV nearly all of 2025–2026).
EIA-930 (fuel-mix + demand) is the one H1-2026 series that is **complete**
through June 30.

**Follow-ups (needed before a 2022 / H1-2026 solve is *scorable*, not part of
this intake):**

- **F1 — `ercot_zonal_gas_hub.csv` 2022/2026 rows.** The ercot32 keeper
  enables `ercot_zonal_gas_basis`; the loader falls back to the
  scalar-anchored mean-zero behaviour for uncovered years. The 2023–2025 rows
  were hand-derived from EIA-923 Schedule-5 quantity-weighted plant receipts
  (North/South/South_Central) and NGI/EIA Waha annual averages
  (West/Panhandle) — reproducing them for 2022 needs the F923 Sch5 workbook
  (published, `www.eia.gov` reachable) and a Waha annual source; 2026 needs
  months not yet published. Not mechanically derivable from the API alone, so
  deferred rather than approximated.
- **F2 — PJM native DataMiner `gen_by_fuel` 2026.** `PJM_2022…2025_gen_by_fuel.csv`
  exist; 2026 needs a registered DataMiner subscription key (none in repo).
  Affects only the clean `generation/PJM` datatype (`is_renewable` flag); the
  EIA-930 PJM fuel-mix — the actual scoring bench — is landed through June.
- **F3 — `eia_demand_profiles{,_meta}.parquet` 2026 rows.** Full-8760 contract
  (`load_demand` asserts 8760); a partial year is unbuildable by design. Build
  at one-shot validation time once the H1-2026 scoring window handling is
  decided. No builder script exists in-repo (hand-uploaded artifact).
- **F4 — scoring-path year registration.** `scripts/build_calibration_reference.py`
  `CALIBRATION_YEARS` has no 2026 and `HENRY_HUB_ACTUAL` lacks 2026 (KeyError
  if asked); extend at validation time, not before.
- **F5 — per-plant monthly coal pricing and fossil CO2 rates for 2022/2026**
  (F923 fuel receipts; CEMS-derived plant emission rates) — the remaining
  backcast fuel overlays; non-trivial derivations, deferred.
- **F6 — facility-level CAMPD outage extracts** (`campd-facility-level/`,
  `campd-outages*.csv`) still 2023–2025; the unit-level overlay above is the
  one the ERCOT/PJM keepers consume.

---

## 2. D-8 — frozen-coefficient stability (RUN)

**Design.** For each *fitted-to-the-scored-years* coefficient family, refit on a
**training subset** of the calibration years and measure (a) how far the
coefficients move vs the all-years fit the keeper ships, and (b) how well the
training fit predicts the held-out calibration year. This exercises the audit's
"regression floors absorbing residual" concern using **only 2023–2025** data —
no holdout year. Harness: `scripts/d8_coefficient_stability.py`
(bundle: `results/calibration/d8-coefficient-stability/`); it imports and reuses
each mechanism's **own frozen derive/probe fit code**, so the numbers are on the
identical estimand the keeper uses. Validation of faithfulness: the ERCOT
all-years drag fit reproduces the shipped `ScenarioConfig` default exactly
(slope 0.00703, cap 0.47).

### 2A. Net-load drag hinge — leave-2025-out

Fit the evening-ramp `frac = clip(slope·netGW + intercept, 0, cap)` floor on
**2023–24 only**, then predict the 2025 floor energy and compare to the
all-years fit. `pred2025 floor` is the drag's *minimum* the LP exceeds
economically (NOT a match to total CT energy — the measured column is context,
not an error bar).

| ISO | slope (train→full) | drift | zero-cross GW (train→full) | cap (train→full) | pred-2025 floor TWh (train→full) | floor drift | measured 2025 CT TWh |
|---|---|:--:|---|---|---|:--:|:--:|
| **ERCOT** | 0.00693 → 0.00703 | **−1.5%** | 20.9 → 20.3 | 0.468 → 0.47 | 2.84 → 2.97 | **−4.2%** | 7.0 |
| **PJM** | 0.00930 → 0.01108 | **−16.1%** | 88.3 → 90.1 | 0.416 → 0.46 | 6.64 → 7.16 | **−7.2%** | 22.3 |
| **CAISO** | 0.01064 → 0.00901 | **+18.1%** | 11.3 → 12.5 | 0.411 → 0.356 | 1.59 → 1.20 | **+32.2%** | 1.36 |

- **ERCOT** — the template mechanism — is **stable**: slope drift −1.5%,
  zero-crossing moves 0.6 GW, floor-energy prediction within 4.2%. Leaving 2025
  out barely moves the ERCOT drag. This is the one coefficient family with clean
  cross-year identification.
- **PJM** slope drifts 16% and the cap moves 0.42→0.46; the applied floor energy
  still predicts within 7%, so the *level* is more robust than the slope. The
  hinge is moderately, not well, identified across years.
- **CAISO** is the least stable: slope drifts 18% and, because the CAISO floor
  is nearly the entire measured CT energy (floor 1.2 vs measured 1.36 TWh — a
  much higher forced share than ERCOT/PJM, where the floor is a fraction of CT),
  the 32% floor-energy prediction drift lands directly on dispatched volume. The
  CAISO CT floor is close to fitting the CT class outright, and its year-to-year
  identification is weak.

### 2B. Temperature-CF reliability floor — leave-2025-out

Recompute per-(zone,class,limb) `floor_pct = commit_frac · min_stable_pct` on
2023–24 CAMPD, and score the 2025-only value. Only the **hot (tmax)** limbs
cleared the enable gate anywhere; all reported limbs below are ones the train or
hold fit would enable.

**Headline: every limb's enable flag flips True→False from 2023–24 to 2025-only,
but this is dominated by a sample-size artifact, not coefficient collapse.** The
enable gate requires `n ≥ 30` flagged (design-cooling) days; a *single* year
supplies only ~3–23 such days per zone×class, so 2025-alone fails `N_MIN`
mechanically. The shipped coefficient uses all three years pooled and clears the
gate. The honest signal is therefore the **`floor_pct` drift** and the **ρ
stability**, not the flip:

| ISO | zone / class | floor_pct (train→2025) | drift | ρ (train→2025) | flag |
|---|---|---|:--:|---|---|
| ERCOT | Houston / CT_PEAKER | 0.339 → 0.298 | **+13.5%** | 0.47 → 0.87 | large drift |
| ERCOT | Houston / CC_REGULAR | 0.512 → 0.520 | −1.6% | 0.39 → 0.87 | stable |
| ERCOT | North / CT_PEAKER | 0.105 → 0.105 | 0.0% | 0.49 → 0.50 | stable |
| PJM | EMAAC / ST_GAS | 0.103 → 0.076 | **+35.8%** | 0.37 → 0.81 | large drift |
| PJM | SWMAAC / CT_PEAKER | 0.320 → 0.379 | **−15.6%** | 0.31 → 0.25 | large drift; ρ weak |
| PJM | ATSI / CT_PEAKER | 0.307 → 0.328 | −6.6% | 0.37 → 0.18 | ρ decays |
| PJM | ComEd / COAL | 0.389 → 0.375 | +3.5% | 0.49 → 0.18 | ρ decays |
| PJM | **ComEd / CC_REGULAR** | 0.490 → 0.520 | −5.7% | **0.35 → −0.19** | **ρ SIGN FLIP** |
| PJM | ATSI / CC_REGULAR | 0.516 → 0.520 | −0.9% | 0.41 → 0.05 | ρ collapses |
| PJM | West_APS / COAL | 0.354 → 0.357 | −0.9% | 0.39 → 0.55 | stable |
| PJM | Central_PA / ST_GAS | 0.117 → 0.115 | +1.8% | 0.39 → 0.50 | stable |
| CAISO | **SP15 / ST_GAS** | 0.079 → 0.058 | **+35.7%** | **0.41 → −0.16** | **ρ SIGN FLIP** |
| CAISO | **SP15 / CC_REGULAR** | 0.330 → 0.296 | +11.6% | **0.69 → −0.10** | **ρ SIGN FLIP** |

- **Coefficient level is mostly stable** (most `floor_pct` drifts < 6%), but
  **five limbs drift > 11%** (ERCOT Houston CT +13.5%, PJM EMAAC ST_GAS +35.8%,
  PJM SWMAAC CT −15.6%, CAISO SP15 ST_GAS +35.7%, CAISO SP15 CC_REGULAR +11.6%)
  — beyond a defensible physical-uncertainty band.
- **The identification is fragile**: several PJM limbs' Spearman ρ decays toward
  zero out-of-training, and **three limbs flip ρ sign** — PJM ComEd CC_REGULAR
  (+0.35 → −0.19) and **both** CAISO SP15 limbs (ST_GAS +0.41 → −0.16;
  CC_REGULAR +0.69 → −0.10) — the exact "sign flip = unidentified" signature D-8
  is designed to catch. For these limbs the temperature→commitment relationship
  reverses out-of-training, so it is not physically identified. CAISO is the
  worst-affected ISO (both its scored limbs sign-flip).

### 2C. Coal passthrough sigmoid — leave-2024-out identifiability

The `COAL_SIGMOID_DEFAULTS` params (`floor`, `ceil`, `gas_mid`, `gas_slope`) are
**hand-tuned** to a per-month coal-vs-gas breakeven across 2023–25 — there is no
automated objective to mechanically refit, so a literal "refit-without-2024" is
not defined. What *is* rigorously computable is **identifiability**: which years'
monthly delivered-gas actually sample each end of the logistic. A sigmoid's
cheap-gas asymptote (`floor`) is identified only by months **below** `gas_mid`;
its dear-gas asymptote (`ceil`) only by months **above**.

Monthly delivered-gas ($/MMBtu) coverage vs each ISO's `gas_mid`:

| ISO (`gas_mid`) | year | gas min–max (mean) | months below / above `gas_mid` |
|---|:--:|---|:--:|
| **ERCOT** (2.85) | 2023 | 1.84–2.41 (2.04) | **12 / 0** |
| | 2024 | 1.52–1.99 (1.69) | **12 / 0** |
| | 2025 | 2.72–3.56 (3.02) | 4 / 8 |
| **PJM** (3.40) | 2023 | 2.89–3.79 (3.21) | 9 / 3 |
| | 2024 | 2.57–3.37 (2.86) | **12 / 0** |
| | 2025 | 3.77–4.94 (4.19) | **0 / 12** |

- The sigmoid's two asymptotes are anchored by **disjoint single years**: the
  **cheap-gas `floor` by the cheapest year (2024)** and the **dear-gas
  `ceil`/`gas_mid` by 2025** (the only above-`gas_mid` year for both ISOs;
  wholly-above for PJM). 2023 is a redundant near-`gas_mid` middle.
- **Leave-2024-out is the binding test.** For PJM, removing 2024 removes the
  deepest cheap-gas observations; 2023 still has 9 below-mid months but at a
  ~$0.35/MMBtu-higher floor, so the fitted `floor` would ride up (less
  cheap-gas discount) with no data to contradict it. For ERCOT, 2023 is also
  fully below `gas_mid`, so the `floor` survives leave-2024-out — but note
  **`gas_mid` = 2.85 sits above *every* month of 2023 and 2024**: the
  midpoint/`ceil` are identified by **2025 alone**. Either way, each of the
  four sigmoid parameters is effectively pinned by a **single** gas regime —
  the family is **weakly identified / borderline unidentified** on three years
  of three distinct gas regimes, exactly the audit's concern.

---

## 3. Per-ISO verdict on forecast-skill evidence

**ERCOT.** *Best-supported of the three.* The net-load drag — ERCOT's headline
structural mechanism and the template copied to other ISOs — is genuinely
cross-year stable (slope −1.5%, floor-energy −4.2% out-of-training), which is
real evidence the drag reflects a persistent net-load→commitment relationship
rather than a 2025-fitted residual. The temperature-CF floors are mostly stable
at the level, with one > 13% limb drift. But the forecast-skill *claim* remains
**unproven, not disproven**: the D-6 out-of-sample dispatch score that would test
it cannot be produced — the 2022/2026 bench actuals are absent from the repo, and
per instruction no solve was run. The coal sigmoid's `gas_mid`/`ceil` ride on
2025 alone.

**PJM.** *Weaker identification.* The drag hinge slope drifts 16% leave-2025-out
(level more robust, 7%), and the temperature-CF floors show the clearest
instability in the study — multiple ρ decays and a **sign flip** (ComEd
CC_REGULAR) that flags an unidentified limb, plus a 36% floor drift on EMAAC
ST_GAS. The coal `floor` is anchored on 2024 and would drift up if 2024 were
removed. On the D-8 evidence, several PJM reliability-floor coefficients are not
yet at "physically identified"; treat PJM forecast skill as **asserted, largely
unverified**.

**CAISO.** *Least stable, highest forced-share.* The CT drag slope drifts 18%
and — because the CAISO floor is ~90% of the measured CT energy (vs a small
fraction for ERCOT/PJM) — the 32% out-of-training floor-energy drift lands
directly on dispatched volume. A floor that nearly equals the class it floors,
and that moves this much year-to-year, is close to fitting the CT class rather
than deriving it. It is also the worst ISO on the temperature-CF limbs: **both**
scored SP15 limbs (ST_GAS, CC_REGULAR) sign-flip ρ out-of-training and one
drifts 36%. This is the weakest forecast-skill evidence of the three and aligns
with the audit's CAISO CT-forcing finding (§5.4, L-rows). No CAISO coal sigmoid
exists (no coal fleet), so 2C is N/A.

**MISO / NYISO / NEISO.** Not evaluated this session (D-8 focused on the three
ISOs whose drag mechanisms the audit names). Data to extend D-8 to them is
present (CAMPD unit-level + EIA-930 hourly + zone temps for 2023–25); the harness
is ISO-generic for the temperature-CF and coal-coverage parts and could be
pointed at them in a follow-up.

---

## 4. Dashboard registration

D-6 produced **no backcast run/bundle** (no solve was run), so there is nothing
to register on the run-explorer dashboard as a holdout probe. The D-8 output is a
coefficient-stability analysis, not a scored `dispatch/<year>.parquet` bundle;
it lives at `results/calibration/d8-coefficient-stability/summary.json` and is
reported here. If the owner later authorizes the D-6 solves (after the 2022/2026
bench-data intake), those runs would be registered as `probe` entries per the
usual `calibration-report` flow.

## 5. Open follow-ups (root-cause items, not fixes)

1. **Intake 2022 + H1-2026 bench + fleet data** (EIA-930 fuel-mix, CAMPD
   unit-level, delivered gas) so D-6 becomes scorable. ~~Un-scorable today.~~
   **DONE for ERCOT + PJM 2026-07-04 (§1.1)** — remaining gaps are the
   unpublished months (CAMPD Q2-2026, delivered gas May-2026+) and the §1.1
   follow-ups F1–F6; still open for CAISO / MISO / NYISO / NEISO.
2. **Temperature limbs with ρ sign flips — PJM ComEd CC_REGULAR and both CAISO
   SP15 limbs (ST_GAS, CC_REGULAR).** Unidentified out-of-training; re-examine
   whether these tmax limbs should ship for those zone/classes at all.
3. **CAISO CT drag forced-share.** Floor ≈ measured CT energy + 18% slope drift
   → the floor is fitting the class. Cross-reference the audit's D-2 forced-
   energy attribution and L-row scrub for CAISO CT.
4. **Coal sigmoid single-year-per-parameter identification.** `gas_mid`/`ceil`
   ride on 2025; `floor` on 2024. Document as literature/physically-anchored
   where possible rather than presenting as a 3-year fit.
