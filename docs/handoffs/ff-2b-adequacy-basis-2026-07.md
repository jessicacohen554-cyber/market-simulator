# FF-2B — Base-year adequacy-basis closure (CAISO / NEISO / NYISO I7) — 2026-07-19

**Lane.** FF-2B of `docs/forecast-development-plan-2026-07.md` §6 (frontier row
§1.2-5: "I7 FAILs at 2026 for CAISO/NEISO/NYISO; NEISO requirement is a NERC
stand-in"). Reconciles each ISO's **base-year (2026) accredited-supply ledger**
against its **requirement** on the ISO's OWN published basis, using PJM (which
PASSES I7 after W2-D) as the worked A/B; replaces the NEISO NERC-reference-margin
stand-in with ISO-NE's own Net ICR; and produces NEISO's first capacity-hindcast
pair. **Every new number is an ISO-published, forward-regenerable parameter with
a primary-source citation — none is tuned to clear I7 (CLAUDE.md rules 5/13; the
W2-D discipline, kept verbatim).**

Model note: FF-2B also fixed a latent blocker — a missing `UNSET` import in
`runner.py` (introduced by the miso-76 `miso_zonal_loss_surface` merge `2ad50aa`,
2026-07-19) that raised `NameError` on **every** forecast-mode run (the
`else UNSET` branch is taken whenever `miso_zonal_loss_surface` is off, i.e.
always by default). One-line import fix; without it no forecast run — including
this lane's — can execute.

**Scope note (2026-07-19, owner):** NYISO stays in scope for the base-year I7
*reconciliation* (forecast-mode, quarantine-legal for any ISO; NYISO's
requirement basis was already settled by FF-3D and is independent of the backcast
keeper that flipped to NOT-YET in the phantom-outage re-audit). No NYISO ≤2021 /
hindcast / holdout work was done (never in scope; NYISO's marker is withdrawn).

---

## 1. Headline

| ISO | I7 before | I7 after | What moved it | Residual (routed) |
|---|---|---|---|---|
| **NEISO** | **FAIL** 27,171 < 28,797 | **PASS** 27,738 ≥ 24,951 | Net ICR requirement (0.157→0.110) + cleared FCM demand resources + cleared imports — all ISO-NE's own published FCA 17 values | none (I7 **and** I12 clear) |
| **CAISO** | **FAIL** 42,734 < 57,306 | **FAIL** 46,105 < 57,306 | +3,371 MW firm RA imports (DMM-measured) | hydro exclusion (3,601 MW, FF-1C) + peak-currency + VRE/storage ELCC (CR-3.1) |
| **NYISO** | **FAIL** 30,322 < 32,121 | **FAIL** 30,322 < 32,121 (unchanged) | nothing — requirement basis already correct (FF-3D ICAP→UCAP 0.8679) | hydro exclusion (3,343 MW, FF-1C) ≈ the entire gap |

**The central finding refines the plan's §1.2-5 hypothesis.** The base-year I7
failures were hypothesized to be a single *accreditation/requirement basis*
mismatch (the #1532 flag). Reconciling each ledger on the ISO's own basis shows
that is true for **NEISO only**. **CAISO and NYISO are dominated by a
ledger-structure gap that is NOT a basis mismatch: hydro is dispatched but never
enters the accredited-supply ledger** (`accredited_firm_capacity_mw` is built
from the persistent `fleet`, which excludes hydro — hydro is handled as an
energy-limited resource in the *dispatch* fleet only). PJM passes I7 because it
has negligible hydro *and* its basis mismatch (DR + ties) was the whole story;
CAISO/NYISO have GW-scale hydro, so closing their basis alone cannot close I7.
The hydro-in-ledger fix is FF-1C's charter (plan §1.2-6) and is routed there with
a precise spec (§4); this lane applies the in-lane cited basis fixes and does not
tune to force CAISO/NYISO closed (rule 1/11 — a residual closable only by an
out-of-lane fix is an open root cause, not a licence to over-credit imports).

---

## 2. Per-ISO reconciliation (base-year 2026, the ISO's own basis)

Every ledger below is the model's own base-year snapshot
(`evolution_2026.json`); supply = `accredited_firm_capacity_mw`, requirement =
`resolve_adequacy_requirement_mw`. Solves: `run_full_horizon.py --iso <ISO>
--start-year 2026 --end-year 2026` at HEAD defaults, before vs after the
constants/capacity.py change.

### 2.1 NEISO — a true adequacy-basis mis-pairing (CLOSED)

Before ledger (peak 24,890 MW): thermal 24,197 (claimed-capability, R5b — no
EFORd derate) + storage 2,264 + wind 224 (1,400 × 0.16) + solar 486 (2,700 ×
0.18) = **27,171 MW**. Requirement = peak × (1 + 0.157) = **28,797 MW** →
FAIL by 1,626 MW.

Three mis-pairings vs ISO-NE's own FCM construction, all closed with published
FCA 17 (CCP 2026/2027) values (the delivery year covering base-year 2026):

1. **Requirement was a NERC stand-in, not ISO-NE's own.** ISO-NE sizes to a Net
   Installed Capacity Requirement (Net ICR = ICR − HQICC), not a reserve-margin
   %. Replaced `PLANNING_RESERVE_MARGIN_BY_ISO["NEISO"]` 0.157 → **30,305 /
   27,298 − 1 = 0.1102** (Net ICR 30,305 MW / summer 50/50 peak 27,298 MW). The
   stand-in was *too high*; ISO-NE's own margin is lower. Source: ISO-NE ICR
   filing, FERC Docket **ER23-405-000** (2022-11-08): ICR 31,306, HQICC 1,001,
   Net ICR 30,305 (p.2-3); 50/50 peak 27,298 (p.9-10, 2022 CELT, "Net with
   Reductions for BTM PV" — same basis as the model's EIA-930 demand). Flip memo
   R-7(i).
2. **Demand resources omitted.** ISO-NE's FCM clears Demand Resources (EE, load
   management, DG) as capacity SUPPLY against Net ICR — FCA 17 cleared **2,940
   MW** (press release 2023-03-10). Added `ADEQUACY_DEMAND_RESPONSE_FRACTION_BY_
   ISO["NEISO"] = 2,940 / 30,305` (rule-14 reconciliation, divided by Net ICR
   like PJM's DR — so the peak-netting reproduces supply-side counting).
3. **Imports omitted.** FCA 17 cleared **567 MW** of imports (NY/QC/NB) holding
   CSOs. Added `ADEQUACY_EXTERNAL_TIE_FIRM_MW["NEISO"] = 567` (HQICC's 1,001 MW
   tie benefit is separately already netted in Net ICR — not double-counted).

After ledger: supply 27,171 + 567 = **27,738 MW**; requirement (peak × (1 −
0.0970) × 1.1102) = **24,951 MW** → **PASS** (reserve margin 11.4% now also
clears the Net-ICR-implied I12 band; the after-run is **0 FAIL / 0 WARN**).

Sanity vs ISO-NE's own auction: cleared 31,370 MW (gen 27,864 + DR 2,940 +
imports 567) ≥ Net ICR 30,305 (+3.5%). The model's reconciled ledger reproduces
the same structure; the model's slightly higher margin (+11% vs +3.5%) is the
model's 2026 peak (24,890) sitting ~9% below ISO-NE's 27,298 CELT 50/50 peak — a
demand-currency wedge (FF-1C), not a basis error.

### 2.2 CAISO — a small basis mis-pairing over a hydro-dominated gap (IMPROVED)

Before ledger (peak 49,831 MW): thermal 30,222 (UCAP 1−EFORd) + storage 7,432 +
wind 1,120 + solar 3,960 = **42,734 MW**. Requirement = peak × (1 + 0.15) =
**57,306 MW** → FAIL by 14,572 MW.

In-lane basis fix (cited): **firm RA imports omitted.** CAISO's CPUC RA credits
imports as capacity-backed must-offer supply. The model's WECC_import node hosts
imports in *dispatch* but the accredited ledger (fleet-based) omits them. Added
`ADEQUACY_EXTERNAL_TIE_FIRM_MW["CAISO"] = 3,371 MW` — the measured average system
RA "Imports" capacity (DMM Annual Report 2024, Table 15.6), which is exactly the
model's own firm CAISO import tranches (`IMPORT_TRANCHES["CAISO"]`:
PNW_hydro_base 1,566 + DSW_solar_PV 1,805). **Not** the 16,148 MW Maximum Import
Capability — the MIC is a deliverability *limit*, not the RA capacity actually
contracted; crediting it would overstate and would be tuning toward the gap.

After ledger: supply **46,105 MW** vs requirement 57,306 → still FAIL by 11,201
MW. That residual is NOT an adequacy-basis mismatch and is deliberately not
closed here (rule 1/11):
- **Hydro exclusion (≈3,601 MW nameplate, FF-1C):** CAISO's 25 hydro plants are
  dispatched (energy-limited) but contribute 0 to the accredited ledger
  (`firm_clean_mw = 0`). At CPUC hydro RA QC this is ~1.8–3.6 GW of uncounted
  firm capacity. → FF-1C (§4).
- **Peak currency (FF-1C-demand):** the model's 2026 peak 49,831 MW runs above
  CAISO's CEC 1-in-2 forecast (~46 GW); ~4.4 GW of the requirement is peak
  inflation. → FF-1C.
- **VRE/storage ELCC (CR-3.1):** CAISO's solar/wind/storage RA use published
  ELCC, not the generic 0.16/0.18/duration credits. → CR-3.1.

### 2.3 NYISO — requirement basis already correct; gap ≈ hydro exclusion (DIAGNOSTIC)

Before/after ledger identical (no in-lane constant changed — see below), peak
29,751 MW: thermal 28,428 (UCAP) + storage 1,306 + wind 404 (2,400 × 0.168,
CR-3.1 penetration ELCC) + solar 184 (1,500 × 0.122) = **30,322 MW**. Requirement
= peak × (1 + 0.244) × 0.8679 = **32,121 MW** → FAIL by 1,799 MW.

Reconciliation finding: **NYISO's requirement basis is already on its own
published basis** — the ICAP-stated IRM (24.4%) paired to UCAP supply via the
NYCA ICAP→UCAP translation factor `PLANNING_RESERVE_MARGIN_ICAP_TO_UCAP_RATIO_BY_
ISO["NYISO"] = 0.8679`, implemented by FF-3D (Option B, 2026-07-18). So there is
**no requirement-side basis mis-pairing left to fix**. The 1,799 MW gap is
essentially the **hydro exclusion**: NYISO's 3 hydro plants (Niagara + St.
Lawrence + one more) total **3,343 MW** dispatched-but-not-accredited (`firm_
clean_mw = 0`) — matching the "~3.3 GW NYISO hydro" the frontier already flags
(§1.2-6). At NYISO's own hydro accreditation (~0.5–0.9 for reliable baseload
hydro) this is 1.7–3.0 GW of uncounted firm capacity — ≥ the gap. → FF-1C (§4).
A secondary uncounted-supply item (ICAP Special Case Resources / demand response)
is a real adequacy-basis omission but was NOT credited this session: no clean
primary-source NYCA SCR UCAP figure was located, and NYISO is hydro-dominated
regardless, so adding an uncited number would violate rules 5/24 and risk masking
the hydro cause (rule 11). Flagged for a future NYISO SCR intake.

---

## 3. The capacity.py change (rule-27 core-file edit — in the diff)

`_firm_import_mw(iso)` is a new single resolver (rule 19) in
`src/market_sim/model/capacity.py` for "firm import the ISO's own adequacy ledger
counts," read by `accredited_firm_capacity_mw`. It generalizes the existing
`ADEQUACY_EXTERNAL_TIE_FIRM_MW` mechanism — previously documented as
topology-absent-only (ERCOT/PJM) — to the import-node ISOs (CAISO WECC_import,
NEISO HQ_import), with the no-double-count reasoning encoded at the code site:
the accredited ledger is a static firm-capacity accounting built from the
persistent `fleet`, which never contains the import pseudo-generators (they exist
only in the transient dispatch fleet), so the RA/FCM firm-import credit is purely
additive to the fleet's firm MW and is never derived from dispatch flow. This is
the mechanism that credits CAISO's 3,371 MW and NEISO's 567 MW. Behavior change
is confined to those two ISOs; `iso=None`/ERCOT/PJM are byte-identical.
`tests/test_capacity.py::TestFF2BAdequacyBasis` locks the intent.

---

## 4. Routed residuals (not this lane's charter)

- **Hydro in the accredited ledger (FF-1C).** Hydro is dispatched (CAISO 3,601
  MW, NYISO 3,343 MW, NEISO 30 MW; via the hydro energy-budget path) but is
  excluded from `accredited_firm_capacity_mw` because it never enters the
  persistent `fleet` (`_FIRM_CLEAN_FUELS=("hydro",)` sums to 0 for all three).
  **Spec for FF-1C:** pass the model's own hydro capability to
  `accredited_firm_capacity_mw` as a credited pool (mirroring wind/solar), at the
  ISO's published hydro RA accreditation (CPUC monthly QC / NYISO CAF / ISO-NE
  QC — NOT necessarily the generic 0.50, since CA hydro is seasonally derated and
  NY baseload hydro accredits higher). This is the dominant cause of the NYISO
  I7 gap and a major CAISO contributor. Note: this refines the frontier's
  §1.2-6 characterization — the base-year issue is a **ledger-structure
  exclusion**, not (only) a forecast-year "hydro drops past the EIA-923 vintage"
  data drop.
- **CAISO peak currency (FF-1C-demand):** 2026 peak 49,831 vs CEC 1-in-2 ~46 GW.
- **CAISO/NYISO VRE + storage ELCC (CR-3.1 / P-2C):** published ELCC curves for
  the RA credit of solar/wind/storage.
- **NYISO ICAP SCRs:** a future NYISO SCR/demand-response intake (needs a primary
  NYCA UCAP figure) before an in-lane credit is admissible.

---

## 5. NEISO per-vintage Pass-1B re-score (no LP)

`scripts/validate_capacity_prices.py` (curve price vs cleared price at the
published, fleet-independent reserve position — no solve). NEISO had never been
re-scored (flip memo R-7(ii)). Scoreable delivery years:

| Delivery yr | Cleared $/kW-yr | Pub net-CONE | Model net-CONE | Reserve pos | Model curve | %err |
|---|--:|--:|--:|--:|--:|--:|
| 2020/2021 | 63.6 | 139.7 | 108.9 | 1.045 | 49.7 | −22% |
| 2021/2022 | 55.6 | 96.5 | 108.9 | 1.035 | 62.8 | +13% |
| 2022/2023 | 45.6 | 97.9 | 108.9 | 1.044 | 50.8 | +11% |
| 2023/2024 | 24.0 | 98.2 | 108.9 | 1.063 | 26.7 | +11% |

2024/25–2025/26 publish no cleared price; 2026/27 is ⛔locked (rule 22). The
−22%…+13% residual is the **frozen FCA18 net-CONE anchor** (108.9 $/kW-yr for
every year) vs each vintage's published net-CONE — confirming the flip memo's
"±11–24% frozen-anchor residual" characterization. Reducing it requires
per-vintage net-CONE anchoring in the pricing seam (curve-eligibility lane), not
an adequacy-basis change.

---

## 6. NEISO first capacity-hindcast PAIR

Bands pre-registered **before** the run in
`docs/handoffs/ff-2b-neiso-hindcast-bands-2026-07.md` (standard T-R battery, NOT
widened; band-file commit precedes the run commit in history). Plain hindcast,
EIA-860 2020 vintage, 2021 seed / 2022 bridged / 2023–2025 scored (rule-22
`{2021}` allowance; NEISO calibration-complete marker verified present 2026-07-19
and HOLDS). Scoring target `capacity_actuals_neiso.csv` built from EIA-860
(retire ≈1.0 GW, add ≈3.0 GW, 2021–2025).

Pair:
- `neiso-2021-2025-fixed` — `capacity_market_clearing` off (harness default).
- `neiso-2021-2025-curve` — `--capacity-market-clearing` (CR-1 sloped curve armed
  for NEISO only).

Scored 2023–2025 (2021 seed, 2022 bridge). Both legs FAIL the thermal-retire
band — the first-ever NEISO retirement/addition evidence, and a clean fixed↔curve
contrast:

| metric | fixed | curve-ON | actual |
|---|--:|--:|--:|
| thermal GW retired (cum) | 0.002 (−100%, FAIL) | 9.325 (+880%, FAIL) | 0.951 |
| unit recall >300 MW | 0% (FAIL) | 100% (PASS) | 1 unit |
| false-retire GW | 0.0 (PASS) | 8.433 / 90% (FAIL) | — |
| additions wind+solar GW | 12.0 (FAIL) | 12.0 (FAIL) | 2.17 |
| additions storage GW | 0.0 (FAIL) | 0.72 (+12%, PASS) | 0.642 |

- **Fixed** reproduces the NEISO "retires ~nothing" pathology the equilibrium
  battery flagged (0 MW thermal / 25 yr): it retires 0.002 of 0.951 GW (0%
  recall) — the fixed capacity payment (BLK-9, 1.26–4.92× FOM) makes fossil exit
  arithmetically impossible.
- **Curve-ON** swaps that for a massive **over-retirement wave**: 9.3 GW retired
  (+880%), 8.4 GW false (gas_cc +4552%, gas_st, gas_ct +786%, oil +573%) —
  recall reaches 100% only by over-firing. This is the BLK-9/BLK-10 wave
  signature (PJM/NYISO's curve-ON over-fire), now MEASURED for NEISO for the
  first time, confirming the flip-memo caution that an evidence-free NEISO flip
  would trade the 0-retire pathology for unmeasured over-retirement dynamics.
- **Both legs over-build VRE** (wind+solar 12 GW vs 2.2 GW actual) — the entry
  economics over-clear NEISO VRE (BLK-8 lane; here over- not under-build).

Verdict: NEISO's flip-gate items 3–4 are now **gradeable** (they were "never
measured" — flip memo §1.4) and both FAIL the T-R battery. This is a root-cause
finding for the retirement decision-rule (FF-0C/FF-1A) + entry-stack (BLK-8/
BLK-10) lanes, NOT something to tune (rule 1/11/14; bands not widened). Bundles
`neiso-2021-2025-{fixed,curve}` registered on the forecast-validation dashboard.

---

## 7. Governance self-check

- Every new number is (a) cited to a primary source (ISO-NE ER23-405-000 +
  FCA 17 press release; CAISO DMM 2024 Table 15.6), (b) in `constants.py` and
  surfaced in each run's `run_config.json` (rules 5/24 — no env knob, no getattr
  fallback literal), (c) never reverse-solved to clear I7 (rule 13 — CAISO/NYISO
  are left FAIL rather than over-credited).
- `capacity.py` source edit is in the diff (`_firm_import_mw` + call site +
  docstring); blob-verified after push (rule 27).
- Forecast-mode only; nothing on the backcast dashboard. Hindcast pair inside the
  `{2021}` allowance; no band widened; no 2019 / H1-2026 / locked-test touch.
