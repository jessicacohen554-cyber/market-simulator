# FINDING — capx D2-B: the I7 legs of MISO / CAISO / NEISO / PJM, reproduced and decomposed from committed artifacts

**Session:** capx D2-B I7 LEDGER DECOMPOSITION (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-25 · **Branch:** `claude/capx-d2b-i7-ledger-xaakeu`
**Charter:** director ledger refresh #4 (`capx-director-ledger-2026-08.md` §0b.3, D2-B row):
apply the NYISO session's method (`FINDING-capx-d2-adequacy-nyiso-2026-08-24.md`) to the four
other I7 ISOs — reproduce each leg from committed artifacts, decompose the gap, adjudicate the
three forks. Records first; a solve only where records cannot answer. **No solve was run, no
year was scored, nothing was registered, and no I7-closing fix was shipped.**

Baseline throughout: `frontend/data/forecast/ff-verdicts.json`, un-suffixed `*-t1f` keys
(FFR-3A-2, `scored_at_sha 8ba59281`, cache epoch 2026-08-03).

---

## 0. Headline

1. **Three of the four legs are reproduced from committed artifacts** — MISO 2026 and CAISO
   2026–2030 **to the MW**, NEISO 2026/2028 to the verdict's own rounding. **PJM's supply side
   is the one leg no committed artifact can reproduce** (§5); its *requirement* side is
   reproduced exactly from constants, and doing so exposes a mid-horizon requirement
   discontinuity that makes the reported 366 MW miss an understatement (§5.2).
2. **The cross-ISO prize is confirmed: MISO is the second NYISO.** MISO credits **zero
   external firm capacity** (`ADEQUACY_EXTERNAL_TIE_FIRM_MW` has no MISO entry) while the
   forecast path floors a **1,400 MW Manitoba firm-hydro import block at 100 % in every
   hour, default-on** (`MISO_FIRM_IMPORT_DEFAULT_ISOS = {"MISO"}`,
   `interchange/spec.py:1537-1599, 1928-1943`). Exactly the case-(b) asymmetry the NYISO
   finding proved: dispatch relies on firm imports the adequacy ledger counts at zero. The
   registry now omits exactly the two ISOs that fail I7 with a default-on firm-import floor
   behind the miss (§6).
3. **A second MISO defect is provable from the repo's own citation blocks:** the fallback
   requirement multiplies the **PY 2024-25** ICAP PRM (0.179) by the **PY 2025-26** ICAP→UCAP
   ratio, and the ratio's own cited source (PY 2025-26 LOLE Study, Module E-1) publishes
   **ICAP 15.7 % / UCAP 7.9 %** — contradicting the PRM entry it is multiplied with. The
   same-document PY 2025-26 pairing puts the requirement **2,637.4 MW lower**, 44 % of MISO's
   6,037 MW 2026 gap (§2.3). Not shipped here — solve-affecting and shared with the
   backcast-reachable retirement reliability floor — routed with its citation (§8, lane S-1).
4. **NEISO's hydro fallback is doing load-bearing work, answering the charter's direct
   question: yes, and it decides the verdict's sign.** The generic
   `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50` fallback (no ISO-published NEISO factor
   exists — FFR-1C open item) contributes **949.75 MW** (1,899.5 MW nameplate × 0.50) — 4.4×
   the 218 MW 2028 gap. The 2028 FAIL/PASS outcome sits entirely inside that one uncited
   input's uncertainty band (§4.3).
5. **CAISO's forks were already adjudicated** — by FFR-3P
   (`ffr-3p-caiso-accreditation-2026-08-04.md`), against CAISO's own published ledger:
   the dominant cause is **fleet-snapshot vintage (fork 2)** — the base-year battery fleet is
   8,000 MW against a published 14,131 MW NDC (≥5,933 MW, 90 % of the base-year deficit,
   blocker B-1). This session does not re-derive that; it adds the committed **horizon**
   decomposition FFR-3P did not have: the 2,824 MW of 2027 confirmed OTC exits, the BLK-10
   backstop ladder (1,396.4 → 2,792.8 → 5,585.6 → 4,268.8 = 14,043.6 MW of administrative
   CTs), and the committed `caiso-nqc-armed` twin measuring the default-off NQC credit at
   **+1,072 MW** (§3).
6. **Base-year vs evolved-year, program-wide (the charter's organizing distinction):** MISO
   2026 and CAISO 2026 are base-year legs — no evolution runs, no mechanism can move them,
   they grade the input data. MISO 2027, CAISO 2027–2029, NEISO 2028 and PJM 2030 are
   evolved-year legs — they additionally grade confirmed exits, the retirement screen, and
   the rate-limited backstop ladder (§7).

---

## 1. Method and artifact routes

Per the charter, every number below is from a committed artifact or a constant at HEAD; the
verdict baseline is the live FFR-3A-2 row quoted beside each reproduction.

| ISO | committed route | coverage |
|---|---|---|
| MISO | `results/ffr1c/{before,after}-miso/MISO/755fd1fba560e0e3/evolution_2026.json` | 2026 leg, to the MW; **2027 leg NOT reproducible** (no committed ledger) |
| CAISO | `results/ffr3p/caiso-control/CAISO/e5822277b72184f6/` (`evolution_2026..2030.json` + `full_horizon_summary.json`) and the `caiso-nqc-armed` twin (`ee0e448058d115aa`) | **full horizon 2026–2030, to the MW** — the committed summary's I7/I12 rows are *verbatim identical* to the live verdict |
| NEISO | `results/ff2b-after/neiso/NEISO/fe4d5bd213dd8607/evolution_2026.json` + `ffr-1c-hydro-accreditation-2026-07-31.md` (hydro nameplate table) + constants | 2026 ledger reconstructed to the verdict's rounding; **2028 leg NOT reproducible** (no committed ledger) |
| PJM | constants only (`capacity_market.py`) | **requirement side exact; supply side NOT reproducible** — the only PJM evolution ledgers ever committed are hindcast 2021–2025 (`results/hindcast/pjm-*`) |

Ledger-inventory basis: `git ls-files | grep evolution_20xx.json` — CAISO 2026–2030,
MISO 2026 (+ 2031–2035 arm3arm), NEISO 2021–2026, NYISO 2021–2026, PJM 2021–2025 only.

**Method note for future decompositions:** an evolution ledger's exits live in **two keys** —
`retirements` (unit-grain drops) *plus* `confirmed_derates` (plant-binned exits that derate a
surviving unit in place). CAISO 2027 reads 1,491.0 MW in the first and 1,333.0 MW in the
second; summing only `retirements` under-counts the exit wave by 47 %. This is the repaired
I4/A1 leak of the capx-D1 finding working as designed, not a defect — but a decomposition
that forgets the second key will mis-attribute the gap.

---

## 2. MISO — 2026 reproduced to the MW; the gap is three named accounting terms

### 2.1 The live record, reproduced exactly

Verdict: *2026: accredited firm 135304 < requirement 141341 MW; 2027: 139147 < 142806.*

From the committed FFR-1C after-ledger (peak 128,548.607, `reserve_margin` 0.052554):

| quantity | value | check |
|---|---:|---|
| accredited firm = peak × (1 + rm) | **135,304.4** | verdict 135304 ✓ |
| requirement = peak × 1.179 × (1.079/1.157) | **141,341.4** | verdict 141341 ✓ |
| **gap** | **6,037.0** | charter 6,037 ✓ |

MISO has no DR netting and no published FPR, so the fallback branch of
`resolve_adequacy_requirement_mw` applies; the I12 floor 10.0 % is the same composite
restated (1.179 × 0.93258 − 1 = 9.95 %), and rm 5.3 % is the ledger's 0.052554.

Full supply-side ledger, rebuilt from the committed fleet-by-fuel and constants:

| class | basis | MW |
|---|---|---:|
| thermal (132,889.8 MW nameplate) | UCAP `1 − EFORd` | 124,464.4 |
| wind pool 32,000 | 0.166 (MISO ELCC curve clamp) | 5,312.0 |
| solar pool 7,000 | 0.18 (generic) | 1,260.0 |
| storage | pre-accredited | 2,797.6 |
| hydro 2,371.5 | DLOL RoR 0.62 | 1,470.3 |
| **external firm import** | **absent** | **0.0** |
| **total** | | **135,304.3** |

The pre-hydro sum (133,834.0) matches the committed *before*-ledger's rm to its 6-dp
rounding, and the hydro back-solve (1,470.3 / 0.62 = 2,371.5 MW nameplate) matches the
FFR-1C doc's published MISO nameplate **to the digit** — the same double-entry closure the
NYISO finding achieved. FFR-1C hydro is already inside MISO's verdict, worth 1,470.3 MW;
nothing premised on un-credited hydro should be chartered (charter's settled item, re-proven
here for MISO).

### 2.2 Fork 1 — accreditation accounting: **OPEN, two named members, both provable**

**(a) External firm capacity credited at zero — the NYISO defect, second instance.** The
forecast path builds a `FirmImport("Manitoba_firmhydro", zone="MISO-West",
capacity_mw=1400.0, floor_frac=1.0)` block **by default** (`resolve_miso_firm_imports`
defaults ON for MISO; the two-way `miso_manitoba_seam` that would replace it is default-off).
So MISO dispatch floors 1,400 MW of firm Manitoba hydro as must-flow in every hour while
`accredited_firm_capacity_mw` credits 0 MW of external capacity. MISO's own construction
counts external resources as ZRC supply toward the PRMR, so MISO belongs in the registry on
the registry's own stated logic. **The 1,400 MW dispatch constant is NOT the number to
intake** — like NYISO's 900 MW it is a ladder-inherited spec constant, not a published RA
accreditation; the honest value is MISO's published PRA external-resource / ZRC accreditation
(§8 lane S-2), never an interface limit (the CAISO-entry discipline).

**(b) Load-modifying resources / DR absent from the construction.** MISO is absent from
`ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO`, yet MISO's own PRMR construction counts LMRs as
ZRC *supply* — the same "cleared supply product" situation for which PJM and NEISO carry
documented reconciliations. No in-repo citation quantifies MISO's LMR ZRCs, so **no number is
claimed here**; the term is named and routed into the fork-2 differencing lane (S-3), where
it must enter as a documented reconciliation, never a raw fraction of peak.

### 2.3 Fork 3 — requirement mismatch: **REAL, provable from the repo's own citation blocks**

`PLANNING_RESERVE_MARGIN_BY_ISO["MISO"] = 0.179` is cited to the **PY 2024-25** LOLE Study.
`PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_ISO["MISO"] = 1.079/1.157` is cited to the
**PY 2025-26** LOLE Study, Module E-1 — *"Summer PRM stated both ways: ICAP 15.7 %,
UCAP 7.9 %"* (`capacity_market.py:2635-2637`). The composite therefore multiplies one
planning year's ICAP PRM by the next planning year's conversion, and equals **neither**
year's own published requirement:

```
shipped composite : peak × 1.179 × (1.079/1.157) = peak × 1.09952
PY 2025-26 pairing: peak × 1.079                   (same-document, both halves)
difference at the 2026 peak = 128,548.607 × 0.02052 = 2,637.4 MW  = 44 % of the gap
```

This is a rule-23-admissible re-derivation — the *source data updated* (PY 2025-26 published
both halves) — and its citation is already in the repo. **It is still not shipped here**,
because it is not pure bookkeeping: the requirement feeds the retirement reliability floor
and the backstop in every solve, MISO has a live backcast lane, and a re-vintage must land
with a re-run and a matrix-conscious charter (§8 lane S-1). ⚠ Trap named in advance, NYISO
finding style: the re-vintage closes 2,637 of 6,037 MW — *it must be shipped because the
source updated, not because of what it closes*, and the residual ~3,400 MW must not be
"finished off" by tuning the remaining terms; they have their own published sources (S-2/S-3).

A second, unquantified fork-3 member is noted for completeness: the requirement's peak is
the model's own simulated weather-year peak, not MISO's coincident 1-in-2 planning forecast —
the same B-4 class question FFR-3P measured at +3,435 MW for CAISO. Unmeasured for MISO in
any committed artifact; folded into S-3's differencing.

### 2.4 Fork 2 — fleet-snapshot vintage: **OPEN, method named, no evidence either way**

The base-year fleet (132.9 GW thermal, 32 GW wind pool, 7 GW solar pool, 2.8 GW storage
firm) reproduces the verdict, but nothing committed differences it against MISO's own
resource ledger. After FFR-3P's CAISO lesson — where the *unnamed* fork-2 term (battery
vintage) turned out to be 90 % of the deficit — MISO deserves the same instrument:
difference the model ledger class-by-class against MISO's own PY 2025-26 PRA / LOLE resource
table (S-3). The hydro-census vintage-clamp half of fork 2 is already CLOSED program-wide by
the D2 session's mutation-verified test guard.

### 2.5 The 2027 leg — evolved year, **not reproducible from committed artifacts**

No committed MISO 2027 ledger exists. What the verdict arithmetic alone bounds: accredited
firm grew 3,843 MW (135,304 → 139,147) against requirement growth 1,465 MW — the backstop
(default-ON for capacity-market MISO from year 2) fired and closed 2,378 MW of the gap net,
landing at 3,659 MW. Which cap bound it — the BLK-10 `entry_rate_limits` growth ladder
(CAISO's signature, §3.3) vs the 10 GW queue cap vs economic-entry interplay — **is
inference, not measurement**, exactly the NYISO finding's §8 posture. Minimum run that would
answer: one T1-F MISO 2026–2027 forecast solve with ledgers (solo — 9.6 GB peak RSS recorded,
"no co-run"), registered on the forecast namespace with its `run_config.json` committed.
Sequencing note: the director's D9 (MISO forecast interchange fallback `ba_code="SOCO"`)
"likely bears on MISO's I7/I12" and should ride with, not after, any such re-measure.

---

## 3. CAISO — full horizon reproduced to the MW; forks pre-adjudicated by FFR-3P; the ladder decomposed

### 3.1 The live record, reproduced exactly — all four failing years

The committed `results/ffr3p/caiso-control/full_horizon_summary.json` carries I7 and I12
rows **verbatim identical** to the live verdict (all four years, every MW), and its per-year
ledgers rebuild them:

| year | peak | rm | firm | req (peak×1.15) | gap | events (from the committed ledgers) |
|---|---:|---:|---:|---:|---:|---|
| 2026 | 49,831.2 | +0.0180 | 50,729 | 57,306 | 6,577 | base year — no evolution (fleet before == after, no events) |
| 2027 | 51,018.3 | −0.0312 | 49,428 | 58,671 | 9,243 | **confirmed OTC exits 2,824.0 MW** LA-Basin `gas_st` (1,491.0 in `retirements` + 1,333.0 in `confirmed_derates`); backstop CT +1,396.4 |
| 2028 | 52,244.9 | −0.0031 | 52,081 | 60,082 | 8,001 | backstop CT +2,792.8; 3 GW gas_cc→gas_cc_ccs retrofit (firm-neutral) |
| 2029 | 53,511.9 | +0.1235 | 60,119 | 61,539 | 1,420 | backstop CT +5,585.6; economic gas_cc +2,000 (decided 2027, landed 2029); wind +702.2, solar +4,000 land |
| 2030 | 54,820.6 | +0.1528 | 63,199 | 63,044 | PASS | backstop CT +4,268.8 (need-limited); Diablo unit −1,122 confirmed |

2026 supply decomposition (mine, closes to the before/after ledgers exactly): thermal UCAP
30,221.4 + wind 1,120.0 (generic 0.16) + solar 3,960.0 (generic 0.18) + storage 7,432.2 +
external tie 3,371.0 = 46,104.6 pre-hydro; + hydro 6,568.4 × 0.7041 = 4,624.8 → **50,729.4**.
Hydro nameplate back-solve matches the FFR-1C table to the digit.

### 3.2 Forks — adjudicated, by citation, not re-derived

FFR-3P (2026-08-04) already adjudicated this deficit against **CAISO's own published
ledger** (2026 Summer Loads & Resources Assessment Table 1.1 + CY2026 NQC report + CPUC 2026
RA Guide). Its verdicts stand and this session found nothing contradicting them:

* **Fork 2 (fleet-snapshot vintage) — the DOMINANT cause.** `STORAGE_BASE_FLEET_MW["CAISO"]
  ["mid"] = 8,000` vs a published **14,131 MW NDC / 13,365 MW NQC** battery fleet:
  **≥ 5,933 MW, 90 % of the 6,577 MW base-year deficit** (blocker B-1 — "this should go
  first"). Hydro fleet coverage −1,670 MW (caveated on the pumped-storage split, B-2).
* **Fork 1 (accreditation accounting) — largely REFUTED.** The hydro class factor is 1.1 pp
  *generous* vs CAISO's realized fleet rate; thermal UCAP sits +242 MW *above* CAISO's own
  NQC (the "CAISO belongs in `THERMAL_ACCREDITATION_BASIS_BY_ISO`" case is textually real
  but empirically refuted — the estimate is KEPT under rule 14's documented-misalignment
  exception). What survives: DR omission (real, small, unquantified — B-5) and the
  default-off `caiso_nqc_accreditation` credit. On the latter this session adds a committed
  measurement: the **`caiso-nqc-armed` twin** ledgers show rm 2026 0.0180 → 0.0395 =
  **+1,072 MW**, matching the constants arithmetic exactly (solar 0.18→0.2096, wind
  0.16→0.2202 on the 2026 pools) — 16 % of the deficit, still I7-failing armed alone.
  Arming posture unchanged (owner D.1 HOLD; FFR-3P's recommended ordering — B-1 first — is
  endorsed by the 90/16 split).
* **Fork 3 (requirement) — REAL, both directions, net +2,030 MW too high.** Weather-year
  simulated peak vs CEC 1-in-2 (+3,435), stale PRM 0.15 vs adopted 0.18 for CY2026-27
  (−1,405), DR netting absent (unquantified). B-3/B-4, routed there.

### 3.3 What this session adds — the horizon story the base-year adjudication could not see

The backstop additions follow the BLK-10 growth ladder exactly — **1,396.4 → 2,792.8 (×2) →
5,585.6 (×2) → 4,268.8 (need-limited)** — totalling **14,043.6 MW of administrative CTs**
(FFR-3P's figure, now decomposed year-by-year from committed ledgers). Two consequences:

1. **The 65.5 % backstop share and the I12 FAIL are downstream artifacts of the input-vintage
   deficit, not independent defects.** The model starts ~6 GW short on accounting (90 %
   storage vintage), loses another 2,824 MW to real confirmed OTC exits in 2027 while the
   ladder is still at its 1.4 GW first rung, and then spends three years of doubling to
   catch up — building CTs that substitute for **batteries that already physically exist**
   but are absent from the base fleet. Fix B-1 and most of the ladder never fires; the
   backstop share collapses without touching the backstop.
2. **The 2027 gap peak (9,243 MW) is structural arithmetic, not a new problem:** confirmed
   exits (real, correctly gated) land at full size in one year while the ladder's first rung
   is small by design. Any future "why does 2027 spike" question should be answered from
   this table, not a new mechanism (rule 19).

Classification: 2026 base-year (input-data leg); 2027–2029 evolved-year (inherited deficit +
confirmed exits + rate-limited catch-up). No new CAISO successor lane is chartered — B-1
through B-8 already exist and are correctly ordered; this section is their horizon evidence.

---

## 4. NEISO — 2026/2028 reconstructed to the verdict's rounding; the fallback hydro credit decides the sign

### 4.1 The live record, reconstructed

No FFR-1C or T1-F NEISO bundle is committed. The route that works: the committed FF-2B
ledger (pre-FFR-1C: peak 24,889.729, rm 0.114428 → firm 27,737.8) plus the FFR-1C doc's
NEISO hydro nameplate (1,899.5 MW) at the fallback credit 0.50:

```
FF-2B firm (hydro uncredited)   = 27,737.8
+ FFR-1C hydro fallback credit  =    949.75   (1,899.5 × 0.50)
= implied live 2026 firm        = 28,687.6  → rm = +15.26 %
verdict I12 2026                = "15.3 % (band [0.2 %, 15.2 %])"  ✓ (rounding)
```

Requirement factor = (1 − 2,940/30,305) × (30,305/27,298) = **1.0024544** (FCA-17 Net ICR
construction, DR netted; floor 0.2 % ✓). Back-solving the 2028 leg: peak₂₀₂₈ =
25,604 / 1.0024544 = **25,541.3**; rm₂₀₂₈ = 25,386/25,541.3 − 1 = **−0.61 %** — the
verdict's "2028: −0.6 %" ✓. Both live legs are therefore reconstructed from committed
artifacts to the verdict's own rounding; no solve was needed.

### 4.2 Shape of the miss

2026 starts **over-built against the band** (+15.3 % vs cap 15.2 % — the I12 WARN's other
half), then accredited firm falls ~3,301 MW by 2028 while peak grows 651 MW, undershooting
the floor by 218 MW (−0.85 %), with 2029–2030 recovering (no later I7 rows; backstop share
11.7 %). The retirement fodder visible in the committed 2026 fleet: **oil 5,181.5 MW**,
gas_st 158.3, coal 108. The year-by-year attribution (which units, which screen, which
ladder rung) is **not reproducible from committed artifacts** — minimum run: one T1-F NEISO
2026–2028 solve with ledgers (cheap: 9.2 min recorded, no heavy-slot constraint).

### 4.3 The charter's direct question — the hydro fallback: **it is doing work, and it is the finding**

`HYDRO_ACCREDITATION_CREDIT_BY_ISO` has no NEISO entry, deliberately — FFR-1C located no
ISO-published NEISO hydro class factor (ISO-NE qualifies hydro per-resource at Seasonal
Claimed Capability; intermittent hydro on a median-output construction) and fell back to the
generic 0.50 rather than borrow a foreign ISO's factor (rule 25). That was the right call
then, and FFR-1C filed it as an open item. What this session adds is the **measurement that
it is now load-bearing**: 949.75 MW of the 2028 ledger rides on an uncited generic constant,
**4.4× the 218 MW gap**. A per-resource QC class average of 0.39 would flip 2027 into FAIL;
0.62 would clear 2028 outright. **The NEISO 2028 verdict is not decidable at the current
input fidelity** — the honest fix is the FFR-1C open item's intake (§8 lane S-4), not a
solve, and until it lands the 2028 row should be read as "within input uncertainty", not as
a capacity-evolution defect.

### 4.4 Forks

* **Fork 1:** hydro half OPEN (above — the finding). External half CLOSED: 567 MW is
  published FCA-17 cleared-import CSOs, with the 1,001 MW HQICC correctly *netted from the
  requirement* (Net ICR) rather than double-credited — internally consistent.
* **Fork 2:** CLOSED for 2026 (the committed FF-2B ledger is the snapshot, and it starts
  *over*-built — the miss is not a small-fleet artifact); OPEN for the 2028 fleet state
  pending the minimum run.
* **Fork 3:** CLOSED — every requirement input (Net ICR 30,305, 50/50 peak 27,298, DR 2,940)
  is same-document FCA-17, the one construction the fallback registries deliberately encode.
  Vintage note only: CCP 2026/27 values are held for 2028; ISO-NE's own 2028/29 values would
  refresh both halves together (rule 23, on publication — folded into S-4's session).

---

## 5. PJM — the one leg no committed artifact can reproduce; the requirement side, reproduced exactly, understates the miss

### 5.1 Supply side: **no committed route exists — stated explicitly, per charter**

The only PJM evolution ledgers ever committed are hindcast 2021–2025
(`results/hindcast/pjm-*`). The FFR-3A-2 T1-F bundle is gitignored by design
(`results/ffr3a2/README.md`), and no FFR-1A/FFR-1C PJM ledger was committed. **The 2030
accredited-firm figure 150,088 MW therefore cannot be decomposed from any committed
artifact.** Minimum run that would: one T1-F PJM 2026–2030 forecast solve — **solo** (8.8 GB
peak RSS recorded, "no co-run"; 19.0 min cold, 3.8 min/solve-year), years sequential,
ledgers landing under `<out-dir>/PJM/<cache_key>/evolution_<year>.json`, registered via
`scripts/register_forecast_run.py` with `run_config.json` committed (FC-7). This session did
not launch it: the heavy-slot budget is shared with the owner's backcast solves, and §5.2's
requirement finding should be adjudicated first so the run measures against the right bar.

### 5.2 Requirement side: reproduced exactly — and it exposes a mid-horizon discontinuity

The verdict's own numbers back-solve on the **fallback** requirement to four digits:

```
requirement factor = (1 − 5,795/146,105) × 1.178 × (0.9170/1.191) = 0.871017 × peak
peak₂₀₃₀ = 150,454 / 0.871017 = 172,733.8
rm₂₀₃₀   = 150,088 / 172,733.8 − 1 = −13.11 %   (verdict I12: "2030: −13.1 %", floor −12.9 % ✓)
```

Why the fallback: `FORECAST_POOL_REQUIREMENT_BY_ISO["PJM"]` ends at delivery year 2028/2029,
and `resolve_forecast_pool_requirement` returns None beyond it. Two consequences, one
benign, one not:

* **The D-1 checker/model divergence (NYISO finding §7) is INERT for this specific leg** —
  with no published 2030/2031 FPR, model and checker both grade 2030 on the same fallback.
  D-1 still stands for 2026–2028 (where the model builds to the FPR and the year-less
  checker grades the lower fallback) and still belongs to a scorer/governance round.
* **The requirement factor falls discontinuously at the FPR table edge, mid-horizon:**

  | delivery years | construction | req factor (on gross peak) |
  |---|---|---:|
  | 2026/27 → 2028/29 | published FPR (0.9170 / 0.9260 / 0.9401), rising | 0.88063 → 0.90281 |
  | 2029/30+ | fallback composite (IRM 17.8 % of 2025/26 × 2026/27 ratio) | **0.87102** |

  Crossing 2028→2029 the bar the model builds to *drops by 3.18 % of peak* — **5,492 MW at
  the 2030 peak** — because the composite's IRM half is two vintages stale against PJM's own
  rising series (published 2027/28 IRM is 20.0 %, and the FPR series rises 0.917 → 0.9401).
  Against a held-last-FPR requirement (the convention `forward_net_cone_anchor` already
  establishes for the demand curve's own forward values), 2030's requirement is ~155,946 MW
  and the miss is **~5.9 GW, not 366 MW** — and 2029 plausibly fails too.

**The honest reading of PJM's I7 row: the reported 366 MW is the artifact of grading the
horizon edge against the weakest available requirement construction. The direction of every
correction is against leniency.** (Same one-sided pattern on the supply side: the external
tie 1,281.7 MW is the 2026/27 BRA cleared UCAP held static; PJM's published 2027/28 figure
is 1,005.9 MW, i.e. −275.8 MW.) Fork 3 is therefore **OPEN as the load-bearing fork** —
successor lane S-5: adjudicate the FPR horizon-edge convention (hold-last vs composite) as a
declared construction, and intake the 2029/30 planning parameters when PJM posts them
(rule 23: on publication). Fork 1 is CLOSED (all three bases published and previously
adjudicated: `elcc_class_rating` thermal, hydro 0.38 BRA class rating, cleared-UCAP
imports). Fork 2 is OPEN-unobservable pending the minimum run, with one named suspect from
the committed hindcast record: the FFR-3A-2 battery close §3.8 measured the PJM retirement
screen recomposition at 29.373 GW total (D-1-attributed) — if the forecast leg over-retires
similarly, the 2030 supply side is retirement-screen-driven; **inference, flagged as such**.

---

## 6. The cross-ISO external-capacity check — the program-level finding

`ADEQUACY_EXTERNAL_TIE_FIRM_MW` audited entry-by-entry against (i) its published basis and
(ii) what the model floors in dispatch:

| ISO | entry | basis | dispatch-side firm treatment | verdict |
|---|---:|---|---|---|
| ERCOT | 817.0 | Dec-2025 CDR, EEA-measured DC-tie contribution | ties embedded in demand, no node | **SOUND** — accreditation-based |
| PJM | 1,281.7 | 2026/27 BRA Table 7 **cleared** import UCAP (not the CIL) | no import node; seams economic, no firm floor | **SOUND**, static vintage noted (2027/28 published: 1,005.9 — correction would *widen* the 2030 miss) |
| CAISO | 3,371.0 | DMM 2024 Table 15.6 RA imports = the model's own firm tranches (1,566 + 1,805) | firm import tranches, same 3,371 | **SOUND** — dispatch and adequacy read the same quantity by construction |
| NEISO | 567.0 | FCA-17 cleared import CSOs; HQICC 1,001 netted requirement-side | HQ_import node | **SOUND** |
| NYISO | **absent** | — | **900 MW HQ firm floored every hour** | **GAP** — proven by D2; intake ISSUED (`claude/capx-d2-nyiso-extcap-intake`) |
| MISO | **absent** | — | **1,400 MW Manitoba firm floored every hour, default-on** | **GAP** — proven this session (§2.2a) |

**The pattern:** every *populated* entry is accreditation-based (cleared/contracted RA
quantity, never a limit) and internally consistent with dispatch — the FF-2B construction
held. The registry's failure mode is **coverage, not basis**: it omits exactly the two ISOs
whose dispatch carries an *inherited-constant* firm-import floor rather than a
measured-intake import node — and both fail I7. The fix pattern is settled (FF-2B / the
issued NYISO intake); MISO needs its own instance with its own published number (S-2), and
the honesty test declared in advance, NYISO-style: MISO's published PRA external-resource
accreditation is **O(10³) MW against a 6 GW gap** — it closes a large *minority* of the gap.
A value that happened to close the whole residual would be the suspicious one (rule 21).

---

## 7. Base-year vs evolved-year — the classification the charter asked for

| leg | class | what it grades | what can move it |
|---|---|---|---|
| MISO 2026 (6,037) | **base-year** | input data only (`evolve_fleet` skipped) | requirement re-vintage (S-1), external intake (S-2), ledger differencing (S-3) |
| CAISO 2026 (6,577) | **base-year** | input data only | B-1 storage vintage (90 %), then NQC arming (16 %), B-3/B-4 requirement |
| MISO 2027 (3,659) | evolved | base deficit + backstop ladder | S-1/S-2 shrink the inherited gap; ladder behaviour only measurable by the minimum run |
| CAISO 2027–2029 (9,243→1,420) | evolved | base deficit + 2,824 MW confirmed OTC exits + BLK-10 ladder | B-1 removes most of the ladder's reason to fire |
| NEISO 2028 (218) | evolved | retirement descent through a floor, within input uncertainty | S-4 hydro intake decides the sign before any mechanism question exists |
| PJM 2030 (366, understated) | evolved | supply unobservable; requirement graded at the weakest construction | S-5 requirement adjudication first, then the minimum run |

Program-wide restatement of the D2 reframing, now with four more data points: **no base-year
I7 leg is a capacity-evolution defect, and neither backstop tuning nor floor relaxation is
ever the answer to one.** The evolved-year legs add exactly two mechanism-flavored
questions — ladder pacing against real exit waves (CAISO 2027 answers it: working as
designed) and retirement-screen calibration (PJM's open suspect) — and even those sit on top
of base ledgers that are provably under-counted (MISO, CAISO) or input-undecidable (NEISO).

---

## 8. Successor lanes — one per open fork, each bounded

| id | lane | fork it closes | scope + discipline |
|---|---|---|---|
| **S-1** | **MISO requirement re-vintage** | MISO fork 3 | Re-derive `PLANNING_RESERVE_MARGIN_BY_ISO["MISO"]` + ratio as the same-document PY 2025-26 pair (ICAP 15.7 % with its own conversion; citation already at `capacity_market.py:2635-2637`). Rule-23 basis: source updated. Solve-affecting, shared with the retirement floor ⇒ needs its own charter + T1-F re-measure; NOT a bookkeeping push. Expected −2,637 MW of the 2026 gap, stated in advance. |
| **S-2** | **MISO external-capacity intake** | MISO fork 1(a) | MISO PRA external-resource / ZRC accreditation → `ADEQUACY_EXTERNAL_TIE_FIRM_MW["MISO"]`, FF-2B construction. NEVER the 1,400 MW dispatch constant, never an interface/CIL limit. Unrestricted data intake (rule 22). |
| **S-3** | **MISO ledger differencing** (the FFR-3P Table-1.1 method) | MISO fork 2 + fork 1(b) | Difference the model's class ledger against MISO's own PY 2025-26 PRA/LOLE resource table; includes the LMR/DR documented reconciliation (PJM/NEISO treatment) and the peak-basis (B-4-class) check. Solve-free. |
| **S-4** | **NEISO hydro accreditation intake** | NEISO fork 1 | The FFR-1C open item, now measured load-bearing (949.75 MW vs a 218 MW gap): per-resource ISO-NE qualified-capacity (SCC) intake aggregated to a class factor, replacing the generic 0.50. Refresh the FCA vintage in the same session. Until it lands, read NEISO 2028 as within-input-uncertainty. |
| **S-5** | **PJM requirement horizon-edge adjudication** | PJM fork 3 | Declare the beyond-last-FPR convention (hold-last, per the `forward_net_cone_anchor` precedent, vs the stale composite) as an owner-visible construction choice; intake 2029/30 planning parameters on publication. Changes PJM's FC-1 verdict ⇒ scorer/governance round, alongside the still-open D-1 checker year-drop. |
| **S-6** | **PJM T1-F ledger run** | PJM fork 2 | The §5.1 minimum run, AFTER S-5 sets the bar. Solo heavy slot; register + commit `run_config.json`. NEISO/MISO single-purpose ledger runs (§2.5, §4.2) fold into their intake lanes' verification solves rather than standing alone. |

CAISO: **no new lane** — B-1..B-8 stand, ordering endorsed (§3.2–3.3).

---

## 9. Governance

* **No solve, no scoring, no registration.** Every number is from a committed artifact or a
  constant at HEAD. Holdout freeze untouched; `complete` = {NEISO, NYISO, PJM} and `final`
  empty as found; no out-of-training year approached (the only run artifacts read are
  committed forecast-mode 2026+ ledgers).
* **No I7-closing fix shipped.** The one candidate meeting the "citation already in repo"
  bar (S-1, the MISO PY 2025-26 pairing) fails the "pure bookkeeping" bar — it changes every
  MISO solve and shares machinery with the backcast-reachable reliability floor — so it is
  routed, not shipped, with its expected effect stated in advance so it cannot be
  back-fitted (rules 13/21/23).
* **Rule 28: no matrix cell edited, none required.** No mechanism was proposed, tested, or
  armed; no `ScenarioConfig` field added. The one fc-posture observation touching a cell —
  `caiso_nqc_accreditation` (cell O) — is left exactly as FFR-3P recorded it; the committed
  `caiso-nqc-armed` twin measurement (§3.2) is *evidence for that cell's eventual
  adjudication*, flagged here for the CAISO lane rather than edited into its shard.
* **Deconfliction:** no backcast keeper shard, `status/*.js`, `calibration-complete.json`,
  offer curve, commitment bridge, or `src/market_sim/` file touched. MISO root causes that
  reach shared solve machinery (S-1) stop at this finding per the charter.
* **Two director cross-references:** S-2 is the MISO analogue of the ISSUED
  `D2-NYISO-INTAKE`; D9 (MISO SOCO interchange fallback) should ride with any MISO
  re-measure (§2.5), per the director's own sequencing note.

---

## 10. Recommendation

1. **Charter S-1 + S-2 + S-3 together as the MISO adequacy package** — the three terms are
   independent, all named, all published-source; together they plausibly account for the
   whole 6,037 MW base-year gap, and none may be sized against the residual.
2. **Charter S-4 before reading anything into NEISO's 2028 row** — 218 MW is inside one
   uncited input's band.
3. **Run S-5 before S-6** — measuring PJM's supply side against a requirement that drops
   3.2 % of peak at the FPR table edge would waste the solo heavy slot.
4. **For CAISO, execute B-1 first** (FFR-3P's ordering, now backed by horizon evidence):
   most of the 14 GW administrative-CT ladder — and with it the 65.5 % backstop share and
   much of the I12 FAIL — is downstream of the storage-fleet vintage.
5. **Do not treat any base-year leg as a capacity-evolution failure in the D7 re-score**
   (extends the D2 recommendation program-wide, §7).
