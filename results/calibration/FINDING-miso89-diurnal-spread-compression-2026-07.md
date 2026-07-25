# FINDING (miso-89, 2026-07-25) — C3b-2025 is diurnal-spread compression driven by a ~10 GW summer-peak under-derate, and every enumerated instrument for it is refuted or provably inert

**Context.** The one load-bearing FAIL holding `2026-07-25-miso-88-egrid-hr` at
NOT-YET: **C3b price shape, 2025 NRMSE 0.208** against a ≤0.20 veto. Scored from
committed artifacts and the model's own data path only — keeper `hourly/`
sidecars, the run payload's `lmpDeltaHr`, `bench/MISO/`,
`data/raw/_validation-source/actual_lmp_hourly_zonal_MISO.parquet`, and direct
calls into `data.outages` / `data.miso_outages` / `data.eia930.weather`.
**No LP re-solve.**

**Bottom line: this is a NO-BUILD finding.** The miss is real, located, and
sized. Every mechanism that could close it is already refuted, already
adjudicated data-blocked, or is measured here to be inert. The deliverable is a
determination question for the owner, not another probe.

---

## 1. It is not a 2025 miss and not a summer miss — it is diurnal-spread compression

Peak (HE16–18) minus night (HE01–03), body-censored at $200, model vs actual:

| season | 2023 m / a / ratio | 2024 m / a / ratio | 2025 m / a / ratio |
|---|---|---|---|
| winter   | 4.3 / 10.9 / **0.39** | 3.8 / 13.1 / **0.29** | 2.9 / 9.9 / **0.30** |
| shoulder | 6.0 / 18.2 / **0.33** | 5.5 / 15.9 / **0.35** | 5.8 / 16.2 / **0.36** |
| summer   | 11.7 / 26.3 / **0.45** | 14.2 / 30.1 / **0.47** | 12.2 / 32.7 / **0.37** |

The model reproduces **29–47 %** of the observed diurnal spread — every season,
every year. A standing structural property, not a 2025 event.

2025 fails the veto only because the **actual** summer spread widened
(26.3 → 30.1 → **32.7**) while the **model's stayed flat** (11.7 → 14.2 → 12.2).

Both ends miss, in opposite directions (Jun+Jul, body ≤ $200):

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| night HE01–03, model − actual | **+8.1** | **+5.6** | **+7.5** |
| peak HE16–18, model − actual | **−5.9** | **−11.9** | **−16.3** |

In 2023 the two errors nearly cancel in the monthly mean (June Δ = +0.4). By 2025
the peak-side error dominates, because C3b is **load-weighted**. The metric
changed; the model's error did not.

## 2. The model's supply stack is nearly flat

Median model price by thermal-dispatch ventile, 2025 summer:

| thermal dispatch | 33.8 GW | 48.1 | 56.1 | 65.3 | 72.9 |
|---|---|---|---|---|---|
| median model price | $28.6 | $33.3 | $36.2 | $41.8 | **$52.4** |

**$24 across 39 GW — ~0.6 $/GW average, 2.0 $/GW at the steepest ventile.** No
convexity at the top of the stack. This is why the spread cannot widen.

## 3. The real peak price is not a merit-order number

Implied marginal heat rate at summer peak (price ÷ the model's own MISO delivered
gas), body-censored:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| gas $/MMBtu (Jun/Jul) | 4.20 | 3.03 | 3.43 |
| model implied HR | 9.0 | 11.4 | 13.4 |
| **actual implied HR** | **10.4** | **15.3** | **18.1** |

At **18.1 MMBtu/MWh** the 2025 actual summer body peak sits far above the
marginal cost of the worst physical unit in MISO's fleet (legacy CT 11.5, ST_GAS
~13). The real summer-peak body price is **rent, not fuel × heat rate.** The
model tops out at 13.4 because P1 start-up amortization is the only thing it has
above physical cost.

## 4. MISO's scarcity apparatus is already built, already on, and never prices

Live in the keeper: `energy_reserve_coopt`, `miso_measured_reserve_requirements`
(market-wide **mean 2.64 / max 3.30 GW**, 2025), `miso_zonal_reserves`,
`miso_midwest_subregional_reserves`, `miso_reserve_pergen`, and
`_miso_design`'s demand curve ramping to `MISO_RESERVE_DEMAND_CURVE_MAX =
$3,500/MWh`.

Reserve shadow price in the committed hourlies: **0 / 6 / 2 hours out of 8760**
(2023 / 2024 / 2025). The curve never leaves its flat segment. **The mechanism is
starved, not missing** — so adding another price-formation mechanism would be a
second mechanism for a phenomenon that already has one (rule 17).

## 5. Why it is starved — and why no availability fix of plausible size arms it

Model fossil capability at Jun/Jul HE16–18, 2025 (from
`unit_outage_derate_factors` + `_iso_plant_capacity`, the maps the LP consumes):

| group | nameplate GW | available @ summer peak GW |
|---|---|---|
| COAL | 44.39 | 35.33 |
| CC_REGULAR | 28.31 | 24.38 |
| CT_PEAKER | 22.39 | 20.15 |
| ST_GAS | 11.61 | 7.65 |
| CC_CHP | 7.04 | 6.24 |
| CT_CHP | 2.63 | 2.36 |
| ST_CHP | 1.94 | 1.36 |
| **total fossil** | **118.29** | **97.46** |

Model fossil dispatch in those hours: **65.57 GW**. So the model carries
**31.9 GW of idle fossil headroom — 49 % above what it dispatches** — against a
**2.6 GW** reserve requirement. The solve's own log confirms the supply side:
*"availability-scaled 10-min deliverable ramp cap mean 37088 / min 32322 MW."*
**Reserve supply exceeds requirement by more than 12×.**

**This refutes the CT-availability hypothesis as a C3b remedy.** CT_PEAKER +
CT_CHP do carry a real coverage hole — **25.02 GW at 0.0 % CAMPD derate
coverage**, against 42–95 % for every other fossil class, with the statistical
fallback deliberately emptying summer of outages (`_availability_matrix`: POF in
shoulder months only, and only `_SUMMER_WEFOR_SHARE = 0.30` of WEFOR in summer,
so CT summer availability is 0.87–0.93 — its *highest* of the year). But even a
generous 15 % additional CT derate removes ~3.4 GW from 31.9 GW of headroom. The
reserve constraint stays slack by ~10×, the RDC still never prices, and at the
measured local stack slope (~2 $/GW) the merit-order effect is **~$4–6 of the
$16.3 gap**. The handoff's LANE B is a real representation defect and should be
fixed on its own merits (rule 11) — **it is not a C3b mechanism.**

## 6. Congestion cannot drive C3b, and is already adjudicated NO-BUILD

The model has essentially no binding internal congestion at summer peak. Zonal
means, Jun/Jul HE16–18, actual censored at $200:

| year | model spread (max−min) | actual spread |
|---|---|---|
| 2023 | **0.4** | 20.6 |
| 2024 | **2.3** | 26.6 |
| 2025 | **1.6** | 32.5 |

All four Midwest zones clear at an identical dual; only MISO-South separates. In
2025 MISO-South is nearly right (**−1.9**) while every Midwest zone misses by
**−18.8 to −24.3**.

**But congestion cannot be the C3b driver.** C3b scores the *load-weighted* ISO
mean, and a load-weighted-zero deviation pattern cannot move a load-weighted
mean. Verified as a diagnostic decomposition (not a proposed input): imposing the
**actual** hourly zonal deviation-from-ISO-mean on the model's own level leaves
NRMSE **identical to three decimals** — 0.081 / 0.129 / 0.206. The zonal-spread
defect is real and worth its own ledger entry; it is **not** this failure.

Independently, the congestion component is already adjudicated **NO-BUILD /
data-blocked-at-representation** (miso-78), with RO-3 zone refinement killed
empirically by the miso-79 probe (intra-LBA mass 88–99.7 %; even a ~12-zone model
converts only ~1.9–3.8 %). Not reopened here.

## 7. What the miss actually is: a ~10 GW summer-peak under-derate in 2025

Model fossil derate vs MISO's own published offline record, Jun/Jul HE16–18:

| year | model fossil derate | published MISO offline (all fuels, all causes) | gap |
|---|---|---|---|
| 2023 | 20.07 GW | 35.10 GW | 15.03 |
| 2024 | 19.07 GW | 33.27 GW | 14.21 |
| **2025** | **20.83 GW** | **45.59 GW** | **24.76** |
| YoY 24→25 | **+1.76** | **+12.32** | |

The offset is stable at ~14.6 GW in 2023/2024 — the expected non-fossil share
plus CT blindness — and then **breaks by ~10 GW in 2025**. This is a
difference-in-differences argument, so it does **not** require attributing the
published total across fuels (the miso-87 refutation is respected): it requires
only that the non-fossil share did not itself jump ~10 GW.

**And 2025 was not a hot year.** MISO zone-mean daily TMAX at summer peak:
**29.6 / 29.2 / 29.8 °C** (2023/24/25). So 2025's price spike occurred at normal
summer temperatures with cheap gas ($3.33–3.52) — it was a **supply-side**
tightening of roughly 12 GW that the model does not see. That is the whole of the
C3b failure, and it is consistent with every other measurement above.

## 8. Instrument enumeration — all closed

| candidate instrument | status |
|---|---|
| Published MISO total, uniform attribution | **REJECTED** — miso-85: over-derates CTs (manufactures a 138 h > $200 tail), under-derates coal (C1 COAL_PRB +28.3 TWh) |
| Cross-fuel attribution of that total | **REFUTED at charter** — miso-87, two independent grounds |
| Zone refinement / congestion representation | **NO-BUILD, data-blocked** — miso-78 §3, RO-3 empirically dead (miso-79) |
| `temp_dependent_derate` | **REJECTED** — refuted for the ERCOT gas fleet, 2026-07-09 |
| `gt_ambient_derate` | **PROVABLY INERT for MISO** — measured here: zone-mean TMAX exceeds the 35 °C reference in **24 h of 2023 and 0 h of 2024/2025**, and **0 h at summer peak in any year**. Removes **0 MW** in the failing window. Physically admissible, but cannot fire on this fleet |
| CT-specific measured availability | **NO SOURCE at CT grain** — CTs are CEMS-blind by construction; MISO publishes region × cause only |
| `unit_partial_outage_windows` (CAMPD ceiling plateaus) | **Premise does not hold** — the detector targets plants *without* unit-level data; MISO already carries 95.4 % coal / 90.1 % CC unit-level coverage |

**No enumerated instrument remains.** Continuing to probe would be searching for
a mechanism to hit a number, which is what rules 1/10 forbid.

## 9. Recommendation — a determination question, not a build

C3b-2025 is a **measurement gap of the same family as the already-ledgered C3c
tail**: the model cannot see ~10 GW of 2025 summer-peak unavailability, because
the only record of it is published at a grain (region × cause, fuel-blind) that
two prior charters proved cannot be attributed onto units without inventing the
attribution.

Three honest paths, all owner calls:

1. **Ledger it and take the determination.** Treat C3b-2025 as a documented,
   sized, instrument-blocked miss on the C3c template — with §7's
   difference-in-differences as its evidence — and re-gate MISO. This is the only
   path that does not require new external data.
2. **Charter a data ask.** The unblocking datum is MISO outage data at
   **unit or fuel grain** (a GADS-derived class series, or the IMM's unit-level
   outage appendix if obtainable). Rule 22 permits intake for training years
   under session-logged owner authorization. Until such a source exists this
   lane cannot be built honestly.
3. **Accept the miso-78 RO-2 program** (physics-derived reduced network). Note
   this addresses §6's zonal-spread defect, **not** §7 — per §6 it would not move
   C3b at all.

**Recommended: (1), with (2) opened as a standing data ask.** Path 3 should not
be chartered in the belief that it closes C3b; the decomposition in §6 shows it
does not.

## 10. What this finding does not license

* **Not** an offer adder, summer multiplier, or residual-tuned band (rules 1/10).
* **Not** widening the C3c ledger to absorb it — §3 shows the miss is a body
  phenomenon and §4 shows the tail apparatus is present, not absent. It needs its
  **own** ledger entry with its own evidence, or none.
* **Not** re-opening any of the §8 refutations without new external facts of the
  class their own charters specify.
* **Not** a fitted availability number. If no measured source resolves at the
  needed grain, the correct outcome is to report that and stop (rule 24).

## 11. Separately actionable, on their own merits (not C3b fixes)

* **CT measured-availability coverage hole** (§5): 25.02 GW at 0.0 % coverage
  while the statistical substitute is at its most generous in summer. A
  representation defect worth fixing under rule 11 — but pre-register that it
  moves C3b by ~$4–6 at most, and expect it to *worsen* C1 CT_PEAKER volume.
* **Zonal price separation** (§6): model spread $1.6 vs actual $32.5 at summer
  peak. Real, and currently unledgered; blocked by miso-78 unless RO-2 is
  chartered.
