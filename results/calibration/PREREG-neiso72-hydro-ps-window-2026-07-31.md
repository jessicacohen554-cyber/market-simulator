# PREREG (neiso-72): NEISO's pumped-storage TIME SPLIT — the per-window level
# treatment, pre-registered BEFORE any solve and BEFORE the charter is granted

**Session:** neiso-72 (the miso-109 §7 / pjm-143 §2 hand-back — NEISO's own lane,
the last open cell of the `hydro_level_923_hy` row)
**Date:** 2026-07-31
**Status:** committed and pushed **before any solve**. NEISO is
calibration-complete with a **declared frontier**, so this document is the
charter request's evidence base — **no keeper-moving solve runs until the owner
signs off** (matrix §5.6: "charter required first").
**Rule 25 `[R-ISO-SCOPE]`:** every number below derived from NEISO's own data
this session (`scripts/probes/_neiso72_ps_window_audit.py`); no MISO or PJM
verdict transferred, and §2 states explicitly where the PJM argument does *not*
transfer.

---

## 1. The seam, measured

The LP's hydro units are EIA-923 prime mover `HY` — conventional inflow hydro
alone (`data/hydro.py` excludes `PS`; pumped storage is a storage resource, not
inflow). The NEISO keeper `2026-07-31-neiso-70-ctheatrate` carries
`hydro_eia930_monthly=true` + `hydro_backfill_year=2024`, so it pins those
units' monthly energy **level** to EIA-930 `NG: WAT`.

NEISO is the **only one of the six ISOs that files an `NG: PS` column at all**,
and it starts filing it part-way through the series. The onset is not
approximate — it is a single hour (probe §1, §9):

| measurement | value |
|---|---|
| first hour with a filed `NG: PS` value | **2024-11-07 00:00** (row 7440 of 8760) |
| filed hours before it, 2019-01 → 2024-11-06 | **zero**, in every month of every year |
| filed hours after it | 1,296 in 2024 (Nov 576, Dec 720); 8,736 in 2025 |
| `NG: PS` sign | **discharge only** — 1.932 TWh positive in 2025, **0.000 pumping**, min 0 MW |

So NEISO's `NG: WAT` folds pumped storage through **2024-11-06** and is split
clean from **2024-11-07**. That is a *per-window* exposure, not the standing
fold MISO and PJM have.

## 2. That the pre-split column really carries the PS block — four independent tests

The registry membership test (miso-109's three signatures) does not apply
literally here, because signature (a) is "files no `NG: PS` column" and NEISO
does file one. The claim needing proof at NEISO is narrower and different:
*before the seam, is the PS energy inside `NG: WAT`?* Four tests, each
independently checkable.

**(i) Nameplate breach stops at the seam, permanently** (probe §2). `NG: WAT`
exceeds NEISO's **own** 1,926.3 MW conventional (`HY`) EIA-860 nameplate in
63–276 h/yr across 2019–2024 — and **0 hours in 2025**, the first fully-split
year. Conventional inflow hydro cannot exceed its own nameplate.

**(ii) The shape fingerprint matches `WAT + PS`, not `WAT`** (probe §6). The
post-split window supplies *both* reference fingerprints from NEISO's own data,
so this is a matched-pair test, not an assumption. All metrics scale-free:

| series | diurnal swing | p99/p50 | >nameplate |
|---|---|---|---|
| POST-split `WAT` alone — the "clean" reference | **1.48×** | 2.60 | **0.0**/1000 h |
| POST-split `WAT + PS` — the "folded" reference | **2.89×** | 3.01 | **19.0**/1000 h |
| PRE-split 2023 | 2.20× | 2.37 | 30.3/1000 h |
| PRE-split 2024 Jan–Oct | 2.70× | 2.60 | 37.8/1000 h |
| PRE-split 2019–2022 | 2.46× | 2.55 | 13.0/1000 h |

Every pre-split window sits at the folded reference and nowhere near the clean
one, on both metrics.

**(iii) The magnitude is the whole PS fleet, not a trace** (probe §8). A
two-component non-negative least squares of each window's 24-point diurnal
profile onto the two measured post-split shapes,
`pre_hod = A·conv_shape + B·ps_shape`. **Self-tested first** on the window whose
answer is known: it returns **0 MW** for post-split `WAT` alone (true 0) and
**218 MW** for post-split `WAT + PS` (true 219). On the pre-split windows:

| window | fitted PS | implied TWh/yr | rms |
|---|---|---|---|
| 2023 | 188 MW | 1.646 | 49.8 MW |
| 2024 Jan–Oct | 263 MW | 2.302 | 72.1 MW |
| 2022 | 196 MW | 1.717 | 44.0 MW |
| 2021 | 178 MW | 1.560 | 46.4 MW |
| 2020 | 168 MW | 1.472 | 46.7 MW |
| 2019 | 154 MW | 1.346 | 49.0 MW |

Against the **1.932 TWh/yr measured directly** in the post-split column. The
fold is full-size. *Stated assumption:* the conventional diurnal shape is stable
across the seam; NEISO's conventional hydro is price-following, so this is an
**estimate with an assumption**, not a measurement — which is why it is
corroborating evidence, not the load-bearing test.

**(iv) The seam falls INSIDE a month — the confound-free test** (probe §9).
Because the onset is 2024-11-07, pre- and post-split windows sit six days apart
inside November 2024: same fleet, same water, same season.

| November 2024 window | h | mean `WAT` | max `WAT` | diurnal swing |
|---|---|---|---|---|
| Nov 1–6, **PRE**-split | 145 | 525 MW | **1,873 MW** | **7.11×** |
| Nov 7–30, **POST**-split | 576 | 332 MW | **685 MW** | **1.79×** |

The peak collapses 63 % and the swing flattens 4× at the hour the PS column
starts being filed. No inflow process does that in six days.

**Where the PJM argument does NOT transfer (rule 25).** pjm-143 refused a
930→923 reconciliation factor partly because PJM's monthly gap **never changes
sign**. NEISO's changes sign constantly — **21 of its 70 pre-split months are
negative**, up to −146 GWh. That is not evidence against the fold (test iv is
decisive); it is evidence that a *second, opposite-signed* discrepancy is also
present — see §3, which is genuinely new and is the reason this session is a
charter request rather than a one-line registry edit.

## 3. The finding the handoff did not anticipate — two large errors that cancel

The handoff sized this lever from the 930-vs-923 **level** gap: "+2.7 %…+10.1 %,
expect a small effect". That gap is real and reproduces exactly (probe §3):

| year | 930 `NG: WAT` (pinned) | 923 `HY` (the units) | gap |
|---|---:|---:|---:|
| 2023 | 8.775 TWh | 8.547 TWh (173 plants) | +0.228 TWh / **+2.7 %** |
| 2024 | 7.394 TWh | 6.714 TWh (169 plants) | +0.681 TWh / **+10.1 %** |
| 2025 | 5.121 TWh | *early release, 6 of a modal 173 — not differenced* | — |

But §2 shows the fold alone is worth **~1.9 TWh/yr**. A +1.9 TWh contamination
cannot produce a +0.23 TWh gap unless something else subtracts ~1.6 TWh. So a
**second discrepancy of order 1.2–1.6 TWh/yr, opposite in sign, is also
present**: EIA-930's `NG: WAT` under-reports the conventional hydro that the
EIA-923 `HY` census carries (BA telemetry misses small/distribution-connected
plants the 173-plant filing includes). The §8 `conv` coefficients say the same
thing — 2023 fits 814 MW ≈ 7.13 TWh against a 923 `HY` of 8.547 TWh.

**This does not change the fix, and it does not change its size.** Refusing the
pin uses 923 `HY` directly, which removes *both* errors at once, and the net
level move stays small precisely *because* they were cancelling. What it changes
is the **story**: the pre-split pin was not "nearly right"; it was two ~1.5–1.9
TWh errors landing near zero together. That is exactly the silent-compensation
pattern rule 14 `[R-ACCURATE]` exists to catch.

**Honesty boundary.** The second discrepancy is only weakly measured. The one
clean post-split month with a complete 923 filing is **December 2024**, where
930 sits **8.0 % below** 923 — consistent in sign, smaller than the 17–20 % the
decomposition implies. 2025 cannot settle it (923 early release). **Sizing this
second discrepancy is explicitly NOT in this session's scope** and is named as a
successor item in §7.

## 4. The design — four candidates, and the recommendation

Levels each treatment hands the LP (probe §5; seam 2024-11):

| year | (A) keeper today | (B) flat refusal | (C) per-window | (D) whole-year | D−A |
|---|---:|---:|---:|---:|---:|
| 2023 | 8.7750 | 8.5469 | 8.5469 | 8.5469 | **−0.2281** |
| 2024 | 7.3942 | 6.7136 | 6.6836 | 6.7136 | **−0.6805** |
| 2025 | 5.1207 | 0.0907 | 5.1207 | 5.1207 | **0.0000** |

* **(B) flat refusal — the MISO/PJM registry switch — is INADMISSIBLE.** 2025's
  923 filing is an early release (6 of a modal 173 plants, 0.091 TWh), so a flat
  listing would replace the one year whose 930 series is *measured clean* with a
  6-plant stub. This is precisely why NEISO cannot take the PJM one-liner.
* **(C) per-window** splices 923 (Jan–Oct) to 930 (Nov–Dec) inside 2024. Given
  §3 — the two sources differ systematically — a mid-year splice injects an
  artificial step at the seam month. It differs from (D) by 0.030 TWh.
* **(D) whole-year rule — RECOMMENDED.** Refuse the pin for any year whose PS
  filing is incomplete (2019–2024); accept it for a fully-split year (2025+).
  Every year stays on **one basis**, no intra-year splice, and the seam
  measurement (§1) is what classifies the year. Zero free parameters — like the
  MISO/PJM fix it *removes* a mechanism rather than adding one.

**Forecast lane.** `forecast_monthly_hydro` averages 930 `NG: WAT` over
`HYDRO_CLIMATOLOGY_YEARS` = (2021…2025), four of whose five years are
PS-contaminated at NEISO. Under (D) NEISO takes `climatological_monthly_hydro_923`
instead: **7.0156 → 7.0020 TWh, −0.2 %**. That near-cancellation is a
**window-mismatch artifact, not a clean measure of the fold** — the 923 side
realises 2021–2024 while the 930 side realises 2021–2025, and 2025 is a
low-water year — exactly the hazard `climatological_monthly_hydro_923`'s
docstring warns about. It is reported, not relied on.

## 5. E1 — sign and magnitude, declared BEFORE any solve

Sized against the keeper's **committed** hourly sidecars (rule 15 — read, not
replayed). The pin binds essentially fully: dispatched hydro is 99.2 / 99.1 /
99.7 % of the pinned level.

| year | keeper load | keeper hydro | keeper LMP | energy removed | as % of load |
|---|---:|---:|---:|---:|---:|
| 2023 | 96.863 TWh | 8.704 TWh (9.0 %) | $39.13 | −0.228 TWh | **−0.235 %** |
| 2024 | 103.810 TWh | 7.327 TWh (7.1 %) | $43.83 | −0.681 TWh | **−0.656 %** |
| 2025 | 107.155 TWh | 5.106 TWh (4.8 %) | $71.99 | 0 | **0.000 %** |

**Direction — declared now.** The fix removes zero-marginal-cost energy in 2023
and 2024 and none in 2025. That energy must be re-served by the marginal stack,
so: **hydro dispatch falls to the corrected budget; CC_REGULAR volume rises;
load-weighted LMP rises in 2023 and 2024 and is BIT-IDENTICAL in 2025.** The
2025 no-op is itself a falsifiable prediction and the cleanest check that the
per-window logic is wired correctly.

**Magnitude.** Small. NEISO's margin is gas CC in the overwhelming majority of
hours (CC_REGULAR is 51.8 of 96.9 TWh in 2023), so displacing 0.23–0.68 TWh onto
an already-marginal class moves price only through the hours where the marginal
unit actually changes. Predicted mean-LMP rise **+0.02 to +0.20 $/MWh
(+0.05 to +0.5 %)** in 2023/2024, **exactly 0.000 in 2025**. Compare PJM's
+6.5–7.0 TWh/yr (72–79 %) and MISO's +1.1–1.5 TWh/yr: NEISO is the smallest of
the three by an order of magnitude, as the handoff expected — though, per §3,
for a different reason than the handoff gave.

**Against the keeper's scored position.** The keeper is
CALIBRATED-WITH-CAVEATS, 0 FAILs, C1 12/12 · free 8/8, C3c the ledgered sole
blocker. A −0.2 %/−0.7 % energy shift is inside the noise of every C1 band; **no
gate flip is predicted in either direction.** If one flips anyway, §6 governs.

**This prediction is a hazard, not a justification.** It is written before the
solve precisely so a favourable move cannot be read as the reason for the
change, and an unfavourable one cannot be read as a reason to revert it.

## 6. KILL/KEEP RULE — declared before any result exists

**The accurate input stays in, whatever the gates do** (rules 1 `[R-STRUCT]` /
14 `[R-ACCURATE]`). If any criterion flips to FAIL in the candidate:

1. the treatment is **NOT reverted**;
2. **no adder, haircut, uplift, reconciliation factor, or offer re-tune** is
   introduced in this session to offset it;
3. the regression is recorded in the FINDING as a **discovered root-cause
   issue**. Leading hypothesis, stated now: NEISO's offer calibration was fitted
   against a supply stack whose hydro level was the residual of two cancelling
   ~1.5 TWh errors (§3), so re-identification on the corrected stack is a
   successor charter, not this session's;
4. both arms are registered on the dashboard regardless of outcome (rule 15),
   and the matrix cell `hydro_level_923_hy` NEISO is stamped with the honest
   verdict either way (rule 26(b)).

**Kill condition for the DESIGN (not for the fix).** If the 2025 arm is **not**
bit-identical to the control, the per-window wiring is wrong — that is a **code
defect**, and the design is fixed and re-solved rather than the verdict being
recorded. This is the one outcome that sends the session back to the
implementation.

There is no outcome in which this session reverts to the contaminated level, and
none in which it tunes anything against the residual. Keeper promotion is a
**separate** decision from landing the fix and is the owner's call.

## 7. Governance boundaries

* **Charter (matrix §5.6).** NEISO's frontier is declared, so this lever needs
  an owner charter before a keeper-moving solve. **No solve has been run.** This
  document plus `_neiso72_ps_window_audit.py` are the charter's evidence.
* **Rule 22 `[R-HOLDOUT]`.** NEISO is the only calibration-complete ISO and its
  `final` tier is **SPENT and never re-grantable**. This session touches
  **2023–2025 and nothing else** — no 2022, no 2019, no H1-2026, not even as a
  diagnostic. Probe §§1–4 read 2019–2022 *raw EIA source files* for the seam
  measurement only; **no LP solve, no scoring, and no registration touches any
  out-of-training year**, which is the line rule 22 draws (data intake and
  no-LP inspection vs solve/score/register).
* **Rule 16 `[R-ALLYEARS]`.** Both arms will cover 2023, 2024, 2025 in one
  bundle each.
* **Rule 12 `[R-PARALLEL]`.** Years sequential, one fresh process per year
  (`_pjm143_chain.sh` pattern); NEISO is the smallest ISO so memory is not
  binding.
* **Rule 19 `[R-ONE-MECH]`.** Enumerated before designing: the keeper carries
  `hydro_budget_nameplate_aware=False`, `hydro_dispatch_envelope=False`,
  `hydro_min_flow_floor=False`, `hydro_ror_split=False`. The monthly level pin
  is therefore the **only** mechanism setting NEISO's hydro energy level, and
  the treatment **replaces** it in place. Nothing is stacked. (Unlike PJM, no
  companion mechanism goes inert — NEISO never armed one.)
* **Rule 23 `[R-FROZEN-DERIVE]`.** No derive script re-runs;
  `HYDRO_CLIMATOLOGY_YEARS` and the 0.50 census gate are unchanged.
* **Rule 26 `[R-MECH-MATRIX]`.** Duty (b): the `hydro_level_923_hy` NEISO cell
  moves off `U` this session with its citation, whatever the outcome — including
  a `G` (governance-refused) if the charter is declined.
* **Rule 27 `[R-PUSH]`.** Opus session; edits made locally with the Edit tool;
  every pushed file ≥300 lines blob-verified after push.

**Explicitly out of scope, named as successors:** sizing the 930-vs-923
conventional under-report (§3); `hydro_dispatch_envelope` /
`hydro_min_flow_floor`, which are built from hourly `NG: WAT` and inherit the
same pre-seam contamination (both default-off and off in this keeper, so nothing
is stacked — but arming either at NEISO needs its own source fix first, and
EIA-923 is monthly so it offers no hourly substitute).
