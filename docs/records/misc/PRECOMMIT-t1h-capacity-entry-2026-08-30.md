# PRECOMMIT — T1-H capacity-entry repair lane (2026-08-30): the STORAGE leg (D-2 + D-3) and the WIND leg (D-8/B-3), chartered as two scoped rungs — Phase-0 ZERO-SOLVE, Phase-1 A/B on the declared gates

**Authority.** Owner ruling 2026-08-30 (director sitting, decision card 2):
*"Charter both legs now"* — the T1-H capacity-entry defect (carried as
"two defects, not one" since board v13 item 11 / A-7) gets a charter and a
lane this sitting. Program: `docs/forecast-development-plan-2026-07.md`
(T1-H); parent diagnosis: `docs/FINDING-entry-screen-t1h-2026-08.md` (the
defect register D-1…D-8 cited below); adjudication context:
`docs/FINDING-entry-signal-disarm-2026-08.md` (the C-1 verdict —
`entry_lookahead_reprice` ERCOT cell `K`, `fc O`; arming/disarming the
signal replacement is an OWNER promotion decision and is NOT re-opened
here). This precommit is pushed before any measurement runs.

## Scope — what this lane owns, and what it explicitly does not

**DEDUP GATE (checked first, Phase-0 step 0):** the capx program's D11-R
lane has already built and registered `entry_margin_exhaustion` (the
margin-exhaustion entry-volume rule; A/B `t1h-d11r-{control,exhaustion}`
registered, arming escalated, hold-until-D12). **Defect D-1 (the bang-bang
allocator: caps decide volume) is therefore CLAIMED by capx and is OUT OF
SCOPE here.** Phase-0 re-verifies that claim from the committed D11-R
artifacts; if D11-R's rule also closes part of the storage leg, that part
transfers to watching D12 and only the residual proceeds here. Rule 26
duty (a): the ERCOT/CAISO shard cells for `entry_lookahead_reprice`,
`capacity_screen_scarcity_restoration` and the D11-R row were checked;
nothing chartered here re-tests an adjudicated `R`/`I`/`G` cell.

- **LEG A — STORAGE ENTRY (defects D-2 + D-3, parent finding §1.1):**
  (i) **D-2**: `apply_storage_new_entry` iterates `STORAGE_TECHS`
  unconditionally (`storage.py:1855`) with **no availability-year gate**,
  while the thermal path gates emerging techs through
  `_EMERGING_AVAILABLE_YEAR` (`new_entry.py:184`, `:258-263`) — so a 2023
  ERCOT decision year builds 3 GW of 100-hour iron-air + 2 GW of vanadium
  flow. The repair candidate is the SAME gate the thermal path already
  uses, extended to storage techs with cited availability years — one
  mechanism, no new free parameter (rule 19 `[R-ONE-MECH]`, rule 5
  `[R-NO-MAGIC]`: each availability year enters `constants.py` with a
  primary-source citation).
  (ii) **D-3**: tech selection ranks by **absolute $/MW-yr margin**
  (`storage.py:1892-1901`), so li-ion clears +$1.47 M/MW-yr and still
  builds zero (6th of 6). The repair candidate is selection on a
  cost-normalized metric (margin per unit capital cost, i.e. the
  developer's actual ranking object) — identification from published
  capital-cost data already in the repo's cost tables, never from the
  residual (rule 23 `[R-FROZEN-DERIVE]`).
- **LEG B — WIND (behaviour B-3, upstream defect D-8):** wind's zero
  economic entry is **downstream of the zone-flat, ORDC-dominated signal**
  (capture ratio vs flat mean 0.74–0.93 while solar reads 1.38–2.58).
  This leg is a MEASUREMENT rung, not a repair rung: Phase-0 quantifies,
  on committed T1-H dumps + the committed disarm-run artifacts, how much
  of the wind miss closes under (a) the dual-based signal object the C-1
  verdict identified as the "right object", and (b) a zonally-resolved
  variant, WITHOUT arming either. Its deliverable is the measured decision
  input for the owner's C-1 promotion call — because the wind leg's repair
  IS the signal-object decision, which is reserved to the owner.

## Phase-0 (ZERO-SOLVE, this lane, immediately)

All reads from committed artifacts: the T1-H hindcast bundles
(`ercot-2021-2025-realized-t1h-refresh`, `caiso-2021-2025-realized`, the
C-1 disarm/control pair), the committed `screen_signal_diag_*.npz` dumps,
and committed code/constants. No LP, no hindcast re-run, no mechanism or
default changed, no matrix cell moved (nothing tested yet).

0. **Dedup verification** (above).
1. **D-2 census:** every storage tech built in any T1-H decision year vs
   its earliest cited commercial-availability year; the anachronism table
   at full magnitude.
2. **D-3 replay:** re-rank the committed entering-2023 storage margins on
   the cost-normalized metric; report the counterfactual build mix (which
   techs/volumes flip) — arithmetic replay only.
3. **Leg-B measurement** as scoped above.
4. **Stop rule:** if Phase-0 finds either leg's defect absent at HEAD
   (e.g. repaired en passant by D11-R or later merges), that leg closes as
   OVERTAKEN with the citation, and does not proceed.

## Phase-1 (opens ONLY on the Phase-0 record; separate push, own A/B)

Leg A only. Implement the D-2 gate + D-3 selection metric as
`ScenarioConfig`-registered mechanisms (rule 24 `[R-REGISTRY]`; matrix row
+ all-shard cell lines in the same PR, rule 26 duty (c)); A/B against the
registered T1-H baseline pair with kill-gates fixed here: the A/B is
REJECTED if (K1) any addition-metric band moves AWAY from actuals by more
than it moves toward on the others (full-magnitude both directions, rule 1
`[R-STRUCT]`), or (K2) the repair's effect is indistinguishable from the
control (inert ⇒ cell `I`). **Arming any Phase-1 mechanism in the T1-H
default lane is an OWNER decision on the A/B record — never this lane's.**
Registration through `scripts/register_forecast_run.py` alone (rule 15).

## Records duties

Phase-0 finding: `docs/FINDING-t1h-capacity-entry-phase0-2026-08-30.md`
(or dated day of landing); matrix cells updated in the session that tests
a mechanism, rejections included (rule 26 duty (b)); this charter is cited
by the §8 ledger entry of the 2026-08-30 decision-card sitting.
