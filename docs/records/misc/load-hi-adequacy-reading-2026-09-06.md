# LOAD-HI adequacy reading — the pre-declared per-ISO adjudication (SCN-WS4b)

**Lane** SCN-WS4b (relaunch r2) · **Model** Fable (`claude-fable-5-1`) · **Date** 2026-09-06 ·
**Charter** `docs/handoffs/forecast-scenario-readiness-plan-2026-09.md` §3 WS-4 items 1 and 3 /
§7 "WS-4" · **Pin** `origin/main` `af6269cf` (desk pin `21deb4a7` + two merges, neither on
the SCN track) · **Solves** none — this lane has no LP by charter. Every number below is
either a constant at this commit, a committed REF trajectory, or arithmetic on the two.

**What this is.** Plan §3 WS-4 item 3 verbatim: *"Adequacy posture under high load — a
`[FABLE]` adjudication, no tuning. Pre-declare how each ISO's high case is read."* It is
written before any `LOAD-HI` number exists and it is not revised to fit one; SCN-WS4c runs
the probes against it. It fixes no invariant and proposes no fix — I7/I12/I3 belong to the
capx director's queue — it says what a `LOAD-HI` number *means* given what already fails.

**What this is not.** Not a screen gate, not a PRECOMMIT, not a residual target. Nothing in
it asks whether a number "looks right"; every expectation is a sign or an order of
magnitude that follows from the mechanism's own arithmetic, so a miss is evidence about
the system, never a reason to move a knob.

---

## 0. Bottom line

1. **The case is declared** (item 1): `LOAD-HI` = `demand_growth_path: high` +
   `datacenter_load_path: high`, `LOAD-HI-ORGANIC` = growth `high` + DC `mid`,
   `electrification_path` as-is — and as-is is `off` in all six ISOs, because REF is the
   ScenarioConfig default and no `iso_configs` override arms the layer (NEISO included).
2. **The ERCOT tail regime is a 2030 event, and it is a discontinuity.** Under `LOAD-HI`
   ERCOT stays in the relocate regime through 2029 with the flat block at 52–95 % of
   energy — so its **peak falls below REF** in every one of those years while energy rises
   6–15 % — and flips to the additive tail regime in 2030, where energy jumps from
   800 TWh to 1,800 TWh and peak from 94 GW to 267 GW in a single year (§2). The 2030
   `LOAD-HI` year is an unserved-energy year by construction; its CO2 delta is not an
   emissions response. `LOAD-HI-ORGANIC` is the smooth ERCOT high case.
3. **The attribution companion is degenerate in three ISOs through 2030** (§3): PJM's high
   DC curve equals mid until 2030, CAISO ships high := mid, NEISO's block is 0 MW. There
   `LOAD-HI == LOAD-HI-ORGANIC` byte-for-byte in the T1 window. SCN-WS4c should not spend
   the ORGANIC arm on them; the DC share of the delta is readable in ERCOT, MISO and NYISO
   only, and in ERCOT and NYISO it is dominated by the block's *shape* effect.
4. **Per ISO, the reading is one line each** (§5, and the scoring table in
   `FINDING-scn-ws4b-2026-09-06.md`): curve-ON ISOs meet the added load through the
   backstop and the entry ladder and report `backstop_built_mw` / `backstop_built_mwh`
   beside CO2; ERCOT meets it with scarcity-priced entry or does not meet it and reports
   `unserved_mwh` beside CO2; every ISO reports the import line beside CO2, expected
   **positive** under high load (the opposite role from the carbon arm: it *compounds*
   the in-ISO increase rather than eroding a reduction).
5. **The live FC-1 fail sets differ between the board's `gate_reading` prose and the bare
   `ff-verdicts.json` keys** for CAISO and MISO (§4). Both are disclosed; the reading is
   scored against the bare keys, which are the later re-scores. This is a records item for
   the capx board owner and is routed, not edited.

---

## 1. Definitions the reading uses

| term | meaning at this commit | where |
|---|---|---|
| backstop | the reserve-margin adequacy build: after the economic screen, if accredited firm < requirement, `gas_ct` is added to close the gap, rate-limited by the entry ladder; **ON iff the ISO has a capacity market** (PJM/MISO/NYISO/NEISO/CAISO), **OFF for energy-only ERCOT by market design** | `capacity_evolution/adequacy.py::resolve_reserve_margin_build_enabled`, `apply_reserve_margin_build` |
| entry ladder | `entry_rate_limits` (default ON): each tech's annual build ≤ 2.0 × its prior maximum annual build (ReEDS growth bound), seeded from EIA-860; the static per-tech queue caps and the ISO budget bind on top | `config/scenarios.py:5091`, `entry_config.ENTRY_GROWTH_LIMIT_MULTIPLE` |
| scarcity-priced entry (ERCOT) | the economic entry screen with the reserve value leg (`screen_reserve_value_enabled`) and the ERCOT-armed `entry_margin_exhaustion` + `entry_forward_reserve_leg` (owner ruling Q15); no requirement, no force-build | `iso_configs._ercot_config` overrides |
| I3 | unserved/dump: load-slack energy > 0.01 % of demand energy in a year, or dump > 2 % of VRE potential | `check_forecast_invariants.check_i3_unserved_dump` |
| I7 | reliability floor: capacity-market ISOs — accredited firm ≥ the model's own requirement (absolute); ERCOT — evolution must not over-retire below a retirement-bounded nameplate floor | `check_i7_reliability_floor` |
| I12 | reserve-margin band: per-year margin within [floor, floor + 15 pp]; floor = requirement-implied for curve-ON ISOs, the 13.75 % scalar for ERCOT; FAIL on ≥ 3 consecutive out-of-band years | `check_i12_reserve_margin` |
| FC-2 row 4 | backstop share of additions = cumulative `reserve_backstop` MW ÷ (thermal + renewable + storage additions); PASS ≤ 10 %, CAVEAT 10–30 %, FAIL > 30 % | `forecast_verdict._score_fc2_backstop` |
| `backstop_built_mw` / `_mwh` | this lane's column: reserve-backstop `gas_ct` on the books in the year (ledger rows, net of retirement) and its dispatched energy (matched on `unit_id`) | `scripts/report_scenario_deltas.py` |
| `unserved_mwh` | the slack column's annual energy, already in the headline frame (SCN-WS0) | `results/export._summarize_year` |
| import line | `import_co2_mt_reported` — reported-only, never inside `emissions_mt`; 0.0 by construction where the ISO has no import node (ERCOT) | `results/emissions.import_co2_tons` |
| relocate / tail regime | the DC block is relocated (energy-invariant, flat) while `dc_E < E`, added on top once `dc_E ≥ E` | `data/datacenter.py::add_datacenter_block` |

**The one sentence that binds every row below.** A CO2 number read under binding slack is
understated by the shed energy, and a CO2 number read without the import line beside it is
understated (under high load) by the import increment. `emissions_mt` is read with
`unserved_mwh` and `import_co2_mt_reported` beside it, and never as a total.

---

## 2. The load arithmetic, per ISO and case (zero-solve)

Method: `E0` and `P0` (the 2024 weather-year energy and peaky peak) are inverted from each
ISO's committed bare-key REF trajectory (2026 row: relocate regime, energy invariant, so
`E0 = E_2026 / f_mid(2026)` and `P0 = (peak_2026 − block) / ((1 − r) f_mid)`); every other
number is `resolve_demand_growth_rate` × `resolve_datacenter_mw` × `datacenter_load_factor`
(0.85) through `add_datacenter_block`'s two regimes. The method reproduces the committed REF
trajectories to the decimal (ERCOT 2027 peak 99.0 vs 98.98 GW committed; PJM 2030 172.8 vs
172.7 GW), which is the check that it is the model's arithmetic and not an estimate.
Script: the scratch `loadhi_arith.py` this lane ran; inputs named per row. REF sources:
`results/ff-t1f-d50/{ercot,neiso}`, `ff-t1f-d45r/pjm`, `ff-t1f-d60/{miso,nyiso}`,
`ff-t1f-d46/caiso` — the runs the bare `ff-verdicts.json` keys score.

### 2.1 ERCOT (`E0` ≈ 464 TWh, `P0` ≈ 84.9 GW; growth mid 8.5 % / high 11.5 %; DC mid 37 GW / high 122 GW by 2030)

| year | REF E / peak | LOAD-HI-ORGANIC E / peak | LOAD-HI block · dc_E/E · E / peak · regime |
|---|---|---|---|
| 2026 | 546 TWh / 93.7 GW | 577 / 99.3 | 34.6 GW · 0.525 · **577 / 84.7** · relocate |
| 2027 | 593 / 99.0 | 643 / 108.3 | 51.9 · 0.706 · **643 / 86.5** · relocate |
| 2028 | 643 / 105.1 | 717 / 118.6 | 69.1 · 0.844 · **717 / 89.6** · relocate |
| 2029 | 698 / 111.9 | 800 / 130.6 | 86.4 · 0.947 · **800 / 94.2** · relocate |
| 2030 | 757 / 119.6 | 892 / 144.2 | 103.7 · 1.019 · **1,800 / 266.9** · **TAIL** |

Two construction facts, neither of them adequacy:

- **2026–2029: the peak falls below REF while energy rises.** The flat block is 52 → 95 % of
  energy, so the peaky organic component is scaled to 47 → 5 % of itself and the load shape
  is nearly flat. Every peak-based adequacy reading — the I12 margin, the I7 firm-vs-peak
  position, `reserve_margin` in the ledger — will **read better than REF**. That is the
  relocate rule at a block size it was never exercised at (the mid path of every ISO sits at
  `dc_E/E ≤ 0.36`), not adequacy, and it is not to be quoted as such.
- **2030: the tail regime, in one step.** `dc_E ≥ E` for the first time, the block is added
  on top, and energy goes 800 → 1,800 TWh, peak 94 → 267 GW between consecutive solve years.
  One-pass evolution (rule 10) against a 12 GW/yr ERCOT queue cap cannot meet it; the
  residual leaves through the VOLL-priced slack column (`adequacy.py` design-intent block,
  D4-I3). **The 2030 `LOAD-HI` CO2 delta is not an emissions response** — it is the fossil
  fleet at full output plus hundreds of TWh of slack.

`LOAD-HI-ORGANIC` never leaves the relocate regime (`dc_E/E` 0.16–0.31) and is the smooth
ERCOT high case: peak 99 → 144 GW, energy 577 → 892 TWh, both monotone above REF.

### 2.2 The other five (2026 → 2030)

| ISO | REF E / peak | LOAD-HI-ORGANIC E / peak | LOAD-HI E / peak | LOAD-HI `dc_E/E` 2030 | DC axis |
|---|---|---|---|---|---|
| CAISO | 237→265 TWh / 49.8→54.8 GW | 244→287 / 51.2→59.6 | **identical** | 0.047 | high := mid (limitation G-D4-2) |
| PJM | 873→1,006 / 161.0→172.8 | 914→1,154 / 168.7→200.6 | **identical** | 0.194 | high = mid through 2030 (30 GW anchors) |
| MISO | 686→775 / 128.5→134.7 | 705→840 / 132.1→147.0 | 705→840 / **132.0→143.4** | 0.239 | live: 27 vs 20.5 GW by 2030 |
| NYISO | 154→162 / 29.4→29.7 | 159→176 / 30.2→32.4 | 159→176 / **29.6→29.0** | 0.353 | live: 10 vs 3 GW by 2031 |
| NEISO | 117→123 / 24.9→26.2 | 119→130 / 25.3→27.6 | **identical** | 0.000 | `{}` (0 MW) |

Read-outs: NYISO's `LOAD-HI` peak is *flat-to-falling* (the block reaches 35 % of energy),
MISO's is 3.6 GW below its ORGANIC twin by 2030 (24 %); CAISO, PJM and NEISO carry no shape
effect. All five stay in the relocate regime in every year.

---

## 3. What the two cases can and cannot attribute

`LOAD-HI − LOAD-HI-ORGANIC` is the DC block's contribution only where the two DC curves
differ in the window:

| ISO | `LOAD-HI − LOAD-HI-ORGANIC` in 2026–2030 | what the difference is |
|---|---|---|
| ERCOT | large, sign-changing | 2026–2029: the block's **shape** effect (energy identical, peak 15–36 GW lower); 2030: the tail-regime step (+908 TWh) |
| MISO | +0.2 → +5.5 GW flat block; energy identical | shape effect (peak −0.1 → −3.6 GW) — energy invariant, so the CO2 difference is the flattening's effect on the merit order, not "DC emissions" |
| NYISO | +1.0 → +5.0 GW flat block; energy identical | shape effect (peak −0.6 → −3.4 GW); same reading |
| CAISO / PJM / NEISO | **exactly zero** | not a finding — the constants coincide in the window; the ORGANIC arm is redundant here and should not be solved |

So in this window the companion answers *"what does the DC block's flatness do to dispatch
and adequacy at fixed energy"*, and it does so only in ERCOT/MISO/NYISO. It does **not**
answer *"how much CO2 is the DC load responsible for"* anywhere — the block's energy is
inside the grown total by construction (relocate), except in the ERCOT 2030 tail year,
where it is all of the increment and the year is unserved. Plan §3.5's line "so the DC
block's share of the emissions delta is readable" is therefore true only as a shape
share in three ISOs; the record should say so rather than let WS-4c discover it.

---

## 4. The live FC-1 fail sets at `mid` — two readings, both disclosed

The charter names `program-status.json` `gate_reading` as the source of the live fail sets.
That paragraph (lane D19, 2026-09-01) reads: **ERCOT {I12, I3} · CAISO {I12, I3, I7} · PJM
{I7, I12} · MISO {I3} · NEISO {} · NYISO {}**. The bare `ff-verdicts.json` keys — the
records the board's own per-ISO blocks cite as later re-scores — read, at this pin:

| ISO | bare key run (scored) | FC-1 fail set | detail on the bare key | FC-2 row 4 backstop share |
|---|---|---|---|---|
| ERCOT | `ercot-2026-2030-d50-ccscapex` (2026-09-04) | **{I12, I3}** | I12 out 2027–2030: 8.9 / 3.0 / −2.5 / −7.1 % vs [13.8, 28.7]; I3 slack 0.08 / 0.14 / 0.59 / 2.34 % of load (2030: 2,467 h, 17,685 GWh); row 6 `hours_ge_500` 4,039 h/yr | 0.0 % (channel off) |
| CAISO | `caiso-2026-2030-d46-remeasure` (2026-09-03) | **{I12, I7}** | I12 out 2026–2028: 10.4 / 7.7 / 10.2 % vs [15, 30]; I7 2026–2028 misses 2,276 / 3,735 / 2,493 MW | **52.6 % FAIL** |
| PJM | `pjm-2026-2030-d45r-remeasure` (2026-09-04) | **{I12, I7}** | I12 2027–2030: −11.2 / −13.5 / −13.1 / −13.0 % vs [−9.7, 5.3]; I7 2027–2030 misses 250 / 6,226 / 5,800 / 5,647 MW | **43.9 % FAIL** |
| MISO | `miso-2026-2030-d60-arm` (2026-09-05) | **{I12, I7}** | I12 2026–2029: −4.1 / −4.6 / −4.8 / 0.7 % vs [0.7, 15.7]; I7 2026–2029 misses 6,175 / 6,853 / 7,304 / 76 MW; I3 PASS | 23.0 % CAVEAT |
| NYISO | `nyiso-2026-2030-d60-arm` (2026-09-05) | **{}** | all 14 PASS; PROMOTE-WITH-CAVEATS (FC-7 only) | 0.0 % PASS |
| NEISO | `neiso-2026-2030-d50-ccscapex` (2026-09-04) | **{}** | all 14 PASS; PROMOTE, caveats [] | 1.2 % PASS |

The two readings differ for **CAISO** (I3 has left the set on the D46 re-measure) and
**MISO** (I3 → {I12, I7} on the D45R/D60 basis, where the base-year firm moved 140.3 →
118.1 GW). The reading below is scored against the **bare keys**; the prose is disclosed
because the charter names it. Reconciling the prose is the capx board owner's records act
(`program-status.json` is forbidden to every SCN lane) — routed in the FINDING §5.

**Marker state read live, not from any doc's summary.** `calibration-complete.json`
`complete` = {ERCOT, NEISO, PJM}; NYISO sits in `withdrawn` (2026-09-05, Q5 uniform rule on
the nyiso-192 promotion) even though `2026-09-06-nyiso-196-extract-basis` promoted a
CALIBRATED keeper on 2026-09-06 — its `complete` marker has **not** been re-declared, so
NYISO's §2.1b leg (a) still reads FAIL, exactly as the charter warned. None of this changes
the adequacy reading (a T0/T1-F needs no gate leg); it is recorded so WS-4c's registration
prose does not overstate NYISO.

---

## 5. The reading, per ISO

Each ISO answers the charter's five questions. (a) which mechanism meets the added load;
(b) which invariants already FAIL at `mid` and what widening looks like; (c) what a reader
may and may not conclude from the CO2 delta; (d) the exact line the delta table must
carry; (e) what the import line is expected to do. The expectations are falsifiable signs
and orders of magnitude; a miss is reported, not tuned away.

### 5.1 ERCOT — energy-only, no backstop

- **(a)** Scarcity-priced economic entry inside the ladder and the 12 GW/yr queue cap, **or
  nothing**: there is no requirement to build to, so what the screen declines is not built
  and the residual is VOLL-priced slack. This is the market design, not an omission
  (`resolve_reserve_margin_build_enabled` design-intent block; D4-I3).
- **(b)** At `mid`: I12 (2027–2030) and I3 (2027–2030) FAIL, and D4-I3 established they are
  *one* phenomenon (every arm that clears I3 over-builds out of the I12 band). Widening
  under `LOAD-HI` is **not monotone**: in 2026–2029 the peak is 9–18 GW *below* REF (§2.1),
  so I12 is expected to **improve or pass** — an artefact — while the year's minimum load
  rises by the block, so I3 is **ambiguous in sign** (fewer peak-hour breaches, more
  energy-constrained hours; the D4-I3 monotonicity in total build is the thing to watch).
  In 2030 both FAIL by construction and I3 is expected in the hundreds of TWh, `hours_ge_500`
  near 8,760. Under `LOAD-HI-ORGANIC` both widen monotonically: margin falls faster than
  REF's 14.8 → −7.1 %, slack rises every year from 2027.
- **(c)** May conclude: the 2026 T0 in-ISO CO2 rise, ≈ fossil-average rate × the added
  fossil-served MWh (relocate regime, energy +5.6 %); CO2 per **served** MWh; the direction
  of the fleet response. May **not** conclude: a 2030 total (understated by the shed
  energy); any adequacy claim from a better I12 in 2026–2029; that "ERCOT meets high
  load"; that `LOAD-HI − LOAD-HI-ORGANIC` is the DC block's emissions (it is the block's
  shape effect through 2029 and the tail step in 2030).
- **(d)** `unserved_mwh` beside `emissions_mt`, every year, with 2030 flagged as the
  tail-regime year; `backstop_built_mw` / `_mwh` printed and expected **0.0** (a non-zero
  is a configuration defect — the backstop cannot be on for ERCOT under `None`); CO2 per
  served MWh; `hours_ge_500`.
- **(e)** `import_co2_mt_reported` = **0.0 exactly**, both cases, every year: ERCOT has no
  import node (its DC-tie interchange rides in the demand series; `import_co2_tons` returns
  0.0 by construction). Not a leakage-free result — a boundary the model cannot see.

### 5.2 CAISO — curve-ON; backstop firing at 52.6 % share

- **(a)** The backstop `gas_ct` sized to the requirement gap, ladder-capped (2.0 × prior
  max — the REF already builds 1,396 / 2,793 / 2,181 / 1,855 MW in 2027–2030), plus
  economic entry (solar/wind/storage). The measured-seam import half of
  `capacity_deliverability_limits` is a backcast keeper flag and is not in REF.
- **(b)** At `mid`: I12 (2026–2028) and I7 (2026–2028) on the bare key; the prose adds I3.
  `LOAD-HI` raises peak +1.4 → +4.8 GW and energy +2.7 → +8.5 %; the requirement rises
  ≈ 1.15 × Δpeak, so I7 misses widen by up to ~5.5 GW unless the ladder absorbs (it can
  chase ~2 × 2.8 GW/yr), the backstop share rises above 52.6 %, I12 stays out of band
  through 2028, and I3 may re-appear in 2029–2030 if the ladder binds. `LOAD-HI-ORGANIC`
  is the same solve (§3).
- **(c)** May conclude: the CO2 delta is the fossil response *plus* administratively-built
  CT energy, and how much of it the backstop is (the column). May not: the DC share
  (zero by construction in this window); a deployment forecast (the HOLD stands — the
  delta is between two runs that share the defect, plan §4).
- **(d)** `backstop_built_mw` / `backstop_built_mwh` beside `emissions_mt`, plus
  `unserved_mwh` (I3 is in the prose set).
- **(e)** `WECC_import` node; REF imports 42–46 TWh (17 % of energy). Expected **up**,
  same sign as the CO2 delta — the headline understates the total increase by the import
  increment. Ceiling: the 7,500 MW simultaneous cap is 65.7 TWh/yr, ~20 TWh of headroom
  at REF 2030; the marginal rungs are DSW_CCGT 0.37 / DSW_CT 0.55 t/MWh, so ≤ ~7–11 Mt if
  the whole headroom were used; the expectation is a fraction of that.

### 5.3 PJM — curve-ON; the cap-bound ladder is the only responding channel

- **(a)** The backstop `gas_ct` ladder — at `mid` it built 734 / 1,469 / 2,937 / 3,874 MW,
  each year exactly the 2.0 × prior-max budget (S-6 / D45R) — plus economic gas_cc, solar
  and wind; the D57 clearing half prices the capacity market but does not add a build
  channel. The dated-exit channel removes 5.5 GW in the window.
- **(b)** At `mid`: I12 (2027–2030) and I7 (2027–2030). `LOAD-HI` raises peak +7.7 →
  +27.8 GW (168.7 → 200.6 GW vs REF 161.0 → 172.8) and energy +4.7 → +14.7 %; the
  requirement rises ≈ FPR × Δpeak, i.e. by ~7–25 GW, while the ladder can at most double
  each year (bounded ≈ 1.5 / 2.9 / 5.9 / 11.7 GW in 2027–2030 if it doubled from the REF
  2027 base every year, ~22 GW cumulative). So I7 misses widen to **tens of GW**, I12 goes
  further negative, the backstop share rises above 43.9 %, and **I3 — absent at `mid` — is
  expected to appear in 2029–2030** as the gap outruns what the ladder can build. This is
  the one curve-ON ISO where the charter's "does not meet it" reading can arrive despite
  the backstop, because the backstop is rate-limited. `LOAD-HI-ORGANIC` is the same solve
  (§3).
- **(c)** May conclude: the CO2 delta is fossil response plus backstop CT; where I3
  appears the number is understated by the shed energy. May not: DC attribution in this
  window (zero by construction; PJM's high curve diverges only after 2030, which needs a
  T2 window and therefore a §2.1b grant); a deployment forecast.
- **(d)** `backstop_built_mw` / `_mwh` and `unserved_mwh` beside `emissions_mt`.
- **(e)** `PJM_external` node armed; REF net interchange runs −1.0 → +6.4 TWh (≤ 0.6 % of
  energy). Expected **up and small**: exports fall (clamped out of the line, so no
  offset) and imports rise on the seam rungs; bounded by the 10,500 MW simultaneous
  import limit.

### 5.4 MISO — curve-ON; backstop at 23.0 % share

- **(a)** The backstop `gas_ct` (0 / 0 / 2,049 / 4,049 / 3,416 MW at `mid`) plus economic
  gas_cc and solar; `entry_rate_limits` (the ISO the ladder was first armed for) and the
  D53 sector gate on the screen; the D42 dates channel executes 11.1 GW of exits.
- **(b)** At `mid`: I12 (2026–2029) and I7 (2026–2029) on the bare key; the prose says I3
  (the S-123-V basis, superseded by D45R/D60). `LOAD-HI` raises peak +3.5 → +8.7 GW and
  energy +2.7 → +8.4 %, with the flattening holding the peak 3.6 GW under ORGANIC by 2030.
  I7 misses widen by ~4–10 GW, I12 goes further negative, the backstop share is expected
  to **cross 30 % (CAVEAT → FAIL)**, and I3 may re-appear in 2029–2030 as it did on the
  S-123-V record when the trigger lagged. The ORGANIC companion is live here.
- **(c)** May conclude: fossil response plus backstop CT; the shape share of the DC block
  (§3). May not: DC energy attribution (energy is identical between the two arms); a
  deployment forecast.
- **(d)** `backstop_built_mw` / `_mwh` and `unserved_mwh` beside `emissions_mt`.
- **(e)** `MISO_external` node exists but REF imports are **0.00 TWh in every year** (the
  firm-import injections are capacity-side). Expected **0.0 in both cases**; a non-zero
  value under `LOAD-HI` is a seam rung activating and is reported as such, sign +.

### 5.5 NYISO — curve-ON; backstop armed, never fired at `mid`

- **(a)** The backstop is armed and its trigger has never fired (margins 18–22 % against a
  [8, 23] band); economic entry (gas_cc 1,000 MW in 2029 at REF); the forecast-peak
  requirement vintage factors (D45) set the bar.
- **(b)** At `mid`: none — 14/14 PASS. `LOAD-HI` raises energy +2.8 → +8.6 % while the
  peak is **flat-to-falling** (29.6 / 29.4 / 29.2 / 29.1 / 29.0 GW vs REF 29.4 → 29.7) because
  the high block (10 GW by 2031, 7.1 GW flat at 2030) is 35 % of energy. So I7/I12 read
  **better than REF** — the same artefact as ERCOT — with one new failure mode: the
  margin may leave the band on the **high** side (the 23 % cap) in 2029–2030, an
  over-procurement WARN/FAIL produced by the shape, not by a build. No backstop and no
  slack expected. `LOAD-HI-ORGANIC` (peak 30.2 → 32.4 GW) lowers the margin by ~8–10 pp to
  ~9–13 %, still above the requirement-implied floor: I7 expected to hold, backstop
  expected 0 or a first small firing in 2030.
- **(c)** May conclude: the in-ISO CO2 rise on existing gas plus the import shift; the
  shape share. May not: DC energy attribution; that the improved I12 under `LOAD-HI` is
  adequacy.
- **(d)** `backstop_built_mw` / `_mwh` (expected 0.0) and `unserved_mwh` (expected 0.0)
  beside `emissions_mt` — printed, because a non-zero is the finding.
- **(e)** `NYISO_external` plus the firm HQ block; REF imports 32–35 TWh (21 %). Expected
  **up**, sign +: the HQ_hydro rung (EF 0) is near its firm depth, so increments land on the
  fossil-priced neighbour rungs at the 0.428 disclosure default.

### 5.6 NEISO — curve-ON; backstop at 1.2 %, floor retention live

- **(a)** The backstop (50 MW in 2029 at `mid`) and the reliability floor's retention
  (699 MW of 2027 gas-CC exits under the ARA-3 requirement), plus economic gas_ct (1,000 MW
  in 2030) and VRE entry. No DC block (`{}`), so `LOAD-HI == LOAD-HI-ORGANIC`, and the case
  is the growth scalar alone (2.2 vs 1.3 %/yr).
- **(b)** At `mid`: none — 14/14 PASS, but I7 positions are thin (+810 / +419 / +334 MW in
  2027–2029). `LOAD-HI` raises peak +0.4 → +1.4 GW and energy +1.8 → +5.5 %; the
  requirement rises ≈ 1.029 × Δpeak, so the thin positions go negative from ~2027–2028
  and the backstop **fires** for the difference: I7 holds by construction (the backstop
  satisfies it), I12 stays in band, and the backstop share climbs from 1.2 % into the
  10–30 % CAVEAT band. No I3 expected.
- **(c)** May conclude: fossil response plus backstop CT **plus the import shift**, which
  for NEISO is the reading — WS-0 measured a 24 % import share and a seam that moved
  4.3 TWh on one rung under a $9/MWh gas adder. May not: a total without the import line;
  DC anything (there is none).
- **(d)** `backstop_built_mw` / `_mwh`, `unserved_mwh`, and the import line **per tranche**
  beside `emissions_mt`.
- **(e)** `HQ_import` node. At REF the seam is already within 1–5 TWh of its 3,850 MW
  simultaneous limit (33.7 TWh/yr): 28.5 TWh in 2026, 33.0 in 2030. Expected: the import
  line rises **early** — ≤ ~5 TWh, ≤ ~2.1 Mt at the 0.428 default, on `NYISO_CT_peak` /
  `NB_north` first — then **saturates** by 2029–2030, after which the in-ISO gas carries the
  increment and the in-ISO CO2 delta grows faster. Sign +, magnitude bounded by the seam.

---

## 6. What SCN-WS4c does with this

1. Solve `REF` vs `LOAD-HI` as the six T0s (2026); spend `LOAD-HI-ORGANIC` on **ERCOT, MISO
   and NYISO only** (§3); the NEISO + ERCOT T1-F 2026–2030 legs per the charter, with the
   ERCOT 2030 year reported as the tail-regime year, separately.
2. Run `scripts/report_scenario_deltas.py` on each matrix; the headline CSV now carries
   `backstop_built_mw` / `backstop_built_mwh` beside `unserved_mwh` and the import line.
3. Score the FINDING's table row by row: each expectation is a sign or a band; report
   every miss at full magnitude and record it as evidence about the mechanism.
4. Do not move a knob. Any FAIL that widens is disclosed per case and left where it lives.
