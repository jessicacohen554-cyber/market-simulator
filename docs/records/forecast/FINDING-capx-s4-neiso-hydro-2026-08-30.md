# FINDING — capx S-4: NEISO hydro accreditation — the ISO-NE per-resource SCC intake replaces the generic 0.50

**Session:** capx S-4 NEISO HYDRO ACCREDITATION (capacity-expansion / Forecast Finalization track)
**Date:** 2026-08-30 · **Branch:** `claude/capx-s4-neiso-hydro-syqu7m`
**Charter:** director ledger lane S-4 (`capx-director-ledger-2026-08.md`, issued 2026-08-25),
executing the FFR-1C open item (`ffr-1c-hydro-accreditation-2026-07-31.md` §4) after capx-D2B
measured it LOAD-BEARING (`FINDING-capx-d2b-i7-ledger-2026-08-25.md` §4.3: the generic
`RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50` fallback contributed 949.75 MW to a ledger whose
2028 gap was 218 MW — 4.4×, the verdict's sign inside one uncited input's band).

---

## 0. Headline

1. **The class factor is sourced, and it is 0.7352** — the aggregate of ISO-NE's OWN
   per-resource summer Seasonal Claimed Capability over its ACTIVE conventional-hydro fleet
   (August 2026 SCC Monthly Report: 244 assets, **1,396.472 MW**) divided by the model's own
   accreditation basis (**1,899.5 MW**, 2024 final EIA-923 census — the same population the
   factor multiplies). Zero free parameters; the credited ledger term equals ISO-NE's published
   aggregate capability by construction. Shipped as
   `HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"] = 1_396.472 / 1_899.5`.
2. **Direction was declared before the number was looked at** (§2): below ~0.39 flips 2027 to
   FAIL, above ~0.62 clears 2028 outright. The sourced 0.7352 landed ABOVE the upper
   threshold, and the verification pair (§5) confirms the ledger movement *(S-4V,
   2026-08-30)*: the credited term lands **+446.7 MW, exact to the digit in the 2026
   base-year isolation**, and I7-2028 clears in the treatment by **+545.4 MW** —
   with the honest §5.4 decomposition that the PASS at today's HEAD is
   over-determined (the control clears too, on epoch drift alone).
3. **NEISO's 2028 I7 leg is now decidable — and it reads PASS in every year 2026–2030**
   *(S-4V, 2026-08-30)*: the bare `neiso-t1f` verdict is re-scored
   `HOLD → PROMOTE-WITH-CAVEATS` (I7 PASS ×5; the caveats are the pre-existing
   I12-2026 over-build WARN, now 17.1 %, and the program-wide DOF-ledger gap). The
   D2-B undecidability is resolved twice over — the uncited 0.50 is replaced by the
   published record, and independently the 2026-08 epoch drift closed the old
   218 MW gap on its own (§5.4).
4. **The FCA-vintage refresh half of the charter closes as NO-SWAP, with the newer
   publication reported at full magnitude** (§6): ISO-NE's CCP 2028/29 values — the trigger
   D2-B §4.4 anticipated — are NOT yet published; the newest published requirement set is the
   Nov 21 2025 ARA filing, whose paired adoption is chartered work for a successor, worth
   ≈ +380 MW of requirement (bigger than the old 218 MW gap — reported so it cannot surprise).

## 1. What was wrong, and what is shipped

`HYDRO_ACCREDITATION_CREDIT_BY_ISO` had no NEISO entry — deliberately: FFR-1C located no
ISO-published NEISO hydro class factor and fell back to the generic 0.50 rather than borrow a
foreign ISO's factor (rule 25). The miss was one of construction, not existence: ISO-NE
publishes no class *rating*, but it publishes the **entire per-resource record** the FCM
accredits hydro on, monthly. This session aggregates that record into the class factor the
registry's shape requires.

Shipped (commit 1):

- `config/capacity_market.py::HYDRO_ACCREDITATION_CREDIT_BY_ISO["NEISO"] = 1_396.472/1_899.5`
  (= 0.7352), stored as an explicit expression so both published MW values stay traceable
  (rule 5; the `PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]` precedent), with a full citation
  block. ERCOT is now the registry's only absence (energy-only; unchanged open item).
- `data/raw/capacity-market/scc/neiso/` — the committed per-asset extract
  (`scc_hydro_august_2026.csv`, 244 rows) + provenance README (source URL, workbook sha256,
  re-fetch command).
- `scripts/data/fetch_isone_scc_hydro.py` — the reproducible fetch+derive path (drives the
  ISO Express `docWidgetGetMore` listing endpoint with the `isox_token` bootstrap; assigns
  the summer/winter season blocks from the workbook's own merged header labels and
  cross-foots the whole sheet against `SCC_Report_Summary` before writing anything).
- `frontend/data/parameters.json` + `docs/parameter-citations.md` — curated registry entry.
- `tests/unit/model/test_hydro_accreditation.py` — NEISO moves from the generic-fallback
  assertion to the published-credit assertions.

## 2. The direction declaration (recorded before computation)

Stated in-session before any ISO-NE number was aggregated, per the charter and rules 13/21:

> The D2-B measurement fixes the decision geometry — a NEISO hydro class factor below ~0.39
> flips 2027 to FAIL; above ~0.62 clears 2028 outright; anything between leaves 2028 FAIL
> with the gap rescaled. Whatever value the ISO-NE per-resource record aggregates to ships
> as-is, in whichever direction it moves the verdict, and if the published construction
> cannot be mapped to a class factor on the model's basis, nothing ships and the generic
> 0.50 stays with its load-bearing warning.

The sourced factor (0.7352) landed above the upper threshold. Because the thresholds were
external (D2-B's committed arithmetic) and the declaration preceded the computation, the
result cannot be read as chosen.

## 3. Source and construction

**Source.** ISO-NE **SCC Monthly Report**, August 2026 vintage (published 2026-08-06) —
"A Monthly Listing of ISO-New England Participant Generator Assets … and their seasonal
capabilities":
`https://www.iso-ne.com/static-assets/documents/100038/scc_august_2026.xlsx`
(sha256 `7fbc8e5b…54b5a`, recorded in the intake README). This is the per-resource record
the FCM's Qualified Capacity is *defined from*: summer QC of a non-intermittent existing
resource = the 5-yr median of its summer SCC ratings (Market Rule 1 §III.13.1.2.2.1.1,
eff. 2025-05-03 — primary-tariff research already committed at
`data/raw/capacity-market/accreditation-filings/neiso/README.md`).

**Population.** ACTIVE assets of the hydraulic-turbine unit types HDP (conv. daily pondage,
17), HDR (conv. daily run-of-river, 198), HW (conv. weekly pondage, 29), HL (tidal, 0) —
**244 assets, summer SCC 1,396.472 MW** (winter 1,433.690). Unit type PS
("Hydraulic Turbine - Reversible") = pumped storage is EXCLUDED (7 assets, 1,862.0 MW — a
storage resource in this model, never part of the conventional-hydro pool).

**The intermittent-hydro median-output construction — how it was handled.** It wasn't
approximated; it was inherited. The 200 `Intermittent` assets' summer SCC values carry
ISO-NE's own `Median Reliability Hours Calculation` determination — i.e. the tariff's
intermittent construction is applied by ISO-NE itself inside the published values, at
per-resource grain, before this session ever aggregates them. The non-intermittent 44
assets (1,150.6 MW of the 1,396.5) are audited seasonal claimed capability, the quantity QC
takes a 5-yr median of.

**Season.** SUMMER — the same peak-risk season as the Net-ICR / summer-50/50-peak
requirement construction every other NEISO adequacy anchor uses (and the same summer-column
choice the MISO/CAISO/NYISO registry entries make).

**Denominator discipline (the charter's basis requirement).** The factor divides by
`modelled_hydro_nameplate_mw("NEISO")` = 1,899.5 MW — the model's OWN accreditation basis
(166 EIA-923-reporting conventional-hydro plants, 2024 final census), i.e. the exact
population `_hydro_firm_mw` multiplies the factor back onto. Two properties follow:

1. The credited ledger term is **exactly ISO-NE's own aggregate published capability**:
   1,899.5 × 0.7352 = 1,396.5 MW. Population mismatches *inside* the class cannot inflate
   the ledger — a model plant with no FCM record enters at zero (conservative floor, the
   registry-wide discipline).
2. The ISO-NE workbook's own "Establish value" column is NOT a nameplate (for intermittent
   assets it sits *below* the SCC — it is an audit-establish quantity), so ISO-NE offers no
   usable same-document denominator; the model basis is the only population-consistent one,
   exactly as the charter prescribed.

**Population audit.** Top-of-fleet maps 1:1 to model plants (Moore 1-4 ↔ S C Moore 195.4 MW,
Comerford 2-4 ↔ Comerford 167.8, Great Lakes-Millinocket ↔ Great Lakes Hydro America-ME
138.0, Cabot 61.8 exact, Harris, Wyman, Bellows Falls, Wilder, Vernon, Shepaug, Harriman …).
The only overstatement channel — SCC assets too small for the EIA census (< 1 MW on both
columns) — totals **16.7 MW, 0.9 % of the numerator** (154 tiny settlement-only assets).
It is left in: trimming would introduce a discretionary threshold (a free parameter) to
remove real ISO-NE-listed capability of the class, and the bound is an order of magnitude
inside the factor's own vintage band. Known understatements run the other way (Comerford
unit 1 absent from the ACTIVE list; any non-participating model plant at zero).

**Vintage stability.** The identical aggregation on the August 2024 / August 2025 reports
gives **0.7389 / 0.7063** — a ±2 pp hydrology band that never approaches either decision
threshold (0.39 / 0.62). The registry follows its own convention of holding the newest
published vintage (CY2025 NQC, 2025-26 CAF, PY2025-26 DLOL, 2026/27 BRA all do the same);
re-derive on a newer vintage or census (rule 23), never a residual.

## 4. Rule compliance notes

- **Rule 13 (measured input, not answer):** SCC is a forward-regenerable market input —
  re-published monthly, responds to fleet and hydrology changes, exists for every future
  delivery year. Nothing here reads a model output.
- **Rule 21 (DOF):** zero free parameters — numerator is a published aggregate, denominator
  is the model's own census, both cited; the one judgment call (not trimming the sub-1-MW
  tail) *rejects* a parameter rather than adding one.
- **Rule 19 (one mechanism):** the factor lands in the existing single resolver
  (`resolve_hydro_capacity_credit`); no new mechanism, gate, or `ScenarioConfig` field.
- **Rule 25 (ISO scope):** derived entirely from ISO-NE's own record; no foreign factor.
- **Rule 28 (matrix):** a registry constant with a published citation is an input, not a
  mechanism — no new row. The existing `hydro_accreditation` row's NEISO cell (O since
  FFR-1C) is re-stamped from this session's verification pair (§5).

## 5. Verification — the T1-F pair

*Completed by the S-4V verification session (director ledger lane S-4V), 2026-08-30 —
the verification half S-4's charter owed. §5.1 is the pre-declared expectation,
written and committed BEFORE any run was launched (rules 13/21; S-4's own §2 is the
model case); the sections after it carry the measured results and were written after.*

### 5.1 Pre-declared expectation (recorded and committed before any solve)

**The construction.** One control/treatment pair at one HEAD, years sequential within
each run (rule 12), both arms invoked identically:

```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-s4hydro/<arm>
```

- **TREATMENT** (`results/ff-t1f-s4hydro/neiso`, run id `neiso-2026-2030-s4hydro`):
  HEAD as shipped — the S-4 factor needs no flag; it is the default registry
  construction.
- **CONTROL** (`results/ff-t1f-s4hydro/neiso-control`, run id
  `neiso-2026-2030-s4hydro-control`): identical invocation with exactly ONE local,
  UNCOMMITTED edit — the `"NEISO"` key of `HYDRO_ACCREDITATION_CREDIT_BY_ISO`
  (`config/capacity_market.py`) removed, so `resolve_hydro_capacity_credit("NEISO")`
  falls back to the generic `RENEWABLE_CAPACITY_CREDIT["hydro"] = 0.50`. A diagnostic
  arm for attribution only, never a shippable configuration; the edit is reverted the
  moment the control solve ends. NOTE: the registry constant is not a
  `ScenarioConfig` field, so the two arms share one cache key and byte-identical
  `run_config.json` — the labelling therefore lives in the run ids, the sidecar meta
  (`s4v_arm`), the verdict keys, and this finding, and is stated here in advance.

**Why `--golden-posture` when the charter's invocation sketch said "no flag involved"
— decided and recorded ex ante.** The parenthetical is about the *factor* (a registry
constant, in the default construction, no flag) and that remains true. The posture
flag is required for the pair to be interpretable at all: the live bare `neiso-t1f`
verdict this pair re-scores was measured by FFR-3A-2 under the shipped NEISO T1-F
posture — `--golden-posture`, resolved curve-ON (`ffr-3a2-battery-close-2026-08-03.md`
§2: "everywhere except NYISO"; cache key `9f2cc6ecd30704ca`) — and the D2-B ledger
arithmetic the expectation below is built on reproduces exactly that leg. Since owner
decision C.4(a) B1 (2026-08-03), `--golden-posture` reads the SHIPPED
`ScenarioConfig.capacity_market_clearing_by_iso` field (`{PJM, MISO, CAISO, NEISO:
True}`) — golden posture and shipped posture are one answer, not two. A bare
invocation, by contrast, resolves NEISO curve-OFF through `reference_config`'s
explicit `capacity_market_clearing_by_iso=None` (the P-3A probe pin), which would
overwrite the bare key with a silent posture swap and confound the attribution with
a second difference. The NYISO precedent's "plain like FFR-3A-2's NYISO leg" carries
the same rule — match the ISO's own T1-F posture — and NYISO is simply the one ISO
whose shipped posture IS the plain default.

**The expectation, from D2-B's committed arithmetic**
(`FINDING-capx-d2b-i7-ledger-2026-08-25.md` §4.1/§4.3), stated before any solve:

1. **Hydro ledger term** moves 949.75 → 1,396.472 MW: isolated delta **+446.72 MW**
   (1,899.5 × (0.7352 − 0.50)), conditional on the accreditation basis
   `modelled_hydro_nameplate_mw("NEISO")` still evaluating to 1,899.5 MW at this HEAD
   (verified as an input check before solving; any census drift is reported, not
   absorbed).
2. **2026 (base year — no evolution runs):** treatment − control accredited firm =
   **exactly +446.7 MW**, nothing else moved on the supply side. This is the clean
   isolation leg: a 2026 delta ≠ +446.7 MW CONTRADICTS the expectation.
3. **2028 I7 on the D2-B ledger basis:** 25,386 + 446.7 = 25,832.7 vs requirement
   25,604 → **clears by ≈ +229 MW**. This is the charter's headline expectation. It
   is *ledger-basis* arithmetic: the solved delta may differ because the evolved
   years respond (the reliability floor gains headroom, so the 2027 exit wave — the
   BLK-10 curve-ON over-retirement, 3,297.9 MW single-year — may deepen; the
   backstop's need shrinks; entry screens see different reserve prices). Exits are
   decomposed summing BOTH `retirements` and `confirmed_derates` (D2-B §1 method
   note).
4. **2026/2027 I7 stay passing in both arms** (2027's epoch margin was thin, ≈ +114
   MW at rm 0.70 %; the factor should move it to structurally held).
5. **I12 (FC-2 row 1), pre-declared so it cannot read as a surprise:** 2026 moves
   FURTHER ABOVE the 15.2 % band cap (≈ 15.26 % + 446.7/24,889.7 ≈ **+17.1 %**) — the
   arithmetic consequence of adding real firm supply to a base year already over the
   band; 2028 re-enters the band (≈ +1.1 %). FC-2 row 1 therefore stays CAVEAT (high
   side), and that is a *pre-existing over-build signal at the base year*, not a
   defect of this intake.
6. **Expected determination:** HOLD → **PROMOTE-WITH-CAVEATS** (FC-1 PASS if I7-2028
   was the sole FAIL at this HEAD; FC-2 CAVEAT on the 2026 band; FC-7 CAVEAT on the
   program-wide absent DOF ledger). The backstop share (11.7 % CAVEAT at the epoch)
   should not rise; whether it crosses the 10 % PASS line is not predictable from
   arithmetic and is simply reported.
7. **Control at today's HEAD** is expected to reproduce the FFR-3A-2 shape (I7-2028
   FAIL ≈ 218 MW) modulo epoch drift since 2026-08-03; the control-vs-FFR-3A-2 delta
   IS the epoch-drift disclosure (the NYISO extcap lane's −341.4 MW peak-drift
   pattern), and the treatment-vs-control delta at one HEAD is the clean attribution.

**If the measurement CONTRADICTS this — 2028 does not clear in the treatment, or the
2026 isolated delta is not ≈ +446.7 MW — the contradiction is the headline, reported
at full magnitude, and the factor is NOT touched: it is sourced (rule 14), so a
surprise is a discovered attribution question, never a reason to revert.**

Concurrency check at launch (rule 12): `git ls-remote --heads origin` shows two
in-flight backcast branches (`claude/caiso-south-belly-pricing-24uv07`,
`claude/miso-190-backcast-calibration-okt1cn`); the NEISO T1-F leg is the light,
non-memory-bound run (9.2 min / ≤ 4.3 GB recorded), run solo and sequentially in this
container — inside the ≤ 2-heavy cap whatever those branches are doing.

### 5.2 The measured pair (S-4V, 2026-08-30)

Both arms solved 5/5 years at one HEAD (`6136a29` + this branch's results-only
commits; solve code identical to `6136a29`), sequentially, `--golden-posture`
resolving curve-ON, identical cache key `9a7f68fc7dcac931` (the registry constant is
not a `ScenarioConfig` field, exactly as §5.1 stated in advance):

- **TREATMENT** `results/ff-t1f-s4hydro/neiso` — 7.5 min wall, 3.25 GB peak RSS.
- **CONTROL** `results/ff-t1f-s4hydro/neiso-control` — 7.5 min. The one-line
  reversion was applied for exactly the duration of this solve and then restored
  from HEAD (`git checkout`), verified by re-resolving the credit (0.735179).

Per-year I7 ledger, both arms (firm = peak × (1 + rm); requirement = peak ×
1.0024544, the FCA-17 factor re-verified byte-identical at this HEAD after the S-5
FPR hold-last landing — NEISO has no FPR table entry, so the D-1 year-threaded
checker repair is a no-op here):

| year | peak MW | control firm | control I7 | treatment firm | treatment I7 | T − C |
|---|---:|---:|---:|---:|---:|---:|
| 2026 | 24,889.7 | 28,687.6 | **+3,736.8** | 29,134.3 | **+4,183.5** | **+446.7** |
| 2027 | 25,213.3 | 26,081.3 | **+806.2** | 26,203.1 | **+928.0** | +121.8 |
| 2028 | 25,541.1 | 26,027.3 | **+423.6** | 26,149.1 | **+545.4** | +121.8 |
| 2029 | 25,873.1 | 26,283.4 | **+346.8** | 26,405.3 | **+468.7** | +121.9 |
| 2030 | 26,209.5 | 27,493.3 | **+1,219.6** | 27,615.1 | **+1,341.4** | +121.8 |

**I7 passes in every year of BOTH arms.** Invariants: 0 FAIL / 1 WARN in both — the
WARN is I12, out-years {2026} only (treatment 17.1 %, control 15.3 %, band cap
15.2 %); the epoch's 2028 below-floor excursion is gone in both arms.

### 5.3 Expectation vs. measurement — the scorecard

1. **The isolation is EXACT.** 2026 (base year, no evolution): treatment − control
   accredited firm = **+446.7 MW to the digit** (29,134.3 − 28,687.6), and the
   control's 2026 ledger reproduces the D2-B/FFR-3A-2 epoch ledger **bit-for-bit**
   (peak 24,889.729 identical to the millwatt — zero demand drift, unlike the NYISO
   lane's −341.4 MW — and firm 28,687.6 exact). Both of §5.1's contradiction
   triggers are therefore negative: 2028 clears, and the isolated delta is exactly
   +446.7 MW.
2. **2028 clears — by +545.4 MW, not the ledger-basis ≈ +229.** The D2-B arithmetic
   assumed the epoch ledger otherwise unchanged; the solve decomposes the
   difference into exactly the two responses §5.1 flagged in advance:
   - **Epoch drift (control vs. FFR-3A-2): +641.3 MW of 2028 firm.** The 2027 exit
     wave shrank from the epoch's 3,297.9 MW to **2,606.2 MW** (−691.7) at today's
     HEAD, on the generic 0.50 and an identical demand path and base fleet — so
     **the control clears 2028 (+423.6 MW) with no help from the factor.** (A
     −50.3 MW step-timing residual on the 54.0 MW coal exit — netted in the 2028
     ledger year at HEAD, in 2029 at the epoch — closes the reconciliation.) The
     drift accumulated over 2026-08-03 → 08-30; the one *documented unconditional
     exit-set change* in that window is the FFR-3F G3 cap-grain fix (`2adfb49` —
     the very change FFR-3A-3 re-measured the T1-H battery for). Commit-level
     attribution of the drift was not chartered and is not claimed; the pair
     *measures* its total.
   - **Floor-headroom response (treatment vs. control): the +446.7 MW input credit
     nets to +121.8 MW of equilibrium ledger.** With the credit in place, the
     reliability floor gains headroom and the 2027 retirement screen admits
     **324.9 MW more gas-CC exit** (p55068 North peak 43.8 + committed 87.1;
     p10726 Central econ 194.0 — the treatment's exit set is a strict superset of
     the control's; `confirmed_derates` = 0 in both arms, both keys summed per the
     D2-B method note). 446.7 − 324.9 = **+121.8 MW**, carried essentially
     unchanged through 2030 (builds are identical in both arms: 2029 wind 712.6 +
     solar 1,089.4; 2030 economic gas-CC 1,000 + wind 287.4 + solar 910.6;
     **backstop 0 MW in both arms** — the epoch's 11.7 % share is also a drift
     casualty, not a factor effect).
   The decomposition closes exactly: control +423.6 + equilibrium +121.8 =
   treatment **+545.4**.
3. **I12 landed on the pre-declared numbers.** 2026 moved 15.3 % → **17.1 %**
   (predicted ≈ 17.1 — the arithmetic consequence of adding real firm supply to an
   already-over-band base year, a pre-existing over-build signal, not a defect of
   the intake); 2028 re-entered the band (+2.38 % T / +1.90 % C vs. predicted
   ≈ +1.1 — more clearance, via the drift). 2027 stayed in-band in both arms.
4. **The determination flipped exactly as declared: HOLD → PROMOTE-WITH-CAVEATS**
   (both arms; the treatment is the live leg). One phrasing inconsistency inside
   §5.1 itself, resolved in favor of its own item 5: item 6 wrote "FC-1 PASS if
   I7-2028 was the sole FAIL", but item 5 had already predicted the I12-2026 WARN
   persists — and FC-1 consumes a WARN as CAVEAT — so FC-1 reads **CAVEAT
   (WARN ['I12'])**, not PASS. Mechanical, pre-implied by the declaration's own
   item 5, determination unaffected.

### 5.4 The honest headline: at THIS head, the 2028 sign no longer rides on the factor

D2-B's finding was that at the FFR-3A-2 epoch the 2028 verdict sat **inside the
uncited 0.50 input's band** — undecidable at that input fidelity. The pair resolves
that undecidability *twice over*: the uncited input is replaced by ISO-NE's own
published record (S-4), **and** independently, 26 days of epoch drift closed the old
218 MW gap on their own (+423.6 MW in the control). The intake therefore buys — at
this HEAD — **input fidelity and +121.8 MW of equilibrium margin (+446.7 MW of
credited input), not the sign**; had the drift gone the other way, it would have
been the sign. This is the NYISO extcap lane's "over-determined PASS" disclosure,
reproduced in its NEISO form: there the drift was on the demand side (−341.4 MW
peak), here it is on the retirement side (−691.7 MW of 2027 exits) with the demand
path bit-identical. Per rules 13/14/21 nothing here re-opens the factor: it is
sourced, its direction was declared before computation, and the drift is a property
of HEAD, not of the input.

### 5.5 FC re-score and registration (rule 15, forecast namespace only)

**Bare `neiso-t1f` (the live leg, scored at `60e19610e454`, cache
`9a7f68fc7dcac931`, rubric v1.0 t1f): `PROMOTE-WITH-CAVEATS`** — FC-1 CAVEAT (lone
I12-2026 WARN at 17.1 %; was FAIL ['I7']), FC-2 CAVEAT (row 1 I12; row 3 cobweb
PASS; **row 4 backstop share 0 % PASS** — was 11.7 % CAVEAT), FC-7 CAVEAT (the
program-wide absent DOF ledger, unchanged), FC-8 PASS (7.5 min). The FFR-3A-2
measurement is preserved verbatim under **`neiso-t1f-ffr3a2`** (HOLD), per the
preserve-then-overwrite convention; the control is on the record under
**`neiso-t1f-s4control`** (PROMOTE-WITH-CAVEATS, provenance labelled as the
uncommitted-diagnostic arm); the `-ff2d` baseline is untouched.

Registered runs (single path, `scripts/register_forecast_run.py --summary`):
**`neiso-2026-2030-s4hydro`** (treatment, `verdict_key: neiso-t1f`) and
**`neiso-2026-2030-s4hydro-control`** (labelled diagnostic,
`verdict_key: neiso-t1f-s4control`) — the exact run ids S-4's own `.gitignore`
block pre-declared. Committed per bundle: canonical sidecar
(`frontend/data/hindcast/<id>.json`), `full_horizon_summary.json`,
`run_config.json` (FC-7), `forecast_verdict.json`, per-year
`evolution_2026..2030.json`, resolved `config.yaml`; heavy dispatch outputs stay
gitignored. The generated registry/runs/manifest namespace files remain gitignored
(the Pages deploy is their writer). The backcast registry was not written to.

## 6. The FCA-vintage half — NO-SWAP, newer publication reported

The charter: *"Refresh the FCA vintage in the same session if ISO-NE has published a newer
one (rule 23: on publication, not on a residual)"*, anchored to D2-B §4.4's vintage note
("CCP 2026/27 values are held for 2028; ISO-NE's own 2028/29 values would refresh both
halves together"). Findings:

1. **The anticipated trigger has not occurred.** No CCP 2028/29 ICR set exists: ISO-NE's
   Dec 30 2025 FERC filing proposes the 2028/29 *auction schedule* (qualification deadline
   Feb 2028) — the ICR-related values for 2028/29 will be filed under the reformed prompt
   schedule, expected late 2026/early 2027. There will never be a newer *FCA* vintage at
   all: the final FCA (FCA-18, CCP 2027/28) was held Feb 2024 and PREDATES FF-2B's anchor
   decision, which deliberately chose FCA-17 as the delivery year covering the 2026 forecast
   base year (the convention D2-B verified and closed as fork 3).
2. **What IS newer, reported at full magnitude so it cannot surprise:** the Nov 21 2025
   ARA ICR filing (`https://www.iso-ne.com/static-assets/documents/100029/icr_for_aras.pdf`)
   re-states the held CCP's requirement under updated system conditions —
   **ARA 3 / CCP 2026-27: Net ICR 30,050 / peak 26,648 / HQICC 1,009** (vs the shipped
   FCA-17 originals 30,305 / 27,298 / 1,001), and **ARA 2 / CCP 2027-28: Net ICR 29,855 /
   peak 26,417 / HQICC 1,041**. Because the peak fell faster than the Net ICR, the paired
   requirement factor RISES: (1 − DR/NetICR) × (NetICR/peak) = 1.00245 (shipped) →
   ≈ 1.0174 (ARA 3, holding the DR share) — **≈ +380 MW of requirement at the model's
   ~25.5 GW 2028 peak, larger than the 218 MW gap this lane was chartered on.**
3. **Why it is not swapped here:** the requirement trio (Net ICR, peak, DR) is
   *same-cycle* FCA-17 by construction — the property D2-B explicitly verified as fork-3
   CLOSED. The ARA filing carries no demand-resource companion (the 2,940 MW is
   FCA-17-cycle), and no clean ARA-cycle DR total was located this session; an unpaired
   swap would break the one discipline that makes the construction defensible, inside a
   lane chartered for a different input, while the anticipated 2028/29 publication is
   months away and would supersede it anyway. **Successor charter (director):** adopt the
   newest same-cycle trio when either (a) an ARA-cycle DR companion is located, or (b) the
   CCP 2028/29 set publishes — and expect it to move NEISO's I7 rows by O(gap) in the
   direction of *more* requirement.
4. One mixed-vintage note discovered en route, for the record: `MARKET_DESIGN["NEISO"]`'s
   demand curve is already FCA-18-anchored (Net CONE 108.94, delivery year 2027-2028) while
   the requirement trio is FCA-17 — a deliberate per-anchor vintage choice inherited from
   FF-3D/FF-2B, not a defect introduced or touched here.

## 7. Registration-debt note (pre-existing, not this lane's)

`scripts/validate_parameters.py` FAILs on clean `origin/main` with **46 constants missing
citation entries** (none of them this lane's — verified by stash-and-rerun; this branch
adds one *curated* entry and no debt). The drift spans several lanes' constants
(`ercot_dc_tie_*`, `scenario.caiso_adaptive_*`, `wright_reference_gw.*`, …).
`generate_parameter_registry.py` would auto-add all 46 as `needs-citation` rows; doing so
inside this lane would launder other lanes' uncited constants into the registry under this
session's name, so it was left for a housekeeping round.

## 8. Answer to the chartered question

**Is NEISO's 2028 I7 leg now decidable?** *(Answered by the S-4V verification
session, 2026-08-30 — §5.2–§5.5 carry the measurement.)*

**YES — decidable, and it reads PASS, in 2028 and in every other year of the
window.** The treatment (HEAD as shipped) clears I7 2026–2030 by +4,183.5 /
+928.0 / +545.4 / +468.7 / +1,341.4 MW, and the bare `neiso-t1f` re-scores
`HOLD → PROMOTE-WITH-CAVEATS`. The decidability claim is the stronger half: the
949.75 MW uncited-input band D2-B identified is gone — the hydro term is now
ISO-NE's own published aggregate (1,396.5 MW, +446.7 exact in the base-year
isolation) — and the verdict no longer sits inside any input's uncertainty band.
The honesty rider (§5.4): at this HEAD the *sign* of 2028 is over-determined —
epoch drift since 2026-08-03 (the 2027 exit wave shrank 691.7 MW) clears the year
even on the generic 0.50 — so what the factor buys today is input fidelity and
+121.8 MW of equilibrium margin, with the floor-headroom response (324.9 MW of
additional admitted gas-CC exit) absorbing the rest of the credit. The successor
question this leaves open is S-4b's (§6): the ARA-vintage requirement refresh,
≈ +380 MW of requirement, which is larger than every 2027–2029 margin in the
control arm and would re-tighten exactly the years this pair just cleared —
**S-4b is now charterable** with the pair as its measured baseline.
