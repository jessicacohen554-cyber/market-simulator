# PRECOMMIT / PHASE 0 — PJM: the ST_GAS merit-order inversion

**Session** `pjm-d4-1` · **ISO** PJM · **Date** 2026-09-09 · **Branch** `claude/pjm-d4-1-qa8gwk`
**Keeper (and G-CTRL form 4 control)** `2026-09-09-pjm-fuelvintage-ep-level`
= `results/calibration/pjm_fuelvintage_A` (2023-25) + `results/calibration/pjm_fuelvintage_TP`
(2020-22 touchpoints, folded).
**Scope: PJM ONLY.** No other ISO's keeper shard, matrix shard, status part or calibration log is
touched.

> Every table below is **ZERO LP** — read off committed artifacts (`legitimacy_diagnostics.json`,
> `hourly/class_hourly_*.parquet`, `run_config.json`, `frontend/data/backcast/bench/PJM/*.json.gz`)
> or off an on-recipe `run_year(..., fleet_only=True)` rebuild through the only sanctioned
> reconstruction, `scripts/replay_keeper.run_year_kwargs` (caiso-243/244).

---

## 0. THE CONTROL POSTURE — inherited, unchanged, and pre-registered here

**G-DRIFT (rule 29(b)) is NOT RUNNABLE for PJM.** Two sessions established this independently on
2026-09-09 — pjm-177 §4 and `PRECOMMIT-pjm-fuelvintage-solve-2026-09-09.md` §(a): the previous
keeper's recorded `git_sha` `457ae04` does not resolve at HEAD and has no entry in
`docs/governance/citation-commit-map.txt` (it predates the 2026-08-16 history rewrite by one day),
and the nearest defensible surrogate base is 221 files / 187,385 insertions away — not an audit that
"costs seconds".

**Posture adopted, fixed BEFORE any solve:** G-CTRL **form 4** (the committed keeper is the control),
declared **IMPAIRED**, with the published drift bands applied — **any class move within ±0.25 %
(±2.4 % for CT_PEAKER) is NOT SEPARABLE from HEAD drift** and will be reported as such, never claimed
for or against an arm. Bands are pjm-177's own same-HEAD control measurement (every class ≤0.25 %
except CT_PEAKER −2.34 %).

---

## 1. RULE 19 `[R-ONE-MECH]` — DISCHARGED FROM THE ARTIFACT, NOT ASSUMED

D-2 rows with `class == "ST_GAS"`, both committed bundles, all six years:

**`st_netload_drag` is the ONLY mechanism forcing PJM ST_GAS in any of the six years.** There is no
other ST_GAS row in D-2, and in D-4 `st_netload_drag` is the only ST_GAS floor. Nothing stacks; there
is nothing to reconcile against.

---

## 2. STEP 1 — THE SIX-YEAR D-2 TABLE, REPRODUCED EXACTLY

| year | forced TWh | class TWh (D-2) | **share of class** | handoff |
|---|---|---|---|---|
| 2020 | 5.511 | 10.149 | **54.3 %** | 54.3 % ✓ |
| 2021 | 6.585 | 10.294 | **64.0 %** | 64.0 % ✓ |
| 2022 | 6.027 | 12.953 | **46.5 %** | 46.5 % ✓ |
| 2023 | 4.765 | 12.182 | **39.1 %** | 39.1 % ✓ |
| 2024 | 4.428 | 12.093 | **36.6 %** | 36.6 % ✓ |
| 2025 | 7.156 | 17.311 | **41.3 %** | 41.3 % ✓ |

The C8 cap is 30 % for a merchant class. **The mechanism is over the cap in all six years.**

### 2a. The class composition, model vs the committed bench (`classFull`)

| class | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|
| **ST_GAS** m/a | **1.74** | **3.15** | **2.55** | **1.52** | **1.00** | **1.29** |
| ST_GAS Δ TWh | +4.93 | +8.17 | +8.97 | +4.65 | +0.05 | +4.30 |
| **CT_PEAKER** Δ % | −1.6 % | **−32.2 %** | **−24.9 %** | **−10.6 %** | +1.5 % | +19.2 % |
| CT_PEAKER Δ TWh | −0.30 | **−6.64** | **−4.60** | −2.29 | +0.35 | +4.57 |
| **CC_REGULAR** Δ % | +3.3 % | +9.9 % | +8.4 % | +1.5 % | +1.0 % | +0.9 % |

2021: **ST_GAS +8.17 against CT_PEAKER −6.64** — near equal and opposite.
2022: **ST_GAS +8.97 against CT_PEAKER −4.60**.

### 2b. THE NUMBER THE HANDOFF DID NOT HAVE — the mandate against the METER

The handoff compared forced energy to the model's own excess. The sharper comparison is forced energy
against **what the real class actually produced**:

| year | forced TWh | **measured class TWh** | **forced ÷ MEASURED** |
|---|---|---|---|
| 2020 | 5.511 | 6.631 | **83.1 %** |
| **2021** | 6.585 | **3.792** | **173.7 %** |
| **2022** | 6.027 | 5.790 | **104.1 %** |
| 2023 | 4.765 | 8.883 | 53.6 % |
| 2024 | 4.428 | 13.107 | 33.8 % |
| 2025 | 7.156 | 14.788 | 48.4 % |

**In 2021 the floor alone mandates 74 % MORE energy than PJM's entire gas-steam fleet metered that
year; in 2022 it mandates more than 100 % of it.** A commitment floor cannot be a lower bound on a
class and simultaneously exceed the class's whole measured output. This is a LEVEL failure in the
holdout years, on top of the allocation failure below.

### 2c. 2024 IS THE CLEANEST CASE, AND IT IS WHY RULE 1 `[R-STRUCT]` GOVERNS

In 2024 ST_GAS is **dead on actual (m/a = 1.00, +0.4 %)** — and **36.6 % of it (4.428 TWh) is
forced**. The class reaches the right total by mandating a third of it. A residual-driven reading
sees nothing wrong in 2024; the mechanism is just as unfaithful there as in 2021.

---

## 3. STEP 2 — THE DECLARED WINDOW AND DRIVER, AND WHAT THE DECLARATION ACTUALLY CLAIMS

**There IS a declared window.** `scripts/legitimacy_diagnostics.py` `D4_WINDOWS` carries
`(MECH_ST_NETLOAD_DRAG, None): (0, 24)` — **h0-23, all hours**, ISO-neutral (`None` class key, no PJM
entry in `D4_WINDOWS_BY_ISO`). So this is **not** a rule-17 missing-declaration failure.

**(a) DRIVER** — RUC-style reliability commitment. `derive_pjm_st_gas_netload_drag.py`: legacy
gas-steam boilers "committed in multi-day blocks when system net-load is high … then held online at
part load through the low-price overnight trough rather than cycling". Applied as
`clip(slope·netGW + intercept, 0, cap) × pmax`, keeper coefficients
`slope 0.01029 / GW`, `intercept −0.7263`, `cap 0.39` ⇒ **zero below 70.6 GW net-load, capped at
108.5 GW**. `gas_st_drag_seasonal = false` (one pooled curve).

**(b) THE HOURS IT MAY BIND, AND WHY** — the registry comment states the justification as a **factual
claim about the class**:

> *"the CAMPD evidence base (`docs/ercot-st-gas-netload-drag-2026-06.md`) shows the gas-steam fleet
> 'committed every day and every night, never fully off' … **Unlike CT (overnight CF ≈ 0), there is no
> hour the class's own driver evidence says it is offline**, so the all-hours boiler floor … binds
> nowhere off-window **by measurement**."*

**(c) FORWARD STORY** — net-load from load forecast + VRE build; the derive is rule-23 frozen.

**The window is therefore conditional on its own evidentiary premise, and the premise is ERCOT's.**
Section 4 measures that premise in PJM.

---

## 4. STEP 3 — THE PREMISE IS FALSE FOR MOST OF PJM'S FLOORED FLEET

D-4's **per-unit conduct rider** (owner decision 2026-08-16, nyiso-140 §5) is the check that actually
tests this. It fires only where the declared window spans 24 h — precisely because the off-window test
is then **vacuous by construction** (`off = sel & ~in_window` is empty, so `offwindow_share ≡ 0.0` and
the window row always reads `pass`). It scores each floored plant over **its own binding hours**, and
it already excludes the two false-positive routes: plants carrying the benchmark's CT-only CEMS flag
(a metering artifact, rule 14) and rows with no meter at all.

**Every floored, metered ST_GAS plant-year, all six years — 58 rows:**

| | rows | floored TWh | share |
|---|---|---|---|
| **FAIL** — measured median 0.000 MW over the floor's own binding hours | **41** | **16.234** | **73.8 %** |
| pass | 17 | 5.749 | 26.2 % |

**The separation is bimodal and has no overlap.** FAILing rows carry `measured_zero_share`
**0.532 – 0.986** (median 0.724); passing rows **0.000 – 0.457**. The gap 0.457 → 0.532 is empty.
These are two distinct populations of plants, not a threshold artifact.

**Per plant, across six years:**

| verdict | plants |
|---|---|
| **FAIL every year floored** | 593 (6/6), 3138 (6/6), 3775 (6/6), 384 (4/4), 874 (3/3), 599 (1/1) |
| FAIL most years | 3131 (5/6), 3148 (5/6), 3149 (4/6) |
| pass most / all years | 1353 (6/6), 3140 (5/6), 3809 (1/1) |

**The rider is a LOWER BOUND**: it covers 21.983 of the mechanism's 34.472 TWh of six-year forced
energy (63.8 %); the remaining 12.489 TWh sits on plants the rider declines to convict for want of a
trustworthy meter.

**This is rule 17 `[R-FLOOR-WINDOW]` on its face** — *"A floor binding in hours its own driver evidence
says the class is offline is a bug by definition, whatever it does to the residual."* The floor's own
declared justification is that no such hour exists. For 41 of 58 PJM plant-years, the meter says the
majority of the floor's binding hours are exactly such hours.

### 4a. WHY OPTION (c) — "the floor is right and the CHECKER is wrong" — IS NOT AVAILABLE

The handoff's option (c) asks whether the old 12-row D-4 form was measuring this. **It was not
measuring anything.** For an all-hours window the `window` check is arithmetically incapable of
failing: `offwindow_share ≡ 0.0` by construction, in every ISO, for every mechanism. The 12-row form
emitted only those vacuous rows. The ~210-row form adds the per-unit conduct rider, which is the first
check ever applied to this mechanism's provenance in PJM. Reverting the checker would restore a
guaranteed PASS, not a measurement — and rule 17 forbids judging the floor by what its own checker
scores.

### 4b. THE DIAGNOSIS THE RECORD ALREADY NAMES

This is not a new object. `apply_gas_st_netload_drag_floor`'s own docstring (ercot-259) states the
defect class:

> *"`floor_frac` is a FLEET capacity factor, so spreading it across every plant's `pmax` asserts that
> every plant is committed at that fraction in every hour … it **over-forces the least-committed plant
> while under-forcing the workhorse**. Measured on the ERCOT keeper's own committed D-4 conduct rows,
> the plant convicted of being floored while its meter reads zero is that year's **LEAST-committed
> plant in all five scored years**."*

And pjm-177 measured the same thing in PJM, from the other side (§5 item 3, and its matrix cell):

> *"all-hours model online duty rises 65.8 % → 77.5 % against a **measured 31.4 %** … the HOURS are
> now right and **the PLANTS are still wrong**, which is `netload_drag_merit_allocation`'s object
> (**U** for PJM)."*
> *"the measured trough block has a persistent HETEROGENEOUS membership (2023 load-dec1 online:
> Brunner Island 85.2 %, New Castle 63.6 %, Shawville 58.2 %, Big Sandy 53.5 % vs **Eddystone 0.9 %**)
> while the drag commits **EVERY plant at ~83 % duty in all hours**."*

Two plants are **nameplate-only dead capacity** in 2023 — Joliet 9 (360 MW) and Yorktown (882 MW)
report `opTime > 0` with **zero** grossLoad all year, 10.1 % of the class nameplate (pjm-177 §2) — and
the pro-rata floor commits them exactly as hard as Brunner Island.

**So the rule-17 defect is not the CLOCK window. It is the PLANT allocation**, which is the same rule
17 clause (b) read at unit grain: for a boiler that is offline all year there is no hour the floor may
bind, so every hour it binds is off-window.

---

## 5. STEP 4 — THE DISCRIMINATOR: IS THERE A SECOND, PRICE-SIDE CHANNEL?

**There is a prima-facie case that there is**, and it is visible in the keeper's own registered
`offer_curve_overrides` before any fleet is built:

| class | committed | econ_low | econ_high | peak |
|---|---|---|---|---|
| **ST_GAS** | **1.000** | **1.000** | **1.000** | 3.024 |
| **CT_PEAKER** | **1.050** | **1.250** | **1.650** | 4.000 |

PJM's CT_PEAKER offers are marked **up 5 – 65 %** on every non-scarcity band through the authorized
price-tuning channel (rule 1 `[R-STRUCT]` carve-out), while ST_GAS carries **neutral 1.0** on all
three. That is a second, independent route by which steam gas can clear ahead of peakers — and it
would survive the removal of the floor entirely.

**Measured below** on the assembled `mc_base`, capacity-weighted per class, on the keeper's own
recipe. *(This section is completed before any arm is chosen; the two channels are separated first,
per the handoff's step 4.)*

---

## 6. WHAT THIS PRECOMMIT FIXES BEFORE ANY SOLVE

- **Control:** G-CTRL form 4, IMPAIRED, bands ±0.25 % / ±2.4 % CT_PEAKER (§0).
- **Rule 1 `[R-STRUCT]`:** no gate below is the target residual. C8 forced share and the D-4 conduct
  count are the mechanism's own provenance instruments, not fit measures. **A fix that makes ST_GAS
  right by making CT_PEAKER worse has moved the error, not removed it**, and will be reported as such.
- **Rule 22 / 30(c):** 2020-2022 are diagnostic touchpoints. **Nothing is tuned on them.** No 2019 or
  H1-2026 work of any kind (locked tier, `final` empty, freeze ACTIVE).
- **Rule 31 `[R-RETAIN]`:** no bundle is deleted; the promotion question goes to the owner.
