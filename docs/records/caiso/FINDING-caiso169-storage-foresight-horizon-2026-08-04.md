# FINDING — caiso-169: S2's cheap substitute is **REFUSED EX ANTE on two independent grounds**, and the reason is a *classification*, not a verdict. The already-built `storage_daily_cycling` (unarmed on CAISO, matrix cell mismarked `.`) **cannot reach the caiso-127 pin** — its only ν-break is at local midnight and **0 of its 365 touched SOC hours** fall inside the pinned-day coupling — and its own stated premise is **false for the fleet it would be applied to**: the measured CAISO battery fleet banks across days at sd **2,482 / 3,685 / 4,029 MWh/day**, so forcing exact day-neutrality trades a **2.01 / 2.16 / 2.18×** overshoot for a total undershoot of the same size. The bounded-foresight horizon family admits exactly **two** non-fitted values and the measured fleet sits **strictly between them**. NO LP, NO SOLVE, NO DERIVE, no `ScenarioConfig` field, keeper unchanged (2026-08-04)

**Session** caiso-169 · **Date** 2026-08-04 · **Branch**
`claude/caiso-169-calibration-jl3x3v` · **Base** `aaa94d23`

**Incumbent CAISO keeper** `2026-08-04-caiso-166-measured-dlap`
(CALIBRATED-WITH-CAVEATS, 2 owner-ledgered caveats, 0 FAILs). **Unchanged by
this session.** No mechanism was armed, no `ScenarioConfig` field was added, no
derive script was run, nothing was registered.

**Target** `docs/mechanism-testing-matrix.md` §5.2 lever-queue **item 3** — S2,
the DA/RT two-settlement separation charter — taken on its **own** object, the
evening/overnight spread compression (`FINDING-caiso127` §1/§2), after caiso-168
closed the *belly* route into it.

**No prereg was committed** because nothing was derived, armed or solved. This
is a measurement-only Phase 0 on committed artifacts, the caiso-167/168 pattern.

**Method** one command, committed artifacts only, no LP anywhere in it:

```
python scripts/probes/caiso169_storage_foresight_phase0.py
```

Artifact: `results/calibration/_caiso169_storage_foresight_phase0.json`.

---

## §0 — the one-paragraph result

**Rule 19 `[R-ONE-MECH]` decided this session before any new mechanism could be
proposed.** The instrument S2 would need already exists in the repo:
`ScenarioConfig.storage_daily_cycling` (wired to
`model.lp.rows._build_storage_daily_cycle_rows`), a zero-parameter
bounded-foresight constraint that pins every storage unit's day-start SOC to a
common level — literally "the LP's single-market perfect-foresight arbitrage
itself", which is how caiso-129 §5 *defined* S2. It is **unarmed on CAISO** and
its matrix cell reads `.` (n/a) with a rule-19 note that this session measures to
be wrong. Adjudicated on CAISO's own data it **fails twice, independently**.
First on **reach**: read off the shipped row builder, the constraint touches SOC
at 365 hours, **all** of them local midnight, and **none** strictly inside the
caiso-127 coupling — so on a pinned day (interior discharge at hod 0–6 *and*
hod 17–21 of the same local day) the identity `λ_ev = λ_on` **survives it
exactly**. Second on **premise**: its stated justification — *"a day-ahead
operator cannot shift across days either"* — is false for the measured CAISO
fleet, which banks at sd **2,482 / 3,685 / 4,029 MWh/day**; the incumbent
annual-cyclic LP overshoots that by **+2,495 / +4,266 / +4,770** and a hard 24 h
cycle undershoots it by **−2,482 / −3,685 / −4,029**. It is a **different wrong
of the same size**, not a fidelity gain. The generalisation is the real result:
the bounded-foresight horizon family has exactly **two** non-fitted values —
24 h (CAISO's IFM trade day) and ∞ (the incumbent) — and the measured fleet sits
**strictly between them**, so the interior point is reachable only with an
explicit uncertainty representation. **That is S2 proper, and it is an owner
charter, not a session lever.**

---

## §1 — the reconstruction, and three independent validations of it

The keeper's `hourly/storage_<y>.parquet` carries per-tech charge/discharge but
**no SOC column**, so SOC is integrated from the LP's own dynamics
`SOC[t] = SOC[t−1] + η_c·Chg − Dis/η_d`. `model.storage` builds every unit with
`eta = rte ** 0.5` and `eta_charge == eta_discharge`, so a per-tech **aggregate**
obeys the same recursion as each of its units and the tech-level reconstruction
is **exact**, not approximate.

Three checks, none of them an assertion:

**V1 — the LP's own annual cyclic SOC row.** Summed over the year the SOC
increment must be exactly zero. Measured residual: **−0.0037 / −0.0104 /
+0.0434 MWh** for `li_ion` on 4.733 / 8.984 / 13.304 TWh of charge, and
**+0.021 MWh** for pumped storage in every year. Float rounding.

**V2 — the pumped-storage capacity, known independently.** The model carries the
whole CAISO PS fleet as one continuous 2,077.6 MW / 10.0 h column (caiso-129 §7),
i.e. **20,776.0 MWh**. The reconstructed annual swing lands on
**20,776.02 MWh** in all three years — **ratio 1.0000010**, one part in a
million, on a number the reconstruction never sees.

**V3 — the clock, verified not assumed.** Model hour 0 is **local** midnight:
the keeper's own demand peaks at **hod 17** and troughs at **hod 3**, and its
solar peaks at **hod 11**. Under a UTC index the solar peak would land at
hod 19–20. This matters more than usual here — the entire §3 argument is a
statement about *where the day boundary falls relative to the two windows*, and
it inverts if the frame is UTC. (The caiso-168 §1 leap-year mapper is used for
every measured series; a linear offset would put every 2024 hour after Feb-28 a
day out of phase.)

## §2 — the model's storage foresight horizon, measured for the first time

The quantity `storage_daily_cycling` forces to exactly zero is the day's change
in stored energy. On the keeper:

| year | `li_ion` daily storage-side net **sd** | day-start SOC mean | day-start SOC **sd** | annual SOC swing |
|---|---:|---:|---:|---:|
| 2023 | **4,977** MWh/day | 5,050 MWh | **4,851** | 25,330 MWh |
| 2024 | **7,951** | 5,692 | **6,446** | 38,453 |
| 2025 | **8,799** | 8,048 | **7,140** | 52,963 |

Two things to read off it.

**The day-start SOC dispersion is as large as its own mean** (sd/mean 0.96 /
1.13 / 0.89). The LP enters each day with a wildly different amount of stored
energy; that day-to-day variation is precisely and entirely what a daily-cycle
constraint removes.

**The arbitrage is seasonal, not diurnal.** The annual SOC swing is
25,330 / 38,453 / 52,963 MWh against a year-end fleet energy capability of
roughly 29,968 / 44,524 / 61,792 MWh (caiso-168's envelope-inverted December
power cap × the 4 h `li_ion` duration — the duration is an assumption, flagged,
and nothing below rests on it). The battery runs an ≈85 %-depth excursion across
the *year*. A real four-hour resource does not.

## §3 — REACH: the ν-break falls outside the coupling, read off the shipped code

On a caiso-127 pinned day the fleet is interior in discharge in both windows, so
by LP optimality `λ_t = c_dis,t − ν_t/η_d` in each, and

> `λ_ev − λ_on = (c_dis,ev − c_dis,on) − (ν_ev − ν_on)/η_d`.

A constraint can only open that spread by moving one of the two terms. For
`storage_daily_cycling` the first term is untouched (it prices nothing), so it
must break `ν_ev = ν_on`. Interior SOC gives `ν_t = ν_{t+1}`; the chain breaks
only at an hour whose SOC column carries an **extra** row.

Stage D imports the production builder and inspects the matrix it returns —
a fact about the shipped code, not a restatement of its docstring:

| | measured |
|---|---|
| rows built (2 units × 364 boundaries) | **728 = 728 expected** |
| rows not of the form (`SOC[0]`, `SOC[24d]`) | **0** |
| distinct SOC hours touched | **365** |
| all touched hours are local midnight | **True** |
| touched hours **strictly inside** the caiso-127 coupling (hod 7…16) | **0** |

The overnight window is hod [0, 7) and the evening window hod [17, 22) of the
**same local day** (§1 V3). Every ν-break the constraint creates sits at hod 0;
**none** sits between the two windows. **The pinned-day identity `λ_ev = λ_on`
survives the constraint exactly**, conditional on interiority. This is the same
*form* of refutation as caiso-129 §3(c)'s "a floor can only ADD" — a property of
the instrument, not of a particular parameterisation.

**Its one residual channel, and that channel is measured near-empty.** The
constraint does not *bound* the day-start SOC, it only makes it common across
days, so it can reach the overnight position only through the day-to-day
variation it removes. Stage E:

| year | corr(day-start SOC, overnight draw), `li_ion` | overnight net, metered |
|---|---:|---:|
| 2023 | **+0.254** | +113.3 MW |
| 2024 | **+0.135** | +105.9 MW |
| 2025 | **+0.059** | +344.1 MW |

The correlation is near zero and **falls as the defect grows**. Equalizing a
quantity that barely covaries with the overnight draw has no measured channel to
it.

**A corroboration nobody aimed at.** The overnight metered net measured here on
the **caiso-166** keeper — +113 / +106 / +344 MW — reproduces caiso-127 §2's
+98 / +104 / +365 MW, which was measured on the **caiso-126** keeper thirteen
keeper generations earlier. The defect has survived the entire intervening
keeper chain unchanged; it is a property of the LP's storage structure, not of
any one calibration.

## §4 — PREMISE: the mechanism's own justification is false for this fleet

`scenarios.py` and the row docstring justify the constraint as *"the realistic
limit for short-duration storage; a day-ahead operator cannot shift across days
either"*. Measured against EIA-930 CISO `NG: OTH` — the same series the armed
`caiso_storage_shape_anchor`'s own envelope is derived from, on the model's
frame, `li_ion` like-for-like:

| year | model sd | **measured sd** | ratio | incumbent error | 24 h-cycle error |
|---|---:|---:|---:|---:|---:|
| 2023 | 4,977 | **2,482** | **2.01×** | +2,495 | **−2,482** |
| 2024 | 7,951 | **3,685** | **2.16×** | +4,266 | **−3,685** |
| 2025 | 8,799 | **4,029** | **2.18×** | +4,770 | **−4,029** |

**The real fleet banks across days.** Not a little: 2.5–4.0 GWh/day of standard
deviation, rising with the fleet. The model banks at **2.01 / 2.16 / 2.18×**
that rate — a stable multiple across a 2× build-out, which is what makes it a
structural signature rather than a year artifact. So:

* the incumbent annual-cyclic LP is **wrong, and the defect is real** — this is
  a genuine finding and it is not diminished by what follows;
* but `storage_daily_cycling` sets the model's dispersion to **exactly zero**,
  and zero is **further from the truth in the same units** on the mechanism's
  own metric in 2023 (2,482 vs 2,495 — a wash) and closer only by 14 % / 16 % in
  2024 / 2025.

Adopting the marginally-closer endpoint of a two-point family on a 14 % margin,
for a mechanism that §3 shows cannot reach the lane's defect, is **metric
selection, not structure** — exactly what rule 1 `[R-STRUCT]` forbids ("never
reach the right number through a mechanism that isn't real"). Exact day-neutrality
is not real conduct for this fleet.

**Two robustness legs, both stated rather than assumed.**
*Basis symmetry* — `NG: OTH` is a net series, so the measured legs are separated
hour by hour before η is applied, while the model side is gross. Collapsing the
**model** the same way moves its statistic by **< 0.02 %** (7–12 hours out of
8,760 carry both legs above 1 MW), so the ratio is not a basis artifact.
*Efficiency* — the measured fleet's true RTE is not observed; recomputing the
measured sd at RTE 0.80 / 0.85 / 0.90 gives 2,491 / 2,482 / 2,489,
3,720 / 3,685 / 3,682 and 4,096 / 4,029 / 3,998. A ±1 % band; the ratio stands.

## §5 — the classification, which is the session's real deliverable

**The horizon family is closed.** A bounded-foresight SOC horizon admits exactly
two values that are not chosen by the modeller: **24 h**, CAISO's IFM trade day,
a market-design fact; and **∞**, the incumbent annual cyclic. §4 places the
measured fleet **strictly between them**. Any intermediate horizon — 48 h, 72 h,
a rolling window — must be *picked*, and picking it against the measured
dispersion is a fitted DOF (rule 24 `[R-DOF]`), against the price residual an
outcome pin (rule 13 `[R-MEASURED]`). **There is no third non-fitted value.**

**The pinned-day instrument space is closed too**, and completely, by the §3
identity. Exactly two routes exist:

* **R1 — differentiate the discharge cost by hour** (`c_dis,ev ≠ c_dis,on`).
  A *shaped* price on the storage column. caiso-129 §5 refuted every shaped
  instrument in this space from one side or the other, and a shape fitted to the
  spread is an outcome pin (rule 13). **New corollary, and it is sharper than the
  reason on file:** a **scalar** `battery_dispatch_adder` cancels **exactly** from
  the identity — `c_dis` appears in both terms — so it could never open the
  spread *whatever its level*. That is a structural reason, independent of, and
  stronger than, caiso-100/101's two-sided throughput guard.
* **R2 — break `ν_ev = ν_on`**, which needs a binding SOC-chain event strictly
  between hod 6 and hod 17. Three candidate objects: (i) the SOC bound itself,
  already free to bind and doing so — 103 / 127 / 105 days bottom out in the
  overnight, which is what makes caiso-127's non-pinned days non-pinned;
  (ii) an explicit belly-phase SOC anchor — **barred**: a phase chosen *because*
  it separates the two windows is an outcome pin, and hod 0 is the only phase
  CAISO's midnight-to-midnight IFM trade day grounds; (iii) a genuine two-market
  structure, which anchors SOC at every hour, the belly included.

**⇒ S2 proper is (iii), and its size is now specified rather than gestured at.**
Two perfect-foresight settlements are algebraically identical to one, so a DA/RT
separation bites **only through an explicit information difference**: a second
LP solved on day-ahead information plus a measured DA-vs-actual forecast-error
input. That input is rule-13 admissible in principle — CAISO publishes DA
forecasts and actuals, and the quantity regenerates for a forward year from
forward drivers. The **build** is not a mechanism: it is two 8,760 solves per
year, an information structure the pipeline does not have, and a decision about
which λ is the scored price. That is the "structural change of a different size
that must be chartered separately" caiso-129 §5 anticipated, and this session
does **not** spend it — it specifies it.

## §6 — a wiring asymmetry, reported not repaired

`limited_foresight_dispatch` is documented as riding "the same machinery as
`storage_daily_cycling`", and in `runner.py:1840` it does — it ORs into the same
`storage_daily_cycle_hours=24` kwarg. **The backcast solve path does not.**
`scripts/run_calibration.py:4376` reads `config.storage_daily_cycling` alone, so
`limited_foresight_dispatch` is **inert on the storage limb in backcast mode**
and live only in a forecast. Reported here rather than fixed: repairing it would
make a mechanism this session refuses newly reachable in backcast, which is a
decision for the flag's own lane (its hydro limb and its G-30 scarcity charter
are not this lane's object).

**This is a known defect class in this repo, not a novel one.** caiso-162 found
the same shape — `apply_caiso_local_import_limits` had **no call site in the
backcast lane**, being invoked only from `runner.py:1627` on the forecast path,
so a `ScenarioConfig` field the queue assumed worked was structurally unreachable
from every calibration solve. It was caught only because the treatment arm
recorded the flag `true` and came back byte-identical to its control; **prices
alone would have written a false `I`**. The lesson that lane drew — check the
wiring *before* solving, not after — is why §3/§4 here read the shipped row
builder and the measured fleet rather than a residual, and it is the reason this
asymmetry is recorded even though nothing in this session depends on it.

## §7 — stated limits, not buried

* **The reconstruction is per-tech, not per-unit.** The sidecar aggregates over
  units, and `li_ion` is one unit per CA zone. Because η is common within a tech
  the aggregate SOC recursion is exact, but a day-boundary deviation could in
  principle be the sum of offsetting per-unit deviations — so §2's dispersion is
  a **lower** bound on the per-unit banking the constraint would remove. That is
  the conservative direction for §4's "the model banks too much" claim and the
  unhelpful direction for a claim of inertness, which is not made.
* **The absolute SOC level is not observable** from the sidecar; the path is
  anchored at its own annual minimum. Every statistic used is a *difference*, so
  the anchor cancels out of all of them.
* **§3's refutation is conditional on interiority.** The identity survives the
  constraint *given* interior discharge in both windows; the constraint could in
  principle reduce the *number* of pinned days by pushing units onto bounds. §3's
  correlation measures that channel on the incumbent solution and finds it
  near-empty and shrinking, which bounds it — it does not eliminate it. A
  counterfactual needs a solve, and §4 is why one was not spent: the mechanism
  fails its own premise independently of whether it would have moved the spread.
* **`NG: OTH` excludes pumped storage by construction** (caiso-168 §3), so §4 is
  a **battery-limb** measurement and says nothing about the walled PS object.
  The PS column's own numbers are reported in the artifact for completeness only.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only, hard-filtered in the probe and
  fail-closed. CAISO holds no `complete` marker, so 2022 / 2019 / ≤2021 /
  H1-2026 were untouched and no marker was written.

## §8 — disposition

- **`storage_daily_cycling` CAISO → `G`, REFUSED EX ANTE**, two independent
  grounds (§3 reach, §4 premise), **no solve spent**, no field added, keeper
  unchanged.
- **The matrix note on that row is corrected.** It read "CAISO uses the shape
  anchor instead — one-mech". That is not a rule-19 conflict:
  `caiso_storage_shape_anchor` is a per-**hour power** cap and constrains
  **zero MWh** of cross-day **energy** banking. The two are different objects on
  different rows, exactly as caiso-168 separated the PS charge **bound** from the
  PS **adder/RTE/duration** row. The correct cell was never `.` (n/a) either —
  CAISO has the fleet the mechanism targets.
- **Item 3 (S2) stays LIVE and is NOT spent.** What is closed is the cheap
  substitute; §5 specifies what the real charter is and what it costs.
- **Item 9 is struck as CLEARED** — a stale-text repair, not a result of this
  session. It was cleared at **caiso-153** (2026-08-02): the gas-coupling
  classifier was re-identified (the defect was the *estimator*, pooled OLS
  levered on the Jan-2023 $24.29/MMBtu citygate spike, not the body probe),
  Theil-Sen restored the CT bucket 1,786 → 9,950 MW and G1 0.235 FAIL → 1.306
  PASS, all four frozen gates passed, the caiso-152 parse correction shipped and
  `2026-07-31-caiso153-reid-b` was promoted. `derive_caiso_offer_surface.py:399`
  ships `theilslopes` on main today. The §5.2 queue entry was never struck and
  read as blocking and unowned for two days.
- **CAISO still holds no rule-22 calibration-complete marker.** No
  out-of-training year was solved, scored or touched, and **no marker was
  written**.

## §9 — DO-NOT-REDO (new, binding)

1. **Do not arm `storage_daily_cycling` (or `limited_foresight_dispatch`) on
   CAISO as a candidate for the evening/overnight spread.** §3 is a property of
   the shipped row geometry — 0 of 365 touched SOC hours fall inside the
   coupling — and §4 refutes the premise independently. Re-opening needs new
   evidence about *where the constraint's rows land* or a *measured* CAISO fleet
   that is day-neutral, not a re-run of this probe.
2. **Do not propose an intermediate SOC horizon** (48 h, 72 h, rolling-N).
   §5: the family has exactly two non-fitted values and the measured fleet is
   strictly between them; any interior value is a fitted DOF (rule 24) or an
   outcome pin (rule 13).
3. **Do not propose a belly-phase SOC anchor** — a cycle boundary moved off
   local midnight so that it separates the overnight from the evening. The phase
   would be chosen *because* it breaks the pin; hod 0 is the only phase CAISO's
   IFM trade day grounds. §5 R2(ii).
4. **Do not re-file a scalar storage price** (`battery_dispatch_adder` or a
   charge-side twin) as a spread instrument. §5 R1: a scalar `c_dis` cancels
   **exactly** from the pinned-day identity, so it cannot open the spread at any
   level. This is additional to caiso-100/101's throughput guard, not a
   restatement of it.
5. **Do not re-measure the model's cross-day banking or the measured
   comparator.** §2/§4 carry them, with the reconstruction validated three ways
   (§1) and two robustness legs on the ratio (§4).
6. **Do not quote `storage_daily_cycling`'s docstring justification** — "a
   day-ahead operator cannot shift across days either" — as a measured fact for
   CAISO. §4 refutes it at sd 2,482 / 3,685 / 4,029 MWh/day. The claim may still
   hold for another ISO's fleet; per rule 25 `[R-ISO-SCOPE]` that is that ISO's
   measurement to make, and **ERCOT's `K` is not disturbed by anything here**.
7. **Use the non-leap 8760 clock with Feb-29 dropped, and verify it** for any
   CAISO probe that pairs a measured series to model hours, or that reasons about
   where a day boundary falls. §1 V3.

Carried forward unchanged: `FINDING-caiso168` §8, `FINDING-caiso167` §8,
`FINDING-caiso153` §G, `FINDING-caiso152` §H (its §I lead refuted at caiso-153),
`FINDING-caiso129` §6, `FINDING-caiso127` §7, and the earlier chain they carry.

Next number: caiso-170.
