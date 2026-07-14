# MISO lane 3 — the North supply-curve depth / N–S separation, measured to its roots

**Date:** 2026-07-14. **Session:** `claude/miso-lane3-north-supply-nfd8um`.
**Lane:** lane 3 of the miso-64 handoff (the dominant remaining July-2025 piece;
`docs/DIAGNOSIS-miso-july2025-lmp-2026-07.md` §1(1), §6). Every number below is
from committed measured sources (the DA hub LMP record with MCC/MLC components,
CAMPD unit-level CEMS, EIA-860, the pbc RDT record, the MISO-AS cleared-reserve
parquets, SOM conduct rows) or a no-LP fleet reconstruction of the promoted
miso-64 keeper (`run_year(fleet_only=True)` on its `meta.json` — the same offer
prices the LP solves on). Nothing here is fit to a residual.

## 1. The separation is congestion, and it is one-sided

The DA hub record carries LMP = MEC + MCC + MLC. Averaging the four North hubs
(MINN/INDIANA/MICHIGAN/ILLINOIS) minus the four South hubs (ARKANSAS/TEXAS/
LOUISIANA/MS):

| year | annual ΔLMP | ΔMCC | ΔMLC | peak months |
|---|---|---|---|---|
| 2023 | +2.26 | +1.98 | +0.28 | Jan +5.9 |
| 2024 | +3.57 | +3.16 | +0.41 | Jul +9.0, Aug +5.4 |
| 2025 | +5.91 | +5.16 | +0.75 | Jun +10.9, **Jul +21.5**, Aug +13.5, Dec +9.9; Mar/May −2.9/−5.3 |

July 2025: **93 % congestion, 7 % losses**. The component structure is
one-sided — South hubs sit at MCC ≈ −$18…−$19 against a common MEC ≈ $57 while
the North hubs sit at MCC ≈ 0…+$4: the South was export-trapped below a system
marginal price set by the *North's* stack. The model prices the whole footprint
at the South's level (keeper July: all six zones within $0.35 of ~$40.2 vs
actual South ≈ $37, North ≈ $58.8). The model's spring-2025 S>N episodes
(Mar–May, South up $2–3) are directionally right — the missing half is
specifically **North-up** separation.

Losses are real but a $0.3–1.6 sideshow; a loss mechanism is not lane 3.

## 2. The corridor is exonerated; the North margin is the defect

The model's S→N corridor (RDT one-way pair + 92 % derate + $40/$500 TCDC tiers
+ RPE $200) binds 236 h in 2025 with ~$0.23 separation vs the measured DA
S→N record's 919 binding hours (mean |shadow| $13.1). The corridor never
separates because the *North's next MW after the free tier saturates is
priced on a ~25-GW-wide coal shelf*. From the keeper's own fleet arrays
(fossil-only, North zones, July 2025): 61.3 GW of July-mean supply below $45
(55.9 below $40), coal cap-weighted at $22.92 with its econ tranches topping
out ≈ $38 — so the stack cannot print a North premium whatever the corridor
does. Placing the *measured* July North fossil output (CEMS) on the model's
own stack: margin mean **$39.80** / p95 $52.60 vs actual North hub mean
**$58.35** / p95 $118.57. (Sanity: the keeper LP's July zonal price is
$40.26 — the reconstruction reproduces the solve.)

The diurnal shape localizes the miss precisely: overnight (h02–04) the model is
RIGHT (margin $31.7 vs actual $26.8–28.4 — reality's coal cycles economically
overnight and the model agrees); the entire gap is h09–21, where actual ramps
$45 → $122 (h18) while the model's margin tops out at $37.6. Event days are not
the whole story: excluding Jul 24/28/29 the actual July mean is still **$52.1**
— a ~$12 broad normal-day daytime gap, plus ~$6 carried by the three event days
(lane 2), matching the diagnosis §1 decomposition ($11 separation + $5
tightness + $3 tail).

The SOM competitiveness anchors (system price-cost markup 3.0 % 2023, output
gap "de minimis") say reality's July prices were **cost-reflective**: a
cost-based model with honest physical inputs should reproduce them. The wedge
is inputs, not conduct markup.

## 3. Where the phantom North supply came from — the stale outage extract

Measured July North coal (CEMS, unit-fuel basis): output mean 27.9 GW, p95
32.2, simultaneous max 33.1; sum of unit daily-maxima ("day-capability") mean
32.2 GW; sum of unit July-maxima 38.5 GW. The keeper's July-mean coal
availability: **33.6 GW** — ≈ the measured *best-hour* fleet coincidence, 5.7 GW
above measured mean output, of which ~4.3 GW is overnight economic cycling
(both sides agree) and **~2 GW is daytime phantom availability**.

Unit-day classification of July-2025 North coal against the committed overlays:
1.70 GW-mean of full-stop days covered by *neither* overlay file, 0.57 partial
plateaus, 2.33 + 0.38 correctly covered. Following the uncovered stops to the
deriver: seven ≥5-day sustained full stops (Ottumwa-1 7.3 d, Gibson-3, Labadie-2,
Baldwin-2, Cayuga-1, Cayuga-2, Sioux-1; span-CF < 0.002 — the full-stop
override's unconditional mechanical signature) are **absent from the committed
`campd-unit-outages-MISO.csv` yet emitted by its own frozen deriver re-run on
the committed CAMPD parquets**. The extract (PR #1820 vintage) was stale
against its own frozen code + data — a reproducibility defect, not a guard or
parameter question. Regenerating (zero flag/guard/constant changes):

- 2,924 → 4,418 rows; +≈1,550 GW-days *in each of 2023/2024/2025*;
- July North-coal outage coverage: 2023 5.32 → 7.03, 2024 4.63 → 6.26,
  2025 2.75 → **4.00 GW mean**;
- verified disjoint from the short-window companion (0 same-unit overlaps;
  std min 5.0 d, short max 4.9 d).

Fix + audit: commit `7b5c26fd`; re-solve = **miso-65**
(`scripts/probes/_miso65_outage_regen.py`, the miso-64 recipe VERBATIM — the
only delta is the corrected measured extract; caiso-78/nyiso-62 re-gate
precedent, LOYO-exempt as a year-invariant measured-input regeneration).

Stack effect (no-LP probe, scaling coal toward measured day-capability): July
margin mean $39.8 → ~$42.4, p95 $52.6 → $59.4, h18 $48.6 → $56.0 — the
afternoon margin crosses from the coal shelf into the CT band, which is where
the S→N corridor and the RPE start earning their separation (South margin
stays ≈ $37–40; spreads of $15–25 are exactly the measured binding-hour
$13–28 range).

**Blast radius:** the same staleness question applies to every other ISO's
unit-outage extract generated in the #1820 era (`campd-unit-outages-{CAISO,
NYISO,NEISO,PJM}.csv`, plant-level `campd-outages*.csv`). Not regenerated here
(each ISO re-gates its keeper in its own session, the nyiso-62 pattern); flagged
for the respective lanes.

## 4. What lane 3 is NOT (measured dead ends, do not re-walk)

- **Not the corridor representation.** RDT + TCDC + RPE mechanics are sound and
  already reproduce the 2023/24 anchors to the cent (miso-61); they under-bind
  in 2025 only because the North margin is too cheap (§2).
- **Not import shortage** (diagnosis §2 — the model *under*-imports).
- **Not CC/CT summer capacity**: model July-mean CC 9.51 GW vs measured p95
  9.19; CT 15.52 vs measured max 15.5 — the EIA-860 net-summer/class derates are
  on-basis.
- **Not a coal fuel-price error**: the F923-delivered shelf ($23–38) matches
  measured delivered PRB/ILB × HR; reality's $50–70 daytime marginal fuel is
  gas (ST_GAS/CT — real CTs ran 7.7 GW *mean* in July 2025 at ~40 % monthly CF,
  CEMS), reached only when the cheap shelf is honestly shallow.
- **Not an STR/reserve-product hole at current depth**: measured cleared STR is
  ~0.3–0.45 GW market-wide (MISO-AS parquets, all three regions); the
  subregional STR product (the "RPE-only" channel) is worth building only after
  the stack is honest enough for it to bind — it displaces too little to matter
  today.
- **Chronic never-runners** (ADM plants, Spiritwood, Prairie Creek 3, Filer
  City, Warrick 2 ≈ 0.8–1.0 GW): partially handled by the existing NET0-923
  net-zero-to-grid rule in the regenerated extract; Warrick 2 is EIA-860 Status
  **OS** — the fleet build carries **no Status filter** (SB 1,174 / OS 364 /
  OA 133 units nationally enter as fully available; MISO SB+OS fossil ≈ 2.7 GW,
  but North coal only ~0.19 GW). A gated 860-status availability treatment is a
  clean small follow-up, mostly *South* (Big Cajun 2, 658 MW OS).

## 5. Remaining July-2025 budget after miso-65 (expected)

With the corrected extract the July stack arithmetic leaves, in order:
(1) the CT/CC max-gen event unavailability (~4.1 GW at the Jul 28–29 peak) —
UNMODELED pending the max-gen/capacity-advisory registry intake (lane 2; owns
most of the ~$6 event-day contribution and the C3c tail);
(2) the sub-5-day uncovered stops (~0.85 GW-mean on CF≥0.55 units) — behind the
short channel's FROZEN in-merit guards (rule 23; re-derive only on new CAMPD);
(3) partial plateaus on running units (~0.3–0.6 GW-mean) — an admissible new
unit-level channel mirroring `derive_partial_outages.py` constants if ever
needed;
(4) the regulated-coal plan-following conduct complement (SOM Table 7: only
44–47 % of regulated coal starts offered economically) — lane 1's charter,
deferred per the standing sequencing;
(5) scarcity/ELMP depth once headroom is honest (the C3c lane).
