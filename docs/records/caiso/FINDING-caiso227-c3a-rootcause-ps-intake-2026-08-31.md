# FINDING — caiso-227: the C3a-2025 DA-basis residual TAKEN TO ROOT CAUSE — the marginal object is the **fuel-coupled CC econ offer acting as the model's price floor through the mid-hours**: reality cleared BELOW the cheapest available CC offer in 42.3 % of Sep–Dec-2025 load-weighted hours while the model did in 23.2 % (a share that did not move YoY), on a CC floor that itself rose +$2.34 lw on measured fuel — so the 2025-specific growth is the measured autumn fuel rise propagating 1:1 through a marginal rung reality increasingly clears under (model YoY coupling +1.23× the CC-offer move; reality −0.32×), compounded by the measured Oct/Dec CC outage deepening (−1.4/−1.3 GW YoY). The supply-state face on the honest CEMS basis: belly gas −762 MW, evening gas +1.24 GW, belly hydro −453 MW, belly imports +1.5 GW — the standing committed-gas/water-state wedge at hour grain. AND the funded PS water-state intake LANDED A PUBLIC BREACH OF THE WALL: Helms (FERC P-2735) published its measured HOURLY generation/pumping/flow/reservoir record 2001-01-01..2022-09-30 in the public FLA Appendix B1 — intaken through the full data contract — but the record ENDS 2022-09-30 and the caiso-186 §a.3 ceiling stands, so **THE HONEST NULL HOLDS**: no admissible in-model lever of the required 2025 size. NOT-YET stands. ZERO SOLVES (2026-08-31)

**Keeper `2026-08-26-caiso-220-c1-crosswalk` UNCHANGED** — re-verified this
session with `calibration_verdict.py --run-id` (committed artifacts, no
solve): NOT-YET, basis *"undocumented out-of-tolerance (FAIL) criteria:
price_mean"* — C3a +4.0 PASS / +12.5 / +15.5 % the sole load-bearing FAIL,
C1 12/12 free 8/8, C2/C3b/C4/C6/C8 PASS, C3c the single ledgered caveat.
**No mechanism armed, no `ScenarioConfig` field, no LP built, no solver
called, nothing registered, no matrix cell moved.** Charter: the owner's
2026-08-31 caiso-227 handoff (C3a-2025 root-cause round + the newly FUNDED
caiso-201 Q2(a) PS water-state intake). `calibration-complete.json` (no CAISO
marker) and `holdout-freeze.json` (ACTIVE) untouched; every model/score read
stayed inside 2023–2025 (the intaken plant record spans 2001–2022 as DATA,
which rule 22 leaves unrestricted — no out-of-training year was solved,
scored, or read against model output).

**NUMBERING NOTE (charter-directed):**
`results/calibration/PRECOMMIT-caiso227-ofo-arm-2026-08-31.md` is caiso-226's
FILED, UNEXECUTED pre-registration of the future OFO arm; its "227" label is
historical. THIS session is caiso-227 (this document); the OFO arm executes
later under its own number and that PRECOMMIT travels with it unchanged.

Instruments (committed, no LP, no solve):

* `scripts/probes/_caiso227_da2025_rootcause.py` →
  `results/calibration/_caiso227_da2025_rootcause.json` — §A–§H below, from
  the keeper's committed `hourly/` sidecars, the committed actual-LMP
  reference (rt+da), the rubric weights, the EIA-930 CISO extract, the CAMPD
  hourly unit files, the bench parts, and the licensed caiso-105/131
  `run_year(fleet_only=True)` reconstruction imported UNCHANGED from
  `_caiso202_marginal_rung.py` (charter reuse directive; only bundle + cache
  paths re-pointed).
* The `ps-water-state` intake artifacts (§I table).

---

## §A — The 2025 DA-basis residual on THIS keeper (probe §A; rt_lw common weights)

| year | model lw | DA lw | gap vs DA | gap vs RT | Sep–Dec share | spring (Mar–May) |
|---|--:|--:|--:|--:|--:|--:|
| 2023 | 55.27 | 61.68 | **−6.41 (−10.4 %)** | +1.34 | −0.44 | −1.30 |
| 2024 | 38.47 | 37.97 | **+0.50 (+1.3 %)** | +3.82 | +0.30 (61 %) | +1.15 |
| 2025 | 38.97 | 35.40 | **+3.57 (+10.1 %)** | +4.55 | **+2.14 (60 %)** | **+0.81** |

caiso-202 §A reproduces on the caiso-220 keeper: 2024 is in band against the
DA (basis-dominated, `caiso_da_rt_two_settlement` R and untouched); 2025 fails
on both bases and its DA-basis gap is 60 % Sep–Dec + the spring belly. The
worst single month is **October 2025 (+0.82 of the +3.57)**.

## §B — Which marginal rung (probe §B; DA-positive hours, biomass-drop-corrected)

2025: **fleet gas-CC econ rungs 49 %** of the positive gap (3,578 h),
unmatched storage/hydro inter-temporal duals 22 %, `fleet:import` 6 %, coal
rungs ~7 % (13 MW plant, degeneracy — caiso-202 §C.1 acquittal carries), all
import tranches combined ~5 %. Identical structure in 2024. The caiso-202 §C
attribution holds on the DA basis on this keeper: **the CC econ rung —
carrying CAISO's own measured DAM bid multipliers — is the binding object**,
and the belly's unmatched storage duals inherit its level (caiso-202 §C.2).

## §C — The supply state in the gap hours, on HONEST bases (probe §C/§C2)

The raw EIA-930 `NG: NG` cell is **corrupt for CISO from ~2024-05**
(owner-signed `FINDING-caiso-c2c4-bench-basis-930ng-2026-07-12.md`: a growing
noon-peaked solar-shaped phantom block), so the measured-gas witness is
rebuilt on the CEMS basis — CAMPD hourly unit records summed over the bench
part's own CAISO gas-plant membership (gross MW; the ~6.4 TWh/yr non-CEMS
cogen block, roughly flat, is not in the series; both stated wherever used).
Model vs measured, 2025 (MW means over the cell):

| cell | model gas − CEMS gas | hydro_net (model − 930 WAT) | interchange (model − meas., −=extra import) |
|---|--:|--:|--:|
| all hours | **+193** | −75 | −368 |
| DA-positive-gap hours | +214 | −118 | −533 |
| **Sep–Dec belly (hod 10–15)** | **−762** | **−453** | **−1,519** |
| Sep–Dec evening (17–21) | **+1,235** | +813 | +989 |
| spring belly | +290 | −1,651 | −1,756 |

The model's ANNUAL gas is right (48.2 TWh vs 46.5 CEMS gross + cogen); its
**shape is wrong in exactly the caiso-135/140 pattern**: reality's committed
gas rides THROUGH the belly (model −762 MW there) and backs down in the
evening behind battery discharge (model +1,235 MW there), while the model
cycles gas off midday and substitutes imports (+1.5 GW extra belly imports).
The belly hydro deficit (−453 MW Sep–Dec) is the caiso-140 §B water wedge,
unchanged on this keeper. Model demand equals the measured EIA-930 D by
construction (same TAC basis), so these are real supply-state deltas, not
load bookkeeping.

## §D–§F — Why 2025 grew: the fuel-coupling divergence (probe §D/§F/§G)

Monthly YoY (2024→2025), the three autumn months that create the year:

| month | Δ CC offer (cap-wtd p50 mc) | Δ model λ | Δ DA actual | Δgap |
|---|--:|--:|--:|--:|
| Sep | +5.99 | **+9.85** | +2.75 | +7.10 |
| Oct | +2.14 | +0.62 | **−8.27** | +8.89 |
| Nov | −0.48 | **+9.23** | +5.41 | +3.82 |
| Dec | +6.22 | −2.68 | −4.35 | +1.67 |
| **Sep–Dec mean** | **+3.47** | **+4.25 (ratio +1.23)** | **−1.11 (ratio −0.32)** | |

The model's Sep–Dec λ tracked the measured hub-gas-driven CC offer rise at
**1.23×**; reality's DA moved **against** it at −0.32×. Two measured model-side
drivers compound it: the CAMPD outage instrument removes **−1,417 MW (Oct)**
and **−1,321 MW (Dec)** more CC availability in 2025 than 2024 (probe §G — a
correct measured input pushing clearing up the measured offer curve; the
caiso-199/200 arc fully identified this instrument and nothing here re-opens
it), and demand/renewables YoY move roughly in parallel in model and reality
(probe §D — the divergence is price-formation-side, not a driver-input error).

## §G — THE ROOT CAUSE, measured (probe §H — the below-the-stack witness)

Share of load-weighted hours whose clearing price sits BELOW the cheapest
**available** CC offer (`cc_min`, the model's effective mid-hour price floor):

| scope | model 2024 | DA 2024 | model 2025 | DA 2025 | cc_min lw 2024→2025 |
|---|--:|--:|--:|--:|--:|
| annual | 33.9 % | 46.9 % | 30.1 % | 44.9 % | 36.57 → 37.24 |
| **Sep–Dec** | **23.1 %** | **37.3 %** | **23.2 %** | **42.3 %** | **36.79 → 39.13** |
| spring | 59.9 % | 70.5 % | 43.7 % | 55.2 % | 34.83 → 33.83 |

**This is the root cause at the grain the charter asked for.** In every
season reality's DA clears below the CC stack in ~12–19 pp more load-weighted
hours than the model — the model's supply state cannot push the margin under
the gas stack as often as reality's committed/must-flow cheap supply does.
The 2025-specific growth is now mechanical: the model's Sep–Dec below-stack
share was **flat YoY (23.1 → 23.2 %)** while reality's **widened 5 pp
(37.3 → 42.3 %)**, and the floor itself **rose +$2.34** on measured fuel — so
every escaped hour escapes a higher floor and the gap grows in both count and
depth. "The standing CC-side supply-state residual" (caiso-202's lane
attribution) is hereby made concrete: *the residual is the below-stack hour
wedge, its price is the fuel-coupled CC floor, and its 2025 growth is the
measured fuel rise times a wedge the model holds constant.*

## §H — What would close it, and what it costs (charter deliverable; no lever armed)

Closing C3a-2025 (−$1.90 lw required) means moving ~15–19 pp of Sep–Dec (and
a similar spring share) of load-weighted hours from CC-offer-priced to
below-stack-priced. The instruments that could do that are all adjudicated on
this record:

1. **The committed-gas ride-through / commitment wedge** (belly −762 MW
   measured here; caiso-140 §C measured the full object at 2.3–2.6 GW) —
   adjudicated R/unfunded (caiso-140 §D/§G, caiso-142/143, caiso-191 rulings);
   nothing here re-tests it, and this finding's shape witness is the same
   object re-measured, not new evidence of a new mechanism.
2. **Sub-zonal surplus/strandedness pricing** — the caiso-221 §E / caiso-223
   representation-grain lane, its static-cap arm R (caiso-224), re-armable
   only through the caiso-222 §(i) watches (all NULL at caiso-225).
3. **The PS/hydro water state** — now partially measured (§I), ceiling
   unchanged: caiso-186 §a.3 bounds its most favourable C3a reach at 62.1 %
   of 2024's required move and **10.4 % of 2025's**, and the public record
   ends 2022-09-30 (no direct 2023–2025 overlay exists).
4. **Import spot capacities** — declared residual (caiso-191 §4; direct λ
   share <5 %, caiso-202 §C).
5. Anything priced to the residual (a coupling haircut, a level adder, a
   scaled offer) — rule 13/24, forbidden, not proposed.

**THE HONEST NULL THEREFORE HOLDS**, exactly as caiso-202/221/222 recorded
and the charter pre-authorized: no admissible in-model lever of the required
2025 size exists at this representation grain. No PRECOMMIT is filed, no
solve is earned, and the caiso-222 §9 terminal rest (Q1 = option 3) stands
undisturbed — this finding sharpens its record from "attributed at this
grain" to "attributed at hour × rung × driver grain, with the YoY growth
mechanism quantified."

## §I — The FUNDED PS water-state intake: the wall has a PUBLIC breach, and it is landed

**The discovery.** The walled object (caiso-141 §G; caiso-186 §a.1: an hourly
split of PS operation from conventional hydro — every public feed nets PS,
omits it, is monthly, or covers ≤39.7 % of the fleet) has a public breach for
its dominant plant: **PG&E filed Helms' measured hourly operations record as
the PUBLIC Appendix B1 (Hydrology) of its Final License Application** — FERC
eLibrary accession **20240418-5301** (P-2735, 2024-04-18) — hourly
GENERATION/PUMPING (MWh), generation/pumping FLOW (cfs), and Courtright/
Wishon reservoir ELEVATION/STORAGE (ft/af), **2001-01-01 → 2022-09-30**
(190,632 gap-free hours on a fixed local standard clock). Also re-verified
this session, all still walls: the EIA-930 2024-H2 schema's explicit
"Pumped Storage" columns exist but **CISO files nulls in them** (live API
total = 0, committed 2024H2–2026 BALANCE files all-null), and PG&E's own
relicensing portal is password-walled.

**What landed** (the full data-intake contract, caiso-226 pattern):

| artifact | path |
|---|---|
| schema (the contract) | `data/dictionary/schema/ps-water-state.schema.yaml` |
| raw snapshot (immutable, sha-manifested) | `data/raw/ps-water-state/caiso/helms_fla_appb1_hydrology.xlsx` + `_snapshot.json` + `README.md` |
| fetch | `scripts/data/fetch_helms_ps_water_state.py` (the eLibrary `File/DownloadP8File` web-API route; the browser `filedownload` URL serves only the SPA shell) |
| registry package | `scripts/lib/ps_water_state/` (`__init__.py`, `caiso.py`) |
| curation | `scripts/data/curate_ps_water_state.py` (+ `regenerate_clean.py` registration) |
| clean partition | `data/clean/ps-water-state/CAISO/ps-water-state.parquet` (derived, gitignored) — 190,632 rows, HELMS |
| tests | `tests/curation/test_curate_ps_water_state.py` (10, tmp-CLEAN_DIR) |
| dictionary | `data/dictionary/data-dictionary.md` re-rendered |

**Verification, against interest where possible:**

* **Clock proof**: 190,632 rows = exactly 7,943 days × 24 h — gap-free,
  fixed-offset, no DST events; asserted by the parser (a gap raises).
* **Cross-source check**: monthly (generation − pumping) vs the independent
  EIA-923 Helms record (plant 6100) tracks at **0.94–0.97 in high-activity
  months** (May-2019 0.97, May-2021 0.94, May/Aug-2022 0.97/1.05) and ~0.90
  annually — the expected direction and size of the plant-records-vs-
  net-of-station-service basis gap. The record is the real plant.
* **Fail-loud parsing caught two real source facts** (both kept as data, not
  "fixed"): 276 negative `flow_pumping_cfs` hours (−795..−0.03, publisher-
  signed reverse-flow during mode changeover — the schema documents them) and
  1,921 hours carrying BOTH generation and pumping (real within-hour mode
  changeovers — no exclusivity is asserted). HEC-DSS sentinels (−901/−902)
  land as nulls; any other negative in an energy/reservoir column raises.

**Ceiling and span, stated up front and not oversold (charter directive):**
caiso-186 §a.3 bounds this object's most favourable C3a reach at **62.1 % of
2024's required move and 10.4 % of 2025's** — partial by its own arithmetic —
and the record **ends 2022-09-30**, before the training window, so no direct
2023–2025 overlay exists even in principle from this source. It is intaken
because it is an accurate measured input the model lacked (rule 14; funded on
rule-1 structural-fidelity grounds per caiso-186 §a.5), grounding the
measured multi-year hourly *conduct* of a 1,080 MW plant the model runs as
part of "one entirely unrestrained arbitrageur" (caiso-127 §B2) — the same
admissibility class as multi-year CAMPD history grounding forecast emission
rates. **Nothing consumes it yet**: arming any mechanism on it is a
separately chartered session with its own PRECOMMIT, and fabricating the
2023–2025 hourly shape from monthly nets, the model's own arbitrage profile,
or any assumed allocation remains FORBIDDEN (rule 13).

**Still walled (`DATA NEEDED`, recorded in the raw README):** Helms
2022-10 → present (PG&E-internal; the relicensing record's study cut-off);
Eastwood (SCE, ~200 MW; no public record located); the DWR 39.7 % (CDEC
AF/flow telemetry needing its own reader + cited AF→MWh parameters); the
SQMD fleet split (SC-confidential; the caiso-222 route-(ii) class the owner
DECLINED).

## §J — Record changes

* This FINDING; `scripts/probes/_caiso227_da2025_rootcause.py`;
  `results/calibration/_caiso227_da2025_rootcause.json`; the §I intake
  artifact set.
* `docs/calibration-log/caiso.md`: caiso-227 entry (with the numbering note).
* **Matrix: NOT touched** — no mechanism was tested, no cell verdict moves,
  no `ScenarioConfig` field was added (the caiso-225/226 precedent; rule 26
  duty (b) attaches to mechanism tests, duty (c) to new solve-affecting
  mechanisms — neither occurred).
* Keeper, keeper shards, `calibration-complete.json`, `holdout-freeze.json`,
  every other ISO's files: **UNTOUCHED**. No run registered (rule 15 binds
  completed solves; none ran — the caiso-201 §"Rule-15/16 note" precedent).

## §K — DO-NOT-REDO (new, binding; the caiso-202 §I … 221 §G / 222 §8 / 225 §9 / 226 §6 chain carries whole)

1. **Never re-derive §A–§H while the caiso-220 keeper stands** — the
   committed probe reproduces every number from committed bytes in minutes
   (the fleet recon caches per year). Re-run it only against a NEW keeper.
2. **The below-stack witness (§G) is the C3a-2025 root-cause statement of
   record.** Do not re-attribute the 2025 residual to a fuel-input error, a
   demand error, or a renewables error — probe §D measures those parallel in
   model and reality; the divergence is the below-stack hour wedge.
3. **Never quote the raw EIA-930 `NG: NG` cell as CAISO's measured gas** in
   any 2024+ diagnostic — corrupt (2026-07-12 finding); use the CEMS basis
   as probe §C2 does.
4. **Never re-run the PS source archaeology**: the EIA-930 PS columns
   (CISO = nulls, live 2026-08-31), the password wall on
   helmsrelicensing.com, the eLibrary retrieval route, fileId and accession
   are all recorded (raw README + `_snapshot.json`). The only open PS-source
   work is the `DATA NEEDED` list itself.
5. **Never treat the Helms record as covering 2023–2025**, and never
   manufacture that coverage (rule 13). Any arm built on this datatype
   states the caiso-186 §a.3 ceiling (10.4 % of 2025) in its PRECOMMIT.
6. **Do not re-open the CAMPD outage instrument on §D–§F's numbers** — the
   Oct/Dec −1.4/−1.3 GW YoY is the fully-identified caiso-199/200 instrument
   doing its job on measured windows, cited here as a driver, not indicted.

Next number: caiso-228.
