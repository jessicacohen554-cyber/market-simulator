# PREREG nyiso-213 — RE-SCREEN of `cc_summer_derate_reconciled_basis` with S-1 and S-2(c) written correctly

**Session:** nyiso-213, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-b6er34`, fast-forwarded to `main` at **`5930e533`** (nyiso-212's
PR #5436 is MERGED, so the mechanism is at HEAD). **Date:** 2026-09-07.
**Keeper:** `2026-09-06-nyiso-202-startup-aware` — CALIBRATED, grade 7/8, fails 0, C3c the lone
ledgered caveat. **Committed and pushed BEFORE the re-screen solve is launched.**

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES TO FIX.** NYISO's keeper reads CALIBRATED with **zero
failing criteria**. Nothing in this session is selected because a residual moved, and no gate below
reads a target residual (rule 1 `[R-STRUCT]`, rule 23 `[R-FROZEN-DERIVE]`, rule 29 `[R-SCREEN]`: a
screen may KILL an arm, never promote one). The arm re-screened here is the rule-19 `[R-ONE-MECH]`
construction repair measured by
`docs/FINDING-nyiso212-cricket-valley-summer-seam-2026-09-07.md`.

**Owner's standing formula, carried verbatim:** *"Is this a recommended keeper candidate? If so plz
promote. If structural integrity improves but gates regress that may still be a keeper.."* It
attaches only to a full-span arm; this screen decides only whether the span is spent.

---

## 0. Why there is a re-screen at all, and the disclosure that goes with it

nyiso-212 pre-registered five gates, spent ONE LP on 2025, and **killed its own arm on the literal
reading of two gates whose wording was its own** — refusing to rewrite them after seeing the
numbers, and leaving the 2023–2025 span unspent (`FINDING …` ADDENDUM §11). The three gates that
carry the mechanism's structural claims — **S-3 confinement, S-4 no load-bearing flip, S-5 the
contradiction removed** — all PASSED, S-5 exactly as phase 0 predicted. The two that failed did so
for reasons that say nothing about the mechanism:

* **S-1** counted the `--year` selection as a recipe difference, and bucketed the armed flag itself
  as a "new dataclass default" rather than as the live delta;
* **S-2(c)** assumed the reconcile table's `mode` label predicts which way a plant's summer ceiling
  moves. It does not — the direction is one inequality, and the file that falsifies the assumption
  (`_nyiso212_arm_phase0.json`) was **committed before that PREREG was written**.

nyiso-212's §11.4 prescribes the two corrections; this document writes them, before measuring
anything.

**DISCLOSURE, stated rather than buried.** I have seen nyiso-212's 2025 screen numbers — they are
in the committed FINDING and in this session's handoff, and there is no way to unsee them. A
re-screen with the prior run's numbers in hand has **less evidential force than a blind one**, and
that is a real cost of nyiso-212's kill, not a technicality. What keeps this a pre-registration
rather than gate-fitting:

1. **Both corrections were prescribed by the session that killed the arm**, in its own committed
   addendum, before this session existed.
2. **Each correction is derived from the mechanism's identity, not from which plants passed.** The
   year-key exclusion follows from how `--replay-bundle … --year 2025` constructs a one-year record
   from a three-year bundle's; the ceiling-direction inequality follows algebraically from the flag
   itself, which replaces `net_summer/nameplate` with `min(1, net_summer/carried)`.
3. **The corrected S-2(c) is STRICTER in coverage than the gate it replaces** — it bounds **all 15**
   reconciled plants individually, where the original bounded only 3 — and it can still kill.
4. It is committed and pushed **before** the solve.
5. **§7 declares a third outcome that voids the screen entirely**, disjoint from both verdicts, and
   it is falsifiable by the very first numbers the solve produces.

---

## 1. The arm — unchanged from nyiso-212

`ScenarioConfig.cc_summer_derate_reconciled_basis = True` on the keeper's committed recipe, through
the replay override channel (`--replay-bundle` + `--cc-summer-derate-reconciled-basis`), so
**G-DELTA is by construction exactly one value**. Mechanism: at each of the 15 CC_REGULAR plants
`cc_capacity_reconcile_NYISO.csv` lists (12 `cap` + 3 `raise`), the Jun–Sep availability multiplier
becomes `min(1, net_summer / capacity actually carried)` instead of `net_summer / nameplate` applied
to an already-reconciled capacity. **Zero free parameters** (rules 21 `[R-DOF]` / 24 `[R-REGISTRY]`).
Nothing else moves.

## 2. Phase 0 (zero LP) — cleared, and REPRODUCED AT HEAD this session

The pre-solve gate is the committed `_nyiso212_arm_phase0.json`. This session **re-ran both probes
from scratch at HEAD** (`nyiso212_overceiling_decomposition.py`, then
`nyiso212_arm_phase0.py`; caches were empty) and **both regenerated records are byte-identical to
the committed ones** — `git status --porcelain` empty on both files, all three years. The 2025 row
this screen is written against:

| check (2025) | value |
|---|---|
| F-1 footprint | 81 of 809 units moved, **all CC_REGULAR**, exactly the 15 reconcile-table plants; `pmax`, heat rate and `mc_base` identical; **off-summer hours untouched** |
| F-2 identity | ON/OFF summer ratio = `min(1, ns/carried) / min(1, ns/nameplate)` at every moved plant to **2.2e-16** |
| F-3 Cricket Valley 57185 | summer factor 0.747075 → **0.902140**; summer available energy **1,812.38 → 2,188.56 GWh (+376.18)**; summer hours meter-above-ceiling 2,225 → 1,638; **months meter-over-ceiling `[6,7,8]` → `[]`** |
| class Jun–Sep available energy delta | CC_REGULAR **+892.95 GWh**; no other class moves |

**Per-plant summer capability delta ΔC_p (GWh over the 2,928 Jun–Sep hours), 2025, read from that
committed file** — this is the table the corrected S-2(c) is bounded by, and it is the file whose
mis-reading killed nyiso-212's gate:

| plant | reconcile `mode` | carried MW | nameplate MW | net summer MW | **ΔC_p (GWh)** | ceiling direction |
|---|---|---:|---:|---:|---:|:--|
| 57185 Cricket Valley | cap | 1,086.9 | 1,312.5 | 1,016.1 | **+511.52** | ROSE |
| 55405 Athens | cap | 1,064.7 | 1,221.6 | 984.4 | +370.10 | ROSE |
| 56940 CPV Valley | cap | 696.1 | 770.5 | 654.2 | +185.05 | ROSE |
| 54574 Saranac | cap | 251.5 | 285.6 | 237.8 | +83.16 | ROSE |
| 7314 Flynn | cap | 108.2 | 170.0 | 139.5 | +56.80 | ROSE |
| **50978 Carr Street** | **raise** | 80.0 | 122.6 | 93.0 | **+56.51** | **ROSE** |
| 54593 Batavia | cap | 42.9 | 66.2 | 48.8 | +33.09 | ROSE |
| 54592 Massena | cap | 53.6 | 102.1 | 81.0 | +32.50 | ROSE |
| 54034 Rensselaer | cap | 78.0 | 88.2 | 79.4 | +22.84 | ROSE |
| 50744 Sterling | cap | 43.9 | 64.2 | 54.8 | +18.74 | ROSE |
| 10620 Carthage | cap | 53.6 | 62.9 | 61.1 | +4.39 | ROSE |
| 10190 Castleton | cap | 71.2 | 72.0 | 67.0 | +2.05 | ROSE |
| 56234 Caithness | raise | 361.7 | 348.9 | 317.3 | −33.96 | FELL |
| 55375 Astoria Energy | raise | 610.4 | 595.0 | 558.0 | −42.16 | FELL |
| **56196 Zeltmann** | **cap** | 560.0 | 528.0 | 474.0 | **−84.03** | **FELL** |

Σ over the 12 `cap` plants = **+1,236.19 GWh**. The rule, verified over all 15 rows and algebraically
identical to the flag: **a plant's summer ceiling RISES iff its carried capacity is BELOW its
EIA-860 nameplate, and FALLS iff it is above.** The `mode` label comes apart from the direction in
**both** directions (Zeltmann is `cap` and falls; Carr Street is `raise` and rises), which is exactly
what nyiso-212's S-2(c) got wrong.

## 3. Screen year — 2025, by the mechanism's OWN measured footprint, never by residual

Unchanged from nyiso-212, and re-stated so it is not inherited silently. The seam is a constant MW
at each plant, so its footprint is the meter energy the constructed ceiling forbids: at 57185 that is
**292.3 GWh in 2025** against 220.8 (2023) and 222.0 (2024)
(`_nyiso212_summer_seam_census.json` → `cricket_valley_ceiling_counterfactual`), and the class
capability delta is largest in 2025 (+892.95 vs +860.3 / +878.8 GWh). The residuals of 2025 played
no part; C1-2025 CC_REGULAR is SKIPPED on the keeper (preliminary EIA-923 vintage), so 2025 is also
the year in which the target criterion is not even gated.

## 4. G-CTRL form 4 — the keeper's committed bundle is the control; G-DRIFT delta audited, ALL INERT

**No control solve is spent** (rule 29(b)). The keeper solved at `c7523509`. nyiso-212 audited
`c7523509..17c48f4e` hunk by hunk and read ALL INERT for a `mode="backcast"`, `iso="NYISO"` solve
(PREREG-nyiso212 §4, which this document adopts rather than repeats). **This session audits only the
delta `main` has added since**, as the handoff directs.

Measured first: `git diff a4676c67 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source data/raw/reference` is
**EMPTY**. So HEAD's solve-path content equals `a4676c67`'s, and the whole increment is
`17c48f4e..a4676c67` — **11 files, +502/−46**, which entered nyiso-212's branch by rebase onto
`1ee2efba` AFTER its screen solve ran at `f76c3011`. Every hunk, classified before this document was
written:

| file | classification | reason |
|---|---|---|
| `config/paths.py` | INERT | adds `SPP_HSL_DIR` / `SPP_WIND_SHAPE_DIR` and an `"SPP"` key in `WIND_SHAPE_DIRS`; NYISO is in neither map before or after |
| `config/scenarios.py` | INERT | one new field `ercot_ep_gas_basis_monthly: bool = False`, registered in `_CACHE_KEY_OPTIONAL_FIELDS` with default `"False"` in the SAME commit, plus its `TIER_TAGS` row; no existing default changed, no field removed |
| `config/iso_configs.py` | INERT | `_spp_config` only: the N↔S TTC placeholder 48,700 → 3,400 MW (lane SPP-53) and its citation comment |
| `data/transmission_expansion.py` | INERT | `TRANSMISSION_BASE_STATIC_VINTAGE["SPP"] 2025 → 2026` + comment; the `"NYISO": 2025` row is untouched |
| `pipeline/backcast_config.py` | INERT | `_SPP_OFFER_CURVE` (neutral 1.0 COAL bands) merged behind `if iso.upper() == "SPP"`; the NYISO branch is untouched |
| `data/fuel/basis/ercot.py` | INERT | `ercot_electric_power_gas_basis_monthly`, reachable only under `iso == "ERCOT"` and `ercot_ep_gas_basis_monthly=True` |
| `data/fuel/basis/meanzero.py` | INERT | adds `SPP_ZONAL_GAS_HUB_PATH`; **no applier is armed for SPP**, nothing reads it |
| `data/fuel/__init__.py`, `data/fuel/basis/__init__.py` | INERT | re-export lines for the two symbols above |
| `data/renewables.py` | INERT | adds `"SPP"` to `_UNCURTAILED_FALLBACK_ISOS` and `_WIND_ZONE_SHAPE_ISOS`, an SPP reference-rate reader, and refactors the MISO rate lookup into `_ANNUAL_REFERENCE_RATE_PROVIDERS`. **NYISO is in neither frozenset** (renewables.py:459 says so in terms), so the reference-rate path at :534 and the zone-shape path at :394 are never entered for NYISO |
| `…/wecc_intertie_lmp_hourly_CAISO.parquet` | INERT | a CAISO data file |

**Verified by execution, not only by reading** (all this session, at HEAD):

* the keeper's 810-field `scenario_config` reconstructs against HEAD's `ScenarioConfig` with **zero
  unknown fields**, and **`cache_key() = 942480d844dfeaa1`** — byte-identical to the value
  nyiso-212 recorded;
* `moved_rows("NYISO") == {}`, `SOLVE_EPOCHS == ()`;
* `cc_summer_derate_reconciled_basis` exists at HEAD, defaults `False`, and is **absent** from the
  keeper's record — so on the arm it reads absent(=`False`) → `True`, which is what S-1 asserts;
* the fleet instrument `nyiso196_rebuild_checks.py --year 2024` reproduces its committed record
  with the tree clean;
* **strongest**: the entire phase-0 chain, rebuilt from empty caches at HEAD, reproduces
  `_nyiso212_overceiling_decomposition.json` and `_nyiso212_arm_phase0.json` **byte-identically for
  all three years** — i.e. the NYISO fleet build at HEAD equals the NYISO fleet build at
  `f76c3011`, measured rather than argued.

**Rebase increment, audited after this document's §4 table was written and before the solve.**
`main` advanced `14dd09a7 → 5930e533` mid-session. On the audited solve paths that increment is
**one file, +15/−6**: `scripts/lib/transmission_expansion/spp.py`, a **docstring-only** revision
bringing that module's prose to the SPP-53 position (the 3,400 MW N↔South base and the 2026 limit
vintage). SPP-only by module path, no executable line changed — **INERT**. Re-verified at
`5930e533`: the keeper's config still reconstructs with **zero unknown fields**, `cache_key()` is
still **`942480d844dfeaa1`**, `moved_rows("NYISO") == {}`, `SOLVE_EPOCHS == ()`.

One carry-forward stated honestly: nyiso-212's audit found the **EIA-860 vintage resolver** to be
the one hunk on the shared backcast path unguarded by ISO or mode, inert only because
`eia860_vintage_year is None` and `eia860_vintage_tracks_solve_year` is absent/False on the keeper.
Both still hold at HEAD (the flag is absent from the 810-key record) and it is **not armed here**.

**Form 4 is therefore valid**: the arm differences against `results/calibration/nyiso202_startup_aware`
(2025) and the committed payload `frontend/data/backcast/runs/2026-09-06-nyiso-202-startup-aware.js`.

## 5. The command

    uv run python scripts/run_calibration_full.py --iso NYISO \
      --replay-bundle results/calibration/nyiso202_startup_aware --year 2025 \
      --cc-summer-derate-reconciled-basis \
      --out-dir results/calibration/_nyiso213_screen_2025 \
      --note "nyiso-213 rule-29 re-screen: keeper recipe + cc_summer_derate_reconciled_basis, 2025 only; DELETE BEFORE MERGE (rule 29c)"

One year, sequential. The bundle is a **throwaway diagnostic probe**: never registered, never a
keeper, never quoted as a keeper number, **deleted from `results/calibration/` before the PR merges**
(rule 29(c)); every number this session cites from it is carried in its FINDING.

## 6. Re-screen gates — STRUCTURAL, STOP-ONLY, declared before the solve

Scored by `scripts/probes/nyiso213_screen_gates.py` (the nyiso-212 scorer with **only** the S-1 and
S-2 verdict definitions replaced; the payload-rebuild instrument, whose identity against the
committed keeper payload nyiso-212 verified to max abs diff 0.0, is unchanged). Every value is
written to the record whatever the verdict, and **both readings are reported** — the corrected bar
and nyiso-212's literal bar side by side.

### S-1 recipe identity — **CORRECTED**

> Compare the arm's recorded `scenario_config` to the keeper's. Two keys are **excluded from the
> live diff**: **`weather_year`** and **`gas_price_override`**. Reason, declared: the keeper's
> `run_config.json` is a **three-year** bundle's record and carries its FIRST year's values
> (`weather_year` 2023, `gas_price_override` 2.54), while a **one-year** replay of 2025 records
> 2025's own. Those two keys encode the `--year 2025` selection that §5's command specifies — they
> are the screen, not a recipe difference. The exclusion set is **exactly these two keys and is
> closed**; any other key that differs still fails the gate.
>
> The armed flag is classified as the **LIVE delta**, not as a new dataclass default: the keeper's
> record predates the field, so its absence *means* `False`, and the arm records `True`. Any OTHER
> key absent from the keeper's record whose arm value equals HEAD's dataclass default is a new
> default, **REPORTED, not counted** (the nyiso-202 discipline).
>
> **BAR (arm KILLED if it fails):** the live recipe diff, so read, is **exactly**
> `{cc_summer_derate_reconciled_basis: absent(False) → True}` and nothing else, and the flag is
> `True` in the arm's record.

*Why this is structural:* it is the statement that the arm IS the keeper recipe plus one value. It
can still kill — any unexpected key, or a flag that did not take, fails it.

### S-2 direction + bound at the footprint — (a), (b) UNCHANGED; **(c) CORRECTED**

> **(a)** Δ summer (Jun–Sep) dispatch at 57185 ∈ **(0, +376.18] GWh** — the availability-inclusive
> ceiling relief from phase-0 F-3. Unchanged; this is the tight bound.
>
> **(b)** Δ summer dispatch summed over the 12 `cap` plants ∈ **(0, +1,236.19] GWh**. Unchanged.
>
> **(c) REWRITTEN on the MEASURED ceiling direction, over ALL 15 plants individually.** For each
> plant *p* with phase-0 summer capability delta ΔC_p from §2's table:
> * ΔC_p > 0 (ceiling ROSE): **Δ summer dispatch_p ≤ ΔC_p**. **No lower bound of any kind** —
>   relieving a bound never *compels* a unit to run, so a negative Δ is permitted and REPORTED as
>   merit re-allocation.
> * ΔC_p < 0 (ceiling FELL): **Δ summer dispatch_p ≥ ΔC_p**. No upper bound; a positive Δ is
>   permitted and REPORTED.
>
> In one sentence: **no plant moves further, in the direction its own ceiling moved, than its own
> ceiling moved.** A violation says the dispatch response at that plant is larger than the
> capability change that could have produced it — i.e. it is not this mechanism.

*The headroom in (c) is declared, not hidden.* ΔC_p is the **capability** delta (pre-availability);
the availability-inclusive relief is ΔC_p × the plant's mean summer availability, which is strictly
smaller — at 57185, 376.18 against 511.52, about 26 % headroom. That headroom is what absorbs
ordinary merit feedback, and it is why (c) is a confinement bar rather than an identity. Leg (a)
carries the tight bound at the one plant where phase 0 measured it.

*The old bar is retained as a reported statistic:* nyiso-212's `mode`-label reading (3 `raise`
plants, Δ ≤ +1 % of keeper summer) is computed and written to the record, marked as the superseded
reading, so the correction is auditable rather than merely asserted.

### S-3 footprint confinement — UNCHANGED

> Δ annual CC_REGULAR energy ∈ **[0, +892.95] GWh**; Δ off-summer dispatch at the 15 plants is
> REPORTED (merit feedback only — their off-summer bounds provably did not move, phase-0 F-1);
> Σ over all classes of Δ annual energy is REPORTED against a fixed load.

### S-4 no non-target load-bearing PASS → FAIL flip — UNCHANGED

> In 2025 no load-bearing criterion that is PASS on the keeper reads FAIL on the arm: **C3a-2025**
> and **C3b-2025**. C1-2025 and C2-2025 are SKIPPED on the keeper for data completeness and must
> stay SKIPPED — a status change there is a data-vintage event, reported. **C8** is NOT computable
> for an unregistered screen bundle (it needs `legitimacy_diagnostics.json`, written only by the
> register path) — **reported, not faked**; the arm moves Jun–Sep availability at 15 CC_REGULAR
> plants and no floor, so the D-2 forced volume is untouched by construction. **C6** is an
> attestation written at registration; the arm is the keeper recipe plus one declared, default-off,
> zero-DOF construction flag (S-1).
>
> **Target criterion, declared so it is never gated:** C1 CC_REGULAR (SKIPPED in 2025 regardless).
> **Explicitly NOT a gate:** any change in C3a/C3b *magnitude* short of a PASS→FAIL flip, the
> CC_REGULAR volume residual, the price residual, the grade.

### S-5 the contradiction is removed — UNCHANGED (the object)

> In the arm bundle, 57185's dispatch never exceeds its ceiling, and the **METER** exceeds the arm's
> monthly ceiling in **no month** of 2025 (phase 0 predicts `[]`; the keeper has Jun, Jul, Aug).

## 7. Predictions — declared before the solve, with sign and magnitude

**PRED-A (favours the answer I prefer).** All five corrected gates clear; verdict **CLEARS**. In
particular S-5 closes exactly as phase 0 predicts: months meter-over-ceiling at 57185 = `[]`, max
dispatch above ceiling ≤ 0.001 MW.

**PRED-B (hurts the answer I prefer, declared so it cannot be discovered later).** The arm makes
2025's **price fit modestly WORSE**, in both load-bearing price criteria and in the same direction:
C3a magnitude moves from **−6.3 % to ≈ −7.3 %** (model mean LMP falling ≈ 0.6 $/MWh, 62.26 → ≈61.6),
and C3b NRMSE rises from **0.152 to ≈ 0.160**. Both stay PASS, so S-4 does not fire. Under rule 1
`[R-STRUCT]` this is **reported at full magnitude and is not a reason to reject the repair — and
equally, it is not a reason to accept it, and it will not be tuned away.** If the span is spent and
the regression persists in 2023 and 2024, it is stated on the determination basis of any promotion,
not smoothed over. PRED-A and PRED-B are mutually consistent by construction: they are exactly the
case rule 1 anticipates — a structurally-correct mechanism whose residual moves the wrong way.

**PRED-C (the disjoint third outcome, which VOIDS the screen).** nyiso-212's screen solved at
`f76c3011`; this one solves at `5930e533`, and the solve-path tree differs by the 11 files (+1 docstring) §4
classifies INERT. If that audit is right, this re-solve **reproduces nyiso-212's numbers exactly**.
Declared to tolerance:

| quantity | predicted | tolerance |
|---|---:|---|
| Δ summer dispatch at 57185 | **+258.39 GWh** | ±0.01 |
| Δ annual CC_REGULAR | **+567.95 GWh** | ±0.01 |
| Δ annual ST_GAS | **−313.89 GWh** | ±0.01 |
| C3a arm model mean LMP | **61.58 $/MWh** | ±0.01 |
| C3b arm NRMSE | **0.160** | ±0.001 |
| months meter over arm ceiling at 57185 | **`[]`** | exact |

**If any of these misses, PRED-C fires: the G-DRIFT audit in §4 is falsified, the screen is VOID,
and the session's result is that finding — not a verdict on the arm.** PRED-C is disjoint from both
PRED-A and PRED-B: it is a statement about the instrument, not about the mechanism, and it is
falsifiable by the first numbers the solve produces.

**If any gate fails:** the arm is killed, the full span is never spent, the screen bundle is deleted,
and the kill is the session's result. **If all clear:** the full span is solved as ONE
`--year 2023 2024 2025` invocation of the same replay + flag (rule 16 `[R-ALLYEARS]`), scored
artifact-only, and only then does the owner's formula apply. A promotion additionally owes D-5(b)
(re-verify the determination artifact-only before re-keying `complete.NYISO.keeper`; a **WORSE**
determination **STOPS** the promotion), the 2022 touchpoint replay + `stamp_touchpoint_holdout.py`,
`build_status.py --iso NYISO`, the forecast gate (a) re-key, and pruning of the superseded
touchpoint — all in the same PR.

## 8. What this re-screen does not decide

* Whether NYISO should instead **disarm** `cc_capacity_reconcile` (the caiso-185 disposition) — a
  keeper-recipe question the FINDING §5 records and does not prejudge.
* **Object (B)**: why the model under-dispatches Cricket Valley even at corrected availability
  (4,109.4 GWh against a 4,861.8 GWh meter in 2025). Untouched, still open, reported not absorbed.
* The WEFOR residual on a demonstrated-peak cap and the net-summer-vs-measured-summer-peak gap.
* The three `raise`-row plants' summer over-statement — the seam's other sign.
* The five pending owner rulings — untouched, and no new card is opened.

*(nyiso-213 re-screen, 2026-09-07. Gates written before the solve; a kill is still a success, and
so is a void.)*
