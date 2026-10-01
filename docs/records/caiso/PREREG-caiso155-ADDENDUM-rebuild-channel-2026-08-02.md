# PREREG-caiso155 ADDENDUM — the census found a SECOND harness defect: the floors rebuild drops the generic override channel, so it must be fixed BEFORE any artifact regen. Committed before any A1/A2 number is computed

**Session:** caiso-155. **Date:** 2026-08-02. Amends
`PREREG-caiso155-diagnostics-plant-set-2026-08-02.md` §3–§4 only; populations
(§2), stop rules (§5) and deliverables (§6) are unchanged. Pattern:
`PREREG-caiso152-ADDENDUM-corpus-2026-08-01.md` (a registered input changed
mid-session → addendum before dependent numbers).

## A. What the census measured before this addendum (fact, already in the probe transcript)

The pre-registered census ran clean at five ISOs (P4 empty everywhere, P5
empty, S2 never fired) and produced one result the fix design of §3 did not
anticipate: **CAISO's P1 is EMPTY on the rebuild path** — its 6 import
tranches + 2 export sinks appear with NO floor — while MISO
(`MISO-West_Manitoba_firmhydro`, 6.36/4.65/1.96 TWh) and NYISO
(`NYISO_external_HQ_hydro`, 7.884 TWh flat) carry exactly the expected
firm-import rows. PJM is S3-BLOCKED on the documented uncommitted-raw hazard
(`data/raw/pjm-da-virtuals/`, after this session regenerated the two
regenerable `data/clean` partitions it also needed); ERCOT and NEISO carry no
`plant_code <= 0` row at all.

**Root cause, measured:** `load_or_rebuild_floors` filters `meta.json` keys to
`run_year`'s signature with `rename = {"commitment": "commitment_enabled"}`
only. The generic override channels are therefore DROPPED — the rebuild log
prints them: `coal_prb_sigmoid_overrides`, `coal_bit_sigmoid_overrides`,
`coal_bit_passthrough_sigmoid`. `run_year` accepts all three under different
names (`prb_overrides` / `bit_overrides` / `coal_bit_sigmoid` —
`scripts/replay_keeper.py::_REMAP` is the existing mapping precedent), and
CAISO's firm-import arming flags (`caiso_firm_import_shape`,
`caiso_firm_import_selfschedule`, `caiso_firm_import_selfsched_clip`) ride
ONLY in that channel (the caiso-150 §E2 "silent trap", re-confirmed here on
the G-06 reconstruction path, which caiso-151 §C did not test).

**Blast radius beyond firm imports (inventoried from the six keeper metas):**
the dropped channel carries floor-affecting mechanisms at FIVE of six keepers —
CAISO (`hydro_ror_split`, `hydro_min_flow_floor`, `chp_steam_floor_p25`, the
firm-import trio), MISO (`st_gas_mustrun_per_plant`,
`coal_bit_committed_takeorpay`, `coal_committed_takeorpay_regulated`,
`st_gas_mustrun_p25_level`), NYISO (`nyiso_gas_commitment_bridge` + its
min-run legs, `reliability_floor_overrides`, `hydro_min_flow_floor`), PJM
(`cc_mustrun_per_plant`, `coal_sub_passthrough_floor`), ERCOT
(`gas_st_netload_drag`, `ercot_coal_min_config_floor`, coal passthrough
floors). NEISO's channel (3 keys) carries none. So EVERY rebuild-path
artifact regeneration at those five ISOs would have reconstructed floors with
keeper mechanisms missing — regenerating committed artifacts from that
rebuild would replace real-floor truth with an unfaithful reconstruction.
(The committed artifacts themselves were generated in-session with the real
`floors/*_P?.npz` still on disk, so they are NOT contaminated; the exposure
is every LATER rebuild-path consumer: the G-06 recompute's fidelity and this
session's re-gate.)

## B. Amended fix design (§3 gains one part; nothing else changes)

**Part 0 (NEW, must land before any regen):** extend the rebuild's rename map
with the three run_year-target entries —
`coal_prb_sigmoid_overrides → prb_overrides`,
`coal_bit_sigmoid_overrides → bit_overrides`,
`coal_bit_passthrough_sigmoid → coal_bit_sigmoid` — so generic-channel
overrides thread into the reconstruction exactly as they thread into a replay.
(`commitment_screen_coal` already passes under its own name.) A unit test
asserts the map covers every channel key `replay_keeper._REMAP` maps to a
`run_year` parameter, so the two reconstructions cannot silently diverge
again. Keys that remain dropped after this (the ERCOT price-overlay flags,
`strict_demand_profile`, `btm_backfill_year`, `td_loss_factor`, provenance
blocks) are price/demand-side with no `min_gen` stamp, are enumerated in the
FINDING as the rebuild's residual fidelity limit, and stay absorbed by G-06's
existing tolerance — widening beyond the three renames is out of scope.

Parts 1–5 of §3 (the `u:<unit_id>` pseudo-plant aggregation, unchanged
dispatch filters, the floor-energy convention, D-1 scope-out, tests) are
unchanged.

## C. Amended acceptance gates (§4's A1/A2 split into a measured ladder)

* **A1a (report-only, quantifies defect 2):** regen per keeper with the HEAD
  scorer (unthreaded rebuild) vs the committed artifact — the per-ISO drift
  inventory. No pass bar; it is the measurement of what the unthreaded
  rebuild loses.
* **A1b (the reproduction baseline, pass bar):** regen with Part 0 ONLY
  (threading fixed, aggregation still HEAD) vs the committed artifact. Must
  land within G-06's named reconciliations: material-class D-2 gated shares
  within `D2_VERIFY_SHARE_TOL` (2.5 pp) after excluding the committed-side
  `ra_mustoffer_bridge` contribution; D-4 rows reproduced (same mechanism
  set; off-window shares within 0.5 pp); D-1 rows equal to committed within
  rounding (D-1 does not read floors, so any D-1 drift is a hard stop).
  Failing A1b = the rebuild is still unfaithful → stop, diagnose; NO
  artifact regen ships.
* **A2 (additivity, unchanged in spirit):** full-fix regen vs the A1b regen —
  byte-identical except ADDITIONS (new D-2 rows with class `""` / exempt
  mechanisms, new D-4 rows, notes).
* **A3 / A4 / A5:** unchanged. (A4's CAISO anchor now actually engages,
  since Part 0 is what makes the CAISO firm floor reconstructible at all.)

The shipped artifacts are full-fix regens, and they ship only if A1b and A2
and A3 all pass; any keeper whose A3 flips fires S1 unchanged.

## D. What this addendum does NOT license

No solve. No registration. No rule-22 marker. No new `D4_WINDOWS` entry. No
change to `replay_keeper.py` (its map is already correct), to any derive, or
to any `ScenarioConfig` field. The PJM S3 block stands (static census; no PJM
regen this session); ERCOT/NEISO need no regen (empty populations) unless
A1a/A1b measurement shows their committed artifacts are ALSO stale against a
faithful rebuild — in which case that is REPORTED, not silently repaired
(their regen would be additive-empty and is permitted under the same gates).
