# FFR-2A — Crossover seam (FR-9), the vanished MISO crossover, and the T1-X refresh

**Session:** FFR-2A `[OPUS]` (forecast-readiness remediation Wave 2, lane L-VAL;
`docs/forecast-readiness-prompt-pack-2026-07.md` §FFR-2A; audit rows FR-9 + FR-21 §3.5 + §4
P1-c). Branch `claude/ffr-2a-crossover-seam-5gnuuz` off `origin/main` @ `579c719`, 2026-08-02.

**Result.** FR-9 is fixed at both the call site and the seam, with the leakage guard extended
to catch a regression at run time. **The audit's MISO hypothesis is REFUTED** — the seam
KeyError is real but was never reachable in the config FF-2D launched. The two FF-2D L-VAL
follow-ups are folded in and the adapter is deleted. The T1-X battery is re-solved COLD for
ERCOT, PJM and MISO at post-Wave-1 HEAD; **all three determinations are HOLD**, unchanged in
kind from FF-2D. **No keeper moved** — attested by measured before/after diff against
`origin/main`, not by argument (§2.4). Nothing was tuned: three residuals are written up as
open blockers in §7 rather than closed.

Commits: `3255dd7` (FR-9) · `d12b4a8` (adapter fold-in + FC-4 family volume) · `efe981d`
(family-grain correction) · `5a1183e` (ERCOT/PJM registration) · `31e16c6` (MISO registration
+ this doc) · `32c1d80` (matrix note + attestation).

---

## 1. The MISO diagnosis (one line, as asked)

**REFUTED.** The seam `KeyError` is real and reproduces on demand
(`neighbor_gas_price(spec, 2026, "hindcast_realized")` → `KeyError: 2026` for all three MISO
neighbours), but it was **never reachable in the run FF-2D launched**: that crossover config
leaves `reference_price_interface=False` (MISO's `ISOConfig.default_scenario_overrides` is
empty and `--capacity-market-clearing` does not arm it), so the priced seam code path is never
entered — the MISO crossover did not crash on the seam.

**What did happen, then.** The T0-scale repro is clean end to end: the config builds,
`assert_forward_drivers` returns `[]`, and the 2026 forward year resolves every driver. The
positive control is the re-run itself — this session's MISO crossover **solved all five years
including 2026 and 2027, reported zero leakage violations, and registered** (§5), on the same
`--crossover --vintage 2023 --capacity-market-clearing` recipe FF-2D launched. Wall clock was
~13 min for 5 solve-years at a 9.7 GB peak. The only remaining explanation consistent with the
evidence is FF-2D §4.3's own hedge: *"If the run did not finish in-session it is a documented
follow-up, not a gap in the gate result."* It did not finish; nothing swallowed it.

**This does not make FR-9 a false positive.** The defect is a live latent one, reachable by any
crossover that arms a seam — and CAISO's crossover would hit the same raw index through
`caiso_hub_reference_price`. It is fixed, and the guard now fails the run loudly instead of
either raising an opaque `KeyError` mid-solve or (worse) silently pricing a forward year off a
measured path. Reproduction, both directions, is pinned in
`tests/scoring/test_crossover_harness.py::TestNeighborSeamForwardGas`.

---

## 2. FR-9 — the crossover neighbour-gas seam

### 2.1 What was wrong

The import/export reference-price seam is a **second gas consumer** beside the ISO's own fuel,
and it was blind to the crossover boundary:

* `runner.py` passed `gas_scenario=config.gas_price_path` unconditionally into
  `apply_interchange_injections`;
* `data/neighbor_price.py` raw-indexed `HENRY_HUB_TRAJECTORIES[gas_scenario][year]` in
  `neighbor_gas_price` (line 206) and `caiso_hub_reference_price` (line 481).

In a T1-X/T1-FF crossover, `gas_price_path` is `"hindcast_realized"` (knots 2021, 2023–2025) and
the forward path is `crossover_forward_gas_path`. A forward year therefore priced its imports
off the realized hindcast path — a `KeyError` where the year is past the last knot, or a
measured level held forward where it is not. That is a measured input reaching a forward year,
rule 13 `[R-MEASURED]`. `assert_forward_drivers` checked only `resolve_annual_gas_price` and was
blind to the seam.

### 2.2 The fix

| Layer | Change |
|---|---|
| Decision | `data/fuel/trajectories.py::resolve_gas_scenario_path(config, year)` — the ONE place the crossover fuel seam is decided (rule 19 `[R-ONE-MECH]`). `resolve_annual_gas_price` now calls it; its behaviour is unchanged. |
| Call site | `runner.py` passes `gas_scenario=resolve_gas_scenario_path(config, year)`. |
| Seam | `neighbor_gas_price` / `caiso_hub_reference_price` hold the nearest knot flat (`_hold_flat_extrapolate`), exactly as the ISO's own resolver does. |
| Guard | `assert_forward_drivers` grows limbs **(d)** `assert_neighbor_seam_drivers` and **(e)** `assert_no_measured_overlays`. |

**Why hold-flat at the seam is not a licence to hold a measured path forward.** The seam's own
docstring contract is that "a neighbor and its bordering ISO see the same Henry Hub level", and
the raw index broke it: the ISO held flat past the last knot while the seam raised. Hold-flat
restores the contract as an *end-of-trajectory* rule. **Which** trajectory a forward year rides
is decided upstream by `resolve_gas_scenario_path` and asserted per-year by the guard — so a
regression surfaces as a loud leakage violation, not as a plausible held-flat number.

### 2.3 The extended guard

**(d) Neighbour seam.** For every armed seam neighbour × forward year, the guard computes the
delivered gas the seam will actually charge and asserts it equals the declared forward
trajectory and is **not** the realized path's — the same two-sided construction limbs (b)/(c)
already apply to the ISO's own gas. Armed seams only: the generic
`reference_price_interface` (non-CAISO) and CAISO's `caiso_reference_price_seam` /
`caiso_intertie_reference_price`. A disarmed seam asserts nothing, because the priced path is
never entered — which is exactly the state §1 found the FF-2D MISO crossover in.

*Negative control:* monkeypatching `resolve_gas_scenario_path` back to the pre-fix
`config.gas_price_path` makes the guard emit two violations (2026, 2027) naming
`hindcast_realized`. Pinned as `test_guard_catches_the_pre_fix_seam`.

**(e) Measured overlays, including the `weather_year`-keyed ones.** Belt-and-braces with the two
landed guards it deliberately duplicates — FFR-1D's `_BACKCAST_ONLY_OVERLAY_FIELDS` refusal in
`ScenarioConfig.__post_init__`, and FFR-1B's `mode == "backcast"` gate on the `weather_year`-keyed
measured single-event derate table. Both live far from the harness; this states the harness's own
contract at run time. Three checks: no backcast-only overlay armed; `outage_source != "historic"`;
and the `weather_year` pin sits strictly **below** the forward boundary on a T1-X (a T1-FF
full-forward run is exempt by construction — its boundary IS its base year, FH-1 plan §2.1).

### 2.4 Byte-identity attestation — no keeper can move

**Measured differential vs `origin/main` @ `579c719`** (a git worktree at the base commit, the
same surface dumped from both trees and diffed): **396 gas-resolution values compared — every
ISO × every trajectory × every seam neighbour and CAISO hub × years 2021/2023/2024/2025, plus
`resolve_annual_gas_price` over 6 ISOs × 3 paths × both modes × 2023–2025.**

* `resolve_annual_gas_price`: **0 divergences.** The refactor is pure.
* Seam + CAISO hub: **48 divergences, every one of them `KeyError → value`** — all at **2021**
  on a trajectory whose earliest knot is 2023 (`low`/`mid`/`high`/`hindcast_asknown_aeo2023`).
  **Not one case where the old code returned a number returns a different number.**

No committed run can have depended on the changed cells: they previously *raised*. Then three
independent reasons no keeper can move, each sufficient:

1. **The seam change is byte-identical wherever the old code succeeded** — the 48 deltas above
   are exactly the raising cases. Every backcast year and every AEO forecast year through 2050
   is a knot, so `_hold_flat_extrapolate` returns `trajectory[year]` unchanged there.
2. **The call-site change cannot fire in a backcast.** `resolve_gas_scenario_path` returns
   `config.gas_price_path` unless `is_crossover_forward_year(year)`, and
   `crossover_forward_year` requires `mode="forecast"` (`__post_init__` raises otherwise).
3. **`runner.py` is the forecast orchestrator.** Keepers run through
   `scripts/run_calibration.py`, whose own seam call site is untouched (and is provably correct
   already, by reason 2).

No `ScenarioConfig` field added, removed or re-defaulted; the pinned default cache key stays
`603c2498bf71d21d` (four pinned-literal tests green); no band widened; no default moved. **No
mechanism-matrix row is required** — nothing here is a solve-affecting mechanism, and no cell
was tested (rule 28 duties (b)/(c) do not fire).

---

## 3. The two FF-2D L-VAL follow-ups, folded in

`scripts/_ff2d_crossover_adapter.py` is **deleted**, not left parsing beside the real path
(rule 26 `[R-DELETE]`).

**(a) The FC-4 rubric contract now comes from the emitter.** `score_crossover.py` writes
`refusal_marker` top-level — serialized from the same constants `_assert_scoreable_year`
enforces, so the artifact *states* the ≥2026 quarantine the loaders already make structural —
and a flat top-level `metrics` list on the rubric's own names. The t2 scorer test that pinned
the pre-fold shape now pins the other half: a marker nested anywhere but top-level is still
ABSENT to the scorer and still FAILs the rule-22 gate.

**(b) `gas_twh` / `coal_twh` are now covered.** FC-4 bands them at ±5 %; the emitter previously
produced only aggregate `fuelmix` (TWh Σ|Δ|) and `price_shape` (NRMSE), neither of which maps to
a fractional band, so both rows were uncovered. `_family_volume` aggregates the GAS and COAL
families over the calibration scorer's own `GAS_CLASSES` / `COAL_CLASSES` taxonomy — no second
list to drift. `price_shape` and aggregate `fuelmix` are still **not** emitted: they have no
fractional counterpart in the rubric and re-keying them onto a band they do not mean would be
worse than leaving them uncovered.

**Uncovered rows are named, never silently passed.** A family with a preliminary-EIA-923 member
(`class_is_gated` false — the same predicate C1 gates on) is emitted `gated: false`, listed in
`metrics_uncovered`, and printed in the report rather than banded. In practice that is
`gas_twh 2025` for all three ISOs and `coal_twh 2025` for PJM/MISO.

### 3.1 A defect in my own first cut, caught on the first score — recorded, not buried

The first ERCOT/PJM score returned `coal_twh = 1.0000` (a 100 % error) in every scored year.
That was an artifact of the aggregation I had just written, **not a dispatch result**. A
crossover bundle runs the legacy equal-width heat-rate bins (`use_campd_bins=False`), so its
whole coal fleet reports in one unsplit `COAL` bucket, while the bench splits coal into
`COAL_PRB`/`COAL_LIGNITE`/`COAL_BIT`/`COAL_WC`. C1 emits no record for either side of that
mismatch — the model's `COAL` is unbenchmarked, the bench's split classes have no model — so
aggregating the C1 *records* read the model's coal volume as ZERO.

`_family_volume` now sums each side over the whole family from the class dicts (`gmModel` vs
`classFull`; the keeper from its own per-class records, whose grain already is the bench's).
That is what the family row means, and it is the documented rule 14 `[R-ACCURATE]` case: real
data on a different boundary than our representation, reconciled rather than discarded.
Measured effect on ERCOT 2023 coal: **39.24 vs 60.42 TWh = −35.1 %**, in place of a fabricated
−100 %. `model_only_classes` now records which buckets exist on one side only, so the grain
mismatch is visible in the artifact instead of inferred. Pinned as
`test_family_volume_reconciles_the_unsplit_coal_bucket`.

---

## 4. T1-X re-run — the input-gap table vs the CURRENT keepers

**Why re-run (audit FR-21).** FF-2D scored at 2026-07-20. Since then ~20 keeper promotions
landed across six ISOs, and the cache epoch taken 2026-08-02 (§W1-X close §0c-3) invalidates
**every** pre-Wave-1 forecast-mode cache at **any** solve year — FR-8 reaches a crossover's
realized 2023–2025 legs. All three legs are therefore **COLD** re-solves. The container was
verified already cold before the first solve (zero `year_*.parquet` anywhere under `results/`),
so the ledger's purge was a no-op here.

Window 2023–2027 (5 solve-years, at the ceiling), vintage 2023, forward boundary 2026,
`crossover_forward_gas_path=mid`; PJM and MISO armed `--capacity-market-clearing` to match their
flipped per-ISO default, ERCOT did not (energy-only). **Scored 2023–2025 only**; the ≥2026
refusal marker is present and clean on all three (FC-4 row 1 PASS), and every leg reports
`leakage_violations: []` and records the active holdout freeze at launch.

`input gap = |forecast err| / |keeper backcast err|` on the SAME criterion, both sides scored by
the same functions. **Treat price as the load-bearing measurement; CO2 is directional only
(§4.2).**

### 4.1 Measured input gap (forecast |err| ; keeper |err|)

| ISO | metric | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| **ERCOT** | price | **68.7 %** ; 33.30 % | **41.9 %** ; 0.78 % | **8.9 %** ; 9.06 % (gap 0.98) |
| | gas_twh | 19.6 % ; 0.16 % | 10.0 % ; 0.15 % | *uncovered* |
| | coal_twh | 35.0 % ; 2.95 % | 44.1 % ; 2.29 % | 38.1 % ; 3.56 % |
| | co2 † | 49.2 % ; — | 42.7 % ; — | 51.2 % ; — |
| **PJM** | price | **3.6 %** ; 6.33 % (gap 0.58) | **7.5 %** ; 0.38 % | **17.2 %** ; 7.49 % (CAVEAT) |
| | gas_twh | 0.4 % ; 0.22 % | 3.6 % ; 0.94 % | *uncovered* |
| | coal_twh | 13.0 % ; 0.16 % | 25.2 % ; 0.80 % | *uncovered* |
| | co2 † | 45.1 % ; — | 42.2 % ; — | 57.3 % ; — |
| **MISO** | price | **13.6 %** ; 1.19 % (CAVEAT) | **15.3 %** ; 6.45 % (CAVEAT) | **30.3 %** ; 14.17 % (FAIL) |
| | gas_twh | 9.5 % ; 5.10 % | 12.1 % ; 2.73 % | *uncovered* |
| | coal_twh | 1.0 % ; 1.83 % | 4.9 % ; 1.49 % | *uncovered* |
| | co2 † | 63.3 % ; — | 59.9 % ; — | 77.1 % ; — |

† no keeper comparator exists — see §4.2. *uncovered* = preliminary EIA-923 vintage, reported
not banded (§3).

### 4.2 CO2 is worse than "reconstruction-basis-partial" — it now has no comparator at all

FF-2D recorded the crossover CO2 as reconstructed on the keeper's full-plant basis via bench
intensities (`dispatch_skill.reconstruction.note`), so the 43–58 % gap was "partly a
reconstruction-basis artifact". **That caveat stands and this session does not narrow it.**

What is new, and is a concrete instance of FR-21: **both current keepers commit ZERO C5a CO2
records** (`V.determine("2026-08-01-ercot149-gas-event-cap")["criteria"]["co2"]["records"] == []`,
same for `2026-07-31-pjm-143b-hy-level`), so the keeper side of the CO2 input gap is `None` in
every cell. FF-2D could still quote "vs keeper 0.2–3 %"; today that comparator does not exist.
CO2's FC-4 rows still band the forecast error against the commercial band (and still FAIL), but
the *input-gap* reading of CO2 is unavailable. **Price is the load-bearing measurement.**

### 4.3 Verdicts — HOLD ×3, unchanged in kind from FF-2D

| ISO | FC-1 | FC-4 | determination | vs FF-2D |
|---|---|---|---|---|
| ERCOT | **FAIL** (I3, I6 26.9 %, I7) | **FAIL** | HOLD | same; I6 25.6 % → 26.9 % |
| PJM | PASS | **FAIL** | HOLD | same |
| MISO | **FAIL** (I9 only) | **FAIL** | HOLD | **first registration** |

For ERCOT and PJM the headline numbers barely moved (ERCOT price 69.2/42.7/8.6 → 68.7/41.9/8.9;
PJM 2025 price 17.5 % → 17.2 %; CO2 within ~1 pp everywhere). **The refresh's value there is
that the evidence is now current and the family-volume rows are covered, not that the picture
changed.** ERCOT's FC-1 failure remains the crossover harness's own forward-year
over-retirement — the same defect FH-1's §3.3 gate reproduced at the T1-FF posture (§0d), owned
by the retirement lanes, not by this one.

**MISO is new evidence, and it is the most informative leg of the three.** Two readings worth
carrying to the owner sitting:

* **Its FC-1 failure is narrow and of a different kind.** The ONLY failing invariant is **I9
  storage integrity** — simultaneous charge+discharge at 0.23 % / 0.10 % / 0.84 % of throughput
  in 2025/2026/2027. That is LP degeneracy at the storage tiebreaker (rule 9 `[R-EPSILON]`,
  ε = 0.001 $/MWh), not a capacity-path defect: MISO's I6/I7 pass, so it does **not** carry
  ERCOT's over-retirement signature. FC-2 PASSes outright.
* **Its volumes are the best of the three and its price is the worst-trending.** `coal_twh`
  1.0 % / 4.9 % is inside the ±5 % commercial band in 2023 and essentially at the keeper's own
  error — the forward drivers reproduce MISO's coal volume nearly as well as the measured
  overlays do. Price nonetheless degrades monotonically 13.6 % → 15.3 % → **30.3 %**, crossing
  the K=3.0 band in 2025 while `gas_twh` drifts +9.5 % → +12.1 % (over-generation). Volume
  skill without price skill, worsening with distance from the vintage year, is the signature
  worth naming — but this lane measured it and did not chase it (rule 1).

---

## 5. Registered runs

Forecast namespace (`frontend/data/forecast/`) via `scripts/register_forecast_run.py` — never
the backcast registry (plan §7.5).

| run id | ISO | verdict key | determination |
|---|---|---|---|
| `ercot-2023-2027-crossover-ffr2a` | ERCOT | `ercot-t1x-ffr2a` | HOLD |
| `pjm-2023-2027-crossover-ffr2a` | PJM | `pjm-t1x-ffr2a` | HOLD |
| `miso-2023-2027-crossover-ffr2a` | MISO | `miso-t1x-ffr2a` | HOLD |

Each carries its **own** verdict key rather than re-pointing FF-2D's, for the reason
`VERDICT_MAP` already states: a run must never render a verdict its own score contradicts. The
`-ff2d` rows are untouched, so both measurements stay on the record and the FR-21 drift is
visible rather than overwritten.

---

## 6. Quarantine and governance posture

* Scoring stops at 2025 on both bounds; `_assert_scoreable_year` guards every bench/actual
  loader **before any file is opened**, and the ≥2026 refusal tests still pass
  (`tests/scoring/test_score_crossover.py`, 26 tests).
* 2026/2027 are solved as **forecast-mode** years reading no measured actuals — rule-22-legal,
  and the harness printed its own freeze-legality statement at launch on every leg.
* The holdout freeze is **ACTIVE** and untouched. No marker was spent; no out-of-training year
  was solved, scored or registered.
* No `.github/workflows/*.yml` added. All three solves ran in-session, years sequential within
  each invocation, ≤2 concurrent invocations, PJM and MISO never co-running (MISO peaked at
  **9.7 GB** RSS, above the 8.6 GB no-co-run anchor — the split was necessary, not just
  procedural).

---

## 7. Open blockers — written up, not closed (rule 1 / rule 14)

1. **The keepers' C5a CO2 records are empty**, so the crossover CO2 input gap has no comparator
   (§4.2). This is a *keeper-artifact* gap, not a crossover one, and it is not this lane's to
   fix — it belongs with whoever owns the C5a emission on keeper promotion. Until then no
   session may quote a crossover CO2 input-gap ratio; only the absolute forecast error is
   available, and it remains reconstruction-basis-partial.
2. **`gas_twh` 2025 (all three ISOs) and `coal_twh` 2025 (PJM, MISO) are structurally
   unscoreable** while the 2025 EIA-923 vintage is preliminary. They are reported as uncovered,
   never passed. They begin gating with no code change when the vintage finalises and the
   completeness audit is re-run — the same auto-extension C1 already has.
3. **Eight tests are RED on `origin/main` beyond the two §0c-6 names.** §0c-6 lists
   `test_ff_readiness_battery.py::test_marker_state_reflects_committed_markers` and
   `test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`. Also red
   at `579c719`, verified by stashing this branch's changes:
   `tests/regression/test_constants_facade.py::test_moved_surface_is_complete`
   (`market_sim.config.fuel_trajectories` grew `PJM_RGGI_ALLOWANCE_PRICE_PER_TONNE`, absent from
   the facade re-export) and **seven** `tests/unit/data/test_measured_chp_heat_rates.py::TestDerive::*`.
   None is attributable to Wave 1 or to this lane. The fast lane is otherwise green: **5,871
   passed** with this branch applied, zero new failures.

None of the three was closed by a tuned value, and none is a residual this lane could close by
changing a parameter.

---

## 8. Standing disclosures (peer review §4, carried verbatim)

> This forecast is produced by a chronological full-8760 LP dispatch model with a one-pass
> annual capacity-evolution loop. It does not include: MIP unit commitment; intertemporal
> capacity optimization or within-year entry/exit convergence; inter-hour ramp constraints;
> intra-ISO hurdle rates; demand-responsive fuel pricing. Unless produced by the weather
> ensemble, results are conditional on a single pinned weather year (stated in the run config).
> Uncertainty bands are dispatch-conditional: the fleet-path (capacity-expansion) component of
> structural error is unmeasured and excluded. Deterministic scenario cases are a range, not a
> probability distribution.

Lane-specific additions for anything quoting §4's numbers:

* A T1-X input gap is a **dispatch-conditional** measurement on a vintage-2023 seeded fleet. It
  measures the backcast→forecast *input* gap, not forecast skill, and it inherits the crossover
  harness's own capacity-path defects (ERCOT's I6 over-retirement is in these numbers).
* **CO2 is directional only** — reconstruction-basis-partial on the forecast side and with no
  keeper comparator at all (§4.2). Price is load-bearing.
* Family-volume rows marked *uncovered* are not passes.

---

## 9. What this session did NOT do

* Did not change a default, a band, a threshold or a `ScenarioConfig` field.
* Did not touch a keeper, a keeper shard, or the backcast registry.
* Did not spend a holdout marker or solve/score/register any out-of-training year.
* Did not re-point FF-2D's verdict keys or edit its findings doc.
* Did not fix the retirement layer behind ERCOT's FC-1 failure — that is FFR-2B's and the
  retirement lanes' (§0d-3).
