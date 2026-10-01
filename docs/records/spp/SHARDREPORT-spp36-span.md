# SHARDREPORT — SPP-36 span shard (2026-09-12)

Registered run: **`2026-09-12-spp-36-shortwindow-span`** — **DETERMINATION: CALIBRATED**.

The arm is keeper 9's recipe (`spp27_span`) plus EXACTLY ONE armed gate,
`unit_outage_short_windows` (COAL scope; the gas companion stays `False`).
Full 2023–2025 span, ONE `replay_keeper.py` invocation, years sequential inside
it (rule 12 `[R-PARALLEL]`).

> **HEADLINE CAVEAT — 2024 and 2025 DO NOT REPRODUCE THE PER-YEAR SHARDS' ARM
> NUMBERS.** 2023 reproduces to four decimals. 2024 and 2025 diverge in slack,
> load-weighted price and coal/gas displacement. The divergence is reported at
> full magnitude in §5 and is NOT tuned toward the expected table. Nothing was
> re-run with varied flags and nothing was patched.

## 1. Hard stops — all four cleared before any solve

| # | check | result |
|---|---|---|
| 1 | `git rev-parse HEAD` | `706aa5475a44e2bb87326a556833f326f926160b` ✓ exact. No pull/rebase/merge was performed. |
| 2 | `tests/unit/pipeline/test_run_year_kwarg_binding.py` | **4 passed** in 0.51 s ✓ |
| 3 | `spp27_span/run_config.json` → `scenario_config` | `mustrun_window_commitment_grain` **True** · `unit_outage_short_windows` **False** · `offer_curve_by_group.CC_REGULAR` = committed/econ_low/econ_high/peak all **0.93** · `wefor_multiplier` **0.7** · `mode` **"backcast"** · `hindcast` **False** · `campd_per_unit_attribution` **False** · `campd_outage_merit_order_guard` **False** ✓ all nine |
| 4 | `data/raw/campd-unit-outages-short-SPP.csv` | **621 lines / 620 data rows**, `plant_group` = COAL on all 620 ✓. Not re-derived (rule 23 `[R-FROZEN-DERIVE]`). |

**Offer-curve identity.** `offer_curve_by_group` whole-mapping
`json.dumps(sort_keys=True)` SHA-256 is
`090abd793b5fa5a79b3e6102d5443585f44a3e6ddcdc264ea1f83be46ba62f65`
in **both** the arm and the control — stated explicitly, as required. The
authorized price-tuning channel (rules 1/13) is therefore byte-identical across
the A/B; the only config delta is the one armed gate
(`unit_outage_short_windows` False → True; gas companion `False`).

## 2. The solve

```
python3 scripts/replay_keeper.py results/calibration/spp27_span \
  --years 2023 2024 2025 \
  --out-dir results/calibration/spp36_span \
  --set unit_outage_short_windows=true \
  --note "SPP-36: ..."
```

- **Exit code 0**, wall time **377 s** (LP + three fleet builds), inside the 35-min budget.
- `unit_outage_short_windows_gas` was NOT passed; `--reuse-solved` was NOT passed.
- Container preflight: ceiling 13.34 GiB, 9 GiB swap provisioned → 22.3 GiB.
  Runner emitted the standard sub-24 GiB warning, which is scoped to per-plant
  MISO/PJM years and did not bind here.
- `memory peak: cgroup_peak_rss_gib=5.71, cgroup_peak_rss_plus_swap_gib=5.71, process_vmhwm_gib=5.15, process_vmswap_now_gib=0.00`

### The three derate lines, VERBATIM

```
short unit-outage derate (SPP 2023): 80 plant-tranches derated (< 5-day baseload-coal windows)
short unit-outage derate (SPP 2024): 73 plant-tranches derated (< 5-day baseload-coal windows)
short unit-outage derate (SPP 2025): 94 plant-tranches derated (< 5-day baseload-coal windows)
```

**80 / 73 / 94 — all three match the expected tranche counts exactly.** The
mechanism's input footprint is reproduced; the divergence in §5 is downstream of
it, in the LP solution, not in what was derated.

## 3. Annual TWh by class, arm vs control (P1)

Control = the committed `spp27_span` bundle (rule 29(b) form 4: the incumbent
keeper's committed numbers ARE the control; no control solve was spent).

### 2023
| class | arm TWh | ctl TWh | Δ TWh |
|---|---|---|---|
| COAL_PRB | 63.9116 | 65.6343 | −1.7227 |
| COAL_LIGNITE | 6.8735 | 7.1781 | −0.3046 |
| CC_CHP | 1.8527 | 1.8472 | +0.0055 |
| CT_CHP | 1.2143 | 1.2030 | +0.0113 |
| ST_CHP | 0.3097 | 0.2922 | +0.0175 |
| ST_GAS | 10.0952 | 9.6983 | +0.3970 |
| CC_REGULAR | 42.5693 | 41.8267 | +0.7425 |
| CT_PEAKER | 16.6146 | 15.7601 | +0.8545 |
| wind / nuclear / hydro / solar / biomass / oil / OTHER | — | — | 0.0000 |
| **TOTAL** | **284.6373** | **284.6364** | **+0.0009** |

**COAL Δ −2.0273 · GAS Δ +2.0108** — matches expected (−2.0273 / +2.0108) exactly.

### 2024
| class | arm TWh | ctl TWh | Δ TWh |
|---|---|---|---|
| COAL_PRB | 58.6172 | 60.6077 | −1.9905 |
| COAL_LIGNITE | 6.1791 | 6.5622 | −0.3831 |
| oil | 0.0033 | 0.0030 | +0.0003 |
| CC_CHP | 1.8900 | 1.8832 | +0.0068 |
| CT_CHP | 1.2466 | 1.2367 | +0.0099 |
| ST_CHP | 0.4246 | 0.3996 | +0.0250 |
| ST_GAS | 13.2733 | 12.8748 | +0.3985 |
| CC_REGULAR | 42.4066 | 41.6791 | +0.7275 |
| CT_PEAKER | 19.3074 | 18.0986 | +1.2087 |
| **TOTAL** | **291.0039** | **291.0008** | **+0.0031** |

**COAL Δ −2.3736 · GAS Δ +2.3514** — expected −2.4089 / +2.4117. **DIVERGES** (coal −0.035 TWh short).

### 2025
| class | arm TWh | ctl TWh | Δ TWh |
|---|---|---|---|
| COAL_PRB | 77.4872 | 80.4149 | −2.9277 |
| COAL_LIGNITE | 6.5483 | 6.7981 | −0.2498 |
| CT_CHP | 1.1555 | 1.1487 | +0.0067 |
| ST_CHP | 0.1855 | 0.1760 | +0.0095 |
| CC_CHP | 1.9486 | 1.9343 | +0.0143 |
| ST_GAS | 12.6132 | 12.0198 | +0.5934 |
| CT_PEAKER | 15.5101 | 14.2422 | +1.2679 |
| CC_REGULAR | 36.1986 | 34.9097 | +1.2889 |
| **TOTAL** | **302.0312** | **302.0280** | **+0.0032** |

**COAL Δ −3.1775 · GAS Δ +3.1713** — expected −2.5714 / +2.5709. **DIVERGES
materially: 24 % MORE coal displaced than the per-year shard reported.**

In every year the displacement is a near-exact coal→gas swap (residual ≤ 0.007 TWh
on ~290 TWh) and no VRE/nuclear/hydro row moves — the mechanism's footprint is
confined to the rows it claims.

## 4. System quantities, arm vs control (P1)

| year | leg | slack MWh | dump | demand TWh | LW price $/MWh | max zonal $ | hrs>200 |
|---|---|---|---|---|---|---|---|
| 2023 | arm | 0.0000 | 0.0000 | 284.5182 | 25.7428 | 61.4221 | 0 |
| 2023 | ctl | 0.0000 | 0.0000 | 284.5182 | 25.3716 | 59.3126 | 0 |
| 2024 | arm | 370.1017 | 0.0000 | 290.8868 | 26.0214 | 2000.0000 | 7 |
| 2024 | ctl | 370.1017 | 0.0000 | 290.8868 | 25.4676 | 2000.0000 | 5 |
| 2025 | arm | 0.0000 | 0.0000 | 301.8402 | 29.5377 | 85.9137 | 0 |
| 2025 | ctl | 0.0000 | 0.0000 | 301.8402 | 28.7893 | 73.7731 | 0 |

`hrs>200` counts hours whose **maximum zonal** price exceeds $200.

## 5. THE DIVERGENCE — reported loudly, not tuned

| year | quantity | expected (per-year shards) | **this span run** | verdict |
|---|---|---|---|---|
| 2023 | tranches | 80 | 80 | ✓ |
| 2023 | coal Δ / gas Δ TWh | −2.0273 / +2.0108 | −2.0273 / +2.0108 | ✓ exact |
| 2023 | arm slack / LW price | 0.0000 / 25.7428 | 0.0000 / 25.7428 | ✓ exact |
| 2023 | hrs>200 arm/ctl | 0 / 0 | 0 / 0 | ✓ |
| 2024 | tranches | 73 | 73 | ✓ |
| 2024 | coal Δ / gas Δ TWh | −2.4089 / +2.4117 | −2.3736 / +2.3514 | ✗ |
| 2024 | **arm slack MWh** | **1295.6995** | **370.1017** | ✗ (= the control's own slack) |
| 2024 | arm LW price | 26.3509 | 26.0214 | ✗ (−0.33) |
| 2024 | hrs>200 arm/ctl | 8 / 5 | 7 / 5 | ✗ arm |
| 2025 | tranches | 94 | 94 | ✓ |
| 2025 | coal Δ / gas Δ TWh | −2.5714 / +2.5709 | −3.1775 / +3.1713 | ✗ (24 % larger) |
| 2025 | **arm slack MWh** | **240.5966** | **0.0000** | ✗ (= the control's own slack) |
| 2025 | arm LW price | 30.0737 | 29.5377 | ✗ (−0.54) |
| 2025 | hrs>200 arm/ctl | 2 / 0 | 0 / 0 | ✗ arm |

**Every CONTROL figure reproduces exactly** (LW price 25.3716 / 25.4676 / 28.7893;
slack 0 / 370.1017 / 0; hrs>200 0 / 5 / 0). Since the control column is read from
the same committed bundle with the same aggregation the shards used, the
aggregation method is confirmed identical — so the discrepancy is a genuine
difference in the **arm's LP solution**, not a reporting or metric-definition
artifact.

### What was ruled out, at zero LP cost

1. **Cross-year LP warm-start** — `replay_keeper.py` pins
   `DETERMINISM_ENV = {"MARKET_SIM_WARMSTART_XYEAR": "0"}`, so a span run does
   not warm-start year N from year N−1. `docs/cross-year-warmstart.md` confirms
   reproducibility baselines pin it OFF "so byte-identity stays basis-independent",
   and states it is bit-neutral within a year regardless. **Not the cause.**
2. **Fleet evolution across the span** — backcast mode has no capacity evolution
   (`runner.py:707`: "the backcast (backcast mode has no capacity evolution)");
   each backcast year builds from its own year-matched EIA-860 vintage. A span
   year-2/3 fleet therefore equals a single-year run's fleet. **Not the cause.**
3. **Config partition** — `spp27_span/meta.json` carries no
   `config_partition_overrides`; the span is single-recipe, so
   `enforce_single_recipe_partition` did not refuse and every year replayed one
   config. **Not the cause.**
4. **Derate input** — tranche counts 80/73/94 match exactly, so the same
   plant-tranches were derated in the same years. **Not the cause.**
5. **Offer-curve drift** — arm and control `offer_curve_by_group` SHA-256 are
   identical. **Not the cause.**

### What remains — NOT resolved by this shard

Backcast years are independent, warm-start is off, and the fleet, the derate
input and the offer curve are all identical, so a span invocation *should*
reproduce three single-year invocations. It did for 2023 and did not for 2024
and 2025. The per-year shards' artifacts do not exist in this container, so the
two runs cannot be differenced directly here. **I did not re-run with varied
flags, did not run a single-year diagnostic, and did not patch anything** — all
four are forbidden to this shard.

Two candidate explanations, neither confirmed:
- the per-year shards' arm figures were produced under some difference this
  bundle cannot see (a different flag, SHA, or transcription); or
- there is genuine run-to-run variation in the SPP arm's LP solution near a
  degenerate scarcity boundary — note that in both divergent years **this run's
  arm slack equals the control's slack exactly** while the shards reported the
  arm pushing the system into *extra* scarcity.

The second would be the more serious finding, because prices are LP duals
(rule 4 `[R-DUALS]`) and a different optimal basis moves them. **The parent
should resolve this before the run is promoted to keeper.** Note also that this
run is the methodologically required construction — rule 16 `[R-ALLYEARS]`
(all years, one invocation, one bundle) — and the per-year arms were single-year
solves, which rule 16 admits only as throwaway diagnostic probes.

### Direction of the divergence

The divergence is **against** the arm, not for it: this span run shows the
mechanism producing *less* extra scarcity and a *smaller* price lift in 2024,
and a *larger* coal displacement with *no* extra scarcity in 2025. Nothing here
was adjusted toward the expected table (rule 1 `[R-STRUCT]`).

## 6. DOF ledger — `n_entries = 5`, `n_residual = 3` (expected 5 / 3 ✓)

The control's committed attestation was copied into the new bundle first, then
the ledger rebuilt over it, so the governance / disclosures / exceptions blocks
carry over.

| entry | identification |
|---|---|
| `offer_curve_by_group` | residual |
| `offer_curve_smoothing` | residual |
| `wefor_multiplier` | residual |
| `unit_outage_short_windows (< 5-day baseload-coal CEMS windows)` | **measured-physical** |
| `st_gas_mustrun_per_plant (ST_GAS local-reliability commitment floor, measured committed window)` | measured-physical |

Exactly as predicted: the control's own config rebuilt at HEAD gives 4/3, and
this arm adds exactly one entry — `unit_outage_short_windows`, identified
**measured-physical**. Nothing was adjusted.

(The control's *committed* attestation, written at its own older revision
`09d9fc00`, reads 3/2 and classifies `offer_curve_smoothing` as
measured-physical; the 4/3 baseline is that config rebuilt at HEAD, which also
adds `st_gas_mustrun_per_plant`. This is a ledger-construction difference
between revisions, not a solve difference.)

## 7. Legitimacy diagnostics — with ROW COUNTS

`legitimacy_diagnostics.py --bundle results/calibration/spp36_span --iso SPP --years 2023 2024 2025`

| gate | verdict | rows |
|---|---|---|
| D-1 diurnal shape | **PASS** | **25** |
| D-2 forced-energy attribution | **PASS** | **15** |
| D-4 off-window binding | **FAIL** | **71** (12 FAIL rows) |
| D-5 forecast/backcast parity | **PASS** | **8** |
| D-9 overlay quarantine | **PASS** | **5** |
| D-10 free-class-only rescore | **PASS** | **6** |
| Overall | **FAIL** | — |

**No gate is vacuous** — every gate carries a non-zero row count, so no PASS
here is a zero-row pass.

D-1 = 25, D-2 = 15, D-4 = 71 with 12 failures: **identical to the control's row
counts and failure count.** The 12 D-4 failures are all
`unit-conduct | st_gas_mustrun_per_plant × ST_GAS | h0-23` rows (plants 1230,
1235, 1271, 3008 in 2023; 1235, 1271, 3008, 6193 in 2024; 1230, 1235, 1271, 3008
in 2025) — a pre-existing control condition, untouched by this arm, and not
attributable to `unit_outage_short_windows`.

Gate thresholds in force: `d1_min_profile_r` 0.8 · `d1_min_cv_ratio` 0.5 ·
`d2_peaker_max_share` 0.15 · `d2_merchant_max_share` 0.3 ·
`d4_max_offwindow_share` 0.05.

## 8. Registration

```
RUN_ID=2026-09-12-spp-36-shortwindow-span
DETERMINATION: CALIBRATED [SPP spp 36 shortwindow span] — 1 ledgered caveat(s) (measured-input or model-class) — REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity (RT hourly)
```

Registered with `--no-prune` (required). `metrics.json` is written by
`dashboard_add_run.py`, not by the replay.

### Full `calibration_verdict.py` output

```
CALIBRATION DETERMINATION: CALIBRATED
  run 2026-09-12-spp-36-shortwindow-span  (SPP: spp 36 shortwindow span)
  scorable years: 2023, 2024, 2025

[✓] PASS    LOAD  C1 fuel-mix by class (grid-delivered)
        SKIPPED 2025 CC_REGULAR: preliminary EIA-923 vintage: incomplete plant data (5/22 prior plants missing (77% reporting)); not gated — C2 family grid reconcile covers this class
        SKIPPED 2025 CC_CHP: preliminary EIA-923 vintage: complete plant data (no per-class actual); not gated
        SKIPPED 2025 CT_PEAKER: preliminary EIA-923 vintage: incomplete plant data (46/62 prior plants missing (26% reporting)); not gated
        SKIPPED 2025 ST_GAS: preliminary EIA-923 vintage: incomplete plant data (16/36 prior plants missing (56% reporting); plant-months 96% present); not gated
        SKIPPED 2025 ST_CHP: preliminary EIA-923 vintage: immaterial plant data (no per-class actual); not gated
        SKIPPED 2025 COAL_PRB: preliminary EIA-923 vintage: incomplete plant data (3/29 prior plants missing (90% reporting)); not gated
        SKIPPED 2025 COAL_LIGNITE: preliminary EIA-923 vintage: complete plant data (no per-class actual); not gated
        SKIPPED 2025 COAL_BIT: preliminary EIA-923 vintage: immaterial plant data (no per-class actual); not gated
[✓] PASS    LOAD  C2 system volume (gas/coal families)
        SKIPPED 2025 gas: -16.2%
        SKIPPED 2025 coal: +2.4%
[✓] PASS    LOAD  C3a mean LMP
        SKIPPED 2023 da_diagnostic: -6.6% vs DA (DA−RT premium $+2.42)
        SKIPPED 2024 da_diagnostic: -8.0% vs DA (DA−RT premium $+2.84)
        SKIPPED 2025 da_diagnostic: -2.2% vs DA (DA−RT premium $+1.60)
[✓] PASS    LOAD  C3b price duration/shape
[~] CAVEAT  SUPP  C3c price tail / scarcity (RT hourly) [ledgered]
        CAVEAT  2023: model 0h [energy-only LMP] vs RT actual 42h (0.00×, >$200)  [ACCEPTED MODEL-CLASS LIMITATION]
        SKIPPED 2023 da_diagnostic: model 0h vs DA actual 6h (out-of-representation companion)
        CAVEAT  2024: model 7h [energy-only LMP] vs RT actual 59h (0.12×, >$200)  [ACCEPTED MODEL-CLASS LIMITATION]
        SKIPPED 2024 da_diagnostic: model 7h vs DA actual 35h (out-of-representation companion)
        CAVEAT  2025: model 0h [energy-only LMP] vs RT actual 68h (0.00×, >$200)  [ACCEPTED MODEL-CLASS LIMITATION]
        SKIPPED 2025 da_diagnostic: model 0h vs DA actual 0h (out-of-representation companion)
[✓] PASS    SUPP  C4 fleet hourly dispatch correlation
[✓] PASS    PROT  C6 governance gate
[✓] PASS    PROT  C8 forced-energy share (D-2)
[·] REPORT  ----  C5a CO2 vs eGRID (REPORTED-ONLY, v2.9)
        PASS    2023: -2.7%
        PASS    2024: -2.5%
        PASS    2025: +1.4%
[·] REPORT  ----  D-A diurnal price amplitude, hour-of-day (REPORTED-ONLY, BAND-FREE, v3.5)
        REPORTED 2023: amplitude 39.7% of measured (hod range $11.69 vs $29.48); peak h17 vs h17, trough h02 vs h01 — phase OK; hod r +0.947; 364 complete days
        REPORTED 2024: amplitude 40.0% of measured (hod range $14.92 vs $37.29); peak h16 vs h16, trough h01 vs h01 — phase OK; hod r +0.970; 364 complete days
        REPORTED 2025: amplitude 25.8% of measured (hod range $12.20 vs $47.28); peak h17 vs h17, trough h01 vs h01 — phase OK; hod r +0.893; 364 complete days
------------------------------------------------------------------------
D-10 free-class C1: C1 all 16/16 · free 12/12
  pinned (excluded from free): CC_CHP, ST_CHP
determination basis:
  - 1 ledgered caveat(s) (measured-input or model-class) — REPORTED, and NOT determination-downgrading under rubric v3.3: C3c price tail / scarcity (RT hourly)
```

C3c is the single ledgered caveat and the only non-PASS; the C8 protective
forced-energy gate PASSES, and the D-4 gate FAIL above does not flip it.

## 9. Registry/payload parity

`scripts/check_registry_payload_parity.py` → **FAILED**, on four bundles that
are **not this shard's and predate it**, all tracked at HEAD:

| bundle | files tracked at HEAD |
|---|---|
| `results/calibration/caiso275_B_gascoupling_2023` | 11 |
| `results/calibration/caiso275_B_gascoupling_2024` | 13 |
| `results/calibration/caiso275_B_gascoupling_2025` | 14 |
| `results/calibration/nyiso227_rebasis_span` | 18 |

Each is the Class-E "bundle dir maps to no retained sidecar" condition —
committed CAISO and NYISO bundles that outlived their sidecars. **`spp36_span`
is not flagged** (it is gitignored and unregistered-as-a-dir, exactly as rules
29(c)/31 require), and neither is `spp27_span`. This shard did **not** touch
them: they belong to other ISOs' lanes, and rule 31 `[R-RETAIN]` forbids
deleting results. **The parent should route this inherited RED to the CAISO and
NYISO lanes.**

## 10. Retention (rule 31 `[R-RETAIN]`)

`results/calibration/spp36_span/` is on local disk and **gitignored**; only the
17 slim files listed in the shard prompt plus the registration outputs are
committed. The bundle's un-pushed parts (`dispatch/`, `unit_hourly_*`,
`network_*`, `btm.parquet`, `flows.parquet`, `system.parquet`, `floors/`) **will
not survive this container.** Nothing under `results/` was deleted.

**The parent must decide on promotion.** This shard does not promote the keeper
— no edit was made to `frontend/data/backcast/keepers/**` or
`calibration-complete.json`, and `build_status.py` / `prune_iso_runs.py` /
`build_manifest.py` were not run. Given §5, **promotion should not proceed until
the 2024/2025 divergence is explained.** Re-solving this span costs ~380 s of LP
plus three fleet builds.
