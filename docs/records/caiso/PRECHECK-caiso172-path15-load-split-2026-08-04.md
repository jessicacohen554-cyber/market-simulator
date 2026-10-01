# PRECHECK — caiso-172: the MEASURED Path-15 split of PG&E TAC load

**Session** caiso-172 · **Date** 2026-08-04 · **Branch**
`claude/caiso172-subtac-load-survey-8ty8zu` · **Base** `aaf1ecea`

**Incumbent CAISO keeper** `2026-08-04-caiso-166-measured-dlap`
(CALIBRATED-WITH-CAVEATS; 2 owner-ledgered caveats, 0 FAILs; `audit_keepers
--iso CAISO` PASS). CAISO holds **no** `complete` marker, and the holdout spend
freeze is ACTIVE. This session solves **2023 / 2024 / 2025 only**.

**Matrix row** — `CAISO_TAC_ZONE_WEIGHTS` is a `constants.py` table, **not** a
`ScenarioConfig` field, so the rule-28 gap sweep cannot see it and duty (c) does
not compel a new row. Disposition in §8.

> **This document is pushed BEFORE any solve.** §4's gates, §6's verdict rule and
> §7's rule-14 disposition are fixed ahead of the LP numbers precisely so none of
> them can be chosen after them. The §3 measured values are **INPUT
> identification** produced by the Phase-0 survey — they read no model output,
> no residual and no scoring target. Nothing in this document is conditioned on
> a backcast result.

---

## 1. Phase 0 answered the frontier question: **sub-TAC load is AVAILABLE**

`ASSESSMENT-caiso171-frontier-2026-08-04.md` §5 item 3 posed the one unresolved
question gating CAISO's `complete` declaration: *does CAISO publish load at
sub-TAC (NP15/ZP26) grain at all?* The survey
(`scripts/probes/_caiso172_subtac_load_survey.py`, committed, network, no LP)
answers it on live bytes.

| id | candidate | verdict |
|---|---|---|
| **S1** | OASIS `SLD_FCST` (the wired `load` dataset) | **WALL** — TAC-area grain under **every** `market_run_id` (ACTUAL/DAM/2DA/7DA/RTM). CAISO-internal areas are only `PGE-/SCE-/SDGE-/VEA-TAC` (+`MWD-TAC`); all other areas in the domain are external WECC BAs. |
| **S2** | the OASIS report catalogue | **AVAILABLE** — `ATL_LDF` × `ATL_PNODE_MAP` (§2) |
| **S2b** | `ENE_SLRS` `TAC_ZONE_NAME` (`TAC_NORTH/NCNTR/ECNTR/SOUTH`) | **WALL** — looks sub-TAC, is not. `ATL_TAC_AREA_MAP` puts the ZP26-side landmarks (Gates, Midway, Panoche, Elk Hills, Helms) in `TAC_NORTH` **together with** Moss Landing / Geysers / Vaca-Dixon / Round Mountain. `TAC_NORTH` spans Path 15 ⇒ the utility geography relabelled. |
| **S3** | CAISO DLAP price nodes (caiso-165 intake) | **dismissed, as charted** — every `PRC_LMP` item at `DLAP_PGAE` is a $/MWh component (`LMP/MCC/MCE/MCL/MGHG`); none is a load quantity. OASIS's generic value column is *named* `MW` for price reports too, which proves nothing. **The load companion of a DLAP is `ATL_LDF`** — which is what S2 uses. |
| **S4** | FERC Form 714 / CEC demand forecast | **WALL** — 714 still HTTP 403 from this environment (unchanged from 2026-07-05); CEC planning areas (PG&E Bay Area / PG&E Valley) remain boundary-mismatched to Path 15 regardless of reachability. |
| **S5** | EIA-930 sub-BA route | **WALL** — demand-only by schema (`data` columns `['value']`, facets `['parent','subba']`); re-confirms caiso-141 S5 rather than re-deriving it. |

**Side finding, logged not actioned:** `MWD-TAC` (Metropolitan Water District,
~208 MW ≈ 0.9 % of ISO load) is a real CAISO TAC area **absent from the
committed `CAISO_tac_load_hourly_*.csv` series** and from
`CAISO_TAC_ZONE_WEIGHTS`. It is an SP15-side omission, **not** a Path-15 split,
so it is out of scope here and is recorded in the FINDING as a separate open
item.

---

## 2. The construction (frozen; `scripts/data/derive_caiso_path15_load_split.py`)

No report publishes an NP15/ZP26 load **MW series**. CAISO does publish both
halves of the split, as effective-dated Atlas reference reports:

* **`ATL_LDF`** — per-pnode **Load Distribution Factors** inside
  `DLAP_PGAE-APND`: CAISO's own published weighting for distributing PG&E LAP
  load onto nodes. Sums to exactly **100.000** over **1,668** load pnodes.
* **`ATL_PNODE_MAP`** — CAISO's **authoritative** `TH_NP15_GEN` / `TH_ZP26_GEN`
  / `TH_SP15_GEN` pnode membership: the Path-15 / Path-26 geography itself.

Joined by **substation** (`SUBSTATION_voltage_id`), two-tier, residue reported:

1. **tier 1 — direct substation match.** A substation counts only if all its hub
   pnodes agree (ambiguous substations dropped, never majority-voted).
2. **tier 2 — PG&E sub-LAP dominant hub.** The 15 `SLAP_PG*` sub-LAPs partition
   **95.78 %** of `DLAP_PGAE` and classify near-perfectly against tier 1:

   | sub-LAP | share of PG&E | tier-1 NP15 : ZP26 |
   |---|---:|---|
   | `SLAP_PGZP` (ZP26) | 6.893 | **0 : 39** |
   | `SLAP_PGKN` (Kern) | 4.293 | **0 : 21** |
   | `SLAP_PGF1` (Fresno) | 13.015 | 71 : 3 |
   | the other twelve | 71.583 | 100 % NP15 |

3. **residue** — ~2.2 LDF points reach neither tier; **excluded from the
   normalisation**, never folded into a side.

Effective windows are **day-weighted** within each calendar year.

---

## 3. What the measurement says (INPUT identification — no model output read)

Per-year, day-weighted over every effective window live in the year, from the
committed snapshot bytes (`derive_caiso_path15_load_split.py`, no network):

| year | NP15 | ZP26 | residue (pts) | tier-1 nodes |
|---|---:|---:|---:|---:|
| 2023 | 0.883565 | 0.116435 | 2.473 | 483 |
| 2024 | 0.884464 | 0.115536 | 2.152 | 488 |
| 2025 | 0.883996 | 0.116004 | 2.152 | 492 |
| **mean** | **0.883951** | **0.116049** | — | — |

**Model currently carries NP15 0.86 / ZP26 0.14.** The measured ZP26 share is
therefore **~2.4 points lower in absolute terms** than the residual-identified
estimate (0.1160 vs 0.1400 — a **17 % relative reduction** in the PG&E load
assigned to ZP26): ZP26 falls from 6.46 % to ~5.36 % of ISO load, and NP15
rises from 39.69 % to ~40.83 %.

The table takes the **backcast-mean** — a single static scalar, because the
object being replaced is a single static scalar and the inter-year spread is
0.0011, an order of magnitude below the 0.024 correction itself.

---

## 4. Acceptance gates — **DATA gates, pre-registered, no model output**

Enforced by `derive_caiso_path15_load_split.py --acceptance`:

| gate | threshold |
|---|---|
| `DLAP_PGAE` LDF partitions the LAP | `ldf_sum ≥ 99.99` per year |
| residue bounded | `unassigned_pts ≤ 5.0` per year |
| tier-1 support behind tier-2 classification | `n_tier1_nodes ≥ 300` per year |
| inter-year stability | `|max − min|` of `zp26_weight` `≤ 0.010` |

A gate failure **stops the substitution** and is reported as such — it does not
get re-tiered or re-thresholded to pass.

---

## 5. The A/B

* **Arm B (candidate)** — `CAISO_TAC_ZONE_WEIGHTS['PGE-TAC']` = the §3 measured
  value. **Zero free parameters**; zero `ScenarioConfig` fields change.
* **Arm A (control)** — a **SAME-HEAD zero-delta** run: identical commit,
  identical CLI, the incumbent 0.86/0.14. Not the incumbent keeper's bundle —
  a freshly solved control, so the only difference between the arms is the
  table.
* **Years `2023 2024 2025` in ONE invocation** (rule 16 `[R-ALLYEARS]`),
  sequential within the run (rule 12), the two arms concurrent.

**Call-site confirmation before solving (the caiso-162 standing lesson).** A
`run_config.json` recording a mechanism as armed is NOT evidence the LP saw it.
`CAISO_TAC_ZONE_WEIGHTS` is consumed by
`market_sim/data/eia930/zonal_shares.py` (hourly zonal load shares) and
`scripts/data/curate_zonal_shares.py` / `derive_load_shares.py` (static
fallback shares) — the **backcast** demand path. This session verifies the
zonal demand series actually differs between the arms **before** reading any
price, and reports that check.

**Measured on a FLOW/QUANTITY observable as well as price**: the NP15↔ZP26
Path-15 link flow and the two zones' served energy, not only λ.

---

## 6. Verdict rule (fixed before the numbers)

The substitution's **admissibility** is settled by rule 14 and is not on trial
(§7). What the A/B decides is only whether the resulting run becomes the
designated CAISO keeper:

* **PROMOTE** iff Arm B's `calibration_verdict.py` determination is **no worse**
  than the incumbent's `CALIBRATED-WITH-CAVEATS` with **0 FAILs**, and the
  ledgered-caveat count does not increase.
* **REGISTER-AS-PROBE (not promoted)** if Arm B degrades the determination or
  adds a FAIL. The measured input is **still kept** (§7); the degradation is
  then a **discovered bug** and is written up as an open root-cause item, not
  reverted.
* Either way the run is registered on the dashboard **in this session**
  (rule 15 `[R-DASHBOARD]`).

**Explicitly NOT the verdict rule:** "does the NP15–ZP26 basis get closer to the
measured +5.947 / +8.576 / +5.727 $/MWh". That basis is reported (§9) because
the assessment asks for it, but it is **not** a gate — steering a load-split
input by a price residual is exactly the outcome-pin rule 13 `[R-MEASURED]`
forbids.

---

## 7. The rule-14 disposition — **stated before the result**

Rule 14 `[R-ACCURATE]` is explicit: prefer accurate/measured data over an
estimate, and **never revert to the estimate because the estimate fits the
backcast better**. A worse fit is a **discovered bug**, not a reason to revert.

So, pre-committed: **the measured split is kept regardless of what it does to
the backcast.** If Arm B is worse, this session keeps the measured input, files
the degradation as an open root-cause issue, and does not restore 0.86/0.14.

The rule-14 **misalignment exception** — which `constants.py` currently invokes
to justify keeping the estimate — is hereby **spent**, and this is the precise
point the incumbent comment gets wrong. Its claim is that "no TAC boundary
exists at Path 15 to measure the split directly." That remains true and is
irrelevant: the exception licenses an estimate only when the real data is
*genuinely misaligned to our representation*. Here the real data is
`ATL_PNODE_MAP` — **CAISO's own Path-15 hub geography**, the exact boundary the
model's NP15/ZP26 link represents. It is not misaligned; it simply had not been
found. Per rule 14's own reconciliation clause the reconciled real data is
preferred over the guess, and §2's construction and §8's limits are the required
written documentation of the reconciliation.

**What this is NOT** (stated so it cannot be over-claimed later):

* It is **not** an hourly NP15/ZP26 load series. An LDF is a *typical*
  distribution factor. This replaces a static scalar with a **measured static
  scalar** — the same kind of object, identified instead of assumed.
* It is **not** a C3a lever, and no N–S topology lever is chartered off its
  result (caiso-164 §0/§6 stands).

It satisfies rule 13's admissibility test: the quantity regenerates for a
forward year from published forward bytes and responds to changed conditions
(Kern/Fresno load growth against Bay-Area growth moves it).

---

## 8. Rule-28 matrix disposition (decided ahead of the result)

`CAISO_TAC_ZONE_WEIGHTS` is a `constants.py` table, not a `ScenarioConfig`
field: `check_mechanism_matrix.py`'s gap sweep cannot see it and duty (c) does
not compel a row. This session **does not mint a new mechanism row** — the
change arms no new mechanism and adds no toggle; it re-identifies an input to an
existing one. It registers on the existing **`demand_repairs`** row (the CAISO
demand-input lane), whose cell and citation are re-stamped with this session's
outcome, and the CAISO column is re-checked. Minting a row for a table with no
flag would put an unarmable cell in the matrix and misreport the mechanism
inventory.

## 9. What gets reported either way

* the per-year and mean measured split, and the acceptance table;
* the zonal-demand call-site diff (arms differ before any price is read);
* NP15/ZP26 served energy and Path-15 flow, both arms;
* the NP15−ZP26 **price basis**, both arms, against the measured
  +5.947 / +8.576 / +5.727 $/MWh (congestion share 80.2 / 87.2 / 81.7 %) and the
  incumbent keeper's +0.236 / +0.127 / +0.109 — **reported, not gated** (§6);
* the DOF ledger consequence: if promoted, this entry moves
  `residual → measured`, `n_residual 9 → 8`, and CAISO's ISO-specific residual
  count `4 → 3`.
