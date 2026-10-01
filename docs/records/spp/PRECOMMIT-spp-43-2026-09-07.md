# PRECOMMIT — SPP-43: re-baseline keeper-2's recipe on the screened wind input (SPP-41 route (b))

**Lane** SPP-43 · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-07 ·
**Branch** `claude/spp-43-screened-rebaseline-2ro0x8` (base `origin/main` `dcb609f4`) · **Data profile** `spp` ·
**Charter** plan §5 row SPP-43 (issued r#8) — SPP-41 §5 route (b) ·
**Control** keeper-2 `2026-09-07-spp-2-crosswalk-hydro` / `results/calibration/spp42_crosswalk_B`
(rule 29(b) **form 4** — its committed bundle, never re-solved).

**This document is pushed BEFORE the solve.** Every gate value, the screen exemption, the G-DRIFT
audit and the promotion rule below are declared here so none of them can be written to fit a result.

---

## 0. Preconditions (verified, `git log origin/main`)

| precondition | check | state |
|---|---|---|
| SPP-41 LANDED (PR #5497) | `origin/main:docs/handoffs/FINDING-spp-41-2026-09-07.md` exists; `actuals._screen_fuel_spike_columns` live at HEAD | **MET** |
| SPP-42 LANDED (PR #5471) | `origin/main:results/calibration/spp42_crosswalk_B/meta.json` exists; `keepers/SPP.json` keyed to `2026-09-07-spp-2-crosswalk-hydro` | **MET** |
| Rule 12 — no concurrent per-plant SPP solve | `ps aux` clean in this isolated container; 15 GB free vs keeper-2's measured 5.55 GB peak RSS. Containers are isolated, so a solve in another session cannot contend for this host's RAM; the desk's concurrency cap is satisfied by construction | **MET** |

## 1. THE RECIPE — keeper-2's `meta.json` flags exactly, and nothing else

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 2024 2025 \
    --out-dir results/calibration/spp43_screened_B \
    --hydro-backfill-year 2024 --hydro-eia930-monthly
```

No other flag. No `ScenarioConfig` default is touched, no offer band moves (SPP carries the identity
1.0 on every key — rule 25), the seam (`actuals.py`) is not edited, the benchmark builder is not
edited. **The only thing that changed under this recipe since keeper-2 solved it is the loader seam
SPP-41 landed.**

## 2. ZERO-LP PHASE 0 (rule 29(0)) — measured at HEAD before this document was pushed

### 2a. FINDING-spp-41 table 0b reproduced for SPP — INPUT path, `load_eia_hourly_renewable_gen`

`before` = `_screen_fuel_spike_columns` masked to the identity; `after` = the live seam. All
`actuals` / `renewables` `lru_cache`s cleared between arms.

| year | series | before GWh | after GWh | Δ GWh | max MW (hour) before → after | verdict |
|---|---|---:|---:|---:|---|---|
| 2023 | wind | 106,634.4740 | **103,048.7595** | **−3,585.7145** | 3,589,445 (h3907) → 23,280 (h1795) | **MOVED** |
| 2023 | solar | 589.3480 | 589.3480 | +0.0000 | 290 (h5488) → 290 (h5488) | identical |
| 2024 | wind | 109,316.5290 | 109,316.5290 | +0.0000 | 23,400 (h4028) → 23,400 (h4028) | identical |
| 2024 | solar | 1,198.6450 | 1,198.6450 | +0.0000 | 661 (h6131) → 661 (h6131) | identical |
| 2025 | wind | 110,457.4360 | 110,457.4360 | +0.0000 | 23,960 (h5446) → 23,960 (h5446) | identical |
| 2025 | solar | 2,347.7450 | 2,347.7450 | +0.0000 | 991 (h7353) → 991 (h7353) | identical |

**Reproduces SPP-41 table 0b to the digit on every one of the six cells.** One mover, as charted.

### 2b. The LP-side bound — what the solve actually sees (the −27 GWh)

Two on-recipe `run_year(fleet_only=True)` rebuilds per year from keeper-2's `meta.json`
(`replay_keeper.run_year_kwargs` + `derived_run_year_inputs` — the sanctioned fleet-only
reconstruction), differing ONLY in whether the seam is live. `_mw_to_cf` divides by the month's
online capacity and clips at `_CF_MAX = 1.0`, which is why the 3.59 TWh extract move is a 27 GWh
move on the LP's wind upper bound:

| year | wind LP bound GWh (cf × cap), before → after | Δ | solar | verdict |
|---|---|---:|---|---|
| 2023 | 114,082.7166 → **114,055.2406** | **−27.4760** | 589.3480 → 589.3480 (0.0000) | **MOVED** |
| 2024 | 120,992.4611 → 120,992.4611 | +0.0000 | 1,198.6450 → 1,198.6450 | identical |
| 2025 | 122,255.2266 → 122,255.2266 | +0.0000 | 2,347.7450 → 2,347.7450 | identical |

**−27.476 GWh, the charter's "−27 GWh", confirmed to three decimals.**

### 2c. The FULL LP-input identity census — 27 arrays per year

Every array the `fleet_only` payload carries, SHA-256'd: `demand`, `mc_base`, `fuel_prices`,
`wind_cf`, `solar_cf`, `wind_cap`, `solar_cap`, `wind_mc`, `solar_mc`, `storage_power_cap` and every
`FleetArrays` numpy array.

| year | arrays checked | arrays MOVED |
|---|---:|---|
| 2023 | 27 | **`wind_cf` — and nothing else** |
| 2024 | 27 | **NONE — every array byte-identical** |
| 2025 | 27 | **NONE — every array byte-identical** |

The 2023 move is **one hour**:

| hour | zonal cf before → after | zonal MW before → after | Δ |
|---|---|---|---:|
| **h3907** | [0.925381, 0.993887] → [0.040995, 0.211678] | 31,604.9 → 4,128.9 | **−27,476.0 MWh** |

*(Clock note, reported not reconciled: the charter and FINDING-spp-40 §4 name this event
"index 3909" on the model's profile clock; SPP-41 names it h3907 on the 8760 UTC-sorted extract
clock. The `fleet_only` payload — the array the LP is bounded by — carries it at **h3907**, i.e. the
extract clock survives into the CF profile unshifted. The two-hour discrepancy is a clock-convention
statement in an earlier record, not a second event: exactly one hour moves in the whole year.)*

**This is the pre-solve half of promotion-rule leg (i).** No 2024 or 2025 LP input moves, so those
two years' P1 objectives are *predicted identical* to keeper-2's. If they are not, something other
than the seam moved and that is a STOP, not a finding to absorb.

## 3. G-DRIFT (rule 29(b)) — `git diff 33034499 HEAD` over the rule-29(b) file set

`src/market_sim scripts/run_calibration.py scripts/run_calibration_full.py scripts/lib
data/raw/_validation-source data/raw/reference` — 11 files, 9,341 insertions. **Every hunk
classified; the reason is cited, not asserted:**

| file | what changed | classification |
|---|---|---|
| `data/eia930/actuals.py` | the SPP-41 seam: `_screen_fuel_spike_columns` + its wiring into every reader | **LIVE — SPP 2023 ONLY.** INERT for 2024/2025 **by measurement**, §2a/§2c: zero moved arrays in either year |
| `pipeline/backcast_config.py` | `_SPP_OFFER_CURVE` extended to the five coal keys | **NOT DRIFT — keeper-2's OWN recipe change.** Its committed `run_config.json` already carries all five keys at 1.0/1.0/1.0/1.0 + `econ_low_share` 0.55, so it was in keeper-2's solve |
| `config/scenarios.py` | capx D76-ARM-B: `capacity_screen_peak_measured_hindcast` default `False → True` + a `__post_init__` coercion back to the frozen declaration when `not hindcast` | **INERT** — forecast-only path (a capacity screen a `mode="backcast"` run never enters), and this recipe is `mode=backcast, hindcast=False`, so the coercion restores `False` and `cache_key()` drops it. Corroborated by the committed epoch record: SPP's `*-plain-backcast` key `989da50bbf0f99d8` is measured **unmoved** by the arm |
| `config/constants.py` | CAISO 2022 nuclear monthly CF row | **INERT** — another ISO's branch |
| `config/fuel_trajectories.py` | CAISO 2022 CARB allowance price | **INERT** — another ISO's branch |
| `model/interchange/spec.py` | CAISO 2022 DSW depths + 2022 import tranches | **INERT** — another ISO's branch |
| `results/cache.py` | module-docstring cache-epoch ledger entry | **INERT** — documentation only; verified no executable line changed |
| `data/raw/_validation-source/caiso-supply-consistent-demand/*` | new CAISO 2022 demand csv + provenance | **INERT** — another ISO's artifact |
| `data/raw/_validation-source/actual_lmp_hourly_area_SPP.parquet` | SPP-57's LMP sidecar | **INERT** — a per-ISO artifact this recipe does not read: no `src/` or non-probe `scripts/` module references it, and `reference_price_interface=False` on this recipe |
| `data/raw/_validation-source/README.md` | one sidecar provenance row | **INERT** — documentation only |

**ALL HUNKS INERT EXCEPT THE ONE THIS LANE IS RE-BASELINING ⇒ rule 29(b) form 4 is VALID and
keeper-2's committed bundle IS the control. No control solve is spent.**

## 4. Rule 29(a) SCREEN — the year-scoped exemption, stated

Rule 29's own text: *"a year-scoped mechanism whose object only exists in one year … is the screen
and the full span at once."* The object here is **one artifact hour in one year** (§2c: 2023 h3907;
2024 and 2025 carry no moved LP input at all). A "screen on the year the footprint is largest" is
2023, and a 2024/2025 screen would be a byte-identical replay of keeper-2 by construction.
**So the screen and the full span are the same solve, and the full span is what runs.** Rule 16
`[R-ALLYEARS]` is met natively — one `--year 2023 2024 2025` invocation, one bundle, years
sequential.

This is an exemption from spending a *separate* screen, not from the screen's discipline: legs
(i)–(iii) of §5 below are exactly a structural STOP gate, they are declared before the solve, and
none of them reads the target residual.

## 5. THE PROMOTION RULE — declared here, before the solve

Promote `spp43_screened_B` to **keeper-3** iff **all four** hold:

- **(i) IDENTITY.** The **2024 and 2025 P1 objectives are IDENTICAL to keeper-2's** (`meta.json` /
  `metrics.json`). §2c predicts this: the seam moves no 2024/2025 input. **A difference is a STOP**
  — it names a hidden mover, and the lane reports the table instead of promoting.
- **(ii) 2023 MOVES ONLY WHERE WIND CAN MOVE IT.** Class deltas reported; coal/gas move only within
  what 27.476 GWh of removed wind headroom can displace, and wind/solar/nuclear/hydro move only as
  that headroom implies.
- **(iii) NO LOAD-BEARING CRITERION FLIPS PASS → FAIL** against keeper-2 in any year (C1, C2, C3a,
  C3b — and the protective C6/C8 stay PASS).
- **(iv) DOF LEDGER UNCHANGED** — 3 entries, 1 residual (the inherited `wefor_multiplier` 0.7),
  0 tuned scalars, `authorized_price_tuning` **NONE**. The seam adds no free parameter: it is a data
  screen with no `ScenarioConfig` field, no CLI flag and no cache-key term (rule 24).

**If (i)–(iv) all hold:** promote, re-key `keepers/SPP.json`, and **prune keeper-1 AND keeper-2** at
registration under rule 15's keeper-only retention (`scripts/prune_iso_runs.py --iso SPP`).

**If ANY leg fails or is ambiguous:** register the run (rule 15 — a run registers the moment it
finishes, keeper or not), **do NOT touch `keepers/SPP.json`**, and **STOP** with the table for the
desk to serve a card.

Note what this rule deliberately does NOT do: it never asks whether a residual improved. C1/C4-2023
wind is **SCORED for the first time** here, and whatever it reads is reported at full magnitude —
it is an outcome, not a gate. Removing an instrument artifact is a rule-14 `[R-ACCURATE]` /
rule-13 `[R-MEASURED]` obligation that stands whichever way the number moves.

## 6. Rules that bite, and how

| rule | how it binds here |
|---|---|
| 1 `[R-STRUCT]` | no band moves; the promotion rule is structural and never reads the target residual |
| 12 `[R-PARALLEL]` | years sequential in ONE invocation; no concurrent SPP solve (§0) |
| 13 `[R-MEASURED]` | the seam repairs a metering artifact in a measured input; it regenerates for any year and responds to conditions |
| 14 `[R-ACCURATE]` | the screened series is the accurate one and stays in whatever it does to the fit |
| 15 `[R-DASHBOARD]` | register in-session; prune, never archive; commit `hourly/` sidecars |
| 16 `[R-ALLYEARS]` | 2023+2024+2025, one invocation, one bundle |
| 20/21 | attestation + DOF ledger regenerated; `authorized_price_tuning` NONE |
| 22 `[R-HOLDOUT]` | 2023–2025 only. SPP holds **no** marker; no out-of-training year is solved, scored or registered |
| 25 `[R-ISO-SCOPE]` | nothing crosses an ISO boundary; only SPP files are touched |
| 27 `[R-PUSH]` | run payload over `git push`; every pushed file ≥300 lines fetch-back hash-verified |
| 28b `[R-MECH-MATRIX]` | **no mechanism is tested** — no cell verdict moves; the SPP shard gets the keeper + gates stamp only |
| 29 | (0) done above; (a) year-scoped exemption stated in §4; (b) form 4 valid by the G-DRIFT audit; (c) no screen or control bundle is produced, so nothing is owed for deletion |
| 30 `[R-TOUCHPOINT-FOLD]` | not engaged — no held-out year is solved |

## 7. Also owed by this lane (zero-LP, no fix applied)

- **R-15** (FINDING-spp-57 §8) — what `calibration_reference.json` carries for SPP 2025 hydro and
  which builder rule decides it; a proposed one-rule repair for the desk, **not applied**.
- **plant 6193** (FINDING-spp-36 §3.2) — is it in the EIA-860 SWPP fleet, and if not why the bench
  population carries 3.178 TWh of its 2023 coal; the crosswalk row stated.
- The "UNSCORED pending SPP-41" lines (log + FINDING-spp-40 §7.1 + FINDING-spp-42 §1: a one-line
  pointer appended, never a rewrite), and SPP-37 N-1 / N-2 (`docs/user-manual.md:646`,
  `market-sim-build-plan.md:11`).

**EXIT:** keeper-3 on `backcast-runs.html#iso=SPP` if the rule fires; otherwise the registered run
plus the STOP table. `FINDING-spp-43-2026-09-07.md` carries the identity check, the determination
table beside keeper-2's, the C1/C4-2023 wind score and the two zero-LP reports.
