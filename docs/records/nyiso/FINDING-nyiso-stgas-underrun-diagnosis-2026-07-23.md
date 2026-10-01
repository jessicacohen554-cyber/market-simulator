# FINDING — NYISO ST_GAS under-generation is a LOAD-POCKET MUST-RUN gap, not an economic heat-rate error; no legitimate NYISO-contained lever closes it. Keeper stays `nyiso-70` (2026-07-23)

**Status: DIAGNOSTIC ONLY. Keeper stays `nyiso-70` (`2026-07-22-nyiso-70-scr-edrp`,
NOT-YET); no keeper change, no new bundle, no registration.** This session took the
2026-07-23 handoff's one real forward lever — NYISO under-generates steam-gas (ST_GAS)
by 15–29% vs the C1 bench, growing every year — and, per the handoff's DIAGNOSTIC-FIRST
instruction, determined **whether the under-run is ECONOMIC (inflated efficient-tranche
HR → clean rule-11 fix) or MUST-RUN (in-city local reliability → rule-23-sensitive).**
The verdict is **MUST-RUN**, specifically **Long Island / NYC in-city load-pocket local
reliability**, and there is **no rule-11 economic HR fix and no clean grounded hourly
must-run obligation** to close it without residual-fitting (rule 23) or blowing the C8
forced-energy budget. `nyiso-70` is held as the most structurally-faithful NOT-YET keeper
(rule 1).

The decisive datum (handoff): model ST_GAS = 7.40 / 8.58 / 11.37 TWh vs C1 bench 8.70 /
11.07 / 16.00 TWh (2023/24/25), i.e. −15% / −22% / −29%, growing. Its **scored**
consequence is the **C7 diurnal-shape FAIL** (ST_GAS off-peak CV 0.483 < 0.5 in 2023),
not C1 (which PASSES — ST_GAS is a small share of ISO generation, so the under-run is
inside the C1 band).

---

## 1. Step 1(a) — the efficient tranche is the EIA-860 DESIGN heat rate, NOT inflated

The model's ST_GAS per-plant `Plant_Avg_HR_MMBtu_MWh` is **byte-identical to the EIA-860
`heat_rate` field** (`eia860_generators.parquet`), to 3 decimals:

| plant (zone) | model `Plant_Avg_HR` | EIA-860 design HR | CEMS operating HR (p50, load>20MW) |
|---|--:|--:|--:|
| Danskammer (CH) | 11.282 | 11.282 | 10.34 |
| Arthur Kill (NYC) | 11.268 | 11.268 | 10.9 |
| Ravenswood (NYC) | 9.500* | 8.800 | 11.4 |
| E F Barrett (LI) | 11.076 | 11.076 | 9.9 |
| Northport (LI) | 10.887 | 10.887 | 10.1 |
| Port Jefferson (LI) | 12.015 | 12.015 | 11.5 |
| Bowline (CH) | 10.186 | 10.186 | 9.6 |
| Roseton (CH) | 10.950 | 10.950 | 10.1 |
| Astoria (NYC) | 11.949 | 11.949 | **5.6 (CEMS artifact — impossible for a 1954–62 steam turbine; excluded)** |

*Ravenswood is a mixed CC+ST facility; its bin HR is clipped up from the 8.80 design.

The keeper's offer curve (`offer_curve_by_group["ST_GAS"]`) prices the tranches at
`committed 1.05× / econ_low 1.08× / econ_high 1.13× / peak 4.20×` **the design HR**. So
the efficient/committed tranche is **1.05–1.13 × EIA-860 design ≈ design ≈ the CEMS
operating HR** (per-plant CEMS 9.6–11.5, matching design ex the Astoria artifact). This is
NOT the pathology the handoff flagged (a cycling-inflated CEMS annual-average applied
where a full-load design HR belongs) — the base **is** the design HR, and the multipliers
are a normal offer-curve rise. **Per the handoff's own test ("efficient tranche ≈ design →
MUST-RUN, not economic"), there is no clean rule-11 HR correction to make.**

## 2. Step 1(b) — the gap is UNECONOMIC and LOAD-POCKET-concentrated, not a pricing error

Profiling the bench ST_GAS (CAMPD `NY_<year>.parquet`, gas-steam units) by hour and price:

- **Bench runs steam across all price bands, including deeply out-of-merit:** 13–16 % of
  annual ST_GAS energy runs when RT price is **below its own p25** (~$21–33), where HR-11
  steam (mc $31–52) loses money on energy — a must-run signature.
- **The volume gap is EVENING-concentrated** (economic hours), not overnight: 2023 model
  vs bench mean MW is 726 vs 770 overnight (gap 44) but **1003 vs 1441 evening (gap 438)**;
  2025 is 1051 vs 1251 overnight and **1631 vs 2257 evening**. The p25 reliability floor
  roughly captures the overnight must-run level; the miss is the evening.
- **The model runs LESS steam at a HIGHER price than reality.** Model on-peak LMP ($40) is
  already above reality's load-weighted ($34.6, C3a finding); model Long-Island evening
  price is **$47** (elevated above NYC $41 / upstate $38 — the model *is* pricing the load
  pocket), yet it runs less LI steam than reality. If the price is already ≥ reality's,
  **no price/HR correction adds the missing volume** — the missing steam is out-of-merit.
- **The missing volume is Long Island / NYC in-city steam, growing fastest on LI.**
  Bench per-plant (2023→2025 TWh): **Northport (LI) 2.56 → 4.31** (the single largest and
  fastest-growing ST_GAS unit), Arthur Kill (NYC) 1.12 → 2.16, Astoria (NYC) 1.55 → 2.67,
  Bowline (CH) 0.98 → 2.06. Long Island's steam sits on expensive **Iroquois Z2 gas
  ($3.28/MMBtu, 2023)** and high design HR (Northport 10.89): its econ-tranche
  **mc ≈ $45–51/MWh**, which is **$5–11 out-of-merit even at LI's elevated $47 evening
  price.** The model correctly declines to dispatch it economically; reality runs it for
  **K-zone (Long Island) load-pocket local reliability.** NYC steam (Astoria/Arthur Kill,
  mc $36–38 on cheaper Transco Z6 gas $1.94) is marginal in the evening and the model runs
  more of it, closer to bench.

**Verdict: MUST-RUN (Long Island + NYC in-city load-pocket reliability), not economic.**
The heat rate is the design/measured basis, the zonal gas basis is measured (NYISO SOM
Fig A-6), and the clearing price is already correct-to-high. Reality dispatches
out-of-merit downstate steam for local reliability that the full-SRMC LP cannot represent
economically.

## 3. The reliability floor is PINNED — it cannot close the gap either way

The NYC/LI ST_GAS reliability floor (`reliability_floor_coeffs_NYISO.csv`) is already a
temperature-dependent floor with an evening ramp (window 14–21), derived at **p25 /
evening-p25 of when-available CF** — a *minimum*. Its scored consequences bracket the
lever from both sides:

| move | C1 volume | C7 shape (D-1 cv_ratio 2023) | verdict |
|---|---|---|---|
| **floor DOWN** (nyiso-71, overnight-p25) | **breaks** (ST_GAS → 6.93/7.92/10.83) | fixes (→ PASS) | rejected — the flat floor is a needed prop |
| keeper nyiso-70 | PASS (7.40/8.58/11.37) | **FAIL (0.483)** | held |
| **floor UP** (this probe, NYC/LI base+evening ↑) | improves toward bench (7.40 → 8.34) | **worsens (0.483 → 0.422)** | rejected — see below |

**Floor-up probe (2023 replay, throwaway; NYC ST_GAS base 0.496→0.62 & evening 0.533→0.72,
LI base 0.436→0.58 & evening 0.572→0.78 & cap 0.815→0.95; CSV reverted after load):** the
extra ~0.94 TWh lands **flat/overnight** (overnight 726→838, evening only 1003→1116 vs
bench 1441), so it **worsens C7** (D-1 cv_ratio 0.483 → **0.422**, still FAIL) and leaves
C3a untouched (off-peak price $32→$31.6, still +$12 vs actual ~$19.6). The floor is the
wrong instrument: it can only add **flat** volume, not the **evening-shaped** volume
reality has.

Independently, D-2 already attributes **26–40 % of ST_GAS to the reliability_floor**
(2024 = 39.3 %, over the 30 % merchant cap; C8 PASSES only via the rubric-v2.2
grounded-above-budget escalation on D-1 provenance). Raising the floor pushes further over
the cap. **So the floor is pinned: down breaks C1, up worsens C7 (and risks C8); neither
closes C3a.**

## 4. Why there is no legitimate lever left

The p25-floor methodology assumes economics backfill above the minimum. That holds for
most classes, but **for uneconomic, reliability-committed in-city steam the economic
backfill never comes** (LI steam is out-of-merit even at the elevated LI evening price), so
floor + economics structurally under-delivers vs reality. Closing it faithfully would
require a **grounded hourly in-city/load-pocket must-run OBLIGATION** (a published NYC/LI
minimum in-city generation requirement) — a *requirement*, not the observed CF. No such
hourly obligation dataset exists in the repo; the reliability_floor coeffs are derived from
CAMPD CF percentiles. Raising the floor to the **observed** level is fitting to the bench
volume — exactly the rule-23 residual-fit the handoff forbids — and it blows the C8
forced-energy budget besides. There is **no rule-11 (HR) fix** because the HR is already
the design/measured basis.

## 5. Recommendation

- **Keeper unchanged: `nyiso-70` remains, NOT-YET.** The ST_GAS under-run is a **structural
  load-pocket must-run gap** of the full-SRMC LP + p25-floor methodology, concentrated on
  Long Island (Iroquois gas + high-HR steam, out-of-merit) and growing. It is **not** an
  economic heat-rate error (HR = EIA-860 design = CEMS operating HR) and **not** a pricing
  error (the model already prices the LI load pocket above the steam's mc).
- **Do NOT** correct ST_GAS heat rates (already design basis, rule 11 n/a), **do NOT** raise
  the reliability floor to the bench volume (rule-23 residual-fit + C8 breach + C7
  regression, empirically confirmed), and **do NOT** lower it (nyiso-71: breaks C1).
- The scored C7 FAIL (2023 ST_GAS off-peak flatness) is the same must-run root: the model
  leans on the flat floor because downstate steam rarely clears economically. It cannot be
  fixed by the floor without a shape regression, and cannot be fixed by economics because
  the steam is out-of-merit.
- **The only structurally-honest forward lever is a grounded in-city/load-pocket
  reliability-commitment mechanism** driven by a published NYISO NYC (Zone J) / Long Island
  (Zone K) minimum in-city generation requirement — a new measured-input mechanism (rule
  13-admissible if the requirement regenerates from forward drivers), **not** a floor-level
  bump and **not** an HR change. Absent that dataset, hold `nyiso-70`. This matches the
  handoff's REALITY CHECK: even a perfect ST_GAS fix leaves C3a FAIL 2023 (the separate
  below-SRMC trough limit), so the determination stays NOT-YET; the win here is the
  **verdict** (economic ruled out, must-run localized to the LI/NYC load pockets), not a
  number.

## Reproduction

```
# read-only diagnostics off the committed keeper sidecars + CAMPD + EIA-860:
#   EIA-860 design HR vs Plant_Avg_HR:  data/raw/eia-860/eia860_generators.parquet
#   bench ST_GAS by plant/hour/price:   data/raw/campd-unit-level/NY_<year>.parquet
#   model ST_GAS + zonal price:         results/calibration/nyiso70_scr_edrp_reserve/hourly/{class_hourly,system}_<year>.parquet
#   zonal gas basis:                    data/raw/nyiso_zonal_gas_hub.csv
# floor-up disqualification probe (2023, throwaway; CSV reverted after the solve loads it):
#   edit reliability_floor_coeffs_NYISO.csv NYC/LI ST_GAS floor_pct up, then:
python scripts/replay_keeper.py results/calibration/nyiso70_scr_edrp_reserve \
  --out-dir /tmp/ab_floorup --years 2023 --note "probe: raise NYC+LI ST_GAS floor"
#   -> ST_GAS 7.40→8.34 TWh (flat overnight); D-1 cv_ratio 0.483→0.422 (C7 worse); C3a unmoved.
```
