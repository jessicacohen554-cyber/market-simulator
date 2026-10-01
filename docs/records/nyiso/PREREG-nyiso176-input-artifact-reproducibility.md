# PREREG — nyiso-176: the NYISO input-artifact reproducibility gap

**Committed BEFORE the probe is run, and before any measurement of either
object.** Ninth consecutive NYISO session to pre-register. Phase 0, **zero
solve** unless a gate below explicitly authorises one.

Keeper `2026-08-30-nyiso-159-loss-surface`, determination **NOT-YET** on
{C3a-2025 −11.5 %, C3c}. **No C3c lever is opened.** No parameter, band, floor
or offer change is proposed. Years read: **2023 / 2024 / 2025 only** for any
solve-relevant statistic; the outage extract's own year span is an *object of
study*, not a spend (no year outside 2023–2025 is solved, scored or registered —
rule 22 `[R-HOLDOUT]`).

## 0. The object

nyiso-175b §4 established that **both** NYISO solve inputs differ from a fresh
HEAD derivation:

| artifact | committed | fresh HEAD (nyiso-175b) | reported delta |
|---|---|---|---|
| `thermal_tranches_NYISO.csv` | 78 rows | 79 rows | **46 of 78 rows differ**; `online_hours` to 26,271 |
| `campd-unit-outages-NYISO.csv` | 4,423 windows | 2,632 windows | **−40 %** |

This session's object is **the attribution of that delta**, and the
**re-baseline decision** that follows from it. It is not the per-unit repair,
which nyiso-175b already built and validated.

## 1. Gates

### R1 — the outage extract's span hypothesis

`derive_campd_unit_outages.py`'s `--years` default is `[2023, 2024, 2025]`
(line 1053). The committed extract's `outage_start` spans **2018–2026**.

**HYPOTHESIS R1:** the reported −40 % is an **invocation-span artifact** — a
3-year derivation compared against a 9-year committed artifact — not code or
data drift.

**TEST:** re-derive at HEAD with the committed artifact's own span
(`--years 2018 2019 2020 2021 2022 2023 2024 2025 2026`) and compare to the
committed bytes.

* **R1 PASSES** iff total windows are within **5 %** of 4,423 **and** every
  calendar year's window count is within **10 %** of the committed year count.
* **R1 FAILS** otherwise, and the residual is a genuine defect to attribute
  under R2.

**Stated in advance, both directions.** A PASS **withdraws** nyiso-175b §4.1's
"−40 % drift from nothing but re-running the deriver" as a comparison artifact
and makes the outage half of the blocker disappear. A FAIL leaves a real, sized
object. Neither outcome is preferred; the measurement decides.

### R2 — residual attribution on the outage extract

Whatever R1 leaves unexplained is decomposed **per plant and per unit**, and the
largest contributors are named with their window counts. No threshold; this is a
reporting duty, not a gate. It is discharged even if R1 passes (the residual may
be small but non-zero).

### R3 — channel ablation on the tranche artifact

Both legs already sit at HEAD over the **same 3-year span** (committed
`online_hours` max 26,253, S-0 control max 26,271 — both consistent with
2023–2025), so the tranche delta is **not** a span artifact and must be
attributed to a mechanism. Four named channels, in nyiso-175b's own ranked
order:

| id | channel | ablation |
|---|---|---|
| **A** | the unit-outage derate overlay (`avail_cap = nameplate × avail_mult`) | `unit_outage_derate_factors` → `{}` (multiplier ≡ 1) |
| **B** | parasitic net/gross factors | `_parasitic_factor_map` → `{}` |
| **C** | HEAD fleet nameplate reconciliation | direct `nameplate_mw` comparison |
| **D** | CAMPD source-data revision | the residual |

**METRIC, fixed here:** `n_match` = the number of the **78 common rows** whose
`online_hours` agrees with the committed artifact to within **24 hours**. The
S-0 control's `n_match` is the baseline.

* A channel is **DECLARED THE DOMINANT CAUSE** iff ablating it raises `n_match`
  to **≥ 60 of 78** (i.e. it explains ≥ 60 % of the differing rows).
* If no single ablation reaches 60, the drift is **DECLARED MULTI-CHANNEL** and
  the best-performing ablation is reported at its measured strength, with no
  dominant cause claimed.

### R4 — the S A Carlson (2682) forensic

The most extreme single case: committed `ST_GAS` **3,913** online hours /
`median_cf` 84.4 against S-0's **120** hours / `median_cf` **150.0** (the
`np.clip(acf, 0, 1.5)` cap — a physically meaningless value, so *something* has
driven `avail_cap` to near zero).

**PRE-REGISTERED EXPECTATION:** channel **A**. `avail_cap = nameplate ×
avail_mult` enters the online test `series > _ONLINE_FRAC × avail_cap` **and**
the `finite` mask via `avail_cap > 0`, so a full derate deletes hours outright.

* **R4 PASSES** iff ablation **A** alone restores plant 2682's `ST_GAS`
  `online_hours` to within **10 %** of 3,913.
* **R4 FAILS** otherwise, and the expectation is reported as refuted at full
  strength.

### R5 — THE RE-BASELINE DECISION RULE

**Pre-registered here, before any drift measurement and before any score of any
kind is consulted.** The branch is chosen on the *attribution* alone.

* **R5-(i)** — R3 names a dominant channel **and** HEAD's behaviour on that
  channel is a **defect** (HEAD is wrong): **repair the defect, re-derive only
  that, and land the nyiso-175b per-unit repair on top as a clean single
  delta.** This is the brief's route (b).
* **R5-(ii)** — R3 names a dominant channel **and** HEAD's behaviour is the
  **more accurate** input (the committed artifact predates a correct wiring):
  **re-baseline the keeper's input to the fresh HEAD derivation.** Rule 14
  `[R-ACCURATE]` binds: the accurate input is kept, and a worse backcast after
  it is a discovered bug elsewhere, **never** a reason to revert. Route (a).
* **R5-(iii)** — R3 declares MULTI-CHANNEL (irreducible accumulation):
  **re-baseline wholesale**, route (a), with the drift documented row-by-row so
  the import is adjudicated rather than silent.
* **R5-(iv)** — the drift turns out to be an **invocation artifact** on both
  artifacts (R1 passes and the tranche legs are reconciled by a matching
  invocation): the artifacts are **REPRODUCIBLE**, the blocker is **withdrawn**,
  and the per-unit repair's A/B needs no control leg.

**In every branch no score is consulted in choosing the branch.** This clause is
the point of pre-registering.

### R6 — K5, carried forward verbatim from nyiso-175b

A **large favourable C3a-2025 move** attributed to the per-unit repair **FAILS**
the gate. Both East River bins carry heat rate 7.4205 and the same delivered
gas, so moving energy between them changes no unit's marginal cost and no
marginal price; the expectation is **~zero**. Carried, not re-derived.

## 2. Stop conditions

* **S1** — if adjudicating the drift requires **solve-side** evidence, the
  session **STOPS at phase 0** and hands the object forward. A speculative solve
  to "see what happens" is not run.
* **S2** — **no lever is opened**: no parameter, band, floor, offer or
  `ScenarioConfig` default changes as a result of a drift measurement. Wiring
  work (a resolver + a rule-24 registry field) is permitted only if R5 selects a
  branch that needs it, and only default-off.
* **S3** — **no C3c lever**, per the brief.
* **S4** — rule 25 `[R-ISO-SCOPE]`: **only NYISO artifacts are derived.** Every
  other ISO's committed tranche and outage CSVs stay byte-untouched. If the
  drift is found to be ISO-agnostic that is *recorded*, never acted on here.
* **S5** — rule 23 `[R-FROZEN-DERIVE]`: any re-derivation commit cites the
  **defect or data change** that justifies it, never a residual. If the only
  argument for a re-baseline turns out to be "it fits better", the re-baseline
  is **refused**.

## 3. What this session will NOT claim

The per-unit repair's C3a-2025 expectation is **~zero** and will not be sold
otherwise. The **re-baseline** has **no pre-registered sign** — it may move
scores either way, and under rule 14 a worse backcast after a more accurate
input is a discovered bug elsewhere.
