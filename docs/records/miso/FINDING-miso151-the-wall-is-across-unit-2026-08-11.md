# FINDING — miso-151: item 9 was chartered, built, solved and REJECTED. MISO's offer wall is an ACROSS-UNIT level-dispersion object, not a within-unit shape object — and the arm improved both failing gates anyway

**Session** miso-151 · **ISO** MISO · **Keeper** `2026-08-09-miso-148-basis-aware`
(`miso148_basis_B`), **UNCHANGED — nothing promoted** · **Date** 2026-08-11 ·
**PREREG** `PREREG-miso151-measured-offer-surface-2026-08-11.md` (+ its dated
§4.2 amendment), pushed **before any adjudicating statistic**, blob-verified ·
**Branch fired: BRANCH-GATE-BREACH-INVERSE** — see §6, no PREREG branch
anticipated this outcome and that is recorded rather than back-fitted.

---

## 1. The one-paragraph answer

The owner chartered queue item 9 — a MISO `measured_offer_surface`,
POSITION-conditioned, SHAPE-only, subsuming `gas_offer_margin`. It was built,
armed, and solved against a same-HEAD zero-delta control. **It improved both
failing criteria** (C3a-2025 −15.6 → **−14.9 %**, C3b-2025 NRMSE 0.212 →
**0.207**, nothing regressed) **and it is still REJECTED**, because this
session's own measurements refuted its identification before the LP: MISO's real
units bid nearly **flat within their own output range** (top-of-own-curve rise
**$3.76/MWh**) against a model that rises to **$95.25**, the reverse of the
pre-registered prior by ~25× with the sign inverted; and the wall that motivated
the whole object lives **17.7× more in ACROSS-unit level dispersion**
($47.84/MWh p90−p10) than in the within-unit axis the surface conditions on.
Promoting it would be reaching the right number through a mechanism that is not
the real one — the thing rule 1 `[R-STRUCT]` forbids in the same breath as it
protects a real mechanism whose gates regress. **The durable result is the
reframing: miso-145's wall is an across-unit object, which closes the
within-unit shape family and names the successor.**

---

## 2. Footing — reproduce before extend (PREREG §2, HARD STOP)

| gate | bar | measured |
|---|---|---|
| **G-F0** miso-150's footing block | **byte-identical** | **identical**; 0 fields out of tolerance |
| **G-F0b** segment vs dense path | miso-150's own | **PASS** |
| **G-F1** committed window deficits | $0.01 | every cell **Δ 0.0** (2023 JJA −8.333, W1 −4.75; 2024 W1 −10.676 …) |
| **G-F2** rule-13 outcome census | **0** award columns | **0** across 6 partitions / **202,734,819** rows |
| **G-F3** LEVEL invariance, real data | see §7 | **5.68e-14** (half a ULP), 0 segments over tolerance |

**G-F1 is doing more work than a footing usually does.** This session refetched
the corpus to the FULL YEAR (2,192 files, 1,652.5 MB) and rewrote the curator to
stream. G-F1 passing byte-identically is the proof that neither touched the JJA
corpus miso-145/150 measured — so every comparison below is against the same
data the standing wall measurement was taken on.

---

## 3. G-1 / P-1 — the prior is REFUTED, with the sign reversed

The measured object is a within-unit, within-hour price RISE
(`Δ = price_j − price_1`), pooled 2023–2025, conditioned on own-curve position,
net-load percentile and delivered gas.

**Measured own-curve rise, $/MWh, by position bin** (DA, cap-weighted median):

| 0.0–0.2 | 0.2–0.4 | 0.4–0.6 | 0.6–0.8 | 0.8–0.9 | 0.9–1.0 |
|---|---|---|---|---|---|
| 0.4736 | 1.0636 | 1.5854 | 2.2302 | **3.7599** | 3.5230 |

**The model's own above-base rise at anchor gas**: CC_REGULAR econ_high
**$1.60**, CC_REGULAR peak **$26.57**, CC_CHP peak $26.68, ST_GAS_INTERMEDIATE
peak $37.69, CT_INTERMEDIATE peak $64.03, **CT_PEAKER peak $95.25**.

**Ratio measured ÷ model at the top = 0.0395**, against a pre-registered prior
of **3.0×, band [1.2, 12], P = 0.75**. Refuted by roughly **25×**, and in the
**opposite direction**: MISO's real book is *flatter* within a unit than the
model, not steeper.

---

## 4. G-5 — the reconciliation with miso-145, and the session's durable result

**NOT pre-registered.** miso-145's wall and this session's Δ are **different
objects**, and stating that is the finding:

* miso-145: a slope on the **fleet-cumulative** supply curve — **$73.4591/GW**.
* miso-151: a slope **inside one unit's own curve** — $/MWh from its own first
  step.

Real MISO DA book, July 2025, capacity-weighted:

| quantity | value |
|---|---|
| across-unit base offer level p10 / p50 / p90 | **0.17 / 19.58 / 48.01** $/MWh |
| p95 / p99 | 91.44 / 298.03 |
| **across-unit spread p90 − p10** | **$47.84/MWh** |
| within-unit rise at top of own curve (median) | **$2.70/MWh** |
| **ratio across-unit ÷ within-unit** | **17.7×** |

**MISO's real offer curve gets its steepness from WHICH UNIT you are on, not
from where you are inside one.** A surface that emits one Δ per position bin
destroys exactly the across-unit spread that constitutes the wall — so item 9 as
chartered **cannot reproduce the wall even in principle**, independently of any
solve result.

---

## 5. G-4 — the estimator, reported against this session's own instrument

The PREREG fixed a capacity-weighted **median**, citing the caiso-153
attenuation defect and the PJM/NEISO convention. That reasoning is about
attenuating *ratio* estimators and was imported without checking this
distribution. Measured (DA-2025-07):

* **38.0 %** of unit-hours submit a **single flat price**; 31.3 % submit ≥ 4.
* That parks **22.9 %** of capacity weight at **Δ exactly 0**.
* At p > 0.8: p50 **4.34** · p75 9.64 · p90 **13.49** · p95 24.37 · p99 **350**
  · mean **13.42** · max 555.

So the median measures *the typical unit-hour*, not the price the marginal MW is
offered at, and on the **mean** the model's CC-peak rise sits near p95 while its
econ rise sits *below* the median — a materially more nuanced picture than §3
alone. **The estimator was NOT changed.** Swapping it after seeing which way it
cut is the move rules 1 and 23 forbid; the arm ran on the surface exactly as
pre-registered and this is the caveat its result is read against.

---

## 6. The arm — and the branch that fired is one the PREREG did not contain

Same-HEAD pair, `--year 2023 2024 2025`, one invocation each, solved **alone**
(§9):

| criterion | control | **arm** | Δ |
|---|---|---|---|
| C3a-2025 | −15.6 % | **−14.9 %** | **+0.7 pp** (≈ +$0.32/MWh) |
| C3b-2025 NRMSE | 0.212 | **0.207** | **−0.005** |
| C3c tail hours 23/24/25 | 0 / 4 / 0 | 0 / 4 / 0 | unchanged |
| C1 · C2 · C4 | PASS | PASS | unchanged |

**The control reproduces the keeper EXACTLY** on every gated number
(−15.6 %, 0.212, 0/4/0), so the pair is a clean A/B despite the miso-148 K0
non-reproducibility caveat.

**Kill gates: K1 does not fire** (C3a did not move negative), **K2 holds**
(C3b-2025 fell), **K3 holds** (2023/2024 unchanged). **P-2 is outside its own
band on the low side**: +$0.32 against [+0.5, +5.5].

**The mechanism's effect is two-sided, and the direction surprised this session.**
Per-year the log reads *median measured rise +2.27 / +1.93 / +2.38 $/MWh,
median model rise replaced **−0.97 / −0.87 / −1.12**, median net mc move
**+1.38 / +1.08 / +2.00***. The model's above-base bands are priced **BELOW
their own plant's base row** — `CC_REGULAR` econ_low **0.95** against committed
**1.005** — so the model's "rising" offer curve **dips below its committed block
before rising**. The surface lifts the many econ tranches ~$1–2 and strips ~$95
off the far fewer CT peak tranches; the net was positive. **This session
predicted the opposite sign in writing, and was wrong** — which is the concrete
argument for having solved the pre-committed arm instead of refusing ex ante on
a confident forecast.

**BRANCH.** PREREG §6 enumerated SHAPE-CONFIRMED, SIGN-INVERTED, INERT and
GATE-BREACH. The actual outcome — **gates improve while the identification is
refuted** — is in none of them. It is recorded as a branch the PREREG failed to
anticipate, not retrofitted into one.

---

## 7. Verdict: REJECTED, and why gate movement does not save it

`measured_offer_surface` MISO **`U` → `R`**.

Rule 1 `[R-STRUCT]` is symmetric and this is its second half: *"never reach the
right number through a mechanism that isn't real."* The owner's standing
structure-over-gates guidance covers a **structurally-right** mechanism whose
gates **regress**; this is the inverse and the guidance does not reach it.
Supporting, none of them load-bearing on their own: the gain is below the
pre-registered band; C3a-2025 remains a FAIL at −14.9 % and C3b at 0.207 against
a 0.200 gate, so nothing closes; the armed surface rests on an estimator §4
measures as mis-specified; and neither run is promotable as-is (C6 UNATTESTED,
C8 SKIPPED on replay bundles, rule-22 leave-one-year-out not run).

**Both runs are registered** (rule 15): `2026-08-11-miso-151-control` and
`2026-08-11-miso-151-offer-surface`.

---

## 8. Named and NOT opened

* **(A) The ACROSS-UNIT dispersion object** (§4). A **new object and an owner
  decision** — explicitly *not* chartered by this session and not a re-pointing
  of item 9.
* **(B) The base-band inversion** (§6): why do MISO's econ_low bands price below
  their own committed block? Nobody chartered it, it is unexplained, and it is
  the cheapest open thread on this lane.
* Out of scope and unchanged: MISO's un-re-tuned outage extract (X_cc = 0.240)
  and the 2025 EIA-860 vintage under-carry, both cross-ISO.

---

## 9. Disclosures — including five defects this session created and caught

1. **The PREREG's own §4.2 formula was wrong** — it added the measured *total*
   rise while removing only the *conduct* markup, double-counting the model's
   physical rise. Corrected to `mc[g] := mc[base(g)] + Δ` and pushed as a dated
   amendment **before the derive ran**. No measurement informed it.
2. **The curator would have OOM'd on a full year** (44 M rows/market-year
   concatenated). Rewritten to stream via `write_clean_iter` — data-byte
   identical, ~1 GB peak instead of ~10 GB. G-F1 is the proof it changed nothing.
3. **`_miso150_universe.py --footing` DESTROYS the artifact it checks** — it
   rewrites `_miso150_universe.json` with only the footing block, dropping
   miso-150's committed `measurement`. Caught at the git check, the committed
   file restored intact, and `_miso151_surface.g_f0_footing` now calls
   `footing()` in process against a **byte-identical** bar.
4. **A wrong capacity field silently broke the mechanism.**
   `getattr(g, "pmax", 0.0)` — the field is `pmax_mw` — drove every position to
   0.0 and collapsed the position-conditioned surface onto its lowest bin. The
   first arm ran it and **looked healthy** (552 tranches repriced, plausible
   $/MWh); only `position p50 0.000` betrayed it. That run was killed and is not
   registered. **The T-2 self-test could not have caught it**: it used
   `SimpleNamespace(pmax=…)`, encoding the same wrong name as the code. Fixed
   three ways — no silent default, a guard that refuses a non-varying position
   coordinate, and `tests/test_miso_offer_surface.py` built from real
   `Generator` rows (6 tests).
5. **An OOM cost a full control solve** — it was run concurrently with the
   probe. MISO solves now run alone (~6 GB RSS, ~50 min).
6. **A gate bar that could only fail:** G-F3 demanded Δ be *bit-identical* under
   a constant curve shift, which IEEE754 cannot satisfy. Corrected to a 1e-9
   tolerance with the magnitude always reported. Disclosed prominently because
   relaxing a failed gate needs the most light — and it rescues nothing, since
   G-1 refutes the prior regardless.
7. **Tool defect, reported not worked around:** `dashboard_add_run.py` prints
   `determination: unavailable (… is not in the subpath of … OR one path is
   relative and the other is absolute)` — a relative-vs-absolute path bug in its
   metrics writer.
8. Rule 22 `[R-HOLDOUT]`: 2023/2024/2025 only, one invocation each. MISO holds
   no marker. The full-year corpus refetch spans training years only.
9. The corpus (1.65 GB raw + 1.25 GB clean) was deleted after the derive; the
   artifact is committed and the manifest makes the refetch reproducible.

**Artifacts.** `results/calibration/_miso151_surface.json`;
`data/raw/_validation-source/miso_offer_surface_positioned.json`; probe
`scripts/probes/_miso151_surface.py`; derive
`scripts/data/derive_miso_offer_surface.py`; tests
`tests/test_miso_offer_surface.py`; bundles `miso151_surface_A` /
`miso151_surface_B`.
