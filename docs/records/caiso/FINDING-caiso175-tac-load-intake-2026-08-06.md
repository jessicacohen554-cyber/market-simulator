# FINDING — caiso-175: the CAISO TAC load-series intake

**MWD-TAC is closed, and the 2023 series was covering 744 of 8,760 hours.**
Both corrections are rule 14 `[R-ACCURATE]` demand inputs with **zero free parameters**.
Keeper **PROMOTED** `2026-08-05-caiso-174-measured-fleet` → **`2026-08-06-caiso-175-tac-intake`**.

**Runs:** both arms registered (rule 15). Determination **CALIBRATED-WITH-CAVEATS**, **0 FAILs**,
same 2 ledgered caveats (C3a, C3c), D-10 12/12 · free 8/8. Solved **2023/2024/2025 in one bundle
per arm** (rule 16); arms **sequential** (rule 12). `holdout-freeze.json` **UNTOUCHED** (owner act);
`calibration-complete.json` re-keyed **only** as rule 22 D-5(b) requires on promotion.
Pre-registration: `PRECHECK-caiso175-tac-load-intake-2026-08-05.md`.

---

## 0. Headline

Three things, in the order they were found.

1. **C7 and C8 were unscored on every CAISO keeper.** No CAISO bundle carried
   `legitimacy_diagnostics.json`, so the two PROTECTIVE criteria scored `SKIPPED`. Closed here
   with **no LP** — rule 21 makes this scorer-only — for both new arms **and** retro-fitted to the
   superseded caiso-174 bundle. Both **PASS**. The scored surface is now **9 criteria, not 7**.
2. **`MWD-TAC` was hard-coded out of the intake.** The sixth CAISO-internal `SLD_FCST` area never
   reached the committed series. Closed — this is the dedicated session caiso-173 §C asked for.
3. **The committed 2023 TAC series covered 744 of 8,760 hours** — January only — so **91.5 % of a
   scored calibration year ran on a flat January-average zonal split.** Not previously on the
   record. Closed.

**On price the intake is close to a measured null, and the control is what proves it.** Incidental
code drift between the keeper's head and this one is **larger in every year** than the treatment.

---

## 1. C7/C8 — the gap the `complete` grant recorded against interest

The CAISO `complete` entry said, of its own keeper:

> C7/C8 are **unscored-protective** on caiso-174 because its bundle carries no
> `legitimacy_diagnostics.json` … a scorer-only gap under rule 21, deliberately not repaired in
> this committed-artifacts-only lane.

`scripts/calibration_verdict.py` names the fix in its own output, and rule 21 sanctions it as
scorer-only: *"no re-solve, no bundle regen, and existing keepers re-score in place."* Generated
and committed. **C7 PASS, C8 PASS**, determination unchanged.

### 1a. Recorded against interest — the raw diagnostic says FAIL and the rubric says PASS

D-1 fails `ST_GAS` on profile correlation, in both new arms and in the incumbent:

| bundle | 2024 ST_GAS r | 2025 ST_GAS r |
|---|---:|---:|
| caiso-174 (incumbent) | 0.117 | −0.039 |
| caiso-175 A (control) | 0.119 | −0.020 |
| caiso-175 B (keeper) | 0.114 | −0.021 |

**These rows are real and are not being dismissed.** They do not raise a C7 FAIL because
`score_shape` applies rule 21's materiality screen — the gate binds only on classes ≥ 2 % of ISO
load — and CAISO `ST_GAS` is **0.6 / 0.4 / 0.1 %**. That is the rubric's own pre-existing constant
(`PROTECTIVE_MIN_LOAD_FRAC = 0.02`, owner amendment 2026-07-06), **not a threshold chosen by this
session**, and rule 21 states the consequence: *"smaller classes are reported by the D-1/D-2
diagnostics but never gated — trivial-class shape/forcing is not worth structural work."*

**No scorer constant was touched.** Filed for a future session, not repaired here: `run_d1`'s own
`gated` column screens on the class list alone, while `score_shape` screens on class list **and**
load share. The machine artifact therefore reads `Overall: FAIL` where the rubric reads PASS. That
is a reporting inconsistency in the diagnostic, and repairing it inside a session whose keeper
depends on the answer would be the wrong session to do it in.

---

## 2. What was wrong with the input

### 2a. MWD-TAC — a whole TAC area, absent

The live OASIS `SLD_FCST` domain carries **six** CAISO-internal areas. `CAISO_TACS` in
`scripts/data/postprocess_oasis_downloads.py` listed **five**. Because
`load_zonal_shares` **normalises the component TACs to 1.0**, this was *not missing load*: MWD's
load was silently re-apportioned **pro rata** across the other four, misplacing part of it north of
Path 15.

Measured MWD load: **119.1 / 171.6 / 144.1 MW** (2023/2024/2025).

**The zone assignment is structural, not fitted.** MWD's CAISO-metered load is the Colorado River
Aqueduct pumping chain (Whitsett Intake, Gene, Iron Mountain, Eagle Mountain, Hinds) in eastern
Riverside/San Bernardino County. The CAISO LCT study's own local-area taxonomy carries that
corridor as **`Blythe` / `Parker`** — distinct from both `LA Basin` and `San Diego/Imperial
Valley` — and `SP15_rest` is defined in `iso_configs` as exactly that SP26 residual. So
`MWD-TAC → {SP15_rest: 1.0}` is a **1:1 area containment**, not a split with a tunable weight.

**The measured shape corroborates the identification rather than assuming it:**

| area | hour-of-day CV | summer/winter |
|---|---:|---:|
| **MWD-TAC** | **0.005** | **1.50** |
| SCE-TAC | 0.115 | 1.34 |
| SDGE-TAC | 0.124 | 1.10 |
| VEA-TAC | 0.128 | 1.38 |

A flat industrial pumping block on water-delivery seasonality — not a retail diurnal shape.

### 2b. The 2023 coverage hole — found while doing 2a

`CAISO_tac_load_hourly_2023.csv` spanned **2023-01-01 → 2023-02-01 only**: 3,720 rows, 744 distinct
hours, against 43,915 rows / 8,783 hours for 2024. The loader had been announcing this in every
2023 CAISO run:

```
CAISO TAC-area load for 2023 covers 744/8760 hours; uncovered hours use the sample-average zone shares
```

So **8,016 of 8,760 hours took a flat January-average share** — no diurnal shape, no seasonal
shape, for eleven months of a scored calibration year. Visible in the input as dispersion: NP15's
hourly-share sd was **0.00374** in 2023 against **0.02615 / 0.03088** in 2024/2025.

### 2c. Why it could never have been back-filled by re-running the fetcher

`fetch_caiso_oasis.py`'s coverage check keys on **one reference series** (`CA ISO-TAC` for the load
report). Once an aggregate exists it reports every day covered — even for a series that was never
kept — so **widening the kept set could not back-fill**. Added `--force` for exactly this case, and
documented it as "use when the KEPT SET widens, not to re-pull data already on disk." Without it
this intake is not reachable at all, which is the structural reason MWD stayed missing after being
identified.

---

## 3. The quantity gate — run BEFORE any price was read

**(a) The re-fetch is byte-faithful on everything it did not add.** Every pre-existing
(timestamp, area) row reproduces to **max |Δ| = 0.000000 MW**, **0 rows differing**, **0 overlap
rows missing**, in all three years. The intake *adds*; it never *rewrites*.

**(b) The arms' `scenario_config` is IDENTICAL across all 692 keys** — verified fail-closed by
`scripts/gen_caiso175_attestation.py`. This session's delta is a data file plus a `constants.py`
table, so *any* config difference would have meant the arms were not comparable. (The caiso-172
predicate, not the caiso-174 one.)

**(c) The correction reached the LP — checked on each bundle's OWN solved output**, never on the
current on-disk CSV. That distinction matters: the CSV is a single mutable file that both arms
cannot simultaneously evidence, so re-deriving it post-hoc would attest to whichever state happened
to be staged last. Two independent legs, both fail-closed:

* SP15_rest demand share gain **+0.00647 / +0.00616 / +0.00514** (MWD landed in-zone);
* 2023 NP15 hourly-share sd **0.00374 → 0.01998 (5.3×)** (the flat regime is gone).

**(d) DOF ledger UNCHANGED** at `n_entries` 11 / `n_residual` 8. An intake that adds a measured
area and completes a measured year introduces no free parameter; the generator refuses to write if
either count moves.

---

## 4. caiso-173 §C is confirmed ON DATA, not re-asserted

§C predicted the MWD omission misplaced **0.241 / 0.297 / 0.243 %** of ISO load north of Path 15.
The realised NP15 demand-share deltas, in the years where MWD is the *only* change:

| year | caiso-173 §C predicted | realised | note |
|---|---:|---:|---|
| 2024 | −0.297 pp | **−0.262 pp** | MWD alone |
| 2025 | −0.243 pp | **−0.215 pp** | MWD alone |
| 2023 | −0.241 pp | **−1.123 pp** | MWD **+ coverage** |

§C's estimate runs ~12 % high in the MWD-only years — it was computed against the **January-window**
MWD mean, which is higher than the annual one. **2023's −1.123 pp is not MWD**; it is the coverage
leg, and it is nearly five times larger than the defect §C described.

**What the January sample was doing to 2023:** NP15 **−1.123 pp**, LA_BASIN **+1.239 pp**. Using
January year-round systematically over-weighted the winter-heavy north and under-weighted the
summer-peaking LA Basin, in every hour of the other eleven months.

---

## 5. GATED — the determination (PRECHECK §2)

| bundle | determination | FAILs | scored | skipped | DOF |
|---|---|---:|---:|---:|---|
| keeper (caiso-174) | CALIBRATED-WITH-CAVEATS | 0 | 7 → **9** | 2 → **0** | 11/8 |
| **A** control | CALIBRATED-WITH-CAVEATS | 0 | 9 | 0 | 11/8 |
| **B** treated | CALIBRATED-WITH-CAVEATS | 0 | 9 | 0 | 11/8 |

**The pre-registered rule fired as written.** PRECHECK §2 fixed, before any number was read, that
determination-holds + no-new-FAIL + no-new-caveat ⇒ **PROMOTE**. It also fixed the row that
actually binds: a *degraded* criterion would **not** revert the input, because rule 14 makes a
worse fit on accurate data a **discovered bug**, not grounds to restore the estimate. The first
branch fired.

---

## 6. REPORTED, NEVER GATED

### 6a. C3a — the control earned its keep, decisively

Load-weighted mean LMP ($/MWh):

| year | keeper | A | B | **A − keeper (drift)** | **B − A (intake)** |
|---|---:|---:|---:|---:|---:|
| 2023 | 56.161 | 56.330 | 56.448 | **+0.168** | **+0.118** (+0.21 %) |
| 2024 | 38.587 | 38.635 | 38.631 | **+0.049** | **−0.004** (−0.01 %) |
| 2025 | 39.346 | 39.460 | 39.462 | **+0.115** | **+0.002** (+0.00 %) |

**Incidental code drift is larger than the treatment in every year.** Without Arm A, 2023's
`B − keeper` of +0.287 would have been read as the intake when **most of it is drift** between head
`ae7658d0` and this one. This is the caiso-174 lesson repeating, and it is why a fresh control was
solved rather than differencing against the keeper's committed metrics.

**MWD alone is a measured null on ISO mean price** (2024/2025: ≤0.01 %). The 2023 movement is the
coverage leg.

### 6b. Intra-ISO, 2023 moves even though the ISO mean barely does

Zonal mean price, B − A ($/MWh):

| year | NP15 | ZP26 | LA_BASIN | SDGE | SP15_rest |
|---|---:|---:|---:|---:|---:|
| 2023 | −0.187 | −0.158 | +0.418 | **−0.860** | +0.418 |
| 2024 | −0.056 | −0.043 | +0.036 | −0.005 | +0.036 |
| 2025 | −0.038 | −0.030 | +0.035 | −0.014 | +0.034 |

Class energy, B − A (TWh): 2023 CC_REGULAR **−0.367**, CT_PEAKER **+0.151**, ST_GAS **+0.149**.
2024/2025 are an order smaller. Restoring eleven months of zonal shape re-dispatches real energy
even where it nets out at the ISO mean.

### 6c. KNOWN-OPEN 1 moves slightly AWAY from measured — and the input stays

NP15−ZP26 annual-mean basis ($/MWh):

| year | measured | A | B | A % of measured | B % of measured |
|---|---:|---:|---:|---:|---:|
| 2023 | 5.947 | 0.336 | 0.307 | 5.7 % | **5.2 %** |
| 2024 | 8.576 | 0.216 | 0.203 | 2.5 % | **2.4 %** |
| 2025 | 5.727 | 0.174 | 0.166 | 3.0 % | **2.9 %** |

**The direction is physically obligatory:** moving load south of Path 15 needs less N→S transfer,
hence less congestion. **The corrected input stays regardless** — rule 1 `[R-STRUCT]` forbids
reverting a correct measured input because a residual did not move the way we wanted, and rule 14
makes this a root-cause signal rather than a reason to restore a truncated series. The congestion
majority (80–87 % of the measured basis) remains unrepresented and **no N–S topology lever is
chartered off this** (caiso-164 §0/§6 stands).

---

## 7. Governance

* **Rule 22 D-5(b) re-keying performed.** CAISO holds a `complete` marker, so
  `calibration-complete.json`'s `keeper` was re-keyed and its `determination` **re-verified from
  committed artifacts only** (`--run-id`, never a solve) before the promotion landed. The
  re-verified determination is **not worse** — same determination, same caveats, same 0 FAILs, and
  two more criteria scored — so the escalation branch did not fire. `keeper_at_declaration`
  preserved; a `rekey_log` entry records the transition.
* **Rule 22 holdout.** 2023/2024/2025 only. The spend freeze is **ACTIVE** and outranks the marker;
  every out-of-training year stays quarantined. `holdout-freeze.json` untouched.
* **Rule 22 LOYO.** This session fits nothing and moves no free parameter, so LOYO reduces to the
  no-held-out-degradation check: no criterion flips in any year, and the two MWD-only years
  (2024/2025) are the independent check that the 2023 result is not carried by a single year.
* **Rule 24 `[R-REGISTRY]`.** No env-var knob, no per-plant dict, no `getattr` fallback. The one new
  CLI flag (`--force`) is a fetch-tooling flag that cannot change a solve.
* **Standing walls unchanged.** C3a needs non-public hourly pumped-storage data (caiso-141 A2);
  C3c needs the SoCalGas OFO declaration record. Neither is touched by a demand-input intake and
  neither in-model lever queue is re-opened.

---

## 8. Open, named, not buried

1. **The D-1 / `score_shape` gating inconsistency** (§1a) — `run_d1` screens on class list only;
   the rubric screens on class list **and** load share. A future session should align the
   diagnostic's own `gated` column with the rubric it feeds, so the artifact stops reading
   `Overall: FAIL` where the keeper scorer reads PASS.
2. **CAISO `ST_GAS` diurnal shape is genuinely poor** (r ≈ 0.11 / −0.02). Rule 21 says a
   0.1–0.6 %-of-load class is not worth structural work, and this session obeyed that. It is
   recorded so the next material-class shape review does not rediscover it as new.
3. **KNOWN-OPEN 1** stays wide open (§6c); **KNOWN-OPEN 2** is untouched.
4. **Other ISOs' TAC/zonal load series have not been audited for the same coverage defect.** The
   2023 hole was invisible because the loader's warning scrolled past in every run. Worth one
   no-LP sweep across the five other ISOs.
