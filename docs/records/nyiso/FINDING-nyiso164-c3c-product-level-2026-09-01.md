# FINDING — nyiso-164: NYISO's C3c caveat is its OWN diagnosis, not an inherited one

**Session:** nyiso-164 (Q2 of the C3c program charter) · **Date:** 2026-09-01 ·
**Mode:** zero-solve, committed artifacts + published raw only ·
**Keeper under test:** `2026-08-30-nyiso-159-loss-surface`
(`results/calibration/nyiso159_lossarm_B`) ·
**Artifact:** `results/calibration/_nyiso164_nyca_shortage_check.json` ·
**Probe:** `scripts/probes/nyiso164_nyca_shortage_check.py`

## 0. Verdict — the pre-registered kill gate FIRES on BOTH clauses

> *"If reality's tail hours show NO NYCA-level shortage, **or** if the model
> carries GW-deep NYCA headroom in those hours, this closes exactly as CAISO
> did: NYISO's C3c ledger is CONFIRMED rather than corrected."*

Both clauses fire independently, and they agree:

| clause | fires | evidence |
|---|---|---|
| **1 — reality was NOT NYCA-short** | **YES** | The NYCA-tier reserve price never exceeds the concurrent LMP in **65/65** tail hours (2023–2025), takes essentially all-distinct values with no RCPF rung atoms, and sits at a stable median **0.54–0.65 × LMP**. A *declared* NYCA-wide reserve pick-up covers only **8/65** tail hours. |
| **2 — the model carries GW-deep NYCA headroom** | **YES** | Reserve-carrying thermal headroom, **lower bound**, in reality's tail hours: **5.08 / 3.92 / 2.99 GW** mean (2023/24/25) against a 2,620 MW NYCA 30-minute requirement — and the NYCA families carry a zero dual and zero ORDC shortfall in **all 26,280** solved hours. |

**NYISO's C3c ledger is CONFIRMED.** The residual above the model's available
locational reserve adder is not a missing reserve *product*: at the tier that
governs a system-wide price tail, model and reality agree that NYISO was not
reserve-short. This closes the inheritance question and closes the lane.

This is a CONFIRM, and per the charter a CONFIRM is the equally-valuable
outcome. Nothing here proposes a mechanism, a parameter, or a prereg.

## 1. The question

nyiso-163b measured the *timing* of the keeper's reserve shortfall against
reality's price tail and found the model reserve-short **in** the hours reality
priced above $300 (overlap 5/10, 0/13, 20/42; 83 % of the model's 2025
shortfall hours). That is the **opposite** of the CAISO measurement on which
the cross-ISO C3c closure rests (caiso-144 §C/§D: 1.6–10.5 GW of model reserve
slack in reality's tail hours, overlay-to-reality overlap 1/47, 0/35, 0/8).
NYISO's lane had nonetheless adopted CAISO/MISO/ERCOT's probabilistic-RT-premium
diagnosis.

But the only families that ever bind in the NYISO keeper are the cheap
locational ones — `nyc_10min_total` / `nyc_30min_total` ($25/MW) and
`seny_30min_total` ($40/MW) — for a maximum available reserve adder of **$90/MWh**
in any single hour, against actual tail means of **$505 / $517 / $659**. Every
NYCA-level product (`nyca_10min_total` $750, `nyca_10min_spin` $775,
`east_10min_total` $775) never binds in any hour of any year.

So the discriminating question is a **quantity** question, not a price one:
*in reality's tail hours, was NYISO short at the NYCA level, or only
locationally in NYC/SENY?*

- NYCA-short in reality + never NYCA-short in the model ⇒ the model understates
  **system-wide** tightness — a headroom/availability defect, and the inherited
  diagnosis is wrong.
- Short only locationally ⇒ the model has the right products binding, the
  residual above $90 is genuinely the probabilistic premium, and the ledger is
  confirmed.

## 2. Method — nested differencing on published reserve prices

NYISO's operating-reserve regions **nest**: NYCA (zones A–K) ⊃ East (F–K) ⊃
SENY (G–K) ⊃ NYC (J) / LI (K) (`src/market_sim/model/reserves/spec.py`,
`NYISO_LOCATIONAL_REGIONS`). A zone's cleared reserve price is the sum of the
shadow prices of every nested region covering it. Zones **A–E** — WEST, GENESE,
CENTRL, NORTH, MHK VL — lie **outside** East/SENY/NYC/LI, so their reserve price
carries the **NYCA-level component alone**.

This is the same differencing construction `spec.py` already uses one tier down
to isolate the NYC-only shadow price ("*the locational regions NEST … so
differencing zone J against a zone sharing every region EXCEPT NYC isolates the
NYC-only shadow price*"). This finding applies it one tier **up**.

**Source (published, in-repo — nothing fetched):**
`data/raw/NYISO-AS/NYISO_as_rt_{2023,2024,2025}.csv` — NYISO MIS RT ancillary
clearing prices, 11 zones × `spin_10, nonsync_10, op_30, reg_cap`.
Corroboration: `data/raw/NYISO-AS/requirements/realtime-events/` — the P-35
Real-Time Events feed, which publishes NYISO's NYCA-wide **reserve pick-up**
operator actions: an independent, non-price record of actual 10-minute reserve
deficiency.

Reality's reserve prices are used **only as a validation target**, never as an
input (rule 13 `[R-MEASURED]`; the same admissibility line
`data/raw/NYISO-AS/requirements/README.md` already draws). No SOM-published
RCPF value is touched — the $25/$40/$750/$775 levels stand exactly as cited.

### 2.1 The construction validates itself

If the nesting holds, zones A–E must price **identically** in every hour. They
do — maximum A–E spread is **exactly 0.000000 $/MW** for all three products in
all 26,280 hours of 2023–2025. The NYCA-only tier is cleanly observable.

### 2.2 A clock repair that changes the answer

`actual_lmp_hourly_NYISO.parquet` is on the model's **fixed standard-time**
non-leap 8760 clock (`scripts/data/derive_actual_lmp.py`,
`_STD_TZ["NYISO"] = Etc/GMT+5`). The NYISO-AS CSVs and the event feed are naive
Eastern **prevailing** wall-clock. They differ by one hour through the entire
DST season — which is where every tail hour sits. A naive positional join would
have been an hour off and would have produced a materially different, wrong
answer.

The AS/event timestamps are therefore localized to `America/New_York` and
re-indexed with the repo's own `_std_hour_index`. An offset scan (−3…+3 h) of
the mean NYCA price in tail hours confirms the conversion, peaking at 0 in
every year:

| year | −2 | −1 | **0** | +1 | +2 |
|---|---|---|---|---|---|
| 2023 | 36.46 | 65.61 | **306.74** | 131.97 | 46.98 |
| 2024 | 5.72 | 105.66 | **254.62** | 89.97 | 30.25 |
| 2025 | 228.58 | 307.00 | **393.31** | 302.35 | 242.73 |

## 3. What reality's tail hours actually show

Tail = the C3c criterion's own definition (RT hourly LMP > $300); counts and
means reproduce the verdict exactly (10/13/42 h; $504.7/$516.7/$658.9).

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| tail hours | 10 | 13 | 42 |
| **NYCA tier** mean $/MW | 306.74 | 254.62 | 393.31 |
| NYCA tier median / max | 248.22 / 761.73 | 239.96 / 552.89 | 403.74 / 1101.85 |
| NYCA tier hours ≥ $40 | 10 | 11 | 41 |
| NYC **locational increment** mean $/MW | 139.57 | 206.77 | 180.20 |
| hours with locational increment > 0 | 9 | 13 | 42 |
| all-year baseline: NYCA ≥ $40 | 67/8760 | 45/8760 | 181/8760 |

Taken alone this looks like a **correction**: the NYCA-tier price is large,
exceeds the NYC locational increment on average in 2023 and 2025, and is
extremely concentrated in the tail (41 of 42 tail hours reach ≥ $40, against
181 of 8,760 hours all year).

**It is not.** A nonzero upstate reserve price means the NYCA reserve
constraint *bound*; it does **not** mean the reserve **demand curve** was
activated. Two signatures separate shortage from opportunity cost:

**(a) Ceiling.** A resource holding reserve forgoes energy, so its opportunity
cost is bounded by (LMP − its marginal cost) < LMP. A price set by the RCPF
demand curve is set by the *penalty factor* instead and can exceed the
concurrent LMP.

> The NYCA-tier reserve price exceeds the concurrent LMP in **0 of 10, 0 of 13,
> and 0 of 42** tail hours. Median ratio 0.573 / 0.536 / 0.654; maximum ratio
> 0.869 / 0.936 / 0.923 — it approaches the LMP but never crosses it, in
> **65/65** hours.

**(b) Quantization.** Demand-curve pricing pins the price to published rungs,
producing repeated atoms — the same signature `spec.py` relies on for NYC ("52
hours of 2025 at EXACTLY $40.00").

> Tail-hour NYCA prices are essentially all distinct — **10/10, 13/13, 33/42** —
> with exactly **one** exact rung hit across all three years ($750.00, 2025).

**(c) The independent operator record.** A declared NYCA-wide reserve pick-up
covers **2/10, 3/13, 3/42** tail hours — 8 of 65. Pick-ups are frequent overall
(35/40/26 per year) but are short contingency responses spread across all
months, not a tail phenomenon.

The stable ~0.5–0.65 × LMP ratio with a hard sub-LMP ceiling and a continuous
distribution is the signature of **energy opportunity cost**, not reserve
scarcity. Reality's tail is an **energy**-scarcity event that drags reserve
opportunity costs up with it — not an independent NYCA reserve shortage the
model is failing to see.

## 4. What the model shows

**The NYCA families never bind — and the reason is real headroom.**

| family | requirement | hours with nonzero dual | hours with shortfall |
|---|---|---|---|
| `nyca_10min_spin` | 655 MW | **0 / 8760** each year | 0 |
| `nyca_10min_total` | 1,310 MW | **0 / 8760** each year | 0 |
| `nyca_30min_total` | 2,620 MW | **0 / 8760** each year | 0 |

Reserve-carrying thermal headroom in reality's tail hours, as a **lower bound**
(the slim keeper bundle carries dispatch, not availability, and a re-solve is
out of scope — so headroom is bounded below by the fleet's own maximum
*simultaneous* thermal output over the year):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| max simultaneous thermal (MW) | 18,331.8 | 17,358.1 | 18,936.1 |
| tail-hour thermal dispatch, mean (MW) | 13,253.6 | 13,442.8 | 15,950.0 |
| **headroom LB, tail mean (MW)** | **5,078.2** | **3,915.3** | **2,986.1** |
| headroom LB, tail min / max (MW) | 0.0 / 12,560.3 | 133.6 / 10,906.2 | 0.0 / 11,850.1 |

Against a 2,620 MW NYCA 30-minute requirement, that is GW-deep on average —
though the bound goes to 0 in the single tightest tail hour of 2023 and 2025,
where it is simply uninformative rather than evidence of tightness.

**Method note, stated because the naive version is wrong and was rejected
mid-session.** Headroom must respect simultaneity. Summing per-class *annual*
peaks gives 26.1 / 26.5 / 30.3 GW — badly overstated, because the class peaks
are non-coincident (the `oil` class alone peaks at 11.1 GW in a handful of hours
on 1.26 TWh/yr in 2025, never together with the CC peak). The maximum the
reserve-carrying fleet ever delivered *at once* is 18.3 / 17.4 / 18.9 GW, and
that is what the bound uses. The rejected figure is retained in the artifact as
`sum_of_class_peaks_mw_NOT_USED`.

## 5. The reversal, reported rather than buried

The charter asked that a GW-deep model-headroom result be surfaced as a genuine
reversal of nyiso-163b §3's reading. It is one, and here is the precise shape of
it.

nyiso-163b's timing overlap is not wrong, but its *interpretation* was. "The
model is reserve-short in the hours reality priced high" was read as evidence
that NYISO is unlike CAISO. Split by **tier**, the picture inverts:

- **Locational tier (NYC/SENY).** The model binds here in reality's tail hours;
  so does reality (a positive NYC locational increment in 9/13/42 tail hours).
  This is **agreement**, not a defect — and it is where NYISO genuinely differs
  from CAISO, whose model had slack in every family.
- **System tier (NYCA).** The model is never short; reality was not short
  either (§3). This is also **agreement** — and it is the tier that would have
  to be short for a system-wide price tail to be a reserve phenomenon.

So NYISO's position **is** closer to CAISO's than the timing overlap alone
implied: at the tier that matters for C3c, both models have slack and both
markets were unshort. NYISO differs from CAISO in *which* tier binds, and
agrees with it on the tier that governs the residual.

The consequence for the ledger is the charter's own kill-gate consequence: the
residual above the model's $90 locational adder is **not** a missing reserve
product. C3c stands as a ledgered model-class limitation, on NYISO's own
evidence rather than by inheritance.

## 6. Limits — what this does not establish

1. **Hourly averaging dilutes the quantization test.** The RT feed is 5-minute,
   folded to hourly; an hour partly at an RCPF rung averages off it. The
   quantization evidence (b) is therefore reported, not relied on alone. The
   ceiling evidence (a) and the operator record (c) do not depend on it.
2. **The headroom figure is a lower bound only**, and is uninformative (0 MW) in
   the single tightest tail hour of 2023 and 2025. Quantifying true availability
   needs a solve, which this session may not run.
3. **The NYCA 30-minute demand curve's 9 interior rungs are not enumerated
   in-repo** (the model carries a single step at $750), so an exact-rung test
   against the full published curve is not possible from committed sources. Only
   $40 / $750 / $775 were testable.
4. **One fall-back hour per year is lost** to the AS feed's collapsed duplicate
   hour, and one spring-forward hour does not exist. Neither carries a tail hour
   in 2023–2025.
5. **This does not close C3c and does not move C3a-2025.** It settles the
   *provenance* of the C3c diagnosis, nothing more.

## 7. Governance

- **No solve, no holdout spend.** Years 2023–2025 only; freeze respected. NYISO
  holds no `complete` marker and is absent from `final` — untouched.
- **No mechanism, prereg, scalar or `ScenarioConfig` field.** Per the charter a
  NYISO mechanism prereg would require this kill gate cleared **and** pjm-164
  (Q1) returning REAL; the gate CONFIRMS instead, so the route does not open.
- **No SOM-published RCPF value is proposed for change**, in any form including
  a sensitivity — the ercot-214 failure this guard exists to prevent
  (rules 13 `[R-MEASURED]`, 1 `[R-STRUCT]`).
- **No keeper, shard, marker, frontier or determination change.** State verified
  unchanged at session start and end: `calibration_verdict.py --run-id
  2026-08-30-nyiso-159-loss-surface` → NOT-YET on {C3a-2025 −11.5 %, C3c};
  `audit_keepers.py --iso NYISO` → PASS 0/0.
- **Untouched by scope:** the nyiso-161 winter-face waiver card (filed, unruled),
  the permanently-closed AORR access route (nyiso-163b), the
  identification-blocked winter face (nyiso-163),
  `docs/calibration-log/governance.md` (pjm-164 may run in parallel; the
  cross-ISO synthesis is a later, separate step).
- **Matrix (rule 26).** **NO cell moves.** Duty (b) is not triggered — nothing
  was tested, armed or adjudicated; this is a measurement on committed artifacts
  and published raw. Duty (c) not triggered (no new `ScenarioConfig` field).
  DO-NOT-REDO honoured: `nyiso_ordc_measured_step_span` **K**,
  `nyiso_li_locational_reserve` **K**, `nyiso_east_reserve_families` **I**,
  `energy_reserve_coopt` **K**, `ordc_scarcity_overlay` NYISO **·**,
  `scuc_load_pocket_commitment` **G**, `diurnal_price_amplitude` **G** — none
  re-tested.

## 8. DO-NOT-REDO for the next session

The product-level question is **settled and must not be re-opened without new
evidence**: NYISO was not NYCA-short in reality's price tail, the model is not
NYCA-short either, and the two agree. Specifically retired here —

- "Raise a NYCA-level requirement / arm a NYCA family so the tail can price" —
  refuted: reality's NYCA tier was not on its demand curve (65/65 hours below
  the concurrent LMP; 8/65 declared pick-ups).
- "The model lacks headroom in the tail" — refuted: 3.0–5.1 GW lower-bound
  headroom against a 2,620 MW requirement.
- "NYISO's C3c caveat is inherited from CAISO/MISO/ERCOT and unsupported by its
  own evidence" — **answered: it is supported by NYISO's own evidence.**

Next shorthand: **nyiso-165**.
