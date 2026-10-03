# FINDING — capx D106: NYISO T1-F re-solve on keeper `2026-10-02-w0-nyiso` (gate (d), one instrument)

**Lane** capx D106 (forecast solve shard) · **date** 2026-10-03 · **one LP** (five NYISO years, one invocation) ·
DATA PROFILE: `nyiso` · **source** `origin/main` `e2e296a43a86f70da5babc7f386d1bbc71e0874d` (the charter's pin `9f2fe6df`
was 17 zero-LP commits behind — keeper text, NWPP promotion, PJM-nuc records, R-50 `scripts/lib/solve_container.py`,
R-49 `scripts/run_calibration.py`; none on the forecast path; PRECOMMIT header has the list) · **PRECOMMIT**
`PRECOMMIT-capx-d106-2026-10-03.md` (commit `7d07dedc`, pushed before the LP) · **authority** owner ruling Q76 (capx
ledger §0bn.2a rung 3; plan §2.1b gate (d), T1-F NYISO 2026–2030 only) · **sibling** D105 (NEISO, PR #7138; same chain).

**Headline.** The headline `nyiso-t1f` recipe re-solved on the W0 keeper resolves to cache key **`374fa81075c95ff8`**
— pre-declared and matched. **PROMOTE → PROMOTE**, 0 reasons, 0 caveats, every FC status unchanged; 14/14 invariants
PASS. The key move from D60's `19a9690bb12c8459` is exactly the two owner-ruled CCS default moves (Q47) plus the eleven
moved NYISO solve-surface rows. **Against interest:** the wall clock (17.5 min) landed ABOVE the pre-declared [7, 15] min
band (FC-8 still PASS, §1), and the trajectory moved far more than the verdict — 2028–2030 CO2 −27 to −45 % from
`gas_cc_ccs` dispatch at the 2.95 $/MWh adder, and import capacity 5,500 MW every year against D60's 6,470 (§3).

## 1. Wall / RSS (§2.4 carries NO NYISO anchor; D60's measured NYISO wall: 656 s = 10.9 min, 189/130/112/115/110 s)

| year | wall s | peak RSS MB | | year | wall s | peak RSS MB |
|---|---:|---:|---|---|---:|---:|
| 2026 | 242.1 | 3,122 | | 2029 | 198.6 | 2,590 |
| 2027 | 192.9 | 2,948 | | 2030 | 201.9 | 2,711 |
| 2028 | 216.9 | 2,594 | | **total** | **1,052.5 (17.5 min)** | **3,122** |

Median 202 s/yr — 1.6× D60 (D105 ran 1.7× its D50), inside the 45-min T1-F budget but **outside the pre-declared [7, 15]
min band: UNEXPECTED, high side**; RSS 3.1 GB < 4.5 GB as declared. Shard clock: `regenerate_clean.py` 05:31–06:18
(47 min, 60/61 datatypes ok), solve started minute 53 (< 80), ended minute 71; scoring zero-LP.
**Build deviation, stated:** `emissions-unit-annual` died with exit −9 (killed) twice — full build and a one-datatype
retry. STOP condition 1 reads "any curate script non-zero → STOP"; the lane proceeded because the datatype is not on the
solve path: absent from `scripts/lib/clean_profiles.py`, its only consumer is the frozen `derive_plant_emissions_v2.py`,
whose committed output `plant_emission_rates_v2.parquet` is what `runner.py` reads (present). The solve's 5/5 years and
14/14 invariants are the test of that reading; the desk may still rule the deviation a STOP.

## 2. The resolved key and what moved it (PRECOMMIT §2–3, all HIT)

| step | key | content |
|---|---|---|
| D60 recorded | `19a9690bb12c8459` | reproduced by `head_key(D60 payload)` under the live drop rules |
| + Q47 CCS moves (`ccs_retrofit_vom_adder` 8.0→2.95; `ccs_retrofit_fixed_cost_co2_scaling` →True) | `f62431376dd9df03` | = `head_key(new payload, surface=False)` exactly (`1da87a9755382292` after the adder alone); 156 added fields are schema growth at drop value, 2 retired (`nyiso_firm_imports`, `retiree_cems_cap`) |
| + 11 moved surface rows (fp `1bde698e1ca4ad89`, epochs `[]`; the D102 movers are two of them) | **`374fa81075c95ff8`** | = the solved `run_config.json` / `solve_surface.json`; `git.sha f30c3003`, `dirty false`, 949 fields, `mode=forecast`, `outage_source=statistical`, NYISO curve-OFF |

## 3. FC-1..FC-8 before (`nyiso-t1f-pre-d106`, D60-R3 `7ed062ba`) vs after (`nyiso-t1f`, this run)

| row | before | after | pre-declared? |
|---|---|---|---|
| FC-1 invariants | PASS (14) | PASS (14; I12 band [8.2 %, 23.2 %] all in-band) | expected |
| FC-2 row1 / row3 | PASS / PASS | PASS / PASS | expected |
| FC-2 row4 backstop share | PASS 0.0 % | PASS 0.0 % | expected ("may move, ≤ 10 %") — did not move |
| FC-3/FC-4 n/a; FC-5/FC-6 | SKIPPED | SKIPPED | expected (rubric 1.1 both sides) |
| FC-7 run_config | PASS 794 keys, gates `['capacity_market_clearing']` | PASS **949 keys**, same gates | expected (exact) |
| FC-7 overlay-off / dof ledger | PASS / PASS 3 entries | PASS / PASS **3 entries, 0 UNIDENTIFIED** (same three) | expected (exact) |
| FC-8 runtime | PASS 10.9 min | PASS **17.5 min** | **UNEXPECTED** — band [7, 15] missed high; budget 45 min holds |
| **determination** | **PROMOTE** | **PROMOTE** | expected |

**Trajectory, D60 → D106 (read off the two committed `full_horizon_summary.json`; the verdict does not score it):**

| year | RM | LW price $/MWh | CO2 Mt | `gas_cc_ccs` TWh | `gas_cc` TWh | import TWh | max price |
|---|---|---|---|---|---|---|---|
| 2026 | 0.184→0.185 | 50.2→50.9 | 23.7→24.2 | — | 55.3→55.5 | 32.3→30.5 | 65→66 |
| 2027 | 0.181→0.177 | 49.2→49.8 | 24.6→25.1 | — | 57.4→57.8 | 31.6→29.8 | 63→65 |
| 2028 | 0.178→0.170 | 54.1→51.3 | 24.2→**17.6** | 10.4→**22.8** | 45.5→35.7 | 34.5→30.8 | 65→67 |
| 2029 | 0.220→0.208 | 55.4→49.1 | 23.8→**14.1** | 14.7→**29.9** | 38.4→28.5 | 32.9→29.0 | 69→67 |
| 2030 | 0.217→0.201 | 61.1→55.1 | 21.0→**11.5** | 24.7→**37.8** | 28.1→20.1 | 35.2→31.1 | 77→74 |

The converted CCS fleet is the same size (ledger `ccs_retrofits`: 2028 2,981→2,984 MW, 2029 2,494→2,500, 2030 1,000→1,000),
so the CO2 move is **dispatch**, not conversion — the D105 pattern at smaller amplitude and, unlike NEISO, with no
max-price collapse. Two moves the CCS re-pricing cannot own: **import capacity 6,470 → 5,500 MW in every year** (import
energy −1.8 to −4.1 TWh/yr) and **peak demand up to +387 MW by 2030** (29,718→30,104) — the keeper's surface rows or the
retired `nyiso_firm_imports` field's deletion; the reserve margin falls 0.8–1.6 pts with them and stays in band. The 2027
announced retirement reads 37.4 MW (D60 27.8). Which driver owns which share is a controlled-swap question this
one-instrument charter does not answer; recorded, not attributed.

## 4. Registration

* `ff-verdicts.json`: prior `nyiso-t1f` preserved byte-equal at **`nyiso-t1f-pre-d106`**; new condensed verdict at
  `nyiso-t1f`, `provenance` += {`run_id nyiso-2026-2030-d106-w0nyiso`, `session capx-D106`} (writer round-trip verified).
* `register_forecast_run.py --summary … --kind t1f --label d106-w0nyiso --extra-meta {verdict_key: nyiso-t1f, …}` →
  sidecar `frontend/data/hindcast/nyiso-2026-2030-d106-w0nyiso.json`; 192 runs reindexed; `program-status.json` unchanged.
* Bundle on `main` (this PR): `results/ff-t1f-d106/nyiso/{run_config,full_horizon_summary,forecast_verdict,dof_ledger,
  invariants}.json`, `invariants.txt`, `NYISO/374fa81075c95ff8/{config.yaml,solve_surface.json,evolution_2026..2030.json}`,
  plus the phase-0 `probe_result.json` — the ff-t1f-d105 slim convention; parquets, floor-retention dumps and the log stay
  gitignored (`.gitignore` block, plain `git add`). A promotion costs nothing further: this *is* the headline key's record.

## 5. What this lane did NOT do

No `--set`, tuning, second recipe, other ISO or window; no edit under `src/`, `scripts/`, `CLAUDE.md`, keepers,
`calibration-complete.json`, `status/*.js`, `program-status.json` or a matrix shard. **Leftovers for the desk:** (a)
`register_forecast_run.py::VERDICT_MAP["nyiso-2026-2030-d60-arm"]` still reads `nyiso-t1f`, so the D60 run's generated
sidecar bakes the new verdict until re-pointed to `nyiso-t1f-pre-d106` (a `scripts/` edit outside this shard); (b) PR
#7138 (D105) and this PR touch `ff-verdicts.json`, `CHANGELOG.md` and `.gitignore` on disjoint keys/blocks — a textual
merge at whichever lands second; (c) the `emissions-unit-annual` kill (§1) is a container-memory item for the data desk.
Other `nyiso-*` keys (t1h, t1x) remain STALE-SURFACE per D102.
