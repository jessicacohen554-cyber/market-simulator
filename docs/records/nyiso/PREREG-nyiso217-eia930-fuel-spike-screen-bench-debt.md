# PRE-REGISTRATION — nyiso-217: paying the C1/C4 benchmark debt on `_screen_fuel_spike_columns`

**Session:** nyiso-217, NYISO backcast calibration. **Branch:**
`claude/nyiso-backcast-calibration-bzuqb3`, on `main` at `12e71b89`. **Date:** 2026-09-07.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — nothing promoted, armed, screened or registered is
contemplated by this session; no marker moves.

**THERE ARE NO IN-SAMPLE RUBRIC FAILURES.** NYISO's keeper reads **CALIBRATED** across 2023–2025
with **zero** failing criteria, C3c the lone ledgered caveat. Nothing below is selected because a
residual moved (rule 1 `[R-STRUCT]`); no residual is consulted at any point. The 2022 held-out rung
carries C1/C3a/C3b failures and is named **nowhere** as a target (rule 22 `[R-HOLDOUT]`).

**ZERO LP.** No solve, no screen bundle, no control bundle. Nothing to delete before merge under
rule 29(c).

---

## 1. The object, and why it is owed

`src/market_sim/data/eia930/actuals.py::_screen_fuel_spike_columns` (lane SPP-41, 2026-09-07)
screens EIA-930 `NG: <CODE>` unit-slip hours for **every** BA, at the one seam every reader in that
module obtains its frame through. It can therefore move the C1/C4 benchmark and the delivered VRE
profile. **NYISO has never checked it.** nyiso-215 §7 flagged it and was out of scope; nyiso-216 §1
discharged it for the **fleet** path by execution and explicitly **passed the benchmark half
forward** ("a NYISO lane that re-solves or re-scores C1/C4 still owes it a check"). Two sessions
have carried it. This session pays it.

The question is **zero-LP** and is a genuine fork: does the screen move NYISO's EIA-930-derived
benchmark at all; if it does, does that move reach a **scored** quantity; and if it does not, that
is a clean negative that closes the debt.

**This is not a rubric failure to tune.** If the screened benchmark differs from the committed one,
rule 14 `[R-ACCURATE]` says the screened (more accurate) benchmark stays even if the fit worsens,
and the correct response is to quantify and report, never to weaken the screen.

---

## 2. §0 — WHAT IS ALREADY IN HAND (disclosed before any prediction is written)

Rule 29 step-0 census work legitimately precedes this PREREG. Everything below was established
**before** §4's predictions were written, and nothing else was.

**(C-1) The artifact chain, read from source.**
`eia930.actuals.load_eia_hourly_benchmark` (screened at HEAD)
→ `run_calibration_full._eia930_frame_generic` (a pass-through: it reshapes that dict to long
format and does nothing else)
→ the bundle's `inputs/eia930.parquet`
→ `render_calibration_html` (`bundle_input_path(bdir, "eia930")`, line 1333 — it reads the
**bundle's parquet**, never the live loader)
→ `frontend/data/backcast/bench/NYISO/<year>.json.gz` (**committed**)
→ `scripts/calibration_verdict.py`.

**(C-2) The keeper bundle is SLIM.** `results/calibration/nyiso213_summer_seam/` holds
`calibration_attestation.json`, `hourly/`, `legitimacy_diagnostics.json`, `meta.json`,
`metrics.json`, `run_config.json` — **no `inputs/`**, so no `eia930.parquet` is committed. The
committed bench part is the only surviving artifact of that benchmark.

**(C-3) The screen is OUT of the HARD freshness gate by construction.**
`scripts/lib/bench_stamp.PAYLOAD_SOURCES` is exactly
`("scripts/render_calibration_html.py", "scripts/render_backcast.py", "scripts/lib/backcast_artifacts.py")`.
The engine (`src/market_sim/`) is deliberately excluded and reported only in
`check_bench_freshness.py`'s SOFT tier ("reported, never gates").

**(C-4) SPP-41's own declared NYISO effect**, from the `_screen_fuel_spike_columns` docstring:
NYISO **2024 `other` 3.3846 → 3.3197 TWh** (1 hour, h6759) and NYISO **H1-2026 `other`
5.3153 → 5.1552** (3 hours, h2957–2959). No other NYISO series or year is claimed to move.

**(C-5) C1 (`score_fuelmix`) reads `ypay["gmModel"]` and `ybench["classFull"]` only**;
`a_gen = Σ classFull.values()`; `vol_band = min(max(2 % load, 3 % a_gen), 8 TWh)`. `e930` is not
read by C1. The gated class set is `(*GAS_CLASSES, *COAL_CLASSES) − FUELMIX_EXCLUDED`.

**(C-6) `e930` reaches `classFull` through exactly two writers in `render_calibration_html`:**
(i) the VRE mirror (`classFull[wind|solar] ← e930[wind|solar]`, lines ~1829–1835), and
(ii) `reconcile_vintage_classes`, whose target is
`_tgt = e930.gas + e930.coal − max(0, classFull.OTHER + classFull.biomass − e930.other)` and which
rescales **every** fossil class by `_tgt/_cur` — but **only** when `_cur` falls outside the
`_VINTAGE_RECONCILE_FRAC` band around `_tgt`. Two independent switches sit between an `other` move
and C1.

**(C-7) C2 (`score_sysvol`) subtracts `bs.gas_foldin_deflation(cf, e930, iso)` from the gas-family
actual directly at score time** (line ~1689), with no reconcile band in the way.

**(C-8) C4 (`score_dispatch_corr`) reads `ypay["fuelRows"]`** — a value committed in the run
payload — for families `gas` and `coal` only, and recomputes on a CEMS basis only for
`CEMS_GAS_ANCHOR_ISOS`.

**(C-9) NYISO 2024 bench part key structure**, read (keys only, no values):
`bench = {plants, e930, classFull, ctOnly, avgLMP, storage, co2}`;
`e930 = {gas, coal, nuclear, wind, solar, other, coal_cems}`;
`classFull = {CC_CHP, CC_REGULAR, COAL_BIT, COAL_PRB, CT_CHP, CT_PEAKER, OTHER, ST_CHP, ST_GAS,
biomass, hydro, nuclear, oil, solar, wind}`; `meta.builderFingerprint = bee29e135d42`.

**(C-10) G-DRIFT, `51f2fc2d` → `12e71b89`** — **22 files, +9,879 / −23** (nyiso-216 audited 14 at
`71e62675`; the reasoning is inherited, the set is re-measured). **Twenty-one INERT**, one **LIVE**:

| file | verdict | reason |
|---|:--|---|
| `scripts/run_calibration.py`, `run_calibration_full.py`, `pipeline/__init__.py`, `pipeline/year.py`, `pipeline/commitment.py`, `runner.py`, `data/floor_mechanisms.py` | INERT | SPP-44 `spp_gas_commitment_bridge` wiring; ISO-exclusive on `iso == "SPP"`, default off, absent from the keeper's recipe |
| `config/constants.py` | INERT | `SPP_GAS_BRIDGE_*` constants + one CAISO 2022 monthly array |
| `config/solve_surface_declared.py` | INERT | two SPP-only registry drops |
| `config/fuel_trajectories.py`, `model/interchange/spec.py` | INERT | CAISO 2022 rows only |
| `config/scenarios.py` | INERT | two new default-off flags (SPP, ERCOT) absent from the keeper's recipe, plus the D76 `capacity_screen_peak_measured_hindcast` flip whose `__post_init__` coercion restores the frozen `False` for `not hindcast` |
| `results/cache.py` | INERT | the same D76 flip's key declaration; zero backcast key moves |
| `pipeline/backcast_config.py` | INERT | `_SPP_OFFER_CURVE` coal-band refactor, inside the `iso == "SPP"` dict |
| `data/fuel/__init__.py`, `data/fuel/basis/__init__.py`, `data/fuel/basis/ercot.py` | INERT | `ercot_zonal_gas_basis_source_group`, ERCOT branch |
| `data/raw/_validation-source/*` (README, SPP LMP parquet, CAISO 2022 demand CSV + provenance) | INERT | SPP / CAISO 2022 artifacts; NYISO reads none of them |
| **`data/eia930/actuals.py`** | **LIVE** | **the object of this session** |

The keeper's `run_config.json` confirms the D76 predicate: `mode = backcast`, `hindcast = False`,
`capacity_screen_peak_measured_hindcast = False`, `git.sha 51f2fc2d`, `git.dirty false`,
`solve_surface.fingerprint 48353917f7510af3`, years `[2023, 2024, 2025]`.

**(C-11) Environment.** `data/clean` built with `curate_capacity_deliverability.py` +
`curate_nyiso_interface_flows.py` only.

**Nothing else has been measured.** In particular I have read **no** bench *value*, no
`_VINTAGE_RECONCILE_FRAC`, no `classFull` number, and have **not** run the screen on any NYISO
frame. Those are §4's measurements.

---

## 3. Basis discipline and standing limits

* **CAMPD on both sides, in every year** where a CAMPD statistic is quoted — none is expected here;
  this session's object is the EIA-930 benchmark, not a plant-grain measurement.
* **C1 scores against bench `classFull`**, which sits below the CAMPD plant sum by −0.44 / −2.38 /
  −0.34 TWh in 2023/24/25. No CAMPD-basis gap is quoted as a C1 number.
* **The bench keys a split plant as `<code>:<group>`** (2500, 50292); keys are never folded.
* **EIA-923 2025 is the preliminary vintage**; a 2025 zero for a small plant is undefined, never a
  measurement. The keeper's own C1 2025 class cells are SKIPPED for that reason.
* **`metrics.json` is stale across six bundles in five ISOs** and is not read; verdicts come from
  `scripts/calibration_verdict.py`.
* **Rule 29(b) form 4 note, stated as a scope limit rather than a claim:** this session uses the
  keeper's committed artifacts as its **object of study**, not as a control for an arm, so the
  G-DRIFT audit above is recorded for completeness and no number here depends on the keeper bundle
  being a valid control.

---

## 4. THE PRE-REGISTERED GATES

Predictions are written now, before any of the following is computed. Each carries a **hurts** limb
declared to defeat my preferred answer (which is: the screen is inert for NYISO's scored quantities
and the debt closes as a clean negative).

### P1 — PROVENANCE, verified by EXECUTION, not by reading

**Construction.** Score the keeper with `scripts/calibration_verdict.py --run-id
2026-09-07-nyiso-213-summer-seam` twice at this HEAD: once unmodified, once with
`market_sim.data.eia930.actuals._screen_fuel_spike_columns` monkey-patched to the identity function
(and with `_ercot_hourly_frame_screened` left alone). Compare the two verdict outputs verbatim.

**Prediction: IDENTICAL**, byte for byte, including every C1, C2 and C4 record and the
determination. Rationale: C-1/C-2 say the scorer reads committed artifacts and never calls the
loader.

**Bar.** Any difference in any character fails the prediction.

**Hurts limb (declared to defeat me).** If the two differ, then the scorer *does* reach the live
loader, the committed-artifact reading in C-1/C-2 is **wrong**, and question (a) is answered the
other way round — a code change to the screen moves a keeper score with no registration at all,
which is a **more serious** finding than anything I expect and would be reported as this session's
headline.

**VOID condition.** If the monkey-patch cannot be shown to be in force (i.e. a control assertion
that the patched symbol is the identity fails), P1 VOIDS and I say so rather than reporting
"identical".

### P2 — DOES THE SCREEN MOVE NYISO'S LIVE BENCHMARK AT ALL?

**Construction.** For `year in {2022, 2023, 2024, 2025}` call
`load_eia_hourly_benchmark("NYISO", year)` twice at this HEAD — once with the screen live, once
with it monkey-patched to the identity — and diff **every** returned series on (i) annual TWh and
(ii) max absolute per-hour difference, and count flagged hours per `NG:` column.

**Prediction: exactly ONE series moves — `other` in 2024 only — by 3.3846 → 3.3197 TWh
(Δ = −0.0649), from exactly 1 flagged hour at h6759**; and **2022, 2023 and 2025 are byte-identical
in every series**. This is SPP-41's declared NYISO set (C-4) and nothing else.

**Bar.** SPP-41's two claimed NYISO-2024 numbers reproduce to **≤ 0.001 TWh** and the flagged-hour
index matches exactly. A miss on either is a **failed prediction**, reported as written.

**Hurts limb (declared to defeat me).** If **any** additional NYISO series or year moves — and
especially if `gas`, `coal`, `wind` or `solar` moves in any year — then the screen's NYISO blast
radius is **larger than SPP-41 declared**, the debt is **not** dischargeable as a clean negative,
and I will report the full moved set and escalate it as a cross-lane finding rather than absorbing
it into an NYISO note.

### P3 — DOES THE MOVE REACH `classFull`, AND THEREFORE C1?

**Construction, exact arithmetic on committed artifacts (no rebuild required).** From C-6, `e930`
reaches `classFull` only via the VRE mirror and via `reconcile_vintage_classes`. The VRE mirror is
disposed of by P2 (it can only fire if `wind`/`solar` move). For the reconcile, note that
`classFull.OTHER` and `classFull.biomass` are **not** members of `_GAS_GROUPS`/`_COAL_GROUPS`, so
the reconcile never rescales them and the **committed** values are the **pre**-reconcile values.
Therefore, from the committed bench part alone:

1. Compute `D(x) = max(0, classFull.OTHER + classFull.biomass − x)` at `x = e930.other`
   (committed) and at `x = e930.other + Δ` (P2's screened value).
2. Compute `_tgt(x) = e930.gas + e930.coal − D(x)` at both.
3. Determine whether the reconcile FIRED for the committed part, by testing whether
   `Σ committed fossil classFull` equals `_tgt(committed)` (fired) or lies inside the
   `_VINTAGE_RECONCILE_FRAC` band around it (did not fire) — these are mutually exclusive and
   jointly exhaustive given the code.
4. Report `∂classFull/∂e930.other` and the resulting per-class TWh move, if any.

**Prediction: the deflation is CLAMPED AT ZERO in 2024** — i.e.
`classFull.OTHER + classFull.biomass < e930.other ≈ 3.32 TWh` — so `D` is 0 at **both** values of
`x`, `∂_tgt/∂e930.other = 0`, `classFull` is byte-identical whether or not the reconcile fires, and
**C1 is unmoved**.

**Bar.** The clamp holds at both `x` values (a strict inequality with ≥ 0.001 TWh of headroom at
the tighter end), **and** the recomputed `_tgt` values agree to ≤ 0.001 TWh.

**Hurts limb (declared to defeat me).** If `D > 0` at either `x` **and** the reconcile fires, then
the screen **does** change what the keeper's C1 is scored against: every gas and coal `classFull`
class scales by `_tgt(screened)/_tgt(committed)`. I will then compute the per-class TWh move, the
resulting C1 status for every gated class, and report it — and, per rule 14 `[R-ACCURATE]`, the
**screened** benchmark is the one that stays even if the fit worsens. I will not propose weakening,
haircutting or bypassing the screen under any outcome.

**Exhaustive sub-partition of P3** (declared now, so no outcome can land in a gap):
(3a) `D = 0` at both `x` → C1 provably unmoved, reconcile state irrelevant.
(3b) `D > 0` at both `x` and the reconcile does **not** fire → `_tgt` moves but `classFull` does
not; C1 unmoved, with a **latent** exposure that fires if a future part crosses the band. Reported
as a named exposure, not absorbed.
(3c) `D > 0` at both `x` and the reconcile **fires** → C1 moves; quantify and re-score.
(3d) `D` straddles zero between the two `x` values → partial move; quantify exactly and treat as
(3b)/(3c) by whether the reconcile fires.

### P4 — C2, WHICH HAS NO RECONCILE BAND IN THE WAY

**Construction.** From C-7, C2's gas-family actual subtracts `gas_foldin_deflation` directly.
Compute that subtraction at both `x` values from the committed bench part.

**Prediction: unmoved**, by the same clamp as P3 (case 3a). If the clamp is **not** active, C2's
2024 gas-family actual falls by **exactly** `|Δ|` (P2's `other` move), because the deflation is
affine in `e930.other` above the clamp.

**Bar.** The two computed C2 gas actuals differ by 0 (clamped) or by exactly `|Δ|` to ≤ 1e-6 TWh
(unclamped). Anything else means my reading of `gas_foldin_deflation` is wrong and P4 VOIDS.

**Hurts limb.** C2 is a **load-bearing** criterion. If it moves, this is a scored-quantity move
even when P3 reads (3a), and the clean negative is **not** available. I declare in advance that a
C2 move alone is enough to defeat the "clean negative" verdict.

### P5 — C4, WHICH IS IMMUNE ON TWO INDEPENDENT COUNTS

**Construction.** (i) Verify `NYISO ∉ CEMS_GAS_ANCHOR_ISOS`, so C4 reads the committed
`ypay["fuelRows"]` unchanged. (ii) From P2's per-column flagged-hour counts, verify the screen
flags **zero** hours in NYISO's `NG: NG` (gas) and `NG: COL` (coal) columns in every year
2022–2025 — the only two families C4 scores.

**Prediction: BOTH hold** — C4 is unmoved because the value is committed **and** because the screen
touches neither family's series.

**Bar.** Both limbs hold. If (i) holds but (ii) fails, C4's committed value is still unmoved but
the *benchmark* is now known-stale for a scored family — I declare now that I will report that as a
**partial** result and **not** as a clean negative.

**Hurts limb.** If NYISO **is** in `CEMS_GAS_ANCHOR_ISOS` for any scored year, C4 recomputes from
`ybench` at score time and my two-count immunity argument is wrong on its first count; I report
that the argument rested on one count, not two.

### An ungated statistic I will report whatever it says

The **committed-vs-HEAD-rebuild** difference for NYISO's `e930` block — i.e. how far the committed
bench part's `e930` numbers sit from what HEAD's loader produces **with the screen live**, which
mixes the screen's effect with any other engine drift since the part was written. This is **not**
gated (it cannot isolate the screen, which is what P2 is for) and it cannot be computed for
`classFull` at all, because the keeper bundle carries no `inputs/` (C-2). I report it because it is
the honest context for "is the committed part what HEAD would produce", and I will report it even
if it cuts against the clean-negative verdict.

---

## 5. THE EXHAUSTIVE OUTCOME PARTITION, and the closure attached to each

Declared before measurement. Every possible result lands in exactly one branch.

* **(A) NO NYISO series moves in any year 2022–2025.** SPP-41's declared NYISO effect does not
  reproduce. → **CLEAN NEGATIVE**, and additionally a **failed P2 prediction** that contradicts
  SPP-41's own docstring, which I escalate rather than quietly enjoy.
* **(B) Exactly SPP-41's declared set moves (2024 `other`), and no scored quantity moves.** →
  **QUANTIFIED NULL. The debt is DISCHARGED and CLOSED**: the screen is measured, not assumed, to
  be inert for every NYISO scored quantity, with the arithmetic that makes it inert stated so a
  later session can re-check it in minutes. Any (3b)-style latent exposure is named.
* **(C) Exactly SPP-41's declared set moves, and a scored quantity moves** (C1 via P3(3c)/(3d), or
  C2 via P4). → **SCORE MOVE.** Quantify the per-class move, re-score the keeper against the
  screened benchmark, report the result at full magnitude whichever way it goes. Rule 14 keeps the
  screened benchmark. This also makes the committed bench part provably not what HEAD's builder
  would produce, which is an owner-facing item; I will state it as such and **not** regenerate the
  part or re-key any marker in this session.
* **(D) A series outside SPP-41's declared set moves** (any year, any series). → **BLAST RADIUS.**
  Report the full moved set, then split by whether a scored quantity moves and apply (B) or (C)'s
  closure on top. Escalate as a cross-lane finding, since the same seam serves every BA.

Branches A–D are exhaustive: A is "nothing moves"; B/C/D partition "something moves" by
(is the mover inside SPP-41's declared set?) × (does it reach a scored quantity?), with D
absorbing the out-of-set case in both of its own sub-cases.

---

## 6. WHAT THIS SESSION WILL NOT DO, WHATEVER IT MEASURES

* **No lever is sized**, proposed, armed or screened. No `ScenarioConfig` field is added or flipped.
* **No other ISO's bench is touched**, read for comparison, or regenerated (rule 25 `[R-ISO-SCOPE]`;
  the screen serves every BA, and the other BAs' numbers are their lanes').
* **No bench part is regenerated** and **no keeper is promoted or re-keyed**; D-5(b) does not
  attach because no promotion is contemplated.
* **No marker moves.** 2020/2021 stay unspent and are a separate owner spend; `final` stays never
  granted; the locked-test freeze is untouched. **No out-of-training year is solved, scored or
  registered** — 2022 appears in P2 only as a *loader input diff*, which is data preparation and
  explicitly unrestricted under rule 22's "what is held out is the SCORE, never the DATA".
* **No eighth owner card is opened.** The seven pending rulings are untouched and none is
  prejudged; cards (vi) and (vii) get no form.
* **The screen is never weakened.** Under every outcome, rule 14 `[R-ACCURATE]` governs: if the
  screened benchmark makes a fit worse, the screened benchmark stays and the miss is a discovered
  root-cause question, not a reason to revert.

---

## 7. Method commitments

* No gate is restated after its number is seen. A prediction that misses is **a result**, reported
  as written.
* If a gate VOIDs, I state **what I did not isolate** rather than guessing.
* No analytic claim is asserted that I have not tested; where an ordering or an identity is needed,
  it is measured.
* An ungated statistic that cuts against my preferred answer is disclosed **in place**.

*(nyiso-217. Written and committed before P1–P5 were measured.)*
