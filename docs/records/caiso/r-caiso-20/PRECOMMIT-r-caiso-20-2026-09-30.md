# PRECOMMIT R-CAISO-20 — arm the overnight clean rung in unprinted years (2026-09-30)

Written before any solve. Owner card 2026-09-30, link 1 "Arm overnight rung pre-2021" and link 2 "Ledger the fold gap".
Incumbent keeper `2026-09-30-caiso-r18-dswgas` (bundle `rcaiso18_A_span`, 2022–25, CALIBRATED, single ledgered C3c
2024). Fold `-touchpoints` (bundle `rcaiso18_A_tp_2019_2021`, NOT-YET).

## 1. What this is: an OWNER RULING, not a measured admission

- R-CAISO-19 FINDING §3 found no measured way to arm any clean rung in 2019–20. The overnight rung's no-wedge evidence
  is the measured 2022–25 CAISO−PaloVerde spread. The WEIM DSW footprint was smaller in 2019–20 (AZPS and NEVP; SRP
  from 2020-04).
- The owner ruled to carry the 2022–25 measured overnight structure into those years. **This is authorised by the
  ruling. It is not admitted under rule 13.** The attestation's DOF/provenance text and the matrix cell say so.
- It is a structural transfer of a window and a pricing basis, with no fitted scalar. Its depth comes from the same
  measured statistic the rung already uses (§3).

## 2. The build (one flag, default off, CAISO-only, backcast-only)

Flag: `caiso_dsw_overnight_clean_unprinted_arm`.

- `inject_caiso_dsw_overnight_clean(unprinted_year_arm=)`: the hod 0–5 evidence gate becomes "raw Palo Verde print
  finite" **or** "the R-CAISO-18 unprinted-year branch prices the hub"
  (`envelopes.measured_intertie_hub_unprinted_year_mask`).
- The seam passes `unprinted_year_arm=True` only when `caiso_intertie_unprinted_year_measured_gas` is also on, so the
  rung is never armed without a price.
- Pricing is unchanged: the formula hub + EF 0 + ε, no wheel. The existing per-hub injector already prices the row
  (R-CAISO-19 FINDING: DSW_overnight_clean mc $28.12 / $30.03 in 2019 / 20).
- Headroom stays net of the firm block and the surplus rung (rule 19).
- **Untouched:** the surplus, daytime and late-evening rungs, which stay raw-print gated (FINDING §3).

**Mask on committed data** (hours; `gap_fill_measured_dam=True`, the keeper's setting):

| | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|--:|--:|--:|--:|--:|--:|--:|
| unprinted-year hours | 8,760 | 8,760 | 2,784 | 0 | **0** | 0 | 0 |
| of which hod 0–5 (newly armed) | 2,190 | 2,190 | 696 | 0 | 0 | 0 | 0 |
| raw-print NaN hours | all | all | 2,784 | 0 | 542 | 0 | 0 |

- **2023 Jan–Feb gap: closed.** Its 542 residual gap hours are a ≤25 % gap, which the ≤25 % fill path owns, and the
  mask cannot contain them. The closed winter lane stays closed by construction, and a test pins it.
- 2022–25 are inert by construction when the flag is on (tests: capability arrays byte-identical on vs off).

## 3. Depth (pre-registered)

Source: `derive_caiso_overnight_clean_depth.py --extra-years 2019 2020 2021 2022`, the rung's own p95 over all
overnight hours of the EIA-930 WECC_DSW corridor net import. **The percentile is not re-sized (rule 1).**

| Year | p95 (MW) | Used |
|---|--:|---|
| 2019 | 6,566 | **6,566** (new table entry) |
| 2020 | 7,166 | **7,166** (new table entry) |
| 2021 | 6,892 | **6,187, the static entry, kept** |
| 2022–25 | 6,309 / 5,870 / 6,205 / 6,487 | unchanged |

**2021 keeps its static entry.** Its printed May–Dec hours already arm at 6,187 in the fold. A table entry would move
those hours too, mixing a depth change into this arm, and one year carries one depth. The 2021 p95 is recorded here for
the record only. The committed-sample gates are unchanged (CV 0.041, LOYO worst 8.1 %).

## 4. Zero-LP first-order estimate (fold legs' P1, R-CAISO-18 leg commits, provenance only)

Capability = Σ over armed hours of max(0, depth − firm − surplus capability). The rung's offer (median $27.5 / $28.6 /
$44.2) sits below the overnight λ, so first order it runs at capability and displaces the DSW gas blocks first.

| TWh | 2019 | 2020 | 2021 |
|---|--:|--:|--:|
| New clean capability | 8.77 | 9.43 | 3.14 |
| DSW gas already running in those hours | 1.69 | 0.70 | 0.06 |
| **First-order added DSW net import** (capability − displaced gas) | **≈ 7.1** | **≈ 8.7** | **≈ 3.1** |
| DSW gap in those hours, model − EIA-930 (pre-arm) | −3.83 | −7.36 | −2.31 |
| DSW gap, whole year (pre-arm) | −13.3 | −20.6 | −11.0 |
| First-order whole-year gap after the arm | ≈ −6.2 | ≈ −11.9 | ≈ −7.9 |

- The corridor ATC envelope can bind and trim these numbers; price feedback is ignored.
- **2019 overnight may overshoot:** +7.1 against a −3.8 overnight gap leaves ≈ +3.2 TWh over EIA-930 in hod 0–5. The
  whole-year |DSW error| still falls. This is reported, not gated (see §6).
- Expected: CC_REGULAR down by about the added import in each fold year.

## 5. Shards (rule 36) and G-DRIFT

- Seven shards, one per year 2019–2025, pinned to the build PR's merge SHA. The parent never solves (rule 32(a)).
- Template `docs/records/caiso/r-caiso-18/shard-prompt.md`, adding `--set caiso_dsw_overnight_clean_unprinted_arm=true`.
  `{SRC}` = `rcaiso18_A_tp_2019_2021` (2019–21) / `rcaiso18_A_span` (2022–25). The 2025 shard gets a 50-min budget.
- New hard stop (THE ARM): the mask probe must print, per year, `<unprinted hod0-5 hours> <depth>`:
  2019 `2190 6566.0`, 2020 `2190 7166.0`, 2021 `696 6187.0`, 2022 `0 6309.0`, 2023 `0 5870.0`, 2024 `0 6205.0`,
  2025 `0 6487.0`.
- G-DRIFT against the keeper's pin `d757b216`: see §8 (addendum, written before any shard launches).

## 6. Decision rule (pre-registered)

**PROMOTE** if all hold:
- (a) The 2022–25 legs reproduce the incumbent: max |Δ class TWh| = 0.0000, and the span stays CALIBRATED.
- (b) Every shard passes its hard stops, and each 2019–21 leg's log shows the overnight arm.

The fold's movement is reported. **Structural backstop, not a fit gate:** if the whole-year |DSW net import − EIA-930|
grows in any fold year, the trade goes to the owner as a decision card instead of an automatic promotion.

Note on rule 30(c) as amended today (rubric v3.13): the ISO-level determination now folds held-out years worst-of,
so a NOT-YET fold makes the ISO headline NOT-YET whatever this arm does to the span. The decision rule above is on the
span keeper's run-level determination, as the handoff states; the ISO headline is reported as computed.

## 7. After the solve (link 2)

Whatever DSW residual remains in 2019–21 is ledgered in the RESULT and the calibration log as
**data-availability limited**: OASIS serves no Palo Verde print before 2021-04-27, so the surplus, daytime and
late-evening rungs have no admissible trigger in those hours (FINDING §3).

## 8. G-DRIFT addendum (rule 29(b); zero LP; written before any shard launches)

`git diff d757b216 origin/main` (0da56737) over `src/market_sim`, `scripts/run_calibration*.py`, `scripts/lib`,
`scripts/replay_keeper.py`, `data/raw/_validation-source`, `data/raw/reference`: 29 files changed, **every hunk INERT
for a CAISO backcast**.
- NYISO F/G split (iso_configs, topology_variant, ttc, zonal_shares, zone_assignment, nyiso_* modules): NYISO-only
  branches.
- SPP CROW residual (`spp_gas_outage.py`, `fleet/arrays.py`), ERCOT prior-year commitment profile: SPP- or
  ERCOT-only, default-off flags.
- `cc_subfloor_eia923_heat_rates`, per-unit vintage denominator, `apply_cc_committed_offer_margin(year=)`,
  `floors.py` hour profile: default-off flags absent from the keeper recipe; the floors refactor computes the same
  target.
- `import_node_links(iso)`: CAISO executes it and it returns the unchanged `IMPORT_NODE_LINKS["CAISO"]`.
- `actual_lmp.json`: MISO entries only.
- The keeper recipe's `cache_key()` is `929b1c6557162913` at both commits, and the CAISO solve-surface moved-row set is
  identical.

Form 4 holds: the committed `rcaiso18_A_span` / `rcaiso18_A_tp_2019_2021` bundles are the control. No control solve.
This build's own hunks are inert with the flag off (tests) and inert in 2022–25 with it on (§2).
