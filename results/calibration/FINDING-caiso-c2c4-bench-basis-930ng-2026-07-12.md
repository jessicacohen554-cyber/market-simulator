# FINDING — CAISO C2/C4 bench basis: the CISO EIA-930 NG cell is corrupted (a noon-peaked, solar-shaped block grows in it from ~2024-05), and the G-21 combined reconcile scales the WHOLE CAISO fossil class actual up to that cell (×1.104 / ×1.211 / ×1.444) — the C2-2025 print, part of the C1 actual, and the 2024/25 C4 gas r are scoring benchmark corruption (2026-07-12)

**Session Task 2** (the 2025 bench-basis rework filed in the caiso-76 FINDING §4
and sharpened in caiso-77 §2/§5). The task's entry question — can main's G-21b
scorer-layer CEMS anchor (50dbb54) be extended to close the CAISO C2-2025
−7.6 % print — is answered in §1; the investigation then found the actual
defect, which is larger than the question. All numbers below are reproducible
from committed repo data (bench parts, CAMPD parquet, `eia-930-hourly/CISO`,
`_eia923_frame`).

## 1. The entry question: G-21b extension is structurally INERT for CAISO

G-21b corrects only the preliminary-vintage family fallback's gas/coal SPLIT:
an incomplete gas family gates against "930 COMBINED fossil minus the coal
anchor". CAISO coal is ~0.01 TWh — the subtraction is a no-op, so the gas
family still gates against (a deflation of) the raw 930 NG cell. Extending the
split anchor cannot move the −7.6 % print; the post-G-21b rescore already
showed exactly that (caiso-77 FINDING §5 port note). The defect is in the
LEVEL authority itself, below.

## 2. Discovery — the committed classFull is not EIA-923: it is 923 scaled to the 930 NG cell

The committed bench `classFull` (the C1 per-class actual and the C2 family
membership) is the 923 class total, BTM-removed, then passed through
`render_calibration_html.reconcile_vintage_classes` (G-21): when the combined
fossil 923 total sits outside ±3 % of the EIA-930 combined fossil cell (after
the geo/biomass fold-in deflation), EVERY fossil class is scaled by the same
factor to the 930 level. For CAISO the factor fires in **every year, including
the complete vintages**, and grows:

| year | fresh `_eia923_frame` CC_REGULAR | committed classFull CC_REGULAR | implied scale (all non-CHP gas classes) |
|---|---|---|---|
| 2023 | 51.86 | 57.26 | ×1.104 |
| 2024 | 45.99 | 55.71 | ×1.211 |
| 2025 | 37.37 (prelim) | 53.98 | ×1.444 |

(CHP classes carry the same scale on their BTM-netted values.) So +5.4 / +9.7 /
+16.6 TWh of CC_REGULAR "actual" in the C1/C2 gates is not any plant's
generation — it is the 923→930 wedge smeared pro-rata across the in-BA
classes. The reconcile's stated rationale (preliminary under-count; residual
CHP/BTM booking) cannot apply to 2023/2024: those vintages are complete, and
the wedge GREW +5 TWh between them.

## 3. What the wedge actually is — the CISO 930 NG cell carries a growing noon-peaked block that no gas fleet produced

Decomposition of the 930 NG cell (fold-in-deflated, i.e. the reconcile's
target) against measured populations:

| year | 930 NG (raw) | geo+biomass fold-in | CEMS bench gas (gross) | non-CEMS CISO cogens (923) | unexplained |
|---|---|---|---|---|---|
| 2023 | 87.74 | 13.79 | 62.91 | 14.09 | ≈ 0 |
| 2024 | 85.39 | 13.59 | 55.47 | 13.58 | **+4.2** |
| 2025 | 79.02 | 10.50 | 46.09 | ~13.5 (prelim) | **+7.9** |

The non-CEMS cogen population (Watson, Crockett, El Segundo Cogen, refinery/
oilfield CHP — 40 plants) is FLAT (14.09 → 13.58 TWh), and CAMPD coverage is
stable (84 → 83 → 82 bench gas plants, −0.3 TWh explained). The unexplained
block's SHAPE identifies it: the hourly wedge (930 NG minus CEMS bench gas,
local-time aligned) is noon-peaked and grows exactly like the solar build-out —
mean hod profile peaks h10-14 at 4.4 → 5.9 → **7.8 GW** (2023/24/25) over a
~2-3 GW flat overnight base (the cogens + fold-in, which balance). And the raw
CISO 930 NG series itself, Jun-Aug **2025**, RISES from 8.1 GW at h07 to
**13.2 GW at noon** then falls to 9.6 GW at h17 — the exact inverse of the
physically-known duck curve (CEMS: real CAISO gas bottoms midday at ~2-4 GW).
Monthly onset: the noon-minus-dawn NG delta flips positive around **2024-05**
(+2.6 GW) and reaches +4.5..4.7 GW in summer 2025. A BA fuel-mix submission
defect (solar-shaped energy misallocated into NG: NG) is the only reading
consistent with all of CEMS, 923 and the shape; no gas fleet in California
runs noon-peaked.

Blast-radius note: the same noon check on MISO/PJM/NYIS/ISNE/ERCO is
inconclusive (positive noon deltas are plausible without deep solar; their
G-21b split errors are separately measured). The corruption evidence here is
CISO-specific — it rests on the CEMS hourly cross-check.

## 4. What is scored against this

- **C2-2025 (−7.6 % FAIL, "MODEL MISS")**: the actual (68.53) is the corrupted
  930 cell, fold-in-deflated. On the measured populations (CEMS 46.09 gross +
  flat cogen block) the 2025 grid-gas actual is ~57-60 TWh — the model (63.32)
  is not under it. The caiso-77 §5 adjudication ("bench-basis artifact, not a
  mechanism regression") now has its concrete mechanism, and the same posture
  pre-registered for caiso-78 is justified.
- **C1 CC_REGULAR, ALL years**: the actual is inflated ×1.104/×1.211/×1.444 —
  so the printed +4.50 TWh (2023) UNDERSTATES the true model CC-over
  (CEMS same-fleet: +5.74), and the caiso-77 "C1-2024 clears" reading is
  basis-flattered. The caiso-78 plant-level target table (CEMS same-fleet) is
  unaffected — it never touches classFull.
- **C4 gas r (0.887 → 0.834 → 0.590)**: `fuelRows[gas].r` is the Pearson of
  model hourly gas vs the RAW 930 NG hourly series. From 2024-05 that series
  is progressively noon-corrupted, so the 2024/25 r degradation substantially
  measures the benchmark, not the model. (2023 r 0.887 predates the onset and
  stands.)
- **C5a-2025 CO₂**: the bench CO2 actual derives from the preliminary-923
  class generation (caiso-76 FINDING §4) — same basis family, same rework.

## 5. Proposed rework (design, for owner sign-off — scorer/bench layer, no re-solve)

For CAISO the 930 NG cell must stop being the fossil LEVEL and SHAPE
authority; the measured replacement exists in-repo with complete coverage:

1. **C2 family / classFull level (CAISO)**: cap the combined reconcile with a
   CEMS cross-check — the fossil actual is `CEMS bench-gas (hourly-integrated,
   every grid CC/CT/ST ≥25 MW) × the gross→net factor + the 923 non-CEMS cogen
   block` (complete vintages: as booked; preliminary vintage: prior-vintage
   cogen block carried, CAMPD backfill for CEMS plants as today). Equivalent
   framing: the "CAMPD-per-class target" refinement already filed as the G-21
   follow-up (docs/handoffs/pjm-cc-overrun-benchmark-basis-g21-2026-07.md §6),
   applied first to the ISO where the 930 cell is demonstrably corrupt.
2. **C4 gas actual (CAISO)**: CEMS fleet hourly + the flat cogen block instead
   of 930 NG hourly, from the onset vintage (≥2024; 2023 may keep 930 for
   continuity — the two agree there).
3. **C5a-2025**: rebuild the CO2 actual on the same complete-coverage basis
   (or eGRID 2025 when it lands), per the caiso-76 filing.
4. PJM/MISO/NYISO/NEISO keep the G-21/G-21b behaviour unchanged — no evidence
   of a corrupted NG cell there, and their reconcile rationale (split repair)
   still holds.

Governance: this is a benchmark-data correction citing a demonstrated source
defect (rule 23's "re-derive only when source data updates" — here the source
is shown wrong against two independent measured sources), NOT a residual-chase:
the correction moves C1/C2 actuals AGAINST the model in 2023/24 (the true CC
over-run is larger) while retiring the fabricated 2025 under-print and the
corrupted C4 comparator. It changes scored actuals for keepers, so it requires
owner sign-off before bench parts are regenerated and keepers re-scored; until
then C2-2025/C4-2024/25 prints carry the adjudication note (caiso-77 §5
precedent). Filed as the concrete design for the open "2025 bench basis
rework" lane.
