# SOCO zonal-load provenance — FERC Form 714, not EIA-930 sub-BAs

`soco_ferc714_hourly_planning_area_demand_2023-2025.parquet` — **hourly
planning-area demand by FERC Form 714 respondent**, 2023-01-01T00 ..
2025-12-31T23 UTC, 210,431 rows over eight respondents. Landed by lane
SOCO-11 (`docs/handoffs/FINDING-soco-11-2026-09-13.md`; charter
`docs/multi-iso/soco-addition-plan-2026-09.md` §2.5, §6 row 2).

## Why this product and not the one every other ISO uses

Every prior addition — MISO's six zones, SPP's seventeen — took its zonal
load from **EIA-930 sub-BA demand**. SOCO cannot: it has no sub-BAs. Measured
at the SOCO charter by listing every `(Balancing Authority, Sub-Region)` pair
in `EIA930_SUBREGION_2023_Jan_Jun.csv`, the product covers
`CISO ERCO ISNE MISO NYIS PJM PNM SWPP` and nothing else.

The substitute is **FERC Form 714, Part 3 Schedule 2 — hourly planning-area
demand**, which each operating company files as its own respondent. That is a
*measured hourly* series per planning area, so it is strictly better than the
annual retail-sales share a lesser source would give, and it is rule-13
`[R-MEASURED]` admissible: it regenerates for a forward year from the
then-current filing and responds to changed conditions.

## Source and route

FERC's own bulk CSV host was probed **403** at the SOCO charter and **403
again from this lane's egress** (exact URLs in the FINDING's blocked table).
The series is taken instead from **PUDL's ETL of the same form**, which
publishes the filed values with a UTC stamp already attached:

    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__hourly_planning_area_demand.parquet
    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/core_ferc714__respondent_id.parquet
    https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__respondents_with_fips.parquet

Pulled **2026-09-13** (nightly build `Last-Modified: 2026-09-11T08:27:22Z`,
339,150,766 bytes). No key, no registration. Respondent names and `eia_code`
are joined from `core_ferc714__respondent_id`; nothing else is added and no
value is modified.

**Schema is the source's own**, sliced to the eight respondents and the
window:

    datetime_utc, respondent_id_ferc714, respondent_name_ferc714, eia_code,
    timezone, demand_reported_mwh, demand_imputed_pudl_mwh,
    demand_imputed_pudl_mwh_imputation_code

`demand_reported_mwh` is FERC's filed value and is the series to use.
`demand_imputed_pudl_mwh` is **PUDL's derived column**, carried for
transparency rather than for consumption: across the window it is flagged on
**550 rows** (`identical_run` 346, `double_delta` 97, `local_outlier_low` 42,
`anomalous_region` 40, `local_outlier_high` 13, `single_delta` 12) and differs
from the reported value by more than 0.01 MWh on **720 of 210,431 rows**
(max 3,479 MWh). No reported value is null.

## The eight respondents, and what each is

| id | respondent | eia_code | role |
|---:|---|---:|---|
| 2 | Alabama Power Company | 195 | Southern operating company — charter spine |
| 183 | Georgia Power Company | 7140 | Southern operating company — charter spine |
| 184 | Mississippi Power Company | 12686 | Southern operating company — charter spine |
| 186 | Southern Power Company | 16687 | Southern's merchant generation arm |
| 107 | Oglethorpe Power Company | 13994 | Georgia G&T cooperative, Georgia ITS co-owner |
| 210 | Municipal Electric Authority of Georgia | 13100 | Georgia joint-action agency, Georgia ITS co-owner |
| 1 | PowerSouth Energy Cooperative | 189 | **own BA (`AEC`)** — carried as a falsifier, see below |
| 34 | City of Tallahassee | 18445 | **own BA (`TAL`)** — carried as a falsifier, see below |

The SOCO **balancing authority** is itself a Form 714 respondent
(id 142, `eia_code` 18195, "Southern company") and PUDL attributes it 252
counties across AL/FL/GA/MS — but **it has filed no hourly demand since 2006**
(8,760 rows, all 2006). There is therefore no BA-level 714 series to check
against; the reconciliation below uses EIA-930 instead.

## Clock — Central, measured on two independent sources

The three Southern operating companies span two civil zones (Alabama and
Mississippi are Central, Georgia is Eastern), so this had to be established
rather than assumed. Two sources agree on **`America/Chicago`**:

* the committed `data/raw/eia-930-hourly/SOCO hourly.parquet` carries exactly
  two UTC-minus-local offsets, **6 h on 9,171 rows and 5 h on 17,133**,
  switching on the US DST dates — CST/CDT, never EST/EDT;
* the `timezone` column here reads `America/Chicago` for Alabama Power,
  Georgia Power, Mississippi Power, Southern Power, PowerSouth **and** the
  SOCO BA respondent. (MEAG and Tallahassee report `America/New_York`; PUDL's
  `datetime_utc` already resolves each respondent's own zone, so the UTC join
  below is unaffected either way.)

Georgia Power's *operating* clock is Eastern; Central is its *reporting*
clock on these two products, and that is what every SOCO series must adopt.
A `"SOCO": "America/Chicago"` key was added to
`scripts/data/fetch_eia930_hourly.py::BA_TIMEZONE` on that basis.

**Alignment is zero-shift UTC, measured not assumed.** Correlating the three
chartered respondents' hourly sum against `SOCO hourly.parquet::Demand` over
shifts −4 h .. +4 h peaks sharply at **k = 0 (r = 0.9935)** and falls away
monotonically either side (±1 h → 0.975/0.973, ±4 h → 0.749/0.737). So
`datetime_utc` here and `UTC time` there are the same stamp.

## THE RECONCILIATION GATE — IT FAILS AS CHARTERED

The charter's gate is that the three Southern operating companies' hourly sum
must reconcile against `SOCO hourly.parquet::Demand`. **It does not.** The
three account for **73.2 %** of the BA's metered demand:

| year | 714 three TWh | 930 BA TWh | residual TWh | residual % | pearson r | max abs Δ MW |
|---|---:|---:|---:|---:|---:|---:|
| 2023 | 168.059 | 229.436 | 61.377 | 26.75 | 0.995967 | 13,155 |
| 2024 | 173.123 | 239.349 | 66.226 | 27.67 | 0.995795 | 13,386 |
| 2025 | 175.357 | 239.518 | 64.161 | 26.79 | 0.990045 | 14,706 |

The *shape* is right (r ≈ 0.99) and the *level* is short by a quarter, every
hour of every year — the signature of whole planning areas being absent from
the sum, not of a scaling error.

**Nothing is rescaled to close it** (rule 13 `[R-MEASURED]`). The raw data is
landed with the failure documented and the lane stops, exactly as chartered.
The diagnostic below is offered to the desk as evidence, **not** applied.

### Diagnostic: two more planning areas file the same schedule inside the BA

Oglethorpe Power and MEAG are the Georgia Integrated Transmission System's
other two co-owners, and both file Form 714 hourly demand:

| sum | 2023 resid % | 2024 resid % | 2025 resid % |
|---|---:|---:|---:|
| three operating companies *(the gate)* | **26.75** | **27.67** | **26.79** |
| + Oglethorpe + MEAG | 3.03 | 2.92 | 1.26 |
| + Southern Power Co | 1.63 | 1.50 | −0.03 |
| + PowerSouth + Tallahassee *(falsifier)* | **−2.28** | **−2.41** | **−4.15** |

The last row is the point: PowerSouth and Tallahassee run their **own**
balancing authorities (`AEC`, `TAL`), and adding them **overshoots**. The
enumeration is therefore discriminating on BA membership rather than on
whichever combination minimises the residual — which is what would make it a
fitted choice and is why the falsifier is carried in the file.

**What this lane could NOT establish, and routes to the desk:** PUDL gives
100 % county containment inside the SOCO BA footprint for Alabama Power
(59/59), Georgia Power (155/155) and Mississippi Power (23/23), and 0/1 for
Tallahassee — the test works where it has data. But it carries **no county
attribution at all** for Oglethorpe, MEAG, Southern Power or PowerSouth (G&T
cooperatives and joint-action agencies have no retail territory of their own),
so containment for the two that matter cannot be settled from this source.
A documented BA-membership citation is needed before any load share is built
on the five- or six-respondent sum.

### One more thing a consumer must know: the 930 side has the defects

The largest hourly residuals are **EIA-930 dropouts, not 714 defects**. At
2025-10-23T21 UTC the BA series reads 12,638 MW while all five respondents
behave normally and sum to 24,694 MW; 2025-09-19T17 and 2025-09-06T15 are the
same class. Those hours drive the 2025 `max abs Δ` of 12,560 MW in every row
of the diagnostic table. Under rule 14 `[R-ACCURATE]` the 714 series is the
better-behaved one in those hours.

## Not derived here

No load share, no zone map, no rescaling — this lane fetches (rule 23
`[R-FROZEN-DERIVE]`). The share derivation is SOCO-32's, and it is blocked on
the membership citation above.

## Widening

The source table spans **2006-01-01 .. 2026-01-01** for all eight respondents,
so the holdout years 2019-2022 need only a re-slice of the same pull, with no
new route and no key.

**Licensing:** FERC Form 714 is a public filing; PUDL is CC-BY-4.0. See
`docs/data-licensing.md`.

---

# BA membership of respondents 107, 210 and 186 — lane SOCO-14, 2026-09-13

**APPENDED BY LANE SOCO-14** (`docs/handoffs/FINDING-soco-14-2026-09-13.md`; charter
`docs/multi-iso/soco-addition-plan-2026-09.md` §5 row SOCO-14, gate **G22**). Everything above
this line is SOCO-11's and is unedited. This section answers the question SOCO-11 routed to the
desk — *"A documented BA-membership citation is needed before any load share is built on the five-
or six-respondent sum"* — and answers it **for two of the three respondents, not three**.

**No share is derived here either** (rule 23 `[R-FROZEN-DERIVE]`; that is still SOCO-32's).

## Verdict

| respondent | inside the SOCO BA? | citation | what the citation actually supports |
|---|---|---|---|
| **107 Oglethorpe Power** | **YES** | NERC/SERC public compliance audit **NCR01248**, p. 3 | GSOC — which schedules and dispatches Oglethorpe's resources and is the registered **LSE** for the 38 member EMCs — has **SCS-Trans (EIA BA `SOCO`)** as its Balancing Authority |
| **210 MEAG Power** | **YES** | MEAG **Annual Information Statement FY2024**, dated 2025-05-22, printed pp. 25–26 | MEAG's **Territorial Load** is delivered inside **"the Southern Company Balancing Authority Area"**, in MEAG's own continuing-disclosure words |
| **186 Southern Power** | **NO — not established** | **none found** | Nothing locates respondent 186's **planning-area load**. The IIC and EIA-860 support only that *part of its fleet* (11 of 53 plants) generates inside SOCO — a different claim |

**Gate G22 therefore FAILS**: the six-respondent sum is not fully sourced. The **five**-respondent
sum (3 OpCos + 107 + 210) **is** — its residual is the 3.03 / 2.92 / 1.26 % row of the diagnostic
table above. Card S3 returns to the owner; this file records the evidence, not a decision.

## Oglethorpe (107) — the chain

| link | source (page) | URL |
|---|---|---|
| Oglethorpe's resources are scheduled/dispatched by **GSOC**, and Oglethorpe buys from GSOC the services GSOC buys from Georgia Power **under the Control Area Compact**, co-signed by Oglethorpe | Oglethorpe Power Corp FY2024 Form 10-K, Item 1 (printed p. 13); same text in the FY2025 10-K | `https://www.sec.gov/Archives/edgar/data/788816/000162828025015552/opc-20241231.htm` · `https://www.sec.gov/Archives/edgar/data/788816/000078881626000009/opc-20251231.htm` |
| *"The Reliability Coordinator (RC), **Balancing Authority (BA)**, and Transmission Operator for GSOC is **Southern Company Services, Inc. – Transmission**."* GSOC itself is registered only as LSE and TOP | NERC/SERC public compliance audit report **NCR01248**, 2014-08-07, Executive Summary **p. 3** | `https://www.nerc.com/pa/comp/Audit%20Repots%20DL/2014_Public_SERC_GSOC-OP.pdf` |
| SCS-Trans is registered for the BA function and *"performs the RC, BA, TOP and TP functions for APC, GPC and MPC"* | NERC/SERC audit **NCR01166/01247/01273/01320**, 2021-11-30, Executive Summary **p. 3** | `https://www.nerc.com/globalassets/our-work/reports/regional-audit-reports-of-registered-entities/serc/2022/ncr01166_01247_01273_01320_southern_serc_pub_2021_op-rev1-11-2022.pdf` |
| **SCS-Trans = EIA BA code `SOCO`, BA ID 18195**, AL/FL/GA/MS; and EIA's own 2024 BA registry has **no** other BA over the Georgia footprint besides TVA, DUK, SCEG, SEPA (68 BA codes total) | EIA-861 2024 final, `Balancing_Authority_2024.xlsx` | `https://www.eia.gov/electricity/data/eia861/zip/f8612024.zip` |
| **37 of the 38 member EMCs** carry `BA Code = SOCO` (the 38th, Three Notch EMC, reads `SEPA`) | EIA-861 2024 `Sales_Ult_Cust_2024.xlsx` (32) + `Short_Form_2024.xlsx` (6); member list from the FY2024 10-K | as above |
| **154 / 154** member-served (state, county) pairs lie inside the SOCO BA's 252-county footprint | EIA-861 2024 `Service_Territory_2024.xlsx` × PUDL `out_ferc714__respondents_with_fips`, respondent 142, 2024 | `https://s3.us-west-2.amazonaws.com/pudl.catalyst.coop/nightly/out_ferc714__respondents_with_fips.parquet` |

**Identity cross-check on the series in this directory:** EIA-861 2024 `Operational_Data` reports
Oglethorpe's winter peak as **10,489 MW**; the 2024 maximum of respondent 107 in
`soco_ferc714_hourly_planning_area_demand_2023-2025.parquet` is **10,489 MW**. Same number, two
different EIA/FERC forms.

## MEAG (210) — MEAG's own words

**Municipal Electric Authority of Georgia, Annual Information Statement for the Fiscal Year Ended
December 31, 2024**, dated **May 22, 2025** (SEC Rule 15c2-12 continuing disclosure), printed
**pp. 25–26** (PDF pp. 30–31), section *Pseudo Scheduling and Services Agreement*:
`https://www.meagpower.org/wp-content/uploads/2025/05/MEAG-2024-Annual-Information-Statement.pdf`
(5,442,616 B; sha256 `11037256b4002424a534c3e4aa7b2e2a22136d6a8cb0859a8be7657b14070632`).
Committed transcription:
`data/raw/soco-planning/transcriptions/MEAG_2024_Annual_Information_Statement_PSSA_pp24-27.txt`.

> (e) MEAG Power controls the other non-nuclear resources in **the Balancing Authority Area of
> The Southern Company** … to meet MEAG Power's requirements.

> The term "MEAG Territorial Control Area Services" means those Control Area Services that are
> needed (a) to effectuate **the delivery of power to MEAG Power's Territorial Load** … and (b) to
> maintain the integrity of the ITS and **the Southern Company Balancing Authority Area** …

> GPC has agreed to cooperate with MEAG Power to develop agreements to permit MEAG Power, upon the
> termination of the PSSA, **to form or become part of another balancing authority area** …

The third passage is what makes the first two dispositive: "**another** balancing authority area"
presupposes the current one, and the document names it. The same language appears in the FY2022
AIS (dated 2023-06-09, printed pp. 30–32), so it is not a one-year artifact.

**Corroboration:** **48 of MEAG's 49 Participants** carry `BA Code = SOCO` in EIA-861 2024 (the
49th, Fort Valley Utility Commission, reads `SEPA`); **51 / 51** Participant-served counties lie
inside the SOCO BA's 252-county footprint. Participant list:
`https://www.meagpower.org/participants/overview/`. **Identity cross-check:** EIA-861 2024 summer
peak **2,399 MW** = the 2024 maximum of respondent 210 in the parquet in this directory.

## Southern Power (186) — a documented NO

Four checks, each returning nothing; two cutting against the assumption.

1. **FERC Form 714 has no field for it.** Part I – Schedule 1 asks a respondent to check
   *Balancing Authority Area* **or** *Planning Area* and name the one it is; the instructions say
   only *"Enter/verify the name of the planning area reporting."* **No planning-area respondent
   names the BA it sits in** — which is why 107 and 210 had to be sourced from outside the form
   too. `https://www.ferc.gov/sites/default/files/2020-06/sample-form.pdf` (p. 1);
   `https://www.ferc.gov/sites/default/files/2020-06/form-714-instructions.doc` (§IV.A).
2. **The schedule that would settle it is unreachable.** Part III – Schedule 1 is titled
   *"Electric Utilities That Compose the Planning Area"* — the filed roster. PUDL does not ETL it,
   and FERC's bulk CSVs are **403** from this egress
   (`https://www.ferc.gov/sites/default/files/2020-06/Form-714-csv-files.zip`), as they were at the
   SOCO-11 charter; Zenodo (PUDL's raw archive, DOI `10.5281/zenodo.4127100`) is 403 too.
3. **EIA gives 186 nothing to attach to.** PUDL/EIA: `respondent_type = utility`, no
   `balancing_authority_code_eia`, no counties, every year 2019–2025 — and Southern Power is
   **absent from EIA-861 entirely**, so no member-containment test exists for it.
4. **The generation claim covers a minority of the fleet and is the wrong claim anyway.** EIA-860
   (`data/raw/eia-860/eia860_plant.parquet`) shows "Southern Power Co" (EIA utility ID 17650)
   operating **53 plants across 15 BAs in 13 states** — CISO 12, **SOCO 11**, ERCO 8, SWPP 6,
   DUK 3, NEVP 3, WACM 2, and one each in CPLE / EPE / IID / ISNE / MISO / PJM / PSEI / SPA. **42 of
   53 are outside SOCO.**

**And the series is not a territorial load.** In 2024 respondent 186 averages **387 MW** at load
factor **0.795**, monthly means spanning only **0.84–1.10×** the annual mean and hourly means
**0.95–1.04×** — no weather signature, no diurnal signature. Georgia Power (183) runs 0.86–1.18 ×
monthly and 0.83–1.11 × diurnal; Oglethorpe (107) 0.79–1.27 and 0.76–1.20. Whatever 186 reports, it
behaves like a flat block, not like the load of a service territory. **A consumer folding 186 into
a zonal spine would be adding level and essentially no shape.**

## Two cautions for anyone quoting the diagnostic table above

1. **The falsifier's overshoot stands; its stated reason does not, for 2023–2025.** The table above
   explains the overshoot as PowerSouth and Tallahassee running "their own balancing authorities
   (`AEC`, `TAL`)". Tallahassee is clean — PUDL classifies respondent 34 as `balancing_authority`
   `TAL`, EIA-861 2024 lists TAL as a BA, and Leon County FL is **outside** SOCO's 252. PowerSouth
   is not: EIA-861's BA registry listed `AEC` in **2019** and **not in 2021–2024**, and EIA-861 2024
   codes PowerSouth's own utility rows (Demand_Response, Energy_Efficiency) to **`SOCO`** — while
   PUDL still classifies respondent 1 as the `AEC` balancing authority through 2025. Two
   EIA-derived products disagree in the window that matters. **Quote the measured overshoot
   (−2.28 / −2.41 / −4.15 %), not the "own BA" sentence, until this is settled.**
2. **County containment is corroboration, not proof.** PowerSouth's `AEC` footprint (50 AL/FL
   counties, PUDL 2019) lies **entirely inside** SOCO's 252-county set, so a nested BA passes the
   containment test. This is a caveat on SOCO-11's 59/59, 155/155 and 23/23 figures as much as on
   SOCO-14's 154/154 and 51/51: containment cannot separate a host BA from one embedded in it.
   The load-bearing evidence for 107 and 210 is the NERC audit and the MEAG AIS, not the geography.

**Licensing:** NERC/SERC public audit reports and FERC Form 714 form/instructions are public
documents; SEC EDGAR filings are public; MEAG's Annual Information Statement is a public
continuing-disclosure filing; EIA-861 is public domain; PUDL is CC-BY-4.0. See
`docs/data-licensing.md`.

## 2019-2022 (I-SOCO, 2026-09-24)

`soco_ferc714_hourly_planning_area_demand_2019-2022.parquet` — the same eight
respondents, 2019-01-01T00 .. 2022-12-31T23 UTC, 280,505 rows, sliced from the
PUDL nightly (`Last-Modified: 2026-09-24T08:18:29Z`, 255,526,300 bytes) by the
now-committed instrument that reproduces SOCO-11's hand slice:

    python scripts/data/slice_soco_ferc714_pudl.py --pudl-dir <dir> --first-year 2019 --last-year 2022

**Proof on the committed window.** `--first-year 2023 --last-year 2025 --check`
against today's nightly: 0 rows only-committed, 0 only-regenerated, and
`datetime_utc`, `respondent_id_ferc714`, `respondent_name_ferc714`,
`eia_code`, `timezone`, **`demand_reported_mwh` (the consumed series)** and the
imputation code identical in all 210,431 rows (same row order).
`demand_imputed_pudl_mwh` — PUDL's own derived column, carried for
transparency and read by nothing — differs by at most 1.06 MWh (relative
1.6e-4) between the two nightlies; the committed 2023-2025 file is left as
landed.

`scripts/data/curate_zonal_shares.py` now reads every present file in
`_SOCO_FERC714_FILES` (local 2022 ends at 2023-01-01T05 UTC, inside the
2023-2025 file). **The 2023/2024/2025 share matrices are byte-identical**
(old parser + old 930 extract vs new parser + both files + extended extract).
2019-2022 assemble all 8,760 hours; mean shares AL / GA / MS 0.286 / 0.651 /
0.063 (2019) .. 0.306 / 0.636 / 0.059 (2022).

**PowerSouth caution extends backward.** PowerSouth (respondent 1, a
falsifier, not in the five-respondent map) was its own BA (`AEC`) until
2021-09-01 (the SOCO interchange book's `AEC` leg ends that hour, and the
EIA-860 vintages code its plants `AEC` through 2021) — so for 2019 .. Aug-2021
the EIA-930 `SOCO` demand level excludes PowerSouth load by construction.
