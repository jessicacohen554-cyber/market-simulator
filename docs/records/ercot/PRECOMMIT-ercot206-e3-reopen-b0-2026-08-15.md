# PRECOMMIT — ercot-206: the FFR-8A §3.3 E3 reopen, Phase B0 — the ORDC LOLP-parameter
# reproduction test re-run on the T-3b SETTLEMENT-CLOSED published series

**Session ercot-206, 2026-08-15. Dispatch: ERCOT-FRONTIER-1 (Phase B, the one live
technical successor). Pushed BEFORE the probe is run and before any solve.**
HEAD at assembly: `86ba8bc5c`. Keeper at session start:
**`2026-08-15-ercot204-rule26-delete`** (owner-promoted at ercot-205, byte-identical
to the superseded `2026-08-14-ercot202-arm-plantphysics`).

**Shorthand and branch note (recorded, not silently resolved).** The dispatch opened
this lane as *ercot-203* ("log tail says 202"). Main has since consumed ercot-203
(the grain-repair lane), ercot-203b (the RTOFFPA protocol gate), ercot-204 (the
RTORPA gate + rule-26 successor) and ercot-205 (the owner-instructed promotion,
landed mid-session while this lane was reading), whose entry closes "Next shorthand:
**ercot-206**." This session is **ercot-206**, per the standing append-collision
convention. The dispatch names landing branch `claude/ercot-frontier-1-e3-reopen`;
the harness-assigned branch is `claude/ercot-frontier-assessment-l1jwi2`. The same
commits are pushed to BOTH refs (same SHA) so neither instruction is broken; the
owner merges whichever. The dispatch's "run192 recipe" A/B baseline is likewise
stale two promotions over — the contingent A/B (§5) is defined off the CURRENT
keeper recipe, with the deviation recorded here.

---

## 1. THE OBJECT, AND WHY THE REOPEN IS LICENSED NOW

FFR-8A §3.3 ESCALATED-not-landed the ORDC LOLP-parameter question (element E3): on
the §1.1(b)/§2.2 reproduction test — the implemented curve evaluated on the measured
NP6-905-CD RTOLCAP/RTOFFCAP series against the measured RTORPA series — **neither**
in-repo parameter set reproduced the published adder series in both years (committed
record `docs/handoffs/ffr-8a/part-a-measured-2026-08-08.json` `legs_ab`):

| year | series | h>$1 | h>$10 | h>$100 | max $ | mean $ | top-50 mean $ |
|---|---|---|---|---|---|---|---|
| 2024 | measured RTORPA (archive) | 78 | 26 | 4 | 252.7 | 0.203 | 33.9 |
| 2024 | flat fallback (μ=0, σ=1400) | 48 | 18 | 6 | 279.0 | 0.181 | 31.5 |
| 2024 | NP6-576-ER table | 77 | 37 | 11 | 639.5 | 0.521 | 89.8 |
| 2025 | measured RTORPA (archive) | 15 | 3 | 1 | 414.1 | 0.065 | 10.6 |
| 2025 | flat fallback | 4 | 1 | 0 | 10.3 | 0.003 | 0.4 |
| 2025 | NP6-576-ER table | 15 | 3 | 0 | 44.5 | 0.014 | 2.2 |

The table was refuted on the 2024 deep tail (~2.6× over), the fallback on the 2025
counts (4/15), and **both** on the 2025 top-50 magnitude (0.4 / 2.2 vs 10.6). E3's
reopen was gated on new evidence bearing on the published series; FFR-8B's Phase 1
was quantity-side and produced none.

**The new evidence exists and is committed.** ercot-198 (T-3b,
`docs/FINDING-ercot198-t3b-adder-overlay-audit-2026-08-14.md` §4) produced a
settlement-closed, SOM-cross-checked measured published RTORPA series for 2024/2025:
the MIS archive retains pre-price-correction prints, and exactly one hour trips the
settlement-closure guard (archive adder total > settled hub RTSPP + $50) — **2025
h4334** (Jun-30 14:00: archive RTORPA $414.12/h vs settled hub RTSPP $54.96, λ
$41.61), a corrected print that never settled, and the entire distance between the
archive's 2025 RTORPA (0.079 dw) and the SOM's <$0.02. **The 2025 row of the
FFR-8A test above therefore scored both parameter sets against one un-settled
archive artifact** (measured max 414.1 = h4334; it is the whole of the 2025
"measured h>$100 = 1" and ~$8.3 of the $10.6 top-50 mean). 2024 is unaffected
(zero flagged hours). Re-running §1.1(b) on the settled basis is exactly the
evidence class the escalation named — including "the 2025 series'
RTC+B-transition truncation" among its candidate causes.

Independently, ercot-204 §A measured the formation defect at full magnitude on the
current keeper recipe: published RTORPA dw 1.2675 / 0.2368 / 0.0787 $/MWh over
1,705 / 560 / 253 hours (2023/24/25, raw-archive basis) vs the model's endogenous
`ordc_adder` dw 0.4067 / 0.0000 / 0.0000 over 42 / 2 / 1 hours — and falsified the
"model holds more reserve" reading (model holds LESS: 6,955 vs 8,854 MW in 2024
fired hours; 6,638 vs 9,654 in 2025). Rule 1 `[R-STRUCT]`: the diagnosis is
structural — parameters and inputs first — and no overlay is contemplated
(ercot-204 §A adjudicated the published-RTORPA overlay non-viable under rules 19
and 13; that adjudication is honoured, not revisited).

## 2. THE SURFACE, CONFIRMED FROM CODE AND THE COMMITTED RECORD (rule 24)

What forms the backcast ORDC adder on the keeper:

1. **The sidecar `ordc_adder` is the LP balance dual of the lumped ORDC
   total-reserve family**, not a post-solve curve evaluation:
   `scripts/run_calibration_full.py` (ORDC-regime branch, `ercot_reserve_supply_cap`
   on, `ercot_market_regime(year)=="ordc"`): with `ercot_ordc_total_reserve=True`
   the adder is `reserve_price_by_family[:, -1]` — the total family is appended
   last — added post-solve to `price` (RTSPP = SPP + RTORPA analogue; the
   `ercot_ordc_only_scarcity` realized-adder branch is OFF on the keeper, and
   `ercot_ordc_cap_dual_adder` is default-off).
2. **The family's demand curve** is `results/scarcity.py::ercot_ordc_demand_steps`,
   built from `resolve_lolp_params(config, hours)` **collapsed to annual means**
   (`mu_s = mean(mu)`, `sigma_s = mean(sigma)`; `model/reserves/spec.py`
   single-product and multiproduct ERCOT designs alike), n_steps=40 over
   `req_total = mcl + mu_eff + 5σ`; penalties `0.5·VOLL·(LOLP_full + LOLP_half)`
   with the OBDRR048 floor applied **unconditionally** in the steps (the
   docstring's recorded caveat: the 2023-11-01 date-gating lives only in the
   post-solve `ordc_adder()` path via `floor_active_mask`).
3. **Keeper effective values, read from the promoted bundle's
   `results/calibration/ercot204_rule26_delete/run_config.json`** (not inherited
   from run192): `ordc_lolp_params_path=None` → the **flat fallback μ=0, σ=1400**
   (μ_eff=700, req_total=10,700 MW); shift 0.5σ; MCL 3,000; VOLL $5,000;
   multistep floor on; `ercot_ordc_total_reserve=True`, `energy_reserve_coopt=True`,
   `ercot_multiproduct_as_coopt=True`, `ercot_reserve_supply_cap=True` (supply
   capped at measured RTOLCAP, `scarcity.ercot_rtolcap_supply_cap_mw`),
   `ercot_load_resource_reserve=True` (LR credit nets the requirement),
   `ercot_ecrs_requirement=False`, `ercot_storage_as_reserve=True`.
4. **The reserve-quantity basis the backcast feeds the curve** is therefore the
   co-optimized held-reserve solution (thermal spinning headroom at plant-online
   grain + storage + LR credit, capped at measured RTOLCAP) — NOT the published
   realized RTOLCAP series itself; the published series enters only as the supply
   CAP. The knee levels on the committed record (part-a JSON): fallback
   $10/$100/$1000 at 7,415 / 6,200 / 4,578 MW; NP6-576-ER seasonal ~8,102–8,255 /
   6,911–7,033 / 5,208–5,282 MW.
5. **`floor_active_mask` date gate confirmed**: all-on for year>2023, all-off
   year<2023, `hour >= ORDC_FLOOR_START_HOUR_2023` (2023-11-01) inside 2023 —
   used by the post-solve/overlay constructions; see (2) for the co-opt caveat.

The E3 delta, if validated, is the **existing default-off field**
`ScenarioConfig.ordc_lolp_params_path` (scenarios.py:2822, cache-key registered)
pointed at the committed published table
`data/raw/_validation-source/ercot_ordc_lolp_params.csv` (NP6-576-ER, μ≈904–947 /
σ≈1333–1368 by season). No new field, zero new scalars, nothing fitted — the
parameters are ERCOT's published ones (rule 13/14 posture of ercot-145b,
VERBATIM: armed on measured-input/parameter correctness, fit gain NOT predicted).

## 3. PHASE B0 — THE PROBE (read-only; measured vs measured; no LP, no solve)

`scripts/probes/ercot206_e3_settled_reproduction.py` →
`results/calibration/ercot206_e3_settled_reproduction.json`.

Construction identical to FFR-8A `leg_ab` (same `ordc_adder` call: full reserve =
rtolcap+rtoffcap, online = rtolcap, floor_active=True for 2024/2025), with ONE
change — **the measured RTORPA/RTORDPA side is settlement-closed by the ercot-198
guard before scoring**: hours where archive (RTORPA + RTORDPA) > settled hub RTSPP
(committed bench `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet`,
`rt`) + $50 are zeroed, each flagged hour reported. 2025 restricted to the
pre-go-live 8,112 ORDC-regime hours as before. Verdict years: **{2024, 2025}**
(the E3 object). A **2023 context block** is additionally reported at full
magnitude (same construction, `floor_active_mask(2023)` honoured, guard applied)
— context ONLY, pre-declared to carry **zero verdict weight**: 2023 is not part
of the E3 escalation, and under Q-B/R-A it appears here as a measured-data
reading, never a target (no year is solved or scored anywhere in B0).

## 4. THE PARAMETER-SET VERDICT RULE (pre-registered, mechanical, direction-blind)

For parameter set S ∈ {fallback, NP6-576-ER table} and year Y ∈ {2024, 2025},
on the settled series, **REPRODUCES(S, Y)** is true iff ALL of:

* **(a) top-50 magnitude**: model top-50 mean / measured top-50 mean ∈ [0.5, 2.0];
  if the measured top-50 mean < $0.50 the ratio leg is replaced by
  |model − measured| ≤ $1.00.
* **(b) count bands at $1 and $10**: for each threshold t ∈ {1, 10}:
  model count / measured count ∈ [0.5, 2.0] OR |model − measured| ≤ 2 hours;
  measured count of 0 requires model count ≤ 2.
* **(c) deep tail at $100**: |model − measured| ≤ 2 hours OR ratio ∈ [0.5, 2.0].

These bands are chosen to reproduce FFR-8A §2.2's own recorded judgments on the
archive basis (fallback-2024 reproduced at ratios 0.62/0.69/Δ2/0.93; table-2024
refuted at 2.65×; fallback-2025 refuted at 0.27; table-2025-magnitude refuted at
0.21) — they are a formalization of the standard already applied, fixed before the
settled numbers are computed. The probe emits the verdict mechanically.

**REPRODUCES-BOTH(S)** := REPRODUCES(S, 2024) ∧ REPRODUCES(S, 2025).

Branches, exhaustive:

* **Exactly one S with REPRODUCES-BOTH** → that S is the validated transcription;
  proceed to Phase B1/B2 (§5) with that S as the single delta.
* **Both S** (not expected, handled anyway): the **published NP6-576-ER table**
  is taken — a legitimacy tiebreak fixed here (the published design's own
  parameters outrank the shipped flat approximation under rules 13/14); never a
  fit comparison.
* **NEITHER** → **E3 STAYS ESCALATED and the lane STOPS at B0.** No build, no
  `--set`, no LP, no year solved or scored, no run registered, no matrix cell or
  row edit (rule 28(b) attaches to a mechanism test; a reproduction test that
  cancels the build is not one). The finding records the settled-basis table at
  full magnitude and the sharpened escalation; recommendation to the owner only.

## 5. PHASE B1/B2 — CONTINGENT A/B (executed ONLY on a §4 validation branch)

* **Recipe**: the CURRENT keeper `2026-08-15-ercot204-rule26-delete` via
  `scripts/replay_keeper.py`; control = keeper recipe verbatim; arm = ONE delta,
  `--set ordc_lolp_params_path=data/raw/_validation-source/ercot_ordc_lolp_params.csv`.
  Years **{2023, 2024, 2025} sequential, one invocation per arm** (rules 12/16).
  Solve-environment pin per ercot-204's recorded procedure: highspy/pandas/pyarrow
  pinned to `run_config.json`'s versions; `./.venv/bin/python` directly.
* **Registration (rule 15), both arms, whatever the outcome**, on the BACKCAST
  registry. Evictions named ex ante: ERCOT stands at 15/15; registering two runs
  displaces the two oldest unprotected — **`2026-08-08-run178-control`** and
  **`2026-08-09-ercot185-shaped-control`**. Neither is the keeper.
* **Guards, direction-blind, protecting every PASSing gate** (verdicts read from
  gates only, never the sign or size of a residual): G-REPRO (control vs keeper
  sidecars byte-identical); C1/C2/C4/C8 hold; C3a-2024/2025 keep PASS and move
  ≤1.0 pp; C3b-2024/2025 stay ≤0.20 and move ≤0.02; G-SHED shed hours not
  increased (4/1/0 hour lists); G-C3c matched-hour tails not worsened; G-COAL148
  above-ceiling rise ≤0.5 TWh; G-DOF `n_entries` 18 / `n_residual` 6 unchanged,
  **zero new scalars**; G-SPUR no new spurious mid-band scarcity hours beyond
  the counts guard.
* **2023 is SIDE-EFFECT-REPORTED at full magnitude under the card-R ceiling**
  (the ~0.59 C3b-2023 floor stated ex ante) and is **never a basis**: Q-B FINAL
  (no C3a-2023 spend of any kind) and R-A (no C3b-2023-targeted determination
  rounds) are cited here and not re-litigated. The lane is armed on 2024/2025
  input/parameter correctness alone; fit gain is NOT predicted (ercot-145b
  posture verbatim).
* **Rule 28**: no new `ScenarioConfig` field ⇒ rule 28(c) not engaged (no row
  minted); the post-A/B 28(b) cell verdict lands on the `energy_reserve_coopt`
  family row's ERCOT cell (currently `K`, ev ercot81), with
  `ordc_lolp_params_path` recorded as that family's sub-scalar per the ercot-156
  literal-registration template; `scripts/check_mechanism_matrix.py` must exit 0.
* **KEEPER CANNOT CHANGE IN-SESSION** in any outcome — promotion is a separate
  owner sitting; this lane produces a recommendation only.

## 6. FENCES (cited, binding, none re-litigated)

**Q-B FINAL** (ercot-190/191: no further ERCOT C3a-2023 spend) and **R-A**
(`docs/DECISION-CARD-ercot193-determination-ceiling-2026-08-13.md` RESOLUTIONS:
hold NOT-YET; no C3b-2023-targeted determination rounds; 2023 appears in this lane
only in ceiling citations and side-effect reports). **L-SCAR §4 must-nots**
(`docs/DECISION-CARD-lscar-screen-revenue-2026-08-13.md`) bind any mechanism
touched — this lane is not an L-SCAR successor and touches no screen mechanism;
the must-nots that reach it are honoured by construction: no ORDC double-count
(rule 19 — the delta re-parameterizes the ONE armed formation mechanism, stacks
nothing), no refused-channel re-open, no holdout spend (rule 22: solve/score
{2023, 2024, 2025} only, 2022 bridged never solved, data intake unrestricted; no
`complete`/`final` marker exists, none is sought), no ISO boundary crossed
(rule 25: ERCOT only). **V0 (FINDING-ercot195) and ercot-201 are DO-NOT-REDO**:
no tightness-conditioned identification, no E1 dispersion repair, no
measured-RTOLCAP-distribution parameterization — the E3 delta's parameters are
the published NP6-576-ER constants, not telemetry-derived; measured RTOLCAP
enters B0 only as the reproduction test's EVALUATION series, the exact
validate-never-parameterize role FFR-8B §4 licenses. Rule 27: Fable, edit-local,
blob-verify every pushed file ≥300 lines. No workflows, no cron.

**STOP conditions**: surface mismatch against §2 (none found — §2 is the
confirmation); B0 NEITHER branch (§4 — stop is the pre-registered outcome, not a
failure); any must-not conflict; OOM/infeasibility in a contingent solve
(register what completed, report). **LANDING**: push-and-stop, NO PR, owner
merges.
