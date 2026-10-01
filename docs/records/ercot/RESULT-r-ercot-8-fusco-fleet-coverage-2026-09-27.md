# RESULT — R-ERCOT-8: Jack Fusco (55357) joins the ERCOT fleet — PROMOTED, ISO reads NOT-YET

**Session:** R-ERCOT-8, 2026-09-27. **PRECOMMIT:** `docs/records/ercot/PRECOMMIT-r-ercot-8-fusco-fleet-coverage-2026-09-27.md`, merged in PR #6772, pinned SHA `5696a72ce54327901681016a417e4900bba70db1`.

**Keeper:** `2026-09-27-r-8-fusco` (bundle `results/calibration/r_ercot8_fusco_span`, 2019–2025). It supersedes `2026-09-25-r-5-hour-grain`.

## Headline

- **ERCOT is promoted and now reads NOT-YET.**
  - The owner answered the decision card with verbatim *"Promote + fix 2023 next (Recommended)"*.
  - The forward config (2024–2025) stays CALIBRATED.
  - The 2023 carve-out drops from CALIBRATED to **NOT-YET**: C3a −7.5 → **−19.8 %**, C3b 0.133 → **0.290**.
- **The `complete` marker is withdrawn** (Q5). Forecast gate (a) is flipped pass → fail in the same commit.
- **The 2023 drop is a real compensating error, now exposed (rule 14).** The fix is an accurate plant, not a mechanism.
  - Of the superseded keeper's 59 hours above $1k in 2023, 22 were formed by the missing 676 MW.
  - 63 % of the −$7.86/MWh LW move sits in those 59 hours. The median hourly move elsewhere is −$0.22.
  - The actual 2023 market had about 61 hours ≥ $1k with Fusco running. The model's 2023 scarcity formation was leaning on capacity that did not exist in the model but did exist in the market.
- **The validation years improve:**
  - 2019 C3a +59.8 → +26.0 %, C3b 1.334 → 0.683;
  - 2020 C3a +11.7 % FAIL → +7.1 % PASS;
  - the 2022 C1 CC_REGULAR gap narrows from −10.88 to −10.05 TWh.
- **Fusco dispatches plausibly:** 2.71 / 3.64 / 2.92 / 3.21 / 3.13 / 3.16 / 3.67 TWh in P1 (2019–2025), against EIA-923 net 2.34 / 3.43 / 2.75 / 3.39 / 3.31 / 3.40 / 3.65.

## Per year (keeper → arm; official `calibration_verdict --years` on committed artifacts)

| year | tier | LW $/MWh | C3a | C3b | C3c (> $200 h, model vs RT) | h > $1k | slack MWh | coal TWh | CC TWh | verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | val | 74.94 → 59.11 | +59.8 → **+26.0 %** | 1.334 → 0.683 | → 90 vs 106 | 53 → 38 | 5,806 → 2,033 | −0.43 | +1.14 | NOT-YET → NOT-YET |
| 2020 | val | 28.48 → 27.32 | +11.7 → **+7.1 % PASS** | 0.361 → 0.285 | → 40 vs 56 | 5 → 3 | 0 → 0 | −0.51 | +0.56 | NOT-YET → NOT-YET |
| 2021 | val | 169.89 → 168.30 | +2.6 → +1.7 % | 0.136 → 0.137 | 672 → 668 vs 258 (caveat) | 123 → 122 | 6,430 → 3,117 | −0.16 | +1.09 | CALIBRATED → CALIBRATED |
| 2022 | val | 68.44 → 67.14 | −8.1 → −9.8 % | 0.164 → 0.184 | → 93 vs 196 (caveat) | 18 → 14 | 0 → 0 | −0.08 | +0.82 | NOT-YET → NOT-YET (C1 CC −10.05) |
| **2023** | **train** | 59.47 → 51.61 | −7.5 → **−19.8 % FAIL** | 0.133 → **0.290 FAIL** | 177 → 152 vs 181 PASS | 59 → 37 | 0 → 0 | −0.44 | +1.39 | **CALIBRATED → NOT-YET** |
| 2024 | train | 29.24 → 28.44 | −5.6 → −8.2 % | 0.120 → 0.143 | 18 → 13 vs 53 (caveat) | 2 → 1 | 454 → 3 | −0.55 | +1.70 | CALIBRATED → CALIBRATED |
| 2025 | train | 33.79 → 33.13 | −6.9 → −8.7 % | 0.108 → 0.120 | 1 → 0 vs 31 (caveat) | 0 → 0 | 0 → 0 | −0.23 | +1.56 | CALIBRATED → CALIBRATED |

## Prediction scorecard (PRECOMMIT §4)

- **P1 met.** Fusco P1 is in [1.5, 4.5] TWh every year. CC rises by less than Fusco's own output. Coal falls by ≤ 0.55 TWh.
- **P2 met.** The C1 benchmark gained Fusco's net generation. The 2019/2020 CC overshoot narrows (2019 +10.05 → +8.85 TWh, 2020 +11.03 → +8.16) and stays a FAIL.
- **P3 MISSED.**
  - 2023 −13.2 % against a sealed bound of ≤ 2.5 %. 2020 −4.1 % against ≤ 2.5 %. 2019 −21.1 % against ≤ 5 %.
  - 2021 −0.9 %, 2022 −1.9 %, 2024 −2.8 % and 2025 −2.0 % were within bounds.
  - The bound assumed a mid-merit CC would move prices by displacement only. It missed that +676 MW removes scarcity hours whose formation is knife-edge in the model.
- **P4 partly met.** Slack falls everywhere and hours > $1k do not rise. The C3c ≤ 5 h bound is missed in 2023 (−25 h).
- **P5 MISSED.** 2023 C3a lands at −19.8 %, below its sealed [−10.0, −7.5]. 2024 (−8.2 %) and 2025 (−8.7 %) are within theirs. The train determination did not stay CALIBRATED.
- **P6 met.** No C8 gate changed a determination. The composite diagnostics carry the same pre-existing D-4 off-window rows as the keeper.

## Decision (PRECOMMIT §5)

- A train year flipped, so the lane put it to the owner with no recommendation to revert. The rule 14 input stays regardless.
- The owner ruled *"Promote + fix 2023 next (Recommended)"*.
- The config_partition_overrides are byte-equal to the outgoing keeper's (`stamp_config_partition --check` OK). No multiplier moved (rule 1(c)), and the DOF ledger is carried verbatim.

## Promotion

1. **Year union (rule 35(b)):** {2019..2025}, read before the prune. The new keeper covers all seven years.
2. **Re-keyed:**
   - `keepers/ERCOT.json`: every partition config, `iso_determination` → NOT-YET, and an `r_ercot8_extension` block;
   - `calibration-complete.json`: ERCOT moved to `withdrawn` (Q5);
   - `program-status.json` gate (a): pass → fail, `marker_complete` False;
   - `status/ERCOT.js` rebuilt;
   - the matrix shard's keeper and gates stamps, and the §5.1 header.
3. **Checks:**
   - `audit_keepers --iso ERCOT` before the prune: only E13 on the outgoing run.
   - `prune_iso_runs.py --iso ERCOT --force-uncite` removed `2026-09-25-r-5-hour-grain`'s three stores.
   - After the prune: 0 failures, 0 warnings.
   - `check_gate_a_provenance --iso ERCOT` OK.

## Where the bytes are (rule 34(e))

- **On `main` once this PR merges:** the keeper bundle `results/calibration/r_ercot8_fusco_span` (rule-15 shape), its sidecar and its run payload.
- **Per-year shard commits** (provenance only, rule 33(d)): 2019 `6f0c78e51d191124e261635fc4a14a4b5ff072b4`, 2020 `75f255d2f96f8d1230f8a60f8c054139e896d65a`, 2021 `f8dbccf57db8eb23327d3f07d063a7104fd7577d`, 2022 `d0c3f146b79dbc70f1e897d79837d98a31838bc8`, 2023 `821bf0e97ad02506c66f3c01f444fef50ce39750`, 2024 `eb2c80731b12231777d17e2b4d2c78c370b43606`, 2025 `675920e53598e253745ed386bdda8d4f0654c0e2`.
- **Re-solve cost of any leg:** one ERCOT year, ~25–35 min of LP.
- **Leftover refs the owner must delete** (sessions cannot, rule 33(f)): `claude/r-ercot8-arm-{2019..2025}`, `claude/r-ercot-8-fusco`.

## Findings routed, not fixed here

1. **The 2023 scarcity formation (the next object).** The keeper's 2023 C3a/C3b was partly supported by missing capacity.
   - The root cause is how the model forms 2023's tight-hour prices: reserve/ORDC in the ECRS era, and the 2023 carve-out's `peak` band multipliers, which were set while Fusco was absent.
   - Re-setting those multipliers against the gate is forbidden (rule 1(c)). A new ex-ante declared value needs owner authorization.
2. **MISO double count.** Fusco is also in MISO's EIA-860-BA fleet and outage extract. That is for the MISO lane (rule 25).
3. **Tooling:**
   - `build_ercot_dam_resource_crosswalk.py` drops all 26 coal rows on a rebuild at HEAD (a COAL-SUB break).
   - `derive_campd_cc_heat_rates.py` does not reproduce 3 ERCOT rows at HEAD.
4. **Decker Creek steam 1–2 (3548)** needs a fleet-loader retirement seam (validation years only).
5. **Main CI red:** 25 fast-tier failures, the same on every PR (SOCO/NWPP/NYISO/NEISO/CAISO/COAL-SUB fixtures, stale ERCOT golden-manifest expectations).
