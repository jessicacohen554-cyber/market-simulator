# FINDING miso-185 — the SOUTH FIRM-EXPORT EVIDENCE HUNT closes **V-NEG-ABSENT, sharpened by V-NEG-SPOT evidence: the miso-182 §6b re-open data does NOT exist.** Twelve quarters of seller-scoped FERC EQR show every MISO-South jurisdictional seller selling to MISO + affiliates ONLY (no pool customer, no pool delivery-BA, largest cross-seam trace $1.9K/quarter); the GFA inventory carries zero Entergy-legacy rows; and TVA's own disclosures put the real MISO→TVA leg on RESERVED-TRANSMISSION + MARKET (SPOT) PURCHASES — the rule-13-inadmissible form. `miso_south_firm_export_block` STAYS `G` with its re-open NARROWED; the D-4 posture question goes to the owner with the ~1.3 GW scarce-export model-class concession as the honest residual. NO LP

**Session miso-185 (2026-08-25).** Executes
`PREREG-miso185-south-firm-export-evidence-hunt-2026-08-25.md` (committed and
pushed at `9b1b2b4` **BEFORE any source was touched**; the probe at `1208d3d`;
the evidence corpus at `ac0ad78`, in the prereg's own order). **NO LP SPENT.
Keeper `2026-08-22-miso-177-rho-measured` (`miso177_rho_B`) UNCHANGED; nothing
armed, no `ScenarioConfig` field created, no run registered** (rule 15 not
engaged; the miso-142…184 no-LP precedent). Determination unchanged: **NOT-YET
on C3a-2025 alone**, C3c the single ledgered caveat. **No matrix cell
minted** — no mechanism-in-kind was tested (the conditional build's license
never fired); the standing `miso_south_firm_export_block` `G` cell gets its
evidence line updated in MISO's shard (rule 26(b) engages via that update +
the §5.4 queue stamp + calibration-log entry).

Instrument: `scripts/probes/_miso185_firm_export_hunt.py` →
`results/calibration/_miso185_firm_export_hunt.json` + the committed
698-report PDF corpus `results/calibration/_miso185_eqr_pdfs/`.

## 0. The verdict

**V-NEG-ABSENT, by the pre-registered mapping** (PREREG §4): every rung of the
§2 source ladder carries a verdict, and **no qualifying obligation** — a firm
physical power sale from a MISO-South resource to a seam-pool counterparty
with stated term ≥ 1 year and stated MW — exists anywhere in the record.
B_y = 0 in all three years; the conditional build (PREREG §5) is not licensed;
the A/B was never run.

Sharpened by the **V-NEG-SPOT** evidence class (found, and affirmatively
classifiable): where the measured scarce-hour MISO→TVA flow has an external
contract face at all, that face is **TVA's market (spot) purchases supported
by reserved firm transmission** — TVA's own 10-Ks state the construct
(2,792 → 4,750 → 3,750 MW of RTO transmission reserved FY2023→FY2025 "to
support purchases from the market", terms ≤ 6 years) — plus a **sub-year**
FY2023-only "Delivered Energy" bridge class (3 contracts, 1,050 MW, absent
from both the FY2022 and FY2024 tables). Both fail rule 13 by construction:
no stated multi-year term × MW pair exists to regenerate a block from. The
transmission reservation is a real, term-bearing object — but it is
transmission, not an energy obligation (PREREG E-2: corroboration-class,
never sizes B_y).

**Consequence.** The miso-184 §5 roads now stand: road 1 (this hunt) is
CLOSED NEGATIVE; what remains is the upstream Midwest-stack internal-direction
object (standing falsifiable prediction unchanged: flip the scarce-hour RDT
toward the measured 32/47 S→N record), a new state-conditioned
mechanism-in-kind (owner charter), or **the honest model-class concession:
~1.3 GW of scarce-set South export (the miso-184 GAP) that no admissible
mechanism currently carries, sitting inside the C3a-2025 miss.** The D-4
determination-posture question goes to the owner with that concession as the
residual (§6).

## 1. E-0 — the seller set (in-repo, frozen method)

326 MISO-South plants (EIA-860: BA = MISO ∧ state ∈ {AR, LA, MS, TX}),
57.9 GW. All named incumbents present. The jurisdictional seller panel:
the six Entergy opcos + Entergy Power + Entergy Services + System Energy
Resources, Cleco Power + Cleco Cajun, Louisiana Generating, NRG Cottonwood
Tenant + Cottonwood Energy, NRG Business Marketing, Plum Point, Carville,
Bayou Cove, and the two co-op G&Ts that DO file EQR (AECC, Cooperative
Energy (MS)); plus the reverse-screen entities (MISO Inc., TVA, AECI, SEPA).
Declared bound carried: pure marketers with no South plant are out of
scope-by-seller (bounded in §3).

## 2. E-1 — the FERC EQR screen (the load-bearing rung)

**Access route** (recorded for successors): the EQR Report Viewer's summary
reports are served **session-free** as ~3–4 KB PDFs from
`Summary_Report.aspx?RptType={Company|Region}&PeriodYear=Y&PeriodNumber=Q&RespondentId=CID&SellerId=CID`.
`Company` = "Energy Sales and Bookouts by Customer" (top-10 by revenue, with
a coverage row); `Region` = "Energy Sales and Bookouts by Balancing
Authority" (delivery-point BA, **exhaustive** — no top-10 cap). Seller CIDs
are **period-specific**: the viewer's per-period seller list must be walked
(2 WebForms postbacks per quarter) before the GETs. The Selective-Filings
full-CSV route is **email-gated** (link mailed to a provided address) —
unreachable for this environment and recorded as such. Total retrieval
≈ 30 MB — far inside the Q-C budget; quarters 2023Q1–2025Q4 only.

**Instrument defect, disclosed against my own screen** (the miso-184
discipline): the first sweep applied 2025Q3's seller CIDs to all 12 quarters;
a CID valid for one period renders any other period's report header over an
**empty body**, so that sweep silently adjudicated only 2025Q3. Caught by the
all-quarters-empty pattern, root-caused via a sessioned Q1-2023 replay
(different CID, real data), preserved in the JSON
(`e1_v1_defective_period_cids`), and re-run correctly. The corrected sweep:
**698 seller-quarter reports, 12/12 quarters, 0 fetch failures.**

**Result: 72 pool-token hits, ALL in exactly four families, none a
MISO-South→pool sale:**

| family | what it is | classification |
|---|---|---|
| AECI (own filing, 24 hits) | sells to MISO/PJM/SPP/marketers; delivers ~1.0–1.1 TWh/qtr **INTO** the Entergy-Arkansas BA | the measured **IMPORT** side (−0.44 GW pool leg), corroborated |
| TVA (own filing, 24 hits) | "TVA fence" off-system sales to Duke/Southern/LG&E, ~0.05–0.12 TWh/qtr, delivered in TVA's own BA | TVA→others, not MISO's seam; trivial |
| "Cooperative Energy Inc (An EMC)" C001933 (12 hits) | sells to Georgia EMCs, delivered in SOCO BA | **name-collision** with the MS G&T — no MISO-South nexus |
| ENTERGY ARKANSAS (12 hits) | "Associated Electric Coop., Inc. — 3 lines" in EVERY quarter, **$1,188–$1,919 per quarter**, quantity blank | a standing interconnection-agreement trace (the 1957-fence class), ≈ 5 orders of magnitude below the object |

**Every other panel seller — all six Entergy opcos, Cleco, LaGen, the NRG
fleet + marketing arm, Plum Point, Carville, Bayou Cove, AECC, Cooperative
Energy (MS) — shows sales to MISO + affiliates ONLY, and delivery-BA rows
only on the MISO side (incl. the legacy "Entergy Arkansas, Inc." TSIN
label), in all 12 quarters.** The MS G&T Cooperative Energy is 100 % MISO
(e.g. 2025Q3: 337,881 lines, 3.87 TWh, customer = MISO, sole delivery BA =
its own legacy South-Mississippi area). Where the by-customer top-10
coverage is < 100 % (NRG Business Marketing, 34–85 %; AECI 98–99 %), the
**exhaustive Region report closes the gap: no pool BA appears**, so nothing
below the top-10 was delivered across the seam.

## 3. The coverage bounds (declared, now quantified)

* **Marketers with no South plant** (out of scope-by-seller): bounded three
  ways. (i) The Region reports' "# of sellers in control area" column counts
  **24–34 EQR sellers delivering in the TVA BA per quarter** — and TVA's own
  PPA tables (§5) account for that population class (its own solar/diesel/
  lignite/financing-PPA fleet). (ii) TVA acquired **95–98 % of purchased
  power through the long-term PPAs it lists by state** — none MISO-South —
  with the remainder spot/short-term. (iii) The pool-side G&Ts that would
  buy a firm block (AECI) show the trade running the other way.
* **The RTO's own resale side is invisible**: MISO Inc.'s seller-side
  summaries are EMPTY in all 12 quarters, so a TVA/pool purchase FROM the
  MISO market cannot be seen through this instrument — it is instead
  established by TVA's own disclosure (the reserved-transmission + market-
  purchase construct, §0), and it is **spot by its own description**.
* **SERI and Entergy Services report no energy lines** (empty all quarters)
  — a reporting-visibility note; both are internal-to-MISO-South constructs
  (the Grand Gulf UPSA's counterparties are the four opcos).
* The **FilingInquiries** tab of the viewer was not drilled (two probe
  attempts, non-converging) — NOT-EXHAUSTED, disclosed. It could only add
  contract-grain detail for transactions the summaries already screened.

## 4. E-2…E-5 — the remaining rungs

* **E-2 MISO OASIS (firm PTP reservations): UNREACHABLE** — OATI webOASIS
  refuses both egress routes at transport (client-certificate gate; http
  503, https connection-refused). Corroboration-class by the PREREG
  regardless (a reservation is not an energy obligation). Consistent with
  the standing key-gated-MISO-source adjudications (miso-77 §2c/miso-174
  K-PRE-4).
* **E-3 GFAs: NEGATIVE on the tariff's own inventory.** MISO Attachment P
  (List of Grandfathered Agreements, ATTACHMENTS 38.0.0, eff. 2026-04-19,
  101 pp, retrieved from `docs.misoenergy.org/miso12-legalcontent/`)
  contains **zero Entergy-legacy rows, zero TVA rows, zero PowerSouth
  rows**; its AECI/LG&E/KU entries are all Midwest-side *transmission*
  contracts (Ameren/Southern-Indiana territory). Scope note: this screens
  the MISO tariff's GFA list; an Entergy-legacy agreement living outside it
  would be a jurisdictional sale → visible in E-1, which is clean.
* **E-4 legacy Entergy unit-power sales: NEGATIVE / subsumed by E-1.** The
  surviving named constructs are the SERI Grand Gulf UPSA (internal), the
  MISO–TVA **emergency energy** agreement (filed 2024-10-24; an emergency
  construct, already adjudicated not-a-block at miso-182 §6), and the
  1957-"TVA fence" exchange arrangements (whose live trace is exactly the
  $1–2K/quarter EAL↔AECI row). Any jurisdictional legacy sale would appear
  in the seller's EQR; none does.
* **E-5 pseudo-ties / dynamic schedules: NEGATIVE-IN-KIND, name-probe
  bounded.** No published inventory resolving pseudo-tie MW by counterparty
  at the southern seam exists (market-report namespace unlistable; all
  probed names 404). Structurally, pseudo-tie generation flow is a
  **component of the RDT calculation itself** (MISO/SPP/Joint-Parties
  settlement construction) — the same unapportionable aggregate miso-182
  criterion 2 refused.

## 5. E-6 — the TVA-side corroboration (level class, never sizes B_y)

TVA's FY2023/FY2024/FY2025 10-K PPA tables (SEC EDGAR, CIK 1376986) list
every long-term PPA by state, MW and termination — **no MISO-South entry
exists in any year**. The Mississippi rows are TVA-area or SOCO-side: the
Coal-Mississippi 1 × 500 MW row (expired 2025-11-30) is the
Mississippi-Power/Plant-Daniel class — SOCO BA, a seam MISO essentially
never exports to (0.1–0.3 % of gross export, and net IMPORT in all three
years); Lignite 440 MW = Red Hills (TVA-interconnected); the solar/battery/
diesel MS rows are TVA-area facilities. The MISO-facing rows are **Midwest**
wind (IA/IL, ~450–750 MW) and one Illinois CCGT (479–495 MW) — the
Midwest→TVA contract-path story, not the South's boundary complex (they
cross or transit outside the `L_S − G_S` measure; unit-contingent wind is
not scarcity-coincident in any case). The FY2023-only "Delivered Energy"
1,050 MW class (§0) is sub-year and source-unplaceable ("multiple generating
assets … various states") — fails Q-B(ii) and Q-A both. Two replacement
contracts commencing 2025-12-01/2026-01-01 (200 MW Missouri, 75 MW North
Carolina) post-date the scarce object (summer 2025) and are below/at the
materiality line besides.

## 6. What this closes, and the owner handoff

* **CLOSED NEGATIVE: miso-182 §6b / miso-184 §5 road 1.** The re-open data
  for `miso_south_firm_export_block` does not exist: no EQR-visible firm
  sale, no GFA, no legacy UPS, no by-counterparty contract-path series, no
  TVA-side PPA. The cell **stays `G`** — but its re-open clause NARROWS:
  the seller-scoped EQR route is now EXHAUSTED for the MISO-South
  jurisdictional panel (12/12 quarters, exhaustive-by-BA), so what could
  still re-open the cell is ONLY (a) **contract-grain** evidence (term ×
  MW) naming a MISO-South resource obligated to a pool counterparty — from
  the full-CSV EQR corpus (email-gated here), a FERC docket, or a
  counterparty disclosure — or (b) a published **by-counterparty
  contract-path schedule series**. Another transaction summary cannot; the
  summaries are adjudicated.
* **The positive characterization** (the V-NEG-SPOT sharpening): the real
  scarce-hour export's external face is TVA's **market purchases over
  reserved firm transmission** plus emergency constructs — price-inelastic
  from MISO's side (driven by TVA's own need, exactly the miso-184
  mechanism signature), yet **contract-formless**: no term × MW exists to
  regenerate. A mechanism representing it would have to be
  state-conditioned (the miso-184 §5 road-3 owner charter), not a firm
  block; this finding is affirmative evidence FOR that road and for the
  concession, and against any further firm-block hunt.
* **D-4, the determination-posture question, now fully briefed:** C3a-2025
  (−11.7 %) remains the SOLE failing criterion on a keeper with zero D-4
  conduct failures, C6 attested, C8 PASS all years. The offer family is
  exhausted (miso-179/180); the import-side seam family is adjudicated end
  to end; the export ladder's tail is adjudicated unrepairable in its class
  (miso-184); and the one named data road out is now closed negative. The
  honest residual is **≈ 1.3 GW of scarce-set South export** (miso-184 GAP
  +1.272 GW; miso-183 conservative floor ≥ 0.93 GW) that the model class
  cannot currently carry. The owner's options: charter the Midwest-stack
  internal-direction object, charter a state-conditioned export
  mechanism-in-kind, or adjudicate the posture with the concession ledgered
  — this session recommends none over another and decides nothing.

## 7. Reported against interest

* **The first sweep was defective and would have under-reported the
  screen** (§2): its "clean" 2023–2024 rows were empty renders, not
  negatives. It is preserved in the JSON, superseded, and the corrected
  sweep re-adjudicated every quarter. The two sweeps AGREE on 2025Q3 — the
  scarce-set quarter — which the defective sweep did adjudicate correctly.
* **The screen is transaction-grain, not contract-grain.** Q-B's term test
  was never reached because no candidate obligation surfaced to test; the
  negative rests on the absence of any pool-facing energy line, not on
  contract classification. A qualifying contract with zero 2023–2025
  deliveries would be invisible here — and also irrelevant to a backcast of
  those years.
* **The Company reports cover energy + bookouts only**; a pure capacity
  sale would be invisible. A capacity-only sale moves no scarce-hour
  energy, so it cannot carry the object either — but the bound is stated.
* **The RTO-resale blind spot** (§3) means "TVA bought X TWh from the MISO
  market in 2025's scarce hours" is NOT measured here — only corroborated
  as the construct by TVA's own filings. No number in this finding
  quantifies the spot leg.
* **The marketer bound is bounded, not closed** (§3): 24–34 sellers
  delivered in the TVA BA per quarter and were not individually
  enumerated. A material (≥ 0.1 GW) long-term firm MISO-South→TVA sale
  hiding in that set would have to evade the seller-scoped screen (be a
  non-South-asset marketer), TVA's own PPA tables, AND the GFA/UPS/docket
  record simultaneously — but it is a logical possibility, and re-open
  route (a) names exactly the evidence that would surface it.
* **`Summary_Report.aspx` accepted parameters no UI path produces** (a
  period × CID pair from different quarters) and rendered a well-formed
  empty report rather than an error — the trap behind the v1 defect. A
  successor reusing the route must re-verify the CID-per-period discipline.
* **AECC and Cooperative Energy (MS) file EQR voluntarily-or-otherwise**
  (co-op G&Ts); their clean MISO-only record is evidence, but other
  non-jurisdictional South entities (municipals, LEPA) do not file at all.
  Their combined scale (E-0: ≈ 3.2 GW owned) bounds what could hide there,
  and a co-op selling firm across the seam would appear in the BUYER-side
  corroboration (TVA/AECI records), which is clean.
* The finding quotes the object ONLY on the basis-free measures (−2.441 GW
  scarce outflow / ≥ 0.93 GW floor / GAP +1.272 GW); the retired pool-basis
  +1.19 appears nowhere as a size.

## 8. Standing OWNER items, restated not decided

(1) the C8 provenance-materiality floor (unrepaired); (2) the
committed-vs-regenerated diagnostics exposure; (3) `RHO_CLIP` 0.5 vs the
measured MISO rho 0.1764 (nyiso-144); (4) **D-4 — §6 above, now with the
export-evidence road closed**; (5) the rule-23 Q-Q DA-basis adjudication
(resolved at miso-184; listed for genealogy).

## 9. Governance

Rule 22 `[R-HOLDOUT]`: 2023–2025 only — every EQR retrieval bounded to
2023Q1–2025Q4 (the TVA 10-K PPA tables are contract metadata; the FY-2022
table read establishes a contract-class ABSENCE, no out-of-train market
outcome enters anything); freeze untouched; MISO holds neither marker; no
re-key owed. Rule 15: not engaged (no solve, no run). Rule 26(b): §5.4 queue
stamp + `docs/calibration-log/miso.md` entry + the MISO-shard evidence-line
update for the standing `G` cell, all in-session;
`scripts/check_mechanism_matrix.py` run before the matrix push. Rules 5/13:
nothing from this hunt enters any solve. Rule 27 `[R-PUSH]`: exact on-disk
bytes; every pushed blob ≥ 300 lines verified. No new `.github/workflows`.

**DO-NOT-REDO honoured throughout** (PREREG §7 carried in full): nothing
re-opened `miso_south_export_ladder_rt_tail` `R`,
`miso_seam_coincident_envelope` `R`, `measured_interface_limits` `R`,
`m2m_seam_entitlement_cap` `G`, `import_shape_lever` `G`,
`internal_congestion_split` `G`, `zonal_loss_surface` `R`, the within-unit
`measured_offer_surface` `R`, `gas_hub_basis_overlay` `R`, `ramp_envelopes`
`I`, `dam_availability_rebasis` `R`, the ordc/reserve and dispersion
families, or the `miso_offer_spread_anchored` unspent re-open clause
(untouched; this session may not be cited as graft evidence). The miso-183
basis adjudication is CLOSED and was not re-litigated; `ba_code="SOCO"`
stays a forecast-lane rule-14 item; the import-side ladder tail stays
NAMED, not touched.

## 10. Reproduction

```
cd <repo root>
uv run --no-project --with pyarrow,pandas,numpy,pypdf,requests \
  --python 3.12 python scripts/probes/_miso185_firm_export_hunt.py --e1
```

Reads `data/raw/eia-860/eia860_{plant,generator_operable,owner}.parquet`
(E-0) and retrieves the EQR summary PDFs (cached in
`results/calibration/_miso185_eqr_pdfs/`; the sweep is idempotent over the
cache). Record: `_miso185_firm_export_hunt.json` (`e0_seller_set`,
`e1_eqr_screen`, and the preserved `e1_v1_defective_period_cids`). External
documents cited: MISO Attachment P (docs.misoenergy.org, eff. 2026-04-19);
TVA 10-Ks FY2022–FY2025 (EDGAR accessions 0001376986-2{2,3,4,5}-000{023,022,029,056}).
PREREG: `9b1b2b4`; probe: `1208d3d`; corpus: `ac0ad78`.
