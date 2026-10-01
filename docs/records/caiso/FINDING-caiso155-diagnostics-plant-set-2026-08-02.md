# FINDING — caiso-155: the diagnostics-harness PLANT-SET defect (caiso-151 §F) is FIXED ISO-generically — and the census found the harness's floors-RECONSTRUCTION drops the generic override channel, a second defect that both LOSES channel-armed floors (CAISO's firm-import trio) and HALLUCINATES replaced ones (MISO's pre-miso-74 Manitoba block). Firm-import floors are now D-2/D-4-visible; no keeper verdict moves

**Session:** caiso-155 (CAISO/cross-ISO calibration). **Date:** 2026-08-02.
**Lane:** the caiso-151 §F filed defect, carried unowned through
caiso-152/153/154 §I. **This is an AUDIT/SCORER fix, not a mechanism lever**
(rule 28a): no adjudicated matrix cell is re-tested, no mechanism armed, no
`ScenarioConfig` field added, no solve run, nothing registered on any
dashboard, no rule-22 marker written. The holdout spend freeze stays ACTIVE
and untouched; every number here is 2023–2025.

Pre-registration: `PREREG-caiso155-diagnostics-plant-set-2026-08-02.md` +
two addenda (`-ADDENDUM-rebuild-channel-`, `-ADDENDUM2-replay-floors-`), each
committed and pushed BEFORE the numbers it governs existed. Instruments:
`scripts/probes/_caiso155_plant_set_census.py` (census, fix-aware on re-run),
the A1a/A1b/A2/A3/A4 ladder (scratch transcripts summarized here),
`scripts/probes/_xiso3_forced_share_d4_census.py` (the production-rubric
re-score, unchanged).

Keepers at entry and exit: ERCOT `2026-08-01-ercot149-gas-event-cap`, CAISO
`2026-07-31-caiso153-reid-b`, PJM `2026-07-31-pjm-143b-hy-level`, MISO
`2026-07-31-miso-109b-hy-level`, NYISO `2026-08-01-nyiso109-zonal-margin-anchor`,
NEISO `2026-07-31-neiso-72-hy-window`. **No keeper is promoted, demoted, or
re-determined by this session** — the re-gate adds visibility rows and flips
nothing (§E).

---

## §A — defect 1 (the charter defect): the plant matrix drops `plant_code <= 0` floored rows

Confirmed exactly as caiso-151 §F filed it, with three concrete sites in
`scripts/legitimacy_diagnostics.py`: `aggregate_floors_by_plant`'s
`keep = plant_code > 0`, the dispatch-side `frame[frame["plant_code"] > 0]`
filter, and the payload path's CAMPD keying (structural). Every floor riding
an interchange pseudo-unit was invisible to D-2 and D-4 — including the
`(MECH_FIRM_IMPORT, None): (0, 24)` window row caiso-151 added (necessary,
not sufficient — its own §F correction, re-verified here).

**The fix (ISO-generic, no per-ISO branch):** floored `plant_code <= 0` rows
now ride as per-unit pseudo-plant rows keyed `"u:<unit_id>"`; unfloored ones
(economic bands, export sinks, seam rows) stay excluded so no denominator
moves. Their dispatch is scored under the pre-registered **floor-energy
convention** (`dispatch := min_gen`, every path): the committed artifact
reports the MANDATED floor energy — path-independent (the #1488/G-06 lesson),
computable from committed data, and for CAISO exactly the caiso-151 §C
exposure statistic. The true at-floor dispatch (caiso-151 §F's 15.47 of
22.68 TWh, CAISO 2024) remains a probe-level statistic on unaggregated LP
rows — a DIFFERENT, narrower number; both definitions are now stated wherever
one is quoted. D-1 is untouched: it is a model-vs-CAMPD shape test and a
boundary tranche has no CAMPD actual (scoped out with this reason, per the
pre-registration).

**Gate invariance is structural and was verified, not assumed:** the new D-2
rows carry class `""` (excluded from the gated summary by the existing #1488
rule) and mechanism `firm_import` ∈ `NON_THERMAL_MECHS` ∪
`calibration_verdict.FORCED_EXEMPT_MECH_NAMES`; the new D-4 rows ride the
all-hours window (off-window ≡ 0). Five new unit tests pin this (including
"pseudo rows report but never gate D-2").

## §B — the census (pre-registered populations, measured with the HEAD scorer first)

Per keeper bundle × year, floors from the standing G-06 reconstruction:

| ISO | dropped floored rows (P1) | floor MW (by year) | TWh/yr | P3 unfloored pc≤0 | P4 class labels | P5 window gaps |
|---|---|---|---|---|---|---|
| CAISO | 0 on the UNTHREADED rebuild — **the §C defect**; 2 firm tranches on faithful floors | see §D | 17.94 / 22.68 / 22.49 | 8 | all `""` | none |
| MISO | 1 (`MISO-West_Manitoba_firmhydro`) on the UNTHREADED rebuild — **a hallucination, §C** | 726 / 531 / 224 | (6.36 / 4.65 / 1.96 — NOT the keeper's, §C) | 48 → 64 threaded | all `""` | none |
| NYISO | 1 (`NYISO_external_HQ_hydro`) | 900 flat | 7.884 / 7.884 / 7.884 | 12 | all `""` | none |
| ERCOT | 0 (no import node; `priced_interchange: False`) | — | 0 | 0 | — | — |
| NEISO | 0 (`priced_interchange: False` — HQ interchange rides demand) | — | 0 | 0 | — | — |
| PJM | S3-BLOCKED empirically (`data/raw/pjm-da-virtuals/` uncommitted); STATIC census: no firm-floor config exists on any PJM neighbor and no firm-import flag in the keeper meta → expected 0 | — | — | — | — | — |

Stop rule S2 never fired (every P1 row carries an empty class — no gated
denominator is touched anywhere). P5 is empty (`firm_import` has its
caiso-151 window row). The PJM block consumed two REGENERABLE `data/clean`
partitions first (`transfer-interface-limits`, `ramp-capability` — both
regenerated this session via `scripts/regenerate_clean.py`) before landing on
the documented uncommitted-raw hazard; the G-06 CI recompute has the same
blind spot there (notes-and-skips).

## §C — defect 2 (found by the census): the floors rebuild drops the generic override channel

`load_or_rebuild_floors` filtered `meta.json` keys against `run_year`'s
signature with only `{"commitment": "commitment_enabled"}` renamed — so the
generic override channels (`coal_prb_sigmoid_overrides` →
`prb_overrides`, `coal_bit_sigmoid_overrides` → `bit_overrides`,
`coal_bit_passthrough_sigmoid` → `coal_bit_sigmoid`; the exact
`replay_keeper._REMAP` mapping) were silently DROPPED from every floors
reconstruction. Consequences, measured on the six keeper metas:

* **CAISO's firm-import trio rides ONLY in that channel**
  (`caiso_firm_import_shape` / `_selfschedule` / `_selfsched_clip` — the
  caiso-150 §E2 "silent trap", now measured on the G-06 path caiso-151 §C
  never tested): the unthreaded rebuild carries ZERO firm floors, so even a
  fixed aggregation had nothing to show for CAISO.
* **The unthreaded rebuild HALLUCINATES MISO's Manitoba block**: the channel
  arms `miso_manitoba_seam` (miso-74), which REPLACES the legacy firm block
  with a two-way priced seam and "drops the Manitoba entry from
  firm_imports". Unthreaded, the rebuild fell back to the legacy block +
  floor (6.36/4.65/1.96 TWh) — floors the keeper does not have. **The
  handoff premise "the same hole hides MISO's Manitoba block" is therefore
  STALE for the current keeper: MISO has NO firm-import exposure**, and its
  committed artifact is correct as committed.
* Five of six keepers arm floor-affecting mechanisms through the channel
  (CAISO: hydro_ror_split / hydro_min_flow_floor / chp_steam_floor_p25 +
  the firm trio; MISO: st_gas_mustrun_per_plant + regulated take-or-pay;
  NYISO: the gas-bridge legs + reliability_floor_overrides +
  hydro_min_flow_floor; PJM: cc_mustrun_per_plant; ERCOT:
  gas_st_netload_drag + ercot_coal_min_config_floor; NEISO: none), so every
  rebuild-path regen at those five ISOs would have reconstructed floors with
  keeper mechanisms missing. The A1a inventory (scratch ladder) measured the
  artifact-level cost: e.g. MISO's committed `st_gas_mustrun_per_plant`
  8.07/8.41 TWh rows read 0 on the unthreaded regen.

**Fixed:** `REBUILD_META_RENAMES` threads the three channels (unit test
asserts consistency with `replay_keeper._REMAP` against `run_year`'s
signature). Keys that remain unmapped are price/demand-side with no
`min_gen` stamp (ERCOT price overlays, `strict_demand_profile`,
`btm_backfill_year`, `td_loss_factor`, provenance blocks) — enumerated as
the rebuild's residual fidelity limit, absorbed by G-06's existing 2.5 pp
tolerance. With threading, the rebuild reproduces every committed GATED
material-class D-2 share at CAISO (max |Δ| 0.0001 after the bridge
subtraction) and MISO (max |Δ| 0.0006) — the A1b ladder measurement.

## §D — defect 3 (exposed by the A1b gate): solve-state floors are unrebuildable, so the P0-bridge family gets the G-06 carve-out and the artifact regen uses replay floors

`run_year(fleet_only=True)` has no P0/P1 solution, so it can NEVER rebuild
the P0-run-pattern commitment-bridge family (`ra_mustoffer_bridge`,
`gas_commitment_bridge`, `nyiso_gas_commitment_bridge`,
`miso_coal_night_floor` — one shared detector,
`model.commitment.caiso_ra_mustoffer_min_gen`) nor the post-fleet-exit
nuclear/hydro/CHP floor applications. Measured consequences:

* **nyiso109's committed CC_REGULAR gated share carries 5.31 / 3.14 / 2.5+ pp
  of `nyiso_gas_commitment_bridge` forcing** that no rebuild reproduces —
  the full `--keepers` G-06 recompute, which subtracted ONLY the CAISO RA
  leg, would false-FAIL a faithful keeper. **Fixed:** `BRIDGE_MECHS` widens
  the committed-side subtraction to the family (with a test). The fast
  per-PR CI gate (`--no-d2-recompute`) never exercised this, which is why it
  was latent.
* A rebuild-sourced artifact regen would REPLACE committed real-floor truth
  (bridge rows, nuclear/hydro/chp detail, `hydro_min_flow` D-4 rows) with a
  lossy reconstruction — **A1b failed, exactly as pre-registered, and NO
  rebuild-sourced regen shipped** (addendum 1 §C). Addendum 2 upgraded the
  instrument: in-place full-span keeper REPLAYS (rule-15's unit-level-question
  license) regenerate the real `floors/<year>_P1.npz` + dispatch parquets,
  gated by D-13 byte-identity of every committed bundle file.

**Replay result: D-13 FAILED — the keeper solve does not reproduce in this
container, and the failure is PRECISELY MEASURED.** The in-place caiso153
replay solved 2023 (P0 244 s + P1 249 s) and its persist rewrote two
committed sidecars. Value-level comparison against git HEAD:
`hourly/system_2023.parquet` **byte-identical** (max value delta 0 — same
duals, same prices, same served load), while `class_hourly_2023` and
`storage_2023` moved by up to **1,997 / 1,516 MW** in single (class, hour)
cells at identical shapes. That is the degenerate-optimum signature: HEAD (or
this box's numerics stack) lands a DIFFERENT equal-cost vertex of the same
LP. The P0-pattern bridges are detected from the P0 SOLUTION, so
replay-sourced floors are not the keeper's floors wherever the vertex
drifted — exactly what D-13 exists to catch (and caiso-154 §H's
"reproductions are not a standing guarantee", now measured on a solve).
Actions per addendum 2 §C: the replay was killed before any 2024 write, the
two clobbered sidecars were restored byte-exact from git, the replay's
`dispatch/` + `floors/2023_P1.npz` were deleted (so no future session
mistakes drifted floors for keeper floors), and the **NYISO replay was NOT
attempted** — its bridge has the same P0-state dependence, so the same gate
would fire; spending ~50 min to re-measure it was declined and is recorded
here as a deliberate scope decision, not a silent skip.

The firm-tranche floors themselves are vertex-INDEPENDENT (fleet-level,
availability × config), which the record shows twice over: the replayed 2023
P1 floors and the threaded REBUILD both carry the same two CAISO tranches
(`WECC_PNW_PNW_hydro_base` + `WECC_DSW_DSW_solar_PV`) at **17.938 / 22.684 /
22.494 TWh** — caiso-151 §C's clipped exposure to the 3rd decimal (gate A4,
two independent reconstructions).

## §E — the re-gate: verdicts

**No committed `legitimacy_diagnostics.json` changed this session, because
BOTH pre-registered regen instruments failed their gates honestly**: the
threaded rebuild fails A1b (it cannot carry the P0-bridge /
post-fleet-exit floors the committed artifacts truthfully embed — replacing
them would trade committed truth for a lossy reconstruction), and the replay
fails D-13 (§D). The committed artifacts remain canonical, and therefore:

* **Every keeper's criterion profile and determination is UNCHANGED** — the
  A3 baseline (`_xiso3_forced_share_d4_census.py`, re-run in-session against
  the committed artifacts: all six C8 PASS, PJM/MISO grounded-above-budget,
  determinations matching FINDING-xiso3) is also the exit state. **Stop rule
  S1 never fired. No keeper flips, is demoted, or is promoted.**
* The scored ladder still establishes the rubric-invariance claim the
  pre-registration made: on the regenerated (scratch) artifacts the new rows
  are class-`""` / exempt-mechanism D-2 rows and all-hours-window D-4 rows —
  no D-2 summary row is added or altered, so C8 cannot move; C7 reads D-1,
  untouched by the fix (the HEAD-vs-committed D-1 drift measured in-session
  is confined to C7-exempt CHP classes with zero verdict changes and rides
  ANY future regen, not this fix).
* **Where the visibility lands:** every FUTURE bundle generated the standard
  way — the artifact written in-session right after the solve, from the
  bundle's real `floors/*_P?.npz` (the flow that produced every current
  keeper's artifact) — now carries the firm-import D-2/D-4 rows
  automatically. The same holds for any bundle whose floors carry no
  solve-state mechanism, via the fixed threaded rebuild. The three current
  keepers' artifacts gain the rows at their next natural regeneration (next
  solve / next promotion in their lanes); nothing needs to be re-solved for
  it, and nothing was.

## §F — what remains open (filed, not fixed)

* **PJM's empirical census** awaits a `fetch_pjm_da_virtuals.py` fetch in a
  PJM-lane session (static census: no exposure expected). The G-06 recompute
  shares the blind spot.
* **The rebuild's residual unmapped keys** (§C list) — price/demand-side;
  a session that needs bit-faithful rebuilt floors for those paths should
  extend the map with the same test pattern.
* **`MECH_NYISO_SELFSUPPLY` has no `D4_WINDOWS` row** (its floors ride REAL
  plants, pc > 0, so it is NOT part of this defect — but its HB14-21 window
  (`inject_nyiso_local_selfsupply` docstring, floor-rederive 2026-07-05) has
  no registry declaration). Not minted here (xiso-3 discipline: a rule-17
  declaration needs its own per-ISO driver evidence); it is non-thermal /
  never gated, so nothing is exposed today.
* The latent D-4 coverage map from xiso-3 §5 is unchanged by this session.

## §G — DO-NOT-REDO (new, binding)

* **Do NOT quote the census's MISO 6.36/4.65/1.96 TWh as a keeper exposure**
  — it is the unthreaded rebuild's hallucination of the pre-miso-74 legacy
  block (§C). MISO's current keeper has NO firm-import floor; re-opening
  that requires a MISO-lane session with new evidence, not this census.
* **Do NOT re-measure the plant-set drop by hand** — re-run
  `_caiso155_plant_set_census.py` (fix-aware: it asserts the drop is GONE
  when the fix is present, and re-measures it when run on pre-fix code).
* **Do NOT narrow `BRIDGE_MECHS` back to the RA leg**, and do NOT read a
  G-06 pass under the family subtraction as evidence the bridges reproduce —
  they are excluded precisely because they cannot.
* **Do NOT treat the pseudo-row floor-energy TWh as at-floor dispatch** —
  they are different statistics (§A); the artifact notes say so per year.
* **Do NOT regenerate a keeper's `legitimacy_diagnostics.json` from the
  fleet_only rebuild when its floors carry bridge/solve-state mechanisms** —
  the A1b ladder is the evidence; use replay floors (addendum 2) or the
  in-session floors of a fresh solve.
* Carried forward unchanged: ALL of FINDING-caiso154 §H, caiso-153 §G,
  caiso-152 §H, caiso-151 §H (the D4_WINDOWS entry alone is still not
  visibility — visibility now additionally requires the plant-set fix and
  faithful floors), caiso-150 §H, caiso-149 §G, caiso-148 §G, caiso-147 §G,
  caiso-146 §G, caiso-144 §G, caiso-143 §H/§I, caiso-142 §K, caiso-141,
  caiso-138 §G, caiso-137b §6, caiso-131 §10; pjm-141 D-BIN; both CAISO
  ledgered caveats untouched.

Next number: caiso-156.
