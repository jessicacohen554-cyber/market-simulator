# ADDENDUM — nwpp-44: the first shard wave was INVALID. `--hydro-backfill-year` was missing.

**Lane:** NWPP-44 · **Date:** 2026-09-20 · Parent of `PRECOMMIT-nwpp-44-2026-09-20.md`
**Status:** first wave DISCARDED before it reached any verdict. Second wave relaunched.
**LP spent by the parent: still ZERO** (rule 32(a)). Cost of the error: three shard
containers, ~10 min each, no verdict.

---

## 1. What happened

The first shard wave (pinned `17943d2c`) was launched with a CLI I reconstructed by
hand from the keeper's `calibration_flags` TRUE booleans plus a `ScenarioConfig`
diff. **That reconstruction was incomplete.** `hydro_backfill_year` is a
*loader argument*, not a `ScenarioConfig` field, so it appears in neither surface I
diffed — it lives only in the bundle's `meta.json`. The keeper carries
`hydro_backfill_year: 2024`; my shards passed nothing, which is `None`.

Only the 2025 leg finished before the wave was stopped. It is the evidence.

## 2. The measured consequence — 38 TWh of hydro that never existed

| | keeper 2025 | arm leg 2025 (invalid) | Δ |
|---|---|---|---|
| hydro | 113.077 TWh | 74.936 TWh | **−38.141** |
| COAL_BIT | 6.942 | 16.655 | +9.713 |
| COAL_PRB | 21.310 | 25.447 | +4.137 |
| CC_REGULAR | 58.960 | 68.746 | +9.786 |
| CT_PEAKER | 8.352 | 17.921 | +9.569 |
| ST_GAS | 0.284 | 3.010 | +2.727 |
| **slack (unserved)** | **0.000 MWh** | **1,330,908.764 MWh** | **+1.33 TWh** |
| price (annual sum over zones) | 1,333,733 | 27,524,048 | **20.6×** |

The loader's own log line names the cause exactly. In a container that passes the
flag:

```
NWPP 2025 hydro budget: backfilled 255 non-reporting plants (38219.0 GWh) from 2024
Loaded NWPP 2025 hydro budget: 280 plants, 113155.5 GWh annual, 35695 MW nameplate
```

**38,219 GWh backfilled against a 38,141 GWh shortfall.** Without the flag, 255 of
NWPP's 280 hydro plants — the ones that had not filed 2025 EIA-923 at this vintage —
carry no energy budget at all.

## 3. Why this was certainly NOT the arm, on LP logic rather than forensics

**Adding cheap supply to a feasible LP can never create unserved energy.** The arm
makes 13 coal rows *cheaper* and changes nothing else (the recipe diff below is
exactly two booleans). The keeper served all 288.7 TWh with `slack = 0`. If the same
fleet on the same inputs with 13 rows cheaper cannot serve demand, then the fleet or
the inputs are not the same. The arm cannot be the cause.

Three corroborations, in increasing order of specificity:

1. **Hydro is lower in ALL 8,760 hours and higher in none** (max −20.5 %, min
   3,691.6 → 0.0 MW). Economic displacement *reschedules* an energy-limited
   resource — it shows up higher somewhere. Strictly-lower-everywhere is a
   capability cut.
2. **The cascade inputs are byte-equal**: `spill_kcfs` differs by 0.062 out of
   650,340, and `plant_code` / `hour` / `year` are identical. Only the duals moved.
   So the defect is in the *budget*, not the cascade.
3. **The full `meta.json` diff has exactly one substantive entry**:
   `hydro_backfill_year` keeper `2024` vs arm `None`. Everything else is
   `git_sha`, `years`, `timestamp`, `composed_from`, `highspy_version`.

And the `scenario_config` diff is clean — the leg differs from the keeper in
**exactly the two armed booleans** plus two default-`False` fields added to `main`
since the keeper (`benchmark_membership_vintage_union`,
`caiso_citygate_blackout_bridge`), both absent from the keeper's recipe and inert.
So the *config* was right; the *loader argument* was not.

## 4. The trap, named so the next lane does not fall in it

**A keeper's recipe is NOT fully described by its `ScenarioConfig`.** Reconstructing
a CLI from `run_config.json` alone silently drops every loader-level kwarg. The
authoritative surface is the bundle's **`meta.json`**, which is what
`replay_keeper.run_year_kwargs()` reads — and which is why the parent's own zero-LP
probe (§5 of the PRECOMMIT) was *correct* while the shard CLI was not: the probe
replays `meta.json`, the shard re-derived flags by hand.

**The rule for a successor: diff `meta.json`, not just `scenario_config`, and do it
BEFORE launching. Better still, have the shard replay the keeper's `meta.json`
rather than hand-build a CLI.**

This one is especially easy to miss because it is **silent**: no error, no warning,
a plausible-looking bundle, and a coal number that lands *on* the EIA actual
(42.269 vs 42.26 TWh). The first shard reported that as success. It was not success
— it was 38 TWh of missing hydro being replaced by thermal, including 9.6 TWh of
*peakers*, which no cheap-coal mechanism could ever produce.

## 5. What the second wave changes

One flag, `--hydro-backfill-year 2024`, matching the keeper. Nothing else; the code
at `17943d2c` is unchanged and the arm is untouched.

New self-checks in every shard prompt, each of which would have caught this:

| check | expected |
|---|---|
| the loader's backfill log line | `backfilled … (38219.0 GWh) from 2024` (2025; non-zero in every year) |
| hydro annual energy | 2023 ≈ 106.9 · 2024 ≈ 107.9 · 2025 ≈ 113.1 TWh |
| `system_<y>.parquet` slack | 2023 ≈ 4,222 · 2024 ≈ 8,818 · 2025 = 0 MWh — **not** 1.33 M |
| `meta.json` `hydro_backfill_year` | `2024` |

## 6. Carried

* The invalid 2025 bundle is **kept on local disk and on its shard branch**
  (rule 31 `[R-RETAIN]` — not deleted). It is the evidence for this addendum. It
  must never be composed or registered.
* **`highspy` 1.15.1 here vs 1.14.0 in the keeper.** Noted, not adjusted: it is the
  container's pinned build and this lane cannot pin the keeper's. It is a candidate
  explanation for any small residual difference that survives the re-solve, and the
  second wave should report its own version so the record is explicit.
* The keeper itself carries non-zero slack in 2023 (4,221.7 MWh) and 2024
  (8,818.0 MWh). Small — 0.0016 % and 0.0032 % of demand — but non-zero, and this
  lane did not introduce it. Reported, not absorbed.
