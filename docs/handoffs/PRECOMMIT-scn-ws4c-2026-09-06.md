# PRECOMMIT — SCN-WS4c: the LOAD-HI probe battery, and the scoring of SCN-WS4b's six pre-declared readings

**Lane** SCN-WS4c · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-06 ·
**Branch** `claude/scn-ws4c-load-hi-probes-r92rzm` ·
**Pin** `origin/main` `fca3b656` (desk pin `3dcf1b22` + two merges) ·
**Charter** `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-4 item 4 /
§7 "WS-4" item 4 · **Campaign** `scn-ws4-probe` · **Data profile** `all`

Written and pushed **before the first solve** (rule 29 `[R-SCREEN]`). Nothing in it is
revised after a number exists; the misses are reported as misses.

---

## 0. What this lane is, in one paragraph

SCN-WS4b wrote down, before any `LOAD-HI` number existed, how each of the six ISOs' high
case is to be read — which mechanism meets the added load, which invariants already FAIL
at `mid`, what a reader may and may not conclude from that ISO's CO2 delta, the exact
delta-table line, and the expected direction of the import-attributed line
(`docs/handoffs/load-hi-adequacy-reading-2026-09-06.md` §5;
`FINDING-scn-ws4b-2026-09-06.md` §2). **This lane is the test of that document.** Every
one of the six readings is scored HIT / MISS / SPLIT with the number that decides it. A
reading that missed is this lane's most valuable output — it means the pre-declaration was
wrong about the mechanism, which is a structural finding. **WS-4b's document is not
revised, and a miss is never a reason to re-read the case.**

---

## 1. Preconditions — verified at this pin, not assumed

| precondition | verification |
|---|---|
| **SCN-WS0 in full** | six commits in `main`'s history: `a66ea7c8` (emissions grain + `import_co2_mt_reported` + `unserved_mwh`), `cf7170f4` (`build_matrix_frame` + `scripts/report_scenario_deltas.py`), `a248c8ac` (`collate_scenario_campaign.py`), `e6464bde` (REF base YAMLs + `configs/scenario_campaign_matrix.yaml` + `--set`), `c95f59de` (the `scenario` registration kind), `47ba0610` (the G-E4 rider) |
| **SCN-WS4a** | `DATACENTER_ZONE_SHARE` carries ERCOT (7 weather-zone-crosswalked shares, 52,306 MW basis) and MISO (LTLF North/Central/South 0.2347/0.5824/0.1829) at `config/constants.py:3087+` |
| **SCN-WS4b** | `LOAD-HI` / `LOAD-HI-ORGANIC` live keys in `configs/scenario_campaign_matrix.yaml`; `backstop_built_mw` / `_mwh` in `scripts/report_scenario_deltas.py` (`BACKSTOP_MW_COL`/`BACKSTOP_MWH_COL`, :86-87); `load-hi-adequacy-reading-2026-09-06.md` present |
| desk pin ancestry | `git merge-base --is-ancestor 3dcf1b22 HEAD` → YES |

**Container state, disclosed because it is a budget item.** This container started with no
Python environment (`pandas` absent — every `data/clean` datatype failed on import) and no
`data/clean`. `uv sync --no-dev` installed the 21 pinned runtime deps; the FF §2.4
prerequisite build (`scripts/regenerate_clean.py`, ≈55 min / 50 datatypes / ≈1.6 GB) is
running before the first solve. Both are one-time per container and are reported in the
FINDING's wall-clock table.

---

## 2. Phase 0 — the zero-LP screen, run BEFORE any arm was scheduled (rule 29 step 0)

Rule 29's step 0 says an arm with a computable pre-solve gate does not reach a solve until
that gate passes. Two gates were computable from the constants alone, and both were run at
this pin against the live resolvers (`resolve_datacenter_mw`, `resolve_demand_growth_rate`,
`add_datacenter_block`) — not against a transcription of them.

**(0a) The ORGANIC companion is degenerate in three ISOs, so three arms are never
scheduled.** WS-4b §3 claims `LOAD-HI == LOAD-HI-ORGANIC` byte-for-byte in the T1 window
for CAISO, PJM and NEISO. **Independently reproduced here** by evaluating
`resolve_datacenter_mw` on both configs for every year 2026–2030:

| ISO | `high` vs `mid` block, 2026–2030 | 2030 high / mid (MW) | ORGANIC arm |
|---|---|---|---|
| ERCOT | differ every year | 122,000 / 37,000 | **spent** |
| MISO | differ every year | 27,000 / 20,500 | **spent** |
| NYISO | differ every year | 8,333 / 2,500 | **spent** |
| CAISO | **identical every year** | 1,800 / 1,800 | not spent — `high := mid` anchors |
| PJM | **identical every year** | 30,000 / 30,000 | not spent — high diverges only at 2040 |
| NEISO | **identical every year** | 0 / 0 | not spent — `DATACENTER_ADDITIONS_MW["NEISO"] == {}` |

WS-4b's §3 is **confirmed at the constants**, so this lane spends 15 T0 arms, not 18.

**(0b) The relocate/tail regime and the 2026 shape, from the model's own arithmetic.**
`add_datacenter_block` relocates while `dc_E < E` and adds once `dc_E ≥ E`. Resolved block
(after the 0.85 load factor) and cumulative growth factor, 2026:

| ISO | REF block / growth-f | LOAD-HI block / growth-f | **2026 ΔE = f_hi/f_ref − 1** |
|---|---|---|---|
| ERCOT | 10.48 GW / 1.177 | 34.57 GW / 1.243 | **+5.61 %** |
| CAISO | 0.51 GW / 1.057 | 0.51 GW / 1.086 | **+2.74 %** |
| PJM | 5.10 GW / 1.073 | 5.10 GW / 1.124 | **+4.75 %** |
| MISO | 1.02 GW / 1.063 | 1.19 GW / 1.092 | **+2.73 %** |
| NYISO | 0.42 GW / 1.025 | 1.42 GW / 1.053 | **+2.73 %** |
| NEISO | 0.00 GW / 1.026 | 0.00 GW / 1.044 | **+1.75 %** |

Every ISO is in the **relocate** regime in 2026 (ERCOT `dc_E/E` = 0.525 < 1), so 2026
energy is set by the growth factor alone and the block moves only the *shape*. The ERCOT
tail regime is a 2030 event and is reached only by the T1-F leg.

---

## 3. The arms — named before the first solve

**Screen year: 2026.** It is the year the mechanism's own footprint is largest *in the
sense the charter asks for*: load is live in year one with no evolution history to
confound it, and it is the only year every one of the six ISOs is inside the §2.1b
5-solve-year cap for a T0. It is **not** chosen on any residual.

### 3.1 T0 battery — 15 arms, 2026 only, campaign `scn-ws4-probe`

| ISO | arms |
|---|---|
| ERCOT | REF · LOAD-HI · LOAD-HI-ORGANIC |
| MISO | REF · LOAD-HI · LOAD-HI-ORGANIC |
| NYISO | REF · LOAD-HI · LOAD-HI-ORGANIC |
| CAISO | REF · LOAD-HI |
| PJM | REF · LOAD-HI |
| NEISO | REF · LOAD-HI |

Construction, identical in every arm:
`scripts/run_full_horizon.py --iso <ISO> --start-year 2026 --end-year 2026 --out-dir
results/scn-ws4-probe/<iso>/<ARM>` plus, for the two cases,
`--set demand_growth_path=high --set datacenter_load_path={high|mid}`. The overrides are
exactly the `configs/scenario_campaign_matrix.yaml` `LOAD-HI` / `LOAD-HI-ORGANIC` keys;
this lane **consumes** that file and does not edit it.

### 3.2 T1-F legs — 4 arms, 2026–2030 (5 solve-years, inside §2.1b)

NEISO REF · NEISO LOAD-HI · ERCOT REF · ERCOT LOAD-HI, under
`results/scn-ws4-probe-t1f/<iso>/<ARM>`. The ERCOT LOAD-HI leg is the only arm that
reaches the tail regime, and its 2030 row is reported **separately and flagged**, never
folded into a trajectory a reader could take as an emissions response.

### 3.3 Control posture — no control solve, and no committed-bundle differencing

Rule 29(b) forbids a control solve. This lane does not need one and does not spend one:
**REF is solved at HEAD in every ISO, as a case of the campaign**, so every delta this
lane reports is a same-HEAD, same-container, same-config-builder difference. G-CTRL form 4
and the G-DRIFT audit are therefore **not invoked** — there is no committed bundle in any
delta.

The committed `ff-t1f-*` REF anchors WS-4b's reading quotes (ERCOT 189.17 Mt / CAISO 30.51
/ PJM 349.09 / MISO 352.99 / NYISO 23.74 / NEISO 16.31 Mt at 2026) were solved at earlier
HEADs. Where this lane's REF differs from them, that difference is **HEAD drift, disclosed
as such in the FINDING, and never used as a case delta or as a score against WS-4b**.

---

## 4. The STOP gate — structural, pre-registered, and it may only kill

Run on every arm. It asks whether the mechanism does what its own arithmetic says it does.
It is **never gated on a residual**, it **may kill an arm and may never promote one**, and
it contributes nothing to any determination.

| # | check | how it can fail |
|---|---|---|
| **S1** | **The CO2 delta is the fuel-mix shift at unchanged per-fuel rates.** `Δemissions_mt` reconciles with `Σ_fuel Δ(CO2_fuel)` from the by-fuel table to the table's grain, and each fuel's implied `ΔCO2_f / ΔGen_f` sits at that fuel's own emission rate | a CO2 delta not attributable to the generation it came from = an accounting defect, not a load response |
| **S2** | **CO2 rises, and the rise is bounded by the fossil-average rate on the added fossil-served MWh.** `0 < Δemissions_mt` and `ΔCO2 / Δ(fossil generation) ≈ r_fossil(REF)` within the spread the merit order can produce (CC ≈ 0.37 → CT ≈ 0.55–0.65 t/MWh) | a fall, or an implied rate outside the fleet's own rate range |
| **S3** | **The footprint is confined to the rows the added load can reach.** Non-zero deltas confined to thermal generation, imports, prices, slack, and (T1-F only) builds/retirements. Renewable *potential* (CF × capacity) is identical between arms in 2026 — load moves no VRE resource | a delta in a row load cannot touch (e.g. VRE potential in a T0) = a config leak between arms |
| **S4** | **Unserved energy and the import line are reported as numbers, every ISO, every arm** — including the `0.0`s, with the reason | a silently-absent line is the disclosure failure the column exists to prevent |
| **S5** | **No non-target load-bearing criterion flips PASS → FAIL** in a way the load case cannot explain. I3/I7/I12 moving under a load case is the *target*; a flip in an unrelated invariant is not | an unexplained invariant flip |
| **S6** | **`backstop_built_mw` = 0.0 exactly for ERCOT in both cases** — a non-zero is a configuration defect (the backstop cannot arm for an energy-only ISO) | non-zero |

---

## 5. Per-ISO pre-declaration — sign, order of magnitude, footprint

These are **my** falsifiable predictions, distinct from WS-4b's readings (§6), and they are
scored as misses where they miss. Order-of-magnitude CO2 bands are `ΔE(2026) × r`, with `r`
bracketed by the CC and CT rates the fleet actually carries; `ΔE` is §2's growth-factor
arithmetic on the committed REF 2026 energy.

| ISO | ΔE 2026 | Δpeak 2026 (WS-4b §2) | **ΔCO2 predicted** | price | footprint / the thing to watch |
|---|---|---|---|---|---|
| **ERCOT** | +5.6 % (≈ +30.6 TWh on 546) | **−9.0 GW** (84.7 vs 93.7) | **+8 to +21 Mt** on 189.17 (+4 to +11 %) | **↑ or ↓ — I predict the load-weighted price may NOT rise** | the one ISO whose peak *falls*: 34.6 GW of flat block replaces peaky organic energy. Flatter+bigger favours CC over CT, so I expect the implied marginal rate at the **low** end of the band and the scarcity hours to *fall*. `hours_ge_500` expected ≤ REF. `backstop_built` 0.0. Import line 0.0. |
| **CAISO** | +2.74 % (≈ +6.5 TWh on 237) | +1.4 GW | **+1.5 to +4 Mt** on 30.51 (+5 to +13 %) | ↑ | the block is immaterial (0.51 GW, unchanged between arms) — this is a **pure growth-scalar** case. Watch whether the response goes to in-ISO gas or across the WECC seam; the import line is the interesting number, not the CO2. |
| **PJM** | +4.75 % (≈ +41.5 TWh on 873) | +7.7 GW | **+16 to +33 Mt** on 349.09 (+5 to +9 %) | ↑ | the largest absolute CO2 delta of the six by construction. Block identical between arms → pure growth. T0 backstop response likely **0.0** (2026 is the year REF itself builds nothing thermal); the backstop story is a T1-F phenomenon and this T0 cannot see it. |
| **MISO** | +2.73 % (≈ +18.7 TWh on 686) | +3.5 GW | **+9 to +16 Mt** on 352.99 (+3 to +5 %) | ↑ | coal-heavy, so the implied rate should be the **highest** of the six (I expect ≥ 0.6 t/MWh). REF 2026 already carries 9 h ≥ $500 and a −4.1 % margin; watch `hours_ge_500` and whether slack appears. Import line predicted 0.0 (WS-4b (e)). |
| **NYISO** | +2.73 % (≈ +4.2 TWh on 154) | +0.2 GW (29.6 vs 29.4) | **+1.0 to +2.1 Mt** on 23.74 (+4 to +9 %) | ↑, weakly | the 2026 shape effect is nearly nil (+0.2 GW) — the flat-peak artefact WS-4b predicts is a **2029–2030** phenomenon and this T0 should NOT show it. `backstop_built` and `unserved` both predicted 0.0. Import line ↑. |
| **NEISO** | +1.75 % (≈ +2.05 TWh on 117) | +0.4 GW | **+0.4 to +0.9 Mt** on 16.31 (+3 to +6 %) | ↑ | no DC block at all — the growth scalar alone (2.2 vs 1.3 %/yr), the cleanest single-axis case in the battery. The HQ seam is ~5 TWh from its SIL at REF, so I expect the import line to take a **material share** of the increment in 2026 and to be the reading, exactly as WS-0's carbon T0 was. |

**Two predictions I expect to be wrong somewhere, recorded so the miss is scoreable:**

1. **"Price rises" is a charter expectation I am pre-declaring will MISS on ERCOT** (§5
   row 1). If ERCOT's 2026 load-weighted price falls while energy rises 5.6 %, that is the
   relocate rule flattening the shape, not a defect — and it means the charter's blanket
   "price rises" is a statement about energy, not about a case that also reshapes the hour.
2. **The T0 cannot see the backstop in most ISOs.** REF builds 0.0 MW of thermal in 2026 in
   all six committed anchors, so `backstop_built_mw` is likely 0.0 in the T0 for every
   ISO — which means WS-4b's readings (a) and (d) are largely **not testable at T0** and
   are properly tested only by the T1-F legs. I flag this now rather than discover it and
   call a not-yet-testable reading a HIT.

**The SCN-WS0 miss this lane is instructed to learn from.** WS-0's precommit predicted a
"low single-digit percent" CO2 delta and measured **16.6 %**, because it under-weighted how
thin NEISO's gas-to-import margin is. The lesson taken here is not "predict bigger" — it is
that a **seam** can absorb a whole case. My NEISO band above (+3 to +6 %) is deliberately
stated as an *in-ISO* band with the expectation that the seam takes a material share on
top; if the in-ISO number lands low because the import line took it, that is a HIT on the
mechanism and a MISS on nothing.

---

## 6. WS-4b's six readings, restated here BEFORE the answer exists

Restated verbatim in substance from `load-hi-adequacy-reading-2026-09-06.md` §5 and
`FINDING-scn-ws4b-2026-09-06.md` §2, so the scoring cannot drift after the numbers land.
Each is scored **HIT / MISS / SPLIT** with the deciding number. Legs marked *(T1-F)* are
not testable by a 2026 T0 and are scored only on the NEISO/ERCOT legs; a leg testable by
neither is scored **NOT TESTABLE HERE** and said so, never counted as a HIT.

| ISO | (a) mechanism | (b) invariant widening | (c) may / may not conclude | (d) delta-table line | (e) import line |
|---|---|---|---|---|---|
| **ERCOT** | scarcity-priced entry inside the ladder + 12 GW/yr cap, **or nothing** → VOLL slack; backstop OFF by design | {I12, I3} at `mid`; **not monotone** — 2026–2029 peak below REF ⇒ I12 improves (artefact), I3 ambiguous in sign; 2030 tail ⇒ I3 in hundreds of TWh, `hours_ge_500` ≈ 8,760 | may: 2026 in-ISO rise ≈ fossil-avg × added fossil MWh, CO2/served MWh. may not: a 2030 total; adequacy from the better I12 | `unserved_mwh` beside `emissions_mt`; `backstop_built` **= 0.0**; CO2/served MWh; `hours_ge_500` | **0.0 exactly**, both cases, every year |
| **CAISO** | backstop `gas_ct` ladder-capped + economic VRE/storage | {I12, I7} 2026–2028 widen; I7 misses ≤ ~5.5 GW; share > 52.6 %; I3 may re-appear 2029–30 | may: fossil response + administratively-built CT, and the CT's share. may not: DC share (zero); a deployment forecast | `backstop_built_mw`/`_mwh` + `unserved_mwh` | **up**, same sign as CO2; ≤ ~7–11 Mt ceiling, expect a fraction |
| **PJM** | the **cap-bound backstop ladder is the only responding channel** (43.9 % share) | {I12, I7} 2027–2030; requirement +7–25 GW vs a ladder bounded ≈ 22 GW cumulative ⇒ I7 misses in **tens of GW**, **I3 expected to APPEAR 2029–2030** | may: fossil + backstop CT; understated where I3 appears. may not: DC attribution in this window | `backstop_built_mw`/`_mwh` + `unserved_mwh` | **up, small** (REF ≤ 0.6 % of energy) |
| **MISO** | backstop + ladder + economic gas_cc/solar; D42 exits 11.1 GW | {I12, I7} 2026–2029; I7 +4–10 GW; **share crosses 30 % → FAIL**; I3 may re-appear | may: fossil + backstop CT; the **shape** share. may not: DC *energy* attribution | `backstop_built_mw`/`_mwh` + `unserved_mwh` | **0.0 both cases**; a non-zero is a rung activating |
| **NYISO** | backstop armed, **never fired**; economic entry | {} at `mid`; peak **flat-to-falling** ⇒ I7/I12 read *better* (artefact); possible I12 exit on the **high** side 2029–30 | may: in-ISO rise on existing gas + the import shift; the shape share. may not: DC energy attribution; adequacy from the better I12 | `backstop_built` **0.0** + `unserved_mwh` **0.0**, printed because non-zero is the finding | **up**, sign + |
| **NEISO** | backstop (50 MW at `mid`) + reliability-floor retention; **no DC block**, so `LOAD-HI == ORGANIC` | {} but **thin I7** (+810/+419/+334 MW 2027–29) ⇒ positions go negative ~2027–28, backstop **fires**, I7 holds by construction, share 1.2 % → the 10–30 % CAVEAT band; **no I3** | may: fossil + backstop CT **+ the import shift, which is the reading**. may not: a total without the import line | `backstop_built` + `unserved_mwh` + the import line **per tranche** | **up early (≤ ~5 TWh, ≤ ~2.1 Mt), then saturates** by 2029–30 |

---

## 7. The leakage line is a deliverable, not a caveat

For every ISO and every arm this lane reports `import_co2_mt_reported` **beside**
`emissions_mt` as a number, names the tranche that moves, and scores it against WS-4b's
(e) column. Where an ISO has no import node the reported value is `0.0` **with the reason
written out** — that is a result about a boundary the model cannot see, not an absence.

WS-0 measured the opposite-signed case: a $25/t carbon arm on NEISO cut in-ISO CO2 by
−2.71 Mt while raising the reported import line by +1.85 Mt on one NYISO rung, so roughly
two thirds of the headline reduction left the scored basis. Under a **load** case the line
moves the **same way** as the in-ISO delta, so the headline **understates** the total. That
carries a second-order consequence this lane will state per ISO: a `LOAD-HI` CO2 delta is
a *lower bound* on the modeled system's response, and the gap is the import increment.

---

## 8. Budget, and the rule-12 schedule

Measured FF §2.4 anchors: ERCOT ~2.4 min/solve-year, NEISO ~1.5, PJM ~5.6, MISO ~10–13,
CAISO ~8, NYISO ~4. Plan: **15 T0 solve-years + 20 T1-F solve-years = 35 solve-years**,
≈ 2 h of serial LP, plus the ≈ 55 min one-time `data/clean` build and the `uv sync`.

Rule 12 `[R-PARALLEL]`: years sequential inside every invocation, always. **≤ 2 concurrent
invocations, and exactly 1 whenever a per-plant multi-zone ISO (PJM, MISO, CAISO) is
running** — this is a 15 GB box and a per-plant multi-zone forecast year measures ≈ 8.6 GB,
so two cannot co-run (RC-1A-D1). RSS is checked before each launch. SCN-WS1b and SCN-WS2b
are solving in their own containers, which is free across containers and does not relax
this lane's own count. Solves run in-session; no CI runner (private repo, billed minutes).

Disk is the second constraint: 20 GB free at start. Each ISO's arms are solved, reported
through `report_scenario_deltas.py`, and their LP caches deleted before the next ISO
starts, so peak disk stays bounded. `results/scn-ws4-probe*/` commits the **slim** artifacts
only (each arm's `full_horizon_summary.json` + `run_config.json`, the matrix bundle, the
delta/rollup tables), following the committed `scn-ws0-smoke` convention exactly; the
nested per-ISO LP caches are gitignored as transient.

---

## 9. Rule compliance declared up front

- **Rule 29(c) DELETE BEFORE MERGE.** The 19 arms here are **registered forecast-namespace
  runs** under campaign `scn-ws4-probe`, not screens, so they are kept and registered
  normally. If any throwaway diagnostic bundle is produced along the way it is deleted from
  the tree before this PR merges, and every number it produced lives in this document or
  the FINDING.
- **Rule 29(b).** No control solves. §3.3 states why none is owed.
- **Rules 1 / 13.** No knob is moved. No default is flipped. No offer-curve multiplier is
  touched — the authorized price-tuning channel is a *backcast calibration* channel and has
  no application in a forecast scenario probe. Every FAIL that widens is **disclosed per
  case and left where it lives** (the capx director's queue).
- **Rule 22.** Every solve year is **2026–2030, forecast mode**. No backcast year, no
  holdout tier, no measured-actual scoring. `datacenter_load_path` is coerced `off` in
  backcast by construction, so nothing here can reach a calibrated year.
- **Rule 27 `[R-PUSH]`.** No file ≥300 lines in `src/` is written by this lane at all —
  its outputs are `results/`, docs, and two matrix cells. Any pushed file ≥300 lines is
  fetch-back verified.
- **File ownership.** `configs/scenario_campaign_matrix.yaml` and
  `scripts/report_scenario_deltas.py` are **consumed, never edited**; if a case needed
  changing this lane STOPS and routes to SCN-DESK. `config/constants.py`,
  `data/datacenter.py`, `policy/*`, `model/lp/*`, `config/scenarios.py`,
  `scripts/register_forecast_run.py`, `scripts/collate_scenario_campaign.py`,
  `frontend/data/forecast/program-status.json` and `frontend/data/backcast/*` are not
  touched. Matrix cells are the **last commit**, after `git fetch origin main` + rebase,
  one appended line per ISO.
- **No new GitHub Actions workflow. No default moves. No solve outside this document.**
