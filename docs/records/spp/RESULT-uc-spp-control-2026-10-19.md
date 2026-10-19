# RESULT — UC-SPP-CONTROL: SPP keeper recipe on the R22/R23 data (2026-10-19)

PRECOMMIT: `PRECOMMIT-uc-spp-control-2026-10-19.md` (pushed `073bbb6f` before any shard). Owner ruling R25, UC-DESK
`session_01WX9W5tgYMre3Z134LZoGF6`. **Nothing registered or promoted.**

## 0. Answer

- **Recipe reproduced exactly.** In all 7 legs, every `scenario_config` field the keeper records has the keeper's value. The 31 fields
  registered since the keeper are all at their defaults (UC off). Epoch `2026-10-18b` is in every leg's surface (`bcdcc055b1144875`).
- **Determination: NOT-YET, the same failing set as the keeper.** No criterion changes verdict in any year. The datafix moves numbers only
  where §2 predicted: 2019 (+2.9 TWh net load) and 2025 (−0.54 TWh).
- **Unserved: 0 MWh in every year** (keeper: 0). Σ dump: 0.
- **C6 reads UNATTESTED** only because attestation is written at promotion (`promote_keeper.py`). This is not a model result. Until a bundle
  is attested, the keeper's auto-ledgered C3c caveats (2019–2022) show as FAIL; they come back on attestation.
- **Hourly price error falls in the masked hours in 5 of 7 years.** Examples: 2024 MAE 18.4 → 12.5, 2025 24.1 → 16.4 $/MWh. Unmasked
  hours move ≤ 0.2 $/MWh mean |Δ| (§3).
- **C4 hourly dispatch correlation falls in 2019 and 2025** (gas r 0.966 → 0.938; 2025 coal 0.919 → 0.882). Both still PASS.
  - Cause: 77–84 % of the dispatch change is in masked hours.
  - In those hours, the C4 benchmark (EIA-930 fuel mix) is still the frozen snapshot, unchanged by rule 37.
  - So the model now follows real load while the benchmark does not. This is a benchmark-basis artefact, not a model regression (§4).

## 1. Legs (all on the first attempt; no hard stop)

Pin `073bbb6fbde18a173a0032d29f802cf458131187`; every container had ceiling + swap of 22.4 GiB (gate 10.6 GiB).

| year | shard | commit | peak GiB | P0 + P1 LP s | files |
|---|---|---|---|---|---|
| 2019 | `session_01G17wbNh76LQJRpF8SbVhN6` | `aee17541fdecc7c22c77360b4840c821f21ca245` | 8.48 | 106 + 28 | 17 |
| 2020 | `session_01TWpEb5fJMPNdpQZALeSWLZ` | `c74ad7854d1c3f42db817eb3e1767bccf78e8999` | 7.91 | 103 + 37 | 17 |
| 2021 | `session_01Fvgkd482eLitfAgnbz22oh` | `d5389096e281bd7b61f9fbe20dbba297dc0f8b20` | 8.28 | 97 + 30 | 17 |
| 2022 | `session_01T1YRNHnVfGEACohiNFkb3K` | `a763f223c6803039b5bbee2ecfe7ae979b1a46e5` | 7.88 | 81 + 21 | 17 |
| 2023 | `session_01EVnmLceGxqyEzT5nKauEgX` | `2e97c42c9e40c4bd0c087a52ea6d8289d21e9e43` | 7.95 | 92 + 32 | 17 |
| 2024 | `session_019u5VxobvEdiRj7aru8ofDd` | `36a181eeaef44dab29a8d7f0bd05e9b0ff70e419` | 7.87 | 141 + 36 | 17 |
| 2025 | `session_01PSLLSzqirFDp153VLj77dZ` | `6276d2386bd3e5e138887c9fd355604ac5320dde` | 7.81 | 91 + 24 | 17 |

- **Verification and archiving (rule 33):** each leg was verified with `git ls-tree` (17 files, incl. `dispatch/<y>_P1.parquet` and
  `hourly/unit_marginal_<y>.parquet`) and its bytes checked out locally. All 7 shards are archived.
- **Composition:** `scripts/probes/_closeoutsppnuc_compose_span.py`, the composer that built the keeper. Every check passed: recipe
  identity per field, one sha, one surface, complete legs.
  - The runbook's `_miso260_compose_span.py` refuses SPP because of a MISO-only partition check.
- **Disclosures:**
  - The shard containers had no venv. Each shard ran `uv sync` (the declared install route) and edited no files.
  - Every leg logs a caught provenance-probe warning: `campd-unit-outages-maxgen-splitremap-SPP.csv` was never derived. The keeper's
    resolved inputs show the same `companions: None`, so this is not a deviation.

## 2. Gate table, keeper → control (`calibration_verdict.py`, rubric as on `main`)

| year | C1 fails | C3a | C3b NRMSE | C3c | C4 gas r / coal r | unserved MWh | year verdict |
|---|---|---|---|---|---|---|---|
| 2019 | — → — | **+12.3 % → +13.5 %** F | 0.160 → 0.172 | 0 h vs 47 | 0.966 → 0.938 / 0.953 → 0.919 | 0 → 0 | F → F |
| 2020 | — → — | +27.7 % → +27.8 % F | 0.345 → 0.346 F | 0 h vs 23 | 0.942 → 0.940 / 0.946 → 0.946 | 0 → 0 | F → F |
| 2021 | CC −8.92 / PRB +10.98 → −8.91 / +11.01 | +7.1 % → +7.1 % | 0.176 → 0.176 | 372 h vs 140 | 0.957 → 0.947 / 0.929 → 0.923 | 0 → 0 | F → F |
| 2022 | CC −9.16 / PRB +10.75 → −9.16 / +10.76 | −4.8 % → −4.8 % | 0.175 → 0.175 | 0 h vs 99 | **0.962 F** → 0.962 F (NRMSE 0.313) / 0.928 → 0.928 | 0 → 0 | F → F |
| 2023 | — → — | −6.4 % → −6.4 % | 0.176 → 0.175 | 0 h vs 42 F | 0.962 → 0.962 / 0.951 → 0.951 | 0 → 0 | F → F |
| 2024 | — → — | −11.2 % → −11.4 % F | 0.216 → 0.215 F | 0 h vs 59 F | 0.954 → 0.945 / 0.916 → 0.912 | 0 → 0 | F → F |
| 2025 | — → — | −4.3 % → −4.6 % | 0.153 → 0.167 | 0 h vs 68 F | 0.954 → 0.930 / 0.919 → 0.882 | 0 → 0 | F → F |

- **Other gates:**
  - C2 PASS → PASS.
  - C8 PASS → PASS (2022 ST_GAS grounded, 33.8 % → 33.8 %).
  - D-4 failure set identical: plant 3008 in 2019–21/23/24, 1230 in 2019, 6193 in 2024.
  - C5a 2019: +2.4 % → +5.1 %.
  - The 2025 plant-6064 D-4 flag in the per-leg check does not appear in the composed span.
- **Determination:** NOT-YET → NOT-YET.

## 3. Price error, split by masked hours (zero LP; hub-mean RT, `neighbor_lmp_hourly`)

| year | masked h | MAE all K → C | MAE masked K → C | bias masked K → C | mean ΔP masked | mean \|ΔP\| unmasked |
|---|---|---|---|---|---|---|
| 2019 | 828 | 11.77 → 11.85 | 9.07 → 9.84 | +1.55 → +3.79 | +2.24 | 0.105 |
| 2020 | 47 | 11.04 → 11.05 | 10.90 → 12.17 | −6.02 → −3.82 | +2.20 | 0.005 |
| 2021 | 142 | 31.47 → 31.39 | 20.69 → **16.23** | +3.40 → +3.33 | −0.08 | 0.035 |
| 2022 | 9 | 21.36 → 21.36 | 18.36 → 19.44 | +16.84 → +18.77 | +1.93 | 0.003 |
| 2023 | 36 | 13.68 → 13.67 | 22.37 → **19.35** | +3.35 → +1.36 | −1.99 | 0.009 |
| 2024 | 510 | 16.43 → **16.10** | 18.39 → **12.46** | +0.51 → +1.49 | +0.98 | 0.178 |
| 2025 | 698 | 16.68 → **16.09** | 24.07 → **16.40** | +0.57 → −0.69 | −1.26 | 0.203 |

$/MWh; K = keeper, C = control.

- **Masked-hour MAE:** it falls where the stale snapshot was large and long (2021 August, 2024, 2025). It rises in 2019, where the model
  now carries December's +2.9 TWh and was already biased high.
- **Unmasked hours:** they move ≤ 0.2 $/MWh. Attribution to the datafix is clean.

## 4. What changed and why

- **2019, C3a +1.2 pp, as predicted (PRECOMMIT §3.1).** SPP GenMix wind is 2.5 TWh below EIA's frozen `NG: WND`, and demand is +0.36 TWh.
  Of the 828 masked hours, 624 fall in Nov–Dec. The extra thermal energy goes to COAL_PRB (+1.4 TWh), CC (+0.7) and CT (+0.6), and price rises.
  The model reads closer to measured inputs and is further from the price benchmark. That is a discovered residual elsewhere (rule 14),
  not grounds to revert.
- **2025, C3a −0.3 pp, as predicted (§3.2).** Net load is −0.54 TWh (December freeze). PRB −0.4 TWh. Price moves down slightly.
- **2020–2023 are within the §3.3 bounds** (|ΔC3a| ≤ 0.1 pp, |ΔC3b| ≤ 0.001, C1 unchanged). The same holds for 2024: |ΔC3a| 0.2 pp.
- **C4 in 2019/2025** (see §0). For 2019, 2024 and 2025, gas-dispatch |Δ| averages 2.4–4.2 GW in masked hours vs 53–72 MW unmasked;
  77–84 % of the total change is in masked hours. The C4 actual there is the frozen EIA-930 record.
  - Re-basing the benchmark is the open rubric/desk question from `RESULT-uc-spp-datafix-2026-10-18.md` §4. It is not changed here
    (rule 37).
- **Mechanism matrix:** no verdict changes, so the SPP shard is not edited.

## 5. Where the bundles are, and what a promotion would cost

- **Composed span:** `results/calibration/uc_spp_control_span` is on `main` with this PR via a `.gitignore` negation (rule 34). It holds
  every year's `dispatch/`, `unit_marginal_<y>` and the `hourly/` sidecars. `unit_hourly_*` stays gitignored (rule 15).
- **Per-year legs:** gitignored here. They remain on shard branches `claude/uc-spp-control-<y>` (SHAs in §1) as transport, until the owner
  deletes them (a session cannot).
- **Promotion cost: zero LP.** It is one `promote_keeper.py --iso SPP --bundle results/calibration/uc_spp_control_span …` run, which:
  - attests (C6), carrying the keeper's exceptions ledger forward with C3c re-measured;
  - adds the `SPP_STALE_SNAPSHOT_REPAIR` DOF data-QA note automatically (epoch `2026-10-18b`);
  - designates, rebuilds status, and prunes `closeout_spp_nuc_span`.
- **Expected determination after attestation:** NOT-YET. The same criteria fail as for the incumbent, with 2019 C3a 1.2 pp worse.
- **Owner question:** promote this control as the SPP keeper (it is the faithful-input version of the incumbent; rule 14 favours it), or
  hold it as the control only? The local scoring registration (`2026-10-19-uc-spp-control`) was not committed.
