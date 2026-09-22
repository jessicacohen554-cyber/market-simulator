# RESULT — xiso (2026-09-22): the LP does not climb its own stack, in **nine ISOs out of nine**

```
SESSION : lp-stack-climb-attribution      SCOPE: CROSS-ISO (all 9 keepers)
ASK     : generalise the PJM h15 / SPP-70 "idle thermal in the top-1% hours"
          measurement to every ISO and decide, on a PRE-REGISTERED two-way
          test, whether C3c's ledgered caveat has a MODEL-CLASS cause.
VERDICT : **UNIVERSAL.** 9 of 9 ISOs clear the pre-registered bar; 7 of 7
          price-scored ISOs clear the robustness leg. Neither is close.
LP SPENT: **ZERO.** 44 fleet_only rebuilds + committed sidecars. No shard
          launched, no bundle produced, no run registered, no keeper moved,
          no cell verdict changed.
```

**Pre-registration:** `docs/PRECOMMIT-xiso-stack-climb-attribution-2026-09-22.md`,
pushed before the probe was run. Every definition and the 10 % / 6-of-9 threshold
were fixed there and **are not moved here**.

---

## 0. Headline

> **The clearing point does not reach the top of the thermal stack in any ISO this
> program models.** In the market's top-1 % hours the median ISO leaves **22–52 %**
> of its availability-aware thermal fleet idle, and — in seven of nine ISOs — that
> idle block is **almost entirely capacity offered ABOVE the clearing price**. The
> stack has the height. The price does not climb it.

The two source lanes were not measuring an ISO quirk. PJM h15 §4 and SPP-70 §4
were both measuring the same model-class property, and it is present everywhere.

---

## 1. The pre-registered verdict

An ISO SHOWS THE SIGNATURE iff the **median over its scored years** of
*% availability-aware idle thermal in the top-1 % window* is ≥ 10 %.

| leg | bar | result | |
|---|---|---|---|
| **PRIMARY** — all 9 ISOs | ≥ 6 / 9 | **9 / 9** | **UNIVERSAL** |
| **ROBUSTNESS** — the 7 price-scored ISOs (the actual C3c population) | ≥ 5 / 7 | **7 / 7** | **UNIVERSAL** |

No ISO fails, and the nearest miss is **SOCO at 15.5 %** — 55 % above the bar.
The two legs agree, so the verdict is not SPLIT.

---

## 2. The measurement — 44 ISO-years, every keeper, zero LP

Availability-aware (`pmax × availability[g,t]`, never a max-over-year proxy),
in the top-1 % hours by each ISO's own actual RT series. `>clr` is capacity
**offered above the clearing price**; `<clr` is the remainder — idle and
**in-the-money**.

| ISO | years | avail GW (med) | **idle %** (med) | **>clr %** | **<clr %** | model $ | market $ |
|---|---|---|---|---|---|---|---|
| CAISO | 2022–25 | 24.3 | **51.6** | 51.6 | ~0 | 53–389 | 112–636 |
| ERCOT | 2021–25 | 53.7 | **15.7** | 5.0 | **6.3–29.4** | 78–8 505 | 238–8 982 |
| MISO | 2020–25 | 80.5 | **33.3** | 31.6 | ~0 | 28–100 | 117–411 |
| NEISO | 2020–25 | 16.7 | **49.2** | 43.7 | 4.5–7.3 | 56–169 | 115–414 |
| NWPP* | 2023–25 | 22.9 | **34.2** | 33.0 | ~0 | 29–74 | (unscored) |
| NYISO | 2022–25 | 18.4 | **39.5** | 42.4 | ~0 | 58–152 | 217–573 |
| PJM | 2020–25 | 104.6 | **22.4** | 20.3 | ~2 | 33–121 | 90–679 |
| SOCO* | 2023–25 | 36.9 | **15.5** | 14.0 | ~0 | 35–4 330 | (unscored) |
| SPP | 2019–25 | 34.7 | **31.2** | 28.5 | ~0 | 23–188 | 173–1 268 |

\* price-unscored by owner registration — measured on a declared **load** window
(PRECOMMIT §2.1). A tightness window, not a price window: these two corroborate
the mechanism and **cannot speak to the price tail**.

**Reconciliation: 44 / 44 ISO-years pass G1–G3 clean.** No fleet class is
missing from its sidecar, no class dispatches above its availability, and every
uncovered sidecar class is non-thermal (nuclear / wind / hydro / solar / import /
biomass / virtuals) — nothing thermal is silently dropped.

### 2.1 The brief's own numbers reproduce, on a different keeper and a different join

PJM's keeper moved h14 → **h15** under the brief, and this lane keys the join on
the sidecar writer's own `klass_base` derivation rather than the h15 probe's
`fuel_type` workaround. Independent route, same answer:

| PJM | idle MW | idle % | CC | COAL | CT_PEAKER | ST_GAS | oil | model $ | market $ |
|---|---|---|---|---|---|---|---|---|---|
| brief / h15 §4 (h14 keeper) | 20 196–8 | 20 % | 95.4 % | 90.6 % | 52.4 % | 72.4 % | 0.3 % | $54.9 | $169.8 |
| **this lane (h15 keeper)** | **20 198** | **19.8 %** | **95.4 %** | **90.6 %** | **52.4 %** | **72.4 %** | **0.3 %** | **$54.9** | **$169.8** |

2025 lands at **16 413 MW**, the brief's figure exactly. The alphabet trap the
brief warned about (~62 GW of phantom idle) is removed by construction, not
routed around: same function, same inputs as the sidecar writer.

---

## 3. The mechanism is the same class in every ISO

Per-class utilisation in the top-1 % window, capacity-weighted across years:

| ISO | CC_REGULAR | COAL* | ST_GAS | **CT_PEAKER** | **oil** |
|---|---|---|---|---|---|
| CAISO | 74.3 % | 98.7 % | 8.0 % | **13.4 %** | **21.0 %** |
| ERCOT | 86.8 % | 96–98 % | 72.2 % | **64.5 %** | **47.9 %** |
| MISO | 85.1 % | 85–89 % | 55.0 % | **30.7 %** | **3.3 %** |
| NEISO | 74.9 % | 80.8 % | 59.9 % | **40.2 %** | **1.3 %** |
| NWPP | 84.5 % | 40–81 % | 11.6 % | **37.6 %** | **1.1 %** |
| NYISO | 88.2 % | 90.3 % | 66.6 % | **30.6 %** | **1.0 %** |
| PJM | 94.1 % | 94–96 % | 58.6 % | **46.2 %** | **1.4 %** |
| SOCO | 100.0 % | 70–78 % | 97.2 % | **80.0 %** | **5.2 %** |
| SPP | 86.1 % | 90–99 % | 59.2 % | **38.3 %** | **10.3 %** |

\* range over that ISO's coal supply classes (BIT / PRB / WC / LIGNITE).

**CC and coal are loaded; the peakers and oil are not.** CT_PEAKER runs at
**13–46 %** in six of nine ISOs *in the highest-priced hours of the year*, and
oil runs at **1–5 %** in six of nine. This is the PJM finding's composition,
reproduced nine times.

---

## 4. Reserve: the one place the story changes — and it changes for ERCOT only

**Not pre-registered.** This leg was added *after* ERCOT 2021 showed 29.4 % idle
with **0.0 %** above the clearing price — a large in-the-money undispatched block
in Winter Storm Uri, which is the signature of capacity held for an ancillary
product rather than out-of-merit capacity. It is reported as a **post-hoc
robustness check and does not move the §1 verdict** (rule 1 `[R-STRUCT]`: a
criterion chosen after the measurement is not a criterion).

The families are **nested, not disjoint** — ERCOT's `ercot_ordc_total` is exactly
`ECRS + NonSpin + RRS + RegUp`; NYISO nests nine families — so two bounds:

| ISO | coopt | gross | net of **max-family** (lower bd) | net of **sum-families** (hostile upper bd) |
|---|---|---|---|---|
| CAISO | off | 51.6 | 51.6 | 51.6 |
| **ERCOT** | on | 15.7 | **5.0** | **0.0** |
| MISO | on | 33.3 | 28.8 | 23.1 |
| NEISO | on | 49.2 | 38.6 | 24.5 |
| NWPP | off | 34.2 | 34.2 | 34.2 |
| NYISO | on | 39.5 | 25.1 | **0.0** |
| PJM | on | 22.4 | 19.3 | 16.6 |
| SOCO | off | 15.5 | 15.5 | 15.5 |
| SPP | off | 31.2 | 31.2 | 31.2 |

**The four ISOs with no reserve sidecar are exactly the four with
`energy_reserve_coopt = False`**, and that is not a measurement gap: verified in
code — `pipeline/kwargs.apply_reserve_coopt` returns `None` when the flag is off,
so **no reserve balance row enters their LP and no MW is withheld**. Their gross
idle *is* their net idle.

**ERCOT is the sole ISO that fails on any defensible reserve bound**, and two
independent diagnostics agree: its idle sits **below** the clearing price
(`<clr` 6.3–29.4 pts) and its reserve netting goes to 0.0 %. **NYISO fails only
under the hostile bound**, which for nine nested families double-counts grossly;
its own `<clr` is ~0, i.e. its idle is *above* the clearing price and therefore
**not** reserve-consistent. NYISO shows; ERCOT does not.

**This is an attribution WITHIN the charter, not a refutation of it.** Reserve
reach is one of the three mechanisms the successor was chartered on. ERCOT — the
one ISO that fully co-optimizes reserves *and* prices them into the energy dual —
is the one ISO whose idle block is explained. That is a result pointing at the
lever, not away from it.

---

## 5. The link to C3c — the tail error is ONE-SIDED, and PJM's "clean pass" is marginal

Model tail hours (max zonal dual above the ISO's `TAIL_THRESHOLD`, from committed
`system_<year>.parquet`) against the committed RT actual
(`frontend/data/backcast/tail/actual_tail.json`). **Energy-only, so this is an
indicative reconstruction of C3c, not the scorer's verdict** — the scorer uses
`ordc.hoursGt200.model` and a settlement basis for some ISOs.

**In 30 of 37 scorable ISO-years the model produces FEWER tail hours than the
market, and in 20 of them it produces ZERO or near-zero.** Only ERCOT 2021 (2.68×)
and SPP 2021 (1.32×) overshoot. The error has one sign, everywhere.

And the ISO-level pattern reproduces every keeper's committed C3c status: PASS
throughout for PJM; failures present for CAISO, ERCOT, MISO, NEISO, NYISO, SPP —
which is exactly the set carrying the ledgered caveat.

**PJM is not a counterexample.** It is the only ISO with a clean C3c pass *and*
it shows the signature at 22.4 %. Measured on the current keeper, its tail ratios
are **0.67 / 0.61 / 0.59** for 2023 / 2024 / 2025 against a **0.5× floor**. PJM
has the same deficit as everyone else; it simply lands inside a 2× band the
others miss. A criterion that 0.59 passes and 0.43 fails is not separating two
different mechanisms.

---

## 6. What does NOT generalise — stated because it was in the brief

**PJM's `peak`-band inertness is PJM-specific.** `CC_REGULAR`'s peak band
dispatches **0.000 MW in all 52 560 hours of all six PJM years** — and in *every
other ISO* that band clears: CAISO 108–150 MW max, ERCOT up to 440, MISO up to
1 938, NEISO ~600–695, NWPP ~922–934, NYISO 730–1 005, SOCO ~895–952, SPP
602–817. The h15 §3 observation is a true statement about PJM's tranche
structure and **must not be quoted as a model-class property**. Half the PJM
evidence generalises; this half does not.

---

## 7. What this means — the successor charter

The pre-registered consequence of UNIVERSAL: **C3c's ledgered caveat has a named
model-class cause for the first time, and the successor is a DEMAND / RESERVE /
COMMITMENT-REACH charter, not an offer-curve one.** The evidence for the second
half is now three-fold and independent:

1. **The stack already has the height.** Every ISO carries a highest available
   offer far above its clearing price ($267–$4 171 vs $23–$389 in the median year).
   Adding extent above a price that never climbs is inert by construction.
2. **Two lanes refused an offer-curve lever on this evidence** — PJM
   `measured_offer_surface` = **R**, SPP in both admissible forms. Under rule 28
   `[R-MECH-MATRIX]` (a) re-testing either needs **new evidence, not a new
   framing**, and this lane supplies none.
3. **Where reserves ARE co-optimized and priced into the dual, the idle block is
   explained** (§4, ERCOT). That is the positive control.

The open question this lane does **not** answer, and hands on: *why* does the
clearing point stop climbing when 13–46 % of the peaker fleet is available above
it? The candidates, in the order the evidence ranks them:

- **(a) Reserve reach** — four ISOs (CAISO, NWPP, SOCO, SPP) hold **zero**
  reserve in the LP, and three of the four sit at 31–52 % idle, the highest in
  the program. ERCOT, which holds the most, is the only ISO explained.
- **(b) Commitment reach** — the idle is concentrated in exactly the classes a
  no-MIP LP commits worst (CT, oil). §4 pattern 1 of the matrix doc already
  indicts LP-vs-MIP as the shared ceiling; this is its supply-side fingerprint.
- **(c) Demand** — the model's top-1 % hours are defined by the *market's* price,
  and in those hours the model's own load may not be tight. **Untested here.**

These are named as a queue, not adjudicated. Nothing in this lane measures which
one binds.

---

## 8. What is NOT claimed

- **No offer-curve lever is proposed** (the brief's constraint; rule 28(a)).
- **Nothing is armed, swept or promoted.** No keeper moves, no `ScenarioConfig`
  field is added, **no cell verdict changes in any shard**, and no ISO's
  determination is re-scored. Rule 25 `[R-ISO-SCOPE]`: the measurement in each
  ISO stands on that ISO's own keeper and fills no other ISO's cell.
- **The §4 reserve leg is post-hoc** and does not move the pre-registered verdict.
- **§5 is an indicative C3c reconstruction**, not the scorer's verdict.
- **The idle metric is an upper bound on "wasted" capacity** wherever an ISO
  co-optimizes reserve, and §4 bounds that error rather than assuming it away.
- **SOCO and NWPP cannot speak to the price tail** — they have no price series.

## 9. Cost and retrievability

**ZERO LP minutes.** 44 `fleet_only` rebuilds (4–40 s each) plus committed
sidecars, all in the parent — rule 32 `[R-SHARD]` (a) is satisfied because
nothing here is a solve. No shard was launched, so rules 33/34 do not engage.
Nothing needs promoting and nothing is at risk from container reclamation: the
probes are committed, and every number above is reproducible from `main` by

```
python3 scripts/probes/_xiso_stack_climb_phase0.py --iso <ISO> --year <Y> \
    --bundle results/calibration/<keeper bundle> --out <dir>
python3 scripts/probes/_xiso_stack_climb_verdict.py --out <dir>
python3 scripts/probes/_xiso_reserve_leg.py --out <dir>
```

**One declared simplification**, recorded in every output blob: PJM rebuilds run
with `pjm_da_virtual_bids = False`, because `data/raw/pjm-da-virtuals/` is
gitignored under PJM DataMiner2's non-member redistribution restriction and is
re-fetch-only. It adds no thermal row and changes no thermal `pmax` or
`availability`, and the dispatch side is read from the committed sidecar which
was written *with* it — so the measured arrays are untouched. Same line as the
h15 probe.

**Three derived partitions had to be regenerated** before the rebuilds would run
(`transfer-interface-limits`, `ramp-capability` per the brief, plus
`capacity-deliverability`, `nyiso-interface-flows`, `nyiso-reserve-requirements`
which the brief did not name and which blocked NYISO entirely).
