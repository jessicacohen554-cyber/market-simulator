# FINDING — `caiso_ct_peaker_committed_measured` backcast→forecast fork (FR-22 GAP)

**Date:** 2026-09-04 · **Lane:** `claude/y4-caiso241-duties-nvcroc` (Y-4) ·
**Pin:** `a8464861`
**Files a GAP row for:** `caiso_ct_peaker_committed_measured`, armed in the
CAISO keeper `2026-09-03-caiso-241-b1-ctpeaker` (#4663) with no
forecast-orchestrator consumer and, until this row, no registry declaration.
**Route:** owner ruling **R-X** (2026-09-02) — the disposition that files the
fork as KNOWN and TRACKED and decides nothing about how it closes. Same route
and same class as `docs/FINDING-fr22-gap-leg2-2026-09.md` (the ERCOT
`ercot_storage_adaptive_expectation` pair and `nyiso_seam_par_attribution`).
**Discharges:** the caiso-241 promoting lane's undischarged FR-22 duty, under
the standing audit-lane exception (#4488 / board v23 job 0 precedent).
**Scope discipline:** no solve · no score · no registration · no keeper shard,
marker or freeze file touched · no matrix edit (a GAP declaration tests no
mechanism) · no test changed (`_FR22_OPEN_UNACCOUNTED` is NOT extended) · no
`BACKCAST_ONLY` claim · no forward wiring.

---

## 1. What the field does

`ScenarioConfig.caiso_ct_peaker_committed_measured` (default `False`,
`src/market_sim/config/scenarios.py:11452`) substitutes ONE band of ONE CAISO
class: `_CAISO_OFFER_CURVE["CT_PEAKER"]["committed"]` moves from the fitted
`1.35` to the measured `phys_committed = 0.991` that the band's own dict
already carries (`avg_committed_p50`,
`data/raw/reference/caiso_campd_marginal_hr_summary.csv`, n = 75, IQR
[0.969, 1.085]). Zero new literals, zero free parameters (rule 21
`[R-DOF]`) — the value is the measurement already resolved onto the band.
`econ_low` / `econ_high` / `peak` are untouched, so it is band-disjoint from
`caiso_offer_surface_measured*` (rule 19 `[R-ONE-MECH]`).

The substitution is applied in `src/market_sim/pipeline/backcast_config.py`
(signature ~1210, block ~2266–2296), on the RESOLVED band dict — CT_PEAKER
resolves a class curve, unlike the caiso-239/240 siblings whose plants are
bypassed out of `offer_curve_by_group`, so there is no consumer-side limb.
Arming it for any ISO but CAISO, or on a band carrying no `phys_committed`
key, raises `ValueError` — never a silent fall back to the fitted value
(rule 25 `[R-ISO-SCOPE]`).

## 2. The fork (measured, at this pin)

| site | role in `SOURCE_ROLES` | names the field |
|---|---|---|
| `src/market_sim/pipeline/backcast_config.py` | `backcast` | yes — the substitution |
| `scripts/run_calibration_full.py`, `scripts/run_calibration.py` | `backcast` | yes — CLI threading |
| `src/market_sim/config/scenarios.py` | `bookkeeping` | yes — declaration + flag list |
| `src/market_sim/runner.py` (the forecast orchestrator) | `forecast` | **no** |
| anything else under `src/market_sim/` | shared | **no** |

`grep` over `src/market_sim/` returns no reference outside
`backcast_config.py` and `scenarios.py`. `backcast_config.py` is the backcast
config builder and is declared `backcast` in `SOURCE_ROLES`, so it supplies no
forecast evidence by construction; `scenarios.py` is `bookkeeping`, so naming
the field there is not consumption. The keeper arms it
(`results/calibration/caiso241_b1_ctpeaker_committed/run_config.json`:
`scenario_config.caiso_ct_peaker_committed_measured = True`; years
[2023, 2024, 2025]).

**Consequence.** A forecast run built from the keeper's config records the flag
as armed and never applies the band substitution: `offer_curve_by_group` IS
read by shared builders (`data/fleet/campd_bins.py`, `data/offer_curves.py`),
but the CAISO per-ISO merge curve `_CAISO_OFFER_CURVE` and every substitution
into it live in `backcast_config` — the offer-curve-base consolidation
deliberately left the per-ISO merge curves there
(`pipeline/offer_curve_base/__init__.py` module docstring). CT_PEAKER would
price its min-load block at the fitted 1.35 in a forecast and at the measured
0.991 in the backcast. That is the nyiso-102 defect class this registry exists
to catch.

## 3. Why `GAP` and not `BACKCAST_ONLY`

`BACKCAST_ONLY` asserts *backcast-only by design — the forecast path must NOT
reach it*, the rule-13 `[R-MEASURED]` claim that the measured input has no
forward analogue. **The code asserts the opposite, in two places, and the
assertion is load-bearing:**

- The field is **deliberately absent** from
  `scenarios._BACKCAST_ONLY_OVERLAY_FIELDS`, and its docstring says so
  explicitly: *"NOT IN `_BACKCAST_ONLY_OVERLAY_FIELDS`, and deliberately so —
  like its caiso-239 sibling and unlike caiso-240's. `avg_committed_p50` is a
  measured PHYSICAL heat-rate ratio that regenerates for a forward year from
  CAMPD conduct and responds to fleet change, so it is admissible in both
  modes (rule 13)."*
- Its caiso-240 sibling `caiso_st_gas_peak_measured` IS registered there, on
  the stated ground that it arms measured **BID** conduct keyed to one year's
  OASIS record. The physical/bid split is the registry's own discriminator,
  and this field sits on the physical side.

A `BACKCAST_ONLY` row would therefore assert a non-regenerability the code
denies, on no evidence — and `check_forecast_parity.py` does not verify the
by-design claim (it only verifies the row is not stale, i.e. not since wired
forward), so the assertion would be this lane's, unbacked. The registry
requires evidence for that disposition and there is none to give.

`PARAMETER_OF` is also unavailable: unlike
`caiso_offer_surface_measured_ungrounded`, which raises unless its parent is
armed and so inherits the parent's filed gap, this block requires no other
CAISO offer-surface flag, is band-disjoint from all of them, and is applied
LAST so it wins over them. It stands alone and needs its own row.

`GAP` is what remains and what the class already uses: the closest sibling
`caiso_offer_surface_measured` is a filed GAP on the identical reason —
*"armed in the CAISO keeper but consumed only in
`pipeline/backcast_config.py` — the backcast config builder, not a shared
builder the forecast path calls."*

## 4. What this does NOT decide

- **Not a fix.** A GAP row makes the checker report the fork loudly on every
  run and count it in the header; the fields stay unaccounted-for in substance.
  Wiring is a follow-up session's job, never this check's (FFR-1E scope).
- **Not an adjudication of the forward channel.** Whether this closes by
  wiring the substitution into a shared builder the forecast path calls (the
  `_CAISO_OFFER_CURVE` merge seam that `offer_curve_base`'s docstring flags as
  a later consolidation step) or by a future evidenced `BACKCAST_ONLY`
  declaration is the capx/forecast desk's call under R-X, and is deliberately
  left open here.
- **Not a statement about the mechanism's merits.** caiso-241's admissibility
  ruling (`PRECOMMIT-caiso241-ct-peaker-committed-2026-09-03.md` §1, five
  limbs) and its keeper promotion are untouched. Nothing here re-opens them,
  and nothing here is a C3a lever — the field's own docstring forbids that use.
- **Not a widening of the pinned exception.** `_FR22_OPEN_UNACCOUNTED` in
  `tests/scoring/test_forecast_parity.py` is unchanged; this row makes the test
  pass by accounting for the field, not by excusing it.

## 5. Verification

- `uv run python scripts/check_forecast_parity.py` — CAISO reports
  `caiso_ct_peaker_committed_measured` as `GAP` with this doc cited; registry
  integrity clean (evidence path exists and names the field; `finding` path
  exists, which the checker requires of every GAP row).
- `uv run pytest tests/scoring/test_forecast_parity.py
  tests/scoring/test_gate_a_provenance.py -q` — green.

Run-level evidence and the lane's other two jobs:
`docs/FINDING-y4-caiso241-duties-2026-09.md`.
