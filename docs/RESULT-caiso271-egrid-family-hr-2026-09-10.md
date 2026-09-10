# RESULT — caiso-271: eGRID family heat rates measured on all four CAISO years; every gate passes; the rubric does not move

**Session caiso-271, 2026-09-10. CAISO only (rule 25 `[R-ISO-SCOPE]`).**
Arm: **`ScenarioConfig.egrid_family_heat_rates`**, default off, ONE flag on the committed keeper recipe via
`--replay-bundle`. Solved as four per-year shards (rule 32 `[R-SHARD]`, the parent ran **zero LP**), all
pinned to `9ee5319bcd48a025aa3cd126283c895fcc72fa65`.
Charter: `docs/PRECOMMIT-caiso271-egrid-family-hr-2026-09-10.md`.
**KEEPER UNCHANGED at `2026-09-10-caiso-269-lateevening-clean`. NOT PROMOTED — the owner's call (§7).**

---

## §1 — The result in six lines

1. **ALL FOUR PRE-REGISTERED STOP GATES PASS, on all four years.** G-IDENT, G-FOOT, G-DIR, G-NOFLIP; and
   G-CTRL form 4 against the committed keeper bundles, so **no control solve was spent**.
2. **Every pre-registered prediction holds.** P1: ST_GAS energy falls in every year. P2: |ΔC3a| < 0.5 pp in
   every year — measured **+0.100 / +0.053 / +0.115 / +0.012 pp** — and **2022 stays FAIL**.
3. **THE ARM DOES NOT CLOSE THE RUBRIC, AND WAS NEVER CLAIMED TO.** 2022 C3a **+12.899 % → +12.999 %**
   against a ≤ +10 % band. Closing it needs −2.45 $/MWh; this moves +0.08.
4. **It costs a little price and buys a little dispatch** — the OPPOSITE trade to caiso-267/268, which
   bought price by degrading dispatch and which the owner refused on rule 1 `[R-STRUCT]` grounds. C1 moves
   **toward** measured for CC_REGULAR (2023, 2024, 2025), CT_PEAKER (2023, 2024, 2025) and CT_CHP (all four).
5. **Nothing is close to a band.** The worst C1 cell in any year is 2023 CC_REGULAR at −3.551 TWh against a
   ±5.27 TWh band; C2 gas total moves ≤ 0.009 TWh; `slack` and `dump` are 0 in every zone-hour of every year.
6. **The session's largest result is still the negative one** carried from the charter §0 and
   `FINDING-caiso270`: **no registered mechanism can close CAISO's 2022 rubric failure**, and the residual
   is a broad ~1 heat-rate-point marginal-unit bias with no single mechanism behind it.

## §2 — The scorecard, arm vs control, every year (G-CTRL form 4)

Controls: the committed keeper bundles `results/calibration/caiso269_lateevening_span` (2023-2025) and
`caiso269_lateevening_2022` — restored by caiso-270 in this same session-chain, which is why form 4 was
available at all. **No control solve was spent.** The instrument reproduces every published control value.

| year | C3a control | **C3a arm** | ΔC3a | C3b control | **C3b arm** | ΔC3b | ST_GAS Δ (TWh) | slack |
|---|--:|--:|--:|--:|--:|--:|--:|--:|
| 2022 | +12.899 % *(pub +12.90)* | **+12.999 %** | **+0.100 pp** | 0.2402 *(pub 0.2402)* | **0.2403** | +0.0001 | −0.0353 | 0 |
| 2023 | +4.331 % *(pub +4.33)* | **+4.383 %** | **+0.053 pp** | 0.0827 *(pub 0.0827)* | **0.0824** | −0.0002 | −0.0386 | 0 |
| 2024 | +8.544 % *(pub +8.54)* | **+8.659 %** | **+0.115 pp** | 0.1391 *(pub 0.1391)* | **0.1392** | +0.0000 | −0.1048 | 0 |
| 2025 | +7.870 % *(pub +7.87)* | **+7.882 %** | **+0.012 pp** | 0.1070 *(pub 0.1070)* | **0.1070** | +0.0001 | −0.0095 | 0 |

**C3a degrades in all four years and that is the headline of this table**, reported before anything
favourable. It is small, it is the direction the §3 footprint requires, and it was pre-registered.

### §2.1 — C1 fuel-mix by class, at full magnitude

Signed error vs actual (TWh), control → arm. **Every cell is inside the rubric v3.4 floored band in every
year** (±5.06 / ±5.27 / ±5.29 / ±5.04 TWh).

| year | CC_REGULAR | CC_CHP | CT_PEAKER | CT_CHP | ST_GAS | C2 gas total |
|---|---|---|---|---|---|---|
| 2022 | +2.853 → +2.888 | +0.908 → +0.907 | −1.432 → −1.433 | −1.076 → **−1.073** | −0.908 → −0.943 | +0.345 → +0.346 |
| 2023 | −3.578 → **−3.551** | +0.770 → +0.770 | −2.120 → **−2.105** | −0.880 → **−0.876** | −1.189 → −1.228 | −6.997 → **−6.991** |
| 2024 | −0.529 → **−0.484** | +0.740 → +0.744 | −2.768 → **−2.725** | −0.777 → **−0.771** | +0.067 → **−0.038** | −3.267 → −3.275 |
| 2025 | −0.171 → **−0.169** | +0.458 → +0.459 | −1.588 → **−1.587** | −0.105 → **−0.105** | −0.063 → −0.073 | −1.470 → −1.475 |

**Against the arm, stated plainly:** ST_GAS moves **away** from measured in 2022, 2023 and 2025 — the class
was already under-run and the arm makes 1,142 MW of it dearer, so it runs less. **For the arm:** CC_REGULAR,
CT_PEAKER and CT_CHP move toward measured in almost every cell, and 2024 ST_GAS improves in magnitude
(+0.067 → −0.038). The net is a small dispatch gain and a small price loss.

## §3 — The four STOP gates (PRECOMMIT §5), scored in the parent

| gate | condition | measured | verdict |
|---|---|---|---|
| **G-IDENT** | only `egrid_family_heat_rates` differs | verified pre-solve on the keeper's own recorded config, and re-verified in all four `run_config.json` (signature: the six armed flags all `true`, `mode backcast`, `gas_price_override` 6.45/2.54/2.19/3.52, `weather_year` matching, `git_sha 9ee5319b`) | **PASS** |
| **G-FOOT** | response confined to the §2 units' classes | class-energy deltas confined to the gas classes plus a rounding-level import / solar / hydro reshuffle (largest non-gas: import +0.0161 TWh in 2024) | **PASS** |
| **G-DIR** | ST_GAS energy **falls**; Alamitos dearer, Glenarm cheaper | ST_GAS **−0.0353 / −0.0386 / −0.1048 / −0.0095 TWh** — falls in every year, as a +2.288 MMBtu/MWh reprice of 1,142 MW requires | **PASS** |
| **G-NOFLIP** | no load-bearing criterion flips PASS → FAIL | C1 every cell in band in every year; C2 gas total moves ≤ 0.009 TWh; C3b flat to ±0.0002; C3a degrades but crosses no band (2022 was already FAIL and stays FAIL — not a flip). C3c exempt (rubric v3.6) | **PASS** |
| **G-CTRL** | form 4, earned by G-DRIFT | caiso-270 confirmed the drift audit **by measurement** (the keeper re-solve reproduced published C3a to ≤0.0041 pp and C3b to 0.0000). **No control solve spent** | **PASS** |

**Load-bearing artifact check, done on the artifacts and never on a shard's claim about them:**
`resolved_inputs.seam_import_cap` reads **`source: "mic_partition"`** in all four bundles (2022 `cap_mw`
15780.0, 2023 16055.0, 2024 16452.0, 2025 16148.0), so **no bundle solved on the retired fitted fallback
import scalar** (rules 20 `[R-DOF]` / 24 `[R-REGISTRY]`).

## §4 — What the mechanism is, and why it stands whatever the residual did

The fleet joins heat rate from eGRID at **PLANT** grain (`PLNT<yy>.PLHTRT`), so a plant hosting two
prime-mover families hands **both halves one generation-weighted blend that is a measured number for
neither**. eGRID publishes the per-family inputs in the same vintage the join already reads. The CAISO
artifact (derived in the PRECOMMIT commit, rule 25) covers **4 plants / 8 (plant, family) rows**, and the
fleet effect is **6 units / 1,451.8 MW / 4.54 % of the CAISO fleet**: AES Alamitos three ST units
(1,142 MW) **+2.288** MMBtu/MWh, Huntington Beach ST (225.8 MW) −0.356, Glenarm (84 MW gas_cc) −1.361.

**Zero free parameters, zero new thresholds** (rules 21/24) — the statistic is arithmetic on published
fields and admission is a population rule. **Rule 19 `[R-ONE-MECH]`:** applied at the eGRID-input seam so
every class-scoped measured mechanism keeps its precedence, and it **retires the `MIXED_FACILITY_STEAM_HR`
hand number** at covered plants rather than stacking on it. **Rule 13 `[R-MEASURED]`:** the identical
construction regenerates from any eGRID vintage; the CC families are stable across vintages (315 CC
7.244 → 6.980; 335 CC 7.098 → 6.954, 2023 → 2024).

**Rules 1 `[R-STRUCT]` and 14 `[R-ACCURATE]` are the whole case.** The direction was measured and declared
**before** the solve. Rule 1 forbids judging a structurally-correct mechanism by whether it improves the
residual; rule 14 says a worse fit from an accurate input is a signal that something else is miscalibrated
— and §5 is where that signal points.

## §5 — Where the real residual is, carried forward unchanged

From the charter §0 and `FINDING-caiso270` §4, neither of which this run moves:

* The residual is **thermal-marginal** (caiso-266 killed the renewable/dump floor family).
* In the 6,924 hours where the CC econ stack reaches its deepest band — **81.8 % of 2022 load** — the model
  carries **+6.63 of the +9.32 $/MWh** annual gap, at implied marginal heat rate **10.33 vs 9.52 actual**.
* **It is not a CC capacity constraint**: CC runs at **55.2 % of its own annual max** in those hours and
  clears 95 % of max in only 315 of them; and CT_PEAKER is **under**-run (3.047 vs 4.479 TWh).
* Across all 48 months of 2022-2025, the model's implied marginal heat rate exceeds the market's in
  **40 of 48**, mean **+1.01**; December 2022's +1.73 ranks **12th of 48**.

**No registered mechanism maps onto that**, and the charter §0 table records why each candidate is dead.

## §6 — Disclosures against interest

1. **C3a degrades in all four years.** Reported in §1 line 3 and at the top of §2, not buried.
2. **ST_GAS moves away from measured in three of four years** (§2.1) — the arm's own footprint doing what it
   must, on a class the model already under-runs.
3. **The arm is small.** 4.54 % of fleet MW, and the affected ST_GAS class carries 0.02–0.38 TWh a year, so
   the repriced block is rarely marginal. 2025 is close to inert (ΔC3a +0.012 pp) — as the shard prompt
   said in advance it might be.
4. **The session did not find what it was asked for.** It was asked for an LP with potential to close the
   rubric. It found none, said so in the PRECOMMIT before solving, and launched this instead on rule-14
   grounds. That is a failure to deliver the requested outcome, not a success to be re-framed.
5. **`egrid_identity_heat_rates` and `egrid_steam_collapse_heat_rates` were NOT tested** — their derives are
   `--iso NYISO`-scoped at HEAD. Extending them is a separate lane's work (rule 19: one mechanism at a time).

## §7 — RULE 31 `[R-RETAIN]`: THE PROMOTION QUESTION, PUT EXPLICITLY

**I have NOT promoted this. The keeper stays `2026-09-10-caiso-269-lateevening-clean`.**

**The four bundles are on this container's local disk (gitignored) AND on their shard branches**
`claude/caiso271-family-{2022,2023,2024,2025}`, which carry the full bundles including `dispatch/`. **The
branches are the durable copy.** Nothing has been deleted.

The trade, stated once: **all four gates pass; C1 dispatch improves in most cells and crosses no band; C3a
degrades by 0.012–0.115 pp; the 2022 rubric failure is untouched.**

* **(a) PROMOTE.** Defensible on the owner's own standing ruling — *"if structural integrity improves but
  gates regress that may still be a keeper"* — and on rules 1/14: it is a measured input replacing a blend,
  with zero free parameters, that also retires a hand number. It changes no determination: train years stay
  CALIBRATED with the single ledgered C3c, 2022 stays NOT-YET.
* **(b) DO NOT PROMOTE, keep the code default-off.** The honest reading of "it costs price and the dispatch
  gain is small". The mechanism and its CAISO artifact stay in the tree for a later lane.
* **(c) PROMOTE THE ARTIFACT AND THE CODE, HOLD THE KEEPER** — keep `egrid_family_heat_rates_CAISO.csv` and
  the measured cell verdict, leave the flag off and the keeper alone. **This is my recommendation**: the
  measurement is worth having on the record, and a 0.1 pp C3a regression buys too little dispatch to spend
  a keeper promotion on while CAISO's real residual is still unexplained.

**Next number: caiso-272.**
