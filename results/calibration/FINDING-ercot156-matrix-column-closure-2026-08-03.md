# FINDING — ercot-156: the ERCOT matrix column is CLOSED (60 absent + 7 prose-only + 31 armed-no-cell → 0/0/0), zero new rows, zero verdicts minted

> Session ercot-156, 2026-08-03. Branch `claude/ercot-matrix-column-closure-umdyn2`.
> **No LP, no solve, keeper UNCHANGED at `2026-08-02-ercot150b-zonal-anchor`.**
> Holdouts untouched (no year touched at all — this is a bookkeeping census,
> rule 28(c)). Instrument: `scripts/mechanism_matrix_gap_sweep.py --iso ERCOT`,
> before/after committed in `results/calibration/_matrix_gap_sweep_ERCOT.json`.

## §1 — what was measured

On current main, ERCOT was the largest remaining rule-28(c) debt: of 84
`ercot_*` `ScenarioConfig` fields, **60 absent** from the mechanism matrix, **7
prose-only** (named only inside some other row's note, so the CI
mention-anywhere gate passes but no cell records anything for them), and **31
armed on the current keeper with no cell anywhere** — the exact shape
(nyiso-112's "227-3 gap") that once hid a promotable mechanism, and the shape
CI cannot see because `check_mechanism_matrix.py`'s diff gate fires only on
fields added in the same PR.

After this session: **0 absent, 0 prose-only, 0 armed-no-cell.** Ratchet
baseline (`docs/codebase-site/data/mechanism-matrix-gaps.json`) ERCOT
**61 → 0**; the full-six rewrite also picked up shrinkage other lanes had
already earned on main (CAISO 37→31, PJM 21→15, NEISO 15→10, MISO 12→11,
NYISO 0→0). No ISO's list grew.

## §2 — how, and why no verdict was minted

Every one of the 67 fields adjudicated to a **sub-scalar / leg of an existing,
already-adjudicated family row**, and was closed by naming it **literally** in
that row's `def` — the checker's documented escape hatch and the exact template
NYISO's nine `nyiso_gas_bridge_*` fields used (nyiso-114 §4). **No genuinely
new mechanism was found**, so no new row was added and no `U` cell was needed:
the census's watch-item — a live-but-invisible, armed-or-armable,
never-adjudicated lever (the nyiso-112 shape) — did **not** occur in ERCOT's
column. Every armed field is a leg of a family whose ERCOT cell already carries
a tested verdict with a log citation.

The placement map (14 family rows):

| row (ERCOT cell) | fields registered |
|---|---|
| `ercot_multiproduct_as` (K) | `ercot_multiproduct_as_coopt` (master), `ercot_as_n_ramp`, `ercot_as_critical_frac`, `ercot_ecrs_requirement` `/_from_year`, `ercot_ecrs_conservative_deployment`, `ercot_nonreleasable_as_withholding`, `ercot_ordc_total_reserve`, `ercot_load_resource_reserve` `/_from_year`, `ercot_reserve_supply_cap_from_year`; forecast analogues `ercot_reserve_supply_forward`, `ercot_as_forward_requirement`, `ercot_thermal_as_endogenous` (14) |
| `measured_offer_surface` (K) | `ercot_offer_surface_conditional`, `_cleared_share` `/_path` `/_rt` `/_rt_mode` `/_rt_path` `/_state` `/_state_path` `/_steam`, `_netload_pcts`, `_min_bin`, `_price_cap_frac`, `_binned_path`, `_lowcurve` `/_path` `/_floorscoped`, `ercot_ct_offer_surface`, `ercot_shoulder_online_span` `/_path` (19) |
| `storage_measured_anchors` (K) | `ercot_storage_as_reserve` `/_from_year`, `_deployment` `/_from_year`, `_product_credit`; G5 legs `_endogenous`, `_duration_gate` (7) |
| `zonal_gas_basis` (K) | `ercot_west_netload_gas_shape`, `ercot_west_gas_delivered_floor`, `_firm_basis`, `_collapse_freq`, `_endogenous_collapse`, `ercot_gas_delivered_floor_basis`, `ercot_gas_contract_haircut` (7) |
| `online_capacity_envelope` (R) | `ercot_online_capacity_envelope_extreme` `/_measured`, `ercot_ordc_only_scarcity`, `ercot_commitment_posture` `/_min_load_frac` (5) |
| `dam_availability_rebasis` (K) | `ercot_thermal_dam_availability_hourly` `/_plant` `/_coal` (3) |
| `pjm_midcurve_belt` (U) | `ercot_offer_surface_midcurve_conditional` `/_path` (2) |
| `wtx_curtailment_driver` (K) | `ercot_wtx_curtail_depth_wind` `/_solar` (2) |
| `gas_offer_net_revenue_margin` (K) | `ercot_offer_hrmult_ep_rebasis` `/_bands` (2) |
| `legacy_p2` (G) | `ercot_as_aware_commitment`, `ercot_as_adequacy_frac` (2) |
| `campd_outage_windows` (K) | `ercot_noncampd_plant_availability` (1) |
| `ordc_scarcity_overlay` (R) | `ercot_market_design` (1) |
| `ercot_faststart_pool_offer` (O) | `ercot_faststart_pool_offer_path` (1) |
| `gas_commitment_bridge` (K) | `ercot_gas_bridge_online_hours` (1) |

The only verdict-bearing text added is **transcription of adjudications already
on the record**, each with its citation — never a new judgment:

* `ercot_commitment_posture` (+ its measured 0.574 LSL/HSL p50 scalar):
  probe-adjudicated **price-INERT**, run
  `2026-07-18-ercot83-commitment-posture-probe` (calibration-log archive).
* `ercot_shoulder_online_span` `/_path`: built and **rejected-as-armed** at
  ERCOT-89 (2026-07-19), merged default-off.
* `ercot_offer_hrmult_ep_rebasis` `/_bands`: **ERCOT-118/119 ordinary
  rejections** (`2026-07-27-ercot118-gas-rebasis-joint` /
  `ercot119-econ-rebasis-joint`). This closes the standing gap **ERCOT-138
  itself filed** ("solve-affecting fields with no matrix row — a rule-26(c)
  gap predating this lane"), repeated open in four later entries.
* `ercot_noncampd_plant_availability`: keeper since
  `2026-07-16-ercot71-noncampd-availability`.

Cell changes: **exactly one** — the audit row `matrix_gap_census` ERCOT
`O → K` (an audit-row status, "column enumerated and closed", not a mechanism
verdict; NYISO's `K` at nyiso-114 is the precedent). Every mechanism row's
6-char cell string is byte-unchanged.

## §3 — what was deliberately left open

The sweep still reports **20 live-but-invisible** fields for ERCOT — all
**shared-stem** (cross-ISO) fields that ERCOT bundles set away from default
with no matrix mention: `weather_year`, `wefor_residual` `/_groups`,
`coal_prb_passthrough_floor` `/_tiered`, `coal_prb_follower_floor`,
`coal_lignite_passthrough_floor` `/_ceil`, `coal_drop_pof`,
`storage_as_commitment`, `gas_st_startup_cost` `/_spread`, and similar. These
are armed identically across multiple ISOs' keepers; registering them touches
family rows whose cells span all six columns, so they are a **cross-ISO
hygiene lane** (like xiso-1/2/3), not one column's session. Filed in the
`matrix_gap_census` note; the ISO-stem ratchet does not track them, so the
baseline claim ("ERCOT 0") is exact for what the ratchet enforces.

Also NOT touched, per the DO-NOT-REDO list: the offer-dispersion arm (R,
ercot-155), item 6 (I, ercot-146), the items-5/6 reopen route (refused,
ercot-147), `ordc_scarcity_overlay` (R). No R/I/G cell was re-tested; no
struck framing is quoted forward.

## §4 — governance

* Rule 28(b): matrix updated **this session**, header stamped, §5.1 of
  `docs/mechanism-testing-matrix.md` stamped, `docs/calibration-log/ercot.md`
  entry added.
* Rule 28(d)/25: zero verdicts minted; a census mints a `U` at most, and this
  one needed none.
* Rule 15: nothing to register — no run was produced (no LP, no solve).
* Rule 22: no year touched, freeze respected trivially.
* Guards run before push: `check_mechanism_matrix.py` PASS,
  `check_registry_payload_parity.py` PASS (see session log).
* Next-largest column: **CAISO (31 after this baseline refresh)** — its own
  lane's session, per the one-ISO-per-lane discipline.
