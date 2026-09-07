# FINDING miso-241 — the lane's four-seam reconstruction was **MISPRICING THE SPP EXPORT LEG**, and the repair **SUPERSEDES on miso-235's own rule** (harness `corr` 0.9845/0.9745/0.9839 → **0.9917/0.9935/0.9935**, level error 49.4/41.6/55.3 → **8.9/1.8/5.8 MW**). On the repaired instrument the SPP seam is at **exactly zero flow in 42/41/48 %** of hours and **merit-set in 74/70/75 %**, while the measured deliverability envelope carries a **large, correctly-signed neighbour-state footprint** (|z| 12.8–31.3, 305–701 MW, 4 combos of 4). **THE CHARTER IS REFUSED: NO DOF-FREE FORM EXISTS**

**Zero LP. No arm, no screen, no bundle, no registration, no field, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was
solved, scored or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration: `PREREG-miso241-the-spp-quantity-side-charter-2026-09-07.md`, pushed at
`6fbc5e83` before any adjudicating quantity.** Two addenda, each pushed before the numbers it
governs: `ADDENDUM-miso241-the-q2-instrument-gate-2026-09-07.md` (`2ef2e667`, which also carried
the probe **before it was run**) and `ADDENDUM-miso241-the-census-is-too-narrow-2026-09-07.md`
(`44ac71ba`). Every decision rule applied below was fixed in one of those three documents; none was
written after seeing a number.

Probe: `scripts/probes/_miso241_spp_quantity_side_charter_phase0.py` →
`results/calibration/_miso241_spp_quantity_side_charter_phase0.json`.

**Queue item taken (rule 28(a)): item 1, THE SPP QUANTITY-SIDE CHARTER** — miso-237's named
successor and the handoff's recommended item.

**Basis (PREREG §0b).** The Indiana-hub **RT** series builds the finite-hour `ok` mask
byte-identically to miso-236/237/238/239/240. Every merit signal and regressor is the Indiana-hub
**DA**; the SPP seam's anchor is the measured **SPP NORTH hub DA**, the identical series the keeper
solved on. They correlate only +0.402/+0.424/+0.553 and are never interchanged. miso-232's measured
decile column (+1,303/+1,384/+948) is **not** restated as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST — four disclosures, and the first two are costly to this lane

### 0a. THE LANE'S OWN INSTRUMENT WAS WRONG, and it has been wrong since miso-235

`scripts/probes/_miso235_seam_variance_decomposition_phase0.py` line 237 prices the export leg of
**every** seam from `MISO_SEAM_LADDER_BY_YEAR[year][seam]["export"]` and clears it on
`p_bus < price_k` — a scalar against the bus-price **LEVEL**. The keeper does not do that on the
two seams its hourly overlay covers. `MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR[y]["PJM"]` and
`..._SPP_BY_YEAR[y]["SPP"]` each carry **both** an `import` and an `export` row of eight offsets
(PREREG §0 F2); `inject_miso_seam_ladder_prices` merges the **whole** per-seam dict and registers
the seam in `anchors`; `_inject_seam_ladder` then writes `mc[row,:] = anchor + prices[k]` to
**every** reference-price row of that seam, export rows included (F3). So on the keeper the SPP
export bands clear on `p_bus(t) < spp_hub(t) + δ_k^export` — a **spread** test — not on
`p_bus < 25.00`.

**This was established from source before the PREREG was written and it is disclosed first**
because the reconstruction it names is the instrument every one of miso-235's, -236's, -237's,
-238's, -239's and -240's model-side columns rides. The repair is a repair of **this lane's
reconstruction**. It changes no keeper, no input, no registry table, no derive and no solve.

### 0b. This session's OWN advance suspicion about PJM was CONFIRMED, not refuted — and it is smaller than feared

PREREG §2.4 said PJM's columns were *expected* unaffected because miso-239's `G-X0` reads its
export leg identically zero, and fixed that *"that expectation is TESTED, not assumed"* and that a
non-zero value would be *"published at full magnitude"*. Measured: the repaired PJM export leg is
**exactly 0.000000 MW in 2023 and 2024** (0 hours of 8,760) and **698.5 MW in 2025 — in 2 hours of
8,712**, mean 0.1 MW, σ 7.6 MW.

**Consequence, stated exactly.** miso-239's `G-X0` and the `MERIT = g(s) − ḡ` identity it licenses
are computed on the INCUMBENT instrument. On the keeper's own construction that identity is
**exact in 2023 and 2024** and **holds in 8,710 of 8,712 hours in 2025**. Every miso-238 and
miso-239 PJM column reproduces here to ≤ 0.004 of bar on the incumbent instrument (§1), and this
session **does not restate any of them as moved**; what it records is that the 2025 leg rests on
two hours the lane's instrument prices differently from the keeper.

### 0c. This session's OWN sharpest structural leg returned MIXED, and it closes nothing

Q-1 was written to decide whether the SPP seam's quantity is set by the ceiling or by the merit
test. `ceiling_active_share` reads **0.2572 / 0.2952 / 0.2474** against a `≥ 0.50` confirmation bar
and a `< 0.10` refutation bar, so on the pre-registered rule it is **MIXED and closes nothing**
(§4). Its reported columns are quoted below and are **not** converted into a verdict.

### 0d. This session's C7 census as COMMITTED was too narrow, and the widening cut AGAINST it

The probe pushed at `2ef2e667` implemented PREREG §5's repository-wide C7 question over six
directories. That is this session's error; it was disclosed and the widened search declared in a
pushed ADDENDUM (`44ac71ba`) **before** anything was opened, with the observation that a wider
search over a superset of paths and tokens is **monotone** — it can only ADD matches, so it can
only cut against the refusal this session was heading for. It added 60 top-level matches and 20
SPP/SWPP children (§6). **The refusal survives the widening**, on the classification rule fixed in
that addendum before any file was opened.

## 1. The provenance gate — **ALL EIGHT LEGS PASS**

| leg | what it reproduces, in the predecessor's own metric | bar | **measured** |
|---|---|---:|---:|
| **G-P1** | miso-235's `sigma_measured_mw` + `sigma_resid_measured_mw`, 4 seams × 3 yr × 2 | ≤ 0.5 MW | **0.000 MW** |
| **G-P2** | miso-236's **gated** `delta_r2_A_nohydro`, recomputed from scratch, 9 cells | ≤ 0.005 | **0.0000** |
| **G-P3** | miso-235's INCUMBENT four-seam harness `corr` and level error, 3 yr × 2 | ≤ 0.002 / 0.5 MW | **0.0000 / 0.00 MW** |
| **G-P4** | miso-238's PJM `sat_share`, on miso-238's own all-8-bands predicate | ≤ 0.002 | **0.0000** |
| **G-P5** | miso-239's PJM `γ_MERIT` (−870.18 / −930.93 / −791.43 MW/z), partial OLS | ≤ 0.5 MW/z | **0.004 MW/z** |
| **G-X0** | the PJM export leg identically zero on the INCUMBENT reconstruction | exactly 0 | **0.000000 MW** |
| **G-ID** | `imp ≡ min(env_i^eff, n_i·w)` and `exp ≡ min(env_e^eff, n_e·w)`, both variants, all four seams | ≤ 1e-6 MW, 0 violations | **0.0 MW, 0 violations** |
| **G-P6** | this session's Q-2 grid reproduces the committed envelope, 4 seams × 3 yr × 2 directions | ≤ 1e-6 MW | **0.0 MW** |

**G-ID is a falsifiable claim, not bookkeeping**: it holds only if each seam's in-merit set really
is the prefix `{0 … n−1}` on **both** legs and **both** export variants — i.e. only if every ladder
is monotone in its own clearing direction. **Zero violations in 24 seam-year-leg cells.**
**G-P6 is exact**: this session's Q-2 grid is the envelope's grid, not a lookalike, so Q-2's
estimator really is the envelope's own `p90`.

Five predecessors' published columns therefore reproduce on an independent code path — miso-235's
σ column (0.000 MW), miso-236's gated `ΔR²` (0.0000), miso-235's harness (0.0000 / 0.00 MW),
miso-238's saturation census (0.0000) and miso-239's `γ_MERIT` (0.004 MW/z) — and a **sixth,
unplanned**: miso-235 §5's incumbent system ratios recompute to **1.85 / 2.21 / 5.61×** against its
published 1.85 / 2.20 / 5.61 (§3b).

## 2. Q-0 — **REPAIRED SUPERSEDES**, on miso-235's own I-1/I-2 rule, and not marginally

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| harness `corr(recon, committed)` — INCUMBENT | 0.9845 | 0.9745 | 0.9839 |
| harness `corr` — **REPAIRED** | **0.9917** | **0.9935** | **0.9935** |
| mean abs level error — INCUMBENT | 49.4 MW | 41.6 MW | 55.3 MW |
| mean abs level error — **REPAIRED** | **8.9 MW** | **1.8 MW** | **5.8 MW** |

**(I-1) corr rises: TRUE in all three years. (I-2) level error not worse: TRUE in all three
years.** The pre-registered condition — miso-235's own rule, the one by which it superseded
miso-234's three-seam instrument — is met, so **the repaired reconstruction supersedes as this
lane's attribution instrument** and §4 reads it.

The repair is not marginal and it is not diffuse: the level error falls **5.5× / 23× / 9.5×**, and
the residual disagreement is confined to exactly the seams the code reading predicted.

### 2a. WHERE the repair acts — SPP, and essentially nowhere else

| seam | export-leg hours ≠ 0, INCUMBENT → **REPAIRED** | export/import disagreement share | net σ INCUMBENT → **REPAIRED** | measured σ |
|---|---|---:|---|---:|
| **SPP** 2023 | 402 → **1,244** | **0.1785** | 279.5 → **348.4** | 577.3 |
| **SPP** 2024 | 949 → **1,416** | **0.2465** | 276.6 → **392.2** | 687.3 |
| **SPP** 2025 | 389 → **1,595** | **0.2146** | 250.3 → **327.0** | 615.4 |
| PJM 2023 / 2024 | 0 → **0** | 0.0000 | unchanged | — |
| PJM 2025 | 0 → **2** | 0.0002 | 1,633.9 → 1,634.1 | 1,647.0 |
| South, Manitoba, all years | unchanged | 0.0000 | unchanged | — |

South and Manitoba are byte-identical because the hourly overlay does not cover them — which is
the code reading (F4) confirmed by measurement rather than asserted.

### 2b. What moves in the PREDECESSORS' published columns — named in advance (PREREG §2.3), and reported at full magnitude

**miso-235 §4's SPP row. The VERDICT LETTER STANDS; the MAGNITUDES MOVE.**

| SPP | 2023 | 2024 | 2025 |
|---|---|---|---|
| `sigma_model_mw` | 279.5 → **348.4** | 276.6 → **392.2** | 250.3 → **327.0** |
| `beta_model` | 7.38 → **11.17** | 5.18 → **10.65** | 4.88 → **7.21** |
| `beta_ratio` | 6.91 → **10.45** | −9.02 → **−18.54** | 4.61 → **6.80** |
| `sigma_resid_model_mw` | 226.9 → **245.7** | 247.1 → **297.7** | 205.8 → **250.5** |
| `resid_ratio` (bar ≤ 0.5) | 0.39 → **0.43** | 0.36 → **0.43** | 0.33 → **0.41** |
| miso-235 §4 flags | `PRICE_RESPONSE_OVERSHOOT` + `MISSING_NON_PRICE_VARIATION` | same | same |

Both of miso-235's ex-ante bars still fire in all three years (β ratio ≥ 1.5; residual-σ ratio
≤ 0.5), so **miso-235 §4's SPP headline `MISSING_NON_PRICE_VARIATION` is UNCHANGED** — and its
companion `PRICE_RESPONSE_OVERSHOOT` is if anything **larger** than published: the model's SPP seam
is **10.5 / 18.5 / 6.8×** as price-responsive as the measured one, not 6.9 / 9.0 / 4.6×. The seam's
σ deficit narrows but does not close: 48 / 40 / 41 % of measured becomes **60 / 57 / 53 %**.
PJM's, South's and Manitoba's §4 rows are unchanged to the digit (PJM 2025 moves in the fourth
significant figure: σ 1,633.9 → 1,634.1, β 28.87 → 28.88).

**miso-235 §5's contribution table, and it corroborates Q-0 on a second, independent statistic.**

| year | INCUMBENT total | **REPAIRED total** | committed solve | measured | ratio inc / **rep** / committed |
|---|---:|---:|---:|---:|---|
| 2023 | −0.1015 | **−0.1083** | −0.1095 | −0.0549 | 1.85 / **1.97** / 1.99 |
| 2024 | −0.0811 | **−0.1120** | −0.1145 | −0.0367 | 2.21 / **3.05** / 3.12 |
| 2025 | −0.1139 | **−0.1164** | −0.1128 | −0.0203 | 5.61 / **5.73** / 5.56 |

The repaired reconstruction lands on the **committed solve's own** contribution to
`corr(imports, P_RT)` to **0.0012 / 0.0025 / 0.0036** against the incumbent's
0.0080 / **0.0334** / 0.0011 — a 6.7× and 13× improvement in 2023 and 2024 and a 3× degradation in
2025, on a statistic no gate reads. **2024 is where the incumbent was worst and it is the year
miso-235, -236, -237, -238 and -239 all flagged as their loosest** (`corr(recon, committed)` 0.9745,
the lowest of the three): that year's reconstruction was under-stating the system contribution by
**29 %**, and the repair removes essentially all of it.

**Reported against interest:** the repaired SPP contribution **flips sign in 2024**,
+0.0138 → **−0.0163**, against a measured **−0.0372** — i.e. the keeper's actual SPP seam has the
*right* sign in 2024 and the lane's instrument had it wrong. In 2023 it stays wrong-signed
(+0.0124 against −0.0291) and in 2025 right-signed and 1.6× too large (+0.0301 against +0.0188).
**The lane's cancellation reading is untouched in substance** — PJM −0.3369 / −0.3071 / −0.3016
against a measured −0.0778 / −0.0573 / −0.0326, South wrong-signed, Manitoba ~2× too positive — and
the handoff's instruction stands: target the **committed** 1.99 / 3.12 / 5.56×, never a per-seam
reconstruction ratio. **Declared un-targetable before it was computed** (ADDENDUM §C).

## 3. Q-1 — **MIXED**, and it closes nothing. But its reported columns are the sharpest structural fact in the session

`ceiling_active_share` = the share of `ok` hours in which at least one of the SPP seam's two legs is
CEILING-SET, i.e. in which `env^eff ≤ n·w` with `n ≥ 1` so that a marginal change in the ceiling
would change the leg's flow. Verdict bars: `≥ 0.50` CEILING-SET, `< 0.10` MERIT-SET.

| SPP, repaired instrument | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **`ceiling_active_share`** | **0.2572** | **0.2952** | **0.2474** |
| `merit_active_share` | 0.7428 | 0.7048 | 0.7526 |

**VERDICT: MIXED.** Neither bar is met in all three years, so on the pre-registered rule **no
property is named and nothing is closed or licensed.** The other seams are reported, never gated:
PJM 0.3796 / 0.3232 / 0.2563, South 0.0258 / 0.0340 / 0.0956, Manitoba 0.4279 / 0.4152 / 0.2492.

**The reported columns, and they are not a verdict** (PREREG §3):

| SPP | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| import leg: hours with **zero** bands in merit | 0.5718 | 0.5788 | 0.7052 |
| import leg: mean bands in merit (of 8) | 0.50 | 0.49 | 0.33 |
| export leg: hours with zero bands in merit | 0.8457 | 0.8279 | 0.7758 |
| **the seam at EXACTLY zero flow, both legs out of merit** | **0.4175** | **0.4066** | **0.4810** |
| `env_i` mean / σ (MW) | 682.4 / 340.8 | 578.5 / 286.0 | 734.8 / 236.5 |
| `env_e` mean / σ (MW) | 480.3 / 362.2 | 720.8 / 590.6 | 542.1 / 414.8 |
| `env_i` = 0 share | 0.0106 | 0.0035 | 0.0034 |

**What that says, without a bar attached to it:** the model's SPP seam spends **42 / 41 / 48 % of
its hours at exactly zero** and its ladder carries **0.33–0.50 of eight** import bands in the mean
hour. It is not a seam pinned by a ceiling; it is a seam that mostly **does not clear at all**. The
ceiling reaches only about a quarter of its hours, and that is a **bound on what any ceiling-side
mechanism could do** — reported here because a charter must know it, and gated nowhere.

## 4. Q-2 — **FOOTPRINT PRESENT**, on all four pre-registered combinations, with every sign correct

The one construction whose estimator is already in the codebase: the envelope's own
`np.percentile(·, 90)` on measured net flow, evaluated on a `(month × hod)` partition **refined by
neighbour state** (SWPP+SPA net load, and SWPP+SPA wind+solar), tercile split, sample-weighted mean
`p90(T3) − p90(T1)`, against a 200-permutation **within-bucket** null (seed 20260907) and a
materiality floor of `0.10 × mean(env)` taken from the model's own object.

| SPP | 2023 | 2024 | 2025 | material bar |
|---|---:|---:|---:|---:|
| **neighbour net load → IMPORT ceiling** | **−556.1** (z −31.3) | **−446.3** (z −24.3) | **−410.7** (z −17.2) | 68.2 / 57.9 / 73.5 |
| **neighbour net load → EXPORT ceiling** | **+517.7** (z +25.7) | **+701.2** (z +21.5) | **+423.5** (z +17.4) | 48.0 / 72.1 / 54.2 |
| **neighbour VRE → IMPORT ceiling** | **+519.1** (z +28.7) | **+341.5** (z +18.6) | **+392.4** (z +17.7) | 68.2 / 57.9 / 73.5 |
| **neighbour VRE → EXPORT ceiling** | **−417.8** (z −21.3) | **−489.3** (z −17.2) | **−304.6** (z −12.8) | 48.0 / 72.1 / 54.2 |

**VERDICT: FOOTPRINT PRESENT** — `|z| ≥ 3` in every cell (measured 12.8–31.3), the materiality bar
cleared by **5.6–9.7×**, and the sign identical across all three years, on **all four** combinations
rather than the one the rule required.

**The four signs were predicted by physics before the numbers and all four are right.** When the
neighbour's net load is high it has less to export, so MISO's deliverable import falls and its
deliverable export rises; when the neighbour's VRE is high the reverse. The measurement recovers
exactly that pattern, independently in each of four cells and each of three years, at magnitudes of
**305–701 MW** against envelope means of 480–735 MW. **This is not a marginal signal.**

**Declared UN-TARGETABLE before it was computed** (PREREG §4, §5.2.2): no successor may size,
scale, tune or select any mechanism to make a modelled quantity land on any number in this table.
miso-236's 328.6 / 341.7 / 207.5 MW sizing likewise stays un-targetable and is not re-quoted here
as a target.

**Reported, never gated:** the same measurement with **MISO's own** net load as the conditioning
variable, and the same four combinations on PJM, South and Manitoba, are in the JSON. And a
confound this session names rather than leaves for a reader to find: the envelope is a `p90` of
**realized net flow** used as a capability proxy, so conditioning it on a *contemporaneous* market
variable necessarily imports some of the hour's own market outcome into the cap. That does not
touch the admissibility of the **driver** (miso-236 settled that); it is a question about the
**estimator**, and §5 treats it as one.

## 5. Q-3 — THE CHARTER. **REFUSED: NO DOF-FREE FORM EXISTS**

The candidate set was fixed in PREREG §5 before any number, and the DOF rule with it: a candidate
is DOF-FREE iff every constant it introduces is either produced by an estimator already in the
codebase reading a committed measured source, or fixed by an identity or a published external
definition — **and none is selected by, or selectable against, any residual, gate or criterion.**

| id | candidate | DOF-free? | admissible? | why |
|---|---|---|---|---|
| **C1** | state-conditioned deliverability envelope (the same p90 on a `(month × hod × state bin)` partition) | **NO** | no | §5a |
| **C2** | neighbour-surplus cap | **NO** (or inert) | no | §5b |
| **C3** | neighbour-state derate window | **NO** | no | §5c |
| **C4** | explicit neighbour supply stack (SWPP+SPA as a modelled zone) | no | **no — rule 25** | §5d |
| **C5** | neighbour state inside the merit test | **NO** | no | §5e |
| **C6** | calendar-free re-conditioned envelope | **NO** | no | §5f |
| **C7** | measured tie / neighbour-fleet outage windows | *n/a* | **no series exists** | §6 |

### 5a. C1 — the ONLY candidate with a measured footprint, and it fails on THREE independent grounds

**(i) It is not DOF-free, and this is intrinsic rather than a matter of taste.** The existing
envelope's partition costs nothing because the **calendar supplies it**: `12 months × 24 hours` is
an identity, not a choice. A neighbour-state partition has no calendar to inherit — its granularity
(terciles? quartiles? a median split? a minimum-sample rule and a fallback for short buckets?) is a
new constant with **no measured source and no identity**, and it is **selectable against a
residual**: one could sweep the bin count until a modelled σ landed where one wanted. That is
precisely the selection PREREG §5's rule, rule 1 `[R-STRUCT]` and rule 21 `[R-DOF]` exist to refuse.
Every continuous alternative is worse, not better: a conditional-quantile regression introduces
fitted coefficients, and a k-nearest-neighbour conditional p90 introduces a bandwidth. **There is no
version of C1 that adds zero free parameters.** The handoff set the bar explicitly — *"A DOF-free
construction is the bar; miso-233 promoted on zero fitted parameters"* — and C1 does not meet it.

**(ii) It is an envelope change, which a standing freeze refuses.** Rule 14 `[R-ACCURATE]` protects
the measured `(month × hod)` envelope, and this lane's binding instruction is explicit: *"NO
re-derive, NO damping factor, NO change of K, NO re-spacing of δ_k, NO envelope or interface-limit
change. It binds."* miso-238 §5.2, miso-239 §5.2 and miso-240 §5.2 each fixed that in advance for
every outcome, and PREREG §5.2 fixed it again here before Q-2 was computed. **This ground is
independent of (i) and would refuse C1 even if it were DOF-free.**

**(iii) Rule 13 `[R-MEASURED]`, on the direction of travel.** The unconditional envelope survives
rule 13 as a *capability* proxy precisely because the calendar keying **smooths away** the hour's
own market conditions. Conditioning the same `p90` on a contemporaneous neighbour-state variable
moves it back toward the realized flow — the thing rule 13 prohibits absolutely. This is stated as
a **named admissibility risk a charter would have to answer**, not as a verdict: the driver is
admissible (miso-236 §2c settled it), the estimator is what is in question.

**(iv) And Q-1 bounds what it could reach anyway.** Even armed, a ceiling-side mechanism changes the
SPP seam's flow only in the hours the ceiling is active — **25.7 / 29.5 / 24.7 %** of them (§3).
Reported, not a reason: a small reach is not a ground for refusal under any rule, and it is not used
as one.

### 5b. C2 — the neighbour-surplus cap: its only DOF-free form is INERT *and* a rule-14 regression

A cap of `(neighbour capacity − neighbour net load) × share` carries a free `share`. Removing the
share leaves `cap = min(interface_limit, neighbour surplus)`, which introduces no constant — and is
**structurally inert**, because SWPP+SPA's surplus is an order of magnitude above the seam's
4,000 MW interface limit in essentially every hour, so the `min` is always the limit. Worse, taking
that branch means **replacing a measured deliverability input with a capacity-headroom estimate** —
the exact move rule 14 `[R-ACCURATE]` forbids in its own words ("never revert to an estimate").

### 5c. C3 — the derate window: no published trigger exists, so both its constants are free

A window needs a threshold and a depth. Neither is produced by any codebase estimator or fixed by an
identity, and §6's census finds **no published SPP reliability-event series** (EEA, conservative
operations, or equivalent) in this repository from which a threshold could be read. Rule 17
`[R-FLOOR-WINDOW]` would in any case demand a driver, the hours it may bind and why, and a forecast
story — and a threshold chosen by the modeller supplies none of them.

### 5d. C4 — the explicit neighbour supply stack: refused by **rule 25 `[R-ISO-SCOPE]`**, not by scope

SPP is one of the seven registered ISOs, so the codebase can build its fleet — which makes this the
one candidate that is *structurally complete*: the neighbour's state would enter through the
neighbour's own energy balance, orthogonally to the hub-pair spread by construction. It is refused
on a rule, not on effort. SPP's offer representation carries SPP's own registered band multipliers,
identified against **SPP's** residual; importing them into MISO's LP is exactly what rule 25 forbids
("Tuned curves never cross ISO boundaries"). Substituting neutral 1.0 bands instead deliberately
mis-specifies the neighbour, and deriving a new SPP offer representation *for MISO's lane* mints
free parameters — the DOF failure again. It would also **replace** the entire priced-band seam
representation, which is an architecture change no lane charter reaches; if an owner ever wanted it,
it is an owner question and not this one.

### 5e. C5 — neighbour state in the merit test: refused three times over

miso-237 measured this channel as **quantity-side** on a pre-registered rule (78–82 % of the
neighbour increment survives a price representation strictly richer than anything the merit test can
express; 95–101 % under miso-236's conditioning), so the price route is the one the evidence
excludes. On top of that, `δ_k` is derived, frozen and pinned to its derive by test (rule 23), and a
state-dependent price adder is a fitted adder — rule 13's named inadmissible form and rule 1's
forbidden channel.

### 5f. C6 — dropping the calendar for a state partition: C1's DOF failure plus a discarded measurement

Same partition DOF as C1, and it additionally **throws away** a measured structure (the seasonal and
diurnal deliverability pattern the envelope carries) — a rule-14 regression on top of a rule-21
failure.

### THE VERDICT, on the rule fixed in PREREG §5

**REFUSED — NO DOF-FREE FORM.** Not one candidate in the pre-registered set is DOF-free, so the
charter cannot be written. Under PREREG §5 the rule-17 `[R-FLOOR-WINDOW]` leg is therefore recorded
as **NOT OWED** — no candidate stands, so there is no mechanism to owe a driver, a window or a
forecast story for — exactly as miso-240 §6(c) recorded it. **The rule-19 `[R-ONE-MECH]` enumeration
is written anyway** (§7), as the PREREG required.

**This is the outcome the handoff blessed in advance:** *"IF NO DOF-FREE FORM EXISTS, SAY SO AND
STOP — miso-240 just demonstrated that is a complete session result."* **Said, and stopped.**

## 6. C7 — the census, WIDENED, and it answers by data absence

`ADDENDUM-miso241-the-census-is-too-narrow-2026-09-07.md` §1 widened the search to the whole of
`data/raw` on a 16-token list plus **every** `spp`/`swpp` child in full, and §2 fixed the
DRIVER-vs-OUTCOME classification before anything was opened. It surfaced 60 top-level matches and
20 SPP/SWPP children. **No measured MISO–SPP tie outage or derate series exists in this repository,
and no SPP reliability-event log exists.** What does exist, classified on the addendum's rule:

| series | what it is | DRIVER / OUTCOME | DOF-free mapping to a MISO–SPP seam object? |
|---|---|---|---|
| `campd-unit-outages-SPP.csv` (+ `-partial-`, `-short-`, `-layup-`) | SPP **fleet** unit outage windows, the construction `campd_outage_windows` **K** already performs for MISO's own fleet | **DRIVER** (rule 13 names outage windows explicitly) | **No** — turning a neighbour *fleet* outage into a *tie* cap needs a coefficient; the coefficient-free route is C2, refused |
| `spp-binding-constraints/Flowgates.csv` | published flowgate registry: seasonal Normal/Emergency ratings, IROL, TRM, From/To area | **DRIVER** | **Adjudicated elsewhere** — "published interface limits as the seam cap" is `measured_interface_limits` **R** at MISO (miso-174) and `miso_rdt_measured_limit` **R**; rule 28(a), not re-tested here |
| `spp-binding-constraints/RTBM-BC-MONTHLY-*.zip` | realized SPP binding-constraint records | **OUTCOME** | inadmissible as an input, on miso-236 PREREG §2c's own rule |
| `transfer-constraint-binding/MISO` | MISO's realized RDT/PBC binding record | **OUTCOME**, and MISO-internal, not the SPP tie | inadmissible; and the RDT object is `miso_rdt_measured_limit` **R** |
| `miso-generation-outages` | MISO's **own** outage record | driver, but not the neighbour | not this object |
| `spp-hsl` (wind curtailment / uncurtailed HSL) | realized SPP curtailment | **OUTCOME** | inadmissible as an input |
| `reference/spp_seam_tieflow_crosscheck.csv` | a validation cross-check of tie-flow against EIA-930 | neither — a validation artifact | not an input |

**And the distinction the addendum fixed in advance, honoured here:** even the one DRIVER-class
series on the SPP side (`campd-unit-outages-SPP`) is **a different driver from the object miso-236
and miso-237 named**, which is SWPP+SPA **net load and VRE**. It would not carry that signal, and
it has no DOF-free mapping in any case. **Nothing in the census rescues the charter, and the
widening that could only have helped it did not.**

## 7. Rule 19 `[R-ONE-MECH]` — the enumeration, written whatever the verdict

What already sets the MISO–SPP seam on the keeper: the armed **hourly SPP neighbour anchor**
(`miso_seam_neighbour_hourly_spp`, band `k` at `spp_hub(t) + δ_k`, **import and export alike** —
which is §0a's whole point); the **frozen Q-Q `δ_k` ladders**
(`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`, derived, frozen, pinned to their derive by test);
the **incumbent MISO-hub Q-Q ladder** it displaces (`MISO_SEAM_LADDER_BY_YEAR["SPP"]`, an
alternative, never stacked); the **measured `(month × hod)` deliverability envelope** in both
directions under the merit-order waterfall (`miso_seam_flow_limit`, `miso_seam_export_limit`,
`miso_seam_envelope_merit_cap`, `miso_seam_envelope_hour_ending_key`); the seam's **4,000 MW**
interface limit and its eight **500 MW** bands; the `MISO_external` border-link TTCs; the
**8,700 MW** `MISO_simultaneous_import` SIL; and the published **CIL/CEL** deliverability groups.
**Nothing is added, so nothing replaces and nothing reconciles.**

## 8. What is handed forward

1. **THE SPP QUANTITY-SIDE CHARTER IS REFUSED — NO DOF-FREE FORM** (§5), on this session's own
   pre-registered rule. A successor should not re-open it without a **new admissible measured
   series** or an **owner ruling**; re-running Q-1 or Q-2 will reproduce these numbers.
2. **THE LANE'S RECONSTRUCTION IS REPAIRED AND THE REPAIRED FORM SUPERSEDES** (§2). Every successor
   using the four-seam instrument should take the export leg from
   `_miso241_spp_quantity_side_charter_phase0.py::build_recons` (or reproduce it), **not** from
   miso-235 line 237. What moves: miso-235 §4's SPP magnitudes and §5's totals (§2b), reported here
   at full magnitude; what does **not** move: every verdict letter, every gated verdict of
   miso-236 and miso-237 (both measured-side, PREREG §2.2), and every PJM column in 2023–2024.
3. **THE OWNER QUESTION, STATED PRECISELY AND NOT ASKED HERE.** If an owner ever wished to weigh
   lifting the envelope freeze, the object with the measured footprint is **C1**, its cost is
   **exactly one new free parameter** (the state-partition granularity, identification "declared",
   ledgered under rule 21 and taking the DOF ledger to 42/2), its reach is bounded at **~25 % of the
   SPP seam's hours** (§3), and its rule-13 estimator risk is §5a(iii). This session **does not ask
   for that ruling, does not recommend it, and charters nothing.**
4. **A STRUCTURAL FACT NEITHER MEASURED NOR EXPLAINED BEFORE, AND NOT CHARTERED HERE:** the model's
   SPP seam sits at **exactly zero flow in 42 / 41 / 48 %** of hours and carries **0.33–0.50 of
   eight** import bands in the mean hour (§3), against a measured seam whose σ is 577 / 687 /
   615 MW. It is reported, it is not a verdict, and it names no mechanism — but it is the reason
   both state blocks under-transmit on this seam (miso-237 §3b, 0.07–0.28×), and a successor should
   understand it before proposing anything on the SPP tie.
5. **UNCHANGED AND NOT RE-TESTED:** queue item 1 (the external-bus price) stays **CLOSED**; the
   per-seam external-node split stays **REFUSED at zero LP**; the saturation hypothesis stays
   **REFUTED**; miso-239's Q-A stays **MIXED** and Q-C **SURVIVES**; miso-240's Q-B stays
   **UNRESOLVED**; the `(month × hod)` template hypothesis stays **REMOVED**; the PJM
   import/export asymmetry stays **CLOSED FOR PJM** on the incumbent instrument (§0b records the
   two 2025 hours); South's neighbour-state route stays **CLOSED**; `miso_manitoba_seam` stays
   **CLOSED as already-armed**; `internal_congestion_split` **G**;
   `vre_reference_rate_curtailment_grossup` **K**; `measured_interface_limits` **R**;
   `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**;
   `miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
   `miso_south_gas_delivered_cost_basis` **R**.
6. **Manitoba determinism** (miso-236 §5.3), **the export-leg asymmetry on SPP/South/Manitoba**
   (handoff item 2 — note that §2a re-bases its SPP leg: the repaired export leg is live in
   1,244 / 1,416 / 1,595 hours, not 402 / 949 / 389), **CC_REGULAR 2024→2025 shape emergence** and
   **C3c**, the designated frontier, are untouched and stay where they are filed. C3c still needs a
   new admissible measured identification **and** an owner ruling; no LP is authorized there and
   none was sought.
7. **NOTHING LICENSES A RE-DERIVE OR A DAMPING FACTOR** on the PJM or SPP `δ_k` ladders (rule 23),
   or any change to the measured `(month × hod)` envelope, its percentile, or any interface limit
   (rule 14). PREREG §5.2 fixed this in advance for **every** outcome and it binds. Every number in
   this document is **UN-TARGETABLE**.

## 9. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number is a solve result. **There is no keeper candidate in this
   session** and nothing to promote.
2. **The Q-0 repair fixes an INSTRUMENT, not the model.** The keeper's LP already priced the SPP
   export leg the repaired way; what was wrong was the lane's reconstruction *of* it. No solve
   output changes, no criterion moves, and no determination is affected.
3. **miso-235 §4's SPP verdict letter is NOT withdrawn** (§2b) — both its flags still fire. What is
   published as moved is its magnitudes and §5's totals, and both are shown side by side.
4. **miso-238's and miso-239's PJM columns are NOT restated as moved.** They reproduce exactly on
   the incumbent instrument (§1), and §0b records precisely the two 2025 hours on which the keeper's
   own construction differs.
5. **Q-1 is MIXED and attaches nothing.** Its reported columns are quoted and are not converted into
   a verdict, however suggestive the 42–48 % zero-flow share is.
6. **Q-2 measures a candidate; it does not build one.** No input was created, no envelope was
   changed, and a measured footprint is not a licence (PREREG §5.2.1).
7. **The model side is a RECONSTRUCTION** throughout — now at harness `corr` 0.9917 / 0.9935 /
   0.9935, closer than the incumbent's 0.9845 / 0.9745 / 0.9839, but not 1.
8. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
9. **MISO has no failing gate**, and nothing here proposes trading a passing one. There is no rubric
   failure anywhere in the program and this session did not invent one.

## 10. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; the charter was refused on **structural
and DOF** grounds, never on a residual, and every number was declared un-targetable before it was
computed. Rule 12 `[R-PARALLEL]`: no LP; nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement
only; no input changed and no measured outcome entered any solve; miso-236 PREREG §2c's
inadmissible-forms list bound throughout and §6 applies it to seven candidate series. Rule 14
`[R-ACCURATE]`: no input changed; the measured envelope, its percentile and every interface limit
are untouched. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered or pruned; MISO keeps
exactly one registered run and the keeper's `hourly/` sidecars stay committed. Rule 17
`[R-FLOOR-WINDOW]`: no floor added — §5 records why none is owed. Rule 19 `[R-ONE-MECH]`: no
mechanism added; §7 writes the enumeration anyway. Rule 21 `[R-DOF]`: **41/2, unchanged**; every
instrument here carries zero free parameters beyond Q-2's two declared design constants (200
permutations, seed 20260907; a 12-sample bucket floor), neither of which can move a verdict's
direction. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no
out-of-training year was solved, scored or registered. Rule 23 `[R-FROZEN-DERIVE]`: no derive
re-run; §8.7 restates the freeze. Rule 24 `[R-REGISTRY]`: no field created. Rule 25
`[R-ISO-SCOPE]`: MISO's shard, section and lane only — SPP's own shard, keeper and lane are
untouched, and §5d refuses C4 *on* rule 25 rather than merely citing it. Rule 26 `[R-DELETE]`: the
defective export-leg predicate is **replaced** in this session's instrument, not left behind a flag.
Rule 27 `[R-PUSH]`: on-disk edits only; every pushed blob ≥ 300 lines verified against local after
push. Rule 28(a): queue item 1 taken and closed; every standing adjudication touched is corroborated
or untouched, never re-tested. Rule 28(b): no verdict moves; evidence appended in MISO's shard
in-session. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0, and it **repaired the lane's
attribution instrument, closed a queue item and refused every candidate it could name before a
single LP minute was spent**, which is the outcome the clause exists to produce.
