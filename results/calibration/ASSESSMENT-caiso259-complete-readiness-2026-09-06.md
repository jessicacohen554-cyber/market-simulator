# ASSESSMENT — caiso-259: what stands between CAISO and `complete` / frontier, measured. **Nothing on the merits blocks the marker; it is an owner act and the owner declined it at caiso-257. What blocks SPENDING the marker is data: a 2022 touchpoint cannot be built today (the demand input chain stops at a missing 2022 bench part) and cannot be PRICE-scored at all (CAISO OASIS retention aged out 2022 hub LMPs and intertie prices in 2026-03). ZERO LP.**

**Session caiso-259, 2026-09-06.** Branch
`claude/caiso-258-backcast-calibration-b1nal9` (continuation; caiso-258 is
merged on `main`). Keeper **`2026-09-06-caiso-257-b1-ctonly`** UNCHANGED,
DETERMINATION **CALIBRATED** (rubric v3.6). Rule 22 `[R-HOLDOUT]`: 2023–2025
only; CAISO holds no `complete`/`final` marker; freeze ACTIVE (locked tier).
**No 2022 model output exists. No 2022 actual was compared to anything. No
artifact for 2022 was written.** Every read below is data-readiness (rule 22
channel 1, unrestricted): year-coverage of inputs and a no-LP fleet rebuild
that stopped at its first missing input.

---

## §0 — The answer, in order

1. **`complete` itself needs no more calibration work.** The 2026-08-06
   withdrawal rested on a NOT-YET keeper (C3a failing 2024/2025). Since
   caiso-252 the keeper reads CALIBRATED; caiso-257 holds it with every scored
   criterion passing and C3c the lone ledgered caveat. The ERCOT/PJM precedent
   asks for (a) a CALIBRATED determination re-verified on committed artifacts,
   (b) a frontier basis stating that every chartered lane is adjudicated and
   what remains is blocked on owner data decisions, (c) the owner's word. (a)
   holds; (b) is drafted in §4 and is honest as written; (c) was declined at
   caiso-257 ("not now, keep raising it"). **Raised again here, not granted.**
2. **Spending the marker on 2022 is NOT possible today.** §1 lists two hard
   blockers, one of which (2022 prices) is a genuine source gap that an owner
   must decide on, and four silent fallbacks that would run a different recipe
   in 2022 without warning.
3. **Frontier's remaining named objects** are all blocked-on-data or under
   DO-NOT-REDO (§4), which is exactly the ERCOT frontier posture. The one
   still executable without new data is a public-record search for a Panoche
   obligation instrument; it was not run this session (§6).

---

## §1 — 2022 readiness: HARD BLOCKERS (the rebuild stops)

The no-LP rebuild `reconstruct_bundle_fleet(caiso257_ctonly, 2022)` raised at
its first input; 2023 rebuilt normally (1,846 rows).

| # | item | status | what closes it |
|---|---|---|---|
| **H-1** | `data/raw/reference/caiso-supply-consistent-demand/caiso_supply_consistent_demand_2022.csv` — the keeper's demand input (caiso-80 Option A basis) | **MISSING; `FileNotFoundError`** | `derive_caiso_supply_consistent_demand.py` for 2022 — but it reads the year's **CEMS-anchored bench part** (`bench/CAISO/2022.json.gz`), which does not exist. Chain: `regen_caiso_bench_cems.py` (YEARS hard-coded 2023–2025; extend to 2022) ← EIA-923 2022 annual/monthly generation (**present**, `eia923_monthly_generation.parquet` 2018–2026) + CAMPD 2022 (**present**) + EIA-930 2022 (**present**, 8,760 h, `NG: OTH` carried). Executable, zero owner input. Note the convention: only marker ISOs carry out-of-training bench parts today (PJM 2021–22, NEISO 2020–22, ERCOT 2022); writing CAISO's before the marker is data prep, but I did not write it in a no-marker lane without saying so first. |
| **H-2** | measured CAISO hub LMPs 2022 (`actual_lmp_hourly_CAISO.parquet` 2023–2026; `actual_lmp.json` CAISO 2023–2026) | **SOURCE GAP.** OASIS `PRC_LMP`/`PRC_INTVL_LMP` retention is a moving ~39-month window (boundary 2023-04-22 on 2026-08-04; `fetch_caiso_oasis.py`); 2022 can never be re-fetched from OASIS. | An **owner data decision**: (i) accept a **volume-only** 2022 rung (C1/C2/C4 scored, C3a/C3b/C3c SKIPPED — the determination for that rung reads unscored-criteria, which rule 30(c) says cannot downgrade the ISO), or (ii) fund an alternative 2022 price source (candidates to adjudicate, none on disk: CAISO's own historical price archives outside OASIS, the EIA/ICE daily SP15/NP15 day-ahead indices — daily not hourly, or a third-party hourly archive). Rule 14 applies: a daily index is a different aggregation and would need a documented reconciliation, not a silent substitute. |
| **H-3** | `wecc_intertie_lmp_hourly_CAISO.parquet` (PALOVRDE / MALIN raw hub, the injector's own input) 2023–2025 only | **SAME SOURCE GAP** (OASIS intertie LMPs). In 2022 the caiso-87 surplus row and the caiso-93/94 clean rows read no hub: `surplus.any()` is False so the surplus row is **not injected**, and the clean rows' admissibility state is unmeasurable. The 2022 import stack would be a **structurally different recipe**, silently. | Same owner decision as H-2; without it the 2022 rung cannot run the keeper's import structure. |

**Verdict as found: NOT READY, and H-2/H-3 are not fixable in-session.**

## §2 — 2022 readiness: SILENT FALLBACKS (the rebuild would not warn)

Each of these takes a documented default when the year is absent. In 2022
the keeper would therefore run a recipe it was never scored on.

| # | input | 2022 behaviour | extension (rule 23: source-data update, cited) |
|---|---|---|---|
| S-1 | `STATE_CARBON_PRICE_BY_ISO["CAISO"]` = {2023: 33.03, 2024: 35.23, 2025: 28.06} | **`None` → the CARB allowance cost is ZERO in 2022** for every in-state fossil unit (the NYISO-134 D-1 defect, CAISO edition). At ~0.41 t/MWh a CC loses ~$11–12/MWh of cost; it re-orders the merit stack, not just the level. | transcribe the four 2022 CARB joint-auction settlement prices (Feb/May/Aug/Nov 2022) from CARB's auction summary results, same recipe as 2023–2025; `CARB_FLOOR_PRICE` 2022 likewise. *Not asserted here — must be transcribed and cited.* |
| S-2 | `IMPORT_TRANCHES_BY_YEAR["CAISO"]` 2023–2025 (DMM RA-import capability: PNW_hydro_base 1,072 / DSW_solar_PV 1,251 in 2023) | falls to the **static** ladder (1,566 / 1,805) — a different firm block | DMM **2022** annual report RA-import table, same basis as the 2023/2024 rows (the 2025 row is already flagged as a methodology break, caiso-252 §3.4). |
| S-3 | `CAISO_DSW_{OVERNIGHT,DAYTIME,SURPLUS}_CLEAN_DEPTH_BY_YEAR` 2023–2025 (5,870 / 5,441 / 5,312 in 2023) | falls to the **STATIC** depths (6,187 / 5,733 / 5,192) | `derive_caiso_overnight_clean_depth.py` and its siblings on 2022 — **but their inputs are the OASIS intertie series (H-3)**, so 2022 is not derivable on the frozen recipe; the static fallback is the only option and must be stated on the rung. |
| S-4 | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]` 2023–2025 and `nuclear-availability-CAISO.csv` (NRC daily, 2023+) | monthly CF falls to the static seasonal pattern + EFORD; the NRC daily windows are **absent** (Diablo's 2022 refuel timing lost) | `derive_nuclear_monthly_cf.py --isos CAISO --years 2022` (EIA-923 2022 present) then `derive_nuclear_availability.py --iso CAISO --years 2022` (`nrc-reactor-status/2022PowerStatus.txt` **present**). Executable, zero owner input. |
| S-5 | `CAISO_RA_MUSTOFFER_GAS_MW` 2023–2025 | falls to the latest vintage (2025) | **inert** on this keeper: `caiso_ra_mustoffer_quantity_gate = False`. No action. |
| S-6 | `caiso-dam-outages` (418 windows in 2022 vs 272,508 in 2023) | — | **inert**: `caiso_dam_outages = False` on the keeper. No action. |

**Verified present for 2022, no action:** EIA-930 CISO wide extract (8,760 h,
battery `NG: OTH` carried, min −2,202 / max +3,028 MW); TAC-area load
(`CAISO_tac_load_hourly_2022.csv`); CAMPD unit-level 2022; CAMPD unit-outage
overlay 2022 (496 rows, the same `cf156483` extract the keeper runs);
`caiso-hsl` 2022; `caiso-weather` 2022; `caiso-curtailment` 2022; F923
monthly fuel costs 2018–2026; CA-composite citygate daily and PG&E/SoCal
weekly 2018–2026; `caiso_zonal_gas_hub.csv` 2022 rows; EIA-860
`vintage_2022`; MIC/LCR partition delivery years 2018–2025 (the
`mic_partition` seam cap resolves for 2022); the measured offer surface is a
2023–2025 statistic applied as ONE config (rule 1(b)) and needs no 2022 row.

## §3 — What a `complete` declaration session would execute (zero LP)

In order, on the ERCOT template in `calibration-complete.json`:

1. `scripts/calibration_verdict.py --run-id 2026-09-06-caiso-257-b1-ctonly`
   — re-verify CALIBRATED on committed artifacts (never a solve).
2. Move CAISO from `withdrawn` to `complete` with: `keeper`,
   `keeper_at_declaration`, `determination` (the re-verification text),
   `tier_authorized` = validation only, `locked_test` = NOT AUTHORIZED,
   `config_2022_designation` = the caiso-257 recipe verbatim, one config,
   `frontier_basis` (§4), `freeze_interaction` (locked tier frozen; validation
   tier governed by the marker + `--holdout-authorized`), `keeper_rekey_policy`
   (D-5(b)).
3. Stamp `frontier` in `keepers/CAISO.json`; `build_status.py --iso CAISO`;
   `audit_keepers.py --iso CAISO` (M1); the `calibration-keeper-auditor` agent.
4. Then, and only then, the §1/§2 extensions, `derive_actual_tail.py` (which
   is marker-gated and will emit CAISO 2022 only once the marker exists — and
   only if H-2 is resolved), and the 2022 rung under `--holdout-authorized`,
   stamped to the keeper per rule 30(a).

## §4 — Draft frontier basis (for the owner's signature; not applied)

> Every chartered CAISO lane is adjudicated on record. The in-model lever
> queue was measured empty at caiso-200; the eight promotions since
> (caiso-231 → caiso-257) were measured-input repairs and de-contaminations
> under rules 13/14, each pre-registered with C3a excluded from its basis and
> none a tuned value (DOF 9 entries / 6 residual, no `authorized_price_tuning`
> block). What remains named, and why none is an executable calibration lane:
> **(i)** the night/evening price-taking import volume — ~1.8 GW at hod 22–23
> in 2025 that no armed rung offers at the matched price (caiso-258 D-3) — a
> **data intake** on contracted import showings beyond the DMM RA figure,
> rule-13 admissibility to adjudicate first; **(ii)** the Panoche / CT volume
> miss — a per-plant commitment object admissible only through a public
> obligation instrument (caiso-119 R4), never a pin; **(iii)** the
> whole-plant-off days (Moss Landing 91, Otay Mesa 121 in 2025) — the
> caiso-187/192 mechanical-vs-layup object, adjudicated and DO-NOT-REDO;
> **(iv)** S2 (DA/RT two-settlement), unfunded under caiso-201; **(v)** C3c,
> the accepted model-class limitation (in-model queue empty on every route,
> caiso-144). Standing constraints carried, not hidden: C4-2025 at 0.300
> against ≤ 0.30; the C3a weight-basis ask (caiso-247 §4.5); the sidecar
> identity residual (caiso-258 §2.1); the six residual DOF rows, two of which
> caiso-238 found groundable (`ST_GAS committed`, instrument in repo;
> `battery_dispatch_adder`, data intake).

## §5 — A correction to caiso-258, recorded here and in the FINDING

caiso-258 §2.3 offered, as a post-registration "lead" for the caiso-247 §4.5
demand-basis ask, that EIA-930's `Demand` cell carries the same mid-day term
as the contaminated `NG: NG` cell. **That is not a lead; it is the caiso-80
Option A basis the keeper's demand input is already built on**
(`derive_caiso_supply_consistent_demand.py`: `demand = NetGen − NG_cell +
CEMS gas + cogen + fold-in − TI`, owner-signed 2026-07-13). The measurement
in caiso-258 is consistent with it and adds nothing to it. The FINDING's
parenthesis is annotated in place; nothing else in caiso-258 depends on it.

## §6 — Not done this session, stated

* No 2022 artifact written (H-1 chain, S-1, S-2, S-4) — each is executable
  data prep, but H-2/H-3 decide whether a 2022 rung is worth building at all,
  and that is the owner's call before the intakes are spent.
* The Panoche instrument search (public RMR / CPM / exceptional-dispatch
  record) was not run.
* `complete` not declared; `program-status.json` stamp not touched.

## §7 — The two decisions this needs from the owner

1. **Declare `complete` / frontier on `2026-09-06-caiso-257-b1-ctonly`** on
   the §4 basis — yes or not now.
2. **The 2022 price source (H-2/H-3):** accept a volume-only 2022 rung on the
   frozen recipe with the S-3 static depths stated, or fund an alternative
   hourly price archive for 2022 (an intake with a rule-14 reconciliation),
   or leave the validation ladder unspent until one exists.

**No run registered (none produced), no keeper change, no `ScenarioConfig`
field, no marker, no 2022 artifact.**
