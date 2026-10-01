# FINDING — SPP-39, card R-be (day selection): **THE CARD DOES NOT CLOSE.** It is a genuine selection defect, and one admissible signal is measurably better than the incumbent.

**VERDICT (one line): the pack expected this card to close at phase 0 on "no forecast-admissible
signal reaches it". It does not. An ORACLE bound proves all ten failing D-4 rows are
selection-fixable in principle (oracle 0.00–0.35 against a 0.50 bar), and a paired reconstruction
finds `day-mean NET load` beats the incumbent `day-mean gross load` on 7 of 10 rows
(mean −0.0335). What is NOT established is whether that is enough to clear the bar — my
reconstruction does not reproduce the scorer, so the absolute crossing is unproven and the card
stays OPEN rather than either closing or promoting.**

Lane **SPP-39** · base `origin/main` @ `33a7c9615f0dbc9aa19e58a976de29df462059d6` ·
branch `claude/spp-39-day-selection-r7k3` · **ZERO LP spent** (rule 32(a): parent is an orchestrator;
no shard launched, none needed yet).

Evidence base: **keeper 11** `2026-09-13-spp-38-vintage-cache` (bundle
`results/calibration/spp38_span`), as the SPP-38 handoff required — *not* keeper 10's, which the
vintage-cache repair superseded.

---

## 1. A CORRECTION I OWE ON MY OWN RECORD: the repair already fixed 2 of the 12 D-4 failures

SPP-38's RESULT, its calibration-log entry and keeper 11's promotion note all say D-4 is
"**identical to keeper 10**, 71 rows". The **71 is the TOTAL row count** and is right; the phrasing
implied the FAILING set was unchanged, and **it is not**:

| | keeper 10 | keeper 11 |
|---|---|---|
| D-4 rows total | 71 | 71 |
| **rows FAILING** | **12** | **10** |

Recovered keeper 10's diagnostics from its pin `f6e3ed374682059291605b0d425b81c399baaa96` and
differenced:

* **RESOLVED by the repair: `(2024, plant 6193)` and `(2025, plant 1230)`.** Nothing became worse;
  the new-failure set is **empty**.
* **`6193` is Harrington** — the coal→gas conversion plant that was *the single largest term in the
  stale vintage map* (1,018 MW filed `(6193,'COAL')` in `vintage_2023` and `(6193,'ST_GAS')` in the
  true 2025 fleet). Its D-4 failure was an artifact of the leak, and repairing the leak removed it.
  That is the repair's signature showing up in a diagnostic nobody gated on.
* **All four 2023 rows moved by exactly +0.0000** — the 2023 self-check again, on a third instrument.
* The seven surviving rows moved by −0.0007 to +0.0023, i.e. numerically inert.

So the failing set is now **10 rows on 4 plants**: `1230` (2023 only), `1235`, `1271`, `3008` (all
three years). **Plant 1230 is two-thirds resolved and plant 6193 is gone from the card entirely.**
The card's object is smaller than the pack describes.

---

## 2. THE SIZE HYPOTHESIS IS REFUTED — this is a selection defect

The cheapest way to close R-be would have been to show the window is simply too big: if the floor
occupies **W** whole days and the plant measurably ran on only **D < W** days, then *no* ranking can
avoid placing the floor on days the plant was off, the defect is window SIZE, and day selection is
the wrong object.

**That is not what the meter says.** ORACLE = rank the plant's days by its OWN measured online hours
(a perfect, deliberately inadmissible ranking — the best any selection rule could ever do):

| year | plant | bind_h | W (days) | D (online days) | D − W | **ORACLE zero_share** | actual |
|---|---|---|---|---|---|---|---|
| 2023 | 1230 | 1287 | 54 | 43 | −11 | **0.3526** | 0.6185 |
| 2023 | 1235 | 1124 | 47 | 50 | +3 | **0.0895** | 0.5632 |
| 2024 | 1235 | 1022 | 43 | 83 | +40 | **0.0000** | 0.5822 |
| 2025 | 1235 | 1138 | 47 | 38 | −9 | **0.2819** | 0.7487 |
| 2023 | 1271 | 836 | 35 | 36 | +1 | **0.2131** | 0.5921 |
| 2024 | 1271 | 732 | 30 | 62 | +32 | **0.0375** | 0.6995 |
| 2025 | 1271 | 852 | 36 | 59 | +23 | **0.0671** | 0.6467 |
| 2023 | 3008 | 2047 | 85 | 159 | +74 | **0.3127** | 0.6087 |
| 2024 | 3008 | 2427 | 101 | 183 | +82 | **0.2603** | 0.5777 |
| 2025 | 3008 | 2412 | 100 | 221 | +121 | **0.2196** | 0.5257 |

**A perfect day ranking clears the 0.50 bar on 10 of 10 rows**, with large margins (0.00–0.35). Even
the three rows where `D < W` clear it, because those plants run *partial* days that still contribute
online hours. **The window is not size-bound. R-be is a real selection defect and the card's framing
is correct.**

This bound is robust to the exact window definition: the margins are 0.15–0.50 wide and seven of ten
rows have `D − W` positive by 23–121 days.

---

## 3. AN ADMISSIBLE SIGNAL IS MEASURABLY BETTER — as a PAIRED result, not an absolute one

Candidates enumerated against rule 13 `[R-MEASURED]`'s forward test ("could this same quantity be
produced for a forward year from forward drivers, and would it respond to changed conditions?"):

| candidate | admissible? | reaches the card? |
|---|---|---|
| **day-mean gross load** (the incumbent) | **yes** — the model's own load shape, regenerated forward by construction | baseline |
| **day-PEAK gross load** | **yes**, same basis | measured, §3.1 |
| **day-mean NET load** (load − wind − solar) | **yes** — all three are the model's own arrays; a forecast year regenerates them from forward drivers and they respond to changed conditions | **measured BETTER, §3.1** |
| **day-PEAK net load** | **yes**, same basis | measured, §3.1 |
| temperature / weather driver | **NO for placement** — no committed SPP weather driver exists, and the LTLF is **blocked** (data audit item 17: `data/raw/load-forecast/spp/spp.csv` does not exist) | unreachable |
| SPP-published commitment or outage instrument | **NO** — data audit items 15/16/19 are `blocked`/`partial`; no per-unit commitment instrument is committed | unreachable |
| `mustrun_online_frac_per_year` | **NO** — reads the solve year's own meter; registered BACKCAST-ONLY and refused by SPP-27 | rule 28(a) DO-NOT-REDO |
| per-plant grain threshold / Mooreland special-case | **NO** — a free parameter chosen against its own statistic (rule 21 / rule 1(c)); miso-170's membership-list warning | rule 28(a) DO-NOT-REDO |

So the admissible-and-reaching set is **NOT empty** — it contains the three load-derived variants,
all on the same rule-13 footing as the incumbent (they are the model's own arrays, not measured
overlays). The pack's premise that it is empty is **falsified**.

### 3.1 The measurement, and its honest limit

Paired, same reconstruction on both arms so the instrument's bias cancels:

| year | plant | gross (incumbent) | **net** | net − gross | better |
|---|---|---|---|---|---|
| 2023 | 1230 | 0.5571 | 0.5980 | +0.0409 | gross |
| 2023 | 1235 | 0.5390 | **0.4078** | −0.1312 | **NET** |
| 2024 | 1235 | 0.4903 | **0.3992** | −0.0911 | **NET** |
| 2025 | 1235 | 0.7145 | 0.7580 | +0.0434 | gross |
| 2023 | 1271 | 0.5405 | **0.5262** | −0.0143 | **NET** |
| 2024 | 1271 | 0.6542 | 0.6847 | +0.0306 | gross |
| 2025 | 1271 | 0.6169 | **0.4977** | −0.1192 | **NET** |
| 2023 | 3008 | 0.4574 | **0.4270** | −0.0304 | **NET** |
| 2024 | 3008 | 0.5611 | **0.5573** | −0.0037 | **NET** |
| 2025 | 3008 | 0.5208 | **0.4608** | −0.0600 | **NET** |

**`day-mean NET load` is better on 7 of 10 rows, mean −0.0335.** Day-PEAK gross is *worse* than the
incumbent (mean 0.5873 vs 0.5652) and day-peak net is between.

> **THE INSTRUMENT DOES NOT REPRODUCE THE SCORER, AND THAT BOUNDS WHAT THIS MEANS.** Two
> reconstructions were tried and both were rejected as unfaithful rather than reported as if they
> were the scorer:
> 1. `W = round(bind_h/24)` over all days — runs **0.03–0.09 optimistic**, biased low on every row.
> 2. mechanism-16 binding cells collapsed per plant off `floors/<year>_P1.npz` — **0 of 10 rows**
>    reproduce; `bind_h` comes out systematically LARGER (1440 vs 1287, 1200 vs 1124, 2448 vs 2047).
>    The scorer evaluates **per class-slice** (`sel[global_i]`, one D-4 row per slice), not per plant
>    collapsed.
>
> **What survives the defect: the PAIRED ranking** (both arms share the bias, so the sign of
> `net − gross` is informative). **What does NOT survive: any absolute claim about crossing 0.50**,
> because the instrument is biased low by roughly the margin that would decide it. The "5 of 10 rows
> clear 0.50 under net load" number an earlier pass produced is therefore **withdrawn as
> unsupported** — it is an artifact of the optimistic bias.

---

## 4. WHY THIS IS NOT YET A PROMOTABLE ARM

Everything rule 29 `[R-SCREEN]` and rule 1 `[R-STRUCT]` require is missing, and the gap is not
closable by more phase-0 arithmetic:

1. **SPP-27 already refused `NET load` once, and its reason still binds.** It measured net-vs-gross a
   **WASH at the hour grain** (0.8168 vs 0.8168 on the conduct-overlap statistic) and refused the
   variant because it "bundles a second, independently-unmotivated change". This lane's result is at
   the **DAY grain**, which SPP-27 did not measure — that is genuinely new evidence under rule 28(a),
   **but it is a statistic, and a statistic is not a driver.** Adopting net load because it scores
   better on the rider it is scored against is exactly the fitted-mechanism selection rule 1
   `[R-STRUCT]` (c) forbids.
2. **A driver argument exists and has NOT been made.** The physical claim would be: a
   vertically-integrated utility commits gas steam against the load its *own* wind cannot serve, so
   the commitment signal is net load, not gross. SPP's wind penetration (model wind ~120 TWh against
   ~300 TWh demand) makes that prima facie plausible. **It requires evidence from SPP's own
   commitment record, not from the D-4 rider**, and this lane did not find such an instrument (§3,
   audit items 15/16/19 blocked).
3. **The instrument must be made faithful first.** No screen gate can be written against a rider this
   lane cannot reproduce. That is a scorer-side task, zero LP, and it is the next step.

**The card therefore stays OPEN, with its object sharpened and one candidate identified.** It is not
closed (the admissible set is non-empty and the oracle says the defect is reachable) and it is not
promoted (no driver, no faithful instrument, no screen).

---

## 5. RULES

- **32(a) `[R-SHARD]`** — zero LP; no shard launched. All of this is committed-artifact arithmetic.
- **28 `[R-MECH-MATRIX]`** — **NO cell verdict is minted**: no mechanism was tested, only measured.
  `st_gas_mustrun_per_plant` keeps its `K`; `mustrun_window_commitment_grain` keeps its `K`. The
  SPP shard is annotated with this enumeration and the open status (duty (b)), nothing more.
- **1 `[R-STRUCT]` / 13 `[R-MEASURED]`** — `offer_curve_by_group` not read, re-cut or swept. No
  adder, offset, haircut or proxy. The net-load candidate is reported as **not yet warranted**
  precisely because its only support is the statistic it would be scored on.
- **21 `[R-DOF]`** — the candidate adds **zero** free parameters (it re-keys an existing ordering);
  that is a necessary condition it meets, not a sufficient one.
- **31 `[R-RETAIN]`** — nothing deleted, no `rm`.
- **C3c** — not read, not gated on, untouched.
- **`[R-HOLDOUT]` removed 2026-09-09** — nothing here is a certified out-of-sample claim.

## 6. WHAT THIS MEANS FOR `complete` / `frontier`

R-be was the **cheapest** of SPP's three open cards and the one the pack expected to close for free.
It does not close. The queue is therefore **longer**, not shorter, than the pack assumed:

| card | status after this lane |
|---|---|
| **R-be** day selection | **OPEN** — object sharpened (10 rows, 4 plants), one candidate identified, needs a driver + a faithful instrument before any screen |
| **R-ba** merit inversion | untouched; zero-LP heat-rate census is its phase 0 |
| **R-bc** price-forming curtailment | untouched; the long pole, three kill conditions before any build |

**Next shorthand: spp-40.** The immediate next step is **zero LP**: make the D-4 rider reproducible
per class-slice, then re-run §3.1 on the faithful instrument. Only if net load still wins *and* a
driver argument lands does this become a PRECOMMIT and a screen.
