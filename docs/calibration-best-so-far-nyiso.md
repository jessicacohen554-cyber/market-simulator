# NYISO calibration — best config so far

> **SESSION 2026-07-04 (probes `nyiso 43 ceiling oilbasis` + `nyiso 44
> faststart`, both registered NOT-YET; keeper unchanged): the run-42
> winter-spread blockers are ROOT-CAUSED AND FIXED, but promotion is blocked
> by a new repo-level regression.** The three carried items closed measured:
> **(E2)** the run-42 C2-2025 gas −2.5% FAIL was a *scoring-basis artifact* —
> the harness had silently enabled `dual_fuel_oil_reattribution` (spec'd
> NEISO-only) for every ISO passing `--gas-hub-basis-daily`, relabelling
> 0.8–1.5 TWh of parity-switched winter gas as oil while the measured NYIS
> EIA-930 feed attributes those hours to `NG: NG` (Jan-2025: 0.80 TWh
> relabelled vs 0.031 measured OIL; 2023: 2.17 TWh NYIS OIL vs a 0.42 TWh
> EIA-923 oil class — static plant-primary attribution). Gate restored to
> NEISO-only → C2-2025 **−0.1% PASS**, and C5a CO2 lands **in band all three
> years** (−2.3/−5.3/−3.7%; the 41 keeper's 2024 −7.1% breach was the same
> relabel exporting switch-hour CO2). **(E3)** the Feb-2023/Jan-2024/Jan-2025
> reconstructions exceeded the measured Algonquin-Citygate ceiling of the NE
> complex Z2 trades inside (13.21 vs 8.13; 8.60 vs 7.68; 18.60 vs 16.92) —
> the reconciled reference now caps each month at the measured ALG monthly
> and water-fills the shaved scarcity excess as a year-round base so the
> measured SOM annual spread is preserved exactly (three measured series, no
> constant; Jan-2024 overshoot +6 → +1.6). **(E1)** decomposed: east level =
> the ledgered offer-markup/reserve frontier (AS data on disk is *prices*,
> not condition-varying requirements → stays data-blocked); plus an upstate
> shoulder collapse (Upstate_West at the $1.4 wind margin ~75% of Apr-2023
> hours behind the measured 1,450 MW CE TTC while the recon band pushes
> ~830 MW of measured net imports through the upstate link; real upstate held
> ~$22-25 via gross two-way tie flows a single external node cannot see —
> per-interface flows/ratings are the new data ask). **THE BLOCKER:** commit
> `0c6c833` (2026-07-03, "Kill cross-ISO leakage of ERCOT-fitted gas offer
> bands") de-leaked the NYISO CT_PEAKER/CT_CHP econ bands to neutral 1.0 with
> "a NYISO-grounded CT econ ramp" as its documented open root cause — the
> LI/NYC peakers now over-run ~2.5× actual (CT 4.9 vs 2.13 TWh) and displace
> steam through the HARD C1 band (**2024 ST_GAS −3.4 TWh FAIL**). Every NYISO
> solve on current main fails this — verified including a re-solve of the
> keeper-41 config itself (CT 4.69/ST 7.65). `nyiso 44` shows the ISO-NE-style
> fast-start amortization (`--tranche-startup-amortization`, real structure,
> worth keeping) moves CT only 4.90 → 4.75: it cannot substitute for the
> missing offer-level grounding. Closure candidates (none on disk): LI/NYC
> peaker delivered-fuel basis (LDC citygate/interruptible; kerosene frames),
> a SOM-groundable markup (the 2024 SOM confirms offers sit above bid-based
> reference levels but publishes no per-class number), DEC Peaker-Rule
> run-hour limits. CEMS marginal HR is ruled out (run-28: 0.66–0.85× base).
> Best NYISO probe state: `nyiso 44` — C2/C5a/C1-2023/C6 PASS, C3a
> −15.4/−14.9/−13.0, C3b 0.207/0.201/0.195, C3c 0/0/7h (3 ledgered soft
> caveats; NOT-YET solely on C1-2024).

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
> +1.00 $/MMBtu; `scripts/fetch_nyiso_gas_narrative.py` + the
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
> (`scripts/derive_nyiso_st_reliability_floor.py`).
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
> (`scripts/derive_nyiso_ct_reliability_floor.py`; archived
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
> (new tool `scripts/derive_campd_marginal_hr.py`, NY+NJ CEMS pooled 2023-25,
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
`scripts/derive_campd_marginal_hr.py`), removing the ERCOT-borrowed reach. It
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
