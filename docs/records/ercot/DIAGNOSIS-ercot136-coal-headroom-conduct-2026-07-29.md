# DIAGNOSIS — ERCOT-136: the unoffered coal headroom is NONE of the three — it is OFFERED, economically, at $8–25/MWh. The model's $4.50 take-or-pay tranche is REFUTED as faithful, and a coal offer-SHAPE correction is licensed for the first time

**Date** 2026-07-29 · **ISO** ERCOT · **Lane** ercot136-coal-headroom-conduct ·
**Keeper** `2026-07-28-ercot116-regate-base` (bundle
`results/calibration/ercot116_regate_base`) — **unchanged by this document** ·
**Method** Phase 1 — **no LP, no solve, no registered run.** Every measured
number is read from the 60-Day SCED disclosure on ERCOT-123's own loader and
conventions (imported, not re-implemented); every model number is read from the
**committed** ERCOT-135 artifact. Default `ScenarioConfig().cache_key()` verified
`603c2498bf71d21d` at session start and end. ·
**Reproduction** `scripts/probes/ercot136_coal_headroom_conduct.py` (committed
with this document); artifact
`results/calibration/ercot136_coal_headroom_conduct.json`.

---

## 0. The result in one line, and the branch that fired

The charter offered three branches — **self-scheduled**, **withheld**,
**telemetered down**. **None of them fires.** The unoffered-in-DAM coal headroom
is **offered in real time, economically, at $8–25/MWh**: the price-taking bucket
is **0.0000–0.0029** of coal capability, the genuinely-unoffered residual is
**0.0001**, and the derate layer is *smaller* than the CC control's. So the
charter's branch-(a) premise — *"if it is SELF-SCHEDULED the model's $4.50
take-or-pay tranche is STRUCTURALLY FAITHFUL"* — is **refuted by its own
antecedent**, and the contrapositive is what this session delivers:

> The real ERCOT coal fleet offers **5.8–8.4 %** of its telemetered capability at
> or below **$4.50/MWh**. The model offers **30 %** there. That is a **3.6–5.2×**
> over-offering of cheap coal, and it is the first measured refutation of the
> model's take-or-pay band on the instrument that actually governs dispatch.

**This licenses a correction — the first this lane has produced.** §7 states its
exact scope, §8 states why it is still not solved here, and
`docs/PRECOMMIT-ercot136-coal-minload-reprice-2026-07-29.md` pre-registers it.

## 1. Prior art — ERCOT-123 already closed the three-way fork, and this session says so

**The ERCOT-136 charter does not cite `DIAGNOSIS-ercot123` (2026-07-27), which
ran this exact instrument and settled the exact fork.** That is recorded here
rather than quietly worked around, because it changes what this lane is for.
ERCOT-123 measured coal's RT-dispatchable headroom (`HASL − LSL`) as
**0.9945–0.9998 offered**, **0.0001–0.0002 residual**, **0.000–0.005
price-taking**, and concluded the DAM non-submission is *QSE self-supply
bypassing DAM transaction*.

Section A of this probe **runs ERCOT-123's `section_a` unchanged**, and it
reproduces that table to the last digit:

| year | family | class | (a) offered | (b) self-sched | (e) residual | curve share |
|---|---|---|---|---|---|---|
| 2024 | tail | **COAL** | 0.9945 | 0.0054 | 0.0001 | 0.9969 |
| 2024 | control | **COAL** | 0.9998 | 0.0000 | 0.0002 | 1.0000 |
| 2025 | control | **COAL** | 0.9979 | 0.0019 | 0.0002 | 0.9963 |
| 2025 | tail | **COAL** | 0.9964 | 0.0035 | 0.0001 | 0.9876 |
| 2024 | tail | CC | 0.9570 | 0.0351 | 0.0079 | 0.9518 |
| 2025 | tail | CC | 0.9852 | 0.0083 | 0.0065 | 0.9798 |

The DAM-side control the charter asked to reuse verbatim is on the same footing:
ERCOT-122 §4's CC **0.594–0.677** offered (coal 0.161–0.184), reproduced by
ERCOT-123 §6(ii) on these very probe days at CC 0.5970/0.6713 against full-year
0.5941/0.6775 — deltas ≤0.010. **The DAM↔RT contrast is the whole finding: the
same capacity that submits nothing in the DAM submits a full three-part offer in
SCED.**

**What ERCOT-123 could NOT see, and this session measures.** Its decomposition
runs over `HASL − LSL` and its supply curve is floored at `LSL`
(`supply(−inf) = LSL`), so the **min-load block is excluded by construction** —
its own §4 says so in terms. Its price grid is `(0, 20, 25, 40, 100, 500)`, so
the whole **$0–20 region is one lump**. The model's cheap band is *inside* that
lump and *below* that floor. **The ERCOT-135 question was therefore untouched by
ERCOT-123**, and it is exactly what §§3–5 resolve.

## 2. The full-range classification — min-load made visible

The same capability re-cut over the **whole telemetered range `HSL`**, so the
min-load block is a named share instead of a divided-out denominator (shares of
`HSL`, capacity-weighted):

| year | family | class | min-load | offered | self-sched | AS-held | residual | `Output Schedule > 0` |
|---|---|---|---|---|---|---|---|---|
| 2024 | tail | **COAL** | 0.4514 | 0.5348 | **0.0029** | 0.0108 | **0.0001** | 0.9993 |
| 2024 | control | **COAL** | 0.4246 | 0.5636 | **0.0000** | 0.0117 | **0.0001** | 0.9977 |
| 2025 | control | **COAL** | 0.4506 | 0.5384 | **0.0010** | 0.0099 | **0.0001** | 1.0000 |
| 2025 | tail | **COAL** | 0.4569 | 0.5312 | **0.0019** | 0.0100 | **0.0001** | 1.0000 |
| 2024 | tail | CC | 0.5934 | 0.3832 | 0.0141 | 0.0062 | 0.0032 | 0.9895 |
| 2025 | tail | CC | 0.5788 | 0.4117 | 0.0035 | 0.0034 | 0.0027 | 0.9948 |

**The `Output Schedule` column is the charter's named instrument, and it is a
trap.** A non-zero output schedule is present in **99.8–100.0 %** of online coal
resource-intervals — which, read naively, says "essentially all coal is
self-scheduled". It does not. The same intervals carry a **full submitted TPO
curve** (98.8–100.0 %), and the schedule sits *inside* the curve's reach: the MW
scheduled **above** what the curve offers is **0.0000–0.0029** of capability.
An ERCOT output schedule for a resource that also submits an energy offer curve
is the QSE's intended operating point, **not** a price-taking must-take — SCED
optimises against the curve. Classifying on `Output Schedule > 0` alone would
have produced exactly the wrong answer, and is why §3, not §2, is decisive.

## 3. THE DECISIVE MEASUREMENT — the bottom of the real fleet's RT curve

`Submitted TPO-Price1` is the price of the fleet's **first and cheapest offered
MW**. It is the direct counterpart of ERCOT-135 §1's *"model bid p10 / p25 =
4.50 / 4.50"*, capacity-weighted on the same convention:

| year | family | class | p10 | p25 | **p50** | p75 | p90 | **MW ≤ \$4.50** | `TPO-MW1 / LSL` p50 |
|---|---|---|---|---|---|---|---|---|---|
| 2024 | tail | **COAL** | 7.00 | 12.97 | **16.86** | 21.60 | 27.55 | **0.0721** | 0.96 |
| 2024 | control | **COAL** | 8.19 | 13.00 | **16.37** | 21.38 | 25.00 | **0.0689** | 0.96 |
| 2025 | control | **COAL** | 8.19 | 10.32 | **15.00** | 21.35 | 23.41 | **0.0868** | 0.76 |
| 2025 | tail | **COAL** | 2.65 | 10.63 | **15.00** | 21.42 | 23.59 | **0.1000** | 0.72 |

`TPO-MW1 / LSL` ≈ 0.72–0.96 says the submitted curve **starts at or just below
min load** — so the fleet's first offered MW *is* the min-load block, and the
price above is the price it attaches to it. **No coal resource anchors its curve
at anything like $4.50.**

The supply grid, sub-$20 resolved, on two denominators (COAL, share of the
denominator):

| year·family | conv | ≤0 | ≤2 | **≤4.5** | ≤10 | ≤15 | ≤20 | ≤25 | ≤500 |
|---|---|---|---|---|---|---|---|---|---|
| 2024 tail | floored | 0.4565 | 0.4565 | 0.4801 | 0.5166 | 0.5397 | **0.7049** | **0.9163** | 0.9970 |
| 2024 tail | **unfloored** | 0.0100 | 0.0104 | **0.0638** | 0.1746 | 0.2389 | 0.5189 | 0.8704 | 0.9947 |
| 2024 control | floored | 0.4297 | 0.4297 | 0.4483 | 0.4875 | 0.5070 | **0.6726** | **0.9197** | 0.9999 |
| 2024 control | **unfloored** | 0.0134 | 0.0143 | **0.0579** | 0.1702 | 0.2362 | 0.5191 | 0.8781 | 0.9999 |
| 2025 control | floored | 0.4551 | 0.4580 | 0.4736 | 0.5105 | 0.5692 | **0.6569** | **0.9192** | 0.9988 |
| 2025 control | **unfloored** | 0.0163 | 0.0307 | **0.0710** | 0.1916 | 0.3497 | 0.5176 | 0.8875 | 0.9962 |
| 2025 tail | floored | 0.4615 | 0.4676 | 0.4836 | 0.5106 | 0.5577 | **0.6436** | **0.9078** | 0.9980 |
| 2025 tail | **unfloored** | 0.0212 | 0.0528 | **0.0836** | 0.1775 | 0.3409 | 0.4920 | 0.8654 | 0.9894 |

**The `floored` rows are ERCOT-123 §5 verbatim and they reproduce exactly**
(≤\$20: 0.705/0.673/0.657/0.644; ≤\$25: 0.916/0.920/0.919/0.908). That is the
proof the new sub-\$20 bands are the same curve, resolved finer — not a second,
subtly different construction.

The `unfloored` rows are the ones ERCOT-135 needs, because nothing is assumed
bought before the curve speaks. **Only 5.8–8.4 % of coal capability is offered
at or below the model's own tranche-1 bid**, and only 1.0–2.1 % at or below \$0
(the price-taking signature, agreeing with ERCOT-123's 0.0000–0.0002 on its own
denominator).

## 4. The min-load block's own declared price — an independent corroboration

`Min Gen Cost` is the QSE's declared cost of running at minimum load. ERCOT-123
§7.4(b) recorded it as present-but-unused; it is used here for one purpose only.
Capacity-weighted, COAL:

| year | family | populated | p10 | **p25** | p50 | p75 | `TPO-Price1` p50, same rows | corr |
|---|---|---|---|---|---|---|---|---|
| 2024 | tail | 0.310 | 15.30 | **18.00** | 24.23 | 28.50 | 20.68 | 0.38 |
| 2024 | control | 0.284 | 18.00 | **18.00** | 24.28 | 28.50 | 20.89 | 0.44 |
| 2025 | control | 0.291 | 18.00 | **18.00** | 19.16 | 23.23 | 21.71 | 0.31 |
| 2025 | tail | 0.288 | 18.00 | **18.00** | 19.16 | 23.23 | 21.65 | 0.42 |

**Units are proved, not assumed:** `Min Gen Cost / LSL` averages **0.19**, so on
a ~200 MW LSL a $/hr reading would imply ~\$0.19/MWh — absurd — while a direct
$/MWh reading gives ~\$22.7/MWh, which matches the same rows' `TPO-Price1` p50 of
\$20.7–21.7. The column is **\$/MWh**.

**Coal's declared min-gen cost bottoms out at \$18.00 in every subset**, and the
floor is coal-specific: the CC control's p10 is **\$0.01**. So a fleet that *can*
declare near-zero min-gen costs, and does for CC, declares **\$18–24/MWh** for
coal. Coverage is 28–31 %, which is the same coverage regime that invalidated the
pooled `econ_high` (ercot122 §1, 21–47 %) — so this section is **corroboration,
not the anchor**. The anchor is §3's `TPO-Price1` at 98.8–100 % coverage.

## 5. The headline sizing

| year | family | model share @ \$4.50 | measured share ≤ \$4.50 | **ratio** | measured curve bottom p50 | measured min-load / HSL |
|---|---|---|---|---|---|---|
| 2024 | tail | 0.30 | 0.0638 | **4.70×** | 16.86 | 0.4514 |
| 2024 | control | 0.30 | 0.0579 | **5.18×** | 16.37 | 0.4246 |
| 2025 | control | 0.30 | 0.0710 | **4.22×** | 15.00 | 0.4506 |
| 2025 | tail | 0.30 | 0.0836 | **3.59×** | 15.00 | 0.4569 |

This is the ERCOT-135 §5 "excess cheap" block (3,255 / 4,163 / 3,171 MW) seen
from the RT side, and it **confirms its magnitude independently**: the model's
30 % cheap band against a measured 5.8–8.4 % leaves ~22–24 pp of coal capacity
mispriced-cheap, against ERCOT-135's 22.7–29.8 pp derived from the DAM. **Two
instruments, two conventions, the same answer.**

## 6. Rule 19 `[R-ONE-MECH]` — the block is already floored TWICE, and priced cheap on top

Enumerated **before** proposing anything, from the keeper's own `run_config.json`:

| mechanism | role | status |
|---|---|---|
| `ercot_coal_min_config_floor` | **FLOORS** min-load (EIA-860 smallest online configuration; 10 plants / 13,611 MW) | ARMED (ERCOT-129) |
| `coal_mustrun_per_plant` | **FLOORS** min-load (per-plant CAMPD `COAL_MUSTRUN_BY_PLANT`) | ARMED |
| `coal_tranche_1_frac` = 0.30 / `coal_tranche_1_fuel_passthrough` = 0.00 | **PRICES** min-load at \$4.50 (VOM only) | ARMED |
| `coal_econ_marginal_hr_bound` | floors the **economic** band only — does not touch tranche-1 | ARMED (ERCOT-115) |
| `ercot_thermal_as_endogenous` | prices the AS reservation | ARMED |

**This is the structural finding, and it is what makes the correction
rule-19-clean rather than a fourth floor.** The model represents "this coal is
must-run" **three times**: two independent floors force the block to clear, and
then a \$4.50 bid forces it to clear *again*, by making it cheaper than
everything else in the stack. The take-or-pay discount is standing in for
must-run behaviour that the floors already deliver.

A committed coal plant's min-load energy is **not cheap** — it is **not
price-responsive**. The model conflates those two. The floors are the correct
representation of "not price-responsive"; the \$4.50 is a second, redundant
mechanism whose side effect is the merit-order bias ERCOT-134 measured in every
band of every year.

## 7. What this licenses — and what it explicitly does NOT

**Licensed, for the first time in this lane:** a **repricing of the coal
tranche-1 band toward its measured level**, on a near-full-coverage measured
anchor (§3, `TPO-Price1` at 98.8–100 %), justified as the **removal of a
redundant mechanism** (§6) rather than the addition of a new one. Both prior
refusals are discharged: ERCOT-122 §4 and ERCOT-132 §7 refused because the
unoffered block's conduct was unknown — it is now measured, and it is economic.

**NOT licensed, and these are binding:**

* **Not a reach mechanism.** Coal offers 99.4–100.0 % of RT headroom; the model's
  ~100 % offering is *correct*. ERCOT-123 §7.1 closed this and nothing here
  re-opens it.
* **Not a fourth floor.** §6 is an argument for *removing* a mechanism. Adding a
  min-load floor or a withholding wall on top of two existing floors is exactly
  the rule-19 stack this section exists to prevent.
* **Not the offer LEVEL rebasis** (ercot132 leg B, CLOSED) — that moved
  `econ_low`/`peak`, bands this correction does not touch.
* **Not a `coal_tranche_1_frac` change.** ERCOT-135 §4 measured the model's 0.30
  as *smaller* than the measured min-load share (0.364–0.384 DAM, 0.425–0.457
  here). Moving both the share and the price would be two mechanisms on one
  phenomenon. **The share stays; only the price moves.**
* **Not a 2023 identification.** The SCED corpus is **2024–2025 only**. Any 2023
  application is an **extrapolation** and must be gated as one (ERCOT-123 §7.2's
  standing requirement).

## 8. Phase 2 is NOT run here — the ERCOT-116 gate still binds

`PRECOMMIT-ercot135` §0 blocks any coal offer-curve arm until the owner rules on
**ERCOT-116 adoption**, and the block is methodological, not procedural: on the
pinned fleet ~31/33/45 % of online coal plant-hours sit at the availability
ceiling, so an offer-curve change **cannot move them**, and any apparent gain
would be measuring the estimate rather than the mechanism (rule 14
`[R-ACCURATE]`). That argument is unchanged by this session's finding — it
applies to *any* coal offer-curve change, including this one. `run_config.json`
confirms `ercot_thermal_dam_availability_coal = False` in the keeper.

**So this session recommends and STOPS**, on the ercot122 §5 / ercot132 §7
precedent. The arm is pre-registered in full at
`docs/PRECOMMIT-ercot136-coal-minload-reprice-2026-07-29.md`, written before any
solve, and is one owner ruling away from executable.

**Also surfaced, not decided** (carried forward from ERCOT-135 §7.2): the
plant-grain water-fill saturates at model `pmax` and can lift a plant back above
a forced derate modelling a destroyed unit (Martin Lake 1.451×), so the ERCOT-116
envelope is not adoptable as-is without deciding how the redistribution and
`BIN_FORCED_DERATE_BY_YEAR` compose.

## 9. The corpus question, answered explicitly

The charter asked whether the sample-day corpus can carry this, or whether a
full-span intake is needed first. **It can, and no intake is needed** — on three
checks, all reported rather than asserted:

1. **The day-selection bias is not load-bearing.** The days are deliberately
   selected *on price* (tail vs control), so the families are their own control.
   The headline statistic agrees across them: MW ≤ \$4.50 = 0.0638 (2024 tail) vs
   0.0579 (2024 control); 0.0836 (2025 tail) vs 0.0710 (2025 control).
2. **The hour-of-day bias is bounded, not assumed away.** Three of four subsets
   sample hours 11–22. On the one all-24-hour subset (`2025_ercot86_tail_days`):
   MW ≤ \$4.50 **0.0997** (h11–22) vs **0.1003** (h23–h10); unfloored supply at
   \$4.50 0.0823 vs 0.0848; min-load share 0.4600 vs 0.4538.
3. **The statistic is conduct, not energy.** A self-schedule share and a curve
   bottom price are properties of *submitted offers*, not annual MWh, so they do
   not require a full span to be meaningful — and ERCOT-123 §6(ii) already showed
   these probe days reproduce the full-year DAM reach to ≤0.010.

**Nothing here is an annual statistic**, and none is quoted as one.

## 10. Scope, closed items honoured, environment parity

No LP was solved, no run was registered, no `ScenarioConfig` field was added or
changed, no keeper file was touched. Holdout years untouched (rule 22
`[R-HOLDOUT]`): the SCED corpus is 2024–2025, in-window; no 2022-or-earlier data
was read. December-2025 intervals are dropped explicitly by the shared loader
(ERCOT's schema revision drops `HASL`/`LASL` and the AS *award* block). No
GitHub Actions workflow was added. Rule 23 `[R-FROZEN-DERIVE]` honoured — every
quantity is read from the raw disclosure or the committed ERCOT-135 artifact; no
residual entered any derivation and no derive script was re-run.

**Section E (the `Base Point` conduct test) is reported as CORROBORATING and
explicitly NOT decisive**, in the probe docstring and in the artifact: both
correlations run 0.86–0.96 because `Base Point`, `Output Schedule` and
curve-at-price all scale with unit size and commitment state, and the hourly-LMP
proxy (the 5-minute SCED LMP is not on disk) attenuates the deviation-vs-price
correlation by construction. It is on the record so it cannot be mined later as
evidence in either direction.

Every CLOSED lane stays closed: coal offer LEVEL (ercot132 leg B), the F923
delivered-coal-price question as a price question (ercot135 §3), pooled
`econ_high` 2.856 (ercot122 §5.2), coal ramp trajectory (ercot127 §1 / ercot132
leg A), the availability ENVELOPE layer (ercot126 §§2–3), min-config upper bound
(ercot130), plant-grain fractional min-load floor (ercot127 §3), unit-grain
commitment STATE (ercot128), availability-SCALED floor (ercot128 P3–P4), age/temp
derates (ercot121 §1a), the EP-rebasis C3c lane (ercot119),
`ercot_zonal_gas_basis`, and the West/Panhandle topology split. **ERCOT-123's
closure of the coal offer-REACH question is honoured and independently
reproduced (§1); this document does not re-open it.**

**Environment parity.** Fresh container, ercot115–135 baseline matched: no
gtc-limits clean partition ("static TTC kept" 3/3), no confirmed-retirements
partition. `ScenarioConfig().cache_key()` = `603c2498bf71d21d` at session start
and end — **unmoved, no repair needed this session** (the ERCOT-135 §7.1
registration holds).
