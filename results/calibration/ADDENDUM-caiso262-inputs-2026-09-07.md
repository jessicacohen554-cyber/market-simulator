# ADDENDUM to PRECOMMIT-caiso262 — the 2022 inputs: S-1…S-4 and H-1, measured and landed

**Session caiso-262, 2026-09-07.** Written after the landings below and
**before** the rung is solved and before G-BENCH is compared. Keeper
**`2026-09-06-caiso-260-b1-demand`** UNCHANGED. **No solve is scored here**; the
one LP entered was the §5.1 bench scaffold, which is never scored and is
deleted before merge (rule 29(c)).

---

## §1 — What every one of these is, in one line

Rule 22 as amended 2026-08-06: **what is held out is the SCORE, never the
DATA.** Each item below is the 2022 row of a table that already carries
2023–2025, landed by the SAME producer, the SAME source and the SAME recipe.
Zero new `ScenarioConfig` fields, zero new parameters, zero tuned values, and
**nothing was selected by what it does to 2022** — no 2022 output existed when
any of them was written.

| id | what it was (measured, before the fix) | what landed | how it was proved |
|---|---|---|---|
| **S-1** | `resolve_carbon_price(CAISO, 2022)` = **$0.00/tCO2** against 33.03 / 35.23 / 28.06 in the tuned years — the NYISO-134 D-1 defect, CAISO edition. ~$11–12/MWh on a gas CC at ~0.41 t/MWh, and **merit-order distorting** (the CC-to-steam rate spread is ~2.9×), not a level shift. | `STATE_CARBON_PRICE_BY_ISO["CAISO"][2022] = 28.45` | Simple mean of the year's four CA-Québec joint-auction **current-vintage** settlement prices — the committed 2023–2025 recipe exactly. Feb $29.15 (30th), May $30.85 (31st, 2022-05-18), Aug $27.00 (32nd), Nov $26.80 (33rd); each attributed to **its own** CARB press release and **cross-checked against EDF Climate 411's independent commentary** before it was written. Four rows added to `data/raw/policy/carbon-auction-results/carbon-auction-results.csv`. |
| **S-2** | `IMPORT_TRANCHES_BY_YEAR["CAISO"]` has no 2022 → falls to the **static** ladder (1,566 / 1,805): a different firm block. | `2022: PNW_hydro_base 1,489 / DSW_solar_PV 1,682` | DMM **2022** Annual Report (2023-07-11) **Table 8.5** p. 234, `Imports` row = **3,171 MW**, × the published 2022 MIC north branch-group share 7,411/15,780 = 0.46965. **The construction was re-proved before 2022 was written and reproduces all three committed years TO THE MW** (1072/1251, 1558/1813, 1566/1805). |
| **S-3** | the three `CAISO_DSW_*_CLEAN_DEPTH_BY_YEAR` tables have no 2022 → fall to the pooled **static** depths (5,192 / 6,187 / 5,733). | `surplus 5,813 · overnight 6,309 · daytime 6,774` | The committed producers, run with a new **report-only** `--extra-years`; each producer's DEFAULT run reproduces its committed 2023–2025 values, its static and its published gates byte-for-byte. |
| **S-4** | `NUCLEAR_MONTHLY_CF_BY_YEAR["CAISO"]` and `nuclear-availability-CAISO.csv` have no 2022 → the static seasonal pattern + EFORD, losing Diablo Canyon's 2022 refuelling timing. | the 2022 monthly CF vector + **730** daily availability rows (365 d × 2 reactors) | `derive_nuclear_monthly_cf.py --isos CAISO --years 2022` (EIA-923 Page 1) then `derive_nuclear_availability.py --iso CAISO --years 2022` (`nrc-reactor-status/2022PowerStatus.txt`). |
| S-5 / S-6 | — | **no action** | Verified inert, not assumed: `caiso_ra_mustoffer_quantity_gate=False` and `caiso_dam_outages=False` on this keeper. |
| **H-1** | `_load_caiso_supply_consistent_demand(2022)` **raises** — the keeper runs `caiso_supply_consistent_demand=True` and the loader never falls back, so the rung could not solve at all. | `caiso_supply_consistent_demand_2022.csv`, **219.538 TWh** | §5 below. |

---

## §2 — S-4: the A-8 assertion, discharged

`derive_nuclear_monthly_cf.py --check` over 2022–2025 returns
**"committed table matches the EIA-923 derivation"** — i.e. the 2023/2024/2025
vectors re-derived byte-identically in the same run that produced 2022, so no
existing year's values moved. `derive_nuclear_availability.py --iso CAISO
--check` returned **"reproduces byte-for-byte"** on the committed extract
BEFORE the re-derive; after it, the 1,886 pre-existing rows are
**row-identical** and only 730 2022 rows are added. 2022 monthly availability
tracks the CF anchors to three decimals (Apr 0.541, Oct 0.730, Nov 0.579) —
Diablo Canyon's two units on alternating spring/fall refuelling cycles.

## §3 — S-3: why the gates did NOT move, and the one number that is out of range

`--extra-years` is **report-only by construction**: an extra year's depth is
measured on the identical construction but never enters the pooled static, the
year-stability CV or the LOYO gate, which stay computed over the committed
2023–2025 sample. That matters because those gates test whether the
CONSTRUCTION is stable across the tuned years; recomputing them over a 4-year
sample would silently re-adjudicate three already-committed rows. Measured:
every producer's default run is unchanged (overnight 5,870/6,205/6,487, CV
0.041; daytime 5,441/5,762/5,998 static 5,733, CV 0.040; surplus
5,312/4,792/5,472 static 5,192, CV 0.056, LOYO worst 12.5 %).

**A NEW PRODUCER LANDED: `scripts/data/derive_caiso_dsw_surplus_depth.py`.**
The south surplus depth was the one of the three with **no committed producer**
— the spec still calls it a "scratch derivation in FINDING-caiso86b", i.e. a
measured parameter no re-run could check. The new script transcribes the
construction documented in the spec and **reproduces the three committed values
to the MW** (5,311.600 / 4,791.900 / 5,472.500 vs 5,312 / 4,792 / 5,472), the
pooled static (5,192) and the published gates, before it emits any new year.

**REPORTED AT FULL MAGNITUDE:** 2022's **daytime** depth, 6,774 MW, sits ~13 %
**above** the 2023–2025 range (5,441–5,998) — the only one of the three that
falls outside. The mechanism is in the window: 2022 is a high-gas year, the
trigger floor is `HR_CCGT × SoCal citygate`, so a higher floor puts MORE hours
on the trigger-OFF side (3,398 of 5,840 measured daytime hours) and the p95 of
that wider, deeper population rises. That is the construction responding to a
changed condition exactly as rule 13 `[R-MEASURED]` requires of an admissible
input. It is **not** a reason to substitute the pooled static, which would
replace a measured year with a mean of three other years.

## §4 — S-2: two transcription traps, recorded so the next lane does not re-hit them

The DMM × MIC construction did not reproduce on the first attempt (every year
landed 3–5 MW low). Both causes are recorded because either would silently
corrupt a future year:

1. **The north branch-group set must include the 22 MW Westley group**, which
   the `_caiso188_import_tranche_census.py` probe's transcription of that set
   omits. (The probe carries an `unmatched_north_names` diagnostic for exactly
   this class of error; it is a frozen record probe and is **not** edited here,
   but its north set is short by this one group.)
2. **CAISO renamed that group `Westley-Los Banos` → `Westley-Fink` for delivery
   year 2025.** A name-keyed north set therefore drops it in 2025 alone, which
   is why 2025 was the last year to fall into line.

Also settled by evidence rather than judgment: **`Imports-MSS` is EXCLUDED.**
The DMM 2023 report's Table 8.4 `Imports` row is 2,323 MW — exactly the
committed 2023 level — while its `Imports-MSS` is 326 MW, so the committed
convention is the `Imports` row alone and 2022 follows it. Figure 8.2's
"about 2,900 MW" is a **different object** (bid-in MW in Aug/Sep peak hours, a
chart read) and is not used.

## §5 — H-1: the circularity, how it was broken, and what the numbers say

**The circle** (PRECOMMIT §5.1): the demand artifact needs
`bench/CAISO/2022.json.gz`; `regen_caiso_bench_cems.py` can only AMEND an
existing part; bench parts are written by the canonical builder from a SOLVED
bundle. **The break:** a bench scaffold solve — the frozen keeper recipe with
`--set caiso_supply_consistent_demand=false` and nothing else changed, via
`scripts/replay_keeper.py`, so no core-infrastructure edit was needed — then
the canonical builder (`render_calibration_html.build_payload` +
`backcast_artifacts.write_bench_part`) writing **only** the bench part.

**`regen_caiso_bench_cems.py` did NOT need extending, and was not extended.**
The handoff and caiso-259 §1 both expected it to. It turns out the RENDER is
now the primary writer of the CEMS-anchor fields: the freshly built 2022 part
came out with `gas_cems_grid 63.042 / gas_cogen_grid 6.796 / fossil_cems_grid
69.914` already populated and `classFull` already on the capped reconcile.
`regen_caiso_bench_cems.py` is a **retrofit** tool for parts built before those
fields existed; a new year does not need it. Its `_CEMS_GUARD` therefore needs
no 2022 entry either, and none was invented.

**The pre-registered guard, and the result.** `_ANNUAL_GUARD[2022]` is
**G-DEMAND-2022** (PRECOMMIT §5.2), fixed from the committed 2023–2025
artifacts **before** the 2022 derive ran: with
`wedge(y) = [930 NetGen − TI](y) − derived demand(y)` measuring
**+5.416 / +10.780 / +17.675 TWh**, the admissible 2022 wedge is
`[−1.5, max + 1.5] = [−1.500, +19.175]`, which against the 2022 930 identity of
218.809 TWh gives the window **(199.6, 220.3) TWh**.

**Derived 2022 demand = 219.538 TWh → wedge = −0.729 TWh. INSIDE the band, and
it CORROBORATES the caiso-80 diagnosis rather than merely passing.** Because
`wedge = NG_cell − (CEMS gas grid + cogen + foldin)`, the wedge measures
exactly the fabricated block the caiso-80 FINDING attributes to the EIA-930
`NG: NG` cell. Its onset is ~2024-05 and it grows: implied `NG_cell` −
measured block = **−0.7 (2022) → +5.4 (2023) → +10.8 (2024) → +17.7 (2025)**.
In the one year that PREDATES the corruption the two agree to under a TWh.
caiso-80 had only 2023–2025 and so could never see this; 2022 is an independent
corroboration of the construction, obtained without tuning anything to it.

**Three disclosures on this number.** (a) My own PRECOMMIT §5.2 predicted 2022
would "sit near 2023's +5.4"; it came in at −0.729 — the direction was right
(smaller than 2023) and the magnitude was not. (b) **−0.729 is only 0.77 TWh
above the band's lower bound**, so a tighter lower bound would have failed it;
the −1.5 was carried from the ±1.5 slack the committed years use, not chosen
for 2022. (c) 219.538 TWh is HIGHER than every training year
(207.5 / 212.2 / 204.8), which is expected — 2022 was the record-peak year
(DMM: 52,061 MW instantaneous peak) and carries three fewer years of BTM-PV
growth — but it is stated rather than assumed.

**A-7 DISCHARGED.** The derive takes no arguments and rewrites every year on
any invocation. After the run: `caiso_supply_consistent_demand_{2023,2024,2025}.csv`
are **sha256-identical** to their pre-run snapshot (`3642dd89…`, `0e3ad15a…`,
`64569f85…`), and `provenance.json` differs in **exactly one key path** —
`years["2022"]` added, every pre-existing year byte-equal, `construction`
unchanged.

## §6 — The solve-surface ledger this owed (capx D79)

Adding a year to a registry table moves that ISO's cache key, and
`solve_surface_declared.py` is **NOT** re-declared (re-declaring restores the
pre-change key and re-serves the pre-change bundle). What the change owes is
the cause block, and it is written: `PINNED_SURFACE_ROWS_BY_ISO["CAISO"]`
advances **`22e6fdb4a5a23589` → `f4057d6db19fe8d3`** (row count unchanged at
202 — both moves are ADDED KEYS in existing tables, not new tables), with a
dated cause block and two `LEDGERED_SURFACE_MOVES_BY_ISO["CAISO"]` entries.

**Rule 25 `[R-ISO-SCOPE]` holds by measurement:** `moved_rows` is `{}` for
MISO/PJM/NYISO/NEISO and names only ERCOT's own pre-existing entry for ERCOT;
CAISO alone moves. **Nothing committed changes**: a 2023–2025 solve reads only
its own year's row from each table and every one of those is unchanged, so a
re-solve reproduces the keeper bundle. `check_cache_key_registration.py` OK;
`tests/regression/test_persisted_identity.py` 24 passed. S-2 and S-3 live in
`model/interchange/spec.py`, which design §2.3 puts OUT of the phase-1 surface,
so they move no fingerprint — a known scope gap of D79 phase 1, not a defect
introduced here.

## §7 — G-BENCH: the guard is SCOPED, and here is exactly why

PRECOMMIT §5.1 declared G-BENCH as: the 2022 bench part rebuilt from the
rung's bundle must be **byte-identical** to the scaffold's. **That form cannot
hold, for a reason discovered after it was written and stated here BEFORE the
comparison runs.**

The bench year payload carries `avgLMP`, the measured actual LMP mean. The
scaffold's part was built while `actual_lmp_hourly_CAISO.parquet` still had no
2022 rows (the RTM crawl is what lands them), so it reads **`avgLMP: None`**;
the rung's part will be built after the crawl and will carry a number. That is
the intake landing between the two builds — not contamination by the
scaffold's demand input.

**The scoped guard, fixed now:**
* **G-BENCH-A (hard):** every field the demand derive actually consumes —
  `plants` (per-plant hourly CEMS, `c_ann`, `btm`, `group`), `e930`
  (`gas_cems_grid`, `gas_cogen_grid`, `fossil_cems_grid`) and `classFull` —
  must be **identical** between the scaffold's part and the rung's. These are
  the fields that could carry a demand-input dependence, and they are the whole
  basis of the H-1 artifact.
* **G-BENCH-B (hard):** a full part diff may differ in **`avgLMP` ONLY**. Any
  other differing key fails the guard.
* Failing either → re-derive the demand artifact from the rung's part and
  re-solve once; failing again → STOP and file a FINDING (PRECOMMIT STOP-5,
  unchanged).

This is a **weakening** of the guard as literally written, and it is recorded
as such. What it is not is a weakening of what the guard protects: G-BENCH-A
covers every field through which the scaffold could have influenced the
artifact chain, and G-BENCH-B refuses every difference except the single one
whose cause is named in advance.

## §7a — S-7: an EIGHTH silent fallback caiso-259 did not list, found and closed

`data/raw/iso-specific-transmission/CAISO_loss_surface.csv` carried year labels
**{0 (pooled), 2023, 2024, 2025}** and no 2022. The keeper runs
`caiso_zonal_loss_surface=True`, and `load_zone_month_deviation` resolves "the
year's own rows when the surface carries them, **else the pooled `year = 0`
rows**" — so a 2022 rung would have run the pooled forecast-mode fallback
surface while every training year rode its own measured one. That is exactly
the class caiso-259 §2 enumerates (S-1…S-6) and it is not on that list; it is
recorded here as **S-7**.

It needed no new data: the derive reads `CAISO_dam_hourly_<year>.csv`, and
**caiso-261 already landed the 2022 DAM aggregate** — so this was closable the
moment H-3 closed, and nobody noticed.

**The pooled rows are the trap, and they were protected.** `POOLED_YEAR = 0` is
computed over `YEARS`; adding 2022 to `YEARS` would have recomputed the
forecast-mode fallback surface over 2022–2025 — a change to a TRAINING-recipe
object. `--extra-years` therefore emits the extra year's own per-year rows and
leaves the pooled computation over `YEARS` alone, the same report-only
discipline as S-3.

Measured: the **DEFAULT run reproduces the committed 240-row file
sha256-identically** (`b883a359…` before and after), which is the strongest
available proof that the derive is frozen and this change is inert by default.
With `--extra-years 2022`: 60 rows added (5 zones × 12 months) and **every
pre-existing row — 2023, 2024, 2025 AND the pooled `year = 0` — unchanged**.
2022 carries **zero interpolated month-cells**, i.e. better DAM coverage than
2023 (12 interpolated cells each for LA_BASIN and SDGE, the Jan–Feb 2023 OASIS
retention gap), and its zone ordering matches 2024/2025 (ZP26 −0.0494 most
negative, then SP15_rest −0.0379, NP15 −0.0182, LA_BASIN −0.0134, SDGE
−0.0034).

## §8 — Test status, checked against a clean base rather than asserted

`tests/regression/test_persisted_identity.py` — the suite that directly guards
this change — **24 passed**. `scripts/check_cache_key_registration.py` OK (297
solve-surface names across 7 modules, all declared).

`tests/unit` reports **35 failed, 4978 passed** (7 distinct test ids). **Every
one of them reproduces on a clean base with these changes stashed**, so none is
introduced here:

| failing ids | cause | why it is not this session's |
|---|---|---|
| `test_cache_solve_surface::test_sidecar_is_written_beside_the_config`, `::test_a_bundle_solved_on_S1_is_not_addressed_on_S2` | the first asserts `stamp["moved"] == {}` for **ERCOT**, which has carried a ledgered `NUCLEAR_MONTHLY_CF_BY_YEAR` move since **ercot-253**; the second is a **MISO** key test | both are ERCOT/MISO; this change moves **CAISO only** (`moved_rows` measured `{}` for MISO/PJM/NYISO/NEISO). **Verified by stashing**: the file run alone on the clean base fails identically, 2 failed / 3 passed. |
| `test_d74_no_default_cap_convention` (parametrized) | `PublishedBarUnavailable: run scripts/data/curate_capacity_market_avoidable_cost_rate.py` | an ENVIRONMENT artifact — `data/clean` starts empty in a fresh session and only the two CAISO datatypes the handoff names were curated. PJM object, untouched here. |
| `test_export.py` × 4 | same missing-curation class | present on the clean base. |

One incidental finding, reported not fixed: the two `test_cache_solve_surface`
failures are **masked when that file runs alongside others** (the 3-file
baseline run passes them, the same file alone fails them), i.e. the file has an
order-dependent surface-cache leak. It is a pre-existing ERCOT/MISO test-hygiene
issue, out of this lane's scope, and it is named here so it is not rediscovered
as "caused by the CAISO 2022 intake".

## §9 — What did NOT happen

No `ScenarioConfig` field; no mechanism-matrix row (none is owed — no mechanism
was tested); no offer-curve band multiplier and no `authorized_price_tuning`
block; no import lever, floor, window or class re-pricing; no control solve
(G-CTRL form 4 stands); no keeper change; no registration; **no 2022 result of
any kind exists yet.** `regen_caiso_bench_cems.py`, `solve_surface_declared.py`
and every other ISO's tables are untouched.

**2019–2021 CARB prices remain ABSENT and are NAMED, not fixed:** those rungs
still resolve to $0/tCO2. They were not added because the auction-by-auction
attribution could not be completed from this environment to the standard S-1
met — the May-2021 (27th) price came back self-contradictory in search, and the
`carbon-auction-results` README's own rule is that no price or metadata is ever
inferred (PRECOMMIT STOP-4). That is a data-intake item for the lane that
spends the 2020/2021 touchpoints.
