# NYISO calibration — best config so far

## Frontier achieved (2026-07-11)

**Formal designation**, registered in `frontend/data/backcast/keepers.json`
(`frontier.NYISO`, `declared: 2026-07-11`):

> "Frontier achieved: the deep >$300 tail's two candidate reserve levers are
> chased to ground — the largest-contingency requirement formula is already in
> the model as the measured NYCA families, and the ORDC/RCPF stack is verified
> complete and SOM-grounded (fires to VOLL in 2023). The sole remaining gap is
> the net-load forecast-uncertainty reserve increment — IMM Recommendation
> 2021-1, which NYISO has not implemented and which has no published formula;
> adding it in-model would be residual-fitting (rule 26). No admissible
> mechanism exists today. 2026-07-11 calibration-log entry (nyiso-61
> follow-up research)."

This closes the two-lever chase that `nyiso-61` (above) left open after the
downstate-import-limit swap produced only a near-null price effect and did
not move the 2025 deep tail (unchanged at 25 h, `docs/calibration-log.md`
lines 173-210): (1) the largest-contingency reserve requirement is already
modeled — it is the measured NYCA family series, not a missing lever; (2) the
ORDC/RCPF scarcity stack is independently verified complete and SOM-grounded,
confirmed firing to VOLL in 2023. With both candidate reserve levers
eliminated, the **sole remaining gap** is the net-load forecast-uncertainty
reserve increment specified by IMM Recommendation 2021-1 — a lever NYISO
itself has never implemented and for which no published formula exists.
Per rule 26 (derive scripts are frozen against residuals — measured-behaviour
parameters re-derive only when source data updates, never to chase a
residual), building an in-model proxy for an unpublished, unimplemented
NYISO mechanism would be residual-fitting dressed as structure: **no
admissible mechanism exists today**, so the deep >$300 tail gap is
formally closed out as data/methodology-blocked, not chased further.

**Disambiguation from informal "frontier" language elsewhere in this file.**
Earlier entries below use the word "frontier" loosely — e.g. nyiso-34's
"documented frontier, non-closable with grounded inputs," nyiso-59's "the
reserve-scarcity frontier is no longer data-blocked," and nyiso-60/61's
"downstate import discipline… the identified next lever for the deep tail."
Those are informal, in-passing descriptions of an open residual at the time
they were written — not a status. The **2026-07-11 designation above is the
first and only formal "Frontier achieved" declaration**: it is a dated,
registered entry in `keepers.json` asserting that every admissible reserve
lever for the NYISO deep price tail has been enumerated and either already
modeled or ruled inadmissible (rule 26), so the tail residual is a
documented, structural stopping point rather than an open lead.

**Not a calibration-complete marker.** Verified against
`frontend/data/backcast/calibration-complete.json`: NYISO does **not** appear
under `"complete"` — only `NEISO` is declared complete there (`declared:
2026-07-07`, keeper `2026-07-08-neiso-54-steamgas-ct`). The two are separate
mechanisms: `calibration-complete.json`'s marker is the rule-22 holdout gate
that authorizes the one-shot validation/locked-test solve (2022, 2019,
H1-2026) for an ISO; the frontier designation above is a train-tier
(2023-2025) finding that the price-tail reserve-lever search is exhausted.
NYISO carries the latter but not the former — its 2022/2019/H1-2026 holdout
years remain fully quarantined (no solve, no score, no registration) until a
separate calibration-complete marker is declared for NYISO.

> **KEEPER (2026-07-11): `nyiso 61 downstate import` — CALIBRATED-WITH-CAVEATS**
> (`2026-07-11-nyiso-61-downstate-import`, bundle
> `results/calibration/nyiso61_downstate_import`, all 3 years + zero-forcing
> ablation twin). The `nyiso-60-ldc-transport` keeper recipe VERBATIM with one
> **measured-data transmission-limit swap** (rules 12/13/14/17, zero new free
> parameters): `nyiso_nyc_lcr_tsl=True` — the Zone-J analog of the Zone-K
> `nyiso_li_lcr_tsl` cap (#1345). In the HB14-21 summer-peak window the
> **Lower_Hudson→NYC (Dunwoodie-South)** link is capped at the **published NYISO
> NYC-locality Bulk-Power Transmission import limit, 2,875 MW** every capability
> year (`data/raw/capacity-deliverability/nyiso/nyiso.csv`), **replacing the
> link's 3,900 MW Gold-Book energy-TTC estimate**; every other hour keeps the
> physical rating. Rule-14 boundary (clean, parallel to LI): the 2,875 MW is the
> AC transmission-security limit; the HVDC ties into Zone J (Neptune/HTP/VFT) are
> the separate priced import-node link (`("NYC", 1000.0)`) and stay uncapped, so
> the cap limits only the Dunwoodie AC link, not total NYC import. A transmission
> limit, not a min_gen floor (forces no energy; stays ON in the ablation twin).
> Effect vs nyiso-60: a **near-null price change** — C3a −3.7/−12.8/−13.7%
> (keeper −4.8/−13.2/−13.7, marginally better/equal), C3b 0.156/0.222/0.198
> (keeper 0.163/0.223/0.199, marginally better), C3c 28/3/25 h (keeper 23/1/25 —
> 2023 slightly more over-count on the ledgered G-20a DA-basis artifact; **2025
> deep tail UNCHANGED at 25 h vs 42 h RT**), C5a +3.3/+2.5/+8.1% **identical**,
> C1 14/14, C2/C4/C7/C8 PASS all identical to the keeper. Ablation twin: floors-
> off simple means 32.29/35.10/60.09 vs keeper 29.14/32.00/54.08 (identical
> deltas to nyiso-60). **FINDING (rule 1 promotion on measured faithfulness, NOT
> residual movement):** downstate import discipline is **NOT** the binding
> deep-tail lever — the measured NYC AC-import limit barely moves the level and
> does not close the 2025 tail. The two remaining open items (do NOT chase with
> tuned adders, rules 11/26): (a) **#1344 B1** condition-varying reserve-
> requirement increments (formal NYISO Market Operations request only; measured
> series is a documented lower bound in non-TSA hours), (b) **Iroquois Z2 winter
> hub** (Ask-C, licensed data). CI replay OOMs GitHub runners in
> regenerate_clean; solve locally (≥15 GB + swap). **Keeper lineage:** nyiso-41 →
> `nyiso-53-li-tsl` → `nyiso-56-measured-zonal` → `nyiso-59-dynamic-rr` →
> `nyiso-60-ldc-transport` → **nyiso-61** (see the dated calibration-log entries).

> **KEEPER (2026-07-10b, superseded same-week by nyiso-61 above): `nyiso 60 ldc transport` — CALIBRATED-WITH-CAVEATS**
> (`2026-07-10-nyiso-60-ldc-transport`, bundle
> `results/calibration/nyiso60_ldc_transport`, all 3 years + zero-forcing
> ablation twin). The `nyiso-59-dynamic-rr` keeper recipe VERBATIM with one
> **measured-data** swap (rules 12/13, zero new free parameters): the
> downstate CT-peaker delivered gas moves from the v1 monthly statewide
> citygate premium (`nyiso_downstate_ct_gas_basis`) to the **measured
> per-zone DAILY LDC-transport delivered index**
> (`nyiso_downstate_ct_gas_daily`, the `nyiso-downstate-gas` datatype v2):
> Transco Z6 NY daily commodity spot + the zone's LDC monthly non-firm
> transportation delivery rate (KEDNY SC-22 Tier 1 / NYC, KEDLI SC-19 Tier 1 /
> Long Island — published statnfdr statements). nyiso-55's G-13 mechanism
> folded into the keeper line (G-13 CLOSED): the interruptible peakers are
> transport customers, not firm-sales citygate customers; the daily hub leg
> prices the cold-snap blowouts (2025-01-17 $97.90) on the exact days the
> peakers run. v1 OFF, v2 ON (rule 19). Effect vs nyiso-59 (v2.4 lw basis):
> C3a −4.8/−13.2/**−13.7%** (2025 gains 2.0 pp), C3b 0.163/0.223/**0.199 —
> 2025 crosses INTO the ≤0.20 band** (one ledgered caveat drops), C3c
> identical 23/1/25 h (G-20a artifacts ledgered), C5a +3.3/+2.5/+8.1%
> (commercial band), C1 14/14, C2/C4/C7 PASS, **C8 clean PASS** (ST_GAS
> 32.1/44.0/36.0% grounded above budget, D-4 off-window 0.0%, D-1 r
> 0.950–0.957). Ablation twin: floors-off prices sit higher (32.20/35.07/60.09
> vs 29.05/31.96/54.08 simple-mean) and the 2023 tail max is in both arms.
> Residual ledger (do NOT chase with tuned adders): (a) B1 condition-varying
> reserve-requirement increments — formal NYISO request only; (b) Iroquois Z2
> winter hub (Ask-C); (c) downstate import discipline — the measured NYC
> locality import limit 2,875 MW vs the 3,900 MW Dunwoodie-South estimate,
> buildable NOW as single-delta probe nyiso-61 (the identified next lever for
> the 2024/2025 deep tail). CI replay OOMs GitHub runners in regenerate_clean;
> solve locally (≥15 GB + swap). **Keeper lineage:** nyiso-41 →
> `nyiso-53-li-tsl` → `nyiso-56-measured-zonal` → `nyiso-59-dynamic-rr` →
> **nyiso-60** (see the dated calibration-log entries).

> **KEEPER (2026-07-10, superseded same-day by nyiso-60 above): `nyiso 59 dynamic rr` — CALIBRATED-WITH-CAVEATS**
> (`2026-07-10-nyiso-59-dynamic-rr`, bundle
> `results/calibration/nyiso59_dynamic_rr`, all 3 years + zero-forcing
> ablation twin). The `nyiso-56-measured-zonal` keeper recipe VERBATIM with
> one **measured-data** change (rules 12/13, zero new free parameters):
> `nyiso_dynamic_reserve_requirements=True` — the in-LP energy+reserve
> co-opt's static locational reserve requirements are replaced by the
> **measured as-enforced hourly series** (the #1344 Ask-B intake,
> `data/raw/NYISO-AS/requirements/`, frozen
> `derive_nyiso_reserve_requirements_hourly.py`): the published SENY 30-min
> **hourly step schedule** (1,300 HB0–5 / 1,550 HB6 / 1,800 HB7–21 / 1,550
> HB22 / 1,300 HB23 — the static 1,300 MW was the overnight floor, 500 MW
> low in every peak hour) × TSA-window zeroing from the B2 MIS event logs
> (185/227/120 h). Effect vs nyiso-56 (v2.4 lw basis): C3a/C3b a **wash**
> (−13.2/−15.7% and 0.221/0.215, all ledgered), C3c gains a real RT-like
> tail — 2024 0→1 h (RT actual 12), 2025 14→**25 h** (RT actual 42; the
> 2.08× DA-basis read is the ledgered G-20a scoring artifact) — C1 14/14,
> C2/C4/C6/C7 PASS, **C8 clean PASS** (ST_GAS 30.3/44.5/38.0% grounded
> above budget, D-4 windows + D-1 r 0.95). The reserve-scarcity frontier is
> no longer data-blocked; the residual is the **B1** formal request
> (condition-varying increments — the derived series is a lower bound in
> non-TSA hours) + the Iroquois Z2 winter hub (Ask-C) + downstate import
> discipline (measured NYC locality limit 2,875 MW vs 3,900 MW estimate).
> CI replay of this recipe OOMs GitHub-hosted runners in regenerate_clean;
> solve locally (≥15 GB + swap). **Keeper lineage since the 2026-07-04
> block below:** nyiso-41 → `nyiso-53-li-tsl` (2026-07-06, L-11 Zone-K
> LCR/TSL) → `nyiso-56-measured-zonal` (2026-07-07, G-20c measured per-zone
> load shares; first NYISO CALIBRATED-WITH-CAVEATS after the 2026-07-09 C8
> D-4 grounding) → **nyiso-59** — see the calibration-log entries of those
> dates; the G-13 LI/NYC delivered-fuel ask below was RESOLVED by
> `nyiso-55-ldc-transport` (per-zone LDC transport gas, registered
> CANDIDATE, not yet folded into the keeper line — the next structural
> combination probe).

> **SESSION 2026-07-04b (probes `nyiso 45 measuredruns` + `nyiso 46
> decpeaker`, both registered NOT-YET; keeper unchanged): the CT offer level
> is now PARTIALLY grounded by three measured mechanisms — the residual
> over-run is the ledgered LI/NYC delivered-fuel basis, and the new C7/C8
> HARD criteria expose the reliability floors' forced share as a first-class
> open root cause.** (1) **Fast-start amortization v3**
> (`--tranche-startup-measured-runs`): the simple-cycle CT tranches amortize
> the NREL start cost over the CAMPD-measured median start-to-stop run
> length (`scripts/data/derive_campd_ct_run_lengths.py` →
> `campd_ct_run_lengths_NYISO.csv`, pooled 2023–25, per-plant medians 2–9 h,
> class fallback 4 h) as the horizon CEILING — P0 runs may only shorten it —
> removing the v2 circularity (too-cheap offers → long P0 blocks → ≈0
> markup) nyiso-44 documented. $2–10/MWh of fuel-invariant commitment
> content: CT_PEAKER 2024 4.75 → 4.54 TWh (actual 2.13), C3a
> −15.4/−14.9/−13.0 → **−14.4/−14.2/−12.4%**, C3b 0.207/0.201/0.195 →
> **0.199/0.194/0.191** (best NYISO price scores to date). (2)
> **Generator-level EIA-860 oil-primary screen** (`--oil-primary-bin-fuel`,
> non-ERCOT resolves from the raw generator sheet's Energy-Source-1 capacity
> majority): VERIFIED CLEAN — every NYISO gas-CT bin is NG-primary at the
> generator level (the per-plant fleet path already routes KER/DFO units to
> raw oil units: Holtsville, Wading River, Glenwood 2514, Shoreham …), so
> the screen flips zero NYISO bins; kerosene mispricing is NOT the CT
> over-run. (3) **NYSDEC 227-3 peaker-rule availability overlay**
> (`--nysdec-peaker-rule`, nyiso-46): curated unit-level ozone-season
> compliance windows from the Gold Book IV-3..IV-6 tables (2023: Coxsackie /
> South Cairo / Northport GT / Port Jeff GT1 / Shoreham 1&2 / Glenwood GT03
> / 74th St; 2025: Astoria GT01 / Arthur Kill GT1 / 59th St; STAR-designated
> Gowanus 2&3 / Narrows barges documented, never restricted). Availability
> only; dispatch delta ~nil by construction (the over-runners are
> 227-3-compliant 2001–04 LM6000s) — kept as real regulatory structure.
> **C1-2024 ST_GAS −3.35 → −3.31 TWh: still the HARD FAIL.** The remaining
> CT over-run (Bayonne/Equus/Edgewood/Glenwood-Landing LM6000s near-baseload
> on Transco Z6 hub gas) is the ledgered **LI/NYC LDC citygate /
> interruptible delivered-gas premium** — the open data ask; do NOT restore
> the ERCOT-fitted bands, no CF-derived caps. **NEW (first NYISO bundle
> scoring C7/C8):** the nyiso-33/34 CT/ST temperature reliability floors
> dispatch 22.6–28.4% of CT_PEAKER (cap 10%) and 34.0–41.5% of 2024/25
> ST_GAS energy (cap 30%) at binding floors and flatten the 2024 CT
> off-peak shape (CV ratio 0.424 < 0.5) — MODEL MISS by construction (rule
> #20), not ledgerable: once the delivered-fuel basis lands, re-derive the
> floor coefficients from source data (rule #23) and re-measure. Best NYISO
> probe state: `nyiso 46 decpeaker` (most structurally faithful; scores
> identical to 45). Prior-session findings (43/44: oil-reattribution basis
> fix restored to NEISO-only, Algonquin ceiling water-fill, E1
> decomposition) stand — see
> `results/calibration/nyiso43_ceiling_oilbasis/SUMMARY.md` and
> `results/calibration/nyiso44_faststart/SUMMARY.md`.**

> **KEEPER (2026-07-03): `nyiso 41 hub prices` — NOT-YET (re-balanced rubric;
> 2026-07-04 note: no longer reproducible on current main — see the 0c6c833
> CT de-leak blocker above; its committed artifacts stand)**
> (`2026-07-03-nyiso-41-hub-prices`, bundle
> `results/calibration/nyiso41_hubprices`, all 3 years). The nyiso-39 config on
> corrected measured gas data plus **measured-neighbor import pricing**
> (`--nyiso-import-hub-prices`, `transmission.inject_nyiso_import_hub_prices`):
> the priced node's `PJM_west` / `ISONE_tie` tranches reprice at the **measured
> hourly PJM / ISO-NE Day-Ahead system LMP** ± the $1 wheeling hurdle
> (`import_scarcity` = hourly max, `export_surplus` = hourly min − hurdle,
> wash-free), replacing the static per-year `IMPORT_TRANCHES_BY_YEAR` ladder —
> which `neighbor_price`'s own docstring calls "a backcast fit … blind to
> neighbor fundamentals" and whose flat 2024 top ($79.7) capped the modeled seam
> exactly when the real seam repriced with the neighbors (model Dec-2024 mean
> $35.3 ≈ the $35.4 PJM_west constant vs NEISO's measured $84.5 month). Exact
> NYISO analogue of the accepted `miso_pjm_lmp_import_pricing` /
> `caiso_import_hub_prices` (rule #12 measured neighbor price-formation input,
> rule #11 blind to NYISO's own flow). Recon band / HQ firm floor / SIL / offer
> curves unchanged. **Also carries two measured-gas fidelity fixes** (isolated
> by the `nyiso 40 truedate gas` control probe): true-date placement of the
> Transco Z6 NY daily quotes (`_transco_z6_daily_dated`; the Jan-2024 $23.90
> print now lands on the 16th, not the 12th) and NYISO monthly hub levels
> recomputed from the completed daily print series (Dec-2024 basis +0.16 →
> +1.00 $/MMBtu; `scripts/data/fetch_nyiso_gas_narrative.py` + the
> fetch-nyiso-gas-narrative workflow).
>
> **Effect — every price criterion moves toward actual with no tuned constant:**
> C3a −15.6/−19.2/−13.2 → **−13.3/−13.4/−9.5%**; C3b NRMSE 0.211/0.304/0.203 →
> **0.209/0.236/0.172**; C3c 0h → **7h** (2025, the first NYISO model >$300
> hours ever). C1/C2/C4/C6 PASS unchanged. C5a CO2 2024 slips to −7.1% (band
> ±7) — exposed by the corrected Dec-2024 hub level; root cause is the ledgered
> in-city steam under-run (see the run-41 attestation). Determination
> **NOT-YET** (soft caveats 4 > budget 2 under the 2026-07-02 re-balance), all
> ledgered.
>
> **The two remaining open items:** (1) the **eastern-NY (Iroquois Z2) winter
> hub level is DATA-BLOCKED — now verified**: the fetch workflow scanned all
> 146 NGWU weekly pages 2023–2025 (compact table, printer-friendly `ngpf.asp`
> table, and narrative) and found **zero** Iroquois prints; NGI/ICE are
> paywalled; the reconstruction (Transco monthly + SOM *annual* spread) reads
> ~$4.0/MMBtu for Dec-2024 vs the ~$9 New England complex the Z2 segment (a CT
> trading point) trades in — worth ≈ −$25/−$19/−$24 of Dec-24/Jan-25/Feb-25
> monthly LMP, the bulk of the residual C3a/C3b miss. Open data ask: a licensed
> Iroquois Z2 series or NYISO SOM monthly per-hub data. (2) the **ledgered
> reserve-scarcity / RT-adder frontier** (idle-capacity headroom credit,
> nyiso-29/31) for the >$300 tail and the broad dual undershoot. Superseded
> keeper below.

> **PRIOR KEEPER (2026-07-02): `nyiso 39 priced interchange` — NOT-YET after
> the 2026-07-02 rubric re-balance** (soft caveat budget 3 → 2 while NYISO
> rode exactly three ledgered price caveats; every hard gate PASSed). See
> `results/calibration/nyiso39_priced_interchange`.

> **PRIOR KEEPER (2026-06-27): `nyiso 34 st-tempfloor` — CALIBRATED-WITH-CAVEATS**
> (`2026-06-27-nyiso-34-st-tempfloor`, bundle
> `results/calibration/nyiso_34_st_tempfloor`, all 3 years). **The first NYISO
> keeper to clear the determination gate** (every prior keeper was NOT-YET). Adds a
> **temperature-keyed downstate ST_GAS (gas-steam) local-reliability floor**
> (`--nyiso-st-reliability-floor`, now the live NYISO default) on top of the
> `nyiso 33` CT-floor keeper — the **ST-fleet companion to the CT floor** — plus
> two structural corrections it depends on and a benchmark-basis fix (Task A).
>
> **Mechanism.** NYISO's downstate steam fleet (NYC zone J Ravenswood / Arthur
> Kill / Astoria; Long Island; Capital) runs a persistent in-city / cable-islanded
> reliability baseline an energy-only LP zeroes out (it imports cheaper CC instead),
> under-running ST_GAS. The floor is a **persistent 24-hour baseline** (`base_24h`)
> with an **evening cooling hot-limb** layered on over HB14-21 via `maximum`,
> applied **per unit, pro-rata** (each in-pocket unit floored at `frac × its own
> available capacity`), keyed per zone to its load-center daily max temperature
> (Islip / Central Park / Albany, NOAA GHCN). Coefficients
> (`transmission.NYISO_ST_FLOOR_COEFFS`) regressed **a priori** from the measured
> per-zone CAMPD ST_GAS CF vs zone TMAX, pooled 2023-2025
> (`scripts/data/derive_nyiso_st_reliability_floor.py`).
>
> **Two structural corrections** (both fix real methodology errors that were
> suppressing the costly in-city units — not residual tunes):
> 1. **When-available CF basis.** `frac` is regressed on CF normalised by
>    *available* capacity (nameplate net of the unit-outage derate), **not** by
>    nameplate over all hours. The floor is applied as `frac × pmax × availability`,
>    so the model already discounts outage downtime; regressing on the all-hours CF
>    **double-discounted** it — the cool-day all-hours CF is itself deflated by the
>    heavy NYC/LI steam downtime, then multiplying by availability again floored
>    Astoria / Arthur Kill near zero. On the available basis these units run a
>    steady ~0.3-0.4 baseline *whenever committed* (NYC temperature corr falls to
>    ~0 — a flat in-city must-run), which `frac × availability` now reproduces.
> 2. **Ravenswood outage routing** (`data.outages._FLEET_GROUP_OVERRIDE`).
>    Ravenswood (2500) is a mixed CC/ST facility classified ST_GAS in our bin, but
>    CAMPD tags every unit `CC_REGULAR`, so its outage rows never reached the ST_GAS
>    bin → it read near-fully-available → the floor over-forced it to a baseload it
>    never runs. The override routes plant 2500's outages to its ST_GAS bin so its
>    model availability reflects the real downtime.
>
> **Capacity-derate check (answering the derate question):** the under-running
> in-city units are **not** ceiling-capped — they reach 0.66-0.92× nameplate in
> summer CAMPD with ample headroom; the under-run was a dispatch/availability/offer
> effect (the two corrections above), **not** a derate to lift. ST_GAS lands *under*
> actual both scored years, so the floor is conservative, not pinned (rules #11/#12).
>
> **Effect — the HARD C1 fuel-mix now PASSES every gas class both scored years:**
> **ST_GAS** `2023 −0.24 (PASS)`, `2024 −3.77 → −1.03 TWh (PASS)`; **CC_REGULAR**
> and **CT_PEAKER** PASS; `dispatch_corr` PASS (gas r=0.91/0.84/0.80); **C5a CO2 in
> band all years.** Plant distribution improved (Arthur Kill near-exact, Astoria /
> EF Barrett recovered, Ravenswood no longer over-forced); a zone-uniform floor
> cannot match every in-pocket unit's heterogeneous when-available CF exactly, so
> per-plant residuals offset *within* the C1 band. **Plus the Task-A benchmark fix:**
> NYISO solar actuals route to **EIA-923** (`actuals_source` ISO-aware) — EIA-930
> NYIS grid solar is a structural 0, so the dashboard now scores the model's ~2 TWh
> of dispatched grid solar against the EIA-923 utility-scale total (2.05/2.90 TWh),
> not a spurious zero.
>
> **Caveats (determination = CALIBRATED-WITH-CAVEATS):** the remaining open items
> are all SOFT price criteria — the **ledgered reserve-scarcity (ORDC) + min-gen-
> floor frontier**. `C3a` mean LMP regresses (−8.0/−19.4/−13.7%) and the `C3b`
> duration curve flattens (2024/2025 just out of band) because the must-run steam
> floor adds inframarginal supply and compresses the merit order rather than letting
> the units SET a scarcity price; the `C3c` >$300 tail is empty in the under-priced
> years (slightly *over* in 2023). Closing the price side needs an ORDC / reserve-
> scarcity demand curve — the documented frontier, non-closable with grounded inputs
> per `nyiso 29/31`, out of scope. Kept per rule #1 (HARD volume gain), not chased.
> See the run-34 attestation (`calibration_attestation.json`).

> **PRIOR KEEPER (2026-06-27): `nyiso 33 ct-tempfloor`**
> (`2026-06-27-nyiso-33-ct-tempfloor`, bundle
> `results/calibration/nyiso_33_ct_tempfloor`, all 3 years). Adds a
> **temperature-keyed downstate CT_PEAKER local-reliability floor**
> (`--nyiso-ct-reliability-floor`, now the live NYISO default) on top of the
> `nyiso 32` steam-markup keeper — the **CAISO local-RA CT floor ported to
> NYISO**'s cable-constrained downstate load pockets (NYC zone J, Long Island
> zone K, Lower Hudson). On hot afternoons the downstate cooling load climbs and
> the UPNY-SENY / LI-cable import limits bind, so fast-start GTs are held online
> for local capacity-area reliability; the energy-only LP imports cheap
> upstate/NYC CC instead and under-runs CT_PEAKER. Floor =
> `clip(base + slope·(TMAX−25), base, cap)` × available downstate-CT capacity
> over HB14-21, with **slope 0.053/°C, cap 0.68, base 0.13** — all regressed *a
> priori* from the measured downstate CAMPD CT_PEAKER evening CF vs NYC daily max
> temperature (NOAA GHCN: Central Park/LaGuardia/JFK), pooled 2023-2025
> (`scripts/data/derive_nyiso_ct_reliability_floor.py`; archived
> `data/raw/nyiso-weather/`). The downstate peaker CF is flat ~0.10-0.18 below
> 25 °C (77 °F) and rises ~2-3× to ~0.6-0.7 above it; ~40-50 % of annual
> downstate peaker energy lands on the ~107 days with TMAX ≥ 25 °C. A **physical
> heat→commitment rule, forward-reproducible** (a forecast year pins a weather
> year, hence a TMAX series, exactly as it pins load/wind/solar), **NOT a CEMS
> pin and NOT residual-tuned** — CT_PEAKER lands *under* actual (−0.85 TWh both
> scored years), so the floor is conservative, not over-forced (rules #11/#12).
>
> **Effect — the HARD C1 fuel-mix improves decisively** (rule-#1 right-structure
> step): **CT_PEAKER** — the open frontier on *every* prior NYISO keeper, and
> confirmed **non-closable via a grounded reserve *requirement*** by `nyiso 29`
> (online-proxy spin) and `nyiso 31` (commitment-gated spin) — `2023 −1.73 →
> −0.85 TWh` and `2024 −1.92 → −0.85 TWh`, **FAIL → PASS both scored years**; the
> complementary `CC_REGULAR` over-run drops `2023 +0.99 → +0.63` (PASS) and `2024
> +1.74 → +1.25` (**FAIL → PASS**). **2023 now has every gas class in C1
> tolerance.** `dispatch_corr` stays PASS (gas r=0.91/0.85/0.80). **Tradeoff
> (kept per rule #1):** `C3a` mean LMP regresses ~1.3 pp (`2023 −10.5 → −11.7 %`,
> `2024 −11.2 → −12.7 %`, `2025 −7.3 → −8.6 %`) because the floor is a **min-gen
> (must-run) representation** — it recovers the local-RA *energy* but adds
> inframarginal supply rather than letting the peakers **set** a scarcity price;
> the price side (`C3a`/`C3c`) stays the **ledgered reserve-scarcity frontier**
> (an ORDC / reserve-scarcity demand curve — non-closable with grounded inputs
> per `nyiso 29`/`31`, would otherwise need an ungrounded adder, rule #12). The
> grounded reserve *requirement* couldn't close CT_PEAKER (non-binding headroom);
> the grounded *temperature floor* can, because it acts directly on the measured
> heat→commitment relationship rather than on a reserve shortage that never
> forms. Remaining C1 miss: `2024 ST_GAS −3.77 TWh` (the floor pulls some evening
> energy from the also-downstate steam fleet too). New keeper because it is the
> **most structurally faithful** NYISO config to date — a real, measured,
> forward-reproducible local-reliability mechanism that closes the largest C1
> miss. C6 governance **PASS** (attested); determination **NOT-YET** (2024 ST_GAS
> C1 + `price_shape`/`price_tail` reserve-scarcity gap). **Import/export:** the
> net-interchange import reconciliation + priced node are unchanged; the downstate
> **interface-TTC congestion separation (U7)** remains data-blocked. Reproduce:
> the `nyiso 32` keeper flags + `--nyiso-ct-reliability-floor` (now the NYISO
> default). Superseded keeper below.

> **PRIOR KEEPER (2026-06-26): `nyiso 32 steam-markup`**
> (`2026-06-26-nyiso-32-steam-markup`, bundle
> `results/calibration/nyiso_32_steam_markup`, all 3 years). The documented
> **run-29 carry-forward** executed on ST_GAS only: re-level the legacy gas-steam
> offer from the ERCOT-shaped rising ramp (`committed 0.97 / econ_low 1.10 /
> econ_high 1.45`) to NYISO's **own measured CAMPD steam marginal HR × a grounded
> competitive markup** (`committed 1.05 / econ_low 1.08 / econ_high 1.13`). The
> markup is the CC class's own defensible reach ratio (keeper CC `econ_high` 1.21
> ÷ native CC marginal 0.925 = **1.31×**) applied to the *flat* steam native
> marginal HR (~0.82-0.83, `nyiso_campd_marginal_hr_summary.csv`), with a thin
> monotone spread to keep a valid rising offer below the unchanged inflexible peak
> tranche. **CC reach is UNCHANGED at run-27** (`econ_high` 1.21/1.24 — the markup
> that holds the clearing price; *not* stripped, unlike the rejected run-28).
> Merit order preserved (steam eff HR 11.1-12.0 > CC 9.4 < CT 16.1, no inversion).
>
> **Effect — the HARD C1 fuel-mix improves across the board** (rule-#1 first
> axis): `2023 ST_GAS −1.26 → −0.01 TWh` (now **PASS** — the flat measured band
> reproduces measured steam volume almost *exactly*, validating the offer LEVEL a
> priori, not residual-fitted), `CC_REGULAR +1.70 → +0.99` (**PASS**); `2024
> ST_GAS −4.14 → −3.28`, `CC_REGULAR +2.09 → +1.74`. `dispatch_corr` stays PASS
> (gas r=0.91/0.84/0.80). **The SOFT C3a mean LMP regresses to a documented
> CAVEAT** (`2023 in-band → −10.5%`, `2024 −9.7% → −11.2%`): the keeper-27 steep
> steam ramp was a **compensating over-pricing** propping up the mid-merit
> clearing price; removing it (the measured-grounded move) **exposes the real root
> cause** — the missing reserve-scarcity / RCPF tail (the *same* cause as the
> CT_PEAKER C1 under-run), confirmed **non-closable with grounded inputs** by
> `nyiso 29` (online-proxy spin) and `nyiso 31` (commitment-gated spin). Kept per
> **rule #1**: the measured steam offer is the real mechanism; reverting to the
> over-priced ramp to recover C3a would reach the right number through a mechanism
> that isn't real *and* re-open the volume miss, and raising steam to chase C3a
> would distort the now-validated steam volume (rule #12) — the **same promotion
> principle as `nyiso 25`** (a measured-data correction kept despite a C3a
> tradeoff attributed to the out-of-scope incidence root cause). New keeper because
> it is the **most structurally faithful** NYISO config: measured-grounded steam
> offer **and** the grounded CC reach. **Import/export:** the net-interchange
> import reconciliation + priced node are unchanged (the keeper mechanism since
> `nyiso 24`); the downstate **interface-TTC congestion separation (U7)** remains
> **data-blocked** (no interface-flow file in `data/raw`) and the downstate
> reserve-scarcity tail is the ledgered, grounded-input-bounded frontier. C6
> governance **PASS** (attested); determination **NOT-YET** (`price_shape`/
> `price_tail` = the genuine reserve-scarcity model gap, unledgered MODEL MISS —
> the same open frontier on every NYISO keeper). Reproduce: the `nyiso 27` keeper
> flags + `--offer-curve-json '{"ST_GAS": {"committed": 1.05, "econ_low": 1.08,
> "econ_high": 1.13}}'` (now the live `_NYISO_OFFER_CURVE` default). Superseded
> keeper below.

> **PRIOR PROBE (rejected, 2026-06-25): `nyiso 28 native-hr`**
> (`2026-06-25-nyiso-28-native-hr`, bundle
> `results/calibration/nyiso_28_native-hr`, all 3 years). Re-grounded ALL of
> `_NYISO_OFFER_CURVE` `CC_REGULAR` / `CC_CHP` / `ST_GAS`
> `committed`/`econ_low`/`econ_high` to NYISO's **OWN** CAMPD incremental-HR
> medians — removing the cross-ISO borrow (the `econ_high` 1.21/1.24 was ERCOT's
> CAMPD-CC reach; `ST_GAS` 1.10/1.45 was ERCOT-shaped). The NYISO-native table
> (new tool `scripts/data/derive_campd_marginal_hr.py`, NY+NJ CEMS pooled 2023-25,
> output `data/raw/reference/nyiso_campd_marginal_hr_summary.csv`):
> `CC_REGULAR 0.632/0.784/0.925`, `CC_CHP 0.809/0.989/1.103`,
> `ST_GAS 0.818/0.825/0.830`. Merit order preserved (CC `econ_high` eff HR
> 7.2/7.7 < ST `committed` 8.7 — no inversion). **REJECTED:** the bare CEMS
> marginal heat rate is the marginal **COST**, not the **OFFER** — it omits the
> competitive offer **markup** (no-load/start/AS cost recovery + inframarginal
> rent) that NYISO has no offer disclosure to measure, so stripping the borrowed
> reach (which *proxied* that markup) under-prices the gas stack ~$10/MWh and
> **craters `C3a`** to −24.0 % / −26.5 % / −23.5 % across 2023-25 (`C3b`
> regresses too). Rule #1: a run **missing real structure** (the markup) is not a
> keeper. **Two sub-findings survive:** (a) the **steam-side** re-level is
> directionally right — lowering `ST_GAS` toward its NYISO-native ~0.82-0.83
> marginal HR nearly **halved the 2024 `ST_GAS` under-run** (−4.14 → −2.22 TWh),
> confirming legacy steam's `1.10/1.45` economic ramp was over-priced (eff HR
> 11.7-15.4 vs measured ~8.7-8.8); (b) the **CC over-run is structural** at
> NYISO's own sub-1.21 reach — it barely moved despite the large offer drop
> (import-constrained downstate leans on its efficient CC regardless). **Live
> source reverted to the run-27 keeper curve**; the probe lives only in its
> bundle + dashboard. **Carry-forward (run 29):** ground a NYISO competitive-offer
> **markup ON TOP of** the native marginal HR (so curve = measured marginal HR ×
> a markup recovering no-load/start/AS cost + rent), lowering steam toward native
> marginal while a stack-wide markup holds the clearing price — **not** a restored
> cross-ISO borrow. The **per-ISO-per-class native-grounding principle stands**;
> what run 28 surfaces is that an ISO without offer disclosure still needs its
> *markup* component grounded, which CEMS alone cannot supply. C6 governance
> **PASS** (attested as a rejected probe); determination **NOT-YET**.

> **KEEPER (2026-06-25): `nyiso 27 cc-offer`**
> (`2026-06-25-nyiso-27-cc-offer`, bundle
> `results/calibration/nyiso_27_cc-offer`, all 3 years). A **re-solve** of the
> `nyiso 26 cc-nameplate` config (byte-identical flags, P1, no commitment) with
> **one source edit**: the NYISO CC offer **level** is re-levelled toward the
> CAMPD CC marginal-heat-rate SRMC reach. `_NYISO_OFFER_CURVE` `CC_REGULAR`
> `econ_high` **1.12 → 1.21** and `CC_CHP` `econ_high` **1.15 → 1.24**
> (`econ_low`/`committed`/`peak` unchanged) — `1.21×` base_hr is the CAMPD CC
> marginal-HR reach at the top of the econ ramp, the **same fit ERCOT's keeper
> uses** (`committed 0.87 / econ_low 0.92 / econ_high 1.21`). This is the
> **rule-#1 second step**: `nyiso 26` fixed the *structure* (full-nameplate CC
> capacity + the Ravenswood steam-HR correction, CC correctly ahead of steam, no
> wall); `nyiso 27` calibrates the offer **level** on that correct structure,
> grounded in the CAMPD CC marginal HR — **not** tuned to the price/volume
> residual (rules #11/#12). The earlier `econ_high 1.12` compressed the upper
> econ slices *below* the CAMPD CC marginal HR; masked while the old 75 % CC wall
> was in place, exposed in `nyiso 26` once the wall came off (the rule-#11
> signal). Effect vs the `nyiso 26` keeper — **all in the predicted direction**,
> no re-walling, no merit inversion, no 2025 overshoot:
> `2023 CC_REGULAR +2.09 → +1.70 TWh`, `ST_GAS −1.48 → −1.26`, `CT_PEAKER −1.33 →
> −1.30`; `2024 CC_REGULAR +2.39 → +2.09`, `ST_GAS −4.31 → −4.14`, `CT_PEAKER
> −1.52 → −1.51`; `C3a` **2023 −8.9 % → in-band**, **2024 −11.0 % → −9.7 %**,
> 2025 stays in-band; `C3b` 2024 `0.250 → 0.243`. The within-gas merit **order**
> stays physically correct throughout (CC ahead of steam). `econ_high` is now at
> the CAMPD/ERCOT-grounded `1.21×` reach, so the CC offer lever is **spent at its
> grounded landing** — the small residual CC over-run / `C3a` 2024 depression
> sits *at* that grounded ceiling and is **not** chased further (rule #12). New
> keeper because it is the **most structurally faithful** NYISO config to date:
> physically-correct CC capacity (`nyiso 26`) **and** a CC offer level grounded in
> the CAMPD CC marginal HR (`nyiso 27`) — the documented CC offer-level frontier
> (`docs/handoffs/pjm-cc-level-tuning-2026-06.md`) now **DONE**. C6 governance
> **PASS** (attested); determination **NOT-YET** (the residual CC/ST C1 + `C3a`
> 2024 honest misses at the grounded offer ceiling + the ledgered EIA-930/923 gas
> basis floor). The RCPF scarcity tail (`C3c`) and NYC-peaker under-run remain
> **incidence-gated** (downstate reserve headroom / import discipline), unchanged
> and out of scope. Reproduce: the `nyiso 26` config (no new flags) with
> `_NYISO_OFFER_CURVE` CC `econ_high` at `1.21`/`1.24`. Superseded keeper below.

> **ROOT-CAUSE CORRECTION (2026-06-25, analysis):** the `C3c` tail / CT_PEAKER
> incidence gap is **NOT** import-discipline- or interface-gated. A diagnostic
> 2024 solve (`docs/handoffs/nyiso-downstate-reserve-incidence-2026-06.md`)
> shows the in-LP locational reserve families never bind (`reserve_price` >$0 in
> 9 h vs measured NYC reserve >$0 in 3,082 h), and the downstate interfaces bind
> ≤7 h/yr (NYC inflow 2,600 mean vs 4,900 ceiling) — so tightening imports /
> interfaces cannot bite. The real cause is that the pure-ED LP **credits idle,
> un-committed peaker capacity as deliverable reserve**, so reserve never goes
> short and NYC LMP never separates upward. The faithful lever is a
> **commitment-aware synchronised reserve** (out of the reserve-incidence /
> import-discipline scope), not import discipline. The "import discipline"
> phrasing in the incidence ledgers below is superseded by this finding.

> **PRIOR KEEPER (2026-06-25): `nyiso 26 cc-nameplate`**
> (`2026-06-25-nyiso-26-cc-nameplate`, bundle
> `results/calibration/nyiso_26_cc-nameplate`, all 3 years). A **re-solve** of the
> `nyiso 25 steam-merit` config (byte-identical flags, P1, no commitment) on the
> **merged code** — **no new source edits**. Two structural levers, both more
> physically faithful, both already on `main`: (1) my Ravenswood mixed CC+ST
> steam-HR fix (`data.fleet.MIXED_FACILITY_STEAM_HR={2500:9.5}`, PR #850); (2)
> `cc_nameplate_summer_derate` (commit `a8b0e55`, AUTO-ON for PJM/NYISO/NEISO):
> CC carries **full EIA-860 nameplate**, derated to the measured net-summer rating
> in **summer only** (winter restores cold-weather capability), dropping the old
> CC "75 % wall" (double summer-derate + statistical POF). Combined effect is the
> **predicted structural direction**: nameplate CC capacity + steam correctly
> above CC ⇒ CC strongly displaces steam and the 2023 within-gas merit split that
> `nyiso 25` left open **over-closes**: `CC_REGULAR −3.47 → +2.09`, `ST_GAS +2.76 →
> −1.48` (2024 likewise `CC_REGULAR −2.61 → +2.39`, `ST_GAS −0.96 → −4.31`). The
> merit **order** is now physically correct (CC ahead of steam) *and* CC capacity
> is physically correct (nameplate, no fitted wall). What the un-walled fleet now
> **exposes** is a cleaner, single-lever miss — the **CC offer level is too cheap**,
> so with full nameplate capacity CC **mildly over-runs** on energy (`CC_REGULAR`
> ~+2 TWh/yr; NYISO's over-run is mild vs PJM's +65 TWh) and **depresses LMP**
> (`C3a` 2023 −8.9 %, 2024 −11.0 %; 2025 +9.3 % → **in-band**). Per rules #1/#11
> the nameplate capacity + corrected steam HR **stay in**: the wall was masking a
> too-cheap CC offer; removing it surfaces the real bug, fixed via the real lever
> (CC `econ_low/econ_high` in `_NYISO_OFFER_CURVE`, grounded in the CAMPD CC
> marginal-HR fit — the `docs/handoffs/pjm-cc-level-tuning-2026-06.md` direction),
> **not** by restoring a capacity haircut. New keeper because it is the **most
> structurally faithful** NYISO config to date, with the remaining miss now cleanly
> localized to ONE diagnostic lever (the CC offer level) instead of entangled with
> a capacity wall. C6 governance **PASS** (attested); determination **NOT-YET**
> (honest CC offer-level misses + the ledgered EIA-930/923 gas basis floor). The
> RCPF scarcity tail (`C3c`) and NYC-peaker under-run remain **incidence-gated**
> (downstate reserve headroom / import discipline), unchanged and out of scope.
> See `docs/nyiso-dispatch-validation-2026-06.md`. Reproduce: the `nyiso 25`
> config (no new flags) on merged `main`. Superseded keeper below.

> **PRIOR KEEPER (2026-06-24): `nyiso 25 steam-merit`**
> (`2026-06-24-nyiso-25-steam-merit`, bundle
> `results/calibration/nyiso_25_steam_merit`, all 3 years). The `nyiso 24`
> config (byte-identical flags) + ONE model-side data correction
> (`data.fleet.MIXED_FACILITY_STEAM_HR`): **Ravenswood** (plant 2500, a mixed
> CC+ST facility) had its ~1.7 GW steam units inheriting the 8.8 MMBtu/MWh
> plant-blended heat rate (the combined cycle's efficiency leaking into the steam
> row), so the big NYC steam unit cleared **ahead of idle NYC combined cycle** on
> merit (the 2023 `CC_REGULAR −4.06 / ST_GAS +3.55 TWh` inversion). Recovering the
> steam units' own HR (9.5) from the blend **restores the physically-correct
> merit order** and `CC_REGULAR` improves **every year** (2023 −4.06→−3.47, 2024
> −3.21→−2.61, 2025 −1.20→−0.6); 2023 `ST_GAS` over-run shrinks (+3.55→+2.76). A
> rule-#11 measured-data correction, not residual-fitted. Tradeoff kept per
> rule #1: `C3a` 2025 mean LMP +9.3 % (just over ±8 %) because import-constrained
> NYC over-relies on Ravenswood steam as the marginal unit — a discovered symptom
> of the out-of-scope NYC import-incidence root cause, not a reason to revert the
> correct HR. The RCPF scarcity tail (`C3c`) is unchanged: it is **incidence-gated
> (downstate reserve headroom / import discipline), not curve-gated** — steepening
> the published RCPF demand curve (the `nyiso 25 rcpf-steep` PROBE) deepens the
> tail but adds no tail hours. C6 governance PASS; determination **NOT-YET** (the
> hard EIA-930/923 gas basis floor, ledgered). See
> `docs/nyiso-dispatch-validation-2026-06.md`. Reproduce: the `nyiso 24` config
> (no new flags). Superseded keeper below.

> **PRIOR KEEPER (2026-06-24): `nyiso 24 import-recon`**
> (`2026-06-24-nyiso-24-import-recon`, bundle
> `results/calibration/nyiso_24_import_recon`, all 3 years). Adds the priced
> import-node **boundary-flow reconciliation** (`--nyiso-import-reconciliation`)
> on top of the `nyiso 23` li-oil-merit keeper config: a per-month band pins the
> priced node's net interchange to the measured EIA-930 schedule, so modeled net
> imports now track **23.09 / 20.32 / 19.28 TWh** vs measured 23.45 / 20.35 /
> 19.09 (was 18.53 / 21.65 / 21.63 — under-import in 2023, over-import in
> 2024/25, both corrected). **C2 gas improves every year** (2023 +2.6 → −2.9 %,
> 2024 −9.0 → −7.0 %, 2025 −7.2 → −3.9 %); **C3a mean LMP PASS** (model
> $30.9/$36.0/$62.1 vs actual RT $30.3/–/$60.7); **C4 dispatch corr PASS**; C6
> governance PASS (attestation added). Determination remains **NOT-YET** (same as
> every prior NYISO keeper): the residual 2024 gas/CO2 is the documented
> EIA-923/EIA-930 **basis floor** (ledgered ACCEPTED, out of scope), and the
> remaining unledgered fails are the 2023 within-gas CC/ST merit split and the
> NYC-peaker reserve-scarcity **tail** — both pre-existing, neither addressable
> by the import boundary flow. Promotion is on **structural faithfulness**
> (rule #1: correct boundary flow replacing an economic estimate), not on a band
> pass. Reproduce: the keeper config plus `--nyiso-import-reconciliation`.
>
> **Superseded determination (2026-06-22, scorer): NOT-YET** for the prior keeper
> `nyiso-15-transco-z6` (`python scripts/calibration_verdict.py --run-id
> 2026-06-21-nyiso-15-transco-z6`). BTM regen done — byte-faithful re-solve
> (gmModel reproduces the keeper to <0.1%) + `btm.parquet`, scoring CHP classes
> on the grid-delivered basis; **2024 CC_CHP clears** (was −2.93 TWh). C6
> governance now PASS (truthful attestation added). Deciding fails are genuine
> **MODEL MISSes** (not ledgerable per rubric §3): C1 CC_REGULAR −7.1/−13.3/−7.9%
> under-dispatch (no BTM component — gas-basis / interchange-wedge merit issue,
> the Transco-Z6/Iroquois overlay is already in the keeper), gas family
> +5.4/−10.6/−7.3%, and ST_GAS ±2–4 TWh; 2023/2025 CC_CHP +2.3/+2.9 TWh is model
> over-run of some CC-CHP plants above their measured EIA-923 grid output. The
> CC_REGULAR/interchange merit split is the next model-side frontier, not chased
> in this BTM-attestation pass.

Keeper: **`nyiso p11 smoke 2023` config (P9b served-interchange defaults),
promoted to the P12 sign-off keeper** (2026-06-12, bundle
`results/calibration/nyiso_smoke_2023`, highspy 1.x). P12 ran the offer-curve /
hydro / storage / import / dual-fuel knobs against this config and **found no
honest knob that improves an in-tolerance class without a zero-sum trade against
another, or without violating a documented convention** — so the structural
P9b config *is* the keeper. Reproduce with:

```
python scripts/run_calibration_full.py --iso NYISO --year 2023 --commitment \
    --out-dir results/calibration/nyiso_smoke_2023
```

All the NYISO calibration toggles fire by **default** in the harness
(`_calibration_config`): measured net interchange served in `load_demand`
(P9b), `gas_monthly_actuals` + `gas_plant_monthly_fuel_pricing` (measured
EIA-923 monthly gas, P7), RGGI via `state_carbon_price_by_iso` ($13.49/t 2023),
the EIA-860 dual-fuel oil-parity cap (385 gas tranches / 15.9 GW), the historic
CEMS outage overlay (318 plant-tranches derated), and the 154-plant hydro
energy budget (28.40 TWh). **No offer band was tuned** — see the success bar.

## Success bar (fuel-mix ±5%/class vs EIA-923; size-aware on the small classes)

NYISO 2023 is **mix-calibrated**: every renewable / baseload class lands inside
±5% of EIA-923, and the two largest gas classes are on target. The residual is
a single **gas-total basis floor** (below) that lands on the small CHP/peaker
classes — the least-distorting place for it.

## Results (P2, 2023, vs EIA-923 incl. CHP/peaker split)

| class | model TWh | EIA-923 TWh | Δ% | bar |
|---|---|---|---|---|
| CC_REGULAR | 32.14 | 33.01 | −2.6% | ✓ |
| CC_CHP | 14.10 | 16.50 | −14.6% | ✗ (basis) |
| ST_GAS | 8.07 | 8.14 | −0.8% | ✓ |
| CT_CHP | 1.44 | 2.59 | −44.2% | ✗ (basis) |
| ST_CHP | 1.25 | 1.53 | −18.0% | ✗ (basis) |
| CT_PEAKER | 0.51 | 2.07 | −75.2% | ✗ (basis) |
| **gas total** | **57.53** | **63.84** | **−9.9%** | basis floor |
| hydro | 28.38 | 28.03 | +1.3% | ✓ |
| nuclear | 27.49 | 27.53 | −0.1% | ✓ |
| wind | 4.60 | 4.77 | −3.6% | ✓ |
| solar | 1.95 | 2.05 | −5.0% | ✓ (edge) |
| OTHER | 2.20 | 2.20 | 0.0% | ✓ |
| biomass | 1.62 | 0.84 | +93% | ✗ (small abs +0.78 TWh) |
| oil | 0.01 | 0.42 | −96.9% | ✗ (U4-blocked) |
| **TOTAL gen** | **123.77** | **129.67** | **−4.5%** | demand-basis gap |
| net interchange | −23.45 | −23.45 (930) | RMSE **0 MW** | ✓ |
| CO2 (approx, class rates) | ~24.2 Mt | eGRID 26.9 (excl-biogenic) | ~−10% | downstream of gas |
| avg price (P10/U2 landed; demand-weighted P1) | $41.79 | actual RT $30.29 / DA $31.11 | +$11.50 vs RT | scored — mid over / tail under |

## The gas-total basis floor (why −9.9% is not a dispatch error)

Energy balance pins the in-state fleet's total: model TOTAL = served demand =
EIA-930 transmission-metered demand (147.05 TWh) + measured net interchange
(−23.45 TWh) = **123.77 TWh**, which is structurally **4.5% below** EIA-923's
plant-net-generation total (129.67 TWh). The non-gas classes all match EIA-923,
so the −5.9 TWh total gap **must** fall on the swing fuel: gas lands at −9.9%.

This gap is **not** closable by any honest dispatch knob:
- **td_loss gross-up** is ruled out — and now **Gold-Book-confirmed** (2026-06,
  `docs/nyiso-td-loss-resolution-2026-06.md`): NYISO Gold Book Table I-2 (NYCA
  Annual Energy, Note 1 "include transmission & distribution losses") reports
  actual 2023 energy = **147,050 GWh = the EIA-930 demand the model serves**, so
  the served demand is *already* the loss-inclusive net-energy-for-load. A
  `td_loss_factor > 0` gross-up adds the losses a second time (double-count;
  rules #11/#12). The reopened gas-total task confirmed this with a 3-year
  baseline and was closed without a code change.
- **import reconciliation** is now the keeper mechanism (`nyiso 24`,
  `--nyiso-import-reconciliation`), and the prior "import scaling — rejected"
  verdict is **retired**. That rejection applied to the *served-wedge* keeper,
  whose interchange already matched the measurement exactly (RMSE 0 MW) — there,
  scaling it would have *degraded* a perfect measured match, which is
  overfitting. **The current PRICED node does not match the measurement**: its
  near-static economic tranche ladder clears a near-flat ~18.5–21.6 TWh that
  deviates ±1–5 TWh/yr and does **not** track the metered schedule's
  year-over-year decline (23.45 → 20.35 → 19.09 TWh). Moving the priced node
  *toward* the metered schedule therefore **replaces an economic estimate with
  the authoritative measurement** (rule #11) — the *opposite* of overfitting.
  The monthly net-interchange band (transmission.`build_import_node_reconciliation`
  → dispatch.`_build_import_node_rows`, ±2% `NYISO_IMPORT_RECON_BAND_FRAC`) pins
  the node's **monthly net throughput** to `nyiso_net_interchange` while the
  priced tranches still set the marginal LMP *within* each month's envelope. The
  target is the measured schedule itself (a forward-reproducible boundary INPUT,
  not the scored OUTPUT), **not** a residual-minimizing volume — no fitted adder,
  no td_loss gross-up, no over-pin past the measurement (rules #1/#11/#12). This
  is standard production-cost boundary-flow calibration (Aurora/PLEXOS/GridView/
  PROMOD pin the metered tie-line net flow against an unmodeled neighbor; ReEDS
  fixes net trade with non-modeled regions). See the `nyiso 24` keeper section
  below and `docs/nyiso-dispatch-validation-2026-06.md`.
- **offer-curve / CHP / storage** reshuffle *within* the fixed total: the
  under-running CHP/peaker classes cannot be lifted into tolerance without
  pulling the on-target CC_REGULAR/ST_GAS down by the same TWh, and the obvious
  CHP lever does not even do that. The P12 `nyiso 2 chp-covered` probe
  (`--chp-startup-covered`, removing the steam-host startup-amortization markup)
  moved CHP by only **+0.1 TWh total** (CC_CHP +0.03, ST_CHP +0.05, CT_CHP
  +0.02; gas total 57.53 → 57.54, price $42.72 → $43.02) — i.e. the CHP/peaker
  deficit is **structural** (the model dispatches CHP economically and enforces
  no hard steam-host must-run floor), not a startup-cost artifact. The current
  split — deficit on the small CHP/peaker classes, big classes on target — is
  the least-distorting landing spot for the basis gap.

Benchmarked against EIA-930 (the operationally consistent basis), gas is
−5.7% (57.53 vs 61.00) — i.e. the class is within a basis-width of tolerance;
the −9.9% is the EIA-930/EIA-923 reconciliation, documented, not tuned.

## Config (the knobs that matter)

- `td_loss_factor = 0.0` (EIA-930 NYIS demand is transmission-metered /
  generation-side; no gross-up — playbook §8.1).
- **Net interchange served by default** (P9b): `load_demand` folds the measured
  EIA-930 `NYIS hourly` `Total interchange` (−23.45 TWh, export-positive, served
  as-is) into demand; the priced node stays the forward mechanism
  (`--priced-interchange`, `include_interchange=False`).
- **Measured monthly gas on by default** (P7): `gas_monthly_actuals = True` +
  `gas_plant_monthly_fuel_pricing = True`. The NYISO ISO-month series carries
  real winter spikes (Jan-2023 **$10.02**/MMBtu, Feb $5.62 vs the flat $2.54 HH
  seed). The explicit `--gas-monthly-actuals` P12 probe was a **no-op** (already
  default) — confirmed byte-identical mix and price duration.
- **RGGI** $13.49/t (2023) active via `state_carbon_price_by_iso.NYISO`.
- **Hydro**: 154-plant, 28.40 TWh annual energy budget; lands +1.3% vs EIA-923,
  no over/under-displacement (the §8.4 hydro failure mode is clean).
- **Dual-fuel**: machinery active (385 gas tranches / 15.9 GW capped at the
  delivered oil price) but oil clears 0.01 vs 0.42 TWh — even measured monthly
  gas (Jan $10) never crosses distillate parity (~$16/MMBtu), so the switch does
  not trip on monthly data. **This is the documented P13 limitation: the winter
  oil recovery is gated on the U4 daily Transco-Z6/Iroquois gas basis, which is
  not uploaded for NYISO** (only the NEISO/Algonquin leg is filled).

## Failure-mode watch (P12 checklist)

- **Residual gas after interchange** 🟢 — gas is *under*, not over: the served
  measured wedge fully removes the P11 over-generation; the residual −9.9% is
  the demand-basis floor above, not unserved imports.
- **Downstate congestion separation** 🟡 now scored (P10/U2 landed) — model
  collapses the four downstate zones to one price and captures only the
  upstate-cheap / downstate-dear split (≈$4), not the full actual J−A spread
  (≈$13); the interface-TTC structural item (U7). See the price re-score below.
- **Hydro displacement** 🟢 — +1.3% vs EIA-923, budget honored.
- **Nuclear refuel months** 🟢 — −0.1% annual; monthly CF overlay clean.
- **Import-share drift** 🟢 (2023 −23.45 / 2025 −19.09 TWh, exact). **🔴 2024
  is data-blocked (below).**

## 2025 — UNBLOCKED & price-scored (2026-06-12)

The EIA-930 `NYIS hourly` extract was refreshed to span full 2025 (was Q1-only),
so `nyiso_net_interchange(2025)` now returns the measured series (−19.09 TWh) and
the backcast serves the import wedge. Run `nyiso_p12_2025_refreshed` (dashboard
`nyiso 2025 refreshed`): the P12 **+22.7% over-generation closes** — gas 68.30
TWh (**−2.8%** vs EIA-930 70.25), TOTAL 132.76 (**+2.5%** vs EIA-930 129.54),
nuclear −0.1%, wind exact, hydro at budget. **EIA-923 2025 is the preliminary
M-file** (total 115.84 TWh, renewables/biomass/oil under-reported) — flagged,
not chased; EIA-930 is the operational basis. Full detail in the calibration log
("NYISO 2025") and the bundle `SUMMARY-nyiso-2025-refreshed.md`.

## Price re-score (P10/U2 landed — no longer level-only)

System level + duration ($/MWh), vs `actual_lmp.json` + `actual_lmp_hourly_NYISO`:

| year | model avg | actual RT | resid | p50 m/a | p90 m/a | p99 m/a |
|---|---|---|---|---|---|---|
| 2023 | 41.79 | 30.29 | +11.50 | 36/26 | 66/42 | 104/120 |
| 2025 | 69.24 | 60.73 | +8.51 | 57/45 | 114/114 | 157/222 |

Per-zone level resid vs actual DA ranges +$1.7 (Long_Island) to +$12.9
(Upstate_West, 2023). Both years over-price the mid-merit band and under-price
the scarcity tail (p99/max) — the no-ORDC/no-reserve-scarcity signature; p90 is
near-exact in 2025. This is the price level the model produces honestly; the
offset is the structural scarcity gap, not an offer-band miss.

## Blocked years (not runnable as clean backcasts yet)

- **2024** — blocked on `NY_2024` unit-level CEMS (only facility-level present)
  and the missing `NYISO_2024_renewable_capacity.csv`.

## History

P11 (`nyiso p11 smoke 2023`) was the structural smoke; P9b served the measured
net interchange (the dominant structural gap), turning the interchange row green
and gas from +25.6% to −9.9%. P12 confirmed the structural config is the keeper.
P12 probes, all rejected (logged in `docs/calibration-log.md`, "NYISO P12"):
`nyiso 1 gas-actuals` (no-op, already default), `nyiso 2 chp-covered`
(negligible — CHP deficit is structural, not a startup-cost artifact).

`nyiso 28 native-hr` (2026-06-25, **rejected probe**): re-grounded the CC/ST
offer curve to NYISO's own CAMPD incremental-HR medians (new tool
`scripts/data/derive_campd_marginal_hr.py`), removing the ERCOT-borrowed reach. It
craters `C3a` to −24/−26.5/−23.5 % because the bare CEMS marginal HR omits the
competitive offer markup CEMS cannot measure (the borrowed 1.21 reach was
proxying that markup). The steam-side re-level was directionally right (halved
the 2024 `ST_GAS` under-run); keeper stays `nyiso 27`. Run-29 path: a
NYISO-grounded markup on top of the native marginal HR. See the run-28
attestation.

## Citations (P12 benchmarks & conventions)

- **Fuel-mix benchmark** — EIA-923 Generation & Fuel (2023), per-plant net
  generation rolled to the model class taxonomy; bundle `eia923.parquet`. 2023
  NYISO class totals: CC_REGULAR 33.01, CC_CHP 16.50, ST_GAS 8.14, CT_CHP 2.59,
  CT_PEAKER 2.07, ST_CHP 1.53 TWh (gas 63.84); hydro 28.03, nuclear 27.53,
  wind 4.77, solar 2.05, OTHER 2.20, biomass 0.84, oil 0.42 TWh.
- **Net interchange** — EIA-930 `NYIS hourly` `Total interchange` (export-
  positive), 2023 = −23.45 TWh / −2,677 MW avg; served as-is by `load_demand`
  (P9b). Coverage: 2023 full, 2024 full, **2025 full (refreshed 2026-06-12;
  −19.09 TWh)** — the EIA-930 extract now spans 2015–2026.
- **LMP benchmark** — `data/raw/_validation-source/actual_lmp.json` (per-zone DA/RT
  levels) + `actual_lmp_hourly_NYISO.parquet` (system hourly DA/RT), landed
  via P10/U2; 2023 RT $30.29 / DA $31.11, 2025 RT $60.73 / DA $60.71.
- **Demand basis** — EIA-930 `NYIS hourly` Demand is transmission-metered
  (generation-side / net of BTM PV), so `td_loss_factor = 0.0` (playbook §8.1;
  param `scenario.td_loss_factor`, EIA-930 Demand + Interchange = Net Generation).
- **CO2 benchmark** — eGRID2023 (EPA, `egrid2023_data_rev2 2.xlsx`), NYISO 2023:
  gas_cc 16.25 + gas_ct 10.36 + oil 0.26 = 26.86 Mt (biomass 1.33 biogenic,
  excluded under EPA/RGGI accounting).
- **RGGI carbon** — `state_carbon_price_by_iso.NYISO` $13.49/t (2023), RGGI
  quarterly CO2-allowance auction clearing prices (annual simple average).
- **Measured monthly gas** — EIA-923 monthly Natural Gas receipt costs,
  volume-weighted to the NYISO hub: Jan-2023 $10.02/MMBtu, Feb $5.62 (vs the
  flat $2.54 Henry-Hub seed). Distillate (oil) parity ~$16/MMBtu (EIA-923
  Schedule 5 Petroleum receipts) — never crossed on monthly averages, hence the
  U4 daily-basis gate on winter oil.
- **Hydro budget** — 154-plant EIA-923 annual energy budget 28.40 TWh (2023);
  NYPA treaty min-flows `nyiso_hydro_treaty_min_flow` (1957 St-Lawrence/Niagara
  treaties).
