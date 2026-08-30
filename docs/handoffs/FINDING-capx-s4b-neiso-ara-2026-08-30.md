# FINDING — capx-S4b: NEISO ARA requirement re-vintage (the S-4 §6.3 successor)

**Session:** S-4b NEISO ARA REQUIREMENT RE-VINTAGE (director refresh #13 charter, ledger §0j;
queued by S-4's own finding §0.4/§6.3). Dispatched after D14's merge (`a6e68e2`), branch
`claude/capx-s4b-neiso-ara-3jhedd`.
**Status:** §§1–4 written and committed BEFORE any solve (rules 13/21 pre-declaration
discipline; S-4V §5.1 is the model case). §§5–6 carry the measured pair and were written after.

## 1. What this is

Rule 23 `[R-FROZEN-DERIVE]` intake on publication: ISO-NE's **Nov 21 2025 ARA ICR filing**
restates the capacity requirement for the CCP the model's NEISO adequacy anchors are
vintage-anchored to (CCP 2026/2027), and S-4 measured the implied move at ≈ +380 MW — larger
than the 218 MW 2028 gap the hydro repair addressed. S-4 could not ship it because the filing
carries no demand-resource companion and an unpaired swap would break the same-cycle
discipline D2-B verified as fork-3 CLOSED (S-4 finding §6.3). This lane's charter: locate the
companion first; ship nothing if it isn't published.

## 2. The companion is LOCATED — S-4's "no clean ARA-cycle DR total" is closed

The filing itself names its companion family: its peak-load values embed the Passive Demand
Response reconstitution adjustments "listed in Section 6.3 of the 2025 CELT Report"
(testimony pp. 10–11). The CELT workbooks publish the demand-resource **CSO totals per CCP at
labelled auction vintages** in sheet 4.1 "Summary of CSOs" (ISO New England Total → DCR
Total), and the **2026 CELT's CCP 2026/27 column is labelled "Includes ARA 3 Results"** — the
same-cycle companion of the filing's ARA-3 requirement values. The vintage ladder as
published (summer CSO, MW):

| snapshot | CCP 2026/27 DR CSO | CCP 2026/27 net import CSO |
|---|---:|---:|
| FCA-17 initial results (shipped) | 2,940 | 567 |
| 2025 CELT 4.1 (incl. ARA 1) | 2,898.441 | 564.079 |
| **2026 CELT 4.1 (incl. ARA 3)** | **2,639.682** | **409.31** |

**The pairing rule.** The shipped FCA-17 trio paired the pre-auction requirement filing
(Net ICR 30,305, ER23-405-000) with the auction-outcome DR (2,940 cleared). The exact ARA-3
analogue pairs the Nov 21 2025 filing's requirement FOR ARA 3 (Net ICR 30,050 / peak 26,648 /
HQICC 1,009, filing p.12 — transcription verified against the PDF text) with the CSOs
INCLUDING ARA 3's outcome. The 2025 CELT (ARA-1) rung is kept on the committed record but is
not the adopted vintage: it predates ARA 2/3 of the same cycle.

Sources (sha256-pinned; committed extract + provenance:
`data/raw/capacity-market/icr-ara/neiso/`, re-fetch
`scripts/data/fetch_isone_ara_requirements.py`):
- ARA ICR filing (2025-11-21): `iso-ne.com/static-assets/documents/100029/icr_for_aras.pdf`
- 2026 CELT (2026-05-01): `iso-ne.com/static-assets/documents/100035/2026_celt.xlsx`
- 2025 CELT (2025-05-01): `iso-ne.com/static-assets/documents/100023/2025_celt.xlsx`

## 3. The intake — four values, zero free parameters

All from the ARA-3 restatement of CCP 2026/27 (`config/capacity_market.py`):

| registry entry | was (FCA 17) | now (ARA 3) |
|---|---|---|
| `PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]` | 30,305/27,298 − 1 = 0.11015 | 30,050/26,648 − 1 = **0.12766** |
| `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_ISO["NEISO"]` | 2,940/30,305 = 0.09701 | 2,639.682/30,050 = **0.08784** |
| `ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"]` | 567.0 | **409.31** |
| ⇒ DR-netted requirement factor (1−f)(NetICR/peak) | 1.0024544 | **1.0286103** |

The import credit moves with the set because it is the same-cycle restatement of the FCA-17
cleared-import supply term (same CELT column) — holding it at 567 against an ARA-3
requirement would mix vintages inside one adequacy comparison, the exact defect this lane
exists to avoid. HQICC (1,009 at ARA 3) stays netted inside the Net ICR, never
double-counted. The 2027/28 ARA-2 values (29,855 / 26,417 / 1,041) are on the committed
extract but NOT adopted: the registry's vintage anchor remains the CCP covering the 2026
forecast base year, per the standing convention; a CCP re-anchor is a separate decision
(and the reformed prompt-schedule CCP 2028/29 set, expected late 2026/early 2027, would
supersede this one — re-derive then, rule 23).

This is data intake, not a mechanism: the requirement term's *representation*
(`resolve_adequacy_requirement_mw`, one requirement/two verbs) is untouched, so no
mechanism-matrix cell is minted (rule 28 duty c does not fire — no new `ScenarioConfig`
field).

## 4. PRE-DECLARED expectation (recorded and committed before any solve)

**Charter-time arithmetic (recorded at r#13, before the companion was found):** ≈ +380 MW of
requirement (holding the DR share) vs the +229 MW D2-B-basis post-hydro 2028 clearance ⇒
2028 plausibly re-opens ≈ −151 MW and NEISO's leg (b) PROMOTE-WITH-CAVEATS may flip back.

**Measured-companion arithmetic (this session, still pre-solve).** The located companion
makes the move LARGER than charter-declared, in the honest direction (DR shed obligations
through the ARAs, so less nets off; the import CSO shed 157.7 MW of supply):

- Requirement factor Δ = +0.0261559 ⇒ +651.0 / +659.5 / +668.1 / +676.7 / +685.5 MW of
  requirement at the S-4V peaks (2026…2030).
- Firm-import credit Δ = −157.69 MW in every year.
- Applied to the S-4V measured I7 ledger (control basis — today's HEAD is S-4V's treatment),
  the ARITHMETIC lands at:

| year | S-4V I7 | Δ requirement | Δ imports | arithmetic I7 |
|---|---:|---:|---:|---:|
| 2026 | +4,183.5 | −651.0 | −157.7 | **≈ +3,374.8** |
| 2027 | +928.0 | −659.5 | −157.7 | **≈ +110.8** |
| 2028 | +545.4 | −668.1 | −157.7 | **≈ −280.4 (FAIL)** |
| 2029 | +468.7 | −676.7 | −157.7 | **≈ −365.7 (FAIL)** |
| 2030 | +1,341.4 | −685.5 | −157.7 | **≈ +498.2** |

**Known endogenous responses, directions declared in advance** (the solve measures the net;
none is a reason to expect the arithmetic to hold exactly):
1. **Retirement floor** — the floor tests the SAME requirement (one requirement, two verbs),
   so a higher factor blocks marginal exits. S-4V measured the loosening twin of this
   response at 324.9 MW of additional admitted gas-CC exit; the tightening direction
   should claw some firm MW back.
2. **Reserve-margin backstop** — `resolve_reserve_margin_build_enabled` resolves ON for
   capacity-market NEISO, so a residual gap the floor cannot close may be BUILT closed:
   I7 can read PASS mechanically while the deficit surfaces as a **backstop-share rise**
   (the row-4 metric that read 11.7 % CAVEAT at the epoch and 0 % PASS in S-4V). A 2028
   "clear" bought by backstop builds is REPORTED AS SUCH, never as organic adequacy.
3. 2026 is the base year (no evolution): the arithmetic should be near-exact there —
   the isolation check, S-4V §5.3-style. Expected 2026 delta ≈ −(651.0 + 157.7) = −808.7 MW
   of I7 margin to within demand-drift noise.

**The honest-outcome clause (charter §3, verbatim discipline):** if 2028 (and now
plausibly 2029) re-opens and leg (b) flips back, THAT IS THE HONEST OUTCOME — reported at
full magnitude; the sourced 0.7352 hydro factor is not touched, nothing is offset or
re-tuned to keep 2028 clear. **A result landing just clear of the gap is the suspicious
one.** If the measurement contradicts the arithmetic beyond the declared response channels,
the contradiction is the headline and an attribution question — never a reason to revert a
sourced input (rule 14).

**Run construction (declared):** one control/treatment pair at one HEAD, mirroring S-4V
§5.1 —
```
MALLOC_ARENA_MAX=2 MARKET_SIM_HIGHS_THREADS=1 OMP_NUM_THREADS=1 \
  python scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
  --golden-posture --out-dir results/ff-t1f-s4b-ara/<arm>
```
- **TREATMENT** (`neiso`, run id `neiso-2026-2030-s4b-ara`): HEAD as committed — the
  re-vintaged set is the default registry construction, no flag.
- **CONTROL** (`neiso-control`, run id `neiso-2026-2030-s4b-ara-control`): identical
  invocation with exactly ONE local, uncommitted edit — the three registry values reverted
  to the FCA-17 prints (0.11015 / 0.09701 / 567.0) for the duration of the solve, then
  restored from HEAD. Diagnostic arm for attribution only, never a shippable configuration.
- The three constants are registry values, not `ScenarioConfig` fields, so both arms share
  one cache key and byte-identical `run_config.json` (the S-4V precedent, stated in
  advance): the labelling lives in the run ids, sidecar meta (`s4b_arm`), verdict keys, and
  this finding. Years sequential within each run (rule 12); NEISO T1-F is the light leg
  (S-4V: 7.5 min / 3.25 GB).
- Registration (single path, `scripts/register_forecast_run.py --summary`): treatment takes
  the bare **`neiso-t1f`** key; the S-4V vintage is preserved under **`neiso-t1f-s4hydro`**
  (exactly as S-4V preserved FFR-3A-2 under `-ffr3a2`); control registers as
  **`neiso-t1f-s4bcontrol`**. Backcast namespace untouched.

---

*(Sections below were written AFTER the solves.)*

## 5. The measured pair

TBD — filled by this session after the solves.

## 6. Registration + board refresh

TBD — filled by this session after registration.
