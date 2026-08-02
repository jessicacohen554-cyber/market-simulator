# FINDING — pjm-145: `pjm_dam_availability` (measured PJM generation-outage availability)

**Session pjm-145, 2026-08-02.** PREREG:
`results/calibration/PREREG-pjm145-dam-availability-2026-08-02.md` (committed
before any measurement; the ex-ante instrument
`scripts/probes/_pjm145_damavail_exante.py` and the chain script
`scripts/probes/_pjm145_chain.sh` committed before running).

## §0 — Headline

**REFUSED EX ANTE — no solve spent, keeper unchanged. Matrix
`dam_availability_rebasis` PJM `U` → `G`.** The ex-ante instrument measured
the armed overlay as a **+19–24 GW mean-availability net RESTORE** (restore on
364/364/360 of covered days; remove on 0/0/5), and the addendum decomposition
shows **66–68 % of that restore is structural-zero resurrection** —
17.7/19.2/18.5 GW mean of capacity the model's own finer, measured, unit-grain
record (CAMPD unit/short/partial outage windows, layup, retiree CEMS caps,
mid-year COD masking, top-of-stack CC outage allocation) says was physically
absent, revived to λ by the water-fill's `_flat` branch. Model covered-class
availabilities are 0.44–0.83 against the uniform fleet-mean target
0.867–0.887: PJM publishes no per-class outage split, so the honest
first-order transform the intake documented (one fleet-wide fraction, applied
uniformly per class) is measured here to be **inadmissible at PJM's fleet
state** — arming it would adjudicate the transform's artifact, not the data.
Refusal grounds: rule 1 `[R-STRUCT]` (the dominant effect is physically-false
capacity injection), rule 14 `[R-ACCURATE]` misalignment clause (an RTO-wide
whole-fleet aggregate — non-fossil forced MW included — mapped onto seven
classes contradicts finer measured inputs already armed, making the fleet LESS
reflective of reality), rule 19 `[R-ONE-MECH]` (the unit-grain CAMPD overlays
are the incumbent availability owner for these classes; this stacks a coarser
second owner that mostly UNDOES the incumbent's measured detail). The
pre-registered kill-rule LETTERS did not fire and are scored honestly in §4;
the refusal rests on the addendum measurement plus the standing rules — the
ERCOT-145 / caiso-149 refused-ex-ante pattern. Direction prediction scored
**WRONG** (§8). Re-open conditions in §9.

## §1 — Session preamble: the two standing fixes

1. **Default cache key (handoff fix a): ALREADY REPAIRED UPSTREAM — no work
   was needed.** At this session's HEAD (f58339b), `ScenarioConfig().cache_key()`
   returns the pinned `603c2498bf71d21d` and all three handoff-named tests pass
   (`test_cc_committed_offer_margin`, `test_ramp_envelope_basis`,
   `test_forecast_xyear_warmstart_flag::test_default_cache_key_unmoved`, plus
   `test_persisted_identity` — 42 passed). The repair was the FFR-W1X Wave-1
   close (2026-08-02): `coal_prb_committed_dispatchable` +
   `coal_prb_committed_split` registered in `_CACHE_KEY_OPTIONAL_FIELDS`
   (scenarios.py:54–71 comment records it as occurrences six and seven of the
   unregistered-field failure), and pjm-144 registered its own two fields. An
   AST field-diff against the pin commit (36cfa4d) confirms all 10 fields added
   since the pin are registered and none was removed.
2. **Full-suite baseline on origin/main f58339b (handoff fix b), recorded
   BEFORE any edit:** `11 failed, 5869 passed, 31 skipped, 1 xfailed`
   (16 m 44 s). The failures:
   `tests/unit/data/test_measured_chp_heat_rates.py` ×7,
   `tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`,
   `tests/scoring/test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers`,
   `tests/curation/test_consume_phase3d.py::EgridZoneAssignmentParity::test_zone_lookup_matches_raw`,
   `tests/regression/test_fleet_arrays_golden.py::test_generators_to_fleet_arrays_ercot_2023_golden`.
   The first three groups are the handoff's known-red set; the last two are
   additional pre-existing failures on clean main (not present in the handoff's
   9950a5c list; both fail before any pjm-145 edit, so neither is a pjm-145
   regression). The handoff's three cache-key tests now PASS (item 1).
   `test_dispatch.py::test_full_year_200_generator_fleet` passed in this run.

## §2 — Queue provenance (rule 28a)

Taken: **`docs/mechanism-testing-matrix.md` §5.3 item 7** — `pjm_dam_availability`
(**U**, "intaken but untested"), the live head of the PJM queue and the one
cross-ISO queue head with committed data, built code, and no charter/data-ask
blocker (MISO has no live lever; ERCOT items 7–8 are data-intake-first; NEISO
requires a charter; CAISO's live items are a charter and a derive
re-identification). Matrix row `dam_availability_rebasis`, PJM column
(cells "KUUR.R", PJM = index 2). Rule 25: no ERCOT parameter or verdict
transfers; every PJM constant is the intake's own cited default.

## §3 — Local-data regeneration required by the keeper recipe (recorded for
the next session)

A fresh clone cannot replay the pjm-143b keeper as-is; two gitignored inputs
had to be regenerated first (both documented regeneration paths, not new
intakes):

- `data/raw/pjm-da-virtuals/hrl_da_incs_decs_{2023..2025}_*.parquet` — the
  keeper arms `pjm_da_virtual_bids`, whose loader hard-fails when the raw
  DataMiner2 feed is absent ("the mechanism never silently no-ops"). Re-pulled
  via `scripts/data/fetch_pjm_da_virtuals.py --feeds hrl_da_incs_decs`
  (36 monthly parquets; the feed is redistribution-restricted, hence
  gitignored — `data/raw/pjm-da-virtuals/README.md`).
- `data/raw/PJM-AS/pjm_{2023..2025}_as_up_mw.parquet` — the measured reserve
  requirement series, derived from the committed
  `reserve_market_results_*.parquet` by
  `scripts/data/build_pjm_as_withholding.py`. Caveat: the deriver also
  rewrites the committed ≤2022 parquets with byte-churned (same-size, no
  source change) parquet metadata — `git checkout` those five afterwards
  rather than committing a rule-23-uncited re-derivation.

Plus the standing setup: `uv sync --frozen`, the three curate scripts, and
`scripts/regenerate_clean.py transfer-interface-limits ramp-capability`.

## §4 — Ex-ante measurement (PREREG §3) and the kill scoring (PREREG §4)

Evidence: `results/calibration/_pjm145_damavail_exante.json` (instrument
committed at c053a51 before running).

**Loader half.** Coverage is essentially complete — 364/364/365 covered days
(2023/2024/2025). Measured unplanned (forced+maintenance) outage MW at PJM RTO:
mean **15.79 / 15.38 / 18.16 GW** (p50 15.36/15.00/18.00). Implied fleet
availability fraction: mean **0.884 / 0.887 / 0.867** (p5 0.831/0.846/0.818);
zero days at or below 0.

**Fleet half** (arm-minus-control, the real `generators_to_fleet_arrays` path
with the keeper's own meta kwargs). Pooled cap-weighted day-mean availability
delta: **+24.02 / +23.69 / +18.84 GW mean** — restore on 364/364/360 days,
remove on 0/0/5; p95 |Δ| 41.0/41.8/39.6 GW, max 48.5/45.4/44.2 GW. Per class
(mean Δ, 2023/2024/2025): COAL **+13.6/+13.4/+11.3 GW** (model cap-weighted
day-mean availability 0.517/0.487/0.513 → target 0.884/0.887/0.867),
CC_REGULAR +6.3/+5.8/+5.0 GW (0.772/0.790/0.783 →), ST_GAS +2.8/+3.3/+1.8 GW
(0.571/0.440/0.576 →), CT_PEAKER +1.2/+1.3/+0.7 GW (0.834/0.835/0.835 →); the
three CHP classes are near-neutral (their model means already sit at the
target).

**Kill scoring, letter-honest.** None of the three pre-registered kill rules
fires as written: KILL-COVER no (364–365 days); KILL-INERT no (the opposite —
the delta is two orders of magnitude above the inertness floor);
KILL-DEGENERATE no **as operationalized** (no class-day pins at cap 1.0 — λ
tops out well below 1 — and no target ≤ 0). The degeneracy KILL-DEGENERATE's
stated rationale targeted ("the measured aggregate and the model fleet basis
are incompatible at first order; arming would exercise the clip, not the
data") **is present but in a mode the two operationalizations did not
anticipate**: not cap-saturation but structural-zero resurrection at λ. That
is recorded as a miss of the kill rule's letter, and the session proceeded to
measure the mode directly (§5) rather than either (a) claiming the kill fired
or (b) spending two chains on a transform the evidence had already
disqualified.

## §5 — The decomposition that closed the lane (addendum instrument, no LP)

Evidence: `results/calibration/_pjm145_damavail_decompose.json`
(`scripts/probes/_pjm145_damavail_decompose.py`, committed before running).
On restore days, the per-unit lift decomposes into **structural-zero
resurrection** (pre-overlay day-mean availability ≈ 0 → lifted to λ by the
water-fill's `_flat` branch) vs **living-unit lift** (λ·(1−ad)):

| year | zero-lift GW | live-lift GW | zero share |
|------|-------------|--------------|-----------|
| 2023 | 17.73 | 9.14 | **66.0 %** |
| 2024 | 19.25 | 9.65 | **66.6 %** |
| 2025 | 18.47 | 8.55 | **68.4 %** |

Where the zero-lift lives (2024): COAL **9.56 GW** (248 units / 27.4 GW ever
zero on restore days — the layup / retiree-CEMS-cap / outage-window record),
CC_REGULAR **5.86 GW** (526 tranches / 57.5 GW — dominated by
`cc_outage_derate_from_top`, which allocates each plant's measured outage MW
to its top-of-stack tranches, zeroing exactly the tranches this overlay then
revives), ST_GAS **3.61 GW**. The overlay's remove leg — the only leg that
could ADD outage information the model lacks — fires on **0/0/5 days in three
years**. As built at PJM, the mechanism is ~entirely its restore leg, and
two-thirds of that leg is resurrection of measured absence.

This is the ERCOT-135 §7.2 defect ("the plant-grain water-fill … can lift a
plant back above a forced derate modelling a physically destroyed unit"),
whose pmax×BIN_FORCED_DERATE_BY_YEAR ceiling fix (ercot137) was applied to
the **ERCOT** path only; the PJM class-grain block in
`src/market_sim/data/fleet/arrays.py` has no such ceiling. It is also why
ERCOT's analogue could be adopted while PJM's cannot: ERCOT's measured target
is the 60-Day DAM disclosure at **per-class/per-plant grain** (the right
boundary), while PJM publishes only an RTO-wide whole-fleet aggregate whose
numerator additionally includes non-fossil forced MW.

## §6 — Why refused rather than solved (the rules, applied)

- **Rule 1 `[R-STRUCT]`:** a mechanism whose dominant measured effect
  (~two-thirds of ~27 GW of restore-day lift) is capacity that did not
  physically exist is not a real market behaviour; its A/B would produce
  evidence about the transform's artifact, not about PJM's outage record. No
  gate outcome from such an arm could be quoted either way.
- **Rule 14 `[R-ACCURATE]`, misalignment clause:** the accurate datum (PJM's
  published outage aggregate) is "defined on a different boundary than our
  representation" — one whole-fleet number (nuclear/hydro/wind forced MW
  included) against seven fossil-thermal classes whose availabilities the
  model already carries from finer measured sources. Using it literally makes
  the fleet less reflective of reality (COAL 0.49–0.52 → 0.884 while PJM's
  coal fleet was in its layup/retirement wave). The clause's remedy — "prefer
  a *reconciled* version of the real data" — is exactly the re-open condition
  (§9), not an in-session retune (rule 23 froze the intake's cited defaults).
- **Rule 19 `[R-ONE-MECH]`:** availability for these classes is already owned
  by the measured unit-grain stack (`outage_source="historic"`: CAMPD unit /
  short / partial outage windows, layup, retiree CEMS caps, COD ramp, CC
  top-of-stack allocation — each individually rule-13-admissible). Arming a
  second, coarser owner on the same phenomenon — one that primarily UNDOES
  the incumbent's detail — is stacking, not replacement.

Not run: the A/B chains (`scripts/probes/_pjm145_chain.sh` stays committed
for any post-re-open session), hence no construction/kill gates (PREREG
§5–§6) were exercised, no bundle exists, and no dashboard run is registered —
the ERCOT-145/146/147 no-solve-closure pattern. C3c is therefore untouched
and its standing 1 h / 2.5 h margins (queue item 6) are unchanged.

## §7 — What this verdict does NOT say

- It does **not** adjudicate the PJM outage *data* — the feed is real,
  rule-13-admissible, coverage-complete, and stays intaken. What is refused is
  the **uniform class-grain application against this fleet representation**.
- It does **not** touch ERCOT's `K` (per-class disclosure, ceiling-fixed,
  owner-adopted), CAISO's `U` (`caiso_dam_outages`, different construction),
  or the MISO/NEISO cells (rule 25 — nothing transfers either way).
- It does **not** close PJM's availability question in general: a future
  mechanism that passes the §9 re-open conditions enters as a NEW
  identification under its own charter.

## §8 — Direction prediction, scored honestly (PREREG §7)

**WRONG, decisively, and before any solve.** Predicted: NET REMOVE (measured
availability below the model's) → prices up. Measured: NET RESTORE
(+19–24 GW mean; remove fires 5 days in three years). The prediction's error
is itself the finding: it assumed the model's covered-class availability was a
~0.90–0.94 statistical estimate the measured aggregate would undercut. In
fact the keeper's availability basis is already a *measured, unit-grain*
stack running the classes at 0.44–0.83 — far below any whole-fleet mean —
which is precisely why a fleet-mean target uniformly applied per class is the
wrong-boundary datum here. (Had the prediction been right, the arm would have
been a small remove-side correction and the A/B worth solving.)

## §9 — Verdict, registration, and re-open conditions

**Matrix:** `dam_availability_rebasis` PJM `U` → **`G`**, cells
`KUUR.R` → `KUGR.R`, evidence citation added (this finding + the two committed
probe JSONs); §5.3 item 7 adjudicated in `docs/mechanism-testing-matrix.md`;
`docs/calibration-log/pjm.md` entry added — all in this session (rule 28b).
No dashboard registration (no run exists). Keeper `2026-07-31-pjm-143b-hy-level`
unchanged. PREREG, both probe scripts, both evidence JSONs, and the unused
chain script are committed on the session branch.

**Re-open conditions** (any one, under its own charter, parameters derived
from PJM's own record — rule 25):

1. **Restore ceiling composed with the structural-derate registry** — port
   the ercot137 fix: cap every unit's restored availability at its
   pre-overlay structural envelope (COD mask, retiree CEMS cap, layup window,
   CC top-of-stack outage allocation are never revived). Note measured here:
   with resurrection removed, the mechanism's remaining content is
   ~9 GW/day of living-unit lift toward a fleet-mean target whose numerator
   still includes non-fossil MW — condition 2 or 3 is likely also needed
   before an arm is worth a solve.
2. **A class- or unit-resolved PJM outage source** (GADS-style split PJM does
   not publish today), or at minimum a fuel-split numerator that purges
   non-fossil forced/maintenance MW from the fossil-thermal derate.
3. **The event-window-cap form** (ERCOT-148/149's shape, PJM-identified):
   measured event windows capping the DAM restore rather than a uniform
   fleet-mean water-fill.
