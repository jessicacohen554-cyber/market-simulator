# PRECOMMIT: SPP-85, net-load-mask repair of SPP's CAMPD outage extracts (7-year control + arm)

Lane: SPP-85 (SPP coal outage-basis reconciliation). Parent: SPP-84
(`FINDING-spp-84-published-outage-vs-keeper-2026-09-26.md` §5.1).
Keeper: `2026-09-24-r-spp-corrected-inputs`, bundle `results/calibration/rspp_span` (2019–2025),
`basis_sha` `ec13e5c2ad35c4f817cc496ff2363affb3fed2f9`. Session base: `origin/main` `56272c15`.
Phase 0 (zero LP): `docs/handoffs/FINDING-spp-85-coal-outage-basis-2026-09-26.md`.

**Written before any price effect of this change was computed.** No re-clear, no merit instrument
and no solve has been run on the arm. The only numbers in hand are availability quantities
(MW / TWh of capacity) and SPP's published outage.

## 1. The defect and the change (frozen now; rule 23)

- **Defect (code scope).** `scripts/lib/outage_detect._ISO_TO_BA` had no `SPP` key.
  `high_load_mask("SPP", …)` therefore returned `None`, and `filter_revealed_outages` kept **every**
  detected span. This is its documented no-mask no-op. The three committed SPP extracts' recorded
  `min_inmerit_hours` (24 standard / partial, 6 short) was **never in effect**. SPP-20 listed this key as
  owed to the outage lane (FINDING-spp-20 §"six-tuples"), and it was never landed.
- **Change.** Add `"SPP": "SWPP"`, the EIA-930 BA the model reads for SPP everywhere else. Re-derive each
  committed extract at **its own recorded invocation**, to new `-netloadmask-` paths:

  | layer | committed | companion | rows |
  |---|---|---|---|
  | ≥ 5-day standard | `campd-unit-outages-SPP.csv` (`05aced4f…`) | `campd-unit-outages-netloadmask-SPP.csv` (`43161365…`) | 6,627 → 6,581 (−46, all COAL) |
  | 1–5 day short | `campd-unit-outages-short-SPP.csv` (`82fca832…`) | `…-short-netloadmask-SPP.csv` (`5c016785…`) | 1,689 → 460 |
  | partial plateau | `campd-partial-outages-SPP.csv` (`7acc39f6…`) | `campd-partial-outages-netloadmask-SPP.csv` (`3792217d…`) | 204 → 0 |

- **Frozen settings changed: NONE.** Every threshold is the committed extract's own. Each companion is a
  strict full-row subset of its incumbent (tested: `tests/unit/data/test_unit_outage_netload_mask_repair.py`).
  The short and partial re-derivations read the **incumbent** standard extract for their when-operable
  baseload guard, exactly as the committed ones did. The only delta is the mask. Nothing was swept;
  no alternative threshold was computed.
- **Basis (rule 23): the measured source, never the residual.** SPP's own published hourly coal outage
  (portal `capacity-of-generation-on-outage`) sits 1.18–3.40 GW below the keeper's coal unavailability in
  every year 2019–24. The repair restores 0.57–1.12 GW of it (FINDING §3).
- **Channel.** New `ScenarioConfig.unit_outage_netload_mask_repair` (default False, in
  `_CACHE_KEY_OPTIONAL_FIELDS`). It selects all three companions and **replaces** each layer; it never
  stacks on one (rule 19). Off, it is byte-inert. There is a matrix row plus a cell in every ISO shard
  (rule 28(c)).

## 2. Zero-LP LP-input delta (fleet_only, keeper recipe, HEAD; `scripts/probes/_spp85_fleet_delta.py`)

| year | Δ coal avail GW (mean) | COAL_PRB TWh | COAL_LIGNITE TWh | rows moved |
|---|---|---|---|---|
| 2019 | +0.510 | +4.204 | +0.260 | 133 |
| 2020 | +0.664 | +4.744 | +1.071 | 115 |
| 2021 | +1.044 | +8.062 | +1.080 | 127 |
| 2022 | +0.903 | +6.608 | +1.301 | 117 |
| 2023 | +0.583 | +4.672 | +0.436 | 103 |
| 2024 | +0.842 | +6.213 | +1.162 | 123 |
| 2025 | +0.812 | +6.311 | +0.802 | 123 |

- Twelve of the 15 LP fleet arrays are **byte-identical** in every year. Moved: `availability` (coal rows
  only), and `min_gen` / `min_gen_mechanism`.
- The floor move is the **incumbent** coal must-run floor (`MECH_COAL_MUSTRUN`, id 3) re-applying in the
  restored hours: +1.90 TWh (2021) and +1.54 TWh (2024) of placed floor. No `min_gen > pmax × avail` cell
  exists in either leg. No new floor is created (rule 19).

## 3. G-DRIFT (rule 29(b)): `ec13e5c2` → `56272c15`: **LIVE, control solve earned**

`git diff --stat ec13e5c2…56272c15 -- src/market_sim scripts/run_calibration*.py scripts/lib
data/raw/_validation-source data/raw/reference` lists **83 files, +7,549 / −366**.

Those hunks cannot be classified all-INERT for SPP at hunk grain. They include the 2026-09-25 coal-subclass
refactor, which reaches every SPP coal row:
- `plant_taxonomy.py`, `coal.py`, `fleet/arrays.py`, `fleet/campd_bins.py`, `fleet/eia860.py`;
- `data/raw/reference/custom-bin-assignments.csv`.

It also includes `outages.py`, `zone_assignment.py`, `ba_membership.py` and `pipeline/commitment.py`.
**Form 4 is void, and a control solve is earned for every year.** Each shard solves the control, the keeper
recipe replayed unchanged at the pinned SHA, and then the arm (control + `--set
unit_outage_netload_mask_repair=true`), for its one year, at the same SHA (the SPP-42 precedent).

The arm is judged against its own control, never against the committed keeper numbers. The control-minus-keeper
difference is reported as the HEAD drift.

## 4. Solve plan (rules 32 / 34 / 36)

**Seven shards, one per year, 2019–2025.** This is SPP's full registered year set (rules 34(c) / 35(b)).
Each shard is pinned to the full SHA of the commit carrying this doc. Each shard runs:

```
python scripts/replay_keeper.py results/calibration/rspp_span --years <Y> \
  --out-dir results/calibration/spp85_ctl_<Y> --note "SPP-85 control <Y>"
python scripts/replay_keeper.py results/calibration/rspp_span --years <Y> \
  --out-dir results/calibration/spp85_arm_<Y> --note "SPP-85 arm <Y>: netload-mask repair" \
  --set unit_outage_netload_mask_repair=true
python scripts/probes/_spp85_shard_check.py --year <Y> --leg results/calibration/spp85_arm_<Y>
```

- **Push.** Both bundles, including `dispatch/<Y>_P1.parquet`, go to `claude/spp85-<Y>` via a `.gitignore`
  negation plus a plain `git add` (rule 34(a)).
- **The parent composes** the seven arm legs:
  `scripts/probes/_rspp_compose.py --side arm --require unit_outage_netload_mask_repair=true`.
  It composes the seven control legs with `--require unit_outage_netload_mask_repair=false`.
- **The parent then** attests, runs `build_dof_ledger --iso SPP --check`, and scores both composites.
  If the owner promotes, it registers the arm and lands it on `main` before merge (rule 33(f)).
- **Control bundles never reach `main`** (rule 29(c)).

## 5. Expectations (directional; declared so they cannot be fitted)

| # | expectation |
|---|---|
| E1 | Shard check PASS on all seven legs: arm recipe = keeper + exactly the one field; six extract sha256 match; resolved CAMPD path is the `-netloadmask-` extract. |
| E2 | Arm − control, COAL (PRB + LIGNITE) TWh **rises in every year**, bounded by §2's Δ available TWh. |
| E3 | Arm − control, demand-weighted price **falls or is flat in every year** (more cheap coal available). The SPP-84 coal-only instrument (a larger, pro-rata rebase) put the full-rebase effect at −0.4 to −4.6 $/MWh. This repair is 22–52 % of that rebase, so the moves should be smaller. |
| E4 | **2024 C3a may worsen** (keeper −3.9 %, and lower prices push it further negative). This is the declared cost. 2019–21 C3a should move toward band. |
| E5 | C8 coal forced share may rise, because the incumbent must-run floor re-applies in restored hours (+1.5–1.9 TWh placed floor). The criterion reads the committed `legitimacy_diagnostics.json`, and it is reported at full magnitude. |
| E6 | 2022 C1 COAL_PRB (already +9.58 TWh, FAIL) worsens. This is a known crossover object (SPP-41/44/69/75/77); nothing here addresses it. |
| E7 | Slack and dump do not rise materially in any year: capacity is added, never removed. |

## 6. Recommendation rule (fixed now)

**Recommend PROMOTE iff all hold:**
- (a) E1 holds on every leg.
- (b) E2 holds in sign in every year (the repair does what it says).
- (c) E7 holds.
- (d) `build_dof_ledger --iso SPP --check` shows zero new free parameters.
- (e) D-4 shows no new off-window binding (rule 20).

**Gate outcomes are not a criterion in either direction** (rules 1 / 14). A C3a regression in 2024 is
reported, attributed and not re-tuned. Offer multipliers stay at 0.93 everywhere (rule 1(b)/(c)). The owner
rules on promotion (rule 31); this lane recommends and does not act.

## 7. Standing duties

- Update `SPP.js` cells (`unit_outage_netload_mask_repair`, `campd_outage_windows`, `dam_availability_rebasis`)
  and add the §5.7 note (rule 28(b)).
- Archive shards once their bytes are fetched and verified (rule 33).
- Delete nothing before the owner rules (rule 31).
- Leftover branches `claude/rspp-2019` … `claude/rspp-2025` need the owner to remove them (sessions cannot delete refs).
