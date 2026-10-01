# PREREG — neiso-83: NEISO 6081 Stony Brook `CA1` classification

**Session:** neiso-83 · **Date:** 2026-08-05 · **ISO:** NEISO (rule 25 `[R-ISO-SCOPE]`)
**Keeper replayed:** `2026-08-04-neiso81-chpheatrate` (bundle `results/calibration/neiso81_chpheatrate_B`)
**Mechanism:** `ScenarioConfig.cc_steam_part_reclass` (NEW field, this PR — rule 28c)

**Pushed BEFORE either arm solves.** Every number in §1–§4 is measured with NO LP,
from committed artifacts, by `scripts/probes/_neiso83_stonybrook_ca1_phase0.py`
(record `results/calibration/_neiso83_stonybrook_ca1_phase0.json`). §5–§8 are the
properties, the stop triggers and the verdict ladder, fixed here.

---

## 1. Q1 — IS `CA1` MISCLASSIFIED IN THE LP? **YES, CONFIRMED.**

Read from the fleet built at the **keeper's own** `ScenarioConfig`
(`measured_ct_heat_rates=True`, `measured_chp_heat_rates=True`,
`cc_steam_part_capacity=False`) — never the loader defaults (the miso-116 trap).

| unit | fuel | plant_group | pmax MW | heat rate | VOM | CO2 t/MWh | NOx | EFORd |
|---|---|---|---|---|---|---|---|---|
| `6081_CA1` | **oil** | *(none)* | **96.0** | 10.60617891 | 4.50 | 1.00 | 4e-4 | 0.10 |
| `6081_CT1` | gas_cc | CC_REGULAR | 69.7 | 10.60617891 | 2.00 | 0.43 | 8e-5 | 0.05 |
| `6081_CT2` | gas_cc | CC_REGULAR | 69.7 | 10.60617891 | 2.00 | 0.43 | 8e-5 | 0.05 |
| `6081_CT3` | gas_cc | CC_REGULAR | 69.7 | 10.60617891 | 2.00 | 0.43 | 8e-5 | 0.05 |
| `6081_1` | oil | *(none)* | 65.0 | 10.60617891 | 4.50 | 1.00 | 4e-4 | 0.10 |
| `6081_2` | oil | *(none)* | 65.0 | 10.60617891 | 4.50 | 1.00 | 4e-4 | 0.10 |
| `6081_EDSI` | oil | *(none)* | 0.6 | 10.60617891 | 4.50 | 1.00 | 4e-4 | 0.10 |

`CA1` is the steam half of a 3×1 combined-cycle block whose three combustion
turbines sit in `CC_REGULAR`; it is dispatched as a standalone distillate unit.
All seven carried units share one heat rate — the eGRID **plant-average**, which
is why the class, not the rate, is the object here.

**Two corrections to the inherited framing, stated so they are not repeated.**

1. **The empty `plant_group` is NOT an anomaly.** It is what *every* oil unit in
   NEISO carries — 135 units / 5,181.5 MW, all empty — because the EIA-860 loader
   assigns a group only to coal and gas. Nothing is inferable from it.
2. **The 96.0 vs 105.0 MW "mismatch" is reconciled, not a discrepancy.** 96.0 is
   EIA-860 **net summer**; 105.0 is nameplate; the fleet's `pmax` rule is
   net-summer-else-nameplate. Both figures are correct on their own basis.

**Why the existing repair cannot reach it — population, not gating.** The
national CC-steam-part predicate is exactly **four** rows, and it splits in two:

| plant | gen | name | ES1 | `_map_fuel_type` | population |
|---|---|---|---|---|---|
| 55088 | ST1 | Dearborn (MI) | BFG | `None` | **DROPPED** → `cc_steam_part_capacity` |
| 54912 | STG1 | Martinez (CA) | OG | `None` | **DROPPED** → `cc_steam_part_capacity` |
| 1004 | ST | Edwardsport (IN) | SGC | `coal` | **CARRIED** → re-class population |
| 6081 | CA1 | Stony Brook (MA) | DFO | `oil` | **CARRIED** → re-class population |

`cc_steam_part_capacity` restores only rows the fuel map **drops**; a carried row
is outside its population entirely. That — not an ISO gate — is why neiso-80
measured a byte-identical armed fleet, and the cell stays `I` untouched (rule 28a).

---

## 2. Q2 — THE PHYSICALLY CORRECT REPRESENTATION

**Chosen: (a) fold `CA1` into its own block — re-class to `gas_cc` / `CC_REGULAR`
at the block's own eGRID heat rate.** Capacity unchanged; class, fuel, VOM, CO2
rate and EFORd move.

**Why the LP must not burn distillate in it.** A combined-cycle steam turbine has
no combustion path — it runs on HRSG exhaust. Measured, not assumed: plant 6081
meters **five** CEMS units in every train year (001/002/003 "Combined cycle" on
Pipeline Natural Gas, 004/005 "Combustion turbine" on Diesel Oil) and **no unit
for `CA1` in any year**. Every MMBtu the block burns is already metered at the
combustion turbines.

**Why this is not double-counting the block's fuel.** The incumbent heat rate is
the eGRID **plant-average**, whose denominator is the plant's whole net
generation — the steam part's output included. A per-MWh rate defined on the
block-total denominator, applied uniformly to every block MW, reproduces the
block's total fuel burn by construction. What the model does *today* is the
inconsistent case: it charges that block-denominated rate to only 209.1 MW of a
305.1 MW block, and prices the missing 96 MW off the distillate curve.

**Why (b) "carry `CA1` as a zero-fuel-cost unit" is rejected.** It is
self-consistent only if the CT siblings simultaneously move to a **CT-denominated**
rate (metered ≈ 12.6 MMBtu/MWh gross). Left on the block-denominated rate they
already carry, (b) would charge the block `10.606 × CT-MWh` instead of
`10.606 × block-MWh` and **under**-count its fuel. (b) is also two changes, not
one, and would be the only CC steam part in the model priced differently from
every other — every `NG`-coded `CA` row in all six ISOs is already `gas_cc` at its
plant's rate. (a) is what the model already does for every other combined cycle;
`CA1` is anomalous only because EIA-860 codes its energy source `DFO`.

---

## 3. Q3 — THE MEASURED IDENTIFICATION

**There is no parameter to identify.** The re-class consumes EIA-860's published
net-summer capacity (96.0 MW) and the incumbent eGRID plant heat rate. **Zero
fitted parameters, zero free parameters, no residual consulted.** The measurements
below establish that the machine is REAL and LIVE — presence evidence, never a
model input. Rule 13 `[R-MEASURED]`: prime mover, unit code, vintage and net
summer capacity are published inputs that regenerate for any forward year.

**Route A — direct (EIA-923 Page 1, 2018–2022).** EIA-923 reports the `CA` row's
own net generation, so the steam share is read, not inferred:

| year | CA net MWh | CT net MWh | steam share of block |
|---|---|---|---|
| 2018 | 28,493 | 74,992 | 0.2753 |
| 2019 | 12,916 | 31,837 | 0.2886 |
| 2020 | 27,121 | 67,926 | 0.2853 |
| 2021 | 15,378 | 37,453 | 0.2911 |
| 2022 | 29,558 | 74,498 | 0.2841 |

**mean 0.2849, sd 0.0060** — a textbook 3×1 steam fraction, and consistent with
`CA1`'s 96.0 / 305.1 = 0.315 capacity share.

**The decisive test — fuel inheritance.** If the steam part had a fuel of its own,
its EIA-923 fuel split would be independent of its siblings'. It is not:

| year | CA DFO share | CT DFO share | \|gap\| |
|---|---|---|---|
| 2018 | 0.4556 | 0.4684 | 0.0128 |
| 2019 | 0.0043 | 0.0206 | 0.0163 |
| 2020 | 0.0096 | 0.0080 | 0.0016 |
| 2021 | 0.0289 | 0.0319 | 0.0030 |
| 2022 | 0.3655 | 0.3872 | 0.0217 |

The `CA` row tracks whatever the block burned, across a 0.004→0.468 swing in the
block's own oil share. **EIA-860's `DFO` on that row is a duct / legacy label, not
a primary energy input.**

**Route B — indirect (2023–2025), and it is a proof, not an estimate.** The `CA`
rows go to 2,165 / 0 / 0 MWh while the `CT` rows' EIA-923 **net** generation
*exceeds* the CAMPD `CT` **gross**:

| year | E923 CA net | E923 CT net | CAMPD CC-CT gross | CT net ÷ CT gross |
|---|---|---|---|---|
| 2023 | 2,165 | 14,611 | 15,668 | 0.933 |
| 2024 | 0 | 41,098 | 30,611 | **1.343** |
| 2025 | 0 | 98,014 | 73,228 | **1.338** |

Net above gross is impossible for a CT-only row, so the zeros record a **reporting-
convention change** (the block folded into the `CT` row from mid-2023), not a
retired steam turbine. **The two routes agree:** applying route A's 0.2849 share to
route B's ratio implies a CT net/gross of **0.9601 / 0.9572** — an ordinary
auxiliary-load figure. Two independent instruments, one number.

---

## 4. THE ARM, MEASURED AT THE LOADER GRAIN BEFORE ANY SOLVE

**Fleet delta — exactly one unit, capacity conserved:**

`6081_CA1`: `fuel_type` oil→gas_cc · `plant_group` ""→CC_REGULAR ·
`efficiency_bin` default→older · VOM 4.50→2.00 · CO2 1.00→0.43 ·
NOx 4e-4→8e-5 · EFORd 0.10→0.05. **`pmax` and `heat_rate` unchanged.**
Fleet total 24,209.58 MW both arms. Class capacity: oil 5,181.5 → 5,085.5;
CC_REGULAR 12,392.0 → 12,488.0.

**Rule 25 proven by running it, not reading it:** with the flag armed, ERCOT
(1,450), CAISO (782), PJM (1,922), MISO (1,975) and NYISO (460) fleets are
**byte-identical**. MISO 1004 Edwardsport — the one other member of the re-class
population, and a genuine 555 MW IGCC machine — stays `COAL`.

**The outage-denominator leg, disclosed in advance because it dominates.** The
CAMPD unit-outage overlay derates `(plant_code, plant_group)` by
`removed_mw / plant_capacity_mw`, and that denominator is read off the same fleet
(`outages._iso_plant_capacity`). It therefore has to move with the flag, or the
overlay removes the wrong absolute MW. **This is not a second mechanism — it is
the same mechanism's own denominator** (a 152 MW 2024 outage against a 209.1 MW
denominator would remove 72.7 % of an armed 305.1 MW bin = 221.8 MW, 46 % more
than went out). Denominator 209.1 → 305.1 MW; measured effect on the block's
effective available capacity:

| year | mean avail off → armed | effective MW off → armed | capacity leg | denominator leg |
|---|---|---|---|---|
| 2023 | 0.0000 → 0.0000 | 0.0 → 0.0 | +0.0 | +0.0 |
| 2024 | 0.2953 → 0.5128 | 61.7 → 156.4 | **+28.3** | **+66.4** |
| 2025 | 0.1935 → 0.4400 | 40.5 → 134.2 | **+18.6** | **+75.2** |

**Three things this table says, all against interest.**

1. **2023 cannot move through this plant at all.** The block is derated to zero in
   all 8,760 hours in BOTH arms, so any 2023 `CC_REGULAR` change is system
   re-dispatch displacing the 96 MW that left `oil`, never 6081 output.
2. **The denominator leg is ~70–80 % of the effect.** The arm is not
   "+96 MW of CC"; most of the available-capacity move is the derate basis
   correcting alongside it.
3. **THE CHARTER'S MAGNITUDE EXPECTATION IS WRONG AND IS CORRECTED HERE.** The
   charter anticipated "< 0.15 % of CC_REGULAR". The measured effective-capacity
   change is materially larger than that, for the reason in (2). Stated before the
   solve so the finding cannot be read as retrofitting the expectation.

**The root cause the denominator leg exposes, NAMED AND NOT FIXED (rules 19, 21,
25).** The reason 6081's CC bin is derated at all in 2024/2025 is that
`campd-unit-outages-NEISO.csv` carries units **004/005 — the plant's DIESEL
peakers — with `plant_group = CC_REGULAR`.** They land there because `oil` carries
no `plant_group`, so the outage overlay cannot represent an oil unit's outage and
the deriver routes it to the plant's only modelled group. In 2024 and 2025 those
two units are the **only** source of 6081 outage rows, while the CC block's own
units 001/002/003 have **none** — so the model derates a fully-available CC block
to 29.5 % / 19.4 %. That is a pre-existing, ISO-agnostic defect in a different
mechanism, it needs a fleet-taxonomy change with six-ISO blast radius, and this
session does **not** touch it. The armed denominator moves the block *toward*
physical truth (~100 % available) rather than away from it, which is why rule 14
`[R-ACCURATE]` says take the consistent basis and open the root cause rather than
bury it in an inconsistent one.

**Rule 23 `[R-FROZEN-DERIVE]` is NOT engaged.** The outage deriver's own inputs at
6081 (`group_by_code`, `groups_by_code`, `steam_np_by_code`) are **identical**
under both arms, so the committed extract would re-derive byte-for-byte. No
artifact is regenerated.

---

## 5. CONSTRUCTION PROPERTIES — all must hold, or the run is INVALID

* **P1 flag fidelity.** Arm A's `run_config.json` records
  `cc_steam_part_reclass: false`; arm B's records `true`.
* **P2 fleet grain.** Exactly one unit differs between the arms' fleets; total
  `pmax` equal to within 0.05 MW; `6081_CA1.heat_rate` identical in both.
* **P3 ISO scope.** The other five ISOs' fleets byte-identical under the armed
  flag (already measured; re-asserted at solve time).
* **P4 — FIRING AT THE ENERGY GRAIN, not the loader grain.** The arm's `oil`
  class annual energy must differ from the control's by **> 0.001 TWh in at least
  one year**. This is the miso-126 wiring-gap guard: a byte-identical arm means
  the flag never reached the LP, which is **INVALID** (the mechanism was never
  applied), *not* "the mechanism is inert". A loader-level check cannot
  substitute.
* **P5 conservation.** Per-hour relative residual of the full identity
  (`class_hourly` + storage vs `system`) ≤ 1e-6 in both arms, all years.
* **P6 system integrity.** Total generation within ±0.05 % of control; slack and
  dump not rising in any year.

## 6. DIRECTIONAL EXPECTATIONS — reported, NEVER gates

Rule 1 `[R-STRUCT]`: a structurally correct mechanism stays in whether or not the
residual moves, so nothing below can reject the arm.

* **S1** `oil` annual energy falls in 2024 and 2025 (2023 may be ~unchanged: the
  block is fully derated, so only the merit-order position of the 96 MW moves).
* **S2** `CC_REGULAR` annual energy rises in 2024 and 2025.
* **Hard physical ceilings** on the 6081 contribution, from §4: ≤ 156.4 MW ×
  8,760 h = **1.370 TWh** (2024) and ≤ 134.2 × 8,760 = **1.176 TWh** (2025);
  **exactly 0** in 2023.

## 7. STOP-AND-ESCALATE TRIGGERS (rule 22 D-5(b))

NEISO holds a `complete` marker, so a promotion re-keys
`calibration-complete.json` **with a determination re-verification**, and a worse
determination **stops the promotion and escalates to the owner** — it is never
silently written.

* **N1** determination worse than **CALIBRATED-WITH-CAVEATS**.
* **N2** any criterion crossing PASS → FAIL.
* **N3** C3c degrading from its ledgered caveat, or a new caveat slot spent.
* **N4** total generation moving > ±0.05 %, or slack / dump rising in any year.

## 8. VERDICT LADDER, fixed before any solve

| branch | condition | outcome |
|---|---|---|
| **V1** | **P4** falsified | **INVALID** — the flag never reached the LP. Fix the wiring, re-solve. **No cell verdict is minted** and nothing is called inert. |
| **V2** | P1 / P2 / P3 / P5 / P6 falsified | **INVALID** — statistic re-scoped, arms re-solved. No verdict. |
| **V3** | all P hold · none of N1–N4 fires | **`K` — PROMOTE.** On rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]` / 14 `[R-ACCURATE]`: a zero-DOF correctness fix that stops the LP burning distillate in a machine with no combustion path. **A correct-and-inert outcome promotes on this branch too** — the size of the residual move is reported, never required. |
| **V4** | all P hold but any N fires | **STOP-AND-ESCALATE to the owner; keeper UNCHANGED.** Cell stays `O` with the escalation recorded (the nyiso-120 precedent). Recommendation stated on the owner's standing standard of 2026-08-04 — *"if structural integrity improves but gates regress that may still be a keeper"* — but the call is the owner's. |

## 9. RECIPE

* Same-HEAD replay via `scripts/replay_keeper.py` on the designated keeper bundle
  `results/calibration/neiso81_chpheatrate_B`.
* **`--years 2023 2024 2025` in ONE invocation per arm** (rule 16 `[R-ALLYEARS]`);
  never a per-year chain, which writes `meta.json` with only the last year.
* **Arm A — `neiso83_control_A`:** zero-delta, no `--set`. Solved and quoted
  first (miso-124: price response is not stable across keepers, so the control is
  the only admissible baseline).
* **Arm B — `neiso83_ca1reclass_B`:** `--set cc_steam_part_reclass=true`.
* Post-solve: `dashboard_add_run.py` (both arms, rule 15) → `legitimacy_diagnostics.py`
  → attestation + DOF ledger → `calibration_verdict.py --run-id … --write-metrics`
  → the A/B scorer `scripts/probes/_neiso83_ca1reclass_ab.py`.

## 10. GOVERNANCE

* **Rule 22 `[R-HOLDOUT]`** — `--year` strictly **{2023, 2024, 2025}**. The
  holdout spend freeze is ACTIVE and outranks every marker. NEISO's locked test is
  **SPENT and never re-grantable** (2026-07-07); its absence from `final` is not a
  pending grant. EIA-923 2018–2022 is read here as **source data for a physical
  share measurement** — no year outside 2023–2025 is solved, scored or registered.
* **Rule 15 `[R-DASHBOARD]`** — both arms registered in-session, keeper or not.
* **Rule 16 `[R-ALLYEARS]`** — 2023 + 2024 + 2025, one bundle per arm.
* **Rule 19 `[R-ONE-MECH]`** — one mechanism. The outage-denominator basis is the
  same mechanism's own input, not a second one; the deriver's oil-peaker routing
  is named as an open root cause and left alone.
* **Rule 20 `[R-DOF]`** — one new DOF-ledger entry, **zero free parameters**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no artifact re-derived; proven unnecessary.
* **Rule 24 `[R-REGISTRY]`** — the arming is a `ScenarioConfig` field visible in
  `run_config.json`; no env var, no hardcoded per-plant dict.
* **Rule 25 `[R-ISO-SCOPE]`** — NEISO-only, ISO-gated on
  `CC_STEAM_PART_RECLASS_ISOS`, cross-ISO invariance measured. MISO's Edwardsport
  is deliberately out of the registry.
* **Rule 27 `[R-PUSH]`** — Opus; every push touching a file ≥ 300 lines is
  blob-verified immediately after.
* **Rule 28 `[R-MECH-MATRIX]`** — the new field's matrix row lands in the same PR
  (28c) and the cell is stamped in this session whatever the outcome (28b).
  `cc_steam_part_capacity` is **not** re-armed and its `I` is **not** re-stamped
  (28a).
