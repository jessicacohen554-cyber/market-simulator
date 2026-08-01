# ira-credit-parameters — raw

Source root for the `ira-credit-parameters` clean datatype
(`data/dictionary/schema/ira-credit-parameters.schema.yaml`). Curated by
`scripts/curate_ira_credit_parameters.py`, which reads
`ira-credit-parameters.csv` in this directory and writes schema-valid
Parquet to `data/clean/ira-credit-parameters/ira-credit-parameters.parquet`.

## Why this exists

D5 (bounded gap) in the forecast-driver audit: `ira.py` has §45V (hydrogen),
§45Q (CCUS), and the wind-PTC/solar-ITC dispatch credits, but **no §45U**
(existing-nuclear PTC — nuclear retirement screens see only exogenous
ZEC/EAC support today) and **no 45Y/48E semantics** (the tech-neutral
successors to §45/§48 for post-2024 vintages). Feeds P-1C.

## Sources and fetchability

`irs.gov` and `law.cornell.edu` are reachable in this environment;
`congress.gov` and `federalregister.gov` (redirects to a bot-check page,
`unblock.federalregister.gov`) are not. §45U's text is unambiguous (a single
well-established credit, no conflicting secondary reporting found) and was
read directly from Cornell's Legal Information Institute (26 U.S.C.
transcription of the current statute). §45Y/§48E's OBBBA amendments are
newer (enacted 2025-07-04) and less settled in publicly-indexed secondary
commentary — see the confidence note below.

## RESOLVED 2026-07-31 (FFR-PB): 45Y/48E phase-down verified against PRIMARY text

**The confidence note below is superseded and kept only as the provenance
record.** The FFR-PB session (FR-20 item M2) read the codified statute
directly from the **Office of the Law Revision Counsel** US Code
(`uscode.house.gov`, prelim edition — reachable in this environment, unlike
`federalregister.gov`) and confirmed **every landed value unchanged**:

- **26 U.S.C. §45Y(d)(2)** — phase-out percentage by the calendar year
  construction *begins*, relative to the "applicable year": **(A) first
  following year 100%, (B) second 75%, (C) third 50%, (D) any subsequent
  calendar year 0%.** This paragraph is original IRA text (Pub. L. 117-169
  §13701(a)); OBBBA did not amend it.
- **26 U.S.C. §45Y(d)(3)**, as amended by **OBBBA Pub. L. 119-21
  §70512(a)(2)**, now reads *in its entirety*: *"For purposes of this
  subsection, the term 'applicable year' means calendar year 2032."*
  OBBBA **struck** the prior (d)(3), which had read *"the later of— (A) the
  calendar year in which the Secretary determines that the annual greenhouse
  gas emissions from the production of electricity in the United States are
  equal to or less than 25 percent of [that] for calendar year 2022, or
  (B) 2032."*
- **26 U.S.C. §48E(e)(2)** — the parallel investment-credit table, naming
  **"energy storage technology"** expressly (this is what puts storage in the
  bucket). **§48E(e)(3)** takes "applicable year" from §45Y(d)(3) by
  cross-reference. Both are original IRA text (§13702(a)); OBBBA §70513(a)
  amended only (e)(1) and added (e)(4), the wind/solar termination.

**Applicable year 2032 ⇒ 100% BOC-2033 / 75% BOC-2034 / 50% BOC-2035 /
0% BOC-2036+** — exactly the landed
`phase_down_full_credit_through_boc_year=2033`, `75pct=2034`, `50pct=2035`,
`0pct=2036` and the `ira_other_clean_*` ScenarioConfig defaults. **No value
changed; this is a provenance upgrade only** (CLAUDE.md rule 23).

Two substantive corrections the primary read forced, beyond confidence:

1. The old note's reconstruction guessed the mechanism turned on a
   *"Treasury/IRS-determined applicable year."* Post-OBBBA it does **not** —
   the year is **flat statutory**, with no Secretarial determination at all.
   The `45Y,applicable_year_treasury_determination` parameter **name** is
   therefore a misnomer; it is kept for key stability, with the correction
   recorded in that row's `notes`. Practically this **removes a contingency**:
   pre-OBBBA the steps could have slid later if electricity emissions fell
   fast enough, and they no longer can.
2. Every `source_doc` on the phase-down rows moved from the secondary Sidley
   Austin client alert to the codified sections above; no secondary citation
   remains on any 45Y/48E phase-down row.

Session record: `docs/handoffs/ffr-pb-atb-statute-intake-2026-07-31.md`.

## CONFIDENCE NOTE (SUPERSEDED — historical record only)

Three sources were checked for the exact construction-begin-year phase-down
percentages that apply to non-wind/solar §45Y/§48E facilities (nuclear,
geothermal, hydropower, storage — the technologies this model's capacity
expansion cares about beyond wind/solar), and they did not fully agree:

1. **Cornell LII (law.cornell.edu/uscode/text/26/45Y), AI-summarized fetch**:
   "Full credit applies to facilities beginning construction through 2032;
   thereafter it declines 100%→75%→50%→0% over three years."
2. **Sidley Austin LLP client alert** (direct quote): "phased out starting
   in 2034... in all cases" for non-wind/solar technologies, with no exact
   percentage table given.
3. **A third source (search-synthesized, echoing CLA/Grant
   Thornton/Kirkland & Ellis-style OBBBA client alerts)**: "Facilities that
   begin construction in 2034 will be eligible for 75%... dropping to 50%
   for construction beginning in 2035, and phasing out entirely for
   projects beginning in 2036 or later."

Sources 2 and 3 **agree** (2034=75%, 2035=50%, 2036=0%), and source 1's
"through 2032" is consistent with the *same* rule if Cornell's AI summary is
off by one year on the boundary (the underlying mechanism defines a
Treasury/IRS-determined "applicable year"; "full credit through
applicable_year+1" with applicable_year=2032 gives exactly "100% through
2033, 75% in 2034, 50% in 2035, 0% in 2036" — reconciling all three).
**The landed values (`phase_down_full_credit_through_boc_year=2033`,
`75pct=2034`, `50pct=2035`, `0pct=2036`) follow the 2-source-agreement
(triangulated), not a single unverified fetch** — but this was **not**
confirmed against the actual Treasury/IRS final rule text (the Federal
Register page redirects to a bot-check wall in this environment; see below).
**P-1C should verify against primary text before treating this as
final** — flagged, not silently trusted.

**Also flagged: this conflicts with `scenarios.py`'s pre-existing comment**
(`ira_other_clean_last_full_year: int = 2028` / `ira_other_clean_phaseout_end:
int = 2033`, comment: "100% through 2028, 80% in 2029, 60% in 2030, 40% in
2031, 20% in 2032, 0% after") — a materially different threshold year (2028
vs. 2033) and a different ramp shape (5-step 20%-decrements vs. 3-step
100/75/50/0). That existing value predates this intake and its own
citation/derivation is not documented in-repo; P-1C should reconcile against
whichever the primary statute text actually says, not assume either existing
number is correct by default.

### MANUAL DOWNLOAD NEEDED — CLOSED 2026-07-31

- [x] Confirm the exact §45Y/§48E "applicable year" and phase-down
      percentage table against primary text. **DONE (FFR-PB), and it did not
      need the Federal Register at all.** `federalregister.gov` still
      redirects to the `unblock.federalregister.gov` bot-wall here, but the
      *codified statute* is the controlling authority for these four step
      years, and the Office of the Law Revision Counsel publishes it at
      `uscode.house.gov` — reachable in this environment. See the RESOLVED
      section at the top. A Treasury/IRS *regulation* pull would add nothing:
      §45Y(d)(2)-(3) and §48E(e)(2)-(3) set the years on their face and leave
      the Secretary no determination to make post-OBBBA.

## Expected file

`ira-credit-parameters.csv` — one row per (statute_section, parameter),
columns:

```
statute_section,parameter,value,value_type,unit,notes,source_doc,source_page
```

- `statute_section`: `45U` | `45Y` | `48E`.
- `value_type`: `numeric` | `date` (ISO YYYY-MM-DD) | `boolean` — parse
  `value` (always a string in the file) accordingly.

## Parameter list landed

**45U** (10 params): `base_credit_rate` (0.3 ¢/kWh), `inflation_adjustment_base_year`
(2023), `phase_down_gross_receipts_threshold` (2.5 ¢/kWh),
`phase_down_rate` (16%), `prevailing_wage_multiplier` (5x),
`credit_start_date` (2024-01-01), `credit_end_date` (2032-12-31),
`feoc_sfe_restriction_effective`, `feoc_fie_restriction_effective`,
`fuel_sourcing_restriction_effective`.

**45Y** (14 params): `base_credit_rate` (0.3 ¢/kWh), `enhanced_credit_rate`
(1.5 ¢/kWh), `credit_period_years` (10), `placed_in_service_start`
(2025-01-01), `ghg_emissions_rate_threshold` (0), `applicable_year_treasury_determination`
(2032, ⚠ see confidence note), `phase_down_full_credit_through_boc_year`
(2033), `phase_down_boc_year_75pct` (2034), `phase_down_boc_year_50pct`
(2035), `phase_down_boc_year_0pct` (2036), `wind_solar_placed_in_service_cutoff`
(2027-12-31), `wind_solar_boc_grandfather_deadline` (2026-07-04),
`feoc_material_assistance_boc_restriction_effective` (2026-01-01),
`enactment_date_original_ira`, `amendment_date_obbba`.

**48E** (14 params): `base_credit_rate` (6%), `enhanced_credit_rate` (30%),
`storage_base_credit_rate` (6%), `storage_enhanced_credit_rate` (30%),
`placed_in_service_start` (2025-01-01), `phase_down_full_credit_through_boc_year`
(2033, ⚠), `phase_down_boc_year_75pct`/`_50pct`/`_0pct` (2034/2035/2036, ⚠),
`wind_solar_placed_in_service_cutoff` (2027-12-31), `storage_wind_solar_exemption`
(true), `domestic_content_threshold_pre_20250616` (40%),
`domestic_content_threshold_post_20261231` (55%),
`feoc_material_assistance_boc_restriction_effective` (2026-01-01).

## DATA (landed)

- [x] `ira-credit-parameters.csv` — 39 rows (10 + 14 + 14 + 1 duplicate-named
      `feoc_material_assistance_boc_restriction_effective` counted once per
      section).

## Consumer

None yet (intake only this session). Future consumer: `ira.py`'s §45U credit
function (threaded through the same attribute-revenue seam EAC/ZEC uses,
`max(45U, eac_price_nuclear, ...)` per the audit plan) and 45Y/48E
tech-neutral phase-down semantics replacing the current binary
`ira_wind_solar_last_year`/`ira_other_clean_*` cliff fields where the
statute is actually a ramp (P-1C, cited to this data per CLAUDE.md rule 23).
