# FINDING miso-239 — the pre-registered property ladder reads **MIXED**, and the one thing every year agrees on is that the carrier is not a *property of `g`* at all

Pre-registration: `PREREG-miso239-which-property-of-g-2026-09-07.md` (pushed `c0e971ee`, before
any adjudicating quantity). Every decision rule applied below is fixed there; nothing here
selected anything. **Zero LP**, as declared. Keeper unchanged at
`2026-09-07-miso-233-spp-hourly` (bundle `results/calibration/miso233_sppseam_K`), DETERMINATION
**CALIBRATED**, C3c the single ledgered caveat, DOF **41/2**. MISO carries exactly ONE registered
run (rule 15). No run produced, none registered, none pruned; no cell verdict moves.

---

## 0 — STATED FIRST, AGAINST INTEREST

### 0a. The gated question did NOT resolve. Q-A reads **MIXED**.

PREREG §3a's ladder requires a share `≥ 0.50` in **all three years**. It gets neither:
`σ_LIN` = 0.668 / **0.284** / 0.731 and `σ_CURVE + σ_STEP` = 0.332 / **0.716** / 0.269 — each
clears the bar in the two years the other fails. **The pre-registered rule therefore names no
property, and under PREREG §3a a MIXED verdict "closes and licenses nothing."** Queue item 1 is
**NOT closed** and a successor may take it again. Everything in §4–§5 below is reported inside
that verdict, never around it.

### 0b. This session's own §2b mapping was INCOMPLETE, and the numbers show it

PREREG §2b assigned `LINEAR → candidate (d)` and `CURVE → candidates (a)+(c)`. **That mapping
over-claimed and it is withdrawn as an interpretation** (the arithmetic is untouched; only the
label is wrong). `CURVE` is *also* a function of the model's own merit spread `s`, so the
regressor mismatch that (d) names acts on `LINEAR` **and** `CURVE` alike; `σ_LIN` measures how
much of `g`'s response happens to be *linear in `s`*, not how much of it is carried by the
`s`-vs-`p1` mismatch. The split between `LINEAR` and `CURVE` therefore tracks **where on the
ladder the spread is sitting that year** — `β` = 106.75 / **50.01** / 65.18 MW per $, with 2024
the flat year — and not which property of `g` acts. That is the mechanical reason Q-A reads
MIXED, and it is a defect in this session's instrument, disclosed before its numbers are
interpreted.

### 0c. miso-238's record was INCOMPLETE on `main`, and this session repaired it

Read at `origin/main` = `8377e878`: miso-238's **FINDING and its phase-0 JSON never landed**, and
the committed miso-238 probe still carried the *marginal covariance* estimator that its own
committed `ADDENDUM` §2 had replaced with miso-237's **partial** OLS slope — i.e. the instrument
on `main` was the one that had failed its own G-P2 at **457.126 MW/z** against a 0.5 bar. **No
miso-238 number quoted in this session's handoff was reproducible from a committed artifact.**

Declared in PREREG §0b before it was run, this session applied **exactly and only** that
addendum's declared repair (partial-OLS `gamma`, plus its declared `gamma_marginal_mw_per_z`
disclosure column) and regenerated `_miso238_pjm_seam_channel_attribution_phase0.json`. **No
miso-238 bar, floor, gating seam, channel definition or decision rule was touched.** The repair
is verified, not asserted: G-P2 falls from 457.126 to **0.005 MW/z**, and **every one of the nine
miso-238 quantities the handoff quotes reproduces EXACTLY, in all three years** (G-P4 worst case
0.0 of bar — §1). miso-238's Q-A verdict re-reads **MERIT-DRIVEN** and its Q-B **MERIT-DRIVEN**,
on the un-moved bars. **This session claims no miso-238 verdict as its own**; it republishes
miso-238's column only as its own provenance leg.

---

## 1 — The provenance gate: all six legs PASS

PREREG §1, fixed ex ante. miso-238's gate fired on its own instrument; this one did not.

| leg | what it reproduces | bar | measured | verdict |
|---|---|---:|---:|---|
| **G-P1** | miso-235's σ column, 4 seams × 3 yr (24 values) | ≤ 0.5 MW | **0.048 MW** | PASS |
| **G-P2** | miso-237's own-net-load coefficients (24 values), **partial** OLS | ≤ 0.5 MW/z | **0.005 MW/z** | PASS |
| **G-P3** | miso-237 ADDENDUM §A's alignment column (48 values) | ≤ 0.001 | **0.00005** | PASS |
| **G-P4** | miso-238's published PJM column, 9 quantities × 3 yr, recomputed from scratch | ≤ 1.0 × bar | **0.0 × bar (exact)** | PASS |
| **G-X0** | the PJM export leg is identically zero | exactly 0 | **0.000000 MW** | PASS |
| **G-ID** | this session's decomposition identity `LINEAR+CURVE+STEP ≡ MERIT` | ≤ 1e-6 MW | **2.728e-12 MW** | PASS |

**G-P4, in full** (handoff value → recomputed, all three years, `abs_delta` 0.000000 on every
cell): `gamma_model` −866.18 / −1043.37 / −843.45 · `share MERIT` 1.005 / 0.892 / 0.938 ·
`share ENV+INT` −0.005 / +0.108 / +0.062 · `a_MERIT_purged` −278.2 / −226.7 / −213.9 ·
`a_model_purged` −327.0 / −263.3 / −242.0 · `a_measured_purged` −256.0 / −119.5 / −205.4 ·
`sat_share` 0.1740 / 0.0068 / 0.0000 · `mean_bands_in_merit` 5.848 / 4.585 / 3.535 ·
`corr(env_i, z_own_nl)` +0.3063 / −0.0843 / +0.3638. **miso-238's published column is confirmed.**

**G-X0 across all four seams** (reported so "PJM is the only seam this object exists on" is
measured, not asserted; only PJM is gated): max |export leg|, MW —
PJM **0 / 0 / 0**; SPP 589.7 / 1,000.0 / 1,000.0; South 2,250.0 / 2,562.9 / 1,875.0;
Manitoba 725.0 / 1,087.5 / 1,057.3. On PJM and PJM alone `MERIT = g(s) − ḡ` exactly, so this
session's object does not exist on the other three seams and **nothing is reported for them.**

Two further identity checks (PREREG §3b / §4), all exact: the band-count identity
`g(s) ≡ G_{n−1}` **0.000e+00 MW** (the ladder is sorted, so the in-merit set really is `{0..n−1}`);
the hour-partition identity `Σ_regions γ = γ` **≤ 3.411e-13 MW/z**; and `γ` of `MERIT`
residualized on band-count dummies **exactly 0.000000** — the framing check that `MERIT` is
measurable w.r.t. `n(t)`.

## 2 — The decomposition (PJM, `ok` hours, 2023 / 2024 / 2025)

`γ` = the partial OLS slope on `z_own_net_load` in `r ~ [1 | z_own_nl | z_own_VRE]`,
`r = ols_resid(·, p1)`, MW per z-score. Marginal covariance reported beside it and never gated.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `γ_MERIT` (partial) | **−870.18** | **−930.93** | **−791.43** |
| `γ_MERIT` (marginal, reported) | −474.91 | −539.06 | −542.99 |
| `γ_LINEAR` | −581.16 | −264.27 | −578.66 |
| `γ_CURVE` | −266.51 | −634.56 | −174.89 |
| `γ_STEP` | −22.51 | −32.10 | −37.88 |
| `σ_LIN` | 0.6679 | **0.2839** | 0.7312 |
| `σ_CURVE` | 0.3063 | 0.6816 | 0.2210 |
| `σ_STEP` | **0.0259** | **0.0345** | **0.0479** |
| `σ_CURVE + σ_STEP` | 0.3321 | **0.7161** | 0.2688 |

All three `|γ_MERIT|` clear the pre-registered 200 MW/z floor, so the rule was read, and it
returned **MIXED** (§0a). Shares sum to 1.000 / 1.001 / 1.000 (rounding).

## 3 — Q-C, the gated non-parametric limb: **SURVIVES**

The handoff's own second test for (d) — `γ` re-run with the spread entered non-parametrically
(miso-237's P2 ventile block, 20 quantile bins) instead of linearly.

`γ_np(p1)` = **−677.62 / −662.69 / −590.15** MW/z, i.e. **0.779 / 0.712 / 0.746** of `γ_MERIT` —
`≥ 0.50` in all three years, so the pre-registered verdict is **SURVIVES**, whose declared
reading is: *the response is **not** a functional-form misspecification of the measured spread
`p1`, and (d) is not closed by this limb.* Three-quarters of the response is orthogonal to
**every** monotone-or-not function of the measured Indiana-hub-DA-minus-border spread.

## 4 — The pre-registered REPORTED columns, and the arithmetic bounds they place

**None of the following is a §3a verdict** — the ladder returned MIXED at step 1, so step 2 and
its sub-verdicts were never reached. These are pre-registered *reported* columns, and what they
support is a **bound**, stated as such.

**(b) K=8 discreteness is small in every year.** `σ_STEP` never exceeds **0.048**, and
`γ_STEP / (γ_CURVE + γ_STEP)` = 0.078 / 0.048 / 0.178. The PREREG §2c robustness twin — the
interpolant through the ladder's *own thresholds* `(δ_k, G_{k−1} + b̄_k/2)` rather than through
its realized level-set means — moves it to 0.113 / 0.069 / 0.260 and **agrees in every year**
(`twin_agrees_on_sub_verdict: true`), so the bound is not an artefact of the interpolant choice.
Whatever the carrier is, granularity is at most a fifth of the ladder's own non-linearity and at
most 4.8 % of `γ_MERIT`.

**(a) boundedness at the top is smaller still, and it is collapsing.** The CAP region (`n = 8`,
where `g` is clipped at `G₇`) carries **0.152 / 0.005 / −0.000** of `γ_MERIT` and 0.130 / 0.120 /
0.000 of `γ_CURVE`, on 1,524 / 60 / **0** hours. The handoff's own first check said so in advance
— mean bands in merit 5.848 / 4.585 / 3.535 of 8, "the ladder operates mid-range, NOT at its cap"
— and the partition confirms it: **in 2025 the cap is never reached and `γ_MERIT` is still
−791.43 MW/z.** The INTERIOR carries 0.794 / 0.635 / 0.602 of `γ_MERIT` throughout.
*Reported against interest:* the **FLOOR** (`n = 0`, `g` clipped at **zero**) is a different
object from the cap and it moves the other way — 0.054 / 0.361 / 0.398 of `γ_MERIT` on 48 / 409 /
865 hours. Clipping is not disappearing from the seam; it is migrating from the top to the
bottom. That is reported, not adjudicated.

**The column that speaks loudest is REPORTED, NOT GATED, and it is labelled as such.** PREREG §4
declared `γ` of `MERIT` residualized on **ventiles of the model's own merit spread `s`** as a
reported framing check and said in advance *"neither can move a verdict."* It reads
**−15.70 / +2.00 / −4.41 MW/z — 1.8 % / 0.2 % / 0.6 % of `γ_MERIT`.** Against the *measured*
spread's ventiles leaving 78 / 71 / 75 % standing (§3), the contrast is the session's sharpest
number: **entering the model's own spread non-parametrically annihilates the response; entering
the measured spread non-parametrically barely touches it.** The supporting census, also
pre-registered and reported: `corr(s, z_own_nl)` = −0.2679 / −0.1458 / −0.3165 while
`corr(p1, z_own_nl)` = +0.0539 / +0.0663 / +0.1219, and `corr(s, p1)` = only 0.4327 / 0.2559 /
0.3790. **This is evidence and it is not a verdict.** It cannot close queue item 1, it is not
quoted as one, and §5 forbids anyone acting on it.

## 5 — What this session does NOT license, restated after the numbers exactly as PREREG §5.2 fixed it before them

1. **NOTHING HERE LICENSES TOUCHING THE LADDER.** The PJM and SPP `δ_k` ladders stay derived,
   frozen and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`), and the
   `(month × hod)` deliverability envelope stays a measured input (rule 14 `[R-ACCURATE]`).
   **No re-derive, no damping factor, no smoothing of the steps, no change of `K`, no re-spacing
   of `δ_k`, no envelope change, no interface-limit change.** In particular the small `σ_STEP` is
   **not** a reason to raise `K`, and the collapsing CAP share is **not** a reason to move a
   bound. A factor swept against any residual is the rule 1 `[R-STRUCT]` fitted mechanism.
2. **Nothing here is a tuning target.** No successor may size, scale, tune or select any mechanism
   to make a modelled `γ`, share, `β` or channel value land on a number produced by this session
   (rules 1 / 13). miso-236's 328.6 / 341.7 / 207.5 MW sizing stays **un-targetable** and is not
   re-quoted as a target.
3. **No adjudicated cell is re-tested** (rule 28(a)). The saturation hypothesis stays **REFUTED**
   (miso-238) — §4's FLOOR/CAP partition is a partition of `γ_CURVE`/`γ_MERIT` by band count, a
   different object from miso-238's ENVELOPE/INTERACT channels, and it neither re-opens nor
   re-litigates that verdict; it corroborates it. Also untouched: the `(month × hod)` template
   hypothesis stays **REMOVED**; the PJM import/export asymmetry stays **CLOSED FOR PJM** (G-X0
   *uses* that closure); South's neighbour-state route stays **CLOSED**; Manitoba stays **CLOSED
   as already-armed**; the item-1 form question stays **ANSWERED** and its SPP object stays **NOT
   CHARTERED**; `internal_congestion_split` **G**, `vre_reference_rate_curtailment_grossup` **K**,
   `measured_interface_limits` **R**, `miso_rdt_measured_limit` **R**,
   `miso_south_firm_export_block` **G**, `miso_south_export_ladder_rt_tail` **R**,
   `miso_south_gas_delivered_cost_basis` **R** all stand.
4. **No cell verdict moves**; rule 28(b) attaches in its evidence-appending form only (the
   miso-206 / miso-234 / miso-235 / miso-236 / miso-237 / neiso-100 / caiso-206 no-solve
   precedent), in MISO's shard only (rule 25).
5. **No promotion, no decertification.** MISO is CALIBRATED today and nothing here trades a
   passing gate for anything (miso-227 promotion rule). C3c is untouched and stays the designated
   frontier; no LP is authorized there and none was sought.
6. **The model side is a RECONSTRUCTION** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839). **2024 is the loosest year and it is
   the year that decided the MIXED verdict** — stated in PREREG §5.8 before the numbers, and it
   is why §0b's withdrawal is a disclosure rather than a rescue.

## 6 — The successor question, NAMED and explicitly NOT CHARTERED

Queue item 1 is **open**. A successor taking it should know three things this session establishes
on gated legs and one it establishes only on reported columns:

* **Gated:** the response is not a misspecification of the *measured* spread's functional form
  (Q-C SURVIVES, 0.779 / 0.712 / 0.746); the export leg is identically zero on PJM so
  `MERIT = g(s) − ḡ` exactly; and miso-238's whole published column reproduces.
* **Gated, and negative:** the pre-registered property ladder does **not** discriminate among
  (a)–(d), because the `LINEAR`/`CURVE` split tracks `β` — where the ladder is operating — rather
  than a property of `g` (§0b). **A successor that re-runs this ladder will get MIXED again.**
  The instrument to change is the decomposition, not the bars.
* **Reported, not gated:** every candidate that is a property of `g`'s *shape* is bounded small
  in at least one year, while any function of `s` at all absorbs 98–100 % of the response (§4).

**That points at `s` itself — the model's `MISO_external` price minus the PJM border price — and
this session charters nothing about it.** Naming an object is not sizing one: no field, no
window, no forecast story, no rule-17 `[R-FLOOR-WINDOW]` argument and no rule-19 `[R-ONE-MECH]`
enumeration exists for it here, and a successor owes all four at zero LP before any solve, plus
its own PREREG with its own gate reproducing this session's column (§1's own discipline). A
DOF-free construction is the bar; miso-233 promoted on zero fitted parameters. **If no DOF-free
form exists, saying so and stopping is a complete session result** — as it is for the SPP
quantity-side charter, which remains the handoff's item 3 and is untouched here.

Handoff items **2** (export-leg asymmetry on SPP / South / Manitoba), **3** (the SPP
quantity-side charter), **4** (Manitoba determinism), **5** (CC_REGULAR 2024→2025 shape) and
**6** (the C3c charter) are **not taken** and stay exactly where they are filed.

## 7 — Governance

Rule 1 `[R-STRUCT]`: no mechanism judged by a residual; nothing proposed, sized or selected;
every number declared un-targetable in the PREREG before it was computed. Rule 12
`[R-PARALLEL]`: no LP; nothing on CI. Rule 13 `[R-MEASURED]`: measurement only; no input changed
and no measured outcome entered any solve. Rule 14 `[R-ACCURATE]`: no input changed; the measured
envelope untouched. Rule 15 `[R-DASHBOARD]`: no run produced, so nothing registered or pruned;
MISO keeps exactly one registered run and the keeper's `hourly/` sidecars stay committed.
Rule 17 `[R-FLOOR-WINDOW]`: no floor added. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21
`[R-DOF]`: **41/2, unchanged**; the decomposition carries **zero** free parameters. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and no out-of-training year was
solved, scored or registered. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run, and §5.1 forbids one
whatever the verdict. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's
shard, section and lane only. Rule 26 `[R-DELETE]`: nothing zeroed in place. Rule 27 `[R-PUSH]`:
the miso-238 probe repair is an on-disk edit, not a regenerated full-file push, and every blob
≥300 lines verified after push. Rule 28: queue item 1 named in the PREREG; evidence-append form
only. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0, and no screen is chartered.

**Artifacts.** `scripts/probes/_miso239_merit_ladder_property_attribution_phase0.py` →
`results/calibration/_miso239_merit_ladder_property_attribution_phase0.json`; miso-238's
ADDENDUM §2 repair applied to `scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py`
with `results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json` regenerated (§0c).
