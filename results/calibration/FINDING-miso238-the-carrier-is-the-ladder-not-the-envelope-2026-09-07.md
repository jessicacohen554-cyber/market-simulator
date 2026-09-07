# FINDING miso-238 — the handoff's **SATURATION HYPOTHESIS IS REFUTED**: the model's spurious PJM own-net-load response, and **85–88 % of its unaccounted price-alignment remainder**, are carried by the **MERIT LADDER'S OWN NONLINEAR TRANSFORM OF THE SPREAD** — the deliverability envelope carries essentially none of either, and in 2025 it never binds at all while the response is undiminished

**Zero LP. No arm, no screen, no bundle, no registration, no cell verdict.**
**Keeper UNCHANGED at `2026-09-07-miso-233-spp-hourly`** (bundle `miso233_sppseam_K`),
DETERMINATION **CALIBRATED**, C3c the single ledgered caveat, DOF ledger **41/2**. Rule 22:
2023–2025 only; MISO holds no `complete` marker and **no out-of-training year was solved, scored
or registered**. MISO still carries exactly **one** registered run (rule 15).

**Pre-registration:
`PREREG-miso238-pjm-seam-channel-attribution-2026-09-07.md`, pushed at `0deffdb9` before any
adjudicating quantity.** One repair is governed by
`ADDENDUM-miso238-gate-repair-and-the-partial-coefficient-2026-09-07.md`, pushed at `6937a251`
**after the provenance gate rejected this session's own instrument and before the repaired
numbers were computed**; §0 below states that against interest, first. Every decision rule
applied here was fixed in one of those two documents; none was written after seeing a number.

Probe: `scripts/probes/_miso238_pjm_seam_channel_attribution_phase0.py` →
`results/calibration/_miso238_pjm_seam_channel_attribution_phase0.json`.

**Basis (PREREG §0b).** The Indiana-hub **RT** series builds the finite-hour `ok` mask
(byte-identically to miso-236/237, so the hour set is the predecessors') **and** is the alignment
price `P` — the same series miso-235 §4b and miso-237 ADDENDUM §A used. **Every regressor and
every merit signal is the Indiana-hub DA** series. They correlate only +0.402 / +0.424 / +0.553
and are never interchanged. miso-232's measured decile column (+1,303 / +1,384 / +948) is **not**
restated as reproduced by anything here.

---

## 0. STATED FIRST, AGAINST INTEREST — the provenance gate REJECTED this session's own instrument, and that is why the rest is trustworthy

PREREG §1 fixed a four-leg gate and said *"If any leg fails, the instrument is declared BROKEN and
NOTHING below is read or published."* **On the first run leg G-P2 FAILED at 457.126 MW per
z-score against a 0.5 bar**, and the probe returned before printing a single adjudicating value.
The cause was a defect in **this session's** statistic, not the predecessor's: PREREG §3 named a
simple covariance where miso-237's `own_net_load_coef_resid_model` is the **PARTIAL** OLS
coefficient on own net load in `r ~ [1 | z_own_net_load | z_own_VRE]`, holding own VRE fixed
(`_miso237_price_representation_vs_state_phase0.py` lines 543–558). The ADDENDUM declared the
repair — adopt the predecessor's estimator, which is linear in `r` and therefore keeps §2's
decomposition exact — **before** the repaired numbers were computed, and **moved no bar, floor,
gating seam or channel definition**.

**The gate after the declared repair:**

| leg | what it reproduces | cells | bar | first run | **after repair** |
|---|---|---:|---:|---:|---:|
| **G-P1** | miso-235's `sigma_measured_mw` + `sigma_resid_measured_mw` | 4 seams × 3 yr × 2 | ≤ 0.5 MW | 0.048 | **0.048 MW** |
| **G-P2** | miso-237's own-net-load coefficients, both sides, in miso-237's own metric | 4 × 3 × 2 | ≤ 0.5 MW/z | **457.126 FAIL** | **0.005 MW/z** |
| **G-P3** | miso-237 ADDENDUM §A's four-value alignment column | 4 × 3 × 4 | ≤ 0.001 | 0.00005 | **0.00005** |
| **G-ID** | the decomposition identity, `Σ channels − model_net − κ` | every hour, every seam-year | ≤ 1e-6 MW | 9.095e-13 | **9.095e-13 MW** |

**ALL FOUR PASS.** So what follows decomposes miso-235's σ column, miso-237's own-net-load
coefficient and miso-237's alignment column — the predecessors' objects, in the predecessors' own
metrics — and the decomposition is exact to machine precision rather than approximately additive.

## 1. What is measured, and the one arithmetic fact that makes the answer sharp

The keeper's seam reconstruction (miso-235's four-seam form) is, exactly, a sum of products of a
**price indicator** and an **envelope weight** (PREREG §0c, code reading only):

    imp(t) = Σ_k m_k(t)·b_k(t)      exp(t) = Σ_k q_k(t)·c_k(t)      model_net = imp − exp

with `K = 8` bands, `m_k = 1[spread > δ_k]`, `q_k = 1[p_bus < λ_k]`,
`b_k(t) = clip(env_i(t) − k·w, 0, w)`, `c_k(t) = clip(env_e(t) − k·w, 0, w)`, and `env` the
measured `(month × hod)` p90 deliverability template. Writing each factor as mean-plus-deviation
splits `model_net` into three channels, up to an additive constant every statistic here
annihilates (PREREG §2):

| channel | definition | what it can carry |
|---|---|---|
| **MERIT** | `Σ_k m̃_k(t)·b̄_k − Σ_k q̃_k(t)·c̄_k` | **a function of the PRICES ALONE.** The `b̄_k` are constants, so on the PJM seam (where the export leg is inert, §4) `MERIT(t) = g(spread(t))` for a **monotone non-decreasing step function `g` bounded above by `Σ_k b̄_k`** — non-decreasing and bounded because every `b̄_k ≥ 0` by construction. After `ols_resid(·, spread)` removes the best linear fit, **all that is left of MERIT is `g`'s own NONLINEARITY in the spread.** |
| **ENVELOPE** | `Σ_k m̄_k·b̃_k(t) − Σ_k q̄_k·c̃_k(t)` | a pure `(month × hod)` template — the deliverability envelope's own **variation** and nothing else. |
| **INTERACT** | `Σ_k m̃_k(t)·b̃_k(t) − Σ_k q̃_k(t)·c̃_k(t)` | the envelope **binding differently in different price hours** — the handoff's named hypothesis in its purest form. |

**The envelope's annual LEVEL sits inside MERIT as the fixed scale `b̄_k`, and that is correct
attribution, not a thumb on the scale:** a constant cannot carry a response to anything. What the
split attributes is the envelope's *variation* and its *interaction*, which are the only two ways
the envelope can act.

**Zero free parameters.** The split has no tunable, no threshold and no fitted weight, and G-ID
verifies it to 9.095e-13 MW.

## 2. Q-A — ITEM 3 IS ATTRIBUTED. The saturation hypothesis is REFUTED as the carrier

`γ` is miso-237's own-net-load coefficient (§0), decomposed. Bars fixed ex ante:
**ENVELOPE-DRIVEN** (the named hypothesis confirmed) iff `(γ_ENV + γ_INT)/γ_model ≥ 0.50` in all
three years; **MERIT-DRIVEN** (it refuted) iff `γ_MERIT/γ_model ≥ 0.50` in all three; **MIXED**
otherwise; read only where `|γ_model| ≥ 200` MW/z. **GATED on PJM**, the seam item 3 names.

| seam | year | `γ_model` | `γ_measured` | **`γ_MERIT`** | `γ_ENVELOPE` | `γ_INTERACT` | **MERIT share** | **ENV+INT share** |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **PJM** (GATED) | 2023 | **−866.18** | +47.40 | **−870.18** | +77.93 | −73.93 | **1.005** | **−0.005** |
| | 2024 | **−1043.37** | −361.10 | **−930.93** | −90.79 | −21.64 | **0.892** | **0.108** |
| | 2025 | **−843.45** | +271.46 | **−791.43** | +77.36 | −129.37 | **0.938** | **0.062** |
| SPP | 2023 / 2024 / 2025 | −51.15 / −34.13 / −26.95 | −296.63 / −301.92 / −16.98 | −6.52 / +15.82 / −30.18 | −53.21 / −49.95 / +1.74 | +8.59 / −0.00 / +1.49 | — | 0.872 / 1.463 / −0.120 |
| South | 2023 / 2024 / 2025 | +73.14 / +152.72 / +70.84 | +13.11 / +90.71 / −1.09 | +71.69 / +157.59 / +77.33 | −1.25 / +3.81 / −2.62 | +2.70 / −8.68 / −3.87 | — | 0.020 / −0.032 / −0.092 |
| Manitoba | 2023 / 2024 / 2025 | +161.33 / +251.62 / +55.56 | +195.94 / +422.32 / −30.61 | +43.83 / +100.54 / +52.61 | +82.27 / +127.84 / −5.16 | +35.24 / +23.24 / +8.12 | — | 0.728 / 0.600 / 0.053 |

MW per z-score, import-positive. `γ_MERIT + γ_ENVELOPE + γ_INTERACT = γ_model` exactly.

| seam | **Q-A verdict** | gated? |
|---|---|---|
| **PJM** | **MERIT-DRIVEN — THE SATURATION HYPOTHESIS IS REFUTED AS THE CARRIER** | **GATED** |
| SPP / South / Manitoba | **NOT MEANINGFUL** — `\|γ_model\|` 26.95–251.62 MW/z, below the pre-registered 200 MW/z floor in at least one year | reported |

**THE ANSWER TO THE HANDOFF'S ITEM-3 QUESTION.** *"WHY does the model's PJM tie fall in
high-MISO-net-load hours after the linear spread is removed?"* — **because the merit ladder's
8-step transform of the spread is not linear in the spread, and nothing else.** 89–100 % of the
response is in a channel that is a **function of the two prices alone**; the deliverability
envelope's variation and its interaction with price together carry **−0.5 % / +10.8 % / +6.2 %**,
and in 2023 the two are of opposite sign and **cancel to nothing** (+77.93 − 73.93 = +4.00 MW/z
against a −866.18 total). The named hypothesis does not survive its own pre-registered bar.

**The three non-gated seams are below the floor and no verdict attaches to any of them** — that
is what the floor was fixed for, and Manitoba's 0.728 / 0.600 / 0.053 share is exactly the kind
of unstable ratio on a small denominator it exists to refuse. They are reported and nothing here
opens, closes or re-tests any of them.

### 2a. The saturation census kills the hypothesis a second time, on its own terms (REPORTED, NOT GATED — PREREG §3a)

"The envelope binds" has an exact meaning in the reconstruction: `imp(t) = env_i(t)` **iff all 8
import bands are in merit**. Measured:

| PJM | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `sat_share` — hours with all 8 bands in merit | 0.1740 | 0.0068 | **0.0000** |
| `sat_share` in the top decile of own net load | **0.0297** | 0.0126 | **0.0000** |
| mean `z_own_net_load` in saturated hours | **−0.122** | +0.867 | — (none) |
| mean `z_own_net_load` in unsaturated hours | +0.026 | −0.006 | 0.000 |
| `corr(env_i, z_own_net_load)` | **+0.3063** | −0.0843 | **+0.3638** |
| `corr(env_i, P_RT)` | −0.0698 | −0.0882 | −0.0442 |

**Three independent readings, all against the hypothesis and all in the same direction.**
**(a) In 2025 the envelope NEVER binds — `sat_share` is exactly 0.0000 — and `γ_model` is
−843.45 MW/z, statistically indistinguishable in size from 2023's −866.18.** A mechanism that
requires the envelope to bind cannot produce a full-strength response in a year it never binds
in. **(b) Where saturation does occur it is concentrated in LOW-net-load hours, not high**: in
2023 saturation is nearly **six times rarer** in the top own-net-load decile than overall
(0.0297 against 0.1740) and saturated hours sit at `z = −0.122`. **(c) The envelope is LOOSER,
not tighter, in high-own-net-load hours** in two of three years (`corr` +0.3063 / +0.3638), and
its mean in the top own-net-load decile exceeds its annual mean — 6,889.5 against 6,231.0 MW in
2023 and 5,555.8 against 4,670.7 MW in 2025.

*(POST-HOC and LABELLED as such, per the handoff's disclosure rule: `mean_bands_in_merit`
5.848 / 4.585 / 3.535 of 8, `env_import_mean_mw` and its top-decile counterpart, and the
envelope's own σ of 980.3 / 1,179.2 / 1,210.0 MW, were computed as scale context and were not
named in PREREG §3a's list. **They move nothing arithmetically:** every §2 and §3 verdict is
computed from `share_envelope_plus_interact`, `share_of_model["MERIT"]` and the absolute floors
alone, none of which reads any of these values, and PREREG §3a fixed in advance that no census
value can move a verdict. They are reported because the reader should be able to see that the
envelope varies by ±16–26 % of its own mean while the merit indicator sum swings across the full
0–8 range, which is the scale reason the split lands where it does.)*

## 3. Q-B — ITEM 2's REMAINDER IS ATTRIBUTED, and it is the SAME CHANNEL

miso-237 removed 36 / 62 / 50 % of the model's excess PJM residual price alignment by purging own
state and left roughly half unaccounted. **That remainder is this leg's object**; nothing here
re-computes `phi` as an adjudication or re-tests the half miso-237 did (G-P3 reproduces its
column only as a provenance leg). The decomposed statistic is the alignment **numerator**
`a(r) = cov(r, P_RT)/σ(P_RT)` in MW, which is additive across channels where `|corr|` is not;
`|corr| = |a|/σ(r)` is reported beside it as the published quantity. Bars are the mirror of §2,
applied to the **own-state-purged** model residual; read only where `|a_model^purged| ≥ 100` MW.
**GATED on PJM.**

| PJM | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `\|corr(r_model, P)\|` — miso-237's column, reproduced (G-P3) | 0.3243 | 0.3143 | 0.2858 |
| `\|corr\|` purged — miso-237's column, reproduced | 0.2530 | 0.1967 | 0.1750 |
| `\|corr(r_measured, P)\|` purged — **the control** | 0.1745 | 0.0830 | 0.1404 |
| `a_model` (MW) | −483.2 | −509.4 | −455.0 |
| `a_measured` (MW) | −197.6 | −186.0 | −100.4 |
| **`a_model` purged (MW)** | **−327.0** | **−263.3** | **−242.0** |
| `a_measured` purged (MW) — **the control** | −256.0 | −119.5 | −205.4 |
| **`a_MERIT` purged** | **−278.2** | **−226.7** | **−213.9** |
| `a_ENVELOPE` purged | −46.4 | −34.7 | −34.1 |
| `a_INTERACT` purged | −2.4 | −1.9 | +6.0 |
| **MERIT share of the remainder** | **0.851** | **0.861** | **0.884** |
| **ENV+INT share of the remainder** | **0.149** | **0.139** | **0.116** |

**Q-B VERDICT ON PJM: MERIT-DRIVEN REMAINDER.** `85.1 / 86.1 / 88.4 %` of what is left of the
model's PJM residual price alignment after miso-237's own-state purge is carried by the merit
channel; the envelope's variation and interaction together carry `14.9 / 13.9 / 11.6 %`.
**Items 2 and 3 are ONE OBJECT and this is the number that says so** — the same channel carries
89–100 % of the spurious own-net-load response and 85–88 % of the alignment remainder, in every
year, on two statistics that share no bar.

**The measured control behaves as a control should and is reported beside every model value.**
The real seam's purged alignment numerator is −256.0 / −119.5 / −205.4 MW against the model's
−327.0 / −263.3 / −242.0 — so the model's **excess** in this metric is −71.0 / −143.8 / −36.6 MW,
and it is smaller as a share than the `|corr|` gap (0.2530 vs 0.1745 etc.) because the two
residuals differ in σ. **Both metrics are quoted and neither is presented as the other.** A
channel share is never read as a defect on its own (PREREG §4).

The three non-gated seams read **NOT MEANINGFUL** — `|a_model^purged|` is 0.3–25.7 MW on every
one of the nine cells, far below the 100 MW floor, so their shares (South 2024's 4.042, SPP
2025's −1.187, Manitoba 2023's 2.025) divide by near-zero denominators and **are disclosed as
meaningless rather than quoted**.

## 4. A LIVE ALTERNATIVE THIS SESSION FLAGGED IN ADVANCE AND CLOSED: the import/export signal asymmetry is INERT on PJM

PREREG §0c(4) recorded, as a code fact and before any number, that the armed keeper's PJM and SPP
**import** legs clear on the hourly **spread** while **every export leg on every seam still
clears on the `p_bus` LEVEL** against the fixed Q-Q ladder — so `ols_resid(·, spread)` does not
remove the export leg's own price signal, and the export leg was a candidate carrier for both
items. **It is not, because on the PJM seam it is structurally inert.** Every export sub-channel
reads exactly **0.00** in both statistics and all three years:

| PJM export leg | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| `γ_MERIT_export` / `γ_ENVELOPE_export` / `γ_INTERACT_export` | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 | 0.00 / 0.00 / 0.00 |
| `a_*_export` purged | 0.0 | 0.0 | 0.0 |

*(POST-HOC and LABELLED, and it moves nothing — it explains a value the pre-registered §3a export
leg already published as exactly zero:* the `MISO_external` bus price **never** falls below the
PJM export ladder's first rung — $12.34 / $11.32 / $18.36 — in **any** of the 8,760 hours of any
year, so no export band ever clears. In 2025 the PJM export envelope is non-zero for 420 hours
(max 698.5 MW) and **still** no band clears, because the merit test never fires. *)*

**So the asymmetry PREREG §0c(4) named has ZERO footprint on the PJM seam and cannot be part of
either item's explanation.** It is recorded here as closed for this seam, and **nothing about it
is proposed** — PREREG §5.1 fixed that in advance and it binds.

## 5. What is handed forward — NAMED, and NOT CHARTERED

No lever is proposed and nothing here licenses one. The PREREG fixed that before the numbers.

1. **THE HANDOFF'S NAMED SATURATION HYPOTHESIS IS REFUTED ON A PRE-REGISTERED RULE** (§2, §2a).
   The deliverability envelope is **not** the carrier of the model's spurious PJM own-net-load
   response, and the strongest single reason is arithmetic rather than statistical: in 2025 the
   envelope **never binds** (`sat_share` 0.0000) and the response is undiminished (−843.45 MW/z).
   **Rule 28(a): do not re-test this.**
2. **ITEMS 2 AND 3 ARE ONE OBJECT AND THE OBJECT IS NAMED: the merit ladder's own NONLINEAR
   transform of the spread.** It carries 89–100 % of the own-net-load response and 85–88 % of the
   alignment remainder, on two statistics sharing no bar. **This NAMES an object; it charters
   nothing**, sizes nothing and names no field.
3. **WHAT IS STILL OPEN INSIDE THE NAMED CHANNEL, stated so a successor does not over-read this.**
   MERIT on the PJM seam is `g(spread)` for a monotone bounded 8-step `g` (§1), so the carrier is
   `g`'s nonlinearity — but **this session does not resolve WHICH property of `g` does it**
   (its boundedness at the top, its step granularity at `K = 8`, the placement of the `δ_k`, or
   the spread's own relation to own net load). Those are distinguishable at zero LP by the same
   instrument and are the successor's question. **What is settled is only what the pre-registered
   rule settles: the envelope is not the carrier and the price-side ladder is.**
4. **NOTHING HERE LICENSES A RE-DERIVE OR A DAMPING FACTOR** on the PJM or SPP `delta_k` ladders,
   which are derived, frozen and **pinned to their derives by test** (rule 23
   `[R-FROZEN-DERIVE]`), and nothing licenses touching the measured `(month × hod)` deliverability
   envelope (rule 14 `[R-ACCURATE]`). **This binds precisely because §2 and §3 land on the
   ladder**: PREREG §5.2 fixed it in advance for exactly this outcome, and a factor swept against
   `γ` or `a` is the rule 1 `[R-STRUCT]` fitted mechanism. **Every number in this document is
   declared UN-TARGETABLE** (PREREG §5.3).
5. **THE PJM EXPORT LEG IS INERT and its signal asymmetry is closed for this seam** (§4). Nothing
   is proposed about it.
6. **UNCHANGED AND NOT RE-TESTED:** the SPP quantity-side object stays **NAMED AND NOT CHARTERED**
   (miso-237 §7.1) and its form question stays **ANSWERED**; South's neighbour-state route stays
   **CLOSED** (miso-236 D-4) and South stays routed upstream to the South-gas price-out lane
   (`gas_marginal_commodity_pricing` **O** / `gas_variable_transport` **O**, owner-court);
   `miso_manitoba_seam` stays **CLOSED as already-armed** (miso-235 §3) and its determinism
   question (miso-236 §5.3) is untouched; the `(month × hod)` template hypothesis stays
   **REMOVED** (miso-236 §3) and was not re-tested; miso-237's own-state purge half of item 3
   stays as it was and was reproduced only as provenance.
7. **C3c** is untouched and stays the designated frontier (2026-07-20). Its charter needs a new
   admissible measured identification **and an owner ruling**; no LP is authorized there and none
   was sought.
8. **The CC_REGULAR 2024→2025 shape emergence** is untouched and stays where miso-234 filed it.

## 6. Non-claims

1. **This session solved nothing.** No screen was run, so nothing here has been through a
   structural gate, and no number is a solve result.
2. **"MERIT-DRIVEN" is an attribution, not a defect finding.** That a channel carries a response
   does not by itself make the channel wrong; the measured control is quoted beside every model
   value in §3 for exactly that reason, and §5.3 states what the attribution does **not** resolve.
3. **The model side is a RECONSTRUCTION number** (miso-235's four-seam form, harness
   `corr(recon, committed)` +0.9845 / +0.9745 / +0.9839), labelled as one in every table. **2024
   remains the loosest year**, and it is also the year with the largest `γ_model` (−1,043.37) and
   the largest `a` excess (−143.8 MW); the three are reported together and none explains another.
4. **The PREREG's first statistic was wrong and the gate caught it** (§0). The published `γ` is
   miso-237's partial coefficient; the marginal one the PREREG originally named is reported
   beside it in the JSON as `gamma_marginal_*` (PJM model −422.00 / −586.24 / −532.47) and **no
   verdict is read on it**.
5. **Three of four seams are BELOW the pre-registered floors on both legs** and carry no verdict
   in either direction. Their channel shares are disclosed as meaningless, not quoted.
6. **The PJM seam's own analysis is on the four-seam reconstruction, not on a census of the real
   tie**; IESO has no US-BA record, but no neighbour-state block enters this session at all, so
   miso-236's 82–84 % census does not bear on any number here.
7. **No verdict moves anywhere in the matrix**, in either direction. Evidence only.
8. **MISO has no failing gate**, and nothing here proposes trading a passing one. There is no
   rubric failure anywhere in the program and this session did not invent one.

## 7. Governance

Rule 1 `[R-STRUCT]`: no mechanism was judged by a residual; nothing was proposed or selected, and
every number here was declared un-targetable before it was computed (PREREG §5.3). Rule 12
`[R-PARALLEL]`: no LP was solved; nothing ran on CI. Rule 13 `[R-MEASURED]`: measurement only; no
measured outcome enters any solve and no input changed. Rule 14 `[R-ACCURATE]`: no input changed;
§5.4 restates that the measured deliverability envelope is not touched. Rule 15 `[R-DASHBOARD]`:
no run produced, so nothing registered or pruned; MISO keeps exactly one registered run and the
keeper's `hourly/` sidecars stay committed. Rule 17 `[R-FLOOR-WINDOW]`: no floor added. Rule 19
`[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged; the decomposition itself
carries **zero** free parameters. Rule 22 `[R-HOLDOUT]`: 2023–2025 only; MISO holds no `complete`
marker and no out-of-training year was solved, scored or registered. Rule 23
`[R-FROZEN-DERIVE]`: no derive re-run; §5.4 restates the freeze and binds this session's own
result to it. Rule 24 `[R-REGISTRY]`: no field created. Rule 25 `[R-ISO-SCOPE]`: MISO's shard,
section and lane only. Rule 27 `[R-PUSH]`: every pushed blob verified against local. Rule 28(a):
the queue items taken are the handoff's items 3 and 2, declared in PREREG §0 as one object on one
instrument exactly as the handoff licenses; every standing adjudication this touches
(`miso_south_firm_export_block` **G**, `miso_south_export_ladder_rt_tail` **R**,
`miso_manitoba_seam` closed-as-armed, `vre_reference_rate_curtailment_grossup` **K**,
`internal_congestion_split` **G**, `measured_interface_limits` **R**, `miso_rdt_measured_limit`
**R**) is **corroborated or untouched, never re-tested**. Rule 28(b): no verdict moves; evidence
appended in-session. Rule 29 `[R-SCREEN]`: clause 0 in full — zero-LP phase 0 first, and it
**refuted the successor's one named hypothesis and attributed two open defects to a single named
channel before a single LP minute was spent**, which is the outcome the clause exists to produce.
