# FINDING — caiso-161: the CAISO matrix column is CLOSED (31 absent + 2 prose-only + 18 armed-no-cell → 0/0/0), zero new rows, zero mechanism verdicts

> Session caiso-161, 2026-08-03. Branch `claude/caiso-matrix-column-closure-wgflbo`.
> **No LP, no solve, keeper UNCHANGED at `2026-08-03-caiso156-meter-screen-b`.**
> Holdouts untouched (no year touched at all — this is a bookkeeping census,
> rule 28(c)). Instrument: `scripts/mechanism_matrix_gap_sweep.py --iso CAISO`,
> before/after committed in `results/calibration/_matrix_gap_sweep_CAISO.json`.

## §1 — what was measured

On current main (after the ercot-156 baseline refresh) CAISO was the largest
remaining rule-28(c) debt: of **61** `caiso_*` `ScenarioConfig` fields,
**31 absent** from the mechanism matrix, **2 prose-only** (named only inside
some other row's `note:`, so the CI mention-anywhere gate passes but no cell
records anything), and **18 armed on the current keeper with no cell anywhere**
— the nyiso-112 "227-3" shape that once hid a promotable mechanism, and the
shape CI cannot see because `check_mechanism_matrix.py`'s diff gate fires only
on fields added in the same PR.

After this session: **0 absent, 0 prose-only, 0 armed-no-cell.** Ratchet
baseline `docs/codebase-site/data/mechanism-matrix-gaps.json` CAISO **31 → 0**;
no other ISO's list grew (ERCOT 0, NYISO 0, PJM 15, MISO 11, NEISO 10
unchanged; `--write-baseline` refuses a partial-ISO write, so all six were
re-swept).

## §2 — the mechanical cause of most of the CAISO gap

**Abbreviated short-forms in a row's `def`.** The rule-28(c) coverage test
matches a field **literally** (or by its ISO-stripped stem) in the row text
*before* `note:`. Four ARMED keeper fields were sitting in
`gas_commitment_bridge`'s def written as `caiso_ra_startup_bridge /
_bridge_decommit / _bridge_startup_aware / _startup_trajectory /
_bridge_curtailment_release` — the leading `caiso_ra` elided — so
`caiso_ra_bridge_decommit`, `caiso_ra_bridge_startup_aware`,
`caiso_ra_startup_trajectory` and `caiso_ra_bridge_curtailment_release` all
read **absent** while three of them shape the keeper. `solar_deliverability`
had the same defect (`_endogenous_spill`). Expanding to literals fixed six
fields and changed nothing about any verdict.

This is worth carrying forward: the abbreviation reads naturally to a human and
is invisible to the checker. Registrations must be written as full literals —
including in prose *about* the gap (this session's own census note initially
wrote `ct_drag_cap / _intercept / _slope_per_gw` and reproduced the bug).

## §3 — placement map (10 existing rows + 1, ZERO new rows)

Every one of the 33 fields adjudicated to a **sub-scalar / leg / superseded
predecessor of an existing, already-adjudicated family row**, closed by naming
it literally in that row's `def` — the checker's documented escape hatch and
the template ercot-156 and nyiso-114 used.

| row (CAISO cell) | fields registered |
|---|---|
| `gas_commitment_bridge` (K) | `caiso_ra_bridge_decommit`, `caiso_ra_bridge_startup_aware`, `caiso_ra_startup_trajectory`, `caiso_ra_bridge_curtailment_release` (literal expansions); superseded predecessor `caiso_gas_commitment_floor` + `caiso_gas_floor_frac` (6) |
| `import_hub_pricing` (K) | `caiso_per_hub_intertie`, `caiso_perhub_firm_base`, `caiso_dsw_surplus_clean`, `caiso_dsw_overnight_clean`, `caiso_dsw_daytime_clean`, `caiso_dsw_daytime_evening_trim`, superseded `caiso_bidir_intertie`, `caiso_import_gas_coupling`, `caiso_import_solar_shape` + its scalars `caiso_solar_shape_nl_hi_pct` / `_lo_pct` (11) |
| `solar_deliverability` (K) | `caiso_solar_endogenous_spill` (literal), `caiso_solar_deliverability_k`, `caiso_solar_deliverability_floor`, `caiso_solar_cap_at_delivered` (4) |
| `measured_offer_surface` (K) | `caiso_offer_surface_measured` (was prose-only), `caiso_offer_surface_conditional`, `_netload_pcts`, `_min_bin`, `_price_cap_frac`, `_binned_path` (6) |
| `gas_hub_basis_overlay` (K) | `caiso_citygate_spot_level`, `caiso_citygate_flow_date` (2) |
| `storage_measured_anchors` (K) | `caiso_storage_as_reservation`, `caiso_charge_allocation_schedule` (2) |
| `measured_interface_limits` (K) | `caiso_corridor_atc_forward`, `caiso_asymmetric_path_ratings` (2) |
| `reference_price_interface` (U) | `caiso_reference_price_seam` (was prose-only), `caiso_intertie_reference_price` (2) |
| `ordc_scarcity_overlay` (G) | `caiso_scarcity_import_headroom` (1) |
| `legacy_p2` (.) | `caiso_lcr_commitment_credit` (1) |
| `lcr_tsl_published` (. → **U**) | `caiso_per_year_import_caps` (1) |

**Cell changes: exactly two, both rule-28(d)-admissible.** The audit row
`matrix_gap_census` CAISO `O → K` (an audit-row status — "column enumerated and
closed" — not a mechanism verdict; ERCOT's `K` at ercot-156 and NYISO's at
nyiso-114 are the precedent), and `lcr_tsl_published` CAISO `. → U` (a census
may mint a `U` and nothing else). Every mechanism row's 6-char `cells` string is
otherwise byte-unchanged; every `fc:` string is byte-unchanged.

## §4 — verdict text is transcription only

No judgment was made here. Each verdict-bearing sentence added carries the
citation of an adjudication already on the record:

* `caiso_storage_as_reservation` — probe-adjudicated **INERT** at caiso-74 (run
  `2026-07-11-caiso-74-storage-as`); the entire AS-award family subsequently
  refuted by arithmetic at caiso-127/129.
* `caiso_charge_allocation_schedule` — built and **REJECTED** at caiso-104 on
  its own pre-registered gates (runs `2026-07-20-caiso-104-m1-v1` /
  `-m1-v2`, both registered PROBE/REJECTED).
* `caiso_scarcity_import_headroom` — the **caiso-137b DO-NOT-REDO** binds that
  treating it (and `caiso_scarcity_pricing`) as live in a CAISO *backcast* is
  byte-identical by construction; do not solve an A/B on it. Consistent with
  the row's existing CAISO `G`.
* `caiso_gas_commitment_floor` / `caiso_gas_floor_frac` — rule-13
  `[R-MEASURED]` inadmissible (a measured-outcome pin); `scenarios.py:2706`
  calls the RA bridge its "Step-1 replacement for the measured-outcome gas
  floor" and `:2740` calls it "the removed NG:NG floor".
* `caiso_solar_cap_at_delivered` — its own definition (`scenarios.py:5604`)
  records it as a DEFAULT-OFF DIAGNOSTIC that pins solar to a measured outcome,
  has no forward analogue, and must never be enabled in a keeper.
* keeper legs — caiso-84 (citygate spot level), caiso-87/93/94/97 (the four DSW
  clean-import depth legs), caiso-90 (citygate flow date).

## §5 — what the census actually found: six armed-looking, provably DEAD fields

This is the CAISO-specific payoff, and it inverts the watch-item. The prompt's
item 2 looks for a *live-but-invisible* lever (the nyiso-112 shape). CAISO's
column has the opposite defect: **six of the 18 "armed on the keeper" fields
are non-default in all 19 bundles' `run_config.json` yet unreadable by any code
path in the keeper's configuration.** Verified at every call site, not inferred
from the flag's prose:

| field | keeper value | why it cannot be observed |
|---|---|---|
| `caiso_gas_floor_frac` | 0.80 | sole read is inside `if getattr(config, "caiso_gas_commitment_floor", False):` — `scripts/run_calibration.py:2964-2969`; keeper has that flag `False` |
| `caiso_solar_deliverability_k` | 0.15 | both derate call sites skip on spill: `runner.py:1556-1570` gates on `not _endogenous_spill`; `scripts/run_calibration.py:272-283` early-returns on the spill branch **before** the derate. Keeper has `caiso_solar_endogenous_spill=True` |
| `caiso_solar_deliverability_floor` | 0.50 | same two call sites |
| `caiso_solar_shape_nl_hi_pct` | 30.0 | sole read is `inject_caiso_import_solar_shape` (`model/interchange/caiso.py:1748-1749`), reached only when `caiso_import_solar_shape` is on (`interchange/registry.py:154`, `runner.py:1463`); keeper has it `False` |
| `caiso_solar_shape_nl_lo_pct` | 10.0 | same |

Consequence for every future CAISO session: **a CAISO `run_config.json` is not
an inventory of what is armed.** Five of its non-default `caiso_*` entries are
dead, and one of them (`caiso_gas_floor_frac=0.80`) is carried by the *standard*
backcast recipe at `pipeline/backcast_config.py:1499` and by ~40 committed probe
drivers, so it propagates into every new CAISO run by default.

**Filed for the owner, not acted on: `caiso_gas_floor_frac` is the rule 26
`[R-DELETE]` shape.** It is the fitted scalar of a *retired,
rule-13-inadmissible* mechanism that still parses — precisely "a deprecated
parameter that still parses is a re-armable answer key". Removing a
`ScenarioConfig` field is a mechanism change and a census lane may not make one
(rule 28(d)), so it is recorded in the matrix, in §5.2 of
`docs/mechanism-testing-matrix.md`, and here.

## §6 — two never-adjudicated, armable candidates: surfaced, NOT tested

Both are rule 14 `[R-ACCURATE]` measured-over-estimate candidates that are
default-off, armed in zero bundles, and appear in **no** log entry, finding or
matrix cell anywhere in the record:

* **`caiso_asymmetric_path_ratings`** — published WECC Path Rating Catalog
  directional limits for CAISO's *internal* N-S paths (Path 15 Midway–Los Banos
  3,265 MW N→S vs 5,400 S→N; Path 26 Midway–Vincent 4,000 N→S vs 3,000 S→N)
  replacing the symmetric TTCs the reduced topology ships. The loose directions
  let the LP equalise the zones (Path 15 never binds; NP15==ZP26 byte-identical
  all years) and ship SP15 midday solar surplus north past the real 3,000 MW
  Path-26 S→N limit, suppressing the measured NP15-over-SP15 premium.
* **`caiso_per_year_import_caps`** — per-year published LCT pocket import caps
  (LA_BASIN 12,008/15,224/15,174 MW, SDGE 1,436/2,074/2,071 MW for 2023/24/25)
  replacing the static 2023 tightest-year bake the SP15 split froze in, which
  `scenarios.py:8955` itself documents as "the deferred end state".

Both are now queued in `docs/mechanism-testing-matrix.md` §5.2. **Neither is
solved here** — a census does not test levers, and folding a lever test into a
census commit is exactly what the lane forbids. A session taking either
pre-registers it as its own single-delta arm (gates + kills + no-tuning clause,
pushed *before* solving) and honours rule 16 (2023–2025 in ONE bundle).

## §7 — what was deliberately left open

The sweep still reports **5 shared-stem** fields CAISO's keeper arms with no
matrix row: `ct_drag_cap`, `ct_drag_intercept`, `ct_drag_slope_per_gw`,
`cc_outage_derate_from_top`, `chp_steam_floor_p25`. These are non-ISO-prefixed
and armed across multiple ISOs' keepers (ERCOT 14, PJM 18, MISO 17 of the same
class), so registering them touches family rows whose cells span all six
columns — a **cross-ISO hygiene lane**, not one column's session. They stay in
the baseline's `shared_armed_on_keeper` block, which is unchanged at CAISO 5.
The ISO-stem ratchet is what the "CAISO 0" claim refers to, and it is exact.

Also not touched, per DO-NOT-REDO: `energy_reserve_coopt` (`I`, caiso-144, with
an explicit DO-NOT-SOLVE), `cc_mustrun_per_plant` (`R`),
`wecc_endogenous_node` (`R`, caiso-110), `caiso_corridor_export_path` (`R`,
caiso-132), `caiso_p1_export_sink_seam` (`R`), `netload_drag_floors` (`R`). No
`R`/`I`/`G` cell was re-tested; no struck framing is quoted forward.

## §8 — governance

* Rule 28(b): matrix updated **this session**; `docs/mechanism-testing-matrix.md`
  §5.2 stamped (and its stale keeper heading corrected from caiso148 to
  caiso156 — the `.js` stamp guard does not see prose drift);
  `docs/calibration-log/caiso.md` entry added.
* Rule 28(d)/25: **zero mechanism verdicts minted.** Two cell changes, both
  admissible: an audit-row status and a single `U`.
* Rule 15: nothing to register — no run was produced (no LP, no solve).
* Rule 16: not engaged (no solve).
* Rule 22: **no year touched**, holdout spend freeze respected trivially.
* Rule 27 `[R-PUSH]`: the matrix file is ≥300 lines; the pushed blob is
  hash-verified against local after the push.
* Guards before push: `check_mechanism_matrix.py` PASS (integrity + keeper
  stamps + both ratchet legs against `origin/main`),
  `check_registry_payload_parity.py` PASS (90 runs, 0 unsynced).
* Next-largest column: **PJM (15 absent / 18 shared)**, then MISO (11/17) and
  NEISO (10/0) — each its own lane's session, per the one-ISO-per-lane
  discipline that keeps the shards conflict-free.
