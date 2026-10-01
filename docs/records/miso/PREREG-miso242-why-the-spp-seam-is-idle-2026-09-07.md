# PREREG miso-242 — WHY IS THE MODEL'S SPP SEAM AT **EXACTLY ZERO FLOW** IN 42 / 41 / 48 % OF HOURS?

**Queue item taken (rule 28(a)): item 1 of the miso-241 handoff — the RECOMMENDED item, and the
first thing miso-241 surfaced that nobody has explained.** Zero LP. No arm, no screen, no bundle,
no registration, no field, no cell verdict.

**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `results/calibration/miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22
`[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete` marker and **no out-of-training year will be
solved, scored or registered**. MISO carries exactly **one** registered run (rule 15) and this
session does not change that.

**This document is pushed BEFORE any adjudicating quantity is computed, together with the probe that
computes them** (`scripts/probes/_miso242_spp_idle_seam_phase0.py`). Every decision rule below is
fixed here; none may be written after seeing a number.

---

## 0. The facts this rests on, established from SOURCE and COMMITTED CONFIG before this document was written

No adjudicating quantity is used in §0. Each item is a code or committed-table reading and is cited.

**F1 — the merit test.** `scripts/probes/_miso241_spp_quantity_side_charter_phase0.py::build_recons`
(the REPAIRED four-seam reconstruction, which superseded on miso-235's own I-1/I-2 rule at
miso-241 §2) clears the SPP seam's bands as

```
import band k in merit  iff   s(t) >  δ_k^imp        s(t) := p_bus(t) − spp_hub(t)
export band k in merit  iff   s(t) <  δ_k^exp
```

with `p_bus` the keeper's committed `MISO_external` P1 zonal price (`BUS_OF_SEAM["SPP"]`) and
`spp_hub` the measured SPP NORTH hub DA (`measured_miso_spp_hub_prices`). Both legs are a test on
the **spread** `s`, which is §0a of miso-241's finding and the whole content of its Q-0 repair.

**F2 — the committed frozen ladder** (`src/market_sim/model/interchange/spec.py`,
`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_SPP_BY_YEAR`), quoted here so G-T can bind on it:

| year | `import` band 1…8 | `export` band 1…8 |
|---|---|---|
| 2023 | 14.10, 32.64, 54.43, 85.36, 145.25, 185.08, 185.08, 185.08 | −4.20, −24.96, −47.33, −92.59, −241.46, −521.38, −521.38, −521.38 |
| 2024 | 14.49, 35.59, 78.29, 212.51, 290.73, 290.73, 290.73, 290.73 | −2.15, −19.39, −33.38, −42.97, −54.84, −64.17, −70.15, −83.23 |
| 2025 | 21.85, 46.55, 87.43, 169.08, 216.02, 252.76, 276.99, 345.40 | 1.04, −14.46, −29.20, −45.92, −125.99, −316.80, −515.34, −515.34 |

and the PJM comparator (`MISO_SEAM_LADDER_NEIGHBOUR_HOURLY_BY_YEAR`), import band 1 =
**−29.17 / −13.87 / −15.79**, export band 1 = **−93.98 / −35.03 / −60.49**.

**F3 — the DEAD BAND, an arithmetic identity on F1+F2.** The import ladder is non-decreasing in `k`
and the export ladder non-increasing, so `n_i = 0 ⟺ s ≤ δ_1^imp` and `n_e = 0 ⟺ s ≥ δ_1^exp`.
The seam is therefore at **exactly zero flow** (both legs out of merit) iff

```
δ_1^exp  ≤  s(t)  ≤  δ_1^imp                    [THE DEAD BAND]
```

On F2 that band is **[−4.20, +14.10] / [−2.15, +14.49] / [+1.04, +21.85]** $/MWh — width
**18.30 / 16.64 / 20.81** — against PJM's **[−93.98, −29.17] / [−35.03, −13.87] / [−60.49, −15.79]**,
whose *upper* edge is **negative in every year**. The monotonicity this identity needs is GATED
(G-T), not assumed.

**F4 — the estimator that set those thresholds.**
`scripts/data/derive_miso_seam_ladders.py::derive_spp_neighbour_hourly` → `_derive_one` → `qq_import`
/ `qq_export`, on `spread = MISO hub DA − SPP hub DA` and the measured SPP seam net flow, at the
midpoint-depth grid `mid_k = (k + 0.5)·step`, `step = interface_limit_mw / SEAM_FLOW_TRANCHES`
= 4000/8 = **500 MW**, so `mid_1 = 250 MW`. The two estimators are, verbatim:

```
δ_k^imp = quantile( spread , 1 − P(flow >  mid_k) )
δ_k^exp = quantile( spread ,     P(flow < −mid_k) )
```

**F5 — the CONSEQUENCE of F3+F4, which is what this session tests.** Substituting `k = 1` into F4
and F3, the share of hours the dead band captures **on the estimator's own spread** is

```
P( δ_1^exp ≤ spread ≤ δ_1^imp )  =  1 − P(flow > 250) − P(flow < −250)  =  P( |flow| ≤ 250 MW )
```

i.e. **a Q-Q ladder's dead band is constructed to reproduce the MEASURED seam's own near-zero
duration**, and the model's 500 MW band granularity then renders every such hour as *exactly* zero.
That is an identity of the estimator, not a measurement; whether the **committed, rounded, no-wash-
reconciled** table actually delivers it, and whether the **model's** spread delivers it too, are the
two things §2 and §3 measure and either could fail.

**F6 — the phenomenon, as published by miso-241 §3 (reported there, gated nowhere).** SPP at exactly
zero flow **0.4175 / 0.4066 / 0.4810**; import leg zero-in-merit 0.5718 / 0.5788 / 0.7052; mean
import bands in merit 0.50 / 0.49 / 0.33 of eight; `ceiling_active_share` 0.2572 / 0.2952 / 0.2474;
`env_i` = 0 in 0.0106 / 0.0035 / 0.0034. The measured seam's σ is 577.3 / 687.3 / 615.4 MW. **σ is
not a near-zero-duration statistic and this session does not treat it as one.**

### 0b. Basis discipline (the lane's standing rule, restated and binding)

The Indiana-hub **RT** series (`_miso224_floor_anatomy_phase0.actual_zone_price`, `values="rt"`)
builds the finite-hour `ok` mask, byte-identically to miso-235/236/237/238/239/240/241. Every
**spread** is on the Indiana-hub **DA** (the basis the ladders were Q-Q derived against). The SPP
anchor is the measured SPP **NORTH** hub DA. They correlate only +0.402 / +0.424 / +0.553 and are
never interchanged. miso-232's measured decile column (+1,303 / +1,384 / +948) is **not** restated
as reproduced by anything here.

### 0c. Row sets, named in advance so no comparison hides one

* **R_D — the DERIVE row set**: `dropna` on (SPP hub DA, MISO hub DA, measured SPP seam flow), the
  row set `derive_spp_neighbour_hourly` itself uses. Q-A is an identity test and runs here.
* **R_K — the KEEPER row set**: the `ok` mask, on the dense/interpolated series miso-241 built.
  Q-B compares two spreads on this **one common** row set, so only the spread differs.

Both are reported for every share, so the row-set difference is visible rather than absorbed.

---

## 1. THE PROVENANCE GATE — six legs. If ANY leg fails the instrument is BROKEN and no Q is read

Each leg reproduces a predecessor's published quantity **in the predecessor's own metric, reading
its estimator rather than its label**, on this session's independent code path. Every reference
value is restated inside the probe so **each leg binds even if the predecessor's JSON artifact is
missing** (the lane's standing "survive the artifact being absent" duty).

| leg | what it reproduces | bar |
|---|---|---|
| **G-T** | the committed SPP + PJM hourly ladder tuples equal §0's F2 quotation, **and** import is non-decreasing / export non-increasing in `k` for both seams, all years | exact equality; **zero** monotonicity violations |
| **G-Z** | miso-241 §3's SPP zero-flow share **0.4175 / 0.4066 / 0.4810** and its `env_i`=0 share 0.0106 / 0.0035 / 0.0034 | ≤ 0.002 |
| **G-L** | miso-241 §3's SPP `ceiling_active_share` **0.2572 / 0.2952 / 0.2474** and mean import bands in merit 0.50 / 0.49 / 0.33 | ≤ 0.002 / ≤ 0.01 |
| **G-ID** | miso-241's identity leg: `flow ≡ min(env^eff, n·w)` on **both** legs of **both** export variants, all four seams | ≤ 1e-6 MW, **0** prefix violations |
| **G-B** | miso-241 Q-0's **REPAIRED** harness `corr` **0.9917 / 0.9935 / 0.9935** and mean level error **8.9 / 1.8 / 5.8 MW** — i.e. this session's reconstruction IS the repaired instrument, not the superseded one | ≤ 0.002 / ≤ 0.5 MW |
| **G-DB** | the dead-band-identity leg: the hour set `{n_i = 0 ∧ n_e = 0}` computed from the band counts equals the hour set `{δ_1^exp ≤ s ≤ δ_1^imp}` computed from F3, on R_K, all years, both seams | **0** disagreeing hours |

**G-DB is falsifiable, not bookkeeping**: it fails if the ladder is not monotone in its own clearing
direction, or if the merit predicate is not the one F1 states. G-B is the leg that would catch this
session silently reverting to miso-235's superseded export pricing.

---

## 2. Q-A — THE Q-Q IDENTITY LEG. Does the COMMITTED, ROUNDED table reproduce its own estimator's target?

Computed on **R_D**:

* `Z_target` := `P(|measured SPP net flow| ≤ 250 MW)` = `1 − P(flow > 250) − P(flow < −250)`.
* `Z_derive` := `P( δ_1^exp ≤ (miso_da − spp_hub) ≤ δ_1^imp )` on the **frozen committed** ladder.

**Decision rule, fixed here.** `|Z_derive − Z_target| ≤ 0.020` in **all three years** ⇒ **IDENTITY
HOLDS**. Otherwise ⇒ **IDENTITY FAILS**.

Tolerance justification, fixed before the numbers: the committed table is rounded to 2 dp and the
same-seam no-wash clamp may move an export band; both perturb a *share* by far less than 0.020 on a
spread whose σ is tens of $/MWh over ~8,750 hours. 0.020 is ~1/20 of the phenomenon (§0 F6), so a
pass cannot be an artifact of a loose bar.

**If IDENTITY FAILS**, that is a finding **about the committed table**, published at full magnitude
and named as such. It licenses **NO re-derive, no damping factor, no re-spacing and no change of K**
(§5.2). It is fixed here, before the number, that a failure is reported and handed forward — never
repaired in this session.

---

## 3. Q-B — THE BASIS-DISPLACEMENT LEG. Does the MODEL's spread transmit the derive basis, or displace it?

Computed on the single common row set **R_K**:

* `Z_model` := `P( δ_1^exp ≤ (p_bus − spp_hub) ≤ δ_1^imp )` — the phenomenon itself (G-Z pins it).
* `Z_derive^K` := `P( δ_1^exp ≤ (miso_da − spp_hub) ≤ δ_1^imp )` — the same ladder, same hours, the
  derive's spread.

**Decision rule, fixed here.** `|Z_model − Z_derive^K| ≤ 0.050` in **all three years** ⇒
**TRANSMITTED** (the model's bus price is not what puts the seam at zero). Otherwise ⇒
**DISPLACED**, and its **sign and magnitude are reported per year**, together with the four
diagnostics that characterise it — `mean(s_model)`, `mean(s_derive)`, `σ(s_model)`, `σ(s_derive)` —
so a successor can tell a *shift* from a *compression*.

Bar justification, fixed before the numbers: 0.050 is ≈ 1/8 of the observed zero share, so a
displacement below it cannot account for the phenomenon; and it is 2.5× Q-A's bar, so the two legs
cannot both pass on the same slack.

---

## 4. Q-C — THE ADJUDICATION. The decision table, fixed before any number

| Q-A | Q-B | **VERDICT** |
|---|---|---|
| IDENTITY HOLDS | TRANSMITTED | **INHERITED.** The 42–48 % is the MEASURED SPP seam's own near-zero duration, transmitted faithfully by a ladder whose dead band is correct on both bases. This is the handoff's third hypothesis — *"this is what a Q-Q ladder on a near-zero-mean seam must look like"*. **Item 1 CLOSES. Nothing is chartered, no successor is named on this object.** |
| IDENTITY HOLDS | DISPLACED | **DISPLACED.** The ladder is correct on its own basis; the model's bus-price spread sits elsewhere, and the excess zero share is attributable to that. This is the handoff's first hypothesis in its *measurement* form. **Item 1 closes with ONE named successor — the `MISO_external` bus-price basis — and nothing is chartered here.** |
| IDENTITY FAILS | any | **TABLE-INTERNAL.** The committed table does not reproduce its own estimator's target. Published at full magnitude, handed forward, **no re-derive licensed**, nothing chartered. |

**In every branch this session charters nothing, arms nothing and solves nothing.** The handoff
blesses the first branch explicitly: *"If the answer is 'the ladder is correct and the real seam's
flow is simply not spread-driven', SAY SO AND STOP — that is a complete session result and it closes
the SPP seam for good."*

### 4a. Q-D — THE PJM CONTRAST. Reported in full; **gated on exactly one thing**

The same three shares for **PJM** (its own `mid_1` = 7300/8 × 0.5 = **456.25 MW**), plus both seams'
dead-band widths (§0 F3) and both spreads' σ.

**The ONE gated question:** is `Z_target(PJM) < Z_target(SPP)` in **all three years**?
**YES** ⇒ the two seams' zero-flow behaviour differs **in the measured record, before any model
object touches it** — which is corroboration of Q-C's first branch on an entirely measured
statistic. **NO** ⇒ the contrast attaches nothing and is reported only. Everything else in Q-D is
**reported, never gated**.

### 4b. Q-E — THE SIGN / BASIS LEG. The handoff's second hypothesis, made falsifiable

* **E1 (sign).** `corr(model SPP net flow, s_model) > 0` in all three years. A **negative** value
  would mean the model's seam imports when MISO is *cheap* relative to SPP — a sign defect, and it
  would be the session's headline. Reported alongside, never gated:
  `corr(measured SPP net flow, s_derive)`, which miso-233's own derive docstring records as
  +0.041 / −0.020 / +0.050 — **the measured seam is barely spread-driven at all**, and that number
  is quoted as context, not as a bar.
* **E2 (basis).** `corr(p_bus, miso_da)` and the mean/σ of both, per year — **reported, never
  gated**; miso-240 closed the external-bus-price question and this session does **not** re-open it
  (rule 28(a)).

**Decision rule:** E1 fails in any year ⇒ **SIGN DEFECT**, which overrides Q-C's verdict and becomes
the session's finding. E1 passes in all three ⇒ the sign hypothesis is **REFUTED** and Q-C stands.

---

## 5. What this session may NOT do — fixed here, for EVERY outcome

### 5.1 Nothing measured here is a target

**Every number this probe produces is UN-TARGETABLE.** No successor may size, scale, tune or select
any mechanism to make a modelled quantity land on any of them. This binds identically whether the
verdict is INHERITED, DISPLACED or TABLE-INTERNAL, and it binds on the PJM contrast and on the
measured near-zero durations in particular. Rule 1 `[R-STRUCT]` and rule 13 `[R-MEASURED]`.

### 5.2 The standing freezes, restated in advance and binding on every branch

**NO re-derive, NO damping factor, NO change of K, NO re-spacing of δ_k, NO envelope change, NO
percentile change, NO interface-limit change.** The PJM and SPP `δ_k` ladders stay derived, frozen
and pinned to their derives by test (rule 23 `[R-FROZEN-DERIVE]`); the measured `(month × hod)`
envelope, its p90 and every interface limit stay untouched (rule 14 `[R-ACCURATE]`). miso-238 §5.2,
miso-239 §5.2, miso-240 §5.2 and miso-241 §5.2 each fixed this in advance for exactly the outcomes
they got, and it is fixed again here **before** Q-A is computed — including for the branch in which
Q-A FAILS, which is the branch where the temptation to re-derive is largest.

### 5.3 No re-testing of settled adjudications (rule 28(a))

Queue item 1 (the external-bus price) stays **CLOSED**; the per-seam external-node split stays
**REFUSED at zero LP**; the saturation hypothesis stays **REFUTED**; miso-239's Q-A stays **MIXED**
and Q-C **SURVIVES**; miso-240's Q-B stays **UNRESOLVED**; the `(month × hod)` template hypothesis
stays **REMOVED**; the PJM import/export asymmetry stays **CLOSED FOR PJM**; South's neighbour-state
route stays **CLOSED**; `miso_manitoba_seam` stays **CLOSED as already-armed**; the SPP
quantity-side charter stays **REFUSED — NO DOF-FREE FORM** (miso-241 §5) and **is not re-opened
here**; `internal_congestion_split` **G**; `vre_reference_rate_curtailment_grossup` **K**;
`measured_interface_limits` **R**; `miso_rdt_measured_limit` **R**; `m2m_seam_entitlement_cap` **G**;
`miso_south_firm_export_block` **G**; `miso_south_export_ladder_rt_tail` **R**;
`miso_south_gas_delivered_cost_basis` **R**.

### 5.4 No verdict moves and no mechanism is added

Rule 28(b): this session tests no mechanism, so **no cell verdict moves in either direction**;
evidence only is appended to MISO's shard, in-session. Rule 19 `[R-ONE-MECH]`: nothing is added, so
nothing replaces and nothing reconciles — miso-241 §7's enumeration of what already sets the
MISO–SPP seam stands unamended. Rule 21 `[R-DOF]`: the ledger stays **41/2**; this probe introduces
**zero** free parameters (its only constants are the four decision bars fixed above and the ±250 /
±456.25 MW midpoints, which are `interface_limit_mw / SEAM_FLOW_TRANCHES / 2` — an identity, not a
choice). Rule 24 `[R-REGISTRY]`: no field created.

### 5.5 Disclosure duties accepted in advance

If this session's own gate or instrument fails, the failure is published **first, at full
magnitude**, any repair is declared in a **pushed ADDENDUM before the repaired numbers exist**, no
bar is moved, and a repair that makes a gate **stricter** is preferred. Any quantity computed
post-hoc is **labelled POST-HOC** and shown arithmetically to move nothing. A non-gated leg that
would have read differently, a statistic that is not the predecessor's, and any advance suspicion
this session raises that is later refuted **or confirmed**, are all disclosed against interest.

---

## 6. Non-claims, fixed in advance

1. This session **solves nothing**: no screen, no bundle, no LP minute, no determination moves.
2. The model side is a **RECONSTRUCTION** (repaired instrument, harness `corr` 0.9917 / 0.9935 /
   0.9935 — close, not 1). Every model-side share inherits that.
3. A measured near-zero duration is **not a licence** and **not a defect**: it is a duration.
4. **MISO has no failing gate.** There is no rubric failure anywhere in the program and this session
   does not invent one. Nothing here trades a passing gate for anything.
5. Q-D's non-gated columns and Q-E's E2 are **context, not verdicts**, and are not converted into
   one however suggestive they read.
