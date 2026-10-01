# PREP — pjm-177 shard B, Phase 1 (ZERO-LP). Two input blockers found and one closed.

**Session** pjm-177-shardB · **ISO** PJM · **Date** 2026-09-09 · **Branch** `claude/focused-pasteur-jzys8p`
**No LP has been solved.** This note exists because the container is ephemeral (rule 31 `[R-RETAIN]`'s
surface-it-before-reclamation discipline) and because finding 2 below is **not** shard-B-specific.

---

## 1. Prep completed

| step | state |
|---|---|
| 12 G swapfile + `vm.swappiness=60` | active (`/swapfile`, 12 G, 0 B used) |
| `uv sync` | clean |
| `hydrate_data.py --profile pjm` | **no-op — this is a FULL clone**, every blob already local |
| `regenerate_clean.py transfer-interface-limits ramp-capability` | 7 + 3 partitions written; PJM 2020/2021/2022 transfer limits all present |
| `fetch_pjm_da_virtuals.py --years 2020 2021 2022 --feeds hrl_da_incs_decs` | **36/36 months** (12 per year), 15 MB, ~8 min |
| `.gitignore` for `results/calibration/pjm177b_*/` | committed + pushed |
| replay recipe resolves | 241 kwargs; `pjm_da_virtual_bids=True` confirmed |

**Governance re-verified by direct call, not by reading** (`enforce_holdout_year_gate`, ISO=PJM):
`[2020, 2021, 2022] --holdout-authorized` → **PASS** (validation tier, `complete` marker present);
the same years without the flag → refused; **2019 → REFUSED, 2026 → REFUSED** (both locked-test, under
the active freeze). PJM is absent from `final`. The locked tier is unreachable from this shard.

The arm's flag is wired on the replay path: `run_replay_bundle` carries an explicit
`netload_drag_min_run_persistence` override (`scripts/run_calibration_full.py`), so the A/B is the
keeper recipe plus exactly one field. `load_hourly_net_virtual_curve('PJM', y, 8760)` returns the
full `(8, 8760)` rung set for **2020, 2021 and 2022**.

---

## 2. BLOCKER 1 (CLOSED) — PJM 2020 could not be solved at all, and 2021 carried a corrupted peak

`data/clean/` in a fresh container holds **only** what this session regenerates, so before the repair:

- `load_demand_meta('PJM', 2020)` raised `ValueError: No EIA-930 data for ISO 'PJM' in year 2020`.
  2020 is a `PRE_WINDOW_YEARS` year (`curate_demand_profile.PRE_WINDOW_YEARS = (2019, 2020)`) and the
  legacy `eia_demand_profiles.parquet` starts at 2021. **The 2020 leg would have hard-failed.**
- **Every** PJM year 2021–2025 fell back to the legacy series the loader itself calls corrupted, and
  PJM **2021's `peak_mw` read 2,147,480,000 MW** — `2^31`, an int32 overflow sentinel, not a load.

Closed by `python scripts/regenerate_clean.py demand-profile` (49 partitions). This is **data
preparation, not a spend**: rule 22 as amended 2026-08-06 — *"what is held out is the SCORE, never the
DATA or the ARCHITECTURE"* — and `curate_pre_window`'s own docstring says so verbatim. It solves,
scores and registers nothing. After the repair `load_demand_meta` returns 2020 = 192,229 MW peak /
768.0 TWh and 2021 = 149,590 MW, and the corrupted-fallback warning is gone for every year.

**This is not shard-B-specific.** Any PJM session in a fresh container that runs
`regenerate_clean.py` with only the two datatypes named in the shard cards is dispatching 2021–2025
on the corrupted legacy series. Worth checking in the parent's container before its 2023 screen is
believed.

---

## 3. BLOCKER 2 (REPORTED, DELIBERATELY NOT FIXED) — 2 residual metering spikes in PJM 2020

PJM 2020 is the **only** year in 2019–2025 with any hour above 165 GW, and it has exactly **two**:

| year | peak MW | p99.99 | p99.9 | mean | TWh | hours > 165 GW |
|---|---|---|---|---|---|---|
| 2019 | 157,644 | 155,609 | 151,110 | 94,964 | 831.9 | 0 |
| **2020** | **197,438** | 183,776 | **148,785** | 92,419 | 809.6 | **2** |
| 2021 | 153,412 | 153,312 | 151,915 | 95,204 | 834.0 | 0 |
| 2022 | 152,376 | 151,692 | 147,488 | 96,114 | 842.0 | 0 |
| 2023 | 152,352 | 151,968 | 148,449 | 94,155 | 824.8 | 0 |
| 2024 | 156,367 | 156,122 | 151,970 | 96,526 | 845.6 | 0 |
| 2025 | 163,033 | 162,861 | 159,483 | 100,013 | 876.1 | 0 |

2020's **p99.9 (148,785 MW) is unremarkable** and its annual energy (809.6 TWh) is right; only the
extreme tail is wrong. Its peak sits **29 % above its own p99.9** where every other year sits within
4 %. The curation screen repairs hours above `2.5 × median` (≈212 GW), so a 197 GW spike survives it.

**Not fixed, on purpose.** Retuning that threshold to catch these two hours would mean choosing a
curation parameter **while looking at a holdout year** — precisely what rule 22 forbids
(*never identify, fit or tune any parameter against 2020/2021/2022*). The threshold is a shared
cross-ISO curation constant and belongs to a data lane with its own derivation, not to a touchpoint
session with 2020 in front of it.

**Why it cannot contaminate the A/B anyway, and where it could still bite:**
- It is **arm-invariant** — control and arm read the identical demand array, so the measured delta
  between the legs is untouched.
- It does **not** reach the capacity screen through capx D76: that seam is predicated on
  `config.hindcast`, and the keeper recipe sets neither `hindcast` nor `mode`
  (`ScenarioConfig.hindcast` defaults `False`; the D76 flag reads `False` under the non-hindcast
  `__post_init__` coercion). Verified by direct inspection of the resolved recipe, not assumed.
- What it *would* touch is any **2020 peak-derived reserve/adequacy number**. No such number is a
  gate on this card, and none should be quoted from the 2020 leg without this caveat.

---

## 4. State at the end of Phase 1

Prep is complete and **no solve has been started**. Awaiting the parent's explicit GO on the 2023
screen before either invocation is launched (rule 29 `[R-SCREEN]`: an arm does not reach a solve
until its gate passes).

Disk after the swapfile: **6.6 G free**; the keeper replay bundle is 6.5 MB, so bundle footprint is
not a constraint. `data/clean/` and `data/raw/pjm-da-virtuals/` are both gitignored and neither is
committed by anything here.
