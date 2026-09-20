# FINDING caiso-291 — the diagnostics' fleet rebuild cannot reach 64 of the keeper's own fields, and caiso-286's successor is now zero-LP

**Lane:** caiso-291 · **Date:** 2026-09-20 · **LP spent: ZERO** (rule 32 `[R-SHARD]` (a): the
parent never solves) · **Nothing armed, nothing registered, no `ScenarioConfig` field added, no
derive re-run, no mechanism cell moved** (rule 28 duty (b) is not owed — no mechanism was tested;
the caiso-284 precedent).

**Keeper unchanged.** On `main` at `83543f3c` the designated CAISO keeper is still
`2026-09-20-caiso-288-citygate-recovery`, and **three** CAISO runs are registered. See §5 — the
lane instruction's §1 describes a promotion that has not landed.

---

## 1. The answer in one paragraph

`scripts/legitimacy_diagnostics.py::_rebuild_fleet_arrays` reconstructs a bundle's fleet by
filtering `meta.json` through `run_year()`'s signature. **64 non-default fields of the CAISO
keeper's own recipe reach neither** — `meta.json` records only `run_year` kwargs, and these are
`ScenarioConfig` fields. The rebuild silently substitutes the dataclass default for every one,
**15 of them fleet-shaping**, and builds a **1,859-row fleet where the solve had 1,705**. Two of
the 64 (`historic_outage_overlay`, `correlated_forced_outage`) are `False` in the recipe and
`True` by default, so the rebuild also applies outage overlays the keeper disabled. Separately,
and independently useful: the artifact caiso-286 named as the blocker for splitting its open
270.3 MW — **P0 dispatch MW** — was landed for all four years by xiso-8, and its fleet is
**identical in unit_id order** to caiso-285's instrumented bundle, so that successor now costs
**no LP at all**.

---

## 2. The defect, measured

Source of truth: the real solve-time fleet in `results/calibration/caiso285_instr_2024/floors/2024_P1.npz`,
recovered from `203124e310f7be4f806ad968d6cf5755f96bbc00` (the SHA caiso-286 recorded).

| | |
|---|--:|
| `scenario_config` fields in the keeper recipe | 860 |
| unreachable by `meta.json` + `run_year()` | 569 |
| …of those, **NON-DEFAULT in this keeper** | **64** |
| …of those 64, **fleet-shaping** | **15** |
| solve fleet rows | **1,705** |
| rebuilt fleet rows | **1,859** |

The 15 fleet-shaping ones are why the row count moves — `plant_level_fleet`, `use_campd_bins`,
`cc_committed_per_plant`, `cc_peaking_per_plant`, `cc_duct_peaking`, `cc_outage_derate_from_top`,
`cc_capacity_reconcile_path`, `chp_steam_floor_p25`, `chp_steam_following`,
`measured_chp_heat_rates`, `caiso_ps_plant_params`, `gas_plant_monthly_fuel_pricing`,
`correlated_forced_outage`, `historic_outage_overlay`, `capacity_screen_peak_measured_hindcast`.
All True-in-recipe / False-by-default, except the last three, which invert.

**What it costs, bounded rather than asserted** (rebuilt vs real `pmax`, joined by unit_id):

| row set | n | rows differing | max \|Δ pmax\| |
|---|--:|--:|--:|
| **`CC_REGULAR`** | **285** | **0** | **0.000000 MW** |
| all mapped rows | 1,641 | 104 | 1,803.33 MW |
| bridge-scope rows unmapped | — | **0** | — |

So the damage is **real but class-dependent**: the CC fleet that carries the belly object rebuilds
**exactly**, while 104 rows — CHP and raw per-plant units the rebuild fails to bin — do not.

**Liveness, stated honestly.** This bundle's committed `legitimacy_diagnostics.json` is **sound**:
its `dispatch_source` is the real `dispatch/<y>_P1.parquet`, and its D-2 rows carry
`ra_mustoffer_bridge` attribution, which a rebuild cannot produce (the rebuild returns static
`fa.min_gen`; the RA bridge is applied at the P0→P1 seam). Both facts mean real `floors/*.npz`
were on disk when it was generated. **The defect is latent for the committed artifact and live for
any regeneration from it** — and the committed bundle carries no `floors/` directory, so a later
session that re-runs the diagnostics *will* hit the rebuild path. That matters because rule 19
`[R-FORCED-BUDGET]` promises D-1/D-2/D-4 are "scorer-only … existing keepers re-score in place";
for CAISO, a re-score from the committed bundle does not reproduce the fleet it is scoring.

**Two claims I tested and withdrew, recorded so they are not repeated.** (i) I first read the
`meta.json` omission as corrupting the committed D-2 `ra_mustoffer_bridge` rows. It does not —
caiso-155 already excludes the whole P0-run-pattern bridge family from rebuild comparisons
(`legitimacy_diagnostics.py` ~L2155). (ii) I measured a meta-driven bridge floor of 4.4302 TWh
against the recipe's 0.8728 TWh and nearly reported a 5.08× overstatement. **No code path executes
that comparison** — `load_or_rebuild_floors` never calls the detector. The number is real and the
inference was wrong.

**Not repaired here.** The fix is one line in intent — read `run_config.json`'s `scenario_config`,
which every bundle already commits and which *is* the authoritative recipe, rather than
`meta.json` — but it re-scores D-1/D-2/D-4 for **every ISO**, and a gate can flip. That is an
owner call, not a lane call (§5).

---

## 3. The candidacy census — caiso-285's 2024 measurement, extended to all four years

Probe: `scripts/probes/caiso291_bridge_candidacy_census.py`; artifact
`results/calibration/_caiso291_bridge_census.json`. It replays
`caiso_ra_mustoffer_min_gen`'s candidacy loop over the keeper's **committed** P0 and ends by
asserting its own run census equals the shipped function's `screen_stats`. **All four years
reproduce exactly**, so the census is the mechanism and not a paraphrase.

**Validated against caiso-285's instrumented probe**, which is the better-grounded measurement:
population **74 scoped / 30 econ-eligible — exact match**; belly mean net load 1890.42 vs
1889.95 MW; `CC_REGULAR` pmax exact on all 285 rows.

### The startup-aware run screen, four years

| year | runs detected | kept | dropped | **drop rate** |
|---|--:|--:|--:|--:|
| 2022 | 24,006 | 8,426 | 15,580 | **64.9 %** |
| 2023 | 19,088 | 4,522 | 14,566 | **76.3 %** |
| 2024 | 22,455 | 2,462 | 19,993 | **89.0 %** |
| 2025 | 18,760 | 1,320 | 17,440 | **93.0 %** |

**Materially above the 42–60 % caiso-287 §5 recorded, and rising monotonically across the window.**
In 2025 the screen keeps 1,320 of 18,760 detected runs.

### What the screen does downstream — belly gap length, armed vs screen forced off

The counterfactual is **diagnostic only**; nothing is armed or disarmed.

| year | armed p50 | armed >24 h | armed gaps | ‖ | screen-off p50 | screen-off >24 h | screen-off gaps |
|---|--:|--:|--:|---|--:|--:|--:|
| 2022 | 19 h | 32.9 % | 2,880 | | 20 h | 13.4 % | 7,742 |
| 2023 | 12 h | 32.2 % | 1,821 | | 15 h | 13.6 % | 7,197 |
| 2024 | **149 h** | **73.2 %** | 557 | | 15 h | 24.0 % | 6,972 |
| 2025 | 15 h | 48.4 % | 767 | | 13 h | 23.2 % | 7,167 |

The underlying P0 idle structure is **stable year to year** (screen-off gaps ≈ 7,000 in every
year). The armed picture is not. Dropping a run **merges** its two neighbouring gaps
(`runs` is rebound to `kept_runs`), so the survivors are fewer and longer — and the day-ahead
horizon cap then declines to bridge them, correctly: a unit idle 149 hours **is** decommitted, and
holding it at min-load for six days is not a thing CAISO does.

**So the DA cap is the proximate filter and not the defect.** I explicitly do **not** claim it is
the dominant one: my hour-weighted metric makes it look like 45.7–84.0 % of foregone belly floor,
but that is partly definitional — the cap selects on gap length and the metric weights by gap
length. **caiso-285's exhaustive MW-conserving partition is the better number and puts the DA cap
(S2) at 302.095 MW, 11.1 % of the belly deficit.** Where this lane adds, it adds upstream: the
screen's severity, and its mechanical route into the cap.

---

## 4. caiso-286's successor is now free

caiso-286 left one question open and costed it at *"an instrumented replay persisting P0 dispatch
MW … one year one shard"*: of the 1,593.4 MW in bucket S3_5, **270.3 mean-belly-MW passes the
restart inequality on the per-gap basis yet is floored by nothing** — removed by either the
surplus decommit screen or the startup-aware gap-merging channel, and it did not have the artifact
to split them.

**That artifact now exists and is committed.** xiso-8 landed `hourly/p0_dispatch_<y>.parquet` for
2022–2025, and I verified the two bundles share a fleet: caiso-285's `floors/2024_P1.npz`
`unit_ids` and xiso-8's `p0_dispatch_2024` `unit_id` column are **identical in order**, 1,705 rows.
The split is a parent-side file operation.

**One caveat that decides how it must be done.** Candidacy is availability-free — runs key on
`p0 > pmax × 0.05` and the inequality on `mc_base`, `p0_prices`, `pmax`, `frac`, `gap` — and `pmax`
rebuilds exactly for `CC_REGULAR`. But `mc_base` and `availability` come from the rebuild, and §2
is precisely why they are wrong (the rebuild re-enables `historic_outage_overlay` and
`correlated_forced_outage`, which the keeper disables — the mechanical cause of the 646,108
`p0 > pmax × availability` cells my replay flagged). **So the split should be run against the real
floors, not a rebuilt fleet** — either from a recovered instrumented bundle, or after §2 is fixed.
Quoting a split off a rebuilt `mc_base` would be a number I could not stand behind.

---

## 5. Open, and NOT this lane's to decide

1. **The lane instruction's §1 is wrong on a load-bearing fact.** It states keeper
   `2026-09-20-caiso-290-leftedge` "promoted 2026-09-20 by xiso-8" and "CAISO now has exactly ONE
   registered run (3 → 1)". At `origin/main` `83543f3c` the keeper shard reads
   `2026-09-20-caiso-288-citygate-recovery` and three CAISO runs are registered. xiso-8's own
   RESULT §7 says **"PROMOTION: NOT TAKEN — the owner's call, and it is open."** That promotion
   question is still open; I have not touched it.
2. **The `meta.json` → `run_config.json` rebuild fix** (§2). Correct in isolation, cross-ISO in
   blast radius. Owner call.
3. **`caiso_ra_bridge_startup_aware`** stays exactly where caiso-287 §5 put it — an admissibility
   question in owner court, unruled. This lane **did not** disarm it and **does not** decide it;
   §3 is evidence for that decision, not a verdict on it. The new evidence is that its drop rate
   is 64.9 → 93.0 % and rising, not the 42–60 % on the record.

**Nothing was solved, so rule 31 `[R-RETAIN]` has nothing to protect**; the recovered
`caiso285_instr_2024` files are a read-only checkout from git history and are left in place.
