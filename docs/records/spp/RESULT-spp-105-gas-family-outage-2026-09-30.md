# RESULT — SPP-105: gas-family outage carriers A and B, solved

- **Lane:** SPP-105, on the owner card "Build carrier a and b".
- **PRECOMMIT:** `docs/records/spp/PRECOMMIT-spp-105-gas-family-outage-2026-09-30.md` (pin `5e0599c8`, Addendum A).
- **Control:** keeper `2026-09-28-spp-100-chp-scope` (rule 29(b) form 4).
- **Arms:**
  - **A:** `wefor_residual 0.0` + `wefor_residual_groups` CC/ST (existing fields). Run `2026-09-30-spp105-wefor-off-covered`, bundle `spp105A_span`.
  - **B:** `spp_gas_crow_residual_outage` (new field). Run `2026-09-30-spp105-b-crow-residual`, bundle `spp105B_span`.
- **Solve:** 14 year-isolated shards (rule 36). The parent ran no LP.
  - Every leg passed `_spp105_shard_check.py` in its shard and again in the parent.
  - Each composite was built with `_rspp_compose.py --require` and attested with `gen_spp105_attestation.py`, which confirms the offer curve and every other scenario field are byte-identical to the keeper.

## 1. What each arm did (arm − keeper)

| year | A: Δprice $/MWh | A: ΔCT / CC / ST / PRB TWh | B: Δprice $/MWh | B: ΔCT / CC / ST / PRB TWh | unserved MWh: keeper / A / B |
|---|---:|---|---:|---|---|
| 2019 | −0.21 | −0.54 / +0.76 / +0.70 / −0.78 | +0.42 | +0.52 / −0.81 / −0.93 / +1.10 | 0 / 0 / 0 |
| 2020 | −0.23 | −0.68 / +0.90 / +0.88 / −0.92 | +0.23 | +0.12 / −0.22 / −0.62 / +0.67 | 0 / 0 / 0 |
| 2021 | −0.78 | −0.36 / +0.22 / +0.39 / −0.22 | **+5.98** | +0.52 / −0.09 / −0.58 / −0.02 | 0 / 0 / 0 |
| 2022 | −0.43 | −0.42 / +0.17 / +0.41 / −0.15 | +0.25 | +0.07 / +0.02 / 0.00 / −0.13 | 0 / 0 / **979** (3 h, Sep) |
| 2023 | −0.32 | −0.70 / +0.64 / +0.83 / −0.70 | +0.21 | +0.27 / −0.23 / −0.46 / +0.39 | 0 / 0 / 0 |
| 2024 | −0.99 | −1.00 / +0.48 / +1.38 / −0.77 | **+6.75** | +0.81 / −1.04 / −1.59 / +1.62 | 862 / 0 / **65,212** (37 h; Apr, Aug–Oct) |
| 2025 | −0.58 | −0.80 / +0.32 / +0.99 / −0.48 | **+2.93** | +0.30 / −0.13 / −0.30 / +0.01 | 136 / 0 / **20,231** (25 h, Apr) |

Carrier B's gas outage equals SPP's published total in the binding hours. In SPP's high-outage shoulder months that leaves the
model's fleet short of load, and **most of B's price move is scarcity at the slack price**, not merit order (the SPP-32 failure
mode). The 2021 move is Uri, non-linear, as the zero-LP instrument warned.

## 2. Scores (`calibration_verdict.py`), keeper → A → B

| year | tier | C3a mean LMP | C3b NRMSE | C3c >$200 h (RT) |
|---|---|---|---|---|
| 2019 | validation | +11.5 → +10.5 → +13.5 % | 0.146 → 0.138 → 0.161 | 0 → 0 → 1 (47) |
| 2020 | validation | +27.5 → +26.2 → +28.9 % | 0.343 → 0.332 → 0.356 | 0 → 0 → 0 (23) |
| 2021 | validation | +6.5 → +4.4 → **+22.5 %** | 0.184 → **0.227** → **0.415** | 352 → 334 → 385 (140) |
| 2022 | validation | −5.8 → −6.8 → −5.2 % | 0.184 → 0.190 → 0.182 | 0 → 0 → 3 (99) |
| 2023 | train | −6.7 → −8.0 → −5.9 % | 0.172 → 0.175 → 0.169 | 0 → 0 → 0 (42) |
| 2024 | train | −8.6 → **−12.5 %** → **+17.9 %** | 0.172 → **0.215** → **0.433** | 7 → 1 → 54 (59) |
| 2025 | train | −5.4 → −7.4 → +4.9 % | 0.146 → 0.149 → **0.415** | 2 → 0 → 32 (68) |

**Train tier 2023–25 (keeper: CALIBRATED, lone ledgered C3c):**
- **A → NOT-YET.** C3a 2024 fails (−12.5 %, outside ±10 %) and C3b 2024 fails.
- **B → NOT-YET.** C3a 2024 (+17.9 %), C3b 2024 and 2025, and C1 2024 ST_GAS (−9.23 TWh) all fail.

## 3. Expectations (PRECOMMIT §5)

| # | expectation | arm A | arm B |
|---|---|---|---|
| E1 | shard check PASS ×7 | **PASS** | **PASS** |
| E2 | Optimal within budget | **PASS** | **PASS** |
| E3 | unserved not up > 500 MWh | **PASS** (0 in every year; the keeper's 862 / 136 MWh in 2024 / 25 go to 0) | **FAIL** (+979 / +64,350 / +20,095 MWh in 2022 / 24 / 25) |
| E4 | no new D-4 FAIL row (keeper 7) | **FAIL by one knife-edge row**: 2021 `coal_mustrun` plant 6095, the same row SPP-104 tripped | **PASS** (7, identical set) |
| E5 | train stays CALIBRATED, no C1/C3a/C3b/C4 flip 2023–25 | **FAIL** (C3a and C3b 2024) | **FAIL** (C1, C3a and C3b 2024; C3b 2025) |
| E6 | rule-14 gas outage vs SPP published | **FAIL** (zero LP: \|gap\| worse in 5 of 7 years) | pass **by construction** (the pin); not evidence |

## 4. Recommendation (pre-registered rule, PRECOMMIT §6)

**RECOMMEND AGAINST promoting either arm.**
- **Arm A:** E4, E5 and E6 fail.
  - The repair moves every year's price down; it breaks the 2024 price band.
  - It moves the keeper away from SPP's own measured gas outage. The statistical WEFOR on CC / ST is standing in for the sub-5-day
    outages the CAMPD windows miss, so removing it is not a structural improvement (rule 14).
- **Arm B:** E3 and E5 fail.
  - Pinning gas outage to SPP's published total leaves the model short of capacity in 2024 / 25 shoulder hours: 85 GWh of
    unserved energy.
  - Its train-tier price moves are that scarcity, not a better merit order.
  - The pin itself (rule 13) was the owner's override on record. The solve shows it does not deliver.
- **Reading carried forward.** The keeper's gas outage is not what is short in 2023–25.
  - Adding SPP's measured outage on top of the keeper's CAMPD events over-removes capacity. The model's fleet and SPP's CROW
    fleet are not the same boundary for gas in the shoulder months, which is itself a rule-14 finding.
  - The upper-tercile price shortfall should be looked for on the offer / commitment side (the MMU Dec 2025 classes: reliability
    commitment status, emergency-max shortfall), not in outage availability.
- The owner decides (rule 31).

## 5. Retrievability (rules 33(d) / 34(e))

- **Both composites** (`results/calibration/spp105A_span`, `spp105B_span`) are in this lane's working tree, **not committed**.
  - Each is registered locally (sidecar + payload); both wait on the owner's ruling.
  - They do not survive the session unless the owner promotes one.
- **Leg provenance** (shard branches; transport, not a recovery route):

| arm | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| A | `c9b62bf7` | `f115050d` | `85a6fad8` | `dbf35472` | `a2408f5d` | `db84644b` | `91568bd2` |
| B | `ffb0556a` | `a946520e` | `2263174a` | `ebde702b` | `4a91fb5b` | `a8db9065` | `a11d183b` |

- **Cost to reproduce** if the working tree is lost: ~12–15 min wall per arm across seven parallel shards.
- **Shards:** all 14 are archived. Three first launches never received a container; they were archived and relaunched, with no
  work lost.

## 6. Rules

- **1:** judged on structure; neither arm is selected on a residual.
- **13:** B's pin is declared and measured, and it fails.
- **14:** A fails E6; B shows a boundary misalignment.
- **19:** both arms replace, never stack.
- **21:** zero free parameters.
- **25:** SPP only.
- **29(b):** the keeper is the control; G-DRIFT all INERT.
- **31–36:** the parent solved nothing; bytes were in hand before archive; one year per shard.

## 7. Owner ruling (2026-09-30)

**"Don't promote (Rec.)."** Keeper `2026-09-28-spp-100-chp-scope` stands (train tier CALIBRATED).

- **Code.**
  - `spp_gas_crow_residual_outage` stays in the code, default off.
  - Carrier A needed no code: it is the existing `wefor_residual` fields.
  - The SPP matrix cells `spp_gas_crow_residual_outage` and `wefor_residual` go O → **R**, with the reading in §4.
- **Local artifacts.** Both local registrations (sidecars and payloads) were removed before any commit, under rule 15
  keeper-only retention and rule 31 trigger (i). The composites `spp105A_span` / `spp105B_span` and the 14 legs were never
  committed to `main`. This doc and git history are the record.
- **Data.** `data/raw/spp-gen-outage/` (SPP's published hourly outage by fuel, 2019–2025) stays committed as a measured input
  for future diagnostics.
