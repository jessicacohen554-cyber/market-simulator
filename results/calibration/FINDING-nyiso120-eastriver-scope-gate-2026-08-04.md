# FINDING — nyiso-120: neither meter is wrong about East River. They AGREE, to 1.0 %, and what they agree on is that the model has been double-counting boiler fuel into a 306 MW NYC gas tranche

**Date:** 2026-08-04 · **ISO:** NYISO · **Years:** 2023–2025 (training only) ·
**Keeper at entry:** `2026-08-03-nyiso-118-seny-span`, CALIBRATED-WITH-CAVEATS,
C3c (`price_tail`) the sole ledgered caveat.

**Prereg (committed BEFORE any statistic, any derive and any solve):**
`results/calibration/PREREG-nyiso120-eastriver-scope-gate-2026-08-04.md`.
**Probes:** `scripts/probes/_nyiso120_eastriver_boundary.py` (no LP),
`scripts/probes/_nyiso120_scope_gate_ab.py`.
**Records:** `results/calibration/_nyiso120_eastriver_boundary.json`,
`_nyiso120_scope_gate_ab.json`, `_nyiso120_artifact_A.csv`.

**Session provenance.** The brief opened on **NEISO**, whose queue is
owner-gated end to end (matrix §5.6: item 1 SPENT, items 3/4/6/7/8 closed,
item 2 ceiling-bounded, items 5 / 5b / C3c-2023 all requiring an owner
green-light that is not granted), and directed a **cross-ISO** cell. This is
NYISO's, and it was minted one day earlier by **miso-122 §7 handoff item 1**,
which measured the defect, declined to act on it under rule 25
`[R-ISO-SCOPE]`, and left one question open: *"which meter is wrong about East
River's boundary, and it is not answerable from MISO's data."*

**It is answerable from NYISO's data, and the answer is that neither is.**

---

## §0 — the verdict in one table

| # | question | measured result | verdict |
|---|---|---|---|
| **KE1** | is eGRID's `CHPCHTI` at East River the same object as the CAMPD dark-boiler fuel? | **13,629,047 ÷ 13,493,031 = 1.0101** | **PASS** — the same object to **1.0 %**. eGRID's "CHP credit" here is not a topping-cycle steam credit; it is the fuel of two boilers that make no electricity |
| **KE2** | do two independent meters agree on the power-only rate? | CAMPD power-train fuel ÷ eGRID `PLNGENAN` = **7.3763** vs eGRID's credited **7.4205** — ratio **0.9940** | **PASS** — they agree to **0.6 %**, and they agree on **7.4**, not on the 11.8032 the keeper charges |
| **KE3** | is the dark set boilers, and is it machinery rather than a reporting spike? | **100.0 %** of dark fuel in `Dry bottom wall-fired boiler` in all three years; share **37.51 / 30.79 / 30.64 %**, max/min **1.22** | **PASS** — R2 (selection artifact) is refuted |
| **H vs R1** | double-count, or genuine boundary ambiguity? | KE1 + KE2 jointly | **H CONFIRMED.** `PLHTIAN` *is* the power train's fuel, so `PLHTRT = 7.4205` is *already* the power-only rate and the add-back **double-counts** |
| **KE4** | does the HEAD re-derive change only what it advertises? | **exactly one** applied row moves (2493/`CT_CHP`, `ok` → `below_credited`); zero other flag changes, zero other applied-rate changes | **PASS** |
| — | the applied-map change | East River's offer heat rate **11.8032 → 7.4205, −37.1 %**, on **306.0 MW** of NYC `CT_CHP` | ships under rule 14 `[R-ACCURATE]` |

---

## §1 — the object, and why it looked like a contradiction

The `measured_chp_heat_rates` mechanism replaces eGRID's **steam-credited**
`PLHTRT` with `(PLHTIAN + CHPCHTI) / PLNGENAN` — eGRID's own published CHP
useful-thermal allocation added back on the same net denominator. Its premise
is that at a **topping-cycle** cogen the process steam is recovered from the
prime mover's exhaust, so it is a free co-product and *all* the fuel belongs to
the power.

miso-122's hybrid-cogen scope gate then found that at some plants a slice of
the metered fuel burns in units with **zero gross load all year** — direct-fired
boilers that make no electricity at all — and that slice cannot be a topping
cycle's co-product either. At NYISO ORIS **2493 East River** the gate measured
that slice at **37.5 %** of 2023 fuel, and removing it produced **7.3763**,
which sits **below eGRID's own credited 7.4205**. The gate's response is the
`below_credited` flag: exclude the plant, on the stated ground that "the two
sources disagree about where the plant's boundary is."

That reading is what this session was sent to test, and it is **too
pessimistic**. The two sources do not disagree.

---

## §2 — the measurement (no LP), on NYISO's own data

CAMPD unit-grain, facility 2493, all four units, all three years — the
behavioural dark rule (`heatInput > 0`, `grossLoad ≤ 0` over the whole year) is
the derive's own, called directly rather than re-implemented; `unitType` is read
only to **check** the selection (rule 24 `[R-REGISTRY]` forbids the allowlist):

| year | unit | `unitType` | heat MMBtu | gross MWh | dark |
|---|---|---|--:|--:|:--:|
| 2023 | 1 | Combined cycle | 11,676,993 | 1,087,690 | — |
| 2023 | 2 | Combined cycle | 11,032,476 | 1,045,798 | — |
| 2023 | **70** | **Dry bottom wall-fired boiler** | **6,922,906** | **0** | **dark** |
| 2023 | **60** | **Dry bottom wall-fired boiler** | **6,706,140** | **0** | **dark** |
| 2024 | 1 / 2 / 60 / 70 | as above | 12,124,977 / 12,038,754 / 6,789,992 / 3,959,851 | 1,120,840 / 1,138,171 / 0 / 0 | 60, 70 |
| 2025 | 1 / 2 / 70 / 60 | as above | 11,905,619 / 11,510,467 / 5,675,265 / 4,668,050 | 1,093,484 / 1,095,160 / 0 / 0 | 70, 60 |

Two generating `Combined cycle` units and two boilers at **exactly zero** gross
load in every hour of every year. This is the hybrid Dearborn shape, and eGRID's
plant-level CHP split cannot see it — one ORIS code, two different machines.

**KE1 — the identity test.** eGRID's 2023 `CHPCHTI` is **13,493,031 MMBtu**.
The CAMPD dark-boiler fuel is **13,629,047 MMBtu**. Ratio **1.0101**, inside the
committed `[0.90, 1.10]` two-meter band (miso-118's, reused not reinvented).
**eGRID's entire CHP thermal allocation at East River is the boiler fuel.**

**KE2 — the basis-matched two-meter comparator.** CAMPD power-train fuel
(units 1+2) is **22,709,469 MMBtu**; over eGRID's **3,078,707 MWh** of net
generation that is **7.3763 MMBtu/MWh**, against eGRID's own credited
**7.4205**. Ratio **0.9940**. Two independent meters — EPA's stack CEMS and
EPA's eGRID plant sheet — agree on the power-only rate to **0.6 %**.

**Together KE1 and KE2 settle it.** If `CHPCHTI` is the boiler fuel, then
`PLHTIAN = total − CHPCHTI` is the power train's fuel, and
`PLHTRT = PLHTIAN / PLNGENAN` is **already the power-only rate**. Adding
`CHPCHTI` back charges the boilers' fuel to the turbines a second time. The
model has been offering 306 MW of NYC `CT_CHP` at **11.8032** — **59 % above**
what the machine actually burns per MWh.

**KE3 — persistence and composition.** 100.0 % of the dark fuel is in a boiler
`unitType` in all three years; the share is 37.51 / 30.79 / 30.64 % with
max/min **1.22**. Machinery, not a reporting spike. R2 is refuted.

### §2.1 — a corroborating physical fact, reported (not pre-registered, not gated)

CEMS gross load at the two generating units is **2,133,488 MWh** in 2023 against
eGRID's **3,078,707 MWh** net — a gross/net ratio of **0.693**, which is
`G_gross < 1`, the **physically impossible** signature miso-118 identified. It
means the plant makes ~0.95 TWh/yr of electricity that CEMS's `grossLoad`
channel never sees: HRSG steam turbines, which burn no fuel of their own and are
not Part-75 monitored. That is exactly why **7.4** and not **10.6** (the naive
CEMS-gross rate) is the right number, and it is why the correct denominator is
`PLNGENAN` — the same denominator the incumbent already divides by. It is
reported because it independently corroborates KE2 from the *generation* side
rather than the *fuel* side; it was not pre-registered and gates nothing.

### §2.2 — what this does NOT claim

It does not claim to know eGRID's allocation *intent*. The claim is the measured
identity — `CHPCHTI` ≈ dark-boiler fuel (KE1) **and** `PLHTIAN / PLNGENAN` ≈
CAMPD power-train fuel ÷ `PLNGENAN` (KE2) — which is sufficient for the
conclusion and does not require reading EPA's mind. It also claims nothing about
any other plant: the other three NYISO rows carrying dark fuel
(50368 Cornell 100 %, 10025 RED-Rochester 100 %, 52168 Riverbay 50.4 %) were
already excluded by the **earlier** scope gates (`not_unfired_topping`,
`basis_mismatch`) and their applied rates are byte-unchanged.

---

## §3 — the re-derive, and KE4

`python scripts/data/derive_chp_power_only_heat_rates.py --iso NYISO`, HEAD,
**unmodified** — the gate is miso-122's, shipped exactly as committed; this
session edited no derive logic (rule 23 `[R-FROZEN-DERIVE]`: the re-derivation
is motivated by a **scope-gate logic change on measured grounds** and cites it,
never by a residual).

| | A (committed, pre-gate) | B (HEAD re-derive) |
|---|---|---|
| sha256 | `407baa55…6ab2` | `c954bf06…588e` |
| `flag` census | ok=18, … | **ok=17**, `below_credited`=1, … |
| 2493 `CT_CHP` flag | `ok` | **`below_credited`** |
| 2493 `CT_CHP` **effective** rate | **11.8032** | **7.4205** |

**KE4 PASSES exactly**: one applied-rate row changes, zero other flag changes,
zero other applied-rate changes. The only other differences are that same row's
`heat_rate` / `model_over_measured` and three purely **additive** columns
(`cems_dark_heat_mmbtu`, `dark_fuel_share`, `heat_rate_all_fuel`).

**The direction is unambiguous only because NYISO carries no hand factor.**
`CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` is `{CAISO, PJM}`; NYISO is not in it, so
an excluded row reverts to the **plain eGRID rate** (7.4205) and the change is a
**37.1 % cut**. In a hand-factor ISO the same exclusion would push the rate
**up** — asserted in the scorer (`k6_direction_integrity`), not assumed.

---

<!-- §4 (A/B) and §5-§7 are completed once both arms have solved. -->
