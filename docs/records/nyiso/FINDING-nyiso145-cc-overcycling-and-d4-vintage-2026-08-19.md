# FINDING nyiso-145 — plant 7314's bridge over-run is **two different defects wearing one label**, and its D-4 conviction is a **measurement-vintage artifact**

Session nyiso-145, job 3. Keeper at HEAD `2026-08-18-nyiso-144-layup-exclusion`
(re-verified **CALIBRATED** this session from committed artifacts,
`scripts/calibration_verdict.py --run-id`, no solve). Every year read, solved or
scored here is **2023, 2024 or 2025**; the holdout spend freeze is ACTIVE and
untouched (rule 22).

Probes: `scripts/probes/_nyiso145_smallcc_overrun.py` (record
`results/calibration/_nyiso145_smallcc_overrun.json`). Its solves are throwaway
single-year in-process replays of the keeper's OWN recipe with **zero config
delta** — instrumentation, not runs: no bundle is written and none is
registrable (see §7).

---

## 0. THE ANSWER, in five lines

1. **7314's 2025-only D-4 unit-conduct FAIL is produced by a data-vintage
   artifact, not by the plant or the mechanism.** It is a CT-ONLY CEMS reporter;
   the rider's own protective `ct_only` skip suppressed it in 2023 and 2024 and
   **cannot fire in 2025**, because the preliminary EIA-923 vintage supplies no
   `e_ann`. C1 guards that vintage by name; **D-4 has no vintage guard at all.**
2. **On the complete vintages the plant is right**: model P1 vs EIA-923 net =
   **1.01× (2023)** and **1.18× (2024)**. The over-run is real only in 2025.
3. **The over-run is not 7314's and not the bridge's.** It is two distinct
   fleet-wide defects in CC_REGULAR, which the probe separates cleanly:
   **(A) over-cycling** of the big committed CCs, and **(B) a merit-order
   inversion** that runs mothballed small CCs at 25–225× their metered output.
4. **The bridge is scaffolding built on defect A, not its cause** — for 7314 in
   2025 it supplies 79.9 GWh of an 884.7 GWh model dispatch (**9 %**).
5. Three candidate explanations were **refuted by measurement, ex ante, with no
   solve**: the fuel price, the heat rate, and a missing outage (§4).

---

## 1. WHAT PLANT 7314 IS

**Richard M Flynn (Holtsville)**, EIA plant 7314 — a 1994 combined cycle in
Suffolk County on Long Island: one 110 MW CT (`NA1`) plus a 60 MW steam turbine
(`NA2`), 170 MW nameplate, dual-fuel (Energy Source 2 = DFO on both units). The
model carries it as 7 CC_REGULAR tranches in `Long_Island`, heat rates
7.834 → 8.668 MMBtu/MWh, VOM $2/MWh, availability 0.79–0.97 with no full-outage
hour.

**It is a CT-ONLY CEMS reporter.** CAMPD carries one unit, `001`, peaking at
112 MW — the CT alone; the steam turbine never reports. Its implied *gross* heat
rate is therefore 12.3–12.7 MMBtu/MWh (whole-train fuel over CT-only output),
and the bench's own `e_ann/c_ann` ratio is **1.46 (2023) / 1.47 (2024)** — the
textbook 1×1 signature.

---

## 2. WHY THE D-4 VERDICT FLIPPED IN 2025 — AND WHY IT IS AN ARTIFACT

`legitimacy_diagnostics._flag_ct_only_reporters` marks a plant `ct_only` when its
EIA-923 annual net exceeds a threshold ratio of its CAMPD annual gross, and
D-4's per-unit conduct rider **skips** such plants by name: *"a median of zero in
a series the benchmark already declines to trust is a metering artifact, not
conduct — the rider must not convict on it (rule 14)."*

| year | 7314 `e_ann/c_ann` | `ct_only` | D-4 rider |
|---|---:|---|---|
| 2023 | **1.46** | True | **SKIPPED** |
| 2024 | **1.47** | True | **SKIPPED** |
| 2025 | **1.00** | False | **CONVICTS** (0.0774 TWh, 2,233 h, 77.1 % at zero) |

The 2025 ratio is exactly 1.00 because **there is no 2025 EIA-923 record for the
plant**: `e_ann` falls back to `c_ann`, and a ratio of exactly one can never
exceed the threshold. The same is true of every other plant the preliminary
vintage misses — the probe finds `e923` absent in 2025 for 54592, 50744, 54593,
50978, 54574, 56188, 10190, 54034 and 7314 alike.

**The scorer already knows about this vintage and guards against it.** The
keeper's own verdict report SKIPS five 2025 classes with the reason
*"preliminary EIA-923 vintage: incomplete plant data (11/20 prior plants missing
(45 % reporting))"* — CC_REGULAR, CC_CHP, CT_PEAKER, ST_GAS and ST_CHP. **C1 has
that guard; D-4's conduct rider does not.**

**Consequence, stated plainly and in both directions.** The keeper's headline
*"D-4 unit-conduct failures 17 → 3, zero new"* is partly a function of which
plants the 2025 vintage happens to un-protect: the vintage can manufacture a
conviction (7314) and it can equally strip protection from a plant that would
otherwise have been skipped. The nyiso-144 A/B's *comparison* is unaffected —
both arms were scored on the same vintage — but the absolute count is not a
clean measure of legitimacy in 2025. **This is a defect in the diagnostic, not
in the keeper**, and it is filed, not fixed here (§6).

---

## 3. THE REAL OBJECT: TWO DEFECTS, SEPARATED

The probe captures the model's own P0 dispatch and the bridge floor per LP row
and scores both against each plant's CAMPD meter **and** its EIA-923 annual net.
The 923 leg is what makes the CT-only plants scoreable at all. Multi-class plants
(`2500`, `50292`) are excluded from every 923-basis ratio below, because their
923 total spans prime movers the CC_REGULAR rows do not.

### 3a. Defect A — the big committed CCs are **over-cycled**, and the bridge pays for it

| plant | year | P0 runs | P0 median run | metered runs | metered median run | model on-share | metered on-share | bridge floor |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| **2539 Bethlehem** (893 MW) | 2023 | **279** | **5 h** | 7 | **608 h** | 0.27 | 0.94 | **779.4 GWh** |
| | 2024 | **302** | 9 h | 5 | **1,217 h** | 0.67 | 0.92 | 490.1 GWh |
| | 2025 | **262** | 7 h | 7 | **487 h** | 0.70 | 0.95 | 484.5 GWh |
| **7314 Flynn** (170 MW) | 2023 | 321 | 6 h | 115 | 20 h | 0.32 | 0.43 | 130.7 GWh |
| | 2024 | 360 | 8 h | 79 | 19 h | 0.46 | 0.46 | 127.0 GWh |
| | 2025 | 286 | 9 h | 106 | 20 h | 0.65 | 0.36 | 79.9 GWh |

Bethlehem is a **near-baseload plant in reality** — 5 to 7 starts a year, runs of
487–1,217 hours, online 92–95 % of the year — and the LP cycles it **262–302
times a year in runs of median 5–9 hours.** It is simultaneously the fleet's
**largest single consumer of bridge floor energy** (779 GWh in 2023, more than
the whole rest of the mechanism) and, at P1, **under**-produced (1,463.5 GWh
against EIA-923's 4,357.9 = **0.34×**). The bridge is manufacturing floor energy
to glue back together a run pattern the continuous LP shattered; it does not
succeed, and the defect survives into P1, which is the scored pass.

This is the failure mode the shared detector's own `startup_aware` screen was
written for (*"phantom micro-runs a real unit commitment would never start"*).
It is NOT proposed here: ERCOT-63 adjudicated that screen and dropped it with
cause, and a NYISO test would need its own pre-registration and its own evidence
(rules 25 / 28d).

### 3b. Defect B — mothballed small CCs are run at **25×–225×** their metered output

Model P0 ÷ EIA-923 annual net, complete vintages:

| plant | MW | 2023 | 2024 | model on-share | metered on-share | bridge floor |
|---|---:|---:|---:|---:|---:|---:|
| **50744 Sterling** | 65 | **225.1×** | **129.9×** | 0.96 / 0.97 | 0.01 / 0.01 | 0.00 |
| **54593 Batavia** | 67 | **68.5×** | **113.6×** | 0.89 / 0.87 | 0.02 / 0.01 | 0.00 |
| **7784 Allegany Cogen*** | 67 | **43.0×** | **33.1×** | 0.99 / 0.99 | — | 14.0 / 18.6 |
| **54592 Massena** | 104 | **27.0×** | **45.9×** | 0.93 / 0.91 | 0.03 / 0.02 | 0.00 |
| **50978 Carr Street** | 123 | 2.92× | 3.13× | 0.90 / 0.94 | 0.26 / 0.31 | 31.2 / 17.0 |
| 56188 Pinelawn | 82 | 1.92× | 2.15× | 0.31 / 0.31 | 0.17 / 0.16 | 0.00 |
| 54574 Saranac | 286 | 1.20× | 1.56× | 0.36 / 0.63 | 0.36 / 0.50 | 15.6 / 30.5 |

*\* 7784 has no CEMS record at all, so only its 923 leg is scoreable; the model
also classes this cogen as `CC_REGULAR`, which is a taxonomy question of its own
and is noted rather than pursued.*

This is **not** a cycling problem: the model runs these plants 87–99 % of the
year while their own meters show 1–7 %. Their **bridge floor is zero** — the
nyiso-144 lay-up membership correction already removed it, because four of them
(Sterling, Batavia, Massena, Pinelawn) are on its exclusion list.

**That is the sharpest thing in this document.** The nyiso-144 correction removed
the *forcing* from these plants and left the *dispatch*: they no longer appear in
D-2 or D-4 at all — no floor, no floored hours, no conduct row — while the LP
still runs them at up to 225× their metered energy. The correction was right (a
floor on a mothballed boiler is indefensible), and its D-4 improvement is real,
but **the manufactured energy did not go away; it changed category from *forced*
to *economic*, where the legitimacy diagnostics do not look.**

---

## 4. WHAT WAS REFUTED, SO IT IS NOT RE-TRIED

### 4a. Fuel price — REFUTED, and the "obvious" repair would make it WORSE

The hypothesis was that the measured downstate delivered-gas re-grounding
(`nyiso_downstate_ct_gas_daily`) is scoped to **CT_PEAKER only**, leaving Long
Island CCs on the hub-basis path at a zone offset of ≤ 0 vs Capital_Hudson while
LI peakers pay a measured index reaching $100.87/MMBtu. The scope is real: 7314's
modelled gas is $5.06/MMBtu in 2025 against the LI delivered index's $7.25.

**But three Long Island gas plants report their actual delivered cost to EIA-923
Schedule 5 for all 36 months of 2023–2025**, and they settle it:

| $/MMBtu | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| **F923 LI peers** (2511 Barrett / 2516 Northport / 2517 Port Jefferson) | **3.70** | **2.83** | **4.74** |
| model, plant 7314 | 3.28 | 2.77 | 5.06 |
| LDC delivered index (Transco Z6 NY daily + KEDLI non-firm transport) | 3.71 | 4.08 | **7.24** |

The model tracks what these plants **actually paid** to −11 % / **−2 %** / +7 %.
The LDC index is **53 % above** it in 2025. Extending the CT re-grounding to the
LI CC/ST fleet would therefore have made the fuel price **materially worse** —
rule 14 `[R-ACCURATE]` cuts *against* the lever. **Refuted ex ante, no solve
spent.** The CT scope is not an unexamined limitation: interruptible peakers
really do buy on the daily non-firm index, and the steam/CC fleet demonstrably
does not.

### 4b. Heat rate — REFUTED

In the one staged 2025 month with hourly zonal actuals (Aug-2025, 745 h), 7314's
revealed turn-on threshold matches its modelled marginal cost to ~$1/MWh: the
median actual LONGIL LMP in the hours it was running is **$45.91** against a
modelled mc of **$47.07**, and its metered P(on) rises monotonically across price
bands (7.7 % below $20 → 100 % above $150).

### 4c. A missing outage — REFUTED, and forcing it would breach rule 13

Every one of 7314's 26 multi-day zero stretches in 2023–2025 sits in
`campd-unit-outages-layup-NYISO.csv` with `out_of_merit_share = 1.0`, and **zero**
land in the physical-outage file `campd-unit-outages-NYISO.csv` (whose only 7314
row is 2026-03). The classifier's own verdict is that these are **economic**
idles. Applying them as availability derates would pin the model to a measured
outcome — exactly what rule 13 `[R-MEASURED]` forbids.

---

## 5. A SECOND, INDEPENDENT DATA DEFECT FOUND WHILE DOING THIS

**The Astoria Energy campus is one CAMPD facility and two EIA plants, and the
benchmark follows CAMPD.**

* EIA-860/923 split **Astoria Energy (55375**, 595 MW, 2006, gens CT1/CT2/ST1)
  from **Astoria Energy II (57664**, 650 MW, 2011, gens CT3/CT4/ST2). EIA-923
  2023 net: 4,086.0 and 3,912.0 GWh.
* **CAMPD reports all four CTs under facilityId 55375** (CT1–CT4, each peaking at
  313 MW, plant peak 1,252 MW against a 595 MW nameplate) totalling 8,292.4 GWh.
* So the bench gives **55375 twice its true output** (`e_ann/c_ann` = 0.49 in
  both complete years) and gives **57664 no row at all** — 650 MW producing
  ~3.9–4.6 TWh a year that is invisible to D-1 / D-2 / D-4 and to the
  CAMPD-basis per-plant view.

On the correct 923 basis the model's Astoria I is **1.00× (2023) / 0.96× (2024)**
— i.e. essentially exact. Read on the CAMPD basis it looks like a 2× under-run.
**Any NYISO analysis that scores plant 55375 on the CAMPD bench is reading a
doubled target.**

This is the same *class* as the nyiso-141/142 Astoria stack duplication (plant
**8906**, `plant_emission_rates_v2`) but a **different, unrepaired instance**: a
campus-level facility-ID collision rather than a duplicated unit row. **Filed,
not fixed** — repairing it moves the benchmark for every NYISO run ever scored,
which nyiso-142's own record shows needs its own pre-registration.

---

## 6. THE QUEUE THIS LEAVES

1. **CC over-cycling (defect A)** — the largest object. Bethlehem alone: 262–302
   model starts a year against 5–7 real ones, 484–779 GWh of bridge floor, still
   0.34× at P1 in 2023. Any lever needs its own pre-registration; the shared
   detector's `startup_aware` screen is the obvious candidate **and carries the
   ERCOT-63 refusal**, so a NYISO test must first show the screen is not
   circular on NYISO's own duals.
2. **Merit-order inversion on mothballed small CCs (defect B)** — Sterling /
   Batavia / Massena / Allegany at 25×–225×. A duty-role **offer-shape** object:
   the mirror of the existing `ct_intermediate_split` / `st_gas_intermediate_split`
   / `cc_intermediate_split` family, all three of which flatten offers for
   HIGH-CF cohorts; NYISO needs the opposite. A new `ScenarioConfig` mechanism
   (rule 28c: base row + a cell in all six shards) with its own identification.
3. **A vintage guard for D-4's conduct rider**, mirroring C1's (§2).
4. **The Astoria campus attribution repair** (§5).

Items 1 and 2 are lane-sized modelling work. **They were not on NYISO's queue
before this session**, which is why the frontier assessment moves against
re-declaration (`ASSESSMENT-nyiso145-frontier-and-complete-2026-08-19.md`).

## 7. GOVERNANCE

* **No registrable run was produced.** The probe's solves reproduce the
  designated keeper's own recipe with zero `scenario_config` delta and write no
  bundle and no metrics; rule 15's object is a calibration *run*, and there is
  none. Nothing was withheld from the dashboard.
* **Rule 22**: 2023–2025 only, everywhere; freeze ACTIVE and unspent.
* **Rule 28(b)**: the one mechanism actually tested here — the class scope of
  `nyiso_downstate_ct_gas_daily` (§4a) — is stamped **rejected** in the NYISO
  shard with this document as its citation. No new `ScenarioConfig` field, so
  duty (c) is not triggered.
* **Rules 25 / 28(d)**: NYISO's shard and lane files only; every measured value
  is NYISO's own.

## 8. REPRODUCTION

```
python scripts/probes/_nyiso145_smallcc_overrun.py --year 2023 2024 2025
python scripts/calibration_verdict.py --run-id 2026-08-18-nyiso-144-layup-exclusion
```
