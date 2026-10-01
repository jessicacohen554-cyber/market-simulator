# PRECOMMIT — caiso-245: the firm import block's CORRIDOR SPLIT re-keyed from the MIC capability share to CAISO's PUBLISHED RA-import capability ALLOCATIONS (form (i) of FINDING-caiso244 §5). Pushed BEFORE the key is computed, BEFORE the arm is coded, BEFORE any LP.

**Session caiso-245, 2026-09-04. Branch `claude/caiso-244-backcast-calibration-jag23e`
(reset onto `main` `a35c9f9b`, which carries caiso-244 merged).** Keeper at open:
**`2026-09-04-caiso-243-b1-f923`** (`caiso243_b1_f923_fallback_guard`, `git_sha
b053e3b8`), **NOT-YET**, C3a the sole load-bearing FAIL **+3.9 / +12.3 /
+14.4 %** (required move +3.297 / −0.805 / −1.498 $/MWh); C1 12/12 free 8/8;
C2 / C3b / C4 PASS; C3c the single ledgered caveat; C6 attested; C8 PASS; DOF
9 / 6. No `complete` / `final` marker; holdout freeze ACTIVE; 2023–2025 only.

---

## §0 — WHAT THIS SESSION IS

### §0.1 — The object, from the queue (handoff item A), and the form (i)

caiso-244 located the CAISO over-import LEVEL: the whole +8.43 / +8.69 /
+5.31 TWh excess is the NORTH corridor (PNW +11.30 / +10.65 / +8.76 TWh; DSW
under −2.87 / −1.96 / −3.45), and it sits on the firm block's corridor split —
the DMM annual RA-import capacity (2,323 / 3,371 / 3,371 MW) × the published
MIC **capability** share north of Path 15 (46.2 / 46.2 / 46.4 %), forced as
energy on COI (7.70 / 9.74 / 9.99 TWh) against a corridor that carried
−0.55 / 2.06 / 4.73 TWh net. The MIC share is a transmission-capability key
used as an energy-source key. Form (i), the recommended one: replace it with
the share of RA import capability that LSEs actually HOLD on each branch
group, from CAISO's own published annual allocation results.

### §0.2 — The source, verified reachable this session (data prep, unrestricted)

`https://www.caiso.com/library/{2023,2024,2025}-import-allocations` lists,
per year: **"Holders of Import Capability" (xlsx: LSE × BRANCHGROUP ×
ALLOCATION MW × START_DT/END_DT)** — the assigned import capability after
every allocation step and bilateral transfer; "Import Capability Used on
Annual Resource Adequacy Plans" (xlsx: MONTH May–Sep × SCID/BG ×
USED_ALL_CAPABILITY Yes/No); "Step 6 Contractual Data" (xlsx) and "Step 6
Assigned and Unassigned RA Import Capability on Branch Groups" (pdf); and the
MIC document already in `data/raw/capacity-deliverability/caiso/`. All
downloaded (13 files, HTTP 200 via the session proxy) and inspected for
STRUCTURE ONLY.

**FULL DISCLOSURE of what was seen before this push:** the first 25 rows of
the 2024 holders sheet (LANC / LANHM / LAZCO / … on ELDORADO_ITC,
MALIN500_ISL, NOB_ITC, PALOVRDE_ITC, IPPDCADLN_ITC, …), the 46-code branch-
group vocabulary across the three years, the row counts (265 / 234 / 240) and
the used-file value counts (Yes/No). **No aggregation, no share, no total was
computed.** The MIC north list from `interchange_config` (Malin 500, COTP,
NOB, Cascade, Summit, Round Mountain 230, Cottonwood 230, Northwest 230,
Marble, Tracy 230/500, Tracy-TEA, Westley-*, Standiford, Oakdale, New Melones,
Rancho Seco/Lake; Merchant kept south) is the geography the key will use —
the same geography as `CAISO_CORRIDOR_DIBA`, so nothing about the corridor
definition is chosen here.

### §0.3 — Admissibility position (rules 13 / 14 / 5 / 21)

The arm changes ONE thing: the number that splits the DMM RA-import level
between the two firm rows. Today that number is the MIC capability share; the
arm makes it the HELD-allocation share, per year, from a published annual
document that regenerates every year on the same cadence (the allocation
process runs each July for the following RA year) — rule 13's test is met by
inspection: a forward year takes the latest published allocation, exactly as
the DMM level does today. **The DMM level itself is NOT touched** (the two
firm caps still sum to 2,323 / 3,371 / 3,371 MW). **Zero new fitted
scalars** (rule 21): the share is a ratio of two published sums. Rule 14: an
allocation is a capability RIGHT, not scheduled energy — that misalignment is
smaller than the MIC's (which is total capability, not even a right), and it
is stated. The "used on RA plans" boolean is computed and REPORTED as a
diagnostic, never armed (a boolean cannot weight MW without a chosen rule).

### §0.4 — HARD STOPS

Training window only; one bundle, three years, sequential; never two CAISO
solves concurrently. No `calibration-complete.json` / `holdout-freeze.json` /
other-ISO shard or bundle touched. The datatype and its curate are
ISO-generic infrastructure (registry pattern); the ARM is CAISO-only and
default OFF. The depth lane stays closed; the 8,800 MW ladder, the firm
PRICES, the clean-depth tranches, the self-schedule floor's LEVEL and the
caiso-151 clip are untouched. `caiso_p1_export_sink_seam` (R) is not
re-opened. **STOP RULE (measured before any code):** if the held-allocation
north share is within **5 percentage points** of the MIC share in every year,
the arm is inert by construction — it is NOT built, no solve is spent, and the
session files the measurement and stops.

### §0.5 — THE HAZARD, before any number

A north→south re-split is **C3a-FAVOURABLE on both zones** (caiso-215: NP15
−6.6 / −0.8 % UNDER-prices; LA_BASIN / SDGE / SP15_rest / ZP26 +13.5…+27.1 %
over-price in 2024/25). This is the **FOURTH** consecutive favourable
direction in the lane. C3a's verdict is EXCLUDED from the promotion basis
(§5.7). If C3a improves, that is reported, never argued.

### §0.6 — DO-NOT-REDO acknowledged

caiso-244 §7 (gross-klass basis; voided ratios; ladder; "inert by
construction"; "< 5 %"; December volume; by-name pattern), caiso-243 §10,
caiso-242 §9, caiso-241 §10, caiso-240 §7, caiso-239 §8, caiso-230 §9 — read,
none re-opened.

---

## §1 — THE MECHANISM (to be coded AFTER the split is measured)

`ScenarioConfig.caiso_firm_import_allocation_split: bool = False`
(CAISO-only, default off; backcast-measured input with the forward story of
§0.3). In `model/interchange/caiso.py::inject_caiso_firm_import_shape`, the
level each firm row is shaped from becomes

    firm_mw[PNW_hydro_base] = DMM_total[year] × share_north[year]
    firm_mw[DSW_solar_PV]   = DMM_total[year] × (1 − share_north[year])

with `DMM_total[year]` = the sum of the two firm caps in
`IMPORT_TRANCHES_BY_YEAR[CAISO][year]` (the published DMM level, unchanged)
and `share_north[year]` read through the clean seam from the new datatype
**`ra-import-allocations`** (`data/dictionary/schema/…`, `scripts/lib/
ra_import_allocations/{__init__,caiso}.py`, `scripts/data/
curate_ra_import_allocations.py`, `data/raw/ra-import-allocations/CAISO/`
holding the 13 fetched files + README + SHA256SUMS), aggregated by the
branch-group → corridor map of §0.2 (an unmapped code is a HARD ERROR, never
a silent default). Everything downstream — the measured shape, the envelope
clip, the self-schedule floor, the caiso-151 ceiling (pro rata by shaped
capability), the clean-depth nets — is untouched and re-flows from the new
level. Rule 19: one mechanism (the split key) replaced, none stacked.

---

## §2 — THE ESTIMATOR AND ITS GATES

* **G-KEY (pre-code, zero LP):** the split is computed from the committed
  raw files by the curate + a one-line derive; the north share per year and
  its "used on RA plans" diagnostic are recorded in
  `_caiso245_allocation_split.json`.
* **G-STRUCT (pre-solve, zero LP):** the fleet-only rebuild with the flag ON
  differs from the keeper rebuild in EXACTLY the two firm rows per year (their
  hourly capability and floor), every other row byte-identical; the two rows'
  annual capability sums to the keeper's (level preserved) within the
  envelope-clip asymmetry, which is reported.
* **G-CTRL, form 3 (owner's caiso-241 amendment):** the arm is live in all
  three years, and form 4 is VOID by its letter — 30 solve-path files changed
  since `b053e3b8` (capacity_evolution, pipeline/solve.py, runner.py …) — so
  ONE control solve is spent: the keeper recipe replayed at HEAD
  (`caiso245_a0_control`), and every arm number is scored **B1 − A0**.
  FALSIFIER: A0 not reproducing the keeper's C3a to 0.05 $/MWh in any year
  ⇒ HEAD drift is reported first and the arm is read against A0 only.
* **G-INERT:** B1 differs from A0 in every year (the key moves in every year
  by §0.4's stop rule).
* **G-C1 / G-C3b / G-C8 / G-CAVEAT / G-C6:** C1 ≥ 12/12 free 8/8; no
  scored criterion's verdict regresses; caveat budget ≤ 1 ledgered / 0
  protective; C6 attested on both bundles.
* **G-C3a, envelope leg:** no strict estimator exists for a re-split (the
  caiso-240/241 §H forms are not bounds); the registered two-sided envelope
  is **ΔC3a ∈ [−2.0, +0.5] $/MWh** in every year, derived from the caiso-215
  zonal residuals (the south's over-price and NP15's under-price bound how far
  the ISO load-weighted mean can move when ≤ 10 TWh/yr of forced import
  changes corridor). Outside ⇒ estimator defect, reported, never re-fitted.
  The VERDICT leg is excluded from promotion (§0.5).

---

## §3 — PREDICTIONS, REGISTERED BEFORE THE KEY IS COMPUTED

| # | prediction | falsified by |
|---|---|---|
| **P-1** (the key) | the HELD-allocation north share is **≤ 36 %** in every year (≥ 10 points below the MIC share) | ≥ 36 % in any year ⇒ the allocation key does not carry the caiso-244 excess; if within 5 points of MIC, §0.4's stop rule fires |
| **P-2** (level) | total held allocation ≥ the DMM RA-import capacity (2,323 / 3,371 / 3,371 MW) in every year — allocations are a ceiling on showings | any year below |
| **P-3** (diagnostic) | the share of north holdings flagged "used all capability" in May–Sep is **≤** the south's in every year | any year above |
| **P-4** (G-STRUCT) | exactly 2 rows differ per year; level preserved to within the envelope-clip asymmetry | any other row moves |
| **P-5** (volume) | PNW model net import falls by **≥ 4 TWh** and DSW rises by ≥ 3 TWh in every year (B1 − A0); total model import changes by **< 1.5 TWh** | either bound missed |
| **P-6** (price) | ISO load-weighted C3a moves **DOWN in 2024 and 2025** and NP15's zonal mean moves **UP** while SP15_rest's moves **DOWN** in every year; no C3a verdict flips; 2023 stays PASS | any sign wrong, or a flip |
| **P-7** (uncomfortable) | the re-split does NOT close C3a: ΔC3a-2025 ≥ −1.0 $/MWh against a required −1.498 | ΔC3a-2025 < −1.0 |
| **P-8** (import-marginal) | the share of hours an import row is marginal at the CAISO landing zone (caiso-244 §3.6: 19.9 / 17.7 / 23.0 %) changes by < 3 points | ≥ 3 points |
| **P-9** (forced budget) | C8 stays PASS and the D-2 `firm_import` forced energy changes by < 10 % (the ceiling clip is level-preserving) | ≥ 10 % or C8 fails |
| **P-10** (DOF) | the DOF ledger does not move (9 / 6): a published key replacing a published key is invisible to `_count_scalars` | any change |

---

## §4 — THE PROMOTION RULE, FIXED NOW

Promote **iff** G-KEY, G-STRUCT, G-CTRL, G-INERT, G-C1, G-C3b, G-C8, G-CAVEAT,
G-C6 and the envelope leg of G-C3a all pass. **The basis is structural:** a
transmission-capability key is replaced by the published allocation key that
measures the quantity the mechanism represents (RA import commitments by
intertie), at zero free parameters, with no scored criterion regressing. C3a's
verdict is reported and excluded. **If every gate passes and C3a does not move,
the arm is still promoted; if the owner's "structural integrity improves but a
gate regresses" case arises, the regression is reported at full size and the
promotion is put to the owner rather than taken.**

---

## §5 — OWNER ASKS ANTICIPATED

1. Whether the "used on RA plans" boolean should ever weight the key
   (needs a rule; not proposed).
2. The DMM level itself (a capacity, forced as energy) — unchanged here;
   caiso-244 §5 form (iv) remains an open question.
3. Everything caiso-244 §8 carried.
