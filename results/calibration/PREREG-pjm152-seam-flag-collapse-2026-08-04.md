# PREREG — pjm-152: collapse `pjm_seam_envelope_by_neighbor` (rule 26 `[R-DELETE]`)

> Session pjm-152, 2026-08-04. Branch `claude/pjm-152-backcast-calibration-gaq8jv`.
> Incumbent keeper `2026-08-03-pjm-151-seam-envelope` (bundle `pjm151_seam_B`),
> determination **CALIBRATED**, 9 scored / 9 target / 0 ledgered / 0 fails,
> C1 `all 16/16 · free 12/12`.
> **Pushed BEFORE the first arm solves.** Rule 22 `[R-HOLDOUT]`: 2023–2025 only;
> PJM holds `complete` (validation 2022 unspent) and is absent from `final`;
> holdout spend freeze untouched.

## §1 — the debt, and why this is admissible off an empty lever queue

The PJM price-formation lever queue is EMPTY and the frontier is **owner-declared**
(pjm-142). This arm is **off-queue and says so**: it is not a lever, not a
successor, and not a mechanism. Rule 28(a) admits it as **chartered debt
discharge** — the rule 26 `[R-DELETE]` follow-up that pjm-151 explicitly owed and
recorded in four places (its PREREG §4, FINDING §7, the keeper note, and the
mechanism-matrix row).

pjm-151 gated the repaired per-neighbour seam-envelope construction behind
`ScenarioConfig.pjm_seam_envelope_by_neighbor` **only** so its A/B could be a
single delta on an ISO with zero caveat budget. The flag is now the keeper's
armed path. What remains behind it is the *broken* construction — the
zone-summed envelope that mixes counterparties — still parsing, still
re-armable, still a value a future session could flip. That is precisely the
shape rule 26 forbids: *"a deprecated parameter that still parses is a re-armable
answer key"* (the ORDC-offset incident it was written for).

## §2 — the change, in full

`model/interchange/pjm.py::inject_pjm_seam_flow_limit`:

* the `by_neighbor` parameter is **deleted**;
* the per-neighbour envelope (`spec.PJM_TIE_NEIGHBOR` →
  `eia_loader.pjm_neighbor_interchange_envelope`) is **unconditional**;
* the zone-summed branch — the per-model-ZONE envelope summed over each
  neighbour's `border_zones` — is **deleted**, along with its `cap_rows`
  border-zone summation.

`config/scenarios.py`: the field, and all three of its registrations —
`_CACHE_KEY_OPTIONAL_FIELDS`, `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`, `TIER_TAGS`.

`scripts/run_calibration.py`: both `_pjm_by_nb` reads and both `by_neighbor=`
kwargs at the import and export call sites; the two log lines now name the one
construction that exists.

**What is deliberately KEPT, and why:**

* **`_PJM_TIE_ZONE` is not touched.** It is not the defect. It remains the
  correct grain for the genuinely per-zone objects — `pjm_zonal_interchange`
  (the measured zonal net-position schedule feeding `load_demand`) and the star
  topology's per-border link caps.
* **`pjm_zonal_interchange_envelope` is not deleted.** It is a public loader
  with four live non-seam readers (`run_calibration.py:2492`, three
  `scripts/probes/_pjm135_star_*` probes) and its own regression tests. Rule 26
  targets the re-armable *knob*, not a shared measured loader.
* **`zone_names` stays in the injector's signature**, for parity with
  `inject_miso_seam_flow_limit` and the positional call sites; documented as
  unused by the per-neighbour path.

## §3 — why this needs a solve at all

**The collapse moves the keeper's cache key.** `pjm_seam_envelope_by_neighbor`
was a registered `_CACHE_KEY_OPTIONAL_FIELD`: dropped from the hash at its
default, but the keeper **armed** it, so it entered the keeper's key as a
distinct scenario. Deleting the field removes it from the hash entirely.

A cache-key move is not a behaviour change — but it cannot be *asserted*
byte-identical either. It has to be **proven**, on the artifacts. So the keeper
recipe is re-solved cold at the collapsed HEAD and diffed class-hour by
class-hour. (Confirmed cache-key-neutral at the *default* config:
`ScenarioConfig().cache_key()` is `973a0acdef818e91` both before and after the
deletion — the same value `results/cache.py`'s epoch-2026-08-03b ledger entry
independently records for HEAD.)

## §4 — the single delta

**There is no `--set`, and there must never be one: the arm IS the keeper
recipe.** The one unavoidable difference is a *recording* artifact — the
keeper's `meta.json` carries `pjm_seam_envelope_by_neighbor: true` inside its
`prb_overrides` channel, and that key no longer names a `ScenarioConfig` field,
so `dataclasses.replace` would raise. `scripts/probes/pjm152_collapse_arm.py`
materialises a stripped recipe view of the keeper's meta, **asserts** that
removing that one key from that one channel is the only edit (every other
top-level key compared for equality), and replays from it.

## §5 — arms

| arm | config | status |
|---|---|---|
| **control** | the committed keeper `pjm151_seam_B` | **NOT re-solved — it is the artifact being reproduced** |
| **A (the collapse)** | the keeper recipe at the collapsed HEAD | 2023 + 2024 + 2025, ONE bundle |

Driver `scripts/probes/pjm152_collapse_arm.py`, walking the rule-12
separate-directory chain (`--out X_y23` → `X_y24 --reuse-from X_y23` →
`X_final --reuse-from X_y24`); `results/PJM` scrubbed before the first link only.

## §6 — pre-registered gates

**K1 — recipe integrity.** `config_drift(pjm151_seam_B, arm A)` returns
`pjm_seam_envelope_by_neighbor` as **`keeper_only`** (the keeper recorded it
`True`; HEAD has no such field) and nothing else unexplained. Every other
difference is enumerated schema drift with the commit that moved it and why it
cannot reach a PJM backcast, or the arm is VOID. Re-diffed again at promotion
time — a parallel session can promote underneath us (the caiso-158 failure).

**K2 — control integrity.** pjm-151 established the keeper reproduces at its own
basis `1c191624`. Every `src/market_sim/` commit between that basis and this
arm's is inspected for PJM reachability and enumerated here:

| commit | reach |
|---|---|
| `bd6d090a` nyiso-119 | registers `nyiso_seny_rcpf_increment_step` in the three config registries; NYISO-family-gated, default off. |
| `db5ff912` FFR-3F (D-8) | adds `exit_rate_limits` (default off) + the exit-throughput cap in `runner.py` / `capacity_evolution/`. |
| `09ef7b2a`, `3e534b99`, `2adfb49f` | the same exit-throughput mechanism: seed resolution, ledger key, admission-cap horizon. All `capacity_evolution/` + `runner.py`. |
| `b291aa2f` | `results/cache.py` **docstring-only** epoch-ledger entry. No executable line. |
| `16da87f6` | re-derives `DEMAND_GROWTH_RATES["NYISO"]` from the 2026 Gold Book. NYISO row only; forecast-only table — the backcast takes measured load and never reads it. |
| `935c33dd` ercot-159 | **added at the 2026-08-04 rebase onto `a0bf3db3`, after this PREREG was pushed.** `ercot_energy_online_capability_cap` (+ its artifact path), default off; sole read is inside `if getattr(config, "ercot_energy_online_capability_cap", False)` on the ERCOT fast-tier row of `reserves/spec.py`'s `online_capacity_cap` block. |
| `eda8ebe8` caiso-164 | **same rebase.** `caiso_zonal_loss_surface`, default off and guarded by `if getattr(...) and iso == "CAISO"` — unreachable for `iso="PJM"` twice over; the `runner.py` site's new conditional reduces to the pre-existing `UNSET` when off. |

*The K2 enumeration is maintained to the arm's actual basis rather than frozen
at pre-registration time: a commit landing between the PREREG and the solve must
be inspected and listed, or the discharge is void (§7). Measured against the
keeper's recorded config, the complete schema drift at this basis is exactly
four `arm_only` fields — `caiso_zonal_loss_surface`,
`ercot_energy_online_capability_cap`, `ercot_energy_online_capability_cap_path`,
`exit_rate_limits` — and one `keeper_only` field, the declared deletion. **E1 is
unchanged and remains absolute**; nothing here relaxes a gate.*

The exit-throughput commits are unreachable from this lane for the reason
pjm-150 §4 established and which must not be mis-stated as "forecast-mode only":
**the calibration harness never calls `evolve_fleet`** — `solve_and_persist`
loops years through `run_calibration.run_year`, a standalone per-year solve, so
`runner.py`'s evolution path (capacity-evolution steps 0–6) is never entered.
The runtime environment is byte-equal to the keeper's recorded block
(python 3.11.15, highspy 1.14.0, numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
pyarrow 24.0.0, pydantic 2.13.4). **K2 is scored, not asserted** —
`pjm152_collapse_gates.gate_k2` fails on any environment drift.

**K5 — span.** `[2023, 2024, 2025]` in ONE bundle (rule 16). No holdout year is
solved, scored, or registered; the driver hard-refuses any other year.

**E1 — THE gate, single and absolute.** A behaviour-preserving collapse admits
**exactly zero** movement:

> **max |ΔMW| = 0.000000 on every P1 class-hour of all three years**, against
> `results/calibration/pjm151_seam_B/hourly/class_hourly_<year>.parquet`.

Scored by `scripts/probes/pjm152_collapse_gates.py` on the LONG-form sidecar,
filtered to `P1` and sorted to a canonical `(klass, hour)` key before a
positional diff — reading it wide or unsorted produces a vacuous comparison
(the defect the pjm-151 scorer recorded against itself). The gate reports
`n_nonzero` and `sum_abs_dMW` alongside the max, so "zero" is a measured
statement about every cell rather than about one statistic.

## §7 — kills

* **Any non-zero |ΔMW| is a STOP-THE-LINE event**, not a finding to characterise
  and not a caveat to absorb. The collapse would have changed behaviour, which
  it has no mechanism to do; the session stops and reports rather than
  proceeding to registration.
* Any `--set` on the arm → VOID. The arm is the keeper recipe.
* Any second unexplained recipe difference → VOID (K1).
* Any environment drift from the keeper's recorded stack → the identity claim is
  void (K2), because alternate-optimal vertices move across numerics versions.
* A holdout year touched in any way → stop-the-line.
* **Any criterion move is reported, never absorbed.** PJM is 9/9 with ZERO
  ledgered caveats; there is no slack. C6 flips `PASS → UNATTESTED` for an
  unattested probe, which is expected and reported, not a regression.
* Tuning `PJM_TIE_NEIGHBOR`, `PJM_SEAM_FLOW_PERCENTILE`, `_PJM_TIE_ZONE` or the
  seam caps in any direction → forbidden outright (rules 5 / 14 / 20 / 24). The
  percentile stays at the shipped `PJM_SEAM_FLOW_PERCENTILE = 90`. Root-cause
  item 15 (the net-export level residual) is **not** chased here and is not
  chargeable to this arm.

## §8 — rule 28 `[R-MECH-MATRIX]` duties

The deleted field was a registered matrix entry on `seam_flow_envelopes`. Duty
(b) and (c) are discharged in the same PR: the row's `def` records the deletion
and retargets the PJM line anchors; the `note` replaces "RULE 26 FOLLOW-UP OWED"
with the discharge and the measured identity result. No verdict is minted and no
other ISO's cell is touched (rule 25) — the MISO literals on that row are left
byte-untouched.
