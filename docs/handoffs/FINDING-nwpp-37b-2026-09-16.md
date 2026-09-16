# FINDING — NWPP-37: the EIA-930 fuel-column unit-slip screen now runs at the frames seam

Lane NWPP-37 · model Fable (`claude-fable-5-1`) · branch `claude/charming-cannon-q5hkxw` · base
`6d1a144d62949b53af088df51787de68d2edf738` (= `origin/main` at issuance; the desk's pin `02c08154`
is an ancestor). PRECOMMIT: `docs/handoffs/PRECOMMIT-nwpp-37-2026-09-16.md` (written before any
source edit; its §3 predictions are scored in §3 below). No solve, no shard, no ScenarioConfig
field, no matrix row, no shared record.

## 0. REPORT FIRST

1. **My enumeration against the desk's.** Nineteen direct `_eia_hourly_frame_filled` reads in
   `src/` — the desk's count exactly. **Seven fuel-column readers**, not "a dozen": six direct
   (`measured_monthly_hydro`, `_hydro_wat_month_hod` → hydro envelope + min-flow,
   `measured_gas_floor_profile`, `caiso_solar_fraction`, `_neighbor_load`, `caiso_hub_load_shape`)
   plus the **NWPP pool constructor itself** (`_pool_hourly_frame` sums RAW member columns). The
   desk's list missed `caiso_solar_fraction` and the pool sum; the desk's "several demand.py
   docstrings say the CF series are drawn from the same frame" resolves to **zero** fuel-column
   reads in `demand.py` — all eight are `Demand`-only (the docstrings describe the
   `actuals.load_eia_hourly_renewable_gen` path). Full table: PRECOMMIT §1 / §1 below.
2. **Shape taken: (A), structural.** The screen is now applied in `frames.py` — inside
   `_eia_hourly_frame_filled` and `_ercot_hourly_frame` for a single BA, and **per member** in
   `_pool_member_frames` before the pool sum — and the three per-reader applications in
   `actuals.py` are reduced to one (`load_eia_hourly_benchmark`, whose frame is its own parquet
   read). I agree with the desk's position, and the pool is the decisive reason: a pool-LEVEL
   screen catches only 2 of NWMT's 4 hydro hours in 2024 and 3 of the 6 in 2025 (a 65,891 MW
   member hour is 100× the member's 641 MW robust peak but only 3.4× the pooled 19,533 MW), so the
   repair has to live where the members are assembled, which is `frames`, not any reader.
3. **Series that moved outside the SPP-41 control set — named, at full magnitude (§3).**
   Reader-level: NWPP (14 outputs, the point of the lane) and **two rows in other regions**, both
   the screen repairing a column that is already repaired on that region's bench path and both
   reachable by NO registered caller: (i) SPP 2023, a `_neighbor_load(kind="net")` probe on SWPP —
   the control-set column `NG: WND` h3907, +3,589,445 MWh of phantom wind removed from a net-load
   driver no `NeighborInterface` instantiates on SWPP; (ii) SOCO 2025 `measured_gas_floor_profile`
   — `NG: NG` h1172/1240/2751/7527 at ~70 GW against a 26.6 GW p99.9, 116 bucket hours move by
   ≤ 457.5 MW, and the function's only caller is CAISO's RA gas floor. **Gate G1 as I pre-registered
   it ("every non-NWPP reader output byte-identical") is therefore TRIPPED on those two rows, and I
   say so rather than re-reading the gate.** Why I still take (A): the pre-registered fallback (B)
   would apply the identical screen at the identical two read sites and produce the identical two
   rows — (B) buys nothing against them, because they are not a property of WHERE the screen runs
   but of the screen running at all on a flagged column, which is the repair the charter asks for.
   The charter's own control clause ("anything beyond that set … must be shown to be a defect
   repair rather than a behaviour change") is the test they meet. The desk may overrule.
   Column-level beyond the control set: SOCO 2023/2024 `NG: OIL`, SOCO 2025 `NG: NG` (SOCO was
   registered a week after SPP-41's measurement; the bench path already repairs them) and the NWPP
   member slips. **ERCOT, CAISO, PJM, MISO, NEISO: zero flags in any year, zero moved outputs.**
4. **NWPP, the measured cost removed.** October 2025 pooled hydro repin target **8,243.5 →
   7,095.6 GWh (−1,148.0 GWh)** against NWPP-32's +1,166 (the difference is AVA's interpolated
   ~1 GW replacing the two slip hours rather than zero). 2024: Aug −67.7, Oct −65.5, Nov −5.6 GWh.
   Pooled `NG: WAT` peak 817,202 → 23,607 MW (2025), 76,472 → 19,981 MW (2024).
5. **One observation routed, not fixed:** SOCO 2024 `NG: OIL` h386–392 reads 530 → 801 → 350 MW,
   a ramp-up-and-down shape over seven consecutive hours against a p99.9 of 72 MW and a median of
   0 — that looks like a real oil-peaker run, not a unit slip, and the screen (unchanged by this
   lane, live on SOCO's bench path since SOCO-20) repairs it. No reader at the frames seam consumes
   SOCO `NG: OIL`, so this lane moves nothing there; the SOCO desk should look (§6).

## 1. Enumeration — every reader, classified at `6d1a144d`

PRECOMMIT §1 carries the 25-row table with line numbers; the classification stands unchanged
after the patch. Summary by class: **F** (fuel column, must be screened) — envelopes.py :109, :167,
:440, :1050; neighbor_price.py :396 (:407-408), :574 (:580-581); frames.py `_pool_hourly_frame`
(members). **T** (Demand / TI / NG total / clock only, outside the screen by ruling P9) —
envelopes.py :371, :1639, :1883; virtual_bids.py :274; zonal_shares.py :384; demand.py :229, :343,
:390, :526, :560, :600, :632, :679, :735; frames.py :295 (pool clock). **S** (screened at its own
read before this lane) — actuals.py :348/:351 (ERCOT wrapper, now deleted), :405/:412 (benchmark,
kept), :485/:488 (renewable profile, its call now removed as redundant).

Direct strict-frame (`_eia_hourly_frame`) readers outside `frames`: `actuals._ercot_hourly_frame`
(screened downstream), `scripts/data/build_calibration_reference._pool_hourly_benchmark` (screens per
member itself — the precedent this lane's pool construction follows; unchanged and now consistent
with the pool frame at every flagged hour), `scripts/data/derive_neiso_offer_surface._netload_pct`
(`Demand − NG: WND − NG: SUN`; ISNE flags nothing in any year, so a re-derive is byte-identical).

Script readers of `_eia_hourly_frame_filled` inherit the screened frame from now on (they are
out of scope and were not edited). Fuel-column consumers among them: `derive_caiso_offer_surface`,
`derive_pjm_offer_surface`, `derive_miso_offer_surface`, `derive_neighbor_convexity`,
`derive_caiso_solar_shape_band`, `derive_caiso_supply_consistent_demand`, `build_nwpp_hydro_budget`
(per-member `NG: WAT` — its committed artefact was built on the raw column; rule 23: it re-derives
when its source data changes, and this lane changed what the loader serves, so the NWPP hydro
desk should note that a re-run now sees repaired members), `scripts/lib/wind_shape` (SWPP 2023
`NG: WND` — the committed SPP wind shape was derived on the raw column; a re-derive moves h3907
only), and four `scripts/probes/`. For CAISO / PJM / MISO / NEISO derive scripts the input is
byte-identical (zero flags).

## 2. What was built

`src/market_sim/data/eia930/frames.py` (+141/−): `_screen_fuel_columns` (lazy import of the
`actuals` screen — `actuals` imports `frames` at load time and the factor is bound by import from
`demand`, the pattern this file already uses for `_screen_demand_dropouts`); `_screen_pool_member_frame`
(screen one member, bridge the flagged hours by the member's own interpolation at the flagged
positions ONLY, leaving `min_count=1` and not-yet-reporting storage semantics untouched);
`_eia_hourly_frame_filled` screens on both branches and skips a pool code (screened per member,
never twice); `_pool_member_frames` screens each member; `_ercot_hourly_frame` screens AFTER the
long-format fill; docstrings on the module, `_eia_hourly_frame` (RAW, not a seam),
`_eia_hourly_frame_filled` (THE seam), `_pool_member_frames`, `_pool_hourly_frame`, `_ercot_hourly_frame`.

`src/market_sim/data/eia930/actuals.py` (+/−118): `_ercot_hourly_frame_screened` deleted, the five
ERCOT readers call `_ercot_hourly_frame`; `load_eia_hourly_renewable_gen` drops its second
application; `load_eia_hourly_benchmark` keeps its own (its frame never comes from `frames` — it
serves a short PJM-2023 or partial H1-2026 year the frame loaders reject) and its docstring says
so; the module docstring and the screen's docstring now describe the seam that exists and the
nine-region measurement, replacing the claim that was true of `actuals` readers only.

`src/market_sim/data/eia930/envelopes.py` (docstrings / comments only, +26/−): rows 1, 2, 4, 5 say
their fuel column arrives screened and what a flagged hour does in each (single-BA NaN left out
of the month like an inserted gap row; NaN dropped from the percentile buckets; `fillna(0.0)`
zero share in the CAISO solar fraction — the existing missing-hour treatment).

`tests/unit/data/test_eia930_fuel_spike_screen.py` (+293/−): the one test that pinned the DEFECT
(`test_the_cached_frame_is_not_mutated` asserted the FILLED frame still carried the spike) is
rewritten to pin the true property — the strict raw cache is untouched, the seam hands out the
repaired frame. New: `TestScreenAtTheFramesSeam` (5: seam screened + strict raw; clean frame
returned uncopied; Demand / totals untouched at the seam; the reindexed short-year branch;
ERCOT after the long fill), `TestScreenOnTheEnvelopeReaders` (5: monthly hydro, hydro envelope +
min-flow with two same-bucket slips so the p95 is actually dragged unscreened, gas floor at p99,
the neighbour net-load driver, the CAISO solar fraction), `TestScreenOnThePoolMembers` (3: the
pooled hour equals 16 × member + the slip member's interpolation; the pool passes the seam
uncopied — not screened twice; no phantom monthly energy), `TestNwppLivePins` (2, `fulldata`:
pooled `NG: WAT` peak < 40 GW in 2024 and 2025; October 2025 = 7.0956 TWh). The synthetic frame's
`Demand` is now built from the CLEAN wind so a fuel slip is the only artefact.

Not touched: `demand.py`, `neighbor_price.py`, `virtual_bids.py`, `zonal_shares.py` (their reads
arrive screened by construction), any config, registry, verdict script, frontend, plan, ledger,
matrix file. No threshold, statistic or per-region branch changed; the test that pins
`_FUEL_SPIKE_RATIO is _DEMAND_SPIKE_THRESHOLD` is untouched and passes.

## 3. The nine-region before / after table (gate G1–G4), measured

Method: `measure_seam.py` run at the base sha (BEFORE) and on the patched tree (AFTER), identical
script — for every region × 2019–2026: every `NG:` column the seam hands out (sha256), the screen's
flags on it, and every fuel-column reader's output plus the `bench` / `renewable_gen` controls.
648 reader outputs compared; 72 region-years with a frame, 17 without.

| region | years with a frame | reader outputs compared | reader outputs moved | `NG:` columns moved at the seam |
|---|---:|---:|---:|---|
| ERCOT | 7 | 72 | **0** | none |
| CAISO | 7 | 80 | **0** | none |
| PJM | 7 | 72 | **0** | none |
| MISO | 7 | 72 | **0** | none |
| NEISO | 7 | 72 | **0** | none |
| NYISO | 7 | 72 | **0** | 2024 `NG: OTH` (h6759 — the control set; no seam reader consumes OTH) |
| SPP | 7 | 72 | **1** — `_neighbor_load(net)` probe, 2023, h3907 only, +3,589,445 MWh (the control column; no registered spec is a net neighbour on SWPP) | 2023 `NG: WND` (h3907 — the control set) |
| SOCO | 3 | 72 | **1** — `measured_gas_floor_profile` 2025 (p50 profile; 116 bucket hours, max 457.5 MW, Σ −19,759 MWh; no SOCO caller) | 2023 `NG: OIL` h7975; 2024 `NG: OIL` h386–392; 2025 `NG: NG` h1172/1240/2751/7527 — all already repaired on SOCO's bench path (registered 2026-09-14, after SPP-41's set was measured) |
| NWPP | 3 (2023–25) | 72 | **14** (below) | 2023 `NG: OTH`; 2024 `NG: COL/NG/OIL/OTH/WAT`; 2025 `NG: COL/NG/OTH/WAT` — per member: PGE OTH (2023); AVA OTH ×6, IPCO OIL (6 vs 2 MW), NWMT COL, NWMT WAT ×4, NEVP NG, NEVP OIL (3 vs 1 MW) (2024); AVA WAT ×2 + OTH, NWMT COL, NWMT WAT ×4, NEVP NG ×5 (2025) |

Controls (G2): every `bench` and `renewable_gen` digest identical before/after in all nine regions.
Class-T readers (`measured_interchange_envelope`, the neighbour driver on NWPP, every demand
loader): identical everywhere. G3: the moved-column set is exactly PRECOMMIT §3's table.

**NWPP movers, at full magnitude** (G4 — direction negative, −1,148.0 vs the pre-registered
−1,166 ± 5 %: PASS):

| output | year | before | after | Δ |
|---|---|---:|---:|---:|
| `measured_monthly_hydro` (the `eia930_monthly` repin target), October | 2025 | 8,243.5 GWh | **7,095.6 GWh** | **−1,148.0 GWh** |
| same, December | 2025 | 12,927.2 | 12,898.5 | −28.8 |
| same, annual | 2025 | 111.4407 TWh | 110.2639 TWh | −1.1768 |
| same, Aug / Oct / Nov | 2024 | 8,761.9 / 6,584.7 / 8,620.0 | 8,694.2 / 6,519.2 / 8,614.4 | −67.7 / −65.5 / −5.6 |
| same, annual | 2024 | 105.1763 TWh | 105.0374 TWh | −0.1389 |
| same, every month | 2023 | — | — | 0 (PGE OTH is the only 2023 flag) |
| pooled `NG: WAT` peak | 2024 / 2025 | 76,472 / 817,202 MW | 19,981 / 23,607 MW | the fleet's peak, not a telemetry hour |
| `measured_hydro_hourly_envelope` (p95 month×hod) | 2024 | max unchanged 19,785.5 | 92 hours move, ≤ 1,226.5 MW | bucket p95s that carried a slip |
| same | 2025 | max unchanged 22,702 | 186 hours move, ≤ 791 MW | |
| same, climatology fallback years 2019–2022, 2026 (pool 2023–25) | — | — | 247 hours move, ≤ 662.8 MW | |
| `measured_hydro_min_flow_level` (p5 by month) | 2025 | Dec 12,132.0 | Dec 12,057.6 | −74.5 MW, one month; 2024 and the fallbacks: 0 |
| `measured_gas_floor_profile` (NEVP `NG: NG` slips; no NWPP caller) | 2024 / 2025 | — | 30 h ≤ 390.5 MW / 91 h ≤ 25 MW | |

The screen is one-pass by construction, and one-pass is now guaranteed per series: re-screening
an already-screened SOCO 2024 `NG: OIL` would flag h385 (155 MW) because removing h386–392 lowers
the p99.9 anchor from 71.7 to 53.0 MW — which is exactly why a reader must never apply it a second
time on a seam frame, and why `_eia_hourly_frame_filled` returns a pool frame unscreened at pool
level. Measured, not asserted: the AFTER run's "what would the screen still flag on the seam's
frame" column is empty for every region-year except that one SOCO row.

## 4. Gates

| gate | result |
|---|---|
| G1 non-NWPP byte-identity | **TRIPPED on 2 of 576 non-NWPP reader outputs** (SPP 2023 net-load probe; SOCO 2025 gas floor) — both the screen repairing a column already repaired on the region's bench path, both without a registered caller, both identical under (B). Reported, not re-read. (A) taken; desk may overrule. |
| G2 controls | PASS — 0 `bench` / `renewable_gen` movers in nine regions |
| G3 column set | PASS — exactly the pre-registered table |
| G4 NWPP direction / magnitude | PASS — −1,148.0 GWh vs −1,166 ± 5 %; 0 class-T movers |
| G5 tests | PASS — screen file 27/27; targeted set (screen, pool frame, facade, neighbour price, calibration-reference screen, eia_loader) 141 passed; envelope-touching set (CAISO shape probe + intertie forward, NWPP zonal-shares curation, NWPP served-interchange trap, hydro, hydro envelope, transmission) 288 passed; fast lane over `tests/unit` + `tests/regression`: see §7 |
| G6 ruff | PASS — check + format clean on all four files |

## 5. Rules

13 `[R-MEASURED]` / 14 `[R-ACCURATE]`: a telemetry defect repaired by the same NaN + interpolation
a missing meter hour gets (single BA: the reader's own gap-fill; pool member: the member's own
interpolation before the sum); never a haircut, never a residual consulted — there is no NWPP
residual. 19 `[R-ONE-MECH]`: one mechanism, one application per series; the redundant `actuals`
applications are deleted, not stacked. 24 in spirit: the docstring now describes the seam that
exists; `_eia_hourly_frame` is labelled RAW so a direct import reads as what it is. 27 `[R-PUSH]`:
edited locally, pushed as on-disk bytes, fetch-back verified (§7). 28(c): no field, no row.
31/32/34: no solve, no shard, nothing to retain or archive.

## 6. Routed to NWPP-DESK / SOCO-DESK (not mine to touch)

1. **SOCO 2024 `NG: OIL` h386–392 may be a REAL peaker run** (530→801→350 MW ramp shape, seven
   consecutive hours) that the unchanged screen repairs on SOCO's bench path. Threshold and
   statistic are outside this lane; SOCO-desk should adjudicate on the ISO's own fuel-mix posting.
2. **`build_nwpp_hydro_budget.py` and `scripts/lib/wind_shape.py`** now read repaired members /
   the repaired SWPP column; their committed artefacts were derived on raw. A re-derive is a
   rule-23 data-change re-derivation and is the owning lane's call, not made here.
3. **NWPP-40's `eia930_monthly` posture**: NWPP-32 §3.2 refused the 2025 repin on two grounds; the
   first (the defective hours) is closed by this lane — October 2025 now reads 7,095.6 GWh. The
   second (the −2.7 TWh 930-vs-923 population mismatch, NWPP-32 §7 item 2) is untouched and
   still stands.
4. Two doc mentions of the deleted `actuals._ercot_hourly_frame_screened` remain in
   `FINDING-spp-41` and `PRECOMMIT-scn-ws5b-nyiso` (historical records; not edited).

## 7. Deliverables and verification

Commits on `claude/charming-cannon-q5hkxw`: (1) the seam + tests; (2) PRECOMMIT + this FINDING.
Every pushed source file ≥ 300 lines is fetched back and compared by line count and sha256 to the
local file after the push (rule 27). Fast-lane sweep result and the verification table are in the
final report.

## Log entry

*(appended verbatim to `docs/calibration-log/nwpp.md` by the NWPP ADDITION DESK — plan §8.0 rule 1;
this lane did not write it into that file.)*

## nwpp-37 — 2026-09-16 — EIA-930 fuel-column screen moved to the frames seam (zero-LP)

Lane NWPP-37, Fable claude-fable-5-1, branch claude/charming-cannon-q5hkxw, base 6d1a144d.
PRECOMMIT + FINDING `docs/handoffs/*-nwpp-37-2026-09-16.md`. No solve, no field, no matrix row.

THE DEFECT, VERIFIED: `_screen_fuel_spike_columns` was applied at three `actuals.py` call sites
only; `frames._eia_hourly_frame_filled` did no screening, so SEVEN fuel-column readers — the
hydro repin, the hydro envelope + min-flow, the gas floor, the CAISO solar share, both neighbour
net-load drivers, and the NWPP pool constructor summing RAW members — read unrepaired columns.
Enumerated 19 direct reads (the desk's count) + the pool; all eight demand.py reads are
Demand-only. SHAPE (A): the screen now runs in `frames` — `_eia_hourly_frame_filled`,
`_ercot_hourly_frame`, and PER MEMBER before the pool sum (a pool-level screen catches 2 of 4 /
3 of 6 NWMT hydro slips; per member catches all). One application per series; the redundant
`actuals` calls deleted; the benchmark loader keeps its own (its frame is its own parquet read).
NINE-REGION TABLE: ERCOT/CAISO/PJM/MISO/NEISO/NYISO 0 moved outputs; SPP 1 (a net-load probe on
the control column, no registered caller); SOCO 1 (gas floor on 2025 NG: NG slips already
repaired on its bench, no caller); NWPP 14 — October 2025 pooled hydro 8,243.5 → 7,095.6 GWh
(−1,148.0, the NWPP-32 §3.2 phantom), 2024 Aug/Oct −67.7/−65.5 GWh, pooled NG: WAT peak
817,202 → 23,607 MW. G1 as pre-registered TRIPPED on the two non-NWPP rows; reported, (A) kept
because (B) yields the same two rows. Routed: SOCO 2024 NG: OIL h386-392 looks like a real
peaker run the unchanged screen repairs (SOCO desk); NWPP hydro-budget / SPP wind-shape derives
now read repaired inputs (owning lanes). Tests +15 (27/27 in the screen file), ruff clean.
