# FINDING — capx T3-NEISO-GOLDEN: the program's first §2.1b full-horizon campaign (NEISO 2026–2050 T3 BAU golden)

**Session:** T3-NEISO-GOLDEN (capacity-expansion / Forecast Finalization track), branch
`claude/capx-t3-neiso-golden-74sq45`, lane issued at the director's r#17 sitting
(`capx-director-ledger-2026-08.md` §0j lane table + §3 Q13).
**Date:** 2026-08-30 · **HEAD at launch:** `bd97c6eb` (origin/main).
**Status:** §§1–4 are the PRE-DECLARATION — written and committed BEFORE any solve was
launched (rules 13/21 discipline; S-4b §4 / S-4V §5.1 are the model cases). §§5–8 carry the
measured record and were written after.

---

## 1. The authorization (leg (d), cited verbatim)

This campaign executes the **FIRST full-solve authorization ever granted under the §2.1b
gate** (`docs/forecast-development-plan-2026-07.md` §2.1b — the "10-hour rule"). The
authorization, owner ruling Q13, capx r#17 sitting 2026-08-30, recorded in
`docs/handoffs/capx-director-ledger-2026-08.md` §3:

> **Q13** — NEISO §2.1b leg (d): first-ever full-solve authorization, presented on S-4b's
> measured result per Q11 — **RULED 2026-08-30 (r#17 sitting) — AUTHORIZED: the T3 BAU
> GOLDEN, NEISO, 2026–2050, budget ~1.0 h / ~4.3 GB (FF-3E), THIS CAMPAIGN ONLY.** The
> first §2.1b gate opening in program history. Caveats carried verbatim into the campaign
> record (floor-dependent 2028/29 I7; D14 exit-composition recall 2/6; FC-7 DOF gap); a
> gate-condition regression re-closes. Execution = lane T3-NEISO-GOLDEN (prompt in the
> pack).

Scope discipline: ISO=NEISO, window=2026–2050 T3 BAU golden, budget ~1.0 h wall /
~4.3 GB RSS (the FF-3E projected table, `docs/handoffs/ff-poc-closeout-2026-07.md` §
"projected full-horizon" row: NEISO 78 s median/yr → **0.95 h**, **4.3 GB**, pairable) —
**THIS CAMPAIGN ONLY**: no standing authorization, and any gate-condition regression
re-closes the gate (charter §2.1b(2)(d)). `--full-solve-authorized` is the FF-3E
schedulability guard for >5 solve-years; it is licensed by the Q13 authorization above and
by nothing else.

## 2. Gate-condition verification at launch (all four legs, read live at `bd97c6eb`)

- **(a) Backcast calibration proof — PASS, re-read live this session:**
  `frontend/data/backcast/calibration-complete.json` `complete` block = {NEISO, PJM};
  NEISO entry keys keeper `2026-08-17-neiso-99-joint-p1` (full-span 2023–2025, rule 16),
  determination CALIBRATED. `final` block empty (never required for forecast work). The
  holdout spend freeze (`holdout-freeze.json`) is TIER-SCOPED to the locked test and its
  `not_frozen` list names "forecast-mode runs spanning 2026+" explicitly — orthogonal to
  this campaign, as charter §2.1b(2)(a) states.
- **(b) POC gates green — PASS:** bare `neiso-t1f` = PROMOTE-WITH-CAVEATS, re-scored
  2026-08-30 by capx-S4b (scored at `88baa9d5c71b`, cache `9a7f68fc7dcac931`): FC-1 PASS
  (all 14 invariants), FC-2 PASS, FC-7 CAVEAT (program-wide DOF gap), FC-8 PASS.
  `FINDING-capx-s4b-neiso-ara-2026-08-30.md` §5.4.
- **(c) Worth-the-compute evidence — PASS:** FF-3E readiness battery green + NEISO's
  first-ever T1-X crossover `neiso-2023-2027-crossover-capxd14` measured FC-4 and reported
  it at FULL MAGNITUDE (lane D14, verdict key `neiso-t1x`, determination HOLD).
- **(d) Owner authorization — the Q13 ruling quoted in §1.**

**Heavy-slot check at launch (charter co-run discipline):** `git ls-remote --heads origin`
shows four in-flight branches — `claude/caiso-backcast-next-run-5u7ob7`,
`claude/capx-d12c-confirm-pair-oji8wv`, `claude/ci-parity-caiso224-bundles-xfpsek`,
`claude/nyiso-161-backcast-calibration-dikoy3`. **No S-6 PJM ledger run and no MISO heavy
solve is in flight** (S-123 merged as #4398 without a solve; S-6 remains
RELEASED-CONDITIONAL on CAISO-224-FIN per Q14, not launched). The ~4.3 GB NEISO leg
therefore launches solo in its own container with no PJM (8.8 GB) / MISO (9.6 GB)
no-co-run conflict. D12-C is mid-execution and may touch adjacent board blocks — rebase
care noted for the registration/board commits.

## 3. PRE-DECLARED run construction, budget, and expectations

**The run — zero config invention, HEAD defaults at golden posture (exactly the S-4b
treatment construction, extended to the authorized window):**

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  uv run python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2050 \
  --golden-posture --full-solve-authorized --out-dir results/ff-t3-neiso-golden/bau
```

- `mode="forecast"`, every `ScenarioConfig` field at its shipped default; golden posture
  resolves the per-ISO capacity-clearing gate through the ONE reader
  (`scripts.lib.forecast_posture.shipped_capacity_clearing_by_iso` — NEISO curve-ON per
  FF-2C), `forecast_xyear_warmstart` OFF per owner D-10. No flag beyond the two the
  charter names; no new mechanism, no `ScenarioConfig` field, no matrix duty.
- Years run SEQUENTIALLY within the invocation (rule 12) — the year loop is never
  parallelized. Container: 15 GB RAM / 4 CPU; `data/clean` was absent (fresh container)
  and is being rebuilt in full before launch (the §2.4 prerequisite; build time reported
  in §5 alongside the solve budget, per the "budget it into the FIRST leg" rule).
- **Expected cost (pre-declared):** ~1.0 h wall / ~4.3 GB peak RSS (FF-3E projection:
  0.95 h / 4.3 GB). Measured-vs-projected is reported in §5 whatever it reads. The S-4b
  anchor for the first five years: 8.0 min / 3.17 GB.
- **Checkpoint discipline:** the runner writes `evolution_<year>.json` beside each year's
  cached result as the horizon progresses (`results/evolution_ledger.py`); per-year
  evolution artifacts are committed as checkpoints mid-horizon (the T1-F pattern), so a
  mid-horizon failure preserves the record. **If the solve breaks mid-horizon, the failure
  record IS the deliverable — reported at full magnitude; a partial run is never
  registered as complete.**
- **Requirement bar carried into the campaign** (the CURRENT bar, S-4b intake, all values
  ISO-NE's own ARA-3 prints): DR-netted requirement factor **1.0286103**
  (`PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]` 0.12766 net of
  `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]` 0.08784), firm external-tie credit
  **409.31 MW**. Nothing in this campaign re-derives or re-tunes any of it.

**Pre-declared expectations (recorded before the solve):**

1. **2026–2030 head-of-horizon reproduction.** The first five years of this window run the
   exact S-4b treatment construction (same HEAD defaults, same golden posture, same
   requirement bar), so the 2026–2030 trajectory — peaks, firm capacity, I7 margins, the
   2027 gas-CC exit wave at 2,231.8 MW, 2029 wind 712.6 + solar 1,089.4, 2030 economic
   gas-CC 1,000 MW + wind + solar — should REPRODUCE the S-4b treatment ledger
   (`FINDING-capx-s4b-neiso-ara-2026-08-30.md` §5.1) to numerical noise. The cache key
   will differ (the window is part of the key); no per-year mechanism reads `end_year`
   forward, so a divergence in the overlap years would surface an end-year coupling —
   reported as a finding and an attribution question, never adjusted away.
2. **Out-year behavior (2031+) is REPORTED, never judged and never back-tuned.** No
   actuals exist for any year in the window; nothing is scored against measured outcomes
   (rule 13), no result feeds back into any input, and no value is reverse-engineered to
   clear an invariant (rule 21). The horizon record reports the fleet-evolution
   trajectory, entry/exit waves, price/reserve-margin paths at reporting grain, and the
   I1–I14 invariant sweep — at whatever magnitude they land.
3. **Verdict construction (declared in advance):** after the solve,
   `forecast_verdict.py --tier t3` is scored from committed artifacts only — the bundle's
   `full_horizon_summary.json` + `run_config.json`, the committed T1-H capacity-hindcast
   score, and the committed D14 T1-X crossover score
   (`results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json`).
   **Expected determination: HOLD** — FC-4 carries D14's committed FAIL at full magnitude
   (a carried caveat of this campaign, §4(ii)), FC-7 carries the program-wide DOF gap, and
   the T3 golden attestation instruments (FC-5 corridor / FC-6 driver battery) are not yet
   built for NEISO, so their REQUIRED rows will read SKIPPED. That is the honest reading:
   **the Q13 authorization licensed the compute, not a promotion claim.** A T3 HOLD with a
   complete horizon record is the expected deliverable, and no instrument is invented
   mid-campaign to move it.
4. **Verdict key:** `neiso-t3` — verified ABSENT from
   `frontend/data/forecast/ff-verdicts.json` at launch (no t3 key of any ISO exists), so
   this is a new key: nothing is displaced, nothing to preserve-then-overwrite.

## 4. The carried caveats (verbatim, per the Q13 ruling — nothing re-tuned)

The campaign record carries these three caveats WITHOUT re-tuning anything:

**(i) The 2028/2029 I7 margins are floor-dependent** (+419.0 / +333.6 MW riding on the
699.3 MW retention response). S-4b §5.3, quoted verbatim:

> - The 2028/2029 clearances (+419.0 / +333.6 MW) are **floor-dependent**: without the
>   retention response the arithmetic lands at −280/−366. The floor is a standing
>   structural mechanism (spec §5.2, one-requirement-two-verbs), measured here against
>   a zero-drift control, its retained units named — not a tuned input. But a reader
>   should know the sign of these two years now rides on the floor's response, exactly
>   as it previously rode on epoch drift (S-4V §5.4) — each successive measurement has
>   moved the margin down (+545 → +419, +469 → +334).
> - §4's suspicion clause ("a result landing just clear is the suspicious one") is
>   answered by the attribution closing to 0.1 MW with a named, symmetric mechanism —
>   the same floor S-4V measured in the loosening direction (324.9 MW) responds here
>   in the tightening direction (699.3 MW). Nothing was re-tuned; the sourced 0.7352
>   hydro factor was not touched; every input value is the filing's/CELT's own print.

**(ii) D14's retirement-composition miss — out-year fleet composition inherits this known
defect, and this record SAYS SO.** The crossover window measured exit recall **2/6**
reachable ≥300 MW targets (`FINDING-capx-d14-neiso-t1x-2026-08-30.md` §2): retirements
model 3.563 GW vs actual 4.997 GW (−28.7 %); the economic screen concentrates the exit
wave in gas (gas_cc +66 % over, 3.128 vs 1.884 GW) and misses the biomass/coal/gas_ct/oil
exits entirely (0.0 vs 0.262/0.846/0.319/1.208 GW). Every 2027+ exit wave this campaign
reports is composed by the same screen; the 25-year fleet composition therefore inherits
a demonstrated gas-concentration bias, and every out-year composition statement in §5–§6
must be read with it.

**(iii) FC-7 — the program-wide DOF-ledger gap.** No committed
`dof_ledger.json` instrument exists for any T1-F/T3 leg (the lane-D8
`build_forecast_dof_ledger.py` gap); FC-7 reads CAVEAT on every leg in the program and
will here too. Program-wide instrument debt, not NEISO-specific, carried as-is.

---

*(Sections below were written AFTER the solve; §§1–4 above were committed before launch.)*

> **Execution note (r#20 relaunch, 2026-08-31).** The dispatched session was lost mid-solve;
> §§1–4 above had already landed (PR #4405) and are the binding pre-declaration, unchanged.
> This session executed them. **HEAD at launch: `9e56f0f`** (not §1's `bd97c6eb` — the
> relaunch rebased onto current main first; the epoch consequence is measured in §5.1).
> Container prerequisite: `data/clean` was absent and was rebuilt in full first —
> 51/51 datatypes, 0 tracebacks, 0 OOM, 1.5 GB, ~30 min wall (00:17:40→00:47:53Z),
> per §3's "budget it into the FIRST leg" clause.

## 5. Measured cost vs projected

**The run completed: 25/25 years, `error: None`.** Launched 02:48:50Z, summary written
03:18Z.

| axis | §3 pre-declared | measured | reading |
|---|---|---|---|
| wall clock | ~1.0 h (FF-3E 0.95 h) | **29.2 min (0.487 h)** | **49 % of budget** |
| peak RSS | ~4.3 GB | **3.50 GB** | **81 % of budget** |
| solve years | 25, sequential | 25/25, sequential (rule 12) | as declared |
| cache epoch | `a4b11ef4aaa1be35` *(predicted ex ante, pre-launch)* | `a4b11ef4aaa1be35` on disk | **exact** |

Per-year: median 68.7 s, min 57.4 s, max 122.7 s (the 2026 base year, which carries fleet
build). The FF-3E projection was **conservative by ~2×** on wall clock — reported as a
projection-quality datum, not a claim about the model.

The cache key was resolved and **declared before launch**, then confirmed against the
on-disk solved key (the D14 resolved-preflight discipline). Gate re-verification at launch
was re-run live and all four legs held as §2 recorded them.

### 5.1 Epoch integrity — measured twice, and the second measurement is a finding

**(a) Across the 38 commits between §1's `bd97c6eb`-era base and the launch HEAD `9e56f0f`
— ZERO DRIFT.** The resolved NEISO 2026–2030 golden-posture key still reproduces S-4b's
committed `9a7f68fc7dcac931` exactly, so the D12-A ERCOT arming, C-1 joint wind and the
MISO/NYISO/CAISO lanes left NEISO's forecast config untouched — rule 25 `[R-ISO-SCOPE]`
holding, verified rather than assumed. *(A first pass of this check appeared to show drift;
it was comparing a pre-resolution `reference_config()` against a post-resolution
`run_config.json`. ISO defaults apply at solve time — `runner.py:1185`,
`apply_iso_scenario_defaults` — so the correct comparison is on the resolved config. Recorded
because the staging error is an easy one to repeat.)*

**(b) Mid-solve, owner ruling R-A landed on main and it bears on this bundle.** Commit
`ecf9972` flipped **`storage_entry_availability_gate`** and
**`storage_entry_cost_normalized_rank`** `False → True` as shipped `ScenarioConfig`
defaults (every ISO's forecast lane). **HEAD was deliberately NOT moved under the running
solve** — a 25-year golden spanning two HEADs has no citable epoch — so this campaign
solved the pre-R-A shipped posture, and the committed `run_config.json` records both fields
at **`False`**.

The consequence is *not* a moved key, and that is the point:

- Both fields are registered in `_CACHE_KEY_OPTIONAL_FIELDS`, which drops a field that
  equals the **live** default. Their default moved, so the post-flip armed posture and this
  run's pre-flip unarmed posture **hash identically**. The NEISO 2026–2050 resolved key at
  current HEAD is still `a4b11ef4aaa1be35`. This is exactly the FFR-3A **blocker-4 silent
  same-key invalidation**, which `scenarios.py` predicted "will silently recur on the next
  default flip".
- The R-A commit **declared it correctly**: `check_cache_key_registration.py` passes
  (218/218 declared defaults match HEAD) and `results/cache.py` carries an
  **Epoch 2026-08-31** entry reading *"INVALIDATED — purge or re-solve before quoting: any
  `results/<ISO>/<key>/` FORECAST-lane bundle solved before this epoch at the shipped
  (unarmed) default."* The guard worked; nothing was hidden.

**Exposure, bounded precisely.** `run_full_horizon` redirects the cache root to `--out-dir`,
so this bundle lives at `results/ff-t3-neiso-golden/bau/NEISO/a4b11ef4aaa1be35/` and **not**
in the shared `results/<ISO>/<key>/` root the notice names — so the *silent-reuse* half of
the hazard does not reach it. What DOES apply is **scenario-identity ambiguity**: at current
HEAD the key `a4b11ef4aaa1be35` denotes the ARMED posture while this bundle holds the
UNARMED solve. **The key alone therefore no longer identifies this run's posture** — cite
`solved_at_sha 9e56f0f` plus the committed `run_config.json` field values.

**Why this is materially significant here rather than bookkeeping (§6.3):** this golden
builds **zero storage in all 25 years**, and R-A armed precisely the two storage-*entry*
mechanisms. The armed posture is the one most likely to move this run's single most striking
structural result. **Routed to the owner/director as a decision, not taken here:** re-solving
under the armed posture is a SECOND campaign, which the Q13 authorization ("this campaign
only") does not cover. This lane does not request it and cannot grant it.

## 6. The horizon record (2026–2050) — reported, never judged, never back-tuned

No actuals exist for any year in this window. Nothing below is scored against a measured
outcome, no result feeds back into any input, and no value was reverse-engineered to clear an
invariant (rules 13/21).

### 6.1 Head-of-horizon reproduction — pre-declared expectation #1, CONFIRMED EXACTLY

§3(1) predicted the first five years would reproduce the S-4b treatment ledger "to numerical
noise" and named a divergence as an end-year-coupling finding. Measured, the reproduction is
**bit-for-bit**:

| year | peak MW (golden / S-4b) | reserve margin | load-wtd price | Δ |
|---|---|---|---|---|
| 2026 | 24,889.7 / 24,889.7 | 0.16420 / 0.16420 | 52.13 / 52.13 | **0.000** |
| 2027 | 25,213.3 / 25,213.3 | 0.06074 / 0.06074 | 53.19 / 53.19 | **0.000** |
| 2028 | 25,541.1 / 25,541.1 | 0.04501 / 0.04501 | 57.37 / 57.37 | **0.000** |
| 2029 | 25,873.1 / 25,873.1 | 0.04150 / 0.04150 | 61.97 / 61.97 | **0.000** |
| 2030 | 26,209.5 / 26,209.5 | 0.07430 / 0.07430 | 69.08 / 69.08 | **0.000** |

The 2027 gas-CC exit wave lands at **2,231.8 MW**, S-4b's treatment figure to the 0.1 MW.
**No per-year mechanism reads `end_year` forward** — the 25-year window's head is identical
to the 5-year run's. The S-4b floor-retention caveat carried at §4(i) therefore transfers
into this campaign unchanged and un-retuned: 2028/2029 clear at +419.0 / +333.6 MW, and
those signs still ride on the 699.3 MW retention response.

### 6.2 Trajectory at reporting grain

| year | peak MW | RM | lw price | CO₂ Mt | thermal MW | firm clean | VRE MW | storage |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2026 | 24,890 | 0.164 | 52.13 | 16.320 | 23,150 | 1,900 | 4,100 | **0** |
| 2030 | 26,209 | 0.074 | 69.08 | 14.680 | 21,810 | 1,900 | 7,100 | **0** |
| 2035 | 27,848 | 0.088 | 72.44 | 10.266 | 22,609 | 1,900 | 14,902 | **0** |
| 2040 | 29,559 | 0.044 | 70.53 | 4.488 | 21,920 | 1,900 | 22,100 | **0** |
| 2045 | 31,376 | 0.091 | 62.68 | 2.666 | 23,920 | 1,900 | 29,902 | **0** |
| 2050 | 33,304 | 0.065 | 66.39 | 3.213 | 23,920 | 1,900 | 37,100 | **0** |

Peak load +33.8 % over the horizon; CO₂ −80.3 % (16.32 → 3.21 Mt); VRE ×9.0; thermal
essentially flat after the 2027 exit wave; firm clean pinned at 1,900 MW for all 25 years.
The RPS dual sits at the **$50 ACP ceiling** from 2030 through 2050 — the constraint is
escaping to its price cap, not clearing. Reserve margin never becomes comfortable (0.042–0.091
out-years). 2050 scarcity: 1,531 h ≥ $100, **0 h** ≥ $500.

**Entry/exit waves.** Exits total 5,676 MW in four discrete waves: 2027 gas_cc 2,136.0 +
gas_st 95.8; 2029 coal 54.0; **2033 gas_cc 210.9 + gas_cc_ccs 1,490.0** (CCS retrofits
retiring); 2037 oil 1,689.3. Thermal additions total 7,500 MW and are **100 % `economic`** —
zero `reserve_backstop`, zero `planned`, so no adequacy anywhere on this horizon is bought by
backstop construction (the S-4b result, extended 20 years). VRE adds in a strict alternating
1,802 / 1,198 MW cadence from 2029 to 2050.

### 6.3 Three structural signals, reported at full magnitude

1. **Zero storage entry in all 25 years.** Under curve-ON with a real capacity market and a
   9× VRE buildout, the value stack never clears for storage in any year. This is the run's
   most striking structural statement, and §5.1(b) is why it is also the least settled: the
   R-A ruling armed exactly the two storage-*entry* mechanisms, after this solve.
2. **I3 FAIL — out-year renewable dump, rising monotonically.** 2043 2.17 % → 2050 **8.50 %**
   of renewable potential. Coherent with (1): 37 GW of VRE against a 33 GW peak with no
   storage and no incremental firm clean. Reported as the model's own consequence, not
   judged against actuals that do not exist.
3. **I13 WARN — cobweb, `gas_cc(10)`.** Ten oscillations in the gas-CC entry channel; the
   alternating VRE cadence in §6.2 is the same signature in the renewable channel. The
   anti-cobweb machinery (entry rate limits + commissioning lag) is armed and this is the
   residual. Flagged, not tuned.

**Caveat (ii) carried, as the Q13 ruling requires:** every exit wave above is composed by the
same economic screen D14 measured at **exit recall 2/6** with a demonstrated gas-concentration
bias (model 3.563 GW vs actual 4.997 GW, −28.7 %; biomass/coal/gas_ct/oil exits missed
entirely). The 25-year fleet composition inherits that defect and **every composition statement
in §6.2 must be read with it** — including the 2033 CCS and 2037 oil waves.

## 7. Verdict, registration + board stamp

### 7.1 Determination: **T3 HOLD** — pre-declared correctly, on more failing gates than predicted

| gate | §3(3) predicted | measured |
|---|---|---|
| FC-1 structural integrity | (not predicted to fail) | **FAIL** — I3 out-year dump |
| FC-2 adequacy & equilibrium | (not predicted to fail) | **FAIL** — cobweb row, gas_cc(10) |
| FC-3 capacity-evolution skill | — | **FAIL** — T1-H bands |
| FC-4 crossover dispatch skill | FAIL (D14 carried) | **FAIL** — as predicted |
| FC-5 external corridor | SKIPPED-required | **SKIPPED-required** |
| FC-6 driver response | SKIPPED-required | **SKIPPED-required** |
| FC-7 provenance & DOF | CAVEAT | **FAIL** |
| FC-8 runtime feasibility | PASS | **PASS** |

**Two honest corrections to the pre-declaration, both stated rather than absorbed:**

- **§3(3) predicted FC-7 CAVEAT; it reads FAIL.** At tier t3 an absent DOF ledger is FAIL,
  not CAVEAT, and a golden additionally draws `UNATTESTED` without a
  `forecast_attestation.json`. **No attestation was authored** — inventing an instrument
  mid-campaign to clear a row is precisely what §3(3) forbids, so FC-7 stands at FAIL.
- **§4(iii)'s premise expired.** It recorded that no committed `dof_ledger.json` instrument
  exists; lane D8 landed one (PR #4427) after §§1–4 were written. The golden's own ledger was
  generated with that committed instrument — **7 entries, 7 identified** (6 published
  ORDC/scarcity values from NEISO's ISO overrides, 1 design-decision), zero unidentified, zero
  new DOF. Scored **both ways** so the addition cannot be an outcome-shopping vector: with the
  ledger FC-7 fails on `UNATTESTED` alone; without it, on `dof ledger absent` **and**
  `UNATTESTED`. **Determination is HOLD either way.**

**FC-3 leg selection, disclosed.** The board names FFR-3A-3 as NEISO's current T1-H basis, but
that bundle's score is not committed in this checkout. The posture-matched curve-ON leg
`neiso-2021-2025-curve` was used. The choice is **non-discriminating**: FC-3 FAILs on *all
four* committed NEISO T1-H legs (9–11 failing bands: curve 9, realized-k99 10,
mystic-rescore 10, fixed 11), so no selection could have changed the row or the determination.

**The honest headline.** The program's first §2.1b campaign is **mechanically clean and
structurally failing** — 25/25 years, zero solve error, inside budget on both axes, and five
failing gates with two more unscorable for want of instruments. That is the board's own
`readiness` sentence — *"ten hours of compute today would buy a mechanically-clean but
structurally-flawed golden run"* — **measured instead of hypothesised**, and at 29.2 minutes
rather than ten hours. The Q13 authorization licensed the compute, not a promotion claim.

### 7.2 Registration (rule 15, forecast namespace ONLY)

`scripts/register_forecast_run.py --summary … --label t3-golden-bau --kind t3` — the single
registration path. Run id **`neiso-2026-2050-t3-golden-bau`**, classified **kind `t3-golden`,
tier `t3`** (the PR #4408 path, first use), verdict key **`neiso-t3`** — verified **absent**
before the write, so nothing was displaced and no preserve-then-overwrite was required.
`ff-verdicts.json` is **purely additive: 178 insertions, 0 deletions**, no reformatting, so the
sibling S-6 / S-123-V keys are untouched. Committed per the campaign `.gitignore` block:
`config.yaml`, all 25 `evolution_<year>.json`, `full_horizon_summary.json`, `run_config.json`,
`forecast_verdict.json`, `dof_ledger.json`; parquet/npz/hourly/floor-retention artifacts stay
gitignored. **The backcast registry was not written to** (plan §7.5). Per-year evolution
artifacts were also committed and pushed **mid-horizon** as checkpoints, per §3's clause.

### 7.3 Board stamp (NEISO block only)

`gate.d_owner_auth` none → **granted**, quoting Q13 verbatim and marked **SPENT on execution**;
`gate.open` false → **true** with the per-campaign scope stated; `closed_on ['d'] → []`;
`gate.note` rewritten; new `t3_determination: HOLD`; `golden` replaced with the measured record.
**S-4b's leg-(b) and D14's leg-(c) content kept VERBATIM and asserted byte-identical**, as were
every other ISO's block and every other top-level key, by assertion before write. Every other
ISO still holds leg (d) `none` — this authorization was per-campaign and per-ISO by its own
terms and generalises to nothing.

**Flagged, not edited** (`t3_golden_campaign.flagged_not_edited`, the S-4V precedent — cross-ISO
prose is outside a NEISO-block-only charter): the `tier_ladder` T3 row still reads *"deferred
(§2.1b, Wave 4 withdrawn)"*; the `readiness` prose still frames the golden as a projection; and
`gate_reading` / `headline` were written for a board on which no ISO held leg (d). All routed to
the director.

**Rule 28:** the NEISO lever queue was read and is **CLEARED**; no lever was taken, no mechanism
tested, no `ScenarioConfig` field added — so no matrix cell is minted (duties b and c do not fire).

## 8. Exit state

**Delivered.** Golden solved (25/25, inside budget), scored (T3 HOLD), registered on the
forecast namespace, board stamped, all pushed and blob-verified.

**Routed to the owner / director — three items, none actionable inside this charter:**

1. **The R-A re-solve question (§5.1(b)) — the substantive one.** This bundle records the
   pre-R-A unarmed posture at HEAD `9e56f0f`; the R-A epoch entry says forecast-lane bundles
   solved before it "purge or re-solve before quoting". Re-solving is a second campaign the
   Q13 authorization does not cover. It matters because the run's headline structural result —
   zero storage entry in 25 years — is precisely what the armed storage-entry mechanisms would
   test.
2. **Cross-ISO board prose** now stale in NEISO's favour (§7.3), flagged not edited.
3. **The FC-5 / FC-6 instrument gap.** Both are REQUIRED at t3 and neither exists for NEISO
   (no committed benchmark-corridor table, no driver battery). Until they are built, **no ISO
   can score better than HOLD at t3 regardless of model quality** — a rubric-level ceiling, not
   a NEISO finding. FC-7's golden attestation is the same class.

**Container/infrastructure note for the next lane:** `data/clean` is gitignored and ephemeral,
so every fresh session pays ~30 min to rebuild it before any solve. `emissions-unit-annual` is
the peak-RSS datatype (transient ~11 GB on a 16 GB box) and the most likely place a constrained
container dies — which presents as a stall at "7 of 51", not as a loud failure, because
`regenerate_clean.py` reports a per-datatype failure without stopping the others. Worth an
environment-level cache decision by the owner; it is not a code change.
