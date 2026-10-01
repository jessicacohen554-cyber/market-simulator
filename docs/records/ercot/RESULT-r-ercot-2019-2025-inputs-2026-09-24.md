# RESULT — R-ERCOT: ERCOT 2019–2025 re-solved on corrected backcast inputs

**Session:** R-ERCOT, parent/orchestrator, 2026-09-24. **PRECOMMIT:** `docs/handoffs/PRECOMMIT-r-ercot-2019-2025-inputs-2026-09-24.md`. **Pinned SHA:** `b1f800e80b03c47abc68c947f7f000dc5c615b18`.
**Registered:** `2026-09-24-r-inputs-2019-2025`, bundle `results/calibration/r_ercot_arm_span`, years 2019–2025. **NOT promoted.** The incumbent keeper `2026-09-19-ercot266-mer-five-year` is untouched.

## Headline

1. **The forward config (2024–2025) holds CALIBRATED on the corrected inputs.**
2. **The 2023 carve-out regresses.** C3b NRMSE goes from 0.146 to **0.232**, which is a FAIL. The train-tier span 2023–2025 is therefore **NOT-YET**, where the keeper is CALIBRATED.
3. **2021 regresses:** C3a goes from +6.0 % to +10.0 %, and C3b from 0.171 to 0.202. **2022 improves:** C3a from −7.7 % to −0.2 %, and C3b from 0.167 to 0.098.
4. **2019 and 2020, new years, fail heavily.** C3a is +364 % and +114 %. The model sheds load at the $5,000 cap: 101 GWh in 2019 and 11 GWh in 2020. Coal (PRB) is short by 12 and 14 TWh.
5. **The control reproduces the keeper to within $0.03/MWh in every year.** Engine drift since the keeper's SHA is therefore negligible, and **every movement above comes from the input correction itself.**

## Per-year, keeper → arm (the control equals the keeper, see §3)

| year | C3a mean LMP | C3b NRMSE | C3c h > $200 (model / actual) | C1 | year verdict (arm) |
|---|---|---|---|---|---|
| 2019 | — → **+364.3 % F** | — → **6.410 F** | 261 / 106 (CAVEAT) | **F** (CC_REG +11.0, ST_GAS +8.9, COAL_PRB −11.9 TWh) | NOT-YET |
| 2020 | — → **+114.3 % F** | — → **2.537 F** | 102 / 56 | **F** (CC_REG +10.4, ST_GAS +10.6, COAL_PRB −13.7 TWh) | NOT-YET |
| 2021 | +6.0 % → **+10.0 % F** | 0.171 → **0.202 F** | 691 → 700 / 258 (CAVEAT) | P | NOT-YET |
| 2022 | −7.7 % → −0.2 % | 0.167 → 0.098 | 102 / 196 | P | CALIBRATED |
| 2023 | −0.9 % → +2.7 % | 0.146 → **0.232 F** | 192 → 189 / 181 | P | NOT-YET |
| 2024 | +0.1 % → +3.7 % | 0.125 → 0.147 | 23 → 29 / 53 (CAVEAT) | P | CALIBRATED (span with 2025) |
| 2025 | −6.8 % → −3.5 % | 0.106 → 0.088 | 1 / 31 (CAVEAT) | P | CALIBRATED (span with 2024) |

- **Span determinations (arm):** forward {2024, 2025} **CALIBRATED**; carve-out {2023} NOT-YET; train {2023–2025} NOT-YET; validation {2021, 2022} NOT-YET; {2019, 2020} NOT-YET.
- **Registered whole-span run:** NOT-YET. It scores 8 criteria with 3 failures (C1, C3a, C3b) and 1 ledgered caveat (C3c).
- **Every year, arm:** C2, C4, C6 and C8 PASS. C5a CO2 is within ±6 % in every year (reported only).

## 1. Prices and slack (P1 load-weighted mean, $/MWh)

| year | actual RT (simple mean) | keeper | control | arm | arm − control | slack MWh (keeper / control / arm) |
|---|---|---|---|---|---|---|
| 2019 | 35.77 | — | — | 217.74 | — | — / — / **101,209** |
| 2020 | 21.21 | — | — | 54.64 | — | — / — / **11,138** |
| 2021 | 148.19 | 175.48 | 175.45 | 182.13 | **+6.68** | 2,659 / 2,659 / **14,907** |
| 2022 | 62.30 | 68.68 | 68.65 | 74.28 | **+5.63** | 0 / 0 / 0 |
| 2023 | 48.36 | 63.72 | 63.69 | 66.07 | +2.38 | 172 / 172 / 164 |
| 2024 | 26.82 | 31.02 | 31.01 | 32.14 | +1.13 | 694 / 694 / 687 |
| 2025 | 32.49 | 33.81 | 33.80 | 35.02 | +1.22 | 0 / 0 / 0 |

All five control years equal the keeper to within $0.03/MWh.

## 2. Where the energy moves (arm − control, TWh; sealed predictions P1/P2)

| class | 2021 | 2022\* | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|
| CC_CHP | −3.36 | −3.89 | −2.57 | −2.59 | −2.83 |
| CC_REGULAR | +2.76 | +4.39 | +1.70 | +1.65 | +2.16 |
| CT_CHP | +0.85 | +1.18 | +1.10 | +1.17 | +1.14 |
| ST_GAS | +0.06 | −0.88 | +0.41 | +0.65 | +0.55 |
| COAL (lignite + PRB) | −0.08 | −0.53 | −0.34 | −0.28 | −0.84 |

\*2022 is differenced against the ctl-2022 leg.

- **P1 CONFIRMED:** CC_CHP falls and CT_CHP rises in every year. This is the direct sign of the heat-rate move: power-only CHP rates raise CC_CHP's base rate by 13–17 %, and CT_CHP's rate falls.
- **P2 CONFIRMED:** coal moves at most 0.84 TWh, under 1.5 %. Coal's offer levels come from its per-plant real-time dispatch (SCED) offer curves (ERCOT-144), so its heat rate barely reaches its price.
- **P3 CONFIRMED by construction:** the class default reaches only the 1,129.9 MW listed in the PRECOMMIT §4.
- **P4:** see §4.

## 3. G-DRIFT, measured

The control solves the incumbent recipe at the pinned SHA with all eight R-ERCOT flags off. It reproduces the keeper:

| year | control − keeper ($/MWh) | slack |
|---|---|---|
| 2021 | −0.03 | identical |
| 2023 | −0.03 | identical |
| 2024 | −0.01 | identical |
| 2025 | −0.01 | identical |
| 2022 | −0.03 | identical |

So the 55-file / +11.6k-line engine diff since `5926ca52` is **inert for ERCOT to the cent**. The G-DRIFT question the PRECOMMIT left open is closed by measurement.

## 4. Root cause, stated as far as it was measured (rule 14: the regressions are reported, not tuned)

**2023 C3b and 2021.** The arm raises prices in every year: +$1.1 to +$6.7/MWh against the control (2022: +$5.63). The mechanism is the ~2.6–3.9 TWh/yr of CC_CHP pushed up the stack by the power-only CHP heat rate, together with the removal of short-window gas/coal availability (census §4c: −200 to −590 MW mean CC_REGULAR). In 2021 the arm also sheds **+12.2 GWh more** load than the control (Uri, Feb 13–15 and September), which is the short-outage family acting on the scarcity hours.

The carve-out recipe's ×33 peak bands were identified against the old inputs. Rule 1(c) forbids re-tuning them here, so the shape miss stands as measured.

**Open question, not decided here:** is the power-only CHP rate the right base for ERCOT's CHP bins? Those bins already carry a separate must-run (host-steam) tranche, so charging the full thermal heat to power *could* double-count the steam side. This is a **rule 19 question about composition** and is routed, not resolved. **It is the most important thing to settle before any promotion.** The census attributes most of the 2023 price move to CC_CHP.

**2019 / 2020.** The measured leading candidate is that ERCOT's 60-Day DAM thermal availability file (`ercot-thermal-dam-availability.csv`) **covers 2021–2025 only**.
- In 2019 and 2020 the gas/coal availability therefore falls back to the statistical + CAMPD stack.
- No ERCOT keeper year has ever run on that stack, because every recipe year had DAM coverage.
- The slack sits in the July–August 2019 peak: 81 hours, max 3.6 GW short at 73.4 GW demand. Real ERCOT served that summer without shedding load.
- Several other ERCOT mechanisms are year-scoped to later years too: the cleared-share RT basis, the fast-start pool, and the coal peak-tranche year level (table covers 2023 only).
- The coal shortfall (COAL_PRB −12 / −14 TWh) points the same way: coal offer levels are measured on later years' SCED curves.

**NOT root-caused.** A pre-2021 availability source would be a new data intake.

## 5. Bundles and retrievability (rules 33(d) / 34(e))

- **On `main` once this lane's PR merges:** the composite `results/calibration/r_ercot_arm_span` in its rule-15 committed shape (hourly sidecars, run configs, attestation, diagnostics), plus `registry/2026-09-24-r-inputs-2019-2025.json` and `runs/2026-09-24-r-inputs-2019-2025.js`. Registration needs nothing more.
- **Per-year legs:** gitignored, on this session's disk only. Their shard branches are transport and will be cut. Provenance shard commits: arm `9c2a75bd` / `876ff233` / `0960ebc7` / `f5fb24e2` / `aa4a3666` / `8610c003` / `2b4bf80a` (2019–2025); ctl `04d6f857` / `778c7c6a` / `a1727e9d` / `9e8dfce4` / `7e3c7d03` (2021–2025).
- **Recovery cost if the composite ever needed a re-solve:** about 17 min per year in parallel shards.
- **Shard branches left for the owner to clear** (a session cannot delete refs, rule 33(f)): `claude/r-ercot-arm-{2019..2025}`, `claude/r-ercot-ctl-{2021..2025}`, and `claude/r-ercot-ctl-2022b` if the stopped replacement pushed one.

## 6. Governance

- **Shards:** all 13 archived — 12 legs plus one redundant ctl-2022 replacement, which was interrupted before it pushed anything.
- **Shard branches:** each leg's `run_config.json` records git `b1f800e8` with a clean tree. The ctl-2022 shard's final "PINNED_SHA mismatch" status is its own commit sitting on top of the pinned SHA; the solve itself ran at the pinned SHA.
- **Matrix:** eight ERCOT cells set to **O** (tested; owner ruling pending), with this evidence.
- **Dashboard:** the run is registered with `--no-prune`.
- **Known red gates:**
  - `audit_keepers` E13 flags the registered candidate, which is neither the keeper nor stamped to it. This is the expected state while a promotion is pending; rule 31 forbids pruning it before the owner rules.
  - `check_registry_payload_parity` is red **locally only**, on the 12 gitignored per-year legs. CI never sees them, as rule 31's correction note predicts.
- **Bench parts:** re-rendered for 2019–2025. 2019 and 2020 are new. The 2021–2025 diffs come from F1/F2 input changes at HEAD (builder fingerprint, eGRID-vintage CO2 intensities, and a handful of plant rows), not from this run.
- **Tests:** 4 pre-existing unit failures, reproduced on clean HEAD; none from this lane.

## 7. Promotion — OWNER DECISION NEEDED

**My recommendation is NOT to promote.** Promoting would move ERCOT's train-tier determination from CALIBRATED to NOT-YET (2023 C3b). The regression is traceable to one input choice — the power-only CHP heat rate on bins that already model host steam — whose composition is unresolved. 2019/2020 also expose a pre-2021 availability-data gap that no recipe setting can fix.

The case for promoting: it is the owner-mandated input set (year-correct EIA-860, plant heat rates, granular outages), and the forward config stays CALIBRATED. Rule 1 says a structurally more faithful run is not rejected for fitting worse.

The options:
1. **Hold** (recommended): keep the incumbent. Route (a) the CHP heat-rate composition question and (b) a pre-2021 ERCOT availability intake. Re-solve once both are settled.
2. **Promote as is:** ERCOT reads NOT-YET, and 2019–2025 join the keeper.
3. **Promote the input set minus the CHP class** (`measured_chp_heat_rates=false` on ERCOT only): this needs a fresh 7-shard solve, about 17 minutes of wall-clock, and is not done here.

**The composite is committed on this branch. The per-year legs are on local disk only and will not survive this session.**
