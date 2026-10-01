# PRECOMMIT miso-231 — the HOURLY neighbour-anchored PJM seam ladder: `pi_k(t) = border(t) + delta_k`, screened on 2024

**Pushed BEFORE the screen solve.** Everything a gate reads — the construction,
the eight offsets per year, their derivation, the G-DRIFT audit, the screen year
and the rule that named it, the pre-solve arithmetic and the five gates with
their numeric bars — is fixed in this document and in the committed artifacts it
cites, so no number here can have been written to fit a result.

**KEEPER (the control, rule 29(b) form 4): `2026-09-06-miso-230-ctdrag-seam`**
(`miso230_ctdrag_seam_K`, git sha `284722a04`), CALIBRATED, C3c the single
ledgered caveat. Rule 22: **2023–2025 only**. DOF ledger unchanged at **41/2** —
this mechanism adds **no free parameter** (§2).

Executes the successor miso-226 named and miso-230 carried forward unchanged:
*"an HOURLY neighbour anchor reading the hourly PJM western-border DA the
incumbent derive already loads, instead of a frozen annual quantile of it — the
only construction on the board that can move the correlation rather than its
level."*

---

## 0. The defect, and the non-claim this arm exists to convert

The promoted annual neighbour ladder repairs the seam's **level** and not its
**responsiveness**. miso-226 measured that and the miso-230 keeper carries the
non-claim forward verbatim:

| | keeper | promoted arm | **MEASURED** |
|---|---:|---:|---:|
| corr(imports, own price) | +0.750 | +0.725 | **−0.101** |
| price-decile slope d1−d10 | −3,573 MW | −3,217 MW | **+1,322 MW** |

3 % of the distance on the correlation; 10 % of the sign error on the slope.
miso-226's structural reason: **the ladder is a FIXED price ladder the LP clears
against its OWN internal price**, so re-anchoring moves the band levels and not
the response — the bands still leave merit exactly when MISO's price falls,
which is when MISO actually imports most.

## 1. The construction — zero fitted parameters, and BOTH halves already registered

Band `k`'s offer becomes hourly:

```
pi_k(t) = pjm_border(t) + delta_k        (import)
sigma_k(t) = pjm_border(t) + delta^x_k   (export)
```

so band `k` clears in hour `t` iff `MISO_price(t) > border(t) + delta_k`, i.e.
iff `spread(t) > delta_k`.

**Nothing here is new.** It is the synthesis of two mechanisms this repo has
already built, registered and adjudicated:

| half | existing mechanism | matrix cell | what it contributes |
|---|---|---|---|
| the **hourly measured anchor** | `miso_pjm_lmp_import_pricing` — prices every PJM tranche at the *measured hourly* PJM western-border DA via `eia_loader.measured_miso_pjm_border_prices` | `import_hub_pricing` **K** | that the hourly border series is an admissible **live solve input** |
| the **Q-Q depth ladder** | `miso_seam_measured_ladder` / `..._neighbour_anchored_ladder` — the per-band Q-Q duration coupling | `seam_neighbour_anchored_ladder` **K**, keeper-armed | the per-band depth slope |

The existing hourly flag prices **every** band identically (`mc[row,:] =
prices + hurdle`, "no flow-responsive slope"); the existing ladder has a slope
but is **frozen annually**. This arm is the first with both. The only new object
is the `delta_k` table, and it is derived, not chosen.

**The rule-13 `[R-MEASURED]` position is the registered flag's own, unchanged**
and quoted from `scenarios.py`: *"Measured neighbor price-formation input, blind
to MISO's own flow (reads only PJM hub LMP)."* It is the **price of a purchased
input** — the same admissibility class as a delivered fuel price, which rule 13
names — not MISO's own outcome. The forward analogue is already in the code: a
forecast year falls through to the **gas-elastic reference-price formula**,
which is itself hourly and responsive, so the backcast here reads the *measured
counterpart of the quantity the forecast computes*. That is a **stronger**
rule-13 position than the annual ladder, which has no hourly forward analogue at
all.

**No hurdle is added on top** (rule 19 `[R-ONE-MECH]`): `delta_k` is a measured
quantile of the spread and already embeds delivery/wheeling, exactly as the
incumbent ladder's own docstring states of its prices. This overwrite runs in the
ladder's slot and **displaces** the annual overlay — alternatives, never stacked.

### 1a. Why this is NOT the refuted spread hurdle

`derive_miso_seam_ladders`'s docstring records why the seam was moved OFF a
spread basis: a hurdle-gated arbitrage seam structurally deletes the flow,
because the measured flow *"is uncorrelated with the RT LMP spread (r = +0.06)"*.
Two differences, **measured** in phase 0 rather than asserted:

1. That statistic is the **RT** spread against MISO's hub. The **DA** spread
   against the **PJM western border** — the series the owner's ruling actually
   points at — correlates with measured flow at **+0.240 / +0.265 / +0.194**
   (2023/24/25), against `corr(flow, MISO DA)` of **−0.136 / −0.039 / −0.059**.
   The spread carries the sign the seam needs; MISO's own price carries the sign
   the model has backwards.
2. **A hurdle is one threshold; this is the same 8-band ladder.** The Q-Q
   coupling puts the shallow bands at **negative** offsets — band 1 at
   **−$29.17** in 2023 — so they clear even when MISO is far below PJM. That is
   precisely the *"46–56 % of measured import MWh moves at spreads inside/below
   the $2 hurdle"* the docstring says a hurdle deletes. **Nothing is gated away**,
   and the measured annual volume is reproduced (§3, readout A).

## 2. The derive — `derive_miso_seam_ladders.py::derive_pjm_neighbour_hourly` (rule 23 `[R-FROZEN-DERIVE]`)

**Byte-for-byte the incumbent estimator, third series.** Same `_derive_one` /
`qq_import` / `qq_export`, same midpoint-depth grid on the same
`SEAM_FLOW_TRANCHES` (8), same measured EIA-930 seam flows, same same-seam
no-wash reconciliation. The only change is which measured series the duration
coupling reads:

| ladder | series read |
|---|---|
| incumbent (`MISO_SEAM_LADDER_BY_YEAR`) | MISO hub DA |
| promoted annual (`..._NEIGHBOUR_BY_YEAR`) | PJM western-border DA |
| **this** (`..._NEIGHBOUR_HOURLY_BY_YEAR`) | **DA − border SPREAD** |

The no-wash reconciliation carries through unchanged: both directions share the
same `pjm_border(t)`, so an ordering constraint on the offsets is the same
constraint on the applied hourly prices.

**The derived offsets `delta_k` ($/MWh), import side, fixed here before the solve:**

| year | k=1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| 2023 | −29.17 | −9.84 | −3.98 | −0.11 | 2.43 | 4.62 | 7.05 | 11.20 |
| **2024** | **−13.87** | **−6.23** | **−1.91** | **1.04** | **3.46** | **6.18** | **10.47** | **19.31** |
| 2025 | −15.79 | −6.12 | −0.67 | 2.64 | 5.82 | 9.68 | 16.93 | 29.86 |

Monotone rising in every year. **DOF: zero** — every value is a quantile of a
measured series at a structurally fixed depth grid, none identified against a
price or volume residual, and rule 23 freezes the script against residuals.

**PJM ONLY**, and that is a DATA boundary rather than a choice (rule 14
`[R-ACCURATE]`'s misalignment clause): no measured SPP or SOCO/TVA price series
is held under `data/raw`, so those seams keep the incumbent anchor. Identical to
the promoted ladder's own boundary.

## 3. Phase 0 (rule 29 clause 0) — **zero LP**, two independent readouts

`scripts/probes/_miso231_hourly_seam_phase0.py` →
`results/calibration/_miso231_hourly_seam_phase0.json`.

### Readout A — OFFLINE, driven by the MEASURED record. **Contains no model output at all.**

All three ladders driven by the measured MISO DA and measured border, scored
against the **measured seam flow**:

| year | arm | mean MW | corr vs MISO DA | slope d1−d10 | **corr vs measured flow** |
|---|---|---:|---:|---:|---:|
| **2023** | measured flow | 4,674 | −0.136 | +1,303 | — |
| | incumbent | 4,650 | +0.819 | −5,273 | **−0.253** |
| | annual neighbour | 5,302 | +0.791 | −4,402 | **−0.262** |
| | **hourly** | **4,649** | **+0.254** | **−1,635** | **+0.271** |
| **2024** | measured flow | 3,678 | −0.039 | +1,384 | — |
| | annual neighbour | 4,028 | +0.740 | −4,633 | **−0.283** |
| | **hourly** | **3,673** | **+0.279** | **−1,284** | **+0.278** |
| **2025** | measured flow | 3,198 | −0.059 | +948 | — |
| | annual neighbour | 3,442 | +0.814 | −5,099 | **−0.164** |
| | **hourly** | **3,199** | **+0.257** | **−1,598** | **+0.260** |

Three things this says, none of them about a residual:

1. **A SIGN FLIP on agreement with the measured seam.** Both fixed ladders are
   **negatively** correlated with the measured hourly flow (−0.16 to −0.28) —
   they get the hour-to-hour seam backwards. The hourly form is **+0.26 to
   +0.28**.
2. **58 % of the correlation distance**, against the annual form's 3 %:
   (0.791−0.254)/(0.791+0.136) in 2023, and comparably in the other years.
   The slope closes **≈48 %** of its sign error and **remains negative** — a
   partial repair, stated as such.
3. **The annual form's own reported volume cost is undone.** miso-226 reported
   that the annual ladder moves the annual import total *further* from every
   measured comparator (5,302 vs 4,674 MW in 2023). The hourly form lands
   **4,649 / 3,673 / 3,199 against 4,674 / 3,678 / 3,198** — within **0.5 %** in
   all three years.

### Readout B — STATIC RE-MERIT at the keeper's own committed prices

Keeper composition exactly (`miso_seam_envelope_merit_cap = True`, the
waterfall bound `clip(cap − (k−1)·width, 0, width)`, read from the keeper's own
`run_config.json` — **not** carried across from miso-226's probe, which used the
uniform derate that keeper ran).

| year | arm | mean MW | corr vs hub price | slope d1−d10 | **frozen G-2 cheap-hour MW** |
|---|---|---:|---:|---:|---:|
| 2023 | annual | 5,407 | +0.517 | −1,430 | 4,672 |
| | **hourly** | 4,857 | **−0.282** | **+1,590** | **6,213 (+1,541)** |
| **2024** | annual | 4,005 | +0.313 | −1,368 | 3,563 |
| | **hourly** | 3,762 | **−0.115** | **+1,529** | **4,963 (+1,400)** |
| 2025 | annual | 3,333 | +0.646 | −1,633 | 2,463 |
| | **hourly** | 2,944 | **−0.364** | **+1,934** | **4,417 (+1,954)** |

**Harness check** — the keeper arms the annual ladder, so this reconstruction
should track its committed imports: `corr = +0.840 / +0.797 / +0.895`, levels
5,407 vs 5,514 / 4,005 vs 3,572 / 3,333 vs 2,767 MW.

**Readout B is the BIASED instrument and is reported as such**: its annual arm
reads corr **+0.517** where the solved arm measured **+0.725**, so the static
re-merit *understates* the model's positive correlation and its absolute levels
are 12–20 % off in 2024/2025. It predicts a direction and an order of magnitude,
not a value. **Readout A carries the load** — it uses no model output at all.

## 4. THE SCREEN (rule 29): **2024, ONE LP, bundle DELETED before merge**

### 4a. The screen year, and the rule that named it

**FOOTPRINT MEASURE DECLARED FIRST**: the mechanism's footprint is the
**band-hours on which the hourly and the promoted annual ladder disagree about
merit**, computed on the **MEASURED record** (readout A's basis). Model-free is
the primary basis because rule 29's footprint is a property of the *mechanism*
against its data, not of the incumbent solve; the keeper-price basis is reported
beside it.

| year | **model-free band-hours** | **model-free TWh moved** | keeper-price band-hours | keeper-price TWh |
|---|---:|---:|---:|---:|
| 2023 | 13,673 (19.51 %) | 12.4766 | 16,852 (24.05 %) | 12.0424 |
| **2024** | **13,946 (19.90 %)** | **12.7257** | 17,621 (25.14 %) | 12.3922 |
| 2025 | 13,931 (19.88 %) | 12.7120 | 18,782 (26.80 %) | **14.0998** |

**SCREEN YEAR = 2024**, largest on the primary basis on **both** sub-measures.

**Disclosed against this choice, at full magnitude:**
- The 2024/2025 margin on the primary basis is **0.1 %** (13,946 vs 13,931
  band-hours; 12.7257 vs 12.7120 TWh) — a near-tie, not a separation.
- The **keeper-price basis picks 2025**, and it is reported rather than dropped.
- The choice is nonetheless **not free of consequence, and 2024 is the year that
  can carry the gate**: in 2025 **every** gas and coal C1 class is SKIPPED on the
  preliminary EIA-923 vintage and C2 skips both families, so a 2025 screen could
  not discharge G-4 on two of the four load-bearing criteria — including C1, the
  cell miso-227 died on. That is a property of the DATA, not of the residual, and
  it is why a 0.1 % footprint margin is allowed to settle the tie rather than
  being overridden.
- **2024 is not miso-226's comparator year** (2023), so no comparator
  convenience is bought by the choice.

### 4b. G-DRIFT (rule 29(b)) — **ALL HUNKS INERT. Form 4 valid. NO control solve.**

`git diff 284722a04 HEAD -- src/market_sim scripts/run_calibration.py
scripts/run_calibration_full.py scripts/lib data/raw/_validation-source
data/raw/reference` = **13 files, +1,487 / −56**. Every hunk classified:

| changed area | class | reason |
|---|---|---|
| `config/paths.py::resolve_backcast_eia860_vintage`, `run_calibration.py`, `runner.py` vintage limb | **INERT** | gated on `eia860_vintage_tracks_solve_year`, new and default `False`, absent from the keeper recipe; precedence falls to the pre-existing branch unchanged |
| `data/transfer_interface_limits.py`, `run_calibration.py` admissibility limb | **INERT** | gated on `pjm_interface_feed_admissibility_gate`, default `False`, and PJM-scoped (rule 25) |
| `config/solve_surface.py`, `solve_surface_declared.py`, `results/cache.py`, `pipeline/persist.py`, `results/export.py` | **INERT — MEASURED, not asserted** | the capx D79 cache-key fingerprint. `surface_stamp("MISO", ScenarioConfig(iso="MISO", mode="backcast"))` reads `moved: {}`, `epochs: []` over 208 rows, so MISO's cache key is byte-identical to the pre-D79 key; the stamp itself is additive and outside `scenario_config` |
| `capacity_evolution/{evolve,retirements}.py` | **INERT** | forecast-only path; a `mode="backcast"` run never enters capacity evolution |
| `scripts/lib/forecast_provenance.py` | **INERT** | governance/provenance tooling, not the solve path |

**Conclusion: the keeper's committed bundle IS the control (form 4). No control
solve is spent.** Recorded here before the arm is solved.

### 4c. The command (single delta on the keeper recipe)

```
python3 scripts/replay_keeper.py results/calibration/miso230_ctdrag_seam_K \
  --years 2024 --out-dir results/calibration/miso231_hourlyseam_S \
  --set miso_seam_neighbour_hourly_ladder=true \
  --note "miso-231 screen: HOURLY neighbour-anchored PJM seam ladder"
```

### 4d. The five gates — STRUCTURAL, and STOP-ONLY

They ask whether the mechanism does what its own arithmetic says. **They may
kill the arm; they may never promote it**, none is gated on the target residual,
and none contributes to a determination.

| gate | bar | fails if |
|---|---|---|
| **G-1 responsiveness** (the target mechanism property) | solved `corr(imports, own hub price)` **falls by ≥ 0.30** from the keeper's **+0.750**, i.e. lands **≤ +0.45** | no material fall, or a fall so large it overshoots below **−0.60** (further from the measured −0.101 than the keeper is, on the other side ⇒ wiring error) |
| **G-2 volume fidelity** (the annual form's own reported cost) | solved annual PJM-seam import energy moves **TOWARD** the measured 2024 comparator, or stays within **±5 %** of the keeper's distance to it | moves further from the measured annual total than the keeper |
| **G-3 confinement** | the repricing touches **only** PJM reference-price band rows — SPP/South/Manitoba band `mc` byte-identical to the keeper's; slack and dump both **0.0000 TWh** | any non-PJM band repriced, or a feasibility artifact |
| **G-4 no collateral flip** | no **non-target** load-bearing criterion flips PASS→FAIL vs the keeper's committed 2024 scores (C1 cells, C2, C3a, C3b, C6). C3c excluded — ledgered caveat, rubric v3.3 | any such flip |
| **G-5 direction of the cheap-hour move** | in the frozen miso-225/226 G-2 hour set (real Indiana hub < $20; n = 2,111 in 2024) solved imports **rise** vs the keeper | imports fall in the hours the measured seam flows most |

**G-4 is the gate most likely to kill this arm, and it is named as such in
advance.** Readout B predicts the hourly form REDISTRIBUTES rather than adds
(−243 MW annual mean in 2024 while +1,400 MW in the cheap hours), so energy
leaves the expensive hours — and CT_PEAKER, whose 2023 C1 cell killed miso-227,
is the class that serves those hours. The keeper's 2024 CT_PEAKER gap is
−3.31 TWh against a ±8.00 band, so there is ~4.7 TWh of headroom; but the
displacement is real and G-4 is where it would surface.

**A screen that kills the arm is this session's result** and the remaining years
are never spent (rule 29).

## 5. If the screen clears

Full span **2023 2024 2025, ONE invocation, ONE bundle** (rule 16
`[R-ALLYEARS]`), scored with `scripts/calibration_verdict.py`. Promote on
CALIBRATED / CALIBRATED-WITH-CAVEATS; on a **load-bearing NOT-YET, report and
escalate to the owner rather than decertifying the ISO** (the miso-227 decision
rule, unchanged and re-adopted here).

**Pre-committed non-claim.** Readout A closes 58 % of the correlation distance
and **≈48 %** of the slope's sign error; the slope **stays negative** in all
three years. This arm does **not** claim to repair the seam's responsiveness —
it claims to move it, for the first time, by more than a rounding error. If it
promotes, that limitation is reported on its determination basis exactly as
miso-226's was, and **no C3c claim of any kind is made**.

The screen bundle `miso231_hourlyseam_S` is **DELETED before merge** (rule
29(c)); every number this session will ever cite from it lands in the FINDING.
Git history is the record.

## 6. Governance

Rule 1 `[R-STRUCT]`: structure first — the gates are structural and STOP-only,
and none reads the target residual. Rule 13 `[R-MEASURED]`: §1, the registered
`import_hub_pricing` flag's own position, with a forward analogue already in the
code. Rule 14 `[R-ACCURATE]`: the PJM-only boundary is stated, not proxied.
Rule 16: the full span is one invocation and one bundle. Rule 19 `[R-ONE-MECH]`:
displaces the annual overlay, never stacked; no hurdle added on top. Rule 21
`[R-DOF]`: **no free parameter added**, ledger stays 41/2. Rule 22: 2023–2025
only; MISO holds no `complete` marker. Rule 23: the derive is frozen against
residuals. Rule 24 `[R-REGISTRY]`: one `ScenarioConfig` field, recorded in
`run_config.json`. Rule 25 `[R-ISO-SCOPE]`: MISO-scoped field, MISO-stamped
table, no coefficient carried from another ISO. Rule 27 `[R-PUSH]`: edited
locally, pushed as on-disk bytes, blobs verified. Rule 28: duty **(c) FIRES** —
a new `ScenarioConfig` field, so its matrix row plus a cell line in **all six**
shards land in this PR; duty (b) on the `seam_neighbour_anchored_ladder` cell.
Rule 29: zero-LP phase 0 ran first (§3), the screen year is named on the
mechanism's own footprint under a measure declared before it was applied (§4a),
G-DRIFT is audited (§4b), and the bundle is deleted before merge.

---

# Addendum A — two gate corrections, made BEFORE any arm number was read

Written and pushed while the screen LP was still running, from the **keeper's
own committed 2024 artifacts only**. No output of the arm existed when these
were fixed, and the arm's bundle was not opened. Both are corrections to
comparators I got wrong in §4d, not renegotiations of a bar I had seen missed.

## A.1 G-1's comparator was a 2023 number quoted for a 2024 screen

§4d wrote the bar as *"falls by ≥ 0.30 from the keeper's **+0.750**, i.e. lands
≤ +0.45"*. **+0.750 is miso-226's 2023 measurement on the miso-220 predecessor**,
not the miso-230 keeper's 2024 value. Measured from the keeper's own committed
`hourly/` sidecars for the screen year:

| keeper 2024, from `miso230_ctdrag_seam_K` | value |
|---|---:|
| corr(imports, **own model** MISO-Indiana hub price) | **+0.4461** |
| corr(imports, **measured** MISO-Indiana hub price) | +0.3211 |
| decile slope d1−d10 on the own-model price | −4,362.3 MW |
| decile slope d1−d10 on measured-price deciles (miso-226's basis) | −3,321.6 MW |

So the absolute leg as written (**≤ +0.45**) is satisfied by the keeper itself
and would pass vacuously — the miso-200 vacuous-pass trap, in my own gate.

**The substantive leg is the relative one, and it is re-anchored to the correct
comparator at the SAME magnitude the PRECOMMIT wrote:**

> **G-1 (corrected).** Solved `corr(imports, own model hub price)` falls by
> **≥ 0.30** from the keeper's own 2024 value of **+0.4461**, i.e. lands
> **≤ +0.146**. FAILS on no material fall, or on an overshoot below **−0.60**
> (further from the measured −0.101 than the keeper is, on the other side ⇒
> wiring error). The measured-price basis is reported beside it, not gated.

## A.2 G-2 is UNSCORABLE against this control, and is withdrawn to REPORTED-ONLY

§4d's G-2 asks for *"solved annual **PJM-seam** import energy"* against a
measured comparator. **The keeper's committed bundle cannot answer it.** Under
rule 15's keeper-only retention the bundle is SLIM — `hourly/` sidecars,
`metrics.json`, `legitimacy_diagnostics.json`, `run_config.json` and
`meta.json`, with **no unit-level dispatch parquet** — so the control's imports
exist only as the aggregate `import` class and cannot be decomposed by seam.
Substituting the aggregate does not rescue the gate either: the model's `import`
class is **gross** reference-node imports (31.2944 TWh in 2024) while the
measured record's comparable total is a **net** across four seams
(+23.038 TWh: PJM +32.223, Manitoba +3.014, SPP −0.373, South −11.825). Those
are different quantities, and a gate that compares them measures the
gross/net convention, not the mechanism.

**G-2 is therefore withdrawn as a gate and the arm's annual import move is
recorded REPORTED-ONLY.** It is not silently dropped, and the question it asked
is not left unanswered: **phase-0 readout A already settles it on measured data
alone**, pre-registered in §3 and needing no control bundle — the hourly ladder
reproduces the measured annual seam volume within **0.5 %** in all three years
(4,649/3,673/3,199 MW against 4,674/3,678/3,198), which is the annual form's own
reported cost undone. What is lost is the *solved* confirmation of that, in this
screen year only.

**The screen therefore rests on four gates, not five**, and that is a weaker
screen than §4d advertised. Stated here rather than discovered in the FINDING.

## A.3 The other three gates, with their comparators fixed

| gate | comparator, from the keeper's own committed 2024 artifacts |
|---|---|
| **G-3 confinement** | SPP/South/Manitoba band `mc` byte-identical — verified STRUCTURALLY and ex ante by `tests/iso/miso/test_miso_seam_ladder.py::TestHourlyNeighbourOverlay::test_spp_and_south_keep_their_scalar_ladders`, so the solved leg is the feasibility half: slack and dump both **0.0000 TWh** (the keeper's 2024 slack is **0.0196 TWh**, pre-existing per the miso-230 assessment §8(f) — so the bar is "no INCREASE beyond the keeper's own") |
| **G-4 no collateral flip** | no non-target load-bearing criterion flips PASS→FAIL vs the keeper's committed 2024 scores. C3c excluded (ledgered caveat, rubric v3.3) |
| **G-5 cheap-hour direction** | frozen G-2 hour set, real Indiana hub < $20, **n = 2,111** in 2024; keeper imports **2,129.3 MW**. PASSES if solved imports RISE |

Everything above is computed by `scripts/probes/_miso231_screen_gates.py`,
committed and pushed with this addendum and **before the arm's bundle was read**.

## Addendum B — G-DRIFT extended over main's 59 later commits. **Still ALL INERT.**

PR #5253 merged this session's implementation + PRECOMMIT (`14ae4d76`,
`7ff10b64`) into `main`, which has since advanced to `6f074049`. Re-running
§4b's audit against the new tip, over the same paths:

```
git diff HEAD origin/main -- src/market_sim scripts/run_calibration.py \
    scripts/run_calibration_full.py scripts/lib data/raw/_validation-source \
    data/raw/reference
```

**Exactly one solve-path file moved**, `scripts/run_calibration.py` (+31 / −8,
ercot-251): a new helper `_renewable_bound_is_delivered_pinned` replacing an
`load_hsl_hourly(...) is None` test at two call sites.

| hunk | class | reason |
|---|---|---|
| `_renewable_bound_is_delivered_pinned` + its two call sites | **INERT** | both call sites are guarded `if getattr(config, "ercot_gtc_limits_measured"/"ercot_wtx_curtailment_driver", False) and iso == "ERCOT"` — ERCOT-only flags **and** an explicit ISO gate, so a MISO backcast never evaluates either branch (rule 25 `[R-ISO-SCOPE]`, §4b's "another ISO's branch" class) |

**Every other one of main's later commits touches nothing on the MISO backcast
solve path** (the diff above is otherwise empty). So the screen — solved on this
branch's HEAD — is byte-equivalent on the MISO path to `origin/main`, §4b's
form-4 conclusion stands unchanged, the keeper's committed bundle remains the
control, and **no control solve is spent**. Recorded before the arm's bundle was
read.
