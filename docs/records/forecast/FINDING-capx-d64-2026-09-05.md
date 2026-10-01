# FINDING — capx D64: the CCS retrofit's fourth seam adjudicated — both fixed-cost legs are TPC-fractions in their own source, so they scale with the island exactly as capex does; the zero-solve re-screen closes PJM's 2029 residual and leaves the RGGI/CARB cap bound; and the capture VOM adder turns out to be the uncited number now holding the carbon-0 screen shut

**Lane:** capx D64 (Phase 0, r#40 am.1) — the D50 §8 Disclosure 1 seam. **Branch**
`claude/capx-d64-ccs-fixedcost-seam-dj6lhx`. **Written 2026-09-05.** **ZERO SOLVES**, no
`ScenarioConfig` field, no constant changed, no matrix cell moved, no forecast surface written.
Every number below is either read off a primary source fetched and hashed this session, read off a
committed ledger, or the screen's own hour-ceiling arithmetic (D49 §1.2 / D50 §1) re-run on the
rebuilt base fleets with the two legs re-sized — the same zero-LP instrument D50 §1 used,
recovered from git history (commit `9e48ff68`, deleted at `677b605a`) and extended.

**The question.** D50 sized the capture island's capex to the host's captured CO2
(`× captured / captured_ref`) and left `ΔFOM` ($35,000/MW-yr) and the capture VOM adder
($8/MWh) at the reference host's per-MW / per-MWh values, so both dilute per captured tonne as
the host's rate rises, and the carbon-0 clearing threshold moved (`er ≥ ~0.46 → ~0.58–0.63`)
rather than vanishing. D50 §4's PJM 2029 residual (909.8 MW at 1.023 / 1.030 of the scaled bar)
sits on that dilution. What does the source say the two legs scale with, what is the zero-DOF
construction, and what does it do to the committed post-Q42 ledgers?

## 0. The verdicts

| # | question | answer |
|---|---|---|
| 1 | What do the legs scale with? | **The island's TPC.** ATB's own words: property taxes & insurance and maintenance labor (FOM) and maintenance materials (VOM) "are calculated as a percentage of TPC" and out-year O&M "are adjusted for the CAPEX reductions". NETL Rev 4a's B31A→B31B.90 exhibits decompose to **95.5 %** TPC-proportional for the fixed increment and **100 %** island-proportional for the variable increment (§1.2). Under seam 1 the island's TPC scales with captured CO2, so **both legs scale with `k = captured / captured_ref`, the factor D50 already computes.** Zero new constants. |
| 2 | The re-screen (seam 4 alone) | **Rule-14 direction, both ways, as pre-stated:** every carbon-0 row that cleared at the ceiling is lost (PJM 1.68 GW → 0 — **the 2029 residual closes**, the two converters fall to 0.633 / 0.638 of the bar; MISO 0.53 → 0), and the one row gained is a sub-reference host under RGGI (`er` 0.34, k 0.95). RGGI / CARB: eligible MW at the ceiling unchanged (NEISO 12.39 GW, NYISO 6.80, CAISO 13.68) — **the 3 GW/yr cap stays bound on the arithmetic**; what moves is the hour requirement, which compresses from 4,900–7,800 h to 6,500–7,700 h and takes the high-`er` hosts' head start away (§2.3). |
| 3 | The finding the charter did not ask for | **`ccs_retrofit_vom_adder` = 8.0 $/MWh is `needs-citation` and is 2.7–3.6× every published basis** (ATB 2024: 4.8 − 2.1 = 2.7 $/MWh 2022$ = **2.95** in 2026$; NETL Rev 4a: **2.23** per host-MWh 2026$). At the published level the carbon-0 screen **reopens** on the shipped shape (ERCOT 10.2 GW, PJM 11.2, MISO 6.7 GW at the ceiling) and stays open by a knife-edge under seam 4 (ERCOT 5.7, PJM 2.5, MISO 0.7 GW, every row within 0.1–4 % of the bar). **The shipped carbon-0 closure is carried by an uncited number**, and the seam-4 shape and the VOM level are coupled: D65 must land them together (§2.4). |
| 4 | Build or no-build | **BUILD (D65).** Not because the residual moves — because the source says the legs are TPC-fractions and the model prices them flat. The charter is in §4; the STOP set includes "no `k = 1` row moves" so the three D50 seams stay untouched. |

---

## 1. The basis — what each leg is published as, and therefore what it scales with

### 1.1 The two published bases, fetched and hashed this session

| source | file | sha256[:16] | $-yr |
|---|---|---|---|
| NREL ATB 2024 v4.0.0, full electricity table (OEDI, NREL's own distribution) | `ATB/electricity/csv/2024/v4.0.0/ATBe.csv` (102.7 MB) | `567dde9d85caa759` | 2022 |
| ATB 2024 fossil methodology page | `atb.nlr.gov/electricity/2024/fossil_energy_technologies` | (HTML; quoted below) | 2022 |
| NETL, Cost and Performance Baseline for Fossil Energy Plants Vol. 1, Rev 4a (Oct 2022) | `CostAndPerformanceBaselineForFossilEnergyPlantsVolume1…_101422.pdf` (863 pp) | `da0027aa408683c0` | Dec 2018 |
| NETL, Cost and Performance of Retrofitting NGCC Units for Carbon Capture, Rev 3 (Mar 2023) | `CostandPerformanceofRetrofittingNGCCUnitsforCarbonCaptureRevision3_031723.pdf` (51 pp) | `e66c0111171cab77` | 2018 |

The committed extract `data/raw/nrel-atb/atb_2024v4_electricity_filtered.*` carries only
`CAPEX` and `Fixed O&M` for `NaturalGas_FE` (348 rows each; no `Variable O&M`, no `Heat Rate`),
which is why the VOM leg had never been read off the pinned basis. The full OEDI file above
carries all four; the CAPEX / FOM rows it holds are byte-identical to the extract.

**ATB 2024 v4, Moderate, Market financials, @2026 (2022$):**

| techdetail | CAPEX $/kW | Fixed O&M $/kW-yr | Variable O&M $/MWh | Heat rate MMBtu/MWh |
|---|---:|---:|---:|---:|
| NG 2-on-1 Combined Cycle (F-Frame) | 1,451.34 | 33.1 | 2.1 | 6.3 |
| NG 2-on-1 Combined Cycle (F-Frame) 95% CCS | 2,845.84 | 65.2 | 4.8 | 7.105 |
| **increment (island)** | **1,394.5** | **32.1** | **2.7** | **+12.8 %** |
| increment in 2026$ (`derive_entry_costs_from_atb.inflation_factor()` = 1.022⁴ = 1.0909) | 1,521.4 ✓ | **35.0 ✓** | **2.95** | — |
| model constant | `ccs_retrofit_capex_kw` 1,521.4 | ΔFOM 35.0 (`fixed_om_gas_cc_ccs` 65 − `fixed_om_gas_cc` 30) | **`ccs_retrofit_vom_adder` 8.0** | `ccs_retrofit_hr_penalty` 0.12 ✓ |

Three of the four legs sit on this basis to the decimal. The fourth — the VOM adder — does not,
and its registry row reads `auto-generated, needs-citation` (`docs/parameter-citations.md` line
1606). §2.4 measures what that costs.

**Units.** ATB publishes FOM in **$/kW-yr of the CCS plant's net capacity** and VOM in **$/MWh of
the CCS plant's net output** — per kW and per MWh of a *specific* plant, never per tonne. The
reference host behind those per-kW numbers is the NETL F-frame 2×1 (B31A: 727 MW net, 6,363
Btu/kWh, **0.342 t/MWh**) with the B31B.90/.95 capture plant (645/640 MW net, 7,169/7,220
Btu/kWh) — captured **224.0 t/hr = 0.347 t per CCS-net MWh = 0.308 t per host MWh** (Exhibit
5-26: 61,089 kg C/hr to CO₂ product). The model's `captured_ref` = 0.90 × 6.3 × 0.057 =
**0.323 t/MWh** sits between the two readings, is the seam-1 convention already shipped, and is
kept here unchanged: this lane adds **no** reference constant.

### 1.2 What the source says the legs are made of — NETL Rev 4a, B31A → B31B.90, absolute $/yr

NETL's own rules (Rev 4a §2.7.2): *"Taxes and insurance are included as fixed O&M costs, totaling
2 percent of the TPC"*; *"Maintenance cost was evaluated on the basis of relationships of
maintenance cost to initial capital cost … for each major plant component"*; *"Labor administration
and overhead charges are assessed at a rate of 25 percent of the burdened O&M labor"*; operating
labor is a per-shift headcount; consumables are *"individual rates of consumption … taken from
technology-specific energy and mass balance diagrams"*. ATB restates it in one sentence:

> "Because the NETL cost estimating methodology factors capital costs into several operating and
> maintenance cost components (property taxes and insurance (FOM component) as well as
> maintenance labor (FOM component) and maintenance materials (VOM component) are calculated as
> a percentage of TPC), out-year operating and maintenance costs are adjusted for the CAPEX
> reductions described above." — ATB 2024, Fossil Energy Technologies

Applied to the capture increment (Exhibits 5-19 and 5-33, 2018$, 85 % CF):

| fixed O&M increment: 16.07 M$/yr | share | scales with |
|---|---:|---|
| property taxes & insurance (2 % of TPC) | 64.7 % | island TPC |
| maintenance labor (% of TPC by account) | 24.6 % | island TPC |
| administrative & support (25 % of O&M labor) | 7.1 % | mostly island TPC |
| operating labor (+1.3 operators/shift) | 3.6 % | a headcount step |
| **TPC-proportional** | **95.5 %** | |

| variable O&M increment: 10.14 M$/yr | share | scales with |
|---|---:|---|
| maintenance material (% of TPC) | 58.5 % | island TPC |
| CO₂ capture-system chemicals (solvent makeup) | 19.4 % | tonnes captured |
| triethylene glycol + reclaimer/TEG waste | 9.9 % | tonnes captured (compression drying, solvent reclaim) |
| water + treatment chemicals (capture-plant cooling duty) | 12.1 % | tonnes captured |
| ammonia / SCR catalyst | 0.0 % | host (unchanged) |
| **island-proportional** | **100 %** | |

Nothing in either increment is proportional to the *host's* MW or MWh: the fixed increment is
the island's TPC × (2 % + a maintenance fraction + overhead) plus a headcount step, and the
variable increment is the island's TPC × a maintenance fraction plus per-tonne consumables.
**The retrofit report confirms the retrofit carries exactly the capture plant's O&M**: Rev 3
Exhibit 4-5 lists first-year fixed O&M 35,539 k$ and variable O&M 22,782 k$ for `B31A-BR.90` —
identical to the greenfield `B31B.90` (Exhibit 4-1) — formed on the retrofit TPC (551.8 M$
greenfield-equivalent × RDF 1.09), with *"additional labor, maintenance and consumables required
by the retrofit"* included and *"no addition or reduction in equipment, operating, maintenance
and support labor, or capital … needed to operate at higher or lower capacity factors."*

### 1.3 The construction that follows (zero DOF)

Under seam 1 the island's TPC for host *h* is `capex_ref × k_h`, `k_h = captured_h / captured_ref`
(`ccs.py::apply_ccs_retrofit`, `capex_scale`). A leg that is a fraction of TPC therefore scales by
the same `k_h`:

```
ΔFOM_h        = ΔFOM_ref        × k_h        (35,000 $/MW-yr × k;  95.5 % of it is a TPC fraction)
vom_adder_h   = vom_adder_ref   × k_h        (per-tonne consumables + a TPC-fraction maintenance term)
k_h           = captured_h / captured_ref    (the D50 factor, unchanged; captured_ref = 0.32319 t/MWh)
```

Every factor is an existing cited constant. The one approximation is folding the 3.6 % operating-
labor headcount step into the TPC-proportional part: its error is `0.036 × 35,000 × (k − 1)` ≈
**$1,300/MW-yr at k = 2** against a bar of ~$200,000/MW-yr (0.6 %), below the cap-packing unit and
below the 5 % the reference-host convention already carries (§1.1). It is a per-MW step in the
source and could be split out as a second constant; this lane does **not** recommend that — it
would add a constant to remove a 0.6 % effect.

**A note on the transport leg, so nobody re-opens it.** `co2_transport_storage_cost` (15 $/t) is
already per tonne and is charged on `captured` — it is outside this seam. ATB explicitly excludes
beyond-the-fence CO₂ costs from its FOM/VOM, so there is no double count.

---

## 2. The zero-solve re-screen

### 2.1 The instrument and the expected asymmetry, stated before the numbers

The D50 census (`_capxd50_scaled_ceiling_census.py`, recovered from `9e48ff68`) evaluates every
eligible gas-CC tranche of the rebuilt base fleet at the **hour ceiling** — every hour in merit at
the per-hour uplift Δ — against `bar = capex_learned × k / 12`. This lane extends it with the legs
re-sized (`ΔFOM × k`, `vom_adder × k`) and two level variants (§2.4), runs it on the six ISOs'
own golden-posture bare recipes (`reference_config(…, golden_posture=True)` →
`apply_iso_scenario_defaults`; the resolved keys are the D60 §3 bare keys —
NEISO `18515067bf4d2fbe`, NYISO `19a9690bb12c8459`, PJM `09996eca71ee80fd`, MISO
`b1a73a087064ffd8`, ERCOT `0c3e9cd5b5993bdf`, CAISO `29f8eb372810195f`) and writes
`results/calibration/capxd64_fourth_seam_census.json`. The PJM census key is the post-D57 bare
key rather than the D50 arm's `167e65187f32056b`; the D57 gates do not enter the screen's inputs
(fleet, gas, carbon, capex path), so the ceiling arithmetic is the same and the D50 rows are
re-found by `unit_id`.

**Expected asymmetry (rule 14), before computing.** Per captured tonne the shipped legs cost
`13.0 / k` (ΔFOM) and `24.8 / k` (VOM) $/t; the faithful legs cost `13.0` and `24.8` $/t for
every host. A high-`er` host (k > 1) therefore gets **harder**, a sub-reference host (k < 1)
**easier**, and at k = 1 nothing moves. At carbon 0 the per-tonne ledger at the ceiling is
`capex 39–41 + ΔFOM 13.0 + VOM 24.8 + HR-penalty 7–11 = 86–90 $/t` against a §45Q credit net of
transport of **70 $/t** — so the expectation is that **no host clears at carbon 0 under seam 4**
regardless of `er` (the threshold vanishes rather than moves), while under RGGI/CARB the
avoided-carbon leg (≈ the program price, per tonne) keeps every host clearing and only the
**ranking** changes.

### 2.2 The census, seam 4 alone (VOM at the shipped 8.0)

| ISO · year | gas | carbon $/t | eligible (no CHP) | clears SHIPPED (D50) | FOM-leg only | VOM-leg only | **clears SEAM 4** | lost | gained |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| ERCOT 2028–30 | 3.17–3.98 | 0 | 13.7 / 9.5 / 8.0 GW | 0 | 0 | 0 | **0** | — | — |
| PJM 2028 | 4.34 | 0 | 56.4 | 0 | 0 | 0 | **0** | — | — |
| PJM 2029 | 4.51 | 0 | 56.4 | 5 / 1.68 GW | 0 | 0 | **0** | 1.68 GW | — |
| PJM 2030 | 5.15 | 0 | 56.4 | 5 / 1.68 | 0 | 0 | **0** | 1.68 | — |
| MISO 2028 | 3.97 | 0 | 27.4 | 2 / 0.05 | 0 | 0 | **0** | 0.05 | — |
| MISO 2029 | 4.14 | 0 | 27.4 | 3 / 0.38 | 0 | 0 | **0** | 0.38 | — |
| MISO 2030 | 4.78 | 0 | 27.4 | 4 / 0.53 | 0 | 0 | **0** | 0.53 | — |
| NEISO 2028 | 4.77 | 29.83 | 12.39 | 86 / 12.38 | 12.38 | 12.39 | **87 / 12.39** | — | 1 / 0.02 (er 0.340, k 0.95) |
| NEISO 2029–30 | 4.94–5.58 | 31.92–34.15 | 12.39 | 87 / 12.39 | 12.39 | 12.39 | **87 / 12.39** | — | — |
| NYISO 2028 | 4.22 | 27.06 | 6.89 | 67 / 6.86 | 6.86 | 6.86 | **65 / 6.80** | 2 / 0.06 | — |
| NYISO 2029–30 | 4.39–5.03 | 28.96–30.98 | 6.89 | 67 / 6.86 | 6.86 | 6.86 | **67 / 6.86** | — | — |
| CAISO 2028–30 | 4.87–5.68 | 34.37–39.36 | 13.68 | 82 / 13.68 | 13.68 | 13.68 | **82 / 13.68** | — | — |

Every carbon-0 row that cleared is lost and every lost row is a high-`er` host (PJM 0.606–0.679,
MISO 0.576–0.838); the single gained row is a sub-reference host. Either leg alone already
closes PJM and MISO at the ceiling — the two defects were not independently small, the same
lesson D41 §4.2 recorded for the level. **Under RGGI/CARB the cap is untouched:** 12.4 / 6.8 /
13.7 GW still clear at the ceiling against a 3 GW/yr cap, because the avoided-carbon leg is per
tonne too — the D50 §1 asymmetry, sharpened.

### 2.3 The committed post-Q42 converters, row by row

The only committed ledgers solved at the post-Q42 construction are the three D50 arms
(`ercot-t1f` = D50 arm, 0 rows; `neiso-t1f` = D50 arm, 39 rows; `pjm-t1f-d50-ccscapex`, 2 rows)
and the two D60 re-solves (`miso-t1f`, 0 rows; `nyiso-t1f`, 38 rows). D60-R2's `pjm-t1f` /
`caiso-t1f` / GOLDEN-3 re-solves have **not landed** at this HEAD (D60 §5 is still the
placeholder; no bundle exists at `09996eca…`, `29f8eb37…` or `f04fd063…`), so CAISO and the
GOLDEN-3 are re-screened at the census only.

| ledger · year | rows / MW | still clears at the ceiling under seam 4 | k range | H\* required, shipped → seam 4 |
|---|---:|---|---|---|
| PJM 2029 (D50 arm) | 2 / 909.8 | **0 / 0** — `p55337_econ` 1.023 → **0.633**, `p55976_econ` 1.030 → **0.638** | 1.69 | 8,548–8,592 → **12,033–12,093 h** (> 8,760: closes at any surface) |
| NEISO 2028 | 15 / 2,982 | 15 / 2,982 | 0.97–1.84 | 5,373–7,659 → **7,017–7,593** |
| NEISO 2029 | 12 / 2,997 | 12 / 2,997 | 0.95–1.87 | 5,065–7,454 → **6,691–7,207** |
| NEISO 2030 | 12 / 2,983 | 12 / 2,983 | 0.95–1.87 | 4,909–7,362 → **6,477–7,092** |
| NYISO 2028 | 15 / 2,981 (14 in base fleet) | 14 / 2,979 | 0.97–2.04 | 5,306–7,831 → **7,210–7,701** |
| NYISO 2029 | 22 / 2,494 | 22 / 2,494 | 0.97–2.02 | 5,074–7,531 → **6,892–7,498** |
| NYISO 2030 | 1 / 1,000 (`gas_cc_h_class_Upstate_West`, in-horizon build) | k = 1.00 exactly (er = 6.3 × 0.057) — **invariant by construction** | 1.00 | unchanged |

**The PJM 2029 residual closes.** D50 §4.1 attributed the two conversions to the surface (clearing
at 1.02–1.03 of the bar needs ≥ 97 % of hours in merit); under seam 4 their bar is 1.58× their
ceiling uplift, so no surface can supply the hours. D50 §8 Disclosure 2's "channel the census can
see" — the five PJM tranches at 1.0–3.6 % above the scaled bar — is the same five rows, and all
five fall to 0.57–0.64 of the bar. The 2029 residual was the fourth seam, not the price object,
after all; the price object remains open for the RGGI ISOs (§2.5).

**The NEISO / NYISO cap question, from the arithmetic.** Not one committed converter loses its
ceiling clearance, and 4× the annual cap still clears at the ceiling in every year — so the
arithmetic says **the cap stays bound**. What the seam does under RGGI is flatten the ranking:
per-tonne economics become host-independent up to the HR-penalty term (which falls with `er`
per tonne), so the high-`er` hosts that needed 4,900–5,800 in-merit hours now need 6,500–7,100,
while the sub-reference hosts get 100–250 hours easier. The docstring's "efficient hosts win"
ordering, which D50 §3 restored for 2028 and saw drift back in 2029–30, is restored by
construction. Measured on the whole fleet, the MW whose requirement fits under 7,000 in-merit
hours collapses:

| GW of fleet with H\* ≤ 6,000 / 7,000 / 7,500 / 8,000 h | shipped | seam 4 |
|---|---|---|
| NEISO 2028 | 4.94 / 5.55 / 8.38 / 12.05 | **0 / 0.38 / 4.81 / 12.16** |
| NYISO 2028 | 0.42 / 1.76 / 2.63 / 6.47 | **0 / 0 / 0.61 / 5.70** |
| CAISO 2028 | 0.60 / 11.57 / 13.52 / 13.67 | **0 / 2.36 / 13.21 / 13.67** |

So whether 3 GW/yr *actually* converts is now a surface question — do ≥ 3 GW of hosts sit in
merit ≥ 7,000–7,600 h on the prior-year signal? The committed ledgers already answer it for
the marginal hosts: `Connecticut_p568_econ` converted needing **7,659 h** (NEISO 2028) and
`Long_Island_p56234_econ` needing **7,831 h** (NYISO 2028), so the surface supplies ≥ 7,800
in-merit hours to at least those hosts, and every seam-4 requirement among the committed
converters is ≤ 7,701 h. **Expectation for the A/B (§4): the cap stays bound in NEISO and NYISO
and the composition re-ranks toward efficient hosts; a year converting materially below the cap
would be the informative surprise, not a STOP.** The GOLDEN-3 horizon (RGGI to $67/t by 2040,
§45Q eligibility ending 2032) is per-tonne-dominant on both sides and is not expected to move
in kind; it is only re-solved if the NEISO t1f arm shows the cap unbinding.

### 2.4 The finding the charter did not ask for: the VOM adder's level

The shipped VOM adder (8.0 $/MWh, `needs-citation`) sits at **24.8 $/t** captured at the
reference host; ATB's increment is 2.95 $/MWh 2026$ (**9.1 $/t**) and NETL's 2.23 $/MWh per
host-MWh 2026$ (6.9 $/t). The per-tonne ledger at the hour ceiling, carbon 0, k = 1:

| $/t captured | capex bar (12-yr) | ΔFOM | VOM | HR penalty (r = 1) | **total** | §45Q net of T&S |
|---|---:|---:|---:|---:|---:|---:|
| shipped VOM 8.0 — ERCOT 2028 / PJM 2029 / NEISO 2028 | 41.0 / 39.4 / 41.0 | 13.0 | 24.8 | 7.4 / 10.5 / 11.2 | **86.2 / 87.7 / 89.9** | 70.0 |
| ATB VOM 2.95 — same three | 41.0 / 39.4 / 41.0 | 13.0 | 9.1 | 7.4 / 10.5 / 11.2 | **70.6 / 72.1 / 74.3** | 70.0 |

At the published level a correctly sized island costs **within 1–6 % of the §45Q credit** at the
hour ceiling — which is what the market shows (no merchant NGCC retrofit has cleared on §45Q
alone, and every announced one is close enough to need something else). The census with the two
level variants:

| ISO · year | shipped (D50) | seam 4 @ VOM 8.0 | **VOM at ATB level, shipped shape** | **seam 4 @ ATB VOM** | ratio range of the seam-4 @ ATB rows |
|---|---:|---:|---:|---:|---|
| ERCOT 2028 / 29 / 30 | 0 / 0 / 0 | 0 / 0 / 0 | **10.19 / 8.43 / 6.80 GW** | **0 / 5.68 / 3.80 GW** | 1.006–1.025 (2029), 1.002–1.010 (2030); er/phys 0.95–1.05 |
| PJM 2028 / 29 / 30 | 0 / 1.68 / 1.68 | 0 / 0 / 0 | 6.17 / 11.16 / 9.42 | **0.41 / 2.48 / 2.48** | 1.001–1.042; er/phys 1.27–1.49 |
| MISO 2028 / 29 / 30 | 0.05 / 0.38 / 0.53 | 0 / 0 / 0 | 3.38 / 6.70 / 4.61 | **0.48 / 0.72 / 0.72** | 1.000–1.044; er/phys 1.26–1.39 |
| NEISO / NYISO / CAISO | cap-bound | cap-bound | cap-bound | cap-bound | committed converters' H\* 5,283–6,139 h |

Three things follow, all stated at the gate:

1. **The carbon-0 closure D50 §1 reported is carried by the uncited 8.0.** On the shipped shape
   with the VOM at its published level, 6–11 GW per ISO clears at the ceiling — the D49 seam
   reopens. D50's direction and mechanism are unaffected (seam 1 is right whatever the VOM
   level is); what the level changes is *how much* the three seams close.
2. **Seam 4 and the level are coupled and must land together.** Seam 4 alone (VOM 8.0 × k)
   over-charges high-`er` hosts by 2.7× a published number scaled up; the level alone re-opens
   the seam D50 closed. Together they put the carbon-0 screen on a knife-edge: 0.4–5.7 GW per
   ISO-year clears **at the hour ceiling by 0.1–4 %**, needing ≥ 8,100 in-merit hours — a
   surface question (D49 §1.4's price object, seam 3), no longer a cost-leg question. The PJM
   and MISO rows that survive are the `er/phys` 1.27–1.49 hosts, i.e. the CAMPD-rate-above-
   physical tranches D49 §1.3 named, and are its business, not this seam's.
3. **The re-identification is a rule-23 act, like D41, and its direction is stated:** it makes
   retrofits **easier**. Rule 14 is explicit that an accurate value is kept whichever way it
   moves the answer, and a per-tonne-correct model that lands 1–6 % short of §45Q at the
   ceiling is a more faithful market than one held shut by a 2.7× VOM. It is nonetheless a
   second constant change in the same screen inside a week, so it is charted as its **own
   arm** in §4 rather than folded into the shape repair, so the two effects are measured
   apart and the owner rules on each.

### 2.5 What this seam does not touch

- **The capex seam and the CHP exclusion (D50 seams 1–2)** — identical factor, no new reference
  host, and a k = 1 host is invariant to the digit (the `gas_cc_h_class_*` new builds prove it in
  the NYISO ledger). A STOP in §4 asserts it.
- **The price object (seam 3)** — every carbon-0 row surviving §2.4 sits within 4 % of the
  ceiling bar; whether it converts is the surface's decision. Untouched, still the director's.
- **The HR-penalty leg** — per host MWh × `hr`, physically the reboiler steam draw, which scales
  with tonnes captured; it is D30 §5 row 5's split-value question and is left where it is.
- **The converted unit's later retirement bar.** `retirements.py::_THERMAL_FOM` reads FOM by fuel
  type (`fixed_om_gas_cc_ccs` = 65 for every `gas_cc_ccs` unit; `Generator` carries no per-unit
  FOM), so a host converted at k = 1.8 would be screened for retirement in later years at the
  reference island's FOM, not its own. Second-order (the retirement screen's going-forward bar
  moves by ≤ $28,000/MW-yr on a unit whose margin is §45Q-dominated) and disclosed for D65 as
  a design decision (§4.2 item 4), not silently absorbed.

---

## 3. The blast radius — stated, not measured

**Re-key: every forecast bare key**, under the (b′-1) declared-default-flip pattern D60 §6
executed — the new field is registered at a frozen `"False"` drop value and its armed default
enters the hash, exactly as `ccs_retrofit_capex_co2_scaling` did. At this HEAD that is the 13 keys
of D60 §3 (`ercot/neiso/pjm/caiso/nyiso/miso-t1f`, the six `*-t1h`, `neiso-t3`) plus the two
pinned defaults (`e5ecd4105ada3e58`, backcast `6a2845e50951394e`). An explicit `False` keeps its
key (D44 §2 rows 3–4). **Behaviour** can move only where `apply_ccs_retrofit` is reached with a
non-reference host: forecast mode, year ≥ 2028, a `gas_cc` candidate with k ≠ 1. Committed census
at HEAD (61 forecast `run_config.json`; D50 §6.2's structure, updated):

| class | count | consequence |
|---|---:|---|
| end ≤ 2027 (every t1h / t1x / crossover) | 30 | byte-identical — key formality only (D60 §3.3's proof applies unchanged) |
| reach ≥ 2028, **no** CCS rows in the committed ledger | 11 | `ercot-t1f` (D50 arm) and `miso-t1f` (D60), plus 9 GOLDEN-3 FC-6 arm stubs without ledgers — **inert under seam 4 alone**; **can move under the VOM re-identification** (ERCOT 2029 up to 5.7 GW at the ceiling, §2.4) |
| reach ≥ 2028 **with** CCS rows | 20 | 14 are pre-Q42 / historical / unregistered records (`*-d45r`, `*-d46`, `s123`, `s4hydro`, `s6-pjm`, the GOLDEN-3 `bau*` family and its FC-6 arms) — preserved, never re-solved; **6 are live**: |
| … `neiso-t1f` (`18515067bf4d2fbe`, 39 rows) | | composition / ranking can move; cap expected bound (§2.3) — **the A/B arm** |
| … `nyiso-t1f` (`19a9690bb12c8459`, 38 rows) | | same, smaller fleet |
| … `pjm-t1f-d50-ccscapex` (`167e65187f32056b`, 2 rows) | | the 909.8 MW closes; the bare `pjm-t1f` is already stale on D57 + Q42 and owes a re-solve regardless (D60 §4) |
| … `caiso-t1f` (60 rows at the pre-flip `772b1e5abc7fc80c`; post-flip `29f8eb372810195f` unsolved) | | cap-bound at the census (13.68 GW); re-ranking only |
| … `neiso-t3` GOLDEN-3 (83 rows at the pre-flip `706e7ba8e6582d42`; post-flip `f04fd06348e1623d` unsolved) | | 2028–32 rows re-rank; 2040's 3,000 MW row is per-tonne-dominant (RGGI $67/t, no §45Q) — not expected to move in kind |

Backcast: byte-identical (no backcast year reaches 2028; no measured fleet carries `gas_cc_ccs`)
— D41 §6.2 / D50 §6.4, unchanged. No committed artifact moves: sidecars, keepers, determinations
and dashboard rows are files.

**Solve cost if the default is ever flipped**, at the D45-R / D46 / D47 rates: NEISO t1f 8.0 min,
NYISO 12, PJM 28 (owed anyway), CAISO 22.6 (owed anyway under Q42), GOLDEN-3 33.0 — the two
"owed anyway" legs are D60-R2's, so the seam's own marginal cost is **≈ 53 min** single-threaded
(NEISO + NYISO + GOLDEN-3), under 40 min with NEISO and NYISO paired per rule 12.

---

## 4. The D65 build charter (draft for the director)

### 4.1 Scope and admissibility

Two acts, **two arms**, one lane, zero solves until the pre-solve gate passes:

- **Act A — the shape (seam 4):** one gated `ScenarioConfig` field, default-off, scaling `ΔFOM`
  and the VOM adder by `capex_scale` (= k). Zero DOF; a posture, no ISO's number (rule 25).
- **Act B — the level:** re-identify `ccs_retrofit_vom_adder` 8.0 → **2.95 $/MWh (2026$)** =
  ATB 2024 v4 Moderate @2026 `(4.8 − 2.1) × 1.0909`, the same extract, deflator and derive path
  as D41's two legs; clear `needs-citation`; state the dollar-year. Rule 23: the trigger is a
  citation audit against the pinned data, never a residual. **Act B is a value change and
  re-keys unconditionally** (unregistered field, D41 §6.2's mechanic) — the owner authorizes the
  pin advance before it lands, as D41 did. NETL's 2.23 is the cross-check, ATB is the basis
  (host and island on one basis, D41 §2.3's rule). **Extend the pinned extract** to carry
  `Variable O&M` and `Heat Rate` for `NaturalGas_FE` (a `fetch_nrel_atb.py` filter widening, the
  same source bytes) so the value is asserted by a source-consistency test like D41's.

### 4.2 The field and the seam

1. **Field:** `ccs_retrofit_fixed_cost_co2_scaling: bool = False` (`scenarios.py`, beside the
   D50 field; validator: `True` requires `ccs_retrofit_capex_co2_scaling` — the fourth seam
   without seam 1 has no `k`). Registered in `_CACHE_KEY_OPTIONAL_FIELDS` +
   `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS["…"] = "False"`; CLI `--ccs-retrofit-fixed-cost-co2-
   scaling` on `run_full_horizon.py` (and the `--no-` form); recorded in `run_config.json`.
2. **Seam (`ccs.py::apply_ccs_retrofit`):** `delta_fom_per_mw_yr` becomes the reference value
   computed once, and inside the loop `delta_fom = delta_fom_ref × (capex_scale if scale_fixed
   else 1.0)`; `mc_post` uses `vom_adder × (capex_scale if scale_fixed else 1.0)`; **the
   conversion applies the same scaled adder to `gen.vom`** (the dispatch VOM of the converted
   unit must be the VOM the screen priced); the log gains `fixed_cost_scale`,
   `delta_fom_per_mw_yr` (already there — now per host) and `vom_adder_per_mwh`. Off path never
   enters the branch — byte-identical by construction.
3. **Matrix (rule 28c):** one base row `ccs_retrofit_fixed_cost_co2_scaling` in
   `mechanism-matrix.js` + a cell in all six shards (`U`/`U`), citing this finding; Act B is a
   costed-parameter change named in the existing `ccs_retrofit_screen` row's `def`/`note` (the
   D41 §6.3 remedy), no cell verdict moved.
4. **Design decision for the director (§2.5, last bullet):** the converted unit's later
   retirement FOM. Options: (i) disclose and defer (second-order); (ii) add
   `Generator.fom_adder_per_kw_yr: float = 0.0`, set at conversion to `35 × (k − 1)`, and add it
   in `retirements.py`'s FOM lookup — faithful, but touches the retirement screen. Recommend (i)
   for D65 with (ii) routed, so D65 stays one-seam.

### 4.3 Tests (all pre-solve; `tests/unit/model/test_ccs_retrofit.py` conventions)

- off path byte-identical and cache-neutral: bare keys unmoved with the field absent and
  explicitly `False` (the D50 `test_off_is_byte_identical_and_cache_neutral` shape);
- **reference-host invariance:** a k = 1 host (er = 6.3 × 0.057, capture 0.9) produces
  identical `uplift_window`, `payback_years` and log rows with the field on and off;
- **per-tonne invariance at carbon 0:** two hosts with equal `hr` and `er` ratio 2:1 have
  `uplift_window / retrofit_capex_per_mw` differing only by the HR-penalty term (asserted
  analytically), i.e. the payback ordering no longer favours the high-`er` host;
- the converted unit's `vom` carries `vom_adder × k`;
- the validator rejects the field without seam 1;
- Act B: `ccs_retrofit_vom_adder == (ATB gas_cc_ccs VOM − ATB gas_cc VOM) × inflation_factor()`
  from the (widened) pinned extract; `ccs_retrofit_vom_adder > 0`;
- `check_mechanism_matrix.py` green.

### 4.4 The A/B — pre-registered, against the committed keeper (G-CTRL form 4, G-DRIFT first)

The control is the committed `neiso-t1f` (`18515067bf4d2fbe`, the D50 arm = the post-Q42 bare
key); a G-DRIFT audit from its `git_sha` to HEAD classifies every backcast/forecast-path hunk
before the arm is solved. **Arm A1 = NEISO t1f, seam 4 alone** (8 min — the ISO where the
re-screen moves the most rows: 39 committed converters re-rank and the cap-binding question is
live); **Arm A2 = NEISO t1f, seam 4 + Act B** (8 min). NYISO (12 min) is the second RGGI
witness if A1 moves the cap. PJM is **not** an arm here — its bare leg is D57 + Q42 stale and is
D60-R2's to land; the seam's PJM effect (the 909.8 MW closing) is read from that re-solve.
**GOLDEN-3 only if A1 shows the cap unbinding or the composition moving by more than the
cap-packing unit** in any year. Pre-registered expectations (falsifiable, not gates):

| | seam 4 alone (A1) | seam 4 + ATB VOM (A2) |
|---|---|---|
| NEISO conversions / yr | cap-bound (2,940–3,000 MW) every year | cap-bound |
| composition | MW-weighted `er` of the 2028 set falls below D50's 0.550; every year's set ranks by `hr` within the in-merit hosts | same |
| ERCOT / MISO (if solved) | 0 rows, byte-identical ledgers | ≤ 5.7 / ≤ 0.7 GW at the ceiling; expected far lower on the surface |
| PJM (from D60-R2's re-solve) | 2029: 0 rows | ≤ 2.48 GW, all `er/phys` ≥ 1.27 hosts |

### 4.5 STOPs (structural; may kill an arm, never promote one)

1. **A k = 1 row moving** in any ledger or any log field — the capex seam must be untouched.
2. **Seam 4 alone making any carbon-0 row clear** that the committed keeper did not, or **any
   high-`er` host (k > 1) converting under A1 that did not convert in the control** in a
   non-cap-bound year — the rule-14-wrong direction.
3. **Any NEISO / NYISO year converting more than the cap**, or ERCOT / MISO gaining a row under
   A1 — the mechanism claims a footprint it does not have.
4. **Key drift:** a realized key ≠ its pre-declared value, or a collision with a committed key.
5. **Byte-inertness failing** on the committed `neiso-t1f` recipe with the field absent / `False`.
6. **Act B landing without the widened extract and its source-consistency test** — a value with
   no asserted derivation is the defect D41 removed.

Under A2 a carbon-0 ISO gaining rows is **not** a STOP (it is the accurate level's expected
signature, §2.4) — it is pre-registered above and reported at full magnitude.

---

## 5. Governance

- **Zero solves; no field; no constant; no matrix cell; no forecast surface** (rules 5, 13, 14,
  21, 25, 28 all satisfied by inaction). The census probe lives in the session scratchpad — the
  same disposition D41 gave its reconstruction script and the repo gave D50's probe at
  `677b605a`; its output JSON is committed at `results/calibration/capxd64_fourth_seam_census.json`
  (six ISOs × 2028–30, every eligible tranche, all four constructions) so every table above is
  re-readable without a rebuild.
- **Rule 22:** nothing touches a holdout year — forecast-mode arithmetic only.
- **Rule 27:** does not bind (docs + one results JSON; no source file touched). The CHANGELOG
  edit is verified by blob after push anyway.
- **What is reported at full magnitude against this lane's own charter:** the charter asked for
  the basis, the construction, the re-screen, the blast radius and a charter-or-closure; it did
  not anticipate the VOM level. That finding is surfaced (§2.4) rather than left for the arm to
  discover, because a D65 that scaled an uncited 8.0 would have built a faithful shape on an
  unfaithful level.
- **Fetched sources:** OEDI `ATBe.csv` v4.0.0 (sha256 `567dde9d…`), NETL Rev 4a (`da0027aa…`),
  NETL NGCC-retrofit Rev 3 (`e66c0111…`), `atb.nlr.gov/electricity/2024/fossil_energy_technologies`.
  None is landed in `data/raw` by this lane (a `code`-profile docs lane); D65's Act B lands the
  widened ATB filter through the existing `fetch_nrel_atb.py` path.
