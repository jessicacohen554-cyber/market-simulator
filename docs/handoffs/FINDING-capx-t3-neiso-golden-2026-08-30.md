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

## 5. Measured cost vs projected — TO BE WRITTEN POST-SOLVE

## 6. The horizon record — TO BE WRITTEN POST-SOLVE

## 7. Verdict, registration + board stamp — TO BE WRITTEN POST-SOLVE

## 8. Exit state — TO BE WRITTEN POST-SOLVE
