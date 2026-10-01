# RESULT (pjm-h7) — the JOINT arm is KILLED AT THE SCREEN by G-4, and the named suspect
# accounts for only **15.8 %** of what the committed band was carrying

**Session** `pjm-h7` · **ISO** PJM · **Date** 2026-09-14 · **Base** `origin/main` @ `c6c70190`
**Screen** PJM 2023, ONE arm shard at one pinned sha (`618c023e`). Parent ran no LP (rule 32
`[R-SHARD]` (a)). **No control solve was spent** — G-CTRL form 4, discharged at zero LP.
**PJM keeper `2026-09-11-pjm-d4-4-gasoutage`: CALIBRATED, 8/8, zero caveats — UNTOUCHED.**
Spec and pre-registration: `docs/PRECOMMIT-pjm-h7-gasmid-joint-2026-09-14.md`.

---

## 1. RESULT

> **The arm is structurally exact and still fails the market — and the diagnosis it was built
> to test is REFUTED AS THE PRINCIPAL CAUSE.** G-1, G-2 and G-3 PASS; **G-4 FAILS** on the same
> class that killed pjm-h6.
>
> | gate | verdict | evidence |
> |---|---|---|
> | G-1 confinement | **PASS** | 605 of 2,978 rows, bands exactly {committed, econ, peak}, six years, phase 0 |
> | G-2 identity | **PASS** | `gas_mid` → 4.58 at dev **0.0**; orthogonality **0.0** both ways, six years |
> | G-3 sign/magnitude | **PASS** | COAL_BIT **82.996**, inside the pre-registered interval (78.834, 105.152) |
> | **G-4 no load-bearing flip** | **FAIL** | **CC_REGULAR 337.382 = +11.71 TWh**, bar was ≤ 333.670 |
>
> **C1 goes 16/16 → 14/16** — the same two classes, the same direction as h6.
> **The re-centring recovers 4.162 of the 26.318 TWh h6 lost: 15.8 %.**

The remaining five years were **never spent** (rule 29 `[R-SCREEN]` clause 2): ~105 min of LP
saved, which is the outcome a STOP gate exists to produce.

## 2. THE C1 TABLE — PJM 2023, band ±8.00 TWh

Scored in the parent on a path validated against **both** committed h6 legs to < 0.001 TWh.

| class | actual | CONTROL | res | | h6 ARM | res | **h7 JOINT** | **res** | |
|---|---:|---:|---:|:--|---:|---:|---:|---:|:--|
| **CC_REGULAR** | 325.670 | 328.456 | +2.79 | PASS | 339.154 | +13.48 | **337.382** | **+11.71** | **FAIL ← G-4** |
| nuclear | — | 272.022 | −1.79 | PASS | 272.022 | −1.79 | 272.022 | −1.79 | PASS |
| **COAL_BIT** | 103.026 | 105.152 | +2.13 | PASS | 78.834 | −24.19 | **82.996** | **−20.03** | **FAIL** (target) |
| wind | 29.626 | 29.628 | +0.00 | PASS | 29.628 | +0.00 | 29.628 | +0.00 | PASS |
| CT_PEAKER | 21.663 | 20.550 | −1.11 | PASS | 26.282 | +4.62 | 25.670 | +4.01 | PASS |
| ST_GAS | 8.883 | 11.332 | +2.45 | PASS | 14.706 | +5.82 | 14.367 | +5.48 | PASS |
| solar | 8.977 | 8.976 | −0.00 | PASS | 8.976 | −0.00 | 8.976 | −0.00 | PASS |
| hydro | 8.976 | 8.903 | −0.07 | PASS | 8.903 | −0.07 | 8.903 | −0.07 | PASS |
| CC_CHP | 6.115 | 8.542 | +2.43 | PASS | 8.067 | +1.95 | 7.901 | +1.79 | PASS |
| OTHER | 4.700 | 7.225 | +2.52 | PASS | 7.225 | +2.52 | 7.225 | +2.52 | PASS |
| COAL_WC | 5.895 | 5.296 | −0.60 | PASS | 4.915 | −0.98 | 4.850 | −1.05 | PASS |
| biomass | 5.298 | 5.298 | +0.00 | PASS | 5.298 | +0.00 | 5.298 | +0.00 | PASS |
| COAL_PRB | 3.550 | 3.053 | −0.50 | PASS | 3.388 | −0.16 | 3.294 | −0.26 | PASS |
| ST_CHP | 2.198 | 0.997 | −1.20 | PASS | 1.029 | −1.17 | 1.025 | −1.17 | PASS |
| CT_CHP | 1.875 | 1.901 | +0.03 | PASS | 1.275 | −0.60 | 1.256 | −0.62 | PASS |
| oil | 0.637 | 0.001 | −0.64 | PASS | 0.001 | −0.64 | 0.001 | −0.64 | PASS |
| | | | **16/16** | | | **14/16** | | **14/16** | |

*(Reporting detail, no gate consequence: this session's bench reader resolved a different
`nuclear` actual basis than h6's table quoted, so nuclear's residual reads −1.79 here against
h6's −0.57. **Both gate-bearing actuals — COAL_BIT 103.026 and CC_REGULAR 325.670 — match h6's
published table exactly**, and nuclear PASSes on either basis.)*

**Price** (model annual mean / load-weighted; bench RT actual **28.44** / RT load-wtd 29.58):
control **28.806** / 29.436 (+0.37) · h6 arm 30.501 / 31.261 (+2.06) · **h7 joint 30.213 /
30.952 (+1.77)**. Marginally better than h6 and still five times the control's error.
**Slack and dump are exactly 0.0 in both legs** — no scarcity artifact anywhere in this result.

## 3. THE SUBSTANTIVE FINDING — the suspect is real, small, and NOT the cause

pjm-h6 measured that PJM's registered `committed` multiplier 0.548 was silently carrying
**26.318 TWh** of coal, and named the mis-grounded sigmoid centre as what it was carrying. This
screen tested that claim directly, and the claim does not survive it:

| | COAL_BIT | recovered |
|---|---:|---:|
| h6 arm (committed basis alone) | 78.834 | — |
| **h7 joint (+ `gas_mid` 3.40 → 4.58)** | **82.996** | **+4.162 TWh** |
| control / keeper | 105.152 | (26.318 needed) |

**15.8 %.** The econ/peak re-centring is a real lever pointing the right way, and it closes
roughly **one sixth** of the gap. **Five sixths of what the committed band was compensating for
is something this lane has not identified.**

**A stated hypothesis of mine was REFUTED, and it matters which way.** PRECOMMIT §5 predicted
≈ 86.3 TWh from a locally-linear read of the cap-weighted coal delta (28.4 % relief), and argued
the estimate *"may understate the relief"* because the `econ` band is where coal competes at the
margin while `committed` is infra-marginal. The measured landing is **82.996** — the econ
discount bought **less** than the cap-weighted average implied (15.8 % against 28.4 %), not
more. The marginal-band argument is not supported by this measurement and should not be carried
forward as an assumption by a successor.

## 4. WHAT THIS DOES **NOT** ADJUDICATE — read this before proposing anything

* **The rule-23 `[R-FROZEN-DERIVE]` wart STANDS, undiminished.** `gas_mid` 3.40 still matches
  **no derivation anywhere in the codebase** — not its own derive script (7.08), not the model's
  own measured delivered coal (4.58). This screen says re-centring it **does not repair the coal
  residual**; it says nothing whatever in favour of 3.40, and **3.40 is not vindicated by this
  result.** A screen that kills an arm does not certify the incumbent value.
* **`gas_mid` ALONE was never solved.** The arm is the joint form (rule 19 `[R-ONE-MECH]`, and
  G-2 leg (iv) proved the halves are arithmetically inseparable), so the verdict is on the joint
  route to the committed-band compensation, **not** on the re-centring as a standalone rule-14
  accuracy repair. That remains an open, and genuinely different, question — see §5.
* **Reverting the committed band to 0.548 is still refused** (rule 14 `[R-ACCURATE]`): burying a
  26 TWh error back inside an inaccurate input is exactly what the rule forbids.
* **No `gas_mid` was swept, and none will be.** 4.58 was fixed in the PRECOMMIT before the probe
  was written and is the only value derivable from the model's own inputs. A value chosen
  between 3.40 and 7.08 because it scores better is the fitted adder rules 1/13 forbid.

## 5. THE SUCCESSOR QUESTION, RAISED AND NOT SETTLED IN-LANE

**Should `gas_mid` go to 4.58 on rule-14 `[R-ACCURATE]` grounds ALONE — independent of the
committed band?** The accuracy case is untouched by this kill: 4.58 is derived from the model's
own measured EIA-923 receipts through the derive script's own published construction, and 3.40
is derived from nothing. Rule 14 prefers the accurate input **and** says a worse fit is a root
cause to chase, not a reason to revert.

What phase 0 says that arm would do, reported and **gating nothing** — it cuts coal, so it
**helps** the years where PJM coal is UNDER and **hurts** the years where it is OVER:

| yr | COAL_BIT residual (keeper) | ARM_G coal Δ$/MWh | direction |
|---|---:|---:|:--|
| 2020 | +22.83 | −0.2718 | hurts (already FAIL) |
| **2021** | −3.71 | **−2.5947** | **helps** |
| 2022 | +3.05 | −0.8808 | hurts |
| 2023 | +2.10 | −1.7287 | hurts |
| 2024 | −1.13 | −0.9652 | **helps** |
| **2025** | +8.40 | **−2.8809** | hurts |

That is a **mixed** picture with its largest effects on 2021 and 2025, and it is **not** this
lane's call: it needs its own charter, its own pre-registered screen year on its own footprint,
and an owner ruling — the frontier was opened for the joint arm, which is now adjudicated.

## 6. THE PROMOTION JUDGMENT (rule 31 `[R-RETAIN]`) — asked, not pre-empted

> **OWNER RULING 2026-09-16: NOT PROMOTING.** The recommendation below was accepted. Recorded
> by session pjm-h8, which also carries new evidence *for* it: measured against PJM's own
> published offers, this arm's committed-band basis lands at **1.205 / 1.294 / 1.324×** the
> measured offer level (2023/2024/2025), i.e. it overshoots PJM's own bids by 21-32 %
> (`docs/FINDING-pjm-h8-coal-minload-is-the-undisciplined-offer-surface-2026-09-16.md` §2).
> The same ruling **RE-OPENED the pjm-142 frontier** for the min-load offer basis; successor
> charter `docs/PRECOMMIT-pjm-h8-minload-measured-offer-2026-09-16.md`.
> Rule 33 `[R-SHARD-ARCHIVE]` (f)(3) now permits deleting branch `claude/pjm-h7-screen-2023`;
> pjm-h8 attempted it and **deletion was REFUSED in-session**, so the branch STANDS and §7's
> recovery command remains valid (rule 33 (f)(5): a session that cannot delete says so rather
> than reporting a cleanup it did not perform).

**RECOMMENDATION: DO NOT PROMOTE**, and the reason is narrower than h6's.

The owner's 2026-09-14 standard is *"if structural integrity improves but gates regress that
**may** still be a keeper"* — permissive, and it does not lower the bar for the structural
argument. Here the structural argument is **weaker than h6's**, not stronger: h6 at least
installed a measured basis exactly. This arm installs that same basis **plus** a second change
whose own measured contribution is **15.8 %** of the problem it was built to solve, while the
run still carries the full 20.03 / +11.71 TWh miss on the two largest classes and a price error
five times the control's. Promoting it would ship h6's residual with one sixth of a repair
attached.

**Nothing is deleted** (rule 31). The bundle is pushed and retrievable; the decision is the
owner's and this document changes nothing about that.

## 7. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e))

On `origin`, complete with the per-plant layer a registration needs (17 files incl.
`dispatch/2023_P1.parquet`, `btm.parquet`, `system.parquet`, all seven `hourly/` sidecars):

```
branch  claude/pjm-h7-screen-2023
SHA     9be0e032e8f3832779b70472ae93813d63e2229a
recover git checkout 9be0e032e8f3832779b70472ae93813d63e2229a -- \
          results/calibration/pjm_h7_screen2023_arm
```

Verified this session by `git ls-tree` (17 files) **and** by checkout + config-signature read:
`committed_band_measured_basis: true`, `gas_mid 4.58`, `floor 0.65`. A promotion from this state
costs **zero re-solves for 2023** and five further years (~90 min) for the rest of PJM's
registered span (2020-2025, rule 35 `[R-PROMOTE]` (c)). The h6 control and armed bundles remain
retrievable at `dadda81404cb36b5dff338c6660e224e083b7209`.

## 8. WHAT WAS SPENT, AND WHAT WAS NOT

* **ONE LP** — PJM 2023, one arm leg. **No control solve**: G-DRIFT found exactly two solve-path
  commits since the h6 control and both classify INERT for PJM **by measurement** (a new module
  with zero importers; a refactor whose `.isin(codes)` is identical to `== code` because
  `ba_codes("PJM") == ("PJM",)`, plus an eGRID repair plant PJM's fleet carries 0 rows for).
  h6 spent ~18 min of control LP on this same question; this lane spent seconds.
* **The six-year span was NOT spent** (~105 min saved).
* **Two silent-failure traps were caught at zero LP before the shard ran**: `gas_mid` routes
  through the `prb_overrides` channel only (the ERCOT-65 re-stomp class — both arming forms were
  verified to resolve to 4.58, and the shard wrote both), and the `.gitignore` negation needed to
  re-include `dispatch/` was tested rather than assumed.
* **Nothing registered, no keeper touched, nothing deleted.** The screen bundle is a throwaway
  probe (rule 29 clause 2) and every number this lane cites is in this document.

## 9. MATRIX (rule 28 `[R-MECH-MATRIX]` (b))

`coal_passthrough_sigmoids` PJM cell stays **K** (the family is armed on the keeper and
unchanged) with a second sub-parameter now adjudicated: the bituminous **`gas_mid`
re-centring, in its JOINT form with `committed_band_measured_basis`, is R**, this document the
citation. `floor` and `gas_slope` remain OPEN; `gas_mid` as a **standalone rule-14 accuracy
repair** is explicitly **NOT** adjudicated (§4, §5). `committed_band_measured_basis` stays **R**.

## 10. RULES

Rule 1 `[R-STRUCT]` (the gate was structural, STOP-only, fixed before the solve and never read
on the target residual — and it killed the arm on a non-target class) · rule 13 `[R-MEASURED]`
· rule 14 `[R-ACCURATE]` (§4 — the kill does not license reverting the committed band, and does
not vindicate 3.40) · rule 19 `[R-ONE-MECH]` (the halves were screened as one because G-2 proved
them inseparable) · rule 21 `[R-DOF]` (zero free parameters; one derived operand; nothing swept)
· rule 23 `[R-FROZEN-DERIVE]` (§4 — the wart stands) · rule 29 `[R-SCREEN]` (clause 0 phase 0;
screen year on footprint; clause (b) G-DRIFT at zero LP; the remaining years were never spent)
· rule 30(c) (no held-out year touches PJM's determination) · rule 31 `[R-RETAIN]` (nothing
deleted; the promotion question is put to the owner) · rule 32 `[R-SHARD]` (a) (the parent ran
no LP) · rule 33 `[R-SHARD-ARCHIVE]` (fetched, checked out, verified, then archived; recovery by
full SHA) · rule 34 `[R-SHARD-PROMOTABLE]` (the shard pushed its bundle with the per-plant layer).
