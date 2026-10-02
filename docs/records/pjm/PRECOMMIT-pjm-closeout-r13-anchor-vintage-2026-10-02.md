# PRECOMMIT — PJM close-out R-13: `gas_offer_margin_anchor_vintage` retest with a displacement-aware S4 (written ex ante)

Lane `closeout-PJM` (branch `claude/closeout-pjm-wave1`), 2026-10-02. Plan `docs/backcast-closeout-plan-2026-10.md` §3.6 step 3; owner ruling **R-13** (§5.0: "re-charter the `gas_offer_margin_anchor_vintage` retest with a displacement-aware S4 written ex ante"). **No solve is authorised by this document**: solves HOLD until the W0 lane (`claude/closeout-b-w0-foundation`) merges and the desk releases the lane.

## 1. Mechanism and why it is re-tested (rule 28: the new evidence)

`ScenarioConfig.gas_offer_margin_anchor_vintage` (pjm-169 F4, built, default off) resolves the PJM gas-offer margin anchor to the **solve year's own** delivered-gas mean instead of the frozen 2023–2025 window mean `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["PJM"] = 3.3483 $/MMBtu`. The reform `mc += markup_hr × (anchor − fuel)` then reduces to the registered band multiplier at each year's own mean gas, instead of extrapolating the training-window identification point into 2019–2022.

Cell `R` (2026-09-07) was set by S4 alone: "Non-gas classes each move < 1.0 % in annual energy" failed on COAL_BIT +3.28 %. The record itself says S4 "probably cannot separate the coal-sigmoid confound … from ordinary merit-order displacement (raising every gas offer $10.57/MWh MUST push dispatch to the next unit up, which in PJM is coal)" and licenses "a displacement-aware footprint gate, but only in its OWN precommit, before its OWN solve". The new evidence: the keeper changed on every input pjm-169's control used (DA-virtual settlement, RGGI, measured HR, year-matched vintage, exit cohort, OVEC) and 2019–2022 entered the span — C3a 2020 (+12.4 %) and C3a 2022 (−11.5 %) both FAIL, and the mechanism moves them in opposite directions (table §3).

**Rule 13.** The anchor is the solve year's own delivered-gas mean: a forward year computes it from its own forecast gas. Zero free parameters (the anchor is an identification point, `derive_gas_offer_margin_anchor.py`). **Rule 19.** It replaces the frozen anchor in the same term; nothing stacks.

## 2. Exact config delta

One field on the incumbent recipe: `--set gas_offer_margin_anchor_vintage=true`. Everything else is identical to the control (§4). Full span 2019–2025, one shard per year (rules 16, 29, 36).

## 3. Zero-LP phase 0 (done; `scripts/probes/_pjmco_r13_anchor_vintage_delta.py` → `results/phase0/pjm/_pjmco_r13_anchor_vintage_delta.json`)

| year | HH | resolved anchor | − frozen 3.3483 | predicted median gas-tranche mc shift (markup_hr 2.804, pjm-169 §7.3) |
|---|---|---|---|---|
| 2019 | 2.57 | 3.2046 | −0.144 | −$0.40 |
| 2020 | 2.03 | 2.4841 | −0.864 | **−$2.42** |
| 2021 | 3.72 | 4.1094 | +0.761 | +$2.13 |
| 2022 | 6.45 | 7.1208 | +3.773 | **+$10.58** |
| 2023 | 2.54 | 3.2551 | −0.093 | −$0.26 |
| 2024 | 2.19 | 2.8556 | −0.493 | −$1.38 |
| 2025 | 3.52 | 3.9567 | +0.608 | +$1.71 |

Identity check: 2022 reproduces pjm-169 S1 exactly (7.1208; predicted +$10.58 vs the +$10.57 it solved). The 2023–25 training years move by ≤ $1.4, so the training tier is touched only second-order; 2020 moves the C3a-correct way (down) by about the −$2.5 the research shard sized as needed (`SHARD-PJM` §2 C3a 2020 row).

## 4. Control

Rule 29(b): no control solve. Control = the **post-W0 PJM incumbent span** — the keeper bundle if W0's PJM re-baseline is promoted, else the W0 lane's PJM span at its recorded SHA. G-DRIFT from that SHA to the arm SHA is a zero-LP hunk audit; any LIVE hunk other than this field earns a control solve before the arm is read. The current keeper (`pjmnext16_A_span`, `6d4c7749`) is **not** a valid control once W0 lands (W0 changes every ISO-year's fleet).

## 5. Gates — fixed now, before any number

STOP gates (structural; any failure kills the arm, nothing promoted):

| # | gate | pass condition |
|---|---|---|
| S1 | identity | each year's resolved anchor equals §3's value to 1e-4 $/MMBtu |
| S2 | stated identity | at `fuel == anchor`, every gas tranche's `mc` equals the registered band multiplier to 1e-6 $/MWh (unit tests, as pjm-169) |
| S3 | direction & size | per year, the arm−control median gas-tranche `mc` delta has §3's sign and lies in [0.5×, 2.0×] of §3's prediction (years with |prediction| < $0.5 — 2019, 2023 — check sign only if |delta| ≥ $0.1, else PASS as inert) |
| **S4a** | **footprint, offers** | every NON-gas unit's P1 `mc` is identical arm vs control (max abs Δ ≤ 1e-6 $/MWh in every unit-hour of `unit_marginal_<y>`). This is the confound test pjm-169's S4 could not do: if coal offers move, the anchor leaks into coal pricing and the arm is killed |
| **S4b** | **footprint, energy (displacement-aware)** | (i) nuclear, wind, solar, hydro, biomass, OTHER each move < 1.0 % of annual energy; (ii) the coal + gas-ST + oil energy change has the sign OPPOSITE the gas-CC+CT change in every year with |§3 shift| ≥ $1 (displacement, not creation); (iii) ≥ 80 % of the |ΔCOAL| TWh falls in plant-hours where the control's coal unit `mc` lies within |shift| + $2/MWh of the control's own zonal price that hour (`system_<y>.parquet`; the merit-order flip band a gas shift of that size can cross, with $2 for the P1 ladder step); (iv) |ΔCOAL| ≤ |ΔGAS| TWh |
| S5 | no non-target flip | C2, C4 and C8 do not go PASS → FAIL in any year; C1 classes other than CC_REGULAR / CT_PEAKER / COAL_* do not go PASS → FAIL |

Pre-fixed outcome reading (reported, not a kill gate; promotion is on structure per rule 1 and is the owner's call): **C3a 2022 ≥ −10 %, C3a 2020 ≤ +10 %, COAL_BIT 2022 stays PASS**, and C3a 2023–2025 stay inside ±10 %. C3a is read on whatever PJM basis is in force at scoring (lane closeout-C implements the zonal load-weighted basis, R-13 second half); both bases are reported if both exist.

## 6. Out of scope

The coal-sigmoid `ceil` extrapolation (pjm-170 R) — not touched; `gas_offer_margin_zonal_anchor_vintage` (U) — a different field; any band-multiplier value (rule 1 channel) — unchanged.

## 7. Cost

7 shards (one per year), ≈ the keeper's per-year runtime; zero new parameters (DOF ledger unchanged).
