# FINDING — miso-153 Phase 0: MISO's summer peak price is set by **CT_PEAKER**, not by a capacity cushion. The lever is the CT offer level, and it is NOT chartered.

**Session** miso-153 · **ISO** MISO · **Date** 2026-08-12 ·
**Keeper** `2026-08-09-miso-148-basis-aware` (`miso148_basis_B`), **UNCHANGED** ·
**Model** `claude-opus-5`.

**PREREG** `results/calibration/PREREG-miso153-summer-peak-phase0-2026-08-12.md`,
pushed at **`857a434`**, blob **`c2c1df03356f3b2f6f02351163cadce5ff5384a7`**,
**verified byte-identical against the FETCHED remote ref** before any
adjudicating statistic was computed (rule 27 `[R-PUSH]`).

**Status: NO SOLVE, NO RUN, NO REGISTRATION, NO `ScenarioConfig` FIELD, NO CELL
VERDICT MINTED** (no mechanism was tested — the miso-142 precedent). Rule 15 is
not engaged: a Phase-0-only session produces no run. **Keeper unchanged.**

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only. MISO holds no marker. No
holdout year was read, solved or scored.

**BRANCH TAKEN: P-D + P-E — both STOP branches. NO PHASE-1 LEVER IS SELECTED
AND NO SOLVE IS RUN.** Under the PREREG's own precedence
(P-D > P-C/P-E > P-A > P-B) this session escalates rather than proceeding.

---

## 1. Headline

At MISO's **top-200 model-demand hours** — 100 % summer, 110.4 GW mean in 2025 —
the price-setting tranche is **`CT_PEAKER`**:

| year | CT_PEAKER sets price | of which `CT_PEAKER\|econ` | COAL | ST_GAS | CC_REGULAR |
|---|---|---|---|---|---|
| 2023 | **40.0 %** | 34.3 % | 19.0 % | 9.5 % | 6.4 % |
| 2024 | **42.6 %** | 35.2 % | 25.2 % | 7.0 % | 5.4 % |
| **2025** | **66.0 %** | **55.0 %** | 7.2 % | 13.2 % | ~3 % |

**Both D-3 priors are refuted, in the same direction.** The pre-registered
priors were CC_REGULAR **45–75 %** and CT_PEAKER **10–35 %**. Measured:
CC_REGULAR **6.4 / 5.4 / ~3 %** — refuted by roughly an order of magnitude — and
CT_PEAKER **above the band in all three years**.

**So the summer peak price level IS the CT econ-band offer level.** That is the
`CT_PEAKER` offer object named-but-not-chartered by miso-152, and the PREREG
routes it to the owner (branch **P-E**), not to this lane.

**The cushion framing is NOT what fails.** D-1's idle headroom came in at
**19.2 / 20.0 / 16.2 GW (20.6 / 21.6 / 18.2 %)** against a pre-registered prior
of **12–28 GW / 12–25 %** — **inside the band in every year**; neither the low
nor the high surprise fired. The stack is not anomalously deep. What is
anomalous is *which* class sits at the margin and *what it is offered at*.

---

## 2. D-1 — the cushion is real, ordinary in size, and almost entirely CT

Available ≡ `pmax × availability`, the LP's own bound
(`model/commitment.py:1601`), against the keeper's committed `class_hourly` P1
dispatch, at the top-200 model-demand hours.

| year | avail GW | disp GW | **idle GW** | idle % | prior 12–28 GW / 12–25 % |
|---|---|---|---|---|---|
| 2023 | 93.28 | 74.06 | **19.22** | 20.6 % | **inside** |
| 2024 | 92.41 | 72.43 | **19.97** | 21.6 % | **inside** |
| 2025 | 89.09 | 72.87 | **16.21** | 18.2 % | **inside** |

**The idle block is CT.** Idle MW by class, and as a share of that class's own
available capacity:

| year | CT_PEAKER | ST_GAS | CC_REGULAR | COAL_FAMILY |
|---|---|---|---|---|
| 2023 | **14.18 GW (69.2 %)** | 1.41 (18.9 %) | 1.69 (6.9 %) | 1.62 (4.5 %) |
| 2024 | **12.90 GW (62.9 %)** | 2.31 (30.4 %) | 1.29 (5.4 %) | 3.15 (8.9 %) |
| 2025 | **11.25 GW (55.8 %)** | 2.64 (34.3 %) | 1.57 (7.0 %) | 0.43 (1.3 %) |

CT_PEAKER alone is **70–74 %** of the whole idle block. Coal runs at
**98.7 %** of its available capability at the 2025 peak.

This **independently corroborates miso-143's in-merit idle block** (19.3 GW in
2025 JJA h12–17, CT_PEAKER 64.5 % idle) on a different window and a different
denominator — measured here as total availability, there as in-merit
capability. Two constructions, same object.

**Idle capacity within $20/MWh above the clearing price:** 12.56 / 12.82 /
**10.64 GW**, of which CT_PEAKER is 7.74 / 7.56 / **6.31 GW**. The price would
have to rise ~$20 to draw in ~6 GW of CT.

---

## 3. D-2 — summer availability is HIGH, but its escalation does **NOT** fire

Cap-weighted mean availability, Jun+Jul minus annual, in percentage points
(absolute Jun+Jul level in brackets):

| year | CC_REGULAR | COAL_FAMILY | CT_PEAKER | ST_GAS |
|---|---|---|---|---|
| 2023 | **+16.9** (0.891) | **+15.7** (0.763) | +6.1 (0.923) | +7.8 (0.591) |
| 2024 | **+14.8** (0.859) | **+17.4** (0.790) | +6.1 (0.926) | +6.2 (0.614) |
| 2025 | **+12.0** (0.794) | **+11.6** (0.756) | +5.5 (0.919) | +7.5 (0.666) |

Against the pre-registered prior of **+0 to +8 pp**: CT_PEAKER and ST_GAS are
**inside** the band; **CC_REGULAR and COAL_FAMILY exceed it by roughly 2×**,
reported here as a genuine surprise.

**Neither pre-registered escalation trigger fires:**

* *"Jun+Jul more than 5 pp BELOW annual"* — **does not fire**; the sign is the
  opposite in every class and year.
* *"Jun+Jul absolute > 0.93 for CC/coal"* — **does not fire**; the maximum is
  CC_REGULAR **0.891** and COAL **0.790**, both below the threshold.

**Consequence: this session does NOT escalate the outage extract, and does NOT
re-tune it.** The seasonal *shape* is directionally correct and physically
right — availability is cut hardest in the shoulder maintenance months (April:
CC 0.56, COAL 0.41) and highest in summer — and the summer *level* is not the
"no derate at all" case the charter flagged. The un-re-tuned `X_cc = 0.240`
concern is **not shown to be load-bearing on the summer peak** by this
measurement. It is also not refuted; it is simply not what D-2 found.

---

## 4. D-4 — reserve co-optimization contributes **exactly nothing** at the summer peak

Read from `hourly/reserve_family_<year>.parquet`, the only artifact in which a
locational family's binding is observable.

**In Jun+Jul (1,464 h), across all three families and all three years: ZERO
binding hours, zero shortfall hours, dual identically $0.00.** Requirement
equals held MW in every hour (e.g. 2025 `miso_rbdc` 2,597 / 2,597 MW).

The **only** binding anywhere in the three years is **2024, rest-of-year,
`miso_subregional_or_midwest`: 4 hours**, dual max $200.00, shortfall max
773 MW.

The pre-registered prior (**0–5 %** of Jun+Jul hours) is **confirmed at its
floor**. The stricter trigger — *"0 binding hours in every family all year"* —
does **not** literally fire, because of those 4 hours in 2024. Substantively:
**MISO's reserve co-optimization is inert at the summer peak.** It is armed and
working (`energy_reserve_coopt` **K**, `reserve_pergen` **K**,
`dynamic_reserve_requirements` **K**); it simply never binds when the system is
tight. That is a fact about the summer peak, **not** a rejection of those
mechanisms, so **no cell verdict is changed**.

---

## 5. Imports — confirmed not the cause, with one leg **unmeasured**

| year | annual mean | top-200 mean | ratio | Jun+Jul mean |
|---|---|---|---|---|
| 2023 | 4,389 MW | 7,346 MW | 1.67× | 4,394 MW |
| 2024 | 2,611 MW | 5,064 MW | 1.94× | 2,815 MW |
| 2025 | 1,892 MW | 4,148 MW | 2.19× | 2,160 MW |

The model *does* import more at peak than on average. But **imports fall
year-over-year and are lowest in the blocker year** — the wrong sign to
manufacture 2025's specific summer failure, and consistent with the existing
import-starvation finding rather than against it.

**Reported against the instrument:** the pre-registered headroom leg is
**UNMEASURED**. `MISO_external` / `MISO_external_South` carry **0 MW of
assembled fleet capacity** — imports enter as a netted pseudo-class, not as LP
generators — so `headroom_share_at_peak` is undefined and the trigger *"above
the annual mean **with headroom remaining**"* cannot be evaluated. **P-B is
therefore NOT fired on imports**, on half a trigger.

---

## 6. THE INSTRUMENT DEFECT — found by the pre-registered gate, repaired, and one sub-hypothesis REFUTED

**T-6 (the PREREG's only gating bar) failed on first run** — and it was right
to. `_apply_outage_overlays` keys the unit-level CAMPD outage derate on
**`config.weather_year`**, not on the solve year
(`data/fleet/arrays.py:1091-1092`), while the production backcast pipeline pins
`weather_year = year` per solve year (`pipeline/backcast_config.py:1235`).
miso-134's `build_year` passes **one** config for every year, so the keeper's
`weather_year = 2023` silently applied **2023's outage windows to 2024 and
2025**.

**The repair is validated by its own built-in control** — 2023, whose
`weather_year` already *was* 2023, is **bit-unchanged**, while 2024 and 2025
move sharply, exactly as the diagnosis predicts:

| year | T-6 pre-repair | T-6 post-repair |
|---|---|---|
| 2023 | FAIL 2.93 % / 2.99 % (CC_CHP) | FAIL 2.93 % / 2.99 % (CC_CHP) — **unchanged** |
| 2024 | FAIL 9.71 % / **19.30 %** (COAL) | FAIL 2.21 % / 2.87 % (CC_REGULAR) |
| 2025 | FAIL 7.57 % / **11.86 %** (ST_GAS) | **PASS 0.43 % / 0.00 %** |

(Bars: ≤ 1 % of cells, ≤ 2 % of class capacity. Magnitudes reported in both
branches, as the PREREG requires.) The MISO extract is year-varying and
substantial — **120 / 121 / 153** derated (plant, group) keys at mean
multiplier **0.665 / 0.659 / 0.542** — so the mis-keying was material.

**Gating consequence, stated plainly.** The PREREG did **not** specify whether
T-6 is evaluated per-year or pooled. Read **per-year**, 2025 — the blocker year
— **clears** the bar and its D-1/D-3 are gated-valid, while 2023/2024 remain
**descriptive only**. Read **pooled**, all three are descriptive only. **The
conclusion is the same under either reading**, because it rests on 2025; the
ambiguity is disclosed rather than resolved in this session's favour.

**A sub-hypothesis of mine, REFUTED by my own measurement.** I expected this
defect might also explain miso-152's CT_PEAKER T-6 failure (+38–40 %), since it
used the same unrepaired `build_year`. **It does not.** On the T-6b
reconstruction bar, CT_PEAKER runs **+22.0 / +22.1 / +23.7 %** hot *after* the
repair against **+22.0 / +23.2 / +26.6 %** before — essentially unmoved.
**miso-152's CT verdict stands on its own**, and the charter's diagnosis is
confirmed: measuring CT properly *"needs an instrument reproducing CT
commitment"*. ST_GAS likewise still fails T-6b (−6.3 / −13.1 / −15.4 %).

**This bounds §1 and is stated as a limit on it.** Because the price-taking
reconstruction over-dispatches CT_PEAKER by ~24 %, the **66.0 % setter share is
an upper-leaning estimate**. The independent cross-check — miso-143's
**43.7 %** marginal CT share on the 2025 JJA h12–17 window — is **lower and
does not itself clear the P-E 50 % threshold**. Both measurements exceed the
10–35 % prior and both name CT as the dominant peak price-setter; the **P-E
trigger is met on this session's window and instrument, and not on
miso-143's**. That disagreement is part of what goes to the owner.

Internal consistency, in the other direction: the reconstruction's marginal
tranche sits within **$0.43 / $1.71 / $0.55** of the keeper's own clearing
price, and post-repair T-6a shows the keeper's dispatch never exceeds
reconstructed availability in 2025 (max violation **0.00 %**).

---

## 7. Traps — every counter-measurement, at full magnitude

| # | Counter-measurement | Result |
|---|---|---|
| T-1 | Bundle repointed to `miso148_basis_B` and asserted | **PASS** — 709 `run_config` keys matched, **0 dropped** |
| T-2 | Zero 3-argument `getattr(` in the probe | **PASS** — grep returns **0**; `ruff` clean |
| T-3 | Full raw band-suffix inventory dumped before aggregation | **PASS** — the econ smoothing is present and *not* collapsed; setter census is reported at raw-suffix grain (`CT_PEAKER\|econ` vs `\|committed` resolved separately) |
| T-4 | Fixtures from production types | **PASS** — every array comes from `generators_to_fleet_arrays`; no `SimpleNamespace` anywhere |
| T-5 | Carry-zone count asserted == 6 | **PASS** — import nodes excluded from all price/demand aggregates |
| **T-6** | **GATING** — dispatch ≤ reconstructed available | **FAILED, defect found and repaired** (§6). Post-repair: 2025 **PASS**, 2023/2024 FAIL |
| T-7 | Oil share of thermal at peak vs 0.5 % bar | **PASS** — 0.000 / 0.031 / 0.000 %; **no pooling required**, dual-fuel re-attribution is immaterial at peak |
| T-8 | Classes with no assembled fleet capacity listed | **REPORTED** — `OTHER, biomass, import, nuclear, oil, solar, wind` = **27.9 / 28.5 / 30.8 %** of peak dispatch, excluded from D-1/T-6 by construction |
| T-9 | Coal split | **POOLED** to `COAL_FAMILY` on **both** sides rather than reproducing `coal_supply_class` — exactly equivalent for D-1 totals, and it removes a fragile mapping. Deviation from the PREREG's stated method, disclosed here |

**No exact 0.0 was reported without a second derivation** (T-3): the one clean
zero in this finding — D-4's zero binding hours — is corroborated by the
`requirement_mw == held_mw` identity in the same rows, which is a different
column.

---

## 8. NOT PRE-REGISTERED — labelled, with counter-measurements

1. **T-6b**, the price-taking reconstruction vs `class_hourly` (±10 %). An
   *addition* carried over from miso-152's own pre-registered bar. It is
   **stricter** than what was pre-registered — it works against this session's
   conclusions, and it is what refuted §6's sub-hypothesis. Full magnitudes in
   §6.
2. **The `weather_year` repair** (§6). A bug fix caught by the pre-registered
   gate, not a new statistic. Both pre- and post-repair magnitudes reported;
   the pre-repair record is preserved at
   `results/calibration/_miso153_summer_cushion_PREREPAIR.json`.
3. **The D-2 mechanism attribution** read from the keeper's committed
   `legitimacy_diagnostics.json` — the attribution miso-143 said *"must precede
   any floor work"*. 2025 forced energy: `st_gas_mustrun_per_plant × ST_GAS`
   **10.735 TWh (47.0 %)**, `chp_steam` 7.09 TWh, `reliability_floor ×
   CT_PEAKER` 1.956 TWh (13.3 %), `nuclear_mustrun` 90.591 TWh (100 %).
4. **A governance observation — RAISED, THEN INVESTIGATED, AND WITHDRAWN. See
   §11.** The original flag read: `st_gas_mustrun_per_plant` and `chp_steam`
   both declare their D-4 window as **`h0-23`**, so their off-window-binding
   test is "vacuous by construction", while ST_GAS's grounded-above-budget pass
   (**34.1 / 35.8 / 48.4 %**) rests on clearing D-4. **That flag was wrong on
   the merits** and §11 records the measurement that refutes it. It is left
   standing here, struck through rather than deleted, so the record shows what
   was claimed before it was checked.

---

## 9. What this finding does **NOT** conclude

* It does **not** propose, test, arm or adjudicate any mechanism. No cell
  verdict is minted.
* It does **not** claim the CT offer level is wrong — only that **CT is what
  sets the summer peak price**, so the CT offer level is where that price comes
  from. Whether it is mis-identified is exactly the un-chartered question.
* It does **not** re-tune, or call for re-tuning, the MISO outage extract (§3).
* It does **not** open the **across-unit dispersion** object (miso-151 G-5) or
  the **CT_PEAKER fill-order** successor (miso-152). Both remain owner
  decisions.
* It does **not** treat the C3c ledger as covering the summer defect. The
  §1 object is the whole summer distribution sitting at winter levels — a
  mean-level failure the C3c tail ledger neither covers nor excuses.

---

## 10. The question that goes to the owner

Phase 0 has done its job: **the summer peak price-setter is identified, and it
is the one object this lane is not chartered to open.**

The measured position: at the 2025 top-200 demand hours the price is set by
`CT_PEAKER|econ` in **55.0 %** of zone-hours (CT_PEAKER overall **66.0 %**, upper-leaning
per §6; independent cross-check **43.7 %**), while **6.31 GW** of CT sits idle
within **$20/MWh** above the clearing price, and **11.25 GW (55.8 %)** of CT's
available capacity is idle at peak. Reserves contribute **nothing** (D-4),
imports are the wrong sign (§5), availability is not the story (§3), and the
cushion is ordinary in size (§2).

**Nothing further can be done in this lane without an owner charter.** The
options are laid out in the session summary; this document takes no position
between them beyond reporting what was measured.

---

## 11. ADDENDUM — the D-4 all-hours-window flag is **WITHDRAWN**. The ST_GAS floor self-windows, by measurement.

**Owner decision 2026-08-12: investigate the §8(4) governance item in this
lane.** Done, no LP. Probe `scripts/probes/_miso153_stgas_window.py`, record
`results/calibration/_miso153_stgas_window.json`. **The flag does not survive
its own investigation, and is withdrawn.**

**First, the citation I had not read closely enough.** `D4_WINDOWS`
(`scripts/legitimacy_diagnostics.py:362-376`) does **not** assert a flat
all-hours floor. It asserts the mechanism is *"self-windowing by construction —
each plant's committed tranche binds only in its top measured `online_frac`
fraction of hours ranked by system load"*, with the **hour-of-day** window
declared all-24 on the Entergy MISO-South VLR/self-commitment trace (Nine Mile
synchronized **98.2 %** of all hours 2023-25, Sabine 85.6 %, Lewis Creek
87.8 %). `chp_steam`'s entry is likewise *"ALL 24 hours **BY MEASUREMENT**"*
(CAISO CC_CHP CEMS net flat 0.65–0.76 GW across every hour-of-day, hod max/min
1.16) **and is D2-exempt** — it carries no C8 escalation path at all, so it was
never load-bearing on the ST_GAS question.

**Second, the D-4 machinery demonstrably bites.** The same registry records the
sibling `cc_mustrun_per_plant` **CT_PEAKER leg** being probed under a declared
`h7-22` window and **DROPPED for 12.8 % overnight off-window binding** — the
exact check I claimed the registry could not perform.

**Third, the measurement.** Reconstructing the floor through the production
chain and attributing it by `MECH_ST_GAS_MUSTRUN_PER_PLANT`:

| statistic | 2023 | 2024 | 2025 | reading |
|---|---|---|---|---|
| **W-2** floored MW, top load decile ÷ bottom | **3.04×** | **3.14×** | **3.28×** | **self-windowing is REAL** |
| **W-1** floored MW, hour-of-day max ÷ min | 1.56× | 1.60× | 1.60× | mild, no off-hour — all-24 is right |
| **W-3** per-plant bind frequency, median | **0.351** | **0.317** | **0.227** | **not an all-hours base** |
| **W-3** rows bound ≥ 99.5 % of hours | **0** | **0** | **0** | no plant is floored everywhere |
| **W-3** max per-plant bind frequency | 0.982 | 0.982 | 0.982 | **matches the cited Nine Mile 98.2 %** |

2025 load deciles, low → high (MW): 763 · 1374 · 1632 · 1635 · 1655 · 1817 ·
1908 · 2021 · 2238 · **2505** — **monotonic in system load**.

**Conclusion.** The `h0-23` entry is an **hour-of-day** declaration for a
mechanism that windows on **load rank**, and both legs hold by measurement: the
load-rank self-windowing is real (3.0–3.3×, monotonic), the median plant is
floored in only **23–35 %** of hours, no plant is floored in all of them, and
the most-bound plant reproduces the cited evidence figure to three digits.
**D-4 tests the hour-of-day claim, which is the correct test for what h0-23
declares, and that claim is true.** The load-rank claim D-4 does not reach is
now independently verified here. **There is no defect; the mechanism is
grounded; ST_GAS's rule-20 grounded-above-budget pass stands.** No cell verdict
changes, nothing is re-tuned, and no governance item is filed.

**Reported against the instrument.** This probe's floored volume (14.3 / 14.6 /
**15.4 TWh**) is larger than the committed D-2 attribution's forced energy
(8.22 / 8.61 / **10.735 TWh**) because they measure different things: D-2 counts
*dispatch at a binding non-exempt floor* (and its own note excludes the
P1-dependent RA bridge, making it a lower bound), while W-* measures the
*floor level itself* as composed. **Every conclusion above is about the floor's
SHAPE** — its load-rank gradient, its hour-of-day flatness, its per-plant
frequency — all of which are ratios invariant to that level difference. No
level claim is made from this probe.

---

## 12. ADDENDUM — the chartered Phase-1 lever is **BLOCKED ON TWO GROUNDS**, both measured before any solve was spent

**Owner charter 2026-08-12:** the miso-151 G-5 across-unit dispersion object,
**scoped to CT_PEAKER at peak**. Identification was attempted first, as rule 1
`[R-STRUCT]` requires. **It does not survive.** No `ScenarioConfig` field was
added, no solve was run, no run was registered. Probe
`scripts/probes/_miso153_ct_dispersion.py`, record
`results/calibration/_miso153_ct_dispersion.json`.

### Ground 1 — the measured side **cannot be scoped to CT_PEAKER**, and the attempt is already adjudicated

MISO's masked energy-offer corpus carries **no fuel or technology attribute**,
and the offer-side class bridge (coal vs CC vs CT) was **built and REFUTED at
miso-138** (`data/raw/miso-energy-offers/README.md`). miso-151's G-5 quantiles
are therefore **FLEET-WIDE**, not CT: cap-weighted p10 **0.169** / p50 **19.583**
/ p90 **48.007** / p95 **91.445** / p99 **298.026** $/MWh, p90−p10 = **47.837**
(DA-2025-07, 744 h). **There is no admissible route from this corpus to a
CT-scoped measured target**, and re-attempting the bridge is a DO-NOT-REDO.

### Ground 2 — the model's CT across-unit dispersion is **NOT collapsed**; it is the widest in the fleet

Across-**plant** dispersion of effective mc at the top-200 model-demand hours,
one observation per (plant, hour) at the plant's cheapest econ tranche,
capacity-weighted:

| class | n plants | 2023 p90−p10 | 2024 | 2025 |
|---|---|---|---|---|
| **CT_PEAKER** | **166** | **$40.09** | **$38.68** | **$26.45** |
| ST_GAS | 23–24 | 17.37 | 27.52 | 22.56 |
| ST_CHP | 27 | 32.86 | 10.15 | 19.62 |
| CT_CHP | 28 | 16.54 | 15.09 | 17.57 |
| COAL | 48 | 14.78 | 12.93 | 14.22 |
| CC_CHP | 17 | 10.85 | 10.69 | 14.86 |
| CC_REGULAR | 44 | 9.04 | 6.95 | 10.27 |

CT_PEAKER 2025 levels: p10 **32.61** / p50 **42.62** / p90 **59.07**.

**CT_PEAKER already carries the widest across-unit spread of any class, across
166 plants, at the same order of magnitude as the fleet-wide measured book
($26–40 vs $47.84).** The chartered premise — that the model collapses the
across-unit spread — **is not true of CT_PEAKER at the peak.**

**Stated against my own measurement, because the comparison is not
like-for-like and I will not present it as one.** G-5's population is the whole
DA book including near-zero self-scheduled price-taker offers (its p10 is
**0.169**), which is what makes its fleet-wide spread large; the model
represents self-scheduling as must-run *floors*, not as $0 offers, and this
probe scopes to **econ** tranches only. A pooled thermal-only model spread
would run roughly **$35–50** (bounded by the cheapest class p10 ≈ $18–20 and
CT's p90 ≈ $59–71) — bracketing $47.84 — but that is a **bound, not a
measurement**, and the populations still differ. **The honest statement is that
no like-for-like comparison is available, which is Ground 1 restated.**

### X-3 — the spread is broadly based, not a single-axis artifact

Holding CT's heat rate at its capacity-weighted mean (12.52 MMBtu/MWh; p10 9.97,
p90 14.81) and re-pricing moves p90−p10 only **40.09 → 34.43**, **38.68 →
29.47**, **26.45 → 22.69**. **Heat-rate dispersion explains only ~14–24 % of
CT's across-unit spread**; the remainder is delivered-fuel and adder dispersion.
`measured_ct_heat_rates` is already armed (**K**, miso-117), so the axis a
dispersion lever would most naturally reach is the one already measured.

### The one thread that runs the other way, reported because it does

The model's CT across-unit spread **narrows** 40.09 → 38.68 → **26.45** exactly
as C3a worsens (**−1.98 → −8.03 → −15.58 %**), and it narrows *against* the fuel
move: 2025 gas is materially higher than 2023, which for a heterogeneous
heat-rate fleet should **widen** an absolute $/MWh spread, not compress it by
34 %. The flat-heat-rate leg compresses too (34.43 → 22.69), so it is not a
heat-rate composition effect. **Something compresses CT's across-plant offer
spread in 2025 and this session did not identify it.** It is **n = 3**, it is
**not** a measured identification, and **no lever is proposed on it** — it is
recorded as the most specific open thread this lane has.

---

## 13. ADDENDUM — the §12 compression thread is **CLOSED**: the narrowing is REAL in the measured data and the model reproduces it faithfully

§12 left one open thread: CT's across-plant offer spread narrows **40.09 →
38.68 → 26.45** $/MWh as C3a worsens, *against* the fuel move that should widen
it. Three candidate causes were put up and **all three are refuted**, in order,
each before anything was built on it. Probe
`scripts/probes/_miso153_fuel_dispersion.py`, record
`results/calibration/_miso153_fuel_dispersion.json`, plus a direct read of the
F923 source table.

**Candidate A — "the 2025 preliminary EIA-923 vintage strips per-plant
delivered prices from most CT plants."** This was my hypothesis, and it was
motivated: the C1 scorer reports `CT_PEAKER` 2025 at **71/96 prior plants
missing, 26 % reporting**, and the keeper arms
`gas_plant_monthly_fuel_pricing = True`, so a coverage collapse *would* push
plants onto one shared trajectory. **REFUTED.** The CT fallback share — the
fraction of plants carrying no plant-specific series — is **flat**:

| year | CT fallback share | distinct CT price series | CT plants |
|---|---|---|---|
| 2023 | **21.7 %** | 63 | 166 |
| 2024 | **22.3 %** | 65 | 166 |
| 2025 | **22.3 %** | 62 | 166 |

**78 % of CT plants still carry a plant-specific series in 2025, the same as in
2023.** The C1 note describes the EIA-923 *generation* vintage used to score the
fuel-mix benchmark; it does **not** carry over to the *receipts* table the fuel
overlay reads.

**Candidate B — "plant-level coverage holds but MONTH-level coverage falls, so
annual means are pulled toward the trajectory."** **REFUTED, and in the
opposite direction** — 2025 is the *best*-covered year on record:

| year | gas plants | months per plant | share with all 12 months |
|---|---|---|---|
| 2023 | 452 | 11.37 | 73.7 % |
| 2024 | 452 | 11.49 | 76.8 % |
| 2025 | 440 | **11.48** | **79.1 %** |

**Candidate C — "it is a model artifact."** **REFUTED.** The compression is
present in the **raw F923 source table itself**, and the model tracks it almost
exactly:

| year | F923 source, across-plant gas price p90−p10 | model CT, same statistic |
|---|---|---|
| 2023 | **5.657** $/MMBtu | 5.321 |
| 2024 | **3.748** | 3.593 |
| 2025 | **3.679** | 3.413 |

**Conclusion: across-plant delivered-gas dispersion genuinely narrowed by ~35 %
between 2023 and 2025, and the model reproduces that faithfully.** The CT
offer-spread compression is not a defect — it is the model being *right* about
its measured input. **The thread is closed and the across-unit dispersion object
is closed with it.**

### What this leaves

The chartered dispersion lever is now closed on three independent grounds — the
measured side cannot be class-scoped (§12 Ground 1, miso-138), the model's CT
spread is already the widest in the fleet (§12 Ground 2), and the one anomaly in
it is a faithful reproduction of real data (§13). **No solve was spent on any of
them.**

D-3 stands: **`CT_PEAKER` sets MISO's summer peak price**, and its *dispersion*
is right. What has not been tested is its **LEVEL** — the miso-152 named
successor — and the blocking dependency for that is unchanged and now
independently re-confirmed by this session's T-6b (CT reconstruction runs
**+22–24 %** hot in every year): **it needs an instrument that reproduces CT
commitment.** That is the lane's next dependency, and it is an owner decision.

---

**Artifacts.** Probe `scripts/probes/_miso153_summer_cushion.py` (ruff clean).
Record `results/calibration/_miso153_summer_cushion.json`; pre-repair record
`results/calibration/_miso153_summer_cushion_PREREPAIR.json`.
PREREG `results/calibration/PREREG-miso153-summer-peak-phase0-2026-08-12.md`
(`857a434`, blob `c2c1df03`).
