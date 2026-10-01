# FINDING — SCN-WS4b: the named high-load case, its adequacy reading, and the "backstop-built" column

**Lane** SCN-WS4b (relaunch **r2**: issued at SCN-DESK r#2, re-emitted at r#3, no branch at
r#4 → NEVER LAUNCHED, re-issued under a fresh stem) · **Model** Fable (`claude-fable-5-1`) ·
**Date** 2026-09-06 · **Branch** `claude/scn-ws4b-load-hi-adequacy-jvv96t` (the charter names
the stem `claude/scn-ws4b2-loadhi-adequacy-x3mc` and the desk's §5 rows name
`claude/scn-ws4b-loadhi-adequacy-b2np`; this session was provisioned on the branch above and
the harness binds pushes to it — noted so the ledger's §5 stem row can be reconciled, exactly
as SCN-WS4a recorded for its own stem) · **Base** `origin/main` `af6269cf` (desk pin
`21deb4a7` + PRs #4895 capx D65 and #4896 caiso-253, neither on an SCN region) ·
**Charter** plan §3 WS-4 items 1 and 3 / §7 "WS-4" · **Data profile** `all` (no `data/raw`
read was needed: every input is a constant, a committed summary or a committed ledger) ·
**Solves** none — no LP, no PRECOMMIT, by charter.

**Preconditions verified with `git log`:** SCN-WS0 on main in full — `cf7170f4` (2/6, the
report), `e6464bde` (4/6, the YAML), `e8c7072d` (5/6, the `scenario` kind), `79034547`
(6/6, the paired T0) — and SCN-WS4a `0fc2cc58`, all ancestors of `21deb4a7`.

---

## 0. Bottom line

All four deliverables land. The named cases were already live keys (SCN-WS0 left them
specified, uncommented) — what was missing was the disclosure, so the case comment is
**completed, not duplicated**: the ERCOT tail-regime arithmetic, the six-ISO reading and
the degeneracy of the ORGANIC companion are in the YAML. The "backstop-built" column is
in the report with 13 tests. The adjudication is
`docs/handoffs/load-hi-adequacy-reading-2026-09-06.md`; §2 below is the one table SCN-WS4c
scores against.

Three things the arithmetic surfaced that the charter did not anticipate, all zero-solve:

1. **ERCOT `LOAD-HI` is a discontinuity, not a widening.** The tail regime the charter asked
   to have disclosed arrives in **2030 only**: energy 800 → 1,800 TWh and peak 94 → 267 GW
   between consecutive solve years. Through 2029 the flat block is 52–95 % of energy and
   ERCOT's **peak is below REF** — the peak-based invariants will read *better* than `mid`,
   an artefact of the relocate rule, not adequacy.
2. **The DC companion is degenerate in PJM, CAISO and NEISO through 2030** (`LOAD-HI ==
   LOAD-HI-ORGANIC` byte-for-byte: high DC = mid DC in the window, high := mid, `{}`).
   SCN-WS4c saves three solves and gains no attribution there; in ERCOT/MISO/NYISO the
   difference is the block's shape effect at identical energy.
3. **Two live fail-set readings disagree for CAISO and MISO** — the board's `gate_reading`
   prose (2026-09-01) vs the bare `ff-verdicts.json` keys (re-scored 2026-09-03/05). Both
   are disclosed; the reading scores against the bare keys; the reconciliation is a records
   act on a file forbidden to every SCN lane (§5).

---

## 1. What landed

| # | file | what |
|---|---|---|
| 1 | `configs/scenario_campaign_matrix.yaml` | `LOAD-HI` / `LOAD-HI-ORGANIC` case comment completed: electrification as-is (= `off` in all six), the ERCOT tail-regime table, the three-ISO degeneracy, the six-line adequacy reading, the slack-understatement sentence. Keys unchanged; file re-parses. |
| 2 | `scripts/report_scenario_deltas.py` | the "backstop-built" column: `backstop_built_mw` (reserve-backstop `gas_ct` on the books in the year — ledger `thermal_additions` rows tagged `source == "reserve_backstop"`, cumulative, net of a later retirement) and `backstop_built_mwh` (those units' dispatch, matched on `unit_id`) in the headline frame, hence in the CSV with `_bau` / `_delta` and in the markdown table + notes. Derived from the ledger the report already reads and the dispatch it already loads; an optional `backstop_units=` argument on `collect_case_year_frames` (omitted ⇒ the pre-WS4b frame column-for-column). A ledger unit absent from the cached fleet is a report note, never a silent 0. |
| 3 | `tests/scoring/test_report_backstop_built.py` | 13 tests, trivial-first: the pure ledger walk on hand-built dicts (only `reserve_backstop` rows count; cumulative; a retirement nets out; the prior-ledger-year fallback), then a 24-hour three-unit REF/LOAD-HI fixture through the real cache + matrix bundle (500 → 800 MW on the books; 200 × 24 then 300 × 24 MWh; deltas equal levels; the CT energy sits inside `generation_twh`, never beside it; markdown carries the definition; the unmatched-unit note; the omitted-map identity). |
| 4 | `docs/handoffs/load-hi-adequacy-reading-2026-09-06.md` | the adjudication: definitions, the per-ISO load arithmetic, the attribution limits, the two fail-set readings, the six readings (a)–(e), what WS-4c does with it. |
| 5 | plan §5.1 Load-HI row 1 + §2.4 G-L3/G-L4 stamps; desk ledger §3 row 1 | the scorecard: **named case landed** (WS-4a's siting half + this lane's case half = row 1 `yes`). |

Tests: `tests/scoring/test_report_backstop_built.py` + `test_report_scenario_deltas.py` +
`test_report_ces_campaign.py` — **42 passed**; `ruff check` / `ruff format --check` clean on
the two Python files (HEAD's file was already formatted; the diff is confined to this lane's
hunks).

---

## 2. THE TABLE — six pre-declared readings SCN-WS4c scores against, unchanged

Columns are the charter's (a)–(e). "mid FAILs" are the bare `ff-verdicts.json` keys at this
pin; the `gate_reading` prose set is shown in brackets where it differs. Every expectation
is a sign or an order of magnitude; a miss is reported at full magnitude and is evidence
about the mechanism, never a reason to move a knob.

| ISO | (a) meets the added load with | (b) FAILs at `mid` → expected widening under `LOAD-HI` | (c) the CO2 delta may / may NOT say | (d) the delta table MUST carry | (e) import line expected |
|---|---|---|---|---|---|
| **ERCOT** | scarcity-priced economic entry (ladder + 12 GW/yr cap) **or nothing** — backstop OFF by design; residual → VOLL slack | {I12, I3} 2027–2030, one phenomenon (D4-I3). **Not monotone:** 2026–2029 peak 9–18 GW *below* REF → I12 improves/passes (artefact), I3 ambiguous in sign; **2030 tail regime** (E 1,800 TWh, peak 267 GW) → I3 in the hundreds of TWh, `hours_ge_500` ≈ 8,760, I12 FAIL. ORGANIC: both widen monotonically | MAY: 2026 T0 in-ISO rise ≈ fossil-avg rate × added fossil-served MWh; CO2 per **served** MWh. NOT: a 2030 total; adequacy from the better I12; "ERCOT meets high load"; DC emissions from the companion (shape through 2029, tail step in 2030) | `unserved_mwh` beside `emissions_mt` every year, 2030 flagged tail-regime; `backstop_built_*` printed, **expected 0.0** (non-zero = config defect); CO2/served MWh; `hours_ge_500` | **0.0 exactly**, both cases — no import node (DC ties ride in demand; `import_co2_tons` → 0.0) |
| **CAISO** | backstop `gas_ct` (REF 1,396/2,793/2,181/1,855 MW, 52.6 % share) ladder-capped + economic VRE/storage | {I12, I7} 2026–2028 [prose adds I3]. Peak +1.4 → +4.8 GW, E +2.7 → +8.5 %: I7 misses widen ≤ ~5.5 GW unless the ladder chases (~2 × 2.8 GW/yr); share > 52.6 %; I12 out through 2028; I3 may re-appear 2029–2030. ORGANIC = same solve | MAY: fossil response + administratively-built CT energy, and the CT's share (the column). NOT: DC share (zero by construction); a deployment forecast (HOLD) | `backstop_built_mw` / `_mwh` + `unserved_mwh` beside `emissions_mt` | **up**, same sign as CO2 (compounds, does not offset); ceiling ~20 TWh headroom under the 7,500 MW SIL on DSW_CCGT 0.37 / DSW_CT 0.55 → ≤ ~7–11 Mt; expect a fraction |
| **PJM** | the cap-bound backstop ladder (REF 734/1,469/2,937/3,874 MW = 2.0 × prior max each year, 43.9 % share) + economic gas_cc/VRE; D57 prices, adds no channel | {I12, I7} 2027–2030. Peak +7.7 → +27.8 GW, E +4.7 → +14.7 %: requirement +7–25 GW vs a ladder bounded ≈ 1.5/2.9/5.9/11.7 GW → I7 misses in the **tens of GW**, I12 further negative, share > 43.9 %, **I3 expected to APPEAR 2029–2030** (the one curve-ON "does not meet it"). ORGANIC = same solve | MAY: fossil response + backstop CT; understated by shed energy where I3 appears. NOT: DC attribution in this window (high diverges after 2030 → T2 → §2.1b); a deployment forecast | `backstop_built_mw` / `_mwh` + `unserved_mwh` beside `emissions_mt` | **up, small** (REF net −1.0 → +6.4 TWh, ≤ 0.6 %); exports fall (clamped out, no offset); bounded by the 10,500 MW SIL |
| **MISO** | backstop `gas_ct` (REF 0/0/2,049/4,049/3,416 MW, 23.0 % CAVEAT) + ladder + economic gas_cc/solar; D42 exits 11.1 GW | {I12, I7} 2026–2029 [prose: {I3}, stale]. Peak +3.5 → +8.7 GW, E +2.7 → +8.4 %, peak 3.6 GW under ORGANIC by 2030: I7 misses +4–10 GW, I12 further negative, **share crosses 30 % → FAIL**, I3 may re-appear 2029–2030. ORGANIC live | MAY: fossil response + backstop CT; the shape share (energy identical between arms). NOT: DC energy attribution; a deployment forecast | `backstop_built_mw` / `_mwh` + `unserved_mwh` beside `emissions_mt` | **0.0 both cases** (REF imports 0.00 TWh every year — injections are capacity-side); a non-zero is a rung activating, reported, sign + |
| **NYISO** | backstop armed, never fired (margins 18–22 % in [8, 23]); economic entry; D45 forecast-peak requirement | {} (14/14). E +2.8 → +8.6 % with peak **flat-to-falling** 29.6 → 29.0 GW (block 35 % of energy): I7/I12 read *better* (artefact); possible I12 exit on the **high** side (23 % cap) 2029–2030 — shape, not a build; no backstop, no slack. ORGANIC (peak 30.2 → 32.4): margin −8–10 pp to ~9–13 %, I7 holds, backstop 0 or a first small 2030 firing | MAY: in-ISO rise on existing gas + the import shift; the shape share. NOT: DC energy attribution; adequacy from the improved I12 | `backstop_built_*` (**expected 0.0**) + `unserved_mwh` (**expected 0.0**) beside `emissions_mt` — printed because non-zero is the finding | **up**, sign + (REF 32–35 TWh, 21 %); HQ_hydro rung (EF 0) near firm depth → increments on the 0.428-default fossil rungs |
| **NEISO** | backstop (REF 50 MW 2029, 1.2 %) + reliability-floor retention (699 MW) + economic gas_ct/VRE; no DC block → `LOAD-HI == ORGANIC`, the growth scalar alone | {} (14/14) but thin I7 positions (+810/+419/+334 MW 2027–2029). Peak +0.4 → +1.4 GW, E +1.8 → +5.5 %: positions go negative ~2027–2028 → backstop **fires**, I7 holds by construction, I12 in band, share 1.2 % → the 10–30 % CAVEAT band; no I3 | MAY: fossil + backstop CT **+ the import shift, which is the reading** (WS-0: 24 % import share, one rung moved 4.3 TWh). NOT: a total without the import line; DC anything | `backstop_built_mw` / `_mwh` + `unserved_mwh` + the import line **per tranche** beside `emissions_mt` | **up early, then saturates**: the HQ seam is 1–5 TWh from its 3,850 MW SIL at REF (28.5 → 33.0 of 33.7 TWh) → ≤ ~5 TWh, ≤ ~2.1 Mt at 0.428, on `NYISO_CT_peak` / `NB_north` first, flat by 2029–2030 |

**Read-across for every row.** A CO2 number under binding slack is understated by the shed
energy; under high load the import line has the *same* sign as the in-ISO delta, so the
headline understates the total by the import increment too. `emissions_mt` is read with
`unserved_mwh` and `import_co2_mt_reported` beside it, never as a total. The I7/I12/I3
FAILs already on the board at `mid` are disclosed per case, not fixed and not proposed for
fixing.

---

## 3. The ERCOT tail-regime arithmetic, as disclosed in the case comment

Constants at this commit: DC `high` 122 GW by 2030 (linear from 0 at 2024) × 0.85 LF;
growth `high` 11.5 %/yr near-era from the 2024 weather base; `E0` ≈ 464 TWh and `P0` ≈
84.9 GW inverted from the committed REF trajectory `results/ff-t1f-d50/ercot` (the same
arithmetic reproduces the committed REF peaks to the decimal, which is the check).

| year | block GW | `dc_E/E` | E TWh (REF) | peak GW (REF) | regime |
|---|---|---|---|---|---|
| 2026 | 34.6 | 0.525 | 577 (546) | 84.7 (93.7) | relocate |
| 2027 | 51.9 | 0.706 | 643 (593) | 86.5 (99.0) | relocate |
| 2028 | 69.1 | 0.844 | 717 (643) | 89.6 (105.1) | relocate |
| 2029 | 86.4 | 0.947 | 800 (698) | 94.2 (111.9) | relocate |
| 2030 | 103.7 | 1.019 | **1,800** (757) | **266.9** (119.6) | **TAIL** |

`LOAD-HI-ORGANIC` stays in the relocate regime through 2030 (`dc_E/E` 0.16–0.31; peak 99 →
144 GW, E 577 → 892 TWh). NYISO flattens too (block 35 % of energy by 2030, `LOAD-HI` peak
29.0 vs ORGANIC 32.4 GW); MISO partly (24 %; 143.4 vs 147.0 GW); CAISO/PJM/NEISO carry no
shape effect. Full per-ISO tables: the reading doc §2.

---

## 4. Duties and byte-identity

- **No `ScenarioConfig` field added, no mechanism tested** — rule 28 duties (b) and (c) do
  not fire, and no shard is stamped. One cell is arguably *owed by WS-4c, not by this
  lane*: the `datacenter_load_block` row's ERCOT cell could carry an evidence note that
  the `high` path enters the tail regime in 2030 — a construction property of
  `add_datacenter_block` at a block size the mid path never reaches. It is a note on a
  mechanism WS-4c will exercise, so it belongs with WS-4c's stamp after the probe.
- **No default moved; no solve; no CI workflow; no file outside this lane's regions.**
  `config/constants.py` and `data/datacenter.py` were read, not written. `results/*`,
  `program-status.json`, `calibration-complete.json` were read only.
- **Byte-identity.** The report change is additive (an optional argument; the omitted-map
  identity is tested); no cached artifact, cache key, LP row or scored number moves. Every
  backcast keeper and every forecast run is byte-identical.
- **Rule 27.** `scripts/report_scenario_deltas.py` (970 lines) is edited in place and pushed
  as the exact on-disk bytes; fetch-back verification against local line count + hash is
  recorded in the push step.

---

## 5. Routed to SCN-DESK (not executed — outside this lane's regions)

1. **`program-status.json` `gate_reading` is stale for CAISO and MISO** against the bare
   `ff-verdicts.json` keys the board's own per-ISO blocks cite: the prose reads CAISO
   {I12, I3, I7} · MISO {I3}, the bare keys read CAISO {I12, I7} (D46, 2026-09-03) · MISO
   {I12, I7} (D60, 2026-09-05). A records act for the capx board owner (D60-R2 / D58);
   forbidden to every SCN lane. The reading scores against the bare keys and discloses both.
2. **`LOAD-HI-ORGANIC` is redundant on PJM, CAISO and NEISO in the T1 window** — WS-4c's
   charter ("six T0 probes REF vs LOAD-HI", then the NEISO + ERCOT T1-F) should spend the
   ORGANIC arm on ERCOT, MISO and NYISO only. Three solves saved, no information lost.
3. **The ERCOT `LOAD-HI` 2030 year is a tail-regime year by construction.** WS-4c's ERCOT
   T1-F leg should report 2030 separately from 2026–2029; it is not a widening and its CO2
   is not an emissions response. Whether the `high` DC anchor (122 GW, the *total credible*
   large-load queue at 0.77 in-service) is the level the owner wants for the campaign is a
   **card D-2 question** the arithmetic makes concrete: at that anchor the case doubles
   ERCOT's energy in one year.
4. **NEISO's `electrification_path`.** The charter's "or `mid` for NEISO where the layer is
   sourced" does not obtain as-is: REF is the ScenarioConfig default `off` and no
   `iso_configs` override arms the layer. Arming it is a REF-posture (plan §3.0) question
   for the desk / owner, never a case override; recorded, not decided.
5. **Plan §3.5's "so the DC block's share of the emissions delta is readable"** is true
   only as a *shape* share in ERCOT/MISO/NYISO (energy identical between the arms by the
   relocate construction) and not at all in the other three through 2030. The §3.5 wording
   is the desk's to amend; this FINDING and the reading doc §3 carry the precise statement.
6. **Branch stem reconciliation** (header): the desk's §5 rows name
   `claude/scn-ws4b-loadhi-adequacy-b2np`, the r2 charter `claude/scn-ws4b2-loadhi-adequacy-x3mc`,
   the session was provisioned on `claude/scn-ws4b-load-hi-adequacy-jvv96t`.

---

## 6. Artifacts

- `configs/scenario_campaign_matrix.yaml` — the case comment (keys unchanged).
- `scripts/report_scenario_deltas.py` — the column; `tests/scoring/test_report_backstop_built.py`.
- `docs/handoffs/load-hi-adequacy-reading-2026-09-06.md` — the adjudication.
- `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §5.1 Load-HI row 1 (+ the
  §2.4 G-L3 / G-L4 stamps); `docs/handoffs/scenario-desk-ledger-2026-09.md` §3 row 1.
- No registered run, no bundle, no dashboard entry — this lane has no solve.

**This landing is the LAST thing blocking SCN-WS4c.**
