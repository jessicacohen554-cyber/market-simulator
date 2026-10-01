# PRECOMMIT — pjm-h19: EIA-930 balance-identity demand repair (`demand_balance_screen`), all six PJM years (2026-09-23)

Card A of `docs/FINDING-pjm-h18-price-object-localised-2026-09-23.md` §5. Written and pushed
**before any solve**; the six shards are pinned to this commit's SHA.

**Keeper (control):** `2026-09-22-pjm-hydro2-ror-span` (2023–25, CALIBRATED) + folded
`2026-09-22-pjm-hydro2-ror-touchpoint` (2020–22, NOT-YET). Bundles
`results/calibration/hydro2_pjm_ror_{span,touchpoint}`, all six legs solved at `152c546a`.
**Rules:** 1 `[R-STRUCT]`, 14 `[R-ACCURATE]`, 16/34(c) all years, 28(c) matrix, 29(b) G-DRIFT,
31 `[R-RETAIN]`, 32 `[R-SHARD]`, 34 `[R-SHARD-PROMOTABLE]`, 36 `[R-YEAR-ISOLATION]`.

## 1. What this lane does

Adds one ISO-agnostic, **default-off** `ScenarioConfig` flag, `demand_balance_screen`, and
re-solves PJM's keeper recipe with **exactly one delta**, `--set demand_balance_screen=true`, on
every year PJM has registered — one shard per year, each pushing its full bundle. Parent composes,
scores, registers, and puts promotion to the owner.

It is a rule-14 source-data repair with **zero fitted parameters**: four EIA-930 `Demand`
readings in PJM's span are physically impossible, and the model serves two of them by shedding
28.2 GW and 13.5 GW at VOLL.

## 2. The bar — declared before the census, with its two pre-solve retirements disclosed

EIA-930 publishes, per BA-hour, `Demand`, `Net generation` and `Total interchange`. Served demand
is net generation minus net export, so **`S = NG − TI` is an independent measurement of the same
load**. At the four pjm-h18 hours `S` is smooth and `D` is not:

| year | hour | D (raw) | D neighbours | NG − TI |
|---|---|---|---|---|
| 2020 | 5003 (07-28 13:00) | 192,229 | 127,489 / 136,631 | 135,564 |
| 2020 | 5031 (07-29 17:00) | 176,085 | 139,527 / 141,853 | 141,358 |
| 2020 | 5383 (08-13 09:00) | 138,575 | 95,297 / 103,352 | 102,845 |
| 2024 | 7787 (11-21 12:00) | 56,260 | 94,812 / 95,482 | 96,156 |

**Disclosure.** The four target hours and their magnitudes were known from pjm-h18 before any bar
was written. The defence is not ignorance of them; it is that the bar uses a **published
convention** on each BA-year's **own** distribution, and that the census below lists every hour it
touches in every ISO-year on disk.

**Bar v3 (live).** Flag hour *t* iff both hold, and interpolate it like the sibling screens:

1. **Isolated reversal.** `s_in = D[t] − D[t−1]` and `s_out = D[t+1] − D[t]` have opposite signs and
   `min(|s_in|, |s_out|) > F`, where `F = Q3 + 3·IQR` of that BA-year's `|ΔD|` — Tukey's *far out*
   fence (Tukey 1977, *EDA* §2C), the published constant. Real load does not jump by an extreme
   hourly ramp and straight back.
2. **Demand carries the departure.** `|D − S|` at *t* exceeds `|D − S|` at both neighbours. A reading
   consistent with EIA-930's own balance identity is never blamed.

`F` for PJM 2020–2025 = 11,093 / 11,329 / 11,229 / 10,503 / 11,046 / 10,666 MW. The target
reversals are 35–65 GW.

**Retired before any solve, with reasons (the census did its job):**

- **v1** — Tukey fence on the de-trended residual `D − S` itself. **Degenerate**: EIA-930 balances
  *exactly* in most hours of most BA-years (IQR = 0), so the fence collapsed to [0, 0] and flagged
  28,307 hours. Retired for the scale, not for what it caught.
- **v2** — v3's leg 1, with leg 2 as "D's neighbour-curvature exceeds S's". Census found a
  **non-target false positive**: CAISO 2019 h1068 (D 24,977, S 24,476 — a *correct* reading flanked
  by two bad ones) was blamed because its bad neighbours inflate the curvature. Leg 2 was replaced
  by the direct residual comparison. The PJM targets were not consulted for this change and are
  flagged identically under v2 and v3.

## 3. Phase 0 census — ZERO LP, every ISO-year 2018–2025 on the ACTUAL loader output

`scripts/probes/pjm_h19_balance_screen_phase0.py` → `results/calibration/_pjm_h19_balance_screen_phase0.json`.
Runs the screen after the existing dropout and spike screens, exactly where `load_demand` applies it.

| ISO | flagged hours (v3) | justification |
|---|---|---|
| **PJM 2020** | **5003, 5031, 5383** | the pjm-h18 hours (§2 table). 2020's other reversals (h2374, 4649, 4906, 4984, 5895, all > 212 GW) are already repaired upstream by `_screen_demand_spikes` |
| **PJM 2024** | **7787** | the pjm-h18 dropout |
| PJM 2021, 2022, 2023, 2025 | none | — |
| PJM 2019 (not modeled) | 8031, 8296 | D 103.4 / 155.3 GW vs S 88.0 / 107.8 GW; 155 GW in December is above any PJM winter peak |
| CAISO 2019 (17 h) | alternating multi-hour clusters (Feb, Apr, May, Dec) | each flagged D departs S by ≥ 6 GW; the Dec cluster alternates with a stuck 27.2 GW value |
| CAISO 2020 | 6730 | D 13.8 GW vs 26.0 / 25.6 neighbours (S also glitched, 6.3 GW) |
| CAISO 2025 | 5076 | D 11.8 GW vs 29.9 / 29.9 neighbours, S 28.0 GW — **a CAISO training-year artifact, routed to the CAISO lane** |
| ERCOT, MISO, NYISO, NEISO, SPP, SOCO | none | — |
| NWPP | inert by construction | the pool frame defines `TI = NG − D` |

**Every flagged hour is a bad reading.** In PJM's modeled span the screen touches exactly the four
target hours. The flag is default-off and armed only for PJM in this lane, so no other ISO moves.

## 4. The population this mechanism CANNOT reach (named, not absorbed)

- **Artifacts EIA-930 also carried into NG or TI** (`D == S` in that hour). Measured: SWPP 2024 h4774
  (25.0 vs 37.2/33.0 GW), SWPP 2025 h4107 (1.5 vs 34.9/34.0 GW), SOCO 2025 h4889/5960/6274/7094/8363.
  Routed to those lanes; not in PJM.
- **Multi-hour artifacts** — leg 1 needs a clean neighbour on each side (CAISO 2019 is only partly reached).
- **The demand-profile fallback path** and NWPP.
- **In PJM, everything that is not a bad meter reading:** Winter Storm Elliott (pjm-h18 Card B,
  a real scarcity event), the CC-marginal +16–20 % overshoot and the CT_PEAKER shelf (Card C),
  2020's remaining ~+14 % C3a residual, and the D-4 coal conduct FAILs.

## 5. G-DRIFT, `152c546a` → HEAD (rule 29(b)) — zero LP

| commit | what | LP | scoring |
|---|---|---|---|
| `329e2026` | NWPP-47 `nwpp_grid_carried_wind_served` | INERT: default False, absent from the keeper; NWPP-only branch | INERT |
| `ad42fe43` | EIA-923 benchmark builder: dual-fuel oil re-attribution | INERT: post-LP benchmark only | **LIVE**: it changes the C1 benchmark |
| this lane | `demand_balance_screen` | the arm | — |

**LP form 4 is valid; the keeper bundles are the LP control.** Because `--rebuild-benchmark` is
mandatory on the composed arm (carried correction 3), the parent **also rebuilds the keeper's
benchmark at HEAD** (zero LP) and differences arm vs control on the **same** benchmark, so the
`ad42fe43` scoring move is never attributed to the arm.

**Built-in drift check (G0).** Four of the six years (2021, 2022, 2023, 2025) receive
byte-identical demand under the arm (census). Their legs are therefore **free same-HEAD controls**.

## 6. Gates — declared before any solve

Decided on structure (rule 1). A failed gate does not kill the arm; a passed gate does not promote it.

- **G0 drift.** 2021, 2022, 2023 and 2025 reproduce the keeper's committed dispatch: class TWh equal
  to 3 decimals and annual mean LMP within $0.01/MWh. A miss is a **LIVE-drift finding**, reported
  as such, never a verdict on the arm.
- **G1 liveness.** Served demand at 2020 h5003/5031/5383 and 2024 h7787 equals the neighbour
  interpolation (~132.1 / 140.7 / 99.3 / 95.1 GW), and **2020 VOLL slack at h5003 and h5031 is 0**
  (keeper: 28.2 and 13.5 GW).
- **G2 targeted statistic — predictions, stated now.**
  - 2020 **C3b 0.212 → ~0.15–0.16: FAIL → PASS** (bar 0.20).
  - 2020 **C3a +19.0 % → ~+14 %: STILL FAIL** (bar ±10 %).
  - 2024: price at h7787 rises from ~$20 toward its ~$33 neighbours; annual C3a moves < $0.01/MWh;
    **no status change**.
  - The touchpoint stays **NOT-YET** (C1, C3a 2020, C3a/C3b 2022 remain). The span stays **CALIBRATED**.
- **G3 no silent breakage.** Full rubric C1–C8 on all six years, reported at full magnitude vs the
  control on the same HEAD-rebuilt benchmark; D-1/D-2/D-4 diagnostics re-run once per bundle.

**Rule 1, restated before any number arrives.** The case for promotion is **structural**: the model
should not shed 41.7 GW of phantom load at $2,000 because of two bad meter readings. If G2's
predictions miss, the input stays correct and the miss is a root-cause question, not grounds to
revert.

## 7. Shards (rule 32 / 34 / 36)

Six, one per year, each pinned to this commit's full SHA. Each shard:

1. `git rev-parse HEAD` must equal the pinned SHA, else STOP.
2. `python3 scripts/hydrate_data.py --profile pjm`; `python3 scripts/regenerate_clean.py` (the full
   curation, ~30 min — hydro-2 §3.6 lost a shard to skipping it).
3. `python3 scripts/data/fetch_pjm_da_virtuals.py --years <y> --feeds hrl_da_incs_decs`.
4. `python3 scripts/data/curate_hydro_plant_modes.py --iso PJM` must report **57 run-of-river-class
   of 82**, else STOP.
5. Census self-check: `_screen_demand_balance` on `_load_pjm_hourly_demand(<y>)` must change
   exactly the hours in §3 for that year, else STOP.
6. `python3 scripts/replay_keeper.py <control> --years <y> --set demand_balance_screen=true
   --out-dir results/calibration/pjm_h19_dbs_<y> --note "pjm-h19 demand_balance_screen arm, <y>"`.
7. Commit the full bundle, `dispatch/<y>_P1.parquet` included, through a `.gitignore` negation and a
   plain `git add`; push to `claude/pjm-h19-dbs-<y>`.

| year | control bundle |
|---|---|
| 2020, 2021, 2022 | `results/calibration/hydro2_pjm_ror_touchpoint` |
| 2023, 2024, 2025 | `results/calibration/hydro2_pjm_ror_span` |

**Retrievability (rule 34(e)):** the parent fetches every leg, composes, and lands the registered
bundles on `main` before this lane's PR merges. Shard SHAs are provenance only.

## 8. Not in this lane

Card B (Elliott) needs an owner ruling. Card C (the CC/CT pair) is next, after this one. The D-4
coal conduct FAILs and SPP-71's `coal_sync_ensemble_level` stay open.
