# FINDING — capx T16-A: T1.6 re-pointed to `entry_rate_limits` (owner ruling Q27), the two rungs run, FC-6 re-scored

**Session:** T16-A (capacity-expansion / Forecast Finalization track), branch
`claude/capx-t16a-ladder-repoint`. **Date:** 2026-09-02. **HEAD at launch:** `69b6c8d9`
(origin/main). **Authorization:** owner ruling **Q27**, capx r#27 sitting, 2026-09-01
(`docs/handoffs/capx-director-ledger-2026-08.md` §3) — *"RE-POINT T1.6 TO
`entry_rate_limits`, at the T16 recommendation … Execution = T16-A (Opus; 2 rungs +
artifact-only re-score, no golden re-solve), HELD until the golden session closes … The
re-point-vs-amend question (T1.6's cell names an economic condition, not a config field)
is verified and stated by the execution lane."*

**Sections §§1–4 are the PRE-DECLARATION** — written and committed BEFORE the two rungs
were solved (the T3-GOLDEN pattern; rules 13/21 discipline). §§5+ carry the measured
record and were written after.

---

## 1. Scope discipline (what this lane may and may not do)

- **Two rungs, one ladder, one ISO.** T1.6 / NEISO / 2026–2050, legacy heat-rate bins
  (the battery's own documented runtime trade). Priced at **~12 min** (D21 measured
  696.5 s for this exact ladder shape); actuals in §5.
- **No golden re-solve** — Q25 is SPENT, and a third campaign needs a new owner act.
- **Artifact-only FC-6 re-score of `neiso-t3`**, control-first: the committed FC-6 record
  is reproduced before anything is re-scored (§4).
- **STOP if anything beyond `neiso-t3`'s FC-6 rows would move.** FC-1/2/3/4/5/7/8 read
  from the same committed artifacts on both sides; the paired P1/P2/P3 rows read from the
  same committed `fc6/paired_invariants.json`. The ONLY row this lane can move is FC-6's
  **battery gate rows**.
- **Rule 28:** `entry_rate_limits` already exists (armed by owner decision D-2,
  2026-08-02) — **no field is added and no default moves**. The T1.6 registry record and
  the NEISO matrix shard are updated with the Q27 citation.
- **Nothing in the backcast namespace.** No keeper, no ISO keeper shard, no
  `calibration-complete.json`, no `status/*.js`, no `bench/`. No holdout year touched
  (this is a forecast-mode 2026–2050 run, unrestricted per rule 22's 2026 clause).
- **No new GitHub Actions workflow**; the rungs solve in-session.

## 2. THE FIRST DELIVERABLE — re-point WITHIN the pre-registration, not an amendment

**Verdict: RE-POINT. Plan §2 is not edited, and does not need to be.**

Plan §2's Tier-1 table (`docs/handoffs/forecast-driver-capacity-revenue-audit-plan-2026-07.md`,
the "Ladder" column) was read live this session. T1.6's cell reads, verbatim:

> **NEISO or CAISO forecast, VRE fleet held short vs long**

That is an **economic condition**, not an implementation. It is the only Tier-1 row that
names no config field:

| Row | Plan §2 "Ladder" cell | Names a config field? |
|---|---|:--:|
| T1.1 | `carbon_price` ∈ {0, 25, 50, 100} $/t | yes |
| T1.2 | `mass_cap_enabled` with `mass_cap_tons` … | yes |
| T1.3 | `gas_price_factor` ∈ {0.5, 1.0, 1.5} | yes |
| T1.4 | `demand_growth_path` low/mid/high | yes |
| T1.5 | Build years straddling `ira_wind_solar_last_year` | yes |
| **T1.6** | **"NEISO or CAISO forecast, VRE fleet held short vs long"** | **NO — an economic condition** |
| T1.7 | PJM `net_cone_per_kw_yr` × {0, 1, 2} | yes |
| T1.8 | `tech_cost_path` low/mid/high | yes |
| T1.9 | Storage fleet seeded at {5, 15, 25} GW (ERCOT) | no — a quantity |

Two consequences follow, and both are load-bearing:

1. **`renewable_buildout_pace` was the 2026-07-12 session's implementation choice made
   UNDER the pre-registration, never the pre-registration itself.** Swapping the
   instrument for one that genuinely holds the VRE fleet short vs long therefore leaves
   the pre-registered claim intact. The precedent is already in the registry: T1.9's
   `_storage_seed_gw` probe patch has exactly this relationship to its own
   "seeded at {5, 15, 25} GW" quantity row.
2. **The expectations are byte-identical across the delete and the re-point.** T1.6a
   (`rps_dual_over_acp` `le_target` 1.0) and T1.6b (`rps_dual_over_acp` `monotone_down`)
   are untouched — deliberately, and now pinned by a test
   (`TestT16Repoint::test_expectations_are_unchanged_by_the_repoint`). It was the
   instrument that failed, not the claim.

**The one thing a re-point still owes**, discharged here rather than assumed: the new
lever must actually hold the VRE fleet short vs long. Verified in code, not asserted —
`runner.py:1575` builds `entry_prior_max_gw` from
`data.build_throughput.max_annual_build_gw_by_tech` only when `entry_rate_limits` is
true, and `runner.py:1901` turns it into `entry_rate_caps_mw = ENTRY_GROWTH_LIMIT_MULTIPLE
(2.0) × prior-max` per technology; with the field false the caps are `None` and entry is
uncapped. `data/build_throughput.py`'s own docstring: *"Wind/solar come from their EIA-860
technology sheets"* — the ladder is not thermal-only. So `True` = short (throughput-limited),
`False` = long (uncapped), which is the plan's condition expressed in the model's own
mechanism.

**Recorded as a re-point, not silently.** This section is the statement Q27 asked the
execution lane for. No plan §2 text is edited by this lane; the ladder's registry comment
in `scripts/run_driver_battery.py` carries the same verification at its use site.

### 2.1 The declared confound (stated, not hidden)

`entry_rate_limits` also gates **thermal** entry and, through the adequacy path, the
reserve-margin backstop. The arm is therefore **broader than VRE alone**, and the ladder
isolates "VRE fleet short vs long" only up to that co-movement. This was disclosed in the
T16 recommendation and is carried into the registry comment rather than left implicit;
the rungs' own `renewable_build_gw` / `entry_thermal_gw` / `reserve_margin_final` metrics
are reported in §5 so the co-movement is measurable rather than argued.

### 2.2 What is NOT repaired here

Plan §2 line 99's third T1.6 clause — *"nuclear does not move the dual (once the CX-6a row
half lands)"* — has never been implemented, and is not implemented here. Q27 re-pointed
the VRE lever; it did not charter the nuclear leg. **T1.6 remains a two-of-three
implementation of its own pre-registration**, and that is stated rather than quietly
carried (it was first surfaced by T16 §6 and is repeated here so the next reader of the
re-pointed ladder does not mistake it for complete).

## 3. Pre-registered outcome map (written before the solve, so no result can be chosen)

**The honesty clause, carried verbatim from T16 §6 and binding by Q27:** in **both** D21
rungs the REC dual sat pinned **at** the $50 ACP ceiling in every year
(`rps_dual_over_acp` = 1.0) with 33.0 GW of VRE already built. **A correctly-wired lever
may still not move it. If it does not, that is a REAL finding about the RPS/ACP stack —
the dual escaping to its cap, NEISO's target unreachable at any plausible VRE build —
reported as the outcome. It is NEVER grounds for trying a third lever until one moves**
(rules 1/11/14; Q27 verbatim).

The three reachable outcomes and what each means, declared now:

| # | Measured `rps_dual_over_acp` across (vre_short, vre_long) | T1.6a / T1.6b | FC-6 battery row | Reading |
|---|---|---|---|---|
| A | falls (short > long) | PASS / PASS, non-vacuous | **PASS** | the lever discriminates; the ladder tests what it pre-registers for the first time |
| B | constant (both at the cap) | PASS / PASS **flagged vacuous** | **CAVEAT** | **the RPS/ACP finding** — the dual escapes to its cap and no VRE volume this lever can reach pulls it off |
| C | rises (short < long) | PASS / **FAIL** | **FAIL** | a directional violation — a root-cause issue to open, never a threshold to widen |

Outcome B is **not** a failure of this lane and is **not** re-run for a better draw: the
scorer's constant-series detector (`forecast_verdict._vacuous_pass_reason`, which exempts
neither `le_target` nor `monotone_down`) labels it vacuous either way, and the caveat's
*reason* becomes a measured statement about the RPS/ACP stack rather than an instrument
defect. Either rung outcome is a valid result.

**FC-6's category status is not in play under any of the three.** FC-6 already reads
**FAIL** on the golden-2 record through the **paired P2** leg ("year 2050: wrong:
gas_cc↓" — the new root-caused finding golden-2 §7.1 left standing, routed to D35).
Outcomes A and B both leave that FAIL exactly where it is; only the battery row moves.
This lane therefore cannot, and does not claim it can, clear FC-6.

## 4. The control (control-first, before any re-score)

`forecast_verdict.py --tier t3` was run at this session's HEAD (`69b6c8d9`) over the
**committed golden-2 artifact set** — the campaign's `full_horizon_summary.json` (also
supplying the invariants vector), `run_config.json`, `dof_ledger.json`,
`forecast_attestation.json`, its own `fc6/paired_invariants.json` and
`fc6/driver-battery-neiso-2026-09-01.json`, the committed T1-H score
(`results/hindcast/neiso-2021-2025-curve/NEISO/2ba529574d4982ea/score.json`), the
committed D14 T1-X crossover score
(`results/hindcast/neiso-2023-2027-crossover-capxd14/NEISO/07e416f3f8072e7c/crossover_score.json`),
the re-authored corridor disposition table and the committed benchmark anchors.

| check | result |
|---|---|
| verdict JSON vs committed `results/ff-t3-neiso-golden/bau/forecast_verdict.json` | **IDENTICAL outside `provenance`** (whole-document compare, every category and row) |
| determination | HOLD both |
| FC-6 battery row | `CAVEAT — no gate FAIL but 2 vacuous row(s) … ['T1.6/T1.6a', 'T1.6/T1.6b']` both |
| `cache_epoch` | `706e7ba8e6582d42` both |
| `scored_at_sha` | control `69b6c8d9793a` vs committed `7726d91e98b4` — the only intended difference |

The control reproduces, so the re-score in §6 differs from the committed record by exactly
one input: the battery JSON.
