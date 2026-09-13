# NWPP coal basin & delivered price, per plant

Landed **2026-09-13** by lane **NWPP-12**
(`docs/multi-iso/nwpp-addition-plan-2026-09.md` §5 row NWPP-12, item 6; FINDING
`docs/handoffs/FINDING-nwpp-12-2026-09-13.md`).

**This lane landed NO new price file.** The footprint's per-plant delivered coal
price is **already committed** and was measured this session; the charter's
question ("PRB vs Uinta vs Colstrip mine-mouth, per plant where the IRPs or
EIA-923 fuel receipts say so") is answered below from it, including the two
plants where the answer is *no data exists*.

## 1. Measured per-plant delivered coal price, 2023–2025

Source: `data/raw/_processed-legacy/eia923_monthly_fuel_costs.parquet` (EIA-923
Schedule 2 monthly fuel receipts, per plant: `year, month, plant_id, state,
fuel_group, price_per_mmbtu, quantity`), joined to
`data/raw/eia-860/eia860_plant.parquet` for balancing authority, restricted to
the 17 NWPP footprint BAs. Quantity-weighted over 2023–2025:

| EIA plant | Name | State | BA | Card N5 zone | $/MMBtu | MMBtu |
|---:|---|---|---|---|---:|---:|
| 8066 | Jim Bridger | WY | PACE | EAST | **3.252** | 11,021,355 |
| 6165 | Hunter | UT | PACE | EAST | **3.315** | 8,157,516 |
| 4158 | Dave Johnston | WY | PACE | EAST | **1.192** | 7,899,535 |
| 7790 | Bonanza | UT | PACE | EAST | **3.021** | 5,108,609 |
| 8069 | Huntington | UT | PACE | EAST | **3.440** | 4,919,330 |
| 6101 | Wyodak | WY | PACE | EAST | **1.378** | 4,564,480 |
| 4162 | Naughton | WY | PACE | EAST | **2.590** | 2,618,679 |
| 8224 | North Valmy | NV | NEVP | SNV | **4.950** | 2,097,399 |
| **6076** | **Colstrip** | MT | NWMT | INLAND | **no rows** | — |
| **3845** | **TransAlta Centralia Generation** | WA | BPAT | NW | **no rows** | — |

Zone aggregates: **EAST 2.658** $/MMBtu over 44,289,504 MMBtu; **SNV 4.950**
over 2,097,399 MMBtu. INLAND and NW carry **no** coal price at all (see §3).

## 2. The basin split is visible in the price, and a state average destroys it

**A per-state coal price is wrong for this footprint, and the error is ~2.7×.**
Within Wyoming the committed data splits cleanly into two populations:

- **Powder River Basin, ~$1.0–1.4/MMBtu.** In-footprint: Dave Johnston
  **1.192**, Wyodak **1.378**. The same band is confirmed by four
  out-of-footprint Wyoming plants measured alongside (all balancing authority
  `WACM`, i.e. **not** NWPP): Dry Fork Station 0.960, Wygen III 1.068, Wygen 2
  1.099, Neil Simpson II 1.101, Laramie River 1.387.
- **Southwest Wyoming (Green River / Kemmerer), ~$2.6–3.3/MMBtu.** Jim Bridger
  **3.252**, Naughton **2.590**. **Jim Bridger is 2.7× the price of Dave
  Johnston despite both being Wyoming PacifiCorp plants** — Bridger's coal comes
  from an adjacent captive mine in the Green River Basin, not from the PRB.
- **Uinta Basin (Utah), ~$3.0–3.4/MMBtu.** Hunter 3.315, Huntington 3.440,
  Bonanza 3.021. The Utah state aggregate (3.294) does describe these three,
  because Utah's in-footprint coal fleet is basin-homogeneous.
- **Rail-delivered Nevada, $4.950.** North Valmy — the dearest coal in the
  footprint and the only coal outside `PACE`.

**Consequence for NWPP-20/NWPP-33 under rule 5 `[R-NO-MAGIC]` and rule 14
`[R-ACCURATE]`:** coal must be priced **per plant** from the committed EIA-923
series, never from a per-state or per-zone average. The zone aggregate in §1
(EAST 2.658) is printed only to show that it describes none of its own members.

> **What the committed data does NOT give:** a **mine or basin label**.
> `eia923_monthly_fuel_costs.parquet` carries no `Coalmine_MSHA_ID`,
> `Coalmine_State` or `ENERGY_SOURCE` column, so the basin attributions above are
> **inferred from the price populations and plant geography**, not read off a
> field. The authoritative per-receipt basin label is in EIA-923 **Schedule 2
> Fuel Receipts and Costs** itself
> (`EIA923_Schedules_2_3_4_5_M_12_<year>_Final_Revision.xlsx` on eia.gov), which
> carries `Coalmine_State` / `Coalmine_County` / `Coalmine_MSHA_ID` /
> `ENERGY_SOURCE` (BIT vs SUB) per receipt. **That workbook was not fetched by
> this lane** — it is a new raw intake, not a `coal-prices` row, and belongs to
> a data lane. A follow-up wanting the label rather than the inference should
> fetch it.

## 3. Colstrip and Centralia have NO measured delivered coal price — a real gap, not a lookup miss

Verified explicitly: filtering `eia923_monthly_fuel_costs.parquet` to
`plant_id ∈ {6076, 3845}` returns **zero rows in any year**, for any fuel group.

This matters more than the missing rows suggest, because these are the
footprint's two largest non-PacifiCorp coal plants — **Colstrip 1,647.4 MW
(NWMT / Montana)** and **Centralia 729.9 MW (BPAT / Washington)** on the plan's
own EIA-860 census (§2.1) — and together they are the **entire** coal fleet of
card N5's `NWPP-INLAND` and `NWPP-NW` zones. So those two zones have coal
capacity and no coal price.

Colstrip is a **mine-mouth** plant (the Rosebud Mine adjoins it) and mine-mouth
receipts are commonly withheld from EIA-923's public fuel-cost fields as
commercially sensitive; this lane did not establish which exemption applies and
does not guess. What is measured is the absence.

**Routes a follow-up should try, in order, rather than substituting a
neighbouring plant's price** (which would be the rule-13 substitution this
program refuses):

1. **EIA-923 Schedule 2 Fuel Receipts and Costs** directly (see §2) — check
   whether the cost field is suppressed or merely absent from the derived
   parquet.
2. **NorthWestern's 2026 Montana IRP, Figure 61 "Estimated Colstrip fuel cost"**
   (`data/raw/nwpp-planning/transcriptions/NorthWestern_2026_MT_IRP_public.txt`,
   printed p. 163). It exists and is exactly this quantity — but it is an
   **image** and did not transcribe, so it needs image extraction or a hand read
   from the public PDF (`data/raw/nwpp-planning/SOURCES.md` §3).
3. **Centralia's remaining life is short** and may not need solving: Washington
   law ends its coal operation (see §4), so a 2023–2025 backcast needs it but a
   forecast largely does not.

Until one of those lands, an NWPP run has **no measured coal price for 2,377.3
MW of the footprint's 8,910.2 MW coal fleet (26.7 %)**, and that should be stated
on a first keeper rather than filled.

## 4. Coal exit dates the IRPs state — instrument vs intention

Full transcription with pages: `data/raw/nwpp-planning/README.md` §4. The
distinction the charter asked for, in one place:

| Plant | What the document says | Class |
|---|---|---|
| **Jim Bridger 1 & 2** | *"On February 14, 2022, Wyoming and PacifiCorp filed a **Consent Decree in the Wyoming State District Court**… reflecting heat input limits consistent with the conversion of Bridger units 1 and 2 to natural gas generation **by January 1, 2024**"* (Idaho Power 2025 IRP, printed p. 17) | **enforceable public instrument with a date** — meets CLAUDE.md's step-0 bar |
| **Jim Bridger 3 & 4** | PacifiCorp: CCS in 2030, operate 12 years of tax-credit eligibility, **retiring in 2043**. Idaho Power: gas conversion. *"the companies will work together to determine the future"* | **IRP intention**, and the two co-owners disagree |
| **Colstrip 3 & 4** | PacifiCorp: *"work with co-owners to develop the most cost-effective path toward an exit from the Colstrip project in Montana **by 2030**"*. NorthWestern Base Case: *"Colstrip retires according to its **project book life on December 31, 2042**"* | **IRP intention** ×2, and they **contradict each other** |
| **Avista's Colstrip share** | *"Avista's Colstrip ownership will end **December 31, 2025**"*; 222 MW transferred to NorthWestern | **dated commitment**; the underlying driver (Washington CETA) was **not** fetched by this lane — see below |
| **Craig Unit 1** | PacifiCorp target exit **2025-12-31** | **IRP intention** (and Craig is in Colorado, outside the footprint) |
| **Naughton 1 & 2** | Gas conversion *"initiated in Q2 2023"*, operations *"spring of 2026"*; South Ash Pond closure *"no later than the end of December 2025 when coal operations cease"*, complete *"by October 17, 2028, as required under its pond closure extension submission"* | the pond-closure date is **regulator-bound**; the conversion date is a **plan** |
| **North Valmy 1 & 2** | *"Conversion of Valmy units 1 and 2 from coal to natural gas **by summer 2026**"*, listed under *"Actions Committed to before the 2025 IRP — Not for Regulatory Acknowledgment"* (Idaho Power, printed p. 6) | **committed plan**, explicitly not a regulatory instrument |
| **Boardman** | *"In 2020, PGE ceased operations at Oregon's last coal-fired plant"* | **already closed** — historical fact |
| **Centralia** | **not covered** by any document this lane fetched | **OPEN** — see below |

**Two instruments this lane did NOT obtain, named so a follow-up can go straight
to them.** Both are statutes rather than IRPs and neither was fetched here:

- **Washington's coal-transition statute** governing **Centralia** (the plan
  records 229.5 MW of footprint coal carrying a 2027 EIA-860 date, which this
  lane could not tie to a document).
- **Washington's Clean Energy Transformation Act** (CETA), the driver behind
  Avista's and PacifiCorp's Washington-allocated **Colstrip** exits at
  end-2025 — referenced repeatedly in the Avista and PGE IRPs but never quoted
  with a section number, so nothing is recorded here as a CETA citation.

Neither is blocked; they simply were not fetched, and inventing a citation for
them would be exactly what this corpus exists to prevent.

## 5. What is already committed in this directory

`eia_coal_market_sales_price.part*.csv` and `eia_coal_price_by_rank.part*.csv`
(see `README.md` / `SOURCES.md` here) are national EIA series, not per-plant, and
are **not** a substitute for §1 at the grain an NWPP run needs. Nothing in this
directory was modified by this lane.
