# RESULT — NWPP-NEXT-27: WECC Path 76 served at its measured bilateral leg, 2019–2025

- PRECOMMIT: `PRECOMMIT-nwppnext27-path76-served-2019-2025-2026-10-03.md`.
- Phase 0: `FINDING-nwppnext27-cc-conduct-path76-phase0-2026-10-03.md`.
- Run `2026-10-03-nwpp-next-27-path76`; bundle `results/calibration/nwppnext27_span`, composed from seven legs.
- Control: keeper `2026-10-03-nwpp-next-26-nevp`, read from its committed bundle.

## Legs (pin `440ad14416cbfd3399e4877a17e7c974c4862fb9`, branch `claude/nwppnext27-pin`; prompts at `d1ceac5c`)

| year | leg SHA | branch | wall |
|---|---|---|---|
| 2019 | `2a49781d62e80445beef6ba50233807aa51585f0` | `claude/nwppnext27-2019` | 73 min |
| 2020 | `616f587621fff1d29cd4632574d82836f4bf4af7` | `claude/nwppnext27-2020` | 29 min |
| 2021 | `76d0e99a63c72002d0a97e77e5b6cf4e6d385695` | `claude/nwppnext27-2021` | 34 min |
| 2022 | `59f50de5dd4c34081a6dc69cdd30788804278ca8` | `claude/nwppnext27-2022` | 21 min |
| 2023 | `1a3ad1c492406138ae2f44769cdd4262ecdfb0eb` | `claude/nwppnext27-2023` | 27 min |
| 2024 | `045f4ca98268e3b766a929ecbf07df8cabcd2994` | `claude/nwppnext27-2024` | 22 min |
| 2025 | `d27464d319b696c6cc9da016aa220441664df25e` | `claude/nwppnext27-2025` | 17 min |

- **Parents.** Every leg sits on the pin. `git diff 440ad144 <leg> -- src scripts tests data configs` is empty for
  all seven.
- **Checks re-run on each leg's bytes:**
  - Hard stops a–h held in every year.
  - The scenario-config diff against the keeper is `[('nwpp_path76_alturas_link', True, False),
    ('nwpp_path76_served_schedule', None, True)]`. It also carries `('zonal_loss_demand_reconciliation', None, False)`,
    a default-off field added on main after the keeper solved. The parent waived it as INERT (PRECOMMIT G-DRIFT).
  - Zonal P1 demand matches the FINDING §E table.
  - There are zero NW↔SNV flow rows.
  - The served leg ranges from −0.177 to −0.610 TWh.
- **Unserved energy:** zero in every year except 2023, where the keeper already had it: NW 24.97, INLAND 3.09 and
  SNV 1.62 GWh, against 25.33 / 3.09 / 1.26.
- **Merge before promotion.** `origin/main` e8570532 was merged into the branch. It brought
  `caiso_dsw_daytime_lateevening_unprinted_arm`, which is CAISO-only and default off, and the UC-MILP text in
  CLAUDE.md. Both are INERT for this bundle.

## What moved (P1, TWh, NEXT-27 against the keeper)

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---:|---:|---:|---:|---:|---:|---:|
| CC_REGULAR | −0.12 | +0.09 | +0.15 | +0.32 | −0.65 | −0.62 | −0.22 |
| CT_PEAKER | +0.10 | −0.08 | −0.07 | +0.08 | +0.31 | +0.09 | −0.08 |
| CC_CHP | −0.09 | −0.01 | −0.09 | −0.13 | −0.03 | 0.00 | +0.04 |

**Zonal prices, 2024.** SNV moves 27.71 → 27.37 $/MWh and NW moves 30.58 → 31.10.

**Seam exports, 2024.** COI moves 8.97 → 8.60 TWh, BC 11.36 → 10.81 and NEVP 10.13 → 10.35.

**What the cut actually did (2024 network sidecars).**
- Path 76's 2.20 TWh of SNV→NW export is gone. SNV re-routes about 0.9 TWh of it:
  - SNV→INLAND (Path 16) +0.21 TWh;
  - net SNV→EAST +0.65 TWh;
  - the NEVP seam +0.22 TWh.
- NW replaces the lost import mainly over INLAND→NW (+0.96 TWh). INLAND is fed by EAST→INLAND (+0.41 TWh), which
  draws on the EAST CCs, and by lower COI and BC exports (−0.37 and −0.55 TWh). The 2023 picture is the same.
- So the CC_REGULAR cut is small: −0.6 to −0.7 TWh in 2023–2024, the low end of the PRECOMMIT range, and −0.12 TWh in
  2019, below the range.
- The rest of the 2024 over-run is the conduct gap in FINDING §C.

## Gate (b): verdict diff against the keeper (same bench render)

Both runs are NOT-YET. **FAIL records 7 → 7, zero flips.**

| record | keeper | NEXT-27 |
|---|---|---|
| C1 CC_REGULAR 2024 (FAIL) | +12.77 | +12.15 |
| C3a 2024 (FAIL) | −10.30 $/MWh | −9.96 |
| C3b 2023 / 2024 (FAIL) | 0.209 / 0.772 | 0.202 / 0.767 |
| C4 gas 2019 / 2023 / 2024 (FAIL) | r 0.669 / 0.533 / 0.797 | r 0.679 / **0.530** / 0.803 |
| C1 CC_REGULAR 2019 / 2023 / 2025 | +7.61 / +1.31 / +6.82 | +7.50 / +0.66 / +6.60 |
| C3a 2023 | −1.46 | −0.52 |
| C4 gas 2020 / 2025 | r 0.822 / 0.828 | 0.828 / 0.833 |
| C2 gas 2024 | +11.43 | +10.79 |

**Regressions, all PASS, at full magnitude:**
- C1 CC_REGULAR 2020 +2.39 → +2.48, and 2021 +2.99 → +3.15.
- C1 CT_PEAKER 2020 −0.82 → −0.90, 2021 −1.54 → −1.61, 2023 +0.02 → +0.33, and 2024 +1.47 → +1.56.
- C1 CC_CHP 2019 −0.35 → −0.44, 2021 −0.82 → −0.90, and 2022 −0.04 → −0.17.
- C1 ST_GAS 2024 −2.90 → −3.02.
- C3a 2025 +0.10 → +0.22.
- C2 gas 2023 −0.13 → −0.53.
- C4 gas 2023 r 0.533 → 0.530; its NRMSE improves, 0.359 → 0.352.
- SNV unserved energy 2023 rises from 1.26 to 1.62 GWh.

## Gate (c): rule 20 and legitimacy

- **D-2.** Forced share is 0 in every class-year. PASS.
- **D-1.** It stays at 18 failure lines. 2022 ST_GAS clears (r 0.735 → ≥ 0.8), and 2021 ST_GAS r 0.794 is new. The
  coal lines move by ≤ 0.05 in r.
- **C6.** PASS. The attestation comes from `scripts/gen_nwppnext27_attestation.py`, which is the NEXT-26 chain with the
  Path 76 link replaced by the served key. It adds zero free parameters.

## §Promotion (2026-10-04)

- **Ruling:** owner card "Promote (Recommended)". The close-out desk (session_01ERkBTm23ZAP4CTZnJVD9Ss) holds the NWPP
  slot for this lane.
- **Promotion command:**
  `promote_keeper.py --iso NWPP --bundle results/calibration/nwppnext27_span --label "nwpp next 27 path76"`. It ran
  register, attest, DOF ledger, re-key (`keepers/NWPP.json` and the `program-status.json` gate-(a) marker), status
  rebuild, audit with E13 tolerated, prune of `2026-10-03-nwpp-next-26-nevp` / `nwppnext26_span`, strict audit (clean),
  and parity (OK: 9 runs, 9 bundle dirs).
- **`keepers/NWPP.json` `superseded`.** It is rewritten to name the NEXT-26 keeper (the desk's follow-up). The earlier
  NEXT-26 and NEXT-24 entries move into the `promotion_note` PRIOR chain. `audit_keepers.py --iso NWPP --check` passes.
- **Not deleted:** `gen_nwppnext26_attestation.py` and its chain, because `gen_nwppnext27_attestation.py` imports them.
