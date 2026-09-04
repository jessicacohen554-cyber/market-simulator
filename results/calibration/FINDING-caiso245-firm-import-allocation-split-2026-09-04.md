# FINDING — caiso-245: the published RA-import capability ALLOCATIONS do NOT carry the north over-import — LSEs hold 48 / 46 / 45 % of their import capability north, the same share the MIC gives — so the pre-registered stop rule fired, the re-split arm was NOT built, and the object moves from "the split" to "RA import CAPABILITY forced as ENERGY". December's price slab is common to import- and domestic-marginal hours. ZERO SOLVES.

**Session caiso-245, 2026-09-04. Branch `claude/caiso-244-backcast-calibration-jag23e`.**
Pre-registered in `PRECOMMIT-caiso245-firm-import-allocation-split-2026-09-04.md`
(pushed `51c9c628` BEFORE the key was computed). **No LP, no solve, no
`ScenarioConfig` field, nothing armed, no run registered, no verdict moved.**
Keeper **`2026-09-04-caiso-243-b1-f923` UNCHANGED**, NOT-YET, C3a the sole
load-bearing FAIL (+3.9 / +12.3 / +14.4 %). No `complete`/`final` marker;
freeze ACTIVE; 2023–2025 only.

---

## §1 — HEADLINE

1. **The key was measured from CAISO's own published holdings and it
   REFUTES form (i).** LSEs hold **48.3 / 45.5 / 45.1 %** of their RA import
   capability on the north branch groups (PACI/Malin 2,426 → 1,832 → 1,669 MW,
   NOB 1,559 → 1,622 → 1,413, Tracy 500 693 → 765 → 844) against the MIC
   capability share **46.2 / 46.2 / 46.4 %** — within **2.1 / −0.7 / −1.3
   points**. The PRECOMMIT §0.4 stop rule (5 points) fires in every year;
   P-1 (≤ 36 %) is FALSIFIED. **The arm was not built. No solve was spent.**
2. **The north holders USE their capability on RA plans MORE than the south's
   do** — 79 / 79 / 48 % of north branch-group rows flagged "used all
   capability" vs 28 / 28 / 28 % south (P-3 FALSIFIED as written). RA import
   capability is held AND shown north in MIC proportion; the corridor's
   measured energy is −0.55 / 2.06 / 4.73 TWh net. **Capability ≠ energy is
   the object; the split key is not.**
3. **Total held allocation is 11.7 / 11.5 / 11.2 GW — 5.1 / 3.4 / 3.3× the DMM
   RA-import capacity (2,323 / 3,371 / 3,371 MW)** the model forces as
   energy (P-2 holds). The DMM figure is the average SHOWN RA import; the
   holdings are the rights behind it.
4. **The data is intaken through the contract** (`ra-import-allocations`, 739
   holdings over 3 years; schema, registry lib, curate, test, dictionary) so
   the refutation is reproducible from committed bytes, and the datatype is
   available to whatever form the owner chooses next. Intake-only.
5. **Queue item B, zero LP: December's price slab is NOT an import-marginal
   phenomenon either.** In Dec-2025 the model's load-weighted price is
   **44.57 $/MWh in the 182 hours an import row sets the landing-zone price
   and 44.04 in the other 562**, against an actual RT of 34.97 — the +9.2
   slab is common to both regimes. And the marginal import row in **69 / 101**
   December hours of 2024 / 2025 is **`DSW_solar_PV` at its FITTED $48** —
   the caiso-151 elastic slice puts the fitted firm price on the SP15 price
   path in one December hour of seven.

---

## §2 — G-KEY, MEASURED (`_caiso245_allocation_split.json`)

| year | held total MW | north MW | **held north share** | MIC north share | Δ pts | held ÷ DMM | used-all north / south |
|---|--:|--:|--:|--:|--:|--:|--:|
| 2023 | 11,740.6 | 5,675.1 | **48.3 %** | 46.2 % | +2.1 | 5.05 | 79.3 / 28.0 % |
| 2024 | 11,512.5 | 5,242.0 | **45.5 %** | 46.2 % | −0.7 | 3.42 | 79.3 / 28.0 % |
| 2025 | 11,232.8 | 5,064.0 | **45.1 %** | 46.4 % | −1.3 | 3.33 | 47.8 / 28.0 % |

Corridor map: branch-group stem → the MIC north list of the
`IMPORT_TRANCHES_BY_YEAR` comment (the same geography as `CAISO_CORRIDOR_DIBA`),
unknown stem = hard error; every one of the 46 codes mapped. The "used all"
diagnostic reads the companion workbook at branch-group grain (its single
code column interleaves LSE IDs, which are dropped and counted: 0 unmapped
after the LSE rows are removed); it is a per-row flag, never a MW weight.

**Reading.** The MIC capability share IS, to two points, how LSEs hold RA
import capability. Nothing in the allocation record moves the north block
south. What the record says instead is that CA LSEs hold ~5 GW of RA import
rights on the Northwest interties and largely show them on RA plans, while
the interties carried almost no net energy into CAISO in 2023–2025 (BPAT
1.14 / 2.14 / 3.00 TWh net; the corridor −0.55 / 2.06 / 4.73). An RA import
is a capacity product; the energy behind it is scheduled economically, and
2023–2025 were years in which the Northwest had less to sell. **The model's
self-schedule energy floor — DMM capacity × measured total-system shape,
clipped at a SYSTEM-level price-insensitive ceiling that is allocated to the
corridors pro rata by that same shaped capability — is what puts 7.7–10 TWh
of forced energy on COI.** The defect is the floor's ENERGY basis and its
corridor allocation of a system-level ceiling, not its capability split.

---

## §3 — QUEUE ITEM B: DECEMBER (`_caiso245_december_carrier.json`)

Every December hour split by what sets the model's landing-zone price
(caiso-244's dual-merit reconstruction on the committed P1 duals):

| Dec | model lw | actual RT lw | actual DA lw | import-marginal hours | model lw, import-marginal | model lw, domestic-marginal | marginal import rows |
|---|--:|--:|--:|--:|--:|--:|---|
| 2023 | 51.08 | 47.05 | 49.30 | 135 (18 %) | 47.04 | 51.98 | overnight_clean 96, surplus_clean 30, DSW_CCGT 5, PNW_midC 4 |
| 2024 | 46.83 | 42.20 | 42.72 | 152 (20 %) | 46.16 | 47.00 | **DSW_solar_PV 69**, overnight_clean 46, DSW_CCGT 26, … |
| 2025 | 44.17 | 34.97 | 38.37 | 182 (24 %) | 44.57 | 44.04 | **DSW_solar_PV 101**, DSW_CCGT 28, overnight_clean 23, PNW_midC 16, … |

Three readings. **(a)** The Dec-2025 slab is flat across the two regimes
(44.6 vs 44.0): whatever sets the price, the model clears ~$9 above the RT
actual — a LEVEL common to gas-marginal and hub-marginal hours, which is
consistent with caiso-232's "slab in all 24 hours" and rules out any single
import row as the carrier. **(b)** The fitted **$48 `DSW_solar_PV` price is
the marginal offer in 101 Dec-2025 hours** (14 % of the month) — the third
signature this week that the two firm prices are live (caiso-244 §3.5
bound-setting; here margin-setting), all of it inside the caiso-151 clip's
elastic slice. It sets a price ABOVE the actual mean in those hours. **(c)**
The import-marginal share is not December-specific (24.5 % vs an annual
23.0 %); December is not special on the import side. The month-by-month
model−actual RT series (2025: −1.0, +1.2, −0.6, +5.1, +3.9, +4.2, +4.1, +1.8,
+5.8, +7.7, +3.1, **+9.2**) shows the slab growing through the autumn — the
2025 Sep–Nov overlay gap (caiso-243 §7.4, 9/12 hub months) and the
D3 55077 row sit exactly there and remain the open asks.

---

## §4 — PREDICTIONS, SCORED

| # | prediction | verdict |
|---|---|---|
| P-1 | held north share ≤ 36 % every year | **FALSIFIED** — 48.3 / 45.5 / 45.1 %; stop rule fires |
| P-2 | held total ≥ DMM level every year | **HOLDS** — 5.05 / 3.42 / 3.33× |
| P-3 | north "used all" share ≤ south's | **FALSIFIED** — 79 / 79 / 48 % vs 28 % |
| P-4 … P-10 | arm outcomes | **UNSCORABLE — the arm was not built** (§0.4 stop rule); registered, unspent, quoted as nothing |

The one prediction that carried the session's design (P-1) is the one that
fell, and it fell on the source the session itself recommended.

---

## §5 — DISCLOSURES AGAINST INTEREST

1. **I expected the allocation key to carry the excess and it does not.**
   caiso-244 §5 ranked form (i) first on admissibility grounds; that ranking
   was right on admissibility and wrong on mechanism. The record says the
   MIC share was a fair proxy for holdings all along.
2. **The intake is committed although no mechanism consumes it.** Rule 13's
   "data prep is unrestricted" and the lane's "every number from committed
   bytes" standard both point the same way; the schema header says
   intake-only in its first paragraph.
3. **The "used all capability" workbook is read at a grain its layout does
   not guarantee** (LSE and branch-group codes interleaved in one column). It
   is a diagnostic in this finding and is deliberately NOT curated.
4. **The December decomposition compares an hourly model series against a
   MONTHLY actual** (the committed bench carries monthly RT/DA means); the
   bucket split is of the model's own mean, not an hourly residual.
5. **One raw print outside the window** (PRECOMMIT-caiso244 §0.2) is quoted
   again in §2 for the same single purpose — naming the 2023 regime break
   caiso-235 already published.

---

## §6 — WHAT THE OBJECT IS NOW, AND THE FORMS LEFT (owner decision; none chosen)

The north excess is the firm block's **energy basis**: a capacity product
(DMM RA import MW) shaped by the measured total-system revealed base and
FLOORED, with the caiso-151 price-insensitive ceiling — a SYSTEM-level series
from CAISO's own DAM intertie bids — allocated to corridors pro rata by that
shaped capability (i.e. by the MIC share).

| form | what | admissibility | status |
|---|---|---|---|
| **(ii)** per-intertie price-insensitive ceiling | allocate the caiso-151 ceiling by the measured self-scheduled / ≤ $0 import bids **per intertie**, not pro rata by capability | the same OASIS PUB_DAM_GRP record caiso-151 used, at intertie grain, IF the intertie ids are exposed; the `caiso-public-bids` corpus is a BLOAT-S2 conversion (README only) — **re-fetch is the only route** | the measured answer to §2's reading; a data-intake session |
| **(iv)** capability-not-floor | drop the north row's floor to the measured price-insensitive north bids (which (ii) supplies) and leave the remainder price-elastic at the hub | needs (ii) | follows (ii) |
| (iii) EIA-930 corridor energy share | re-key by measured corridor flows | rule-13 tension (caiso-244 §5) — unchanged, weakest | not recommended |
| **the two fitted firm prices** ($28 / $48) | now measured margin-setting in 69 / 101 December hours and bound-setting on 0.7–3.3 TWh/yr | a G-26 honesty item; the caiso-83/86 Q-Q derivation failed its LOYO gate (30.5 %) | an owner ask, not a lever |

**Recommendation, stated and not taken:** (ii) as a data-intake session
(OASIS PUB_DAM_GRP intertie bids, 2023–2025), then a pre-registered
single-flag arm that allocates the existing caiso-151 ceiling by intertie.
Direction on C3a: favourable on both zones (caiso-215) — the standing
hazard; C3a excluded from any promotion basis.

---

## §7 — DO-NOT-REDO ADDS

1. **Never re-key the firm block's corridor split on RA import capability
   holdings** — measured within 2.1 points of the MIC share in every year.
2. **Never attribute the December slab to import-marginal hours** — the
   model's price sits ~$9 over the actual in both regimes in Dec-2025.
3. **Never quote the firm prices as inert** (now: margin-setting in 14 % of
   Dec-2025 hours).
4. caiso-244 §7 and caiso-243 §10 stand in full.

---

## §8 — OWNER ASKS

1. **Form (ii)** — the per-intertie price-insensitive intertie-bid intake
   (OASIS PUB_DAM_GRP, re-fetch) so the caiso-151 ceiling can be allocated by
   measurement rather than pro rata.
2. **The two fitted firm prices** — measured live on the December price path;
   the Q-Q route failed its gate at caiso-86; a decision on whether a
   measured contract-cost source exists (DMM RA import price reports).
3. **The autumn-2025 slab** (§3) — the overlay coverage gap and D3 are the
   standing asks that sit on it.
4. Everything caiso-244 §8 carried.

---

## §9 — DELIVERABLES

`PRECOMMIT-caiso245-firm-import-allocation-split-2026-09-04.md`; the
`ra-import-allocations` intake (`data/dictionary/schema/ra-import-allocations.schema.yaml`,
`data/raw/ra-import-allocations/CAISO/` 9 workbooks + README + SHA256SUMS,
`scripts/lib/ra_import_allocations/{__init__,caiso}.py`,
`scripts/data/curate_ra_import_allocations.py`,
`tests/curation/test_curate_ra_import_allocations.py`, `regenerate_clean.py` +
data-dictionary registration); `scripts/probes/_caiso245_allocation_split.py` →
`_caiso245_allocation_split.json`; `scripts/probes/_caiso245_december_carrier.py`
→ `_caiso245_december_carrier.json`; this finding; the caiso.md entry;
evidence appends (no verdict move) on the CAISO shard's `import_hub_pricing`
and `caiso_firm_selfsched_floor`. **No run registered (none produced), no
keeper change, no `ScenarioConfig` field.**

**Next number: caiso-246.**
