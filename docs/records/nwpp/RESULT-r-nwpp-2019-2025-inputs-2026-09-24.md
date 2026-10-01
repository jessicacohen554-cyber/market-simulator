# RESULT R-NWPP: NWPP 2019 + 2021–2025 on corrected backcast inputs (2026-09-24)

**Run:** `2026-09-24-rnwpp-inputs-span`, bundle `results/calibration/rnwpp_span`, registered, **not promoted**.
**Recipe:** `docs/handoffs/PRECOMMIT-r-nwpp-2019-2025-inputs-2026-09-24.md` §4.
**Solved:** six year-isolated shards (rule 36), all pinned to `b6ce536ad1e7e41e083b81f784f8e94084bbce2f`. The parent spent zero LP.
**Control:** keeper `2026-09-24-nwpp-49-ror-split`, 2023–2025 (rule 29(b) form 4).

## 1. Headline

**NOT-YET on {fuelmix, dispatch_corr}.** The keeper is NOT-YET on {dispatch_corr} alone. Price is **unscored**
(rubric v3.8). C2, C6 and C8 PASS.

| criterion | keeper (2023 / 24 / 25) | R-NWPP (2019 / 21 / 22 / 23 / 24 / 25) |
|---|---|---|
| C1 fuel mix | PASS | 2019 PASS · 2021 PASS · **2022 FAIL** · **2023 FAIL** · 2024 PASS · 2025 SKIPPED (preliminary 923) |
| C2 system volume | PASS | PASS (2025 SKIPPED) |
| C4 coal r | 0.660 / 0.618 / 0.638 FAIL | 0.774 / 0.740 / 0.772 PASS · **0.671 / 0.622 / 0.687** FAIL |
| C4 gas r | 0.846 / 0.894 / 0.868 | 0.763 / 0.842 / 0.863 / 0.833 / 0.889 / 0.860 (all PASS) |
| C6 governance | PASS | PASS |
| C8 forced share | PASS | PASS |

**The two C1 failures are both CC_REGULAR (band ±8.00 TWh):**

* **2023: −7.21 → −8.32 TWh.** NWPP-51 predicted this flip: Jim Bridger 1–2 are coal in `vintage_2023`, and the added
  coal displaces gas on top of the open demand-basis gap (FINDING-nwpp-45 §8: −7.6 / −10.0 / −7.1 TWh).
* **2022 (a new year): −11.23 TWh.** In the same year, COAL_PRB is +7.61 and COAL_BIT is +5.68 TWh, both inside their
  bands. That is the same coal-over-gas signature as 2023, but larger.

## 2. Per-year class table (model − actual, TWh; C1 status)

| year | CC_REGULAR | CC_CHP | CT_PEAKER | ST_GAS | COAL_PRB | COAL_BIT |
|---|---|---|---|---|---|---|
| 2019 | +1.50 | −1.27 | −1.39 | −0.90 | +3.58 | −4.47 |
| 2021 | −6.59 | −1.88 | −2.45 | −0.85 | +3.61 | +3.45 |
| 2022 | **−11.23 FAIL** | −1.32 | −2.38 | −1.10 | +7.61 | +5.68 |
| 2023 (keeper) | **−8.32 FAIL** (−7.21) | −0.62 (+0.77) | −4.75 (−3.97) | −1.36 (−1.31) | +3.76 (+0.49) | +4.54 (+4.18) |
| 2024 (keeper) | −2.57 (−5.21) | −0.92 (−0.29) | −3.33 (−2.33) | −4.06 (−4.23) | +2.04 (+3.27) | −0.04 (−0.36) |
| 2025 | skipped (preliminary EIA-923) | | | | | |

**Class energy vs the keeper, 2023 / 2024 / 2025 (model TWh):**

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CT_PEAKER | −0.78 | −1.00 | −1.49 |
| CC_CHP | −1.39 | −0.64 | −0.69 |
| COAL_PRB | +3.27 | −1.23 | −1.07 |
| CC_REGULAR | −1.10 | +2.63 | +2.94 |

Hydro, wind, solar, nuclear and biomass are unchanged (≤ 0.01 TWh).

**C5a CO2** (reported only): −12.4 / −9.4 / −3.3 / −8.0 / −15.4 / −14.2 %.

**Model-only mean LMP, UNVERIFIED** (no reference exists): $32.89 / 47.52 / 59.37 / 48.54 / 29.65 / 31.43 per MWh.

## 3. Reading it (rule 1: structure first)

* **The input corrections are real and zero-DOF.** They do three things:
  * CT_PEAKER now uses measured heat rates. The capacity-weighted rate moves from 8.90 to 10.7–11.1, and CT
    energy falls accordingly. CT_PEAKER was already short of actual, and is now shorter: 2023 −4.75, 2024 −3.33
    TWh. That points to CT commitment or offers, not to the heat rate.
  * The retired and converted coal units are now year-correct.
  * The pre-2023 years are solvable at all.
* **The gas-short / coal-long pattern is the standing NWPP defect, not a new one.**
  * It appears in the three new years too: 2021 CC −6.59 with coal +7.1; 2022 CC −11.23 with coal +13.3.
  * It is the FINDING-nwpp-45 §8 demand-basis gap: EIA-930 under-books gas in PGE/BPAT/PACW. That owner decision
    is still OPEN.
  * Year-correct coal widens the gap because the fleet is now honest about the coal that existed.
* **Coal dispatch r improves in every scored year** (+0.011 / +0.004 / +0.049) and passes in 2019/21/22. It still
  fails in 2023–25.
* **What this run does NOT carry:**
  * The hydro cascade is inert in 2019/21/22, because CROHMS covers 2023–25 only.
  * The 2020 year.
  * Short-gas outage windows, not armed (the guard cannot separate idling on NWPP).

## 4. Recommendation

**Promote on structure (rule 1), with the C1 regression stated at full magnitude rather than tuned away.**

* It is the only NWPP run carrying the owner-ordered correct inputs.
* It is the only one covering 2019 and 2021–2022.
* Keeping the incumbent means keeping 2023–24 on 2025ER-snapshot fleets and eGRID-2023 class rates, which rule 14
  says was compensating for the demand-basis gap.

If the owner prefers a clean C1 first, the lever is the demand-basis decision (FINDING-nwpp-45 §8 framing 2), not
a multiplier. **The promotion is the owner's call (rule 31); nothing was promoted or pruned.**

If promoted:

* **Rule 35(b)–(c) holds.** The incoming run covers the keeper's whole registered year set {2023, 2024, 2025}.
* **The prune order is:** `keepers/NWPP.json` → `audit_keepers.py` E1 → `prune_iso_runs.py --iso NWPP`.

## 5. Retrievability (rule 34(e))

* **On `main` via this lane's PR:**
  * the registered slim bundle (`results/calibration/rnwpp_span`: `hourly/`, per-year `run_config_<y>.json`,
    `meta.json`, `metrics.json`, attestation, legitimacy diagnostics);
  * the sidecar;
  * the run payload `runs/2026-09-24-rnwpp-inputs-span.js`;
  * the bench parts.

  **A promotion costs zero re-solves:** the payload is already built.
* **Not on `main`:** the full `dispatch/` parquet (67 MB) and the per-year legs. They are gitignored on the parent's
  disk. A later re-render that needs `dispatch/` costs **~35 min wall, re-solved**: six parallel shards, ~30–35 min
  each.
* **Leg provenance, by SHA only** (shard branches are transport, rule 33(d)/(f)):

  | year | leg SHA |
  |---|---|
  | 2019 | `45d6c3bc57bcffdcde5a17c0af330084d1e01a5e` |
  | 2021 | `4c00a047ac3f4c139cf9b7aef76ac3d9bd1728c4` |
  | 2022 | `2021ab7e7f4591a9131d19ae20769b61549692ef` |
  | 2023 | `e90513088dadaa799462b899101a6edb5000ac20` |
  | 2024 | `350bd57a8e1e02a442dfe8e1578ae829cb31a950` |
  | 2025 | `cc3746809e68df0f47d93e2f18ecd3a0cdb2517b` |

* **Leftover shard branches the owner needs to clear** (the session cannot delete refs, rule 33(f)(2)):
  `claude/rnwpp-{2019,2021,2022,2023,2024,2025}`.

## 6. Process notes

* **The parent's hard stop 4 was mis-specified.**
  * It required `run_config_<Y>.json` and `metrics.json`. A single-year leg writes `run_config.json`, and neither
    `metrics.json` nor `legitimacy_diagnostics.json` exists until composition.
  * The first 2021 and 2022 shards stopped correctly on it and could not be messaged. Those two years were
    relaunched (~35 min) with the corrected check.
  * The stopped shards were archived, and their unpushed duplicate solves were lost. No result was lost, because
    the relaunches reproduce the same pinned recipe.
* **All eight shard sessions are archived.**
* **Composition:** `scripts/probes/_nwpp42_compose_span.py`, with the 2023 leg as the base. The meta therefore
  records `hydro_backfill_year=2024`, and 2019/21/22 replay with `--set hydro_backfill_year=null`, which the
  attestation declares. Every `scenario_config` field agreed across the six legs; solve-surface fingerprint
  `0814211c28908d1b`.
* **`check_registry_payload_parity.py` is RED locally** only on the six gitignored leg dirs (rule 31, correction
  note). Nothing else is flagged.
