# PRECOMMIT — NYISO-NEXT-17: the F/G re-partition (`nyiso_fg_split`) — 2026-09-30

- **Session:** NYISO-NEXT-17, the orchestrator. This container runs no LP (rule 32 (a)).
- **Design and phase 0:** `docs/records/nyiso/DESIGN-nyiso-next17-fg-split-2026-09-30.md`.
- **Owner decision card (this session):** "Build design A anyway".
- **Queue:** item 1 (2021 C3a +11.1 %, the owner's block on `complete`).
- **Rule 28:** `nyiso_fg_split` is a new row (cell U); no adjudicated cell is re-tested.
- **Control (form 4):**
  - Keeper `2026-09-30-nyisonext16-winter-spread-span` (bundle `results/calibration/nyisonext16_span`, 2022–2025).
  - Stamped `2026-09-30-nyisonext16-winter-spread-2021` (bundle `results/calibration/nyisonext16_2021`).
- **Arm:** the keeper recipe plus `nyiso_fg_split: true`. Nothing else moves. The flag requires `nyiso_total_east_cutset_ttc`, which the keeper already arms.

## 1. G-DRIFT (keeper `git_sha` 38ea5423 → pin)

- `ca84177c` R-CAISO-17 (`constants.py`, `scenarios.py`, `solve_surface_declared.py`): CAISO's EIA-930 clock windows, read only under `caiso_eia930_clock_repair`. Another ISO's branch. **INERT.**
- This session's code (`nyiso_fg_split` and its plumbing) is default-off and byte-identical off (`tests/iso/nyiso/test_nyiso_fg_split.py`, and the NYISO suite passes). The one shared-path edit caps a pooled border link that receives no attributed row at 0. In the base partition every pooled NYISO link is attributed, so that edit is **INERT** for the control.

Form 4 is valid; the keeper's committed bundles are the control.

**Zero-LP pre-flight (DESIGN §4).** A 2023 fleet-only rebuild conserves NYCA demand (147,048.9 GWh) and thermal nameplate (42,955.0 MW) exactly. It moves 9,014.7 GWh and 4,878.8 MW from Capital_Hudson to Lower_Hudson, and it adds the `Upstate_West>Lower_Hudson` link.

## 2. Legs (rule 36)

Five year-isolated shards at the pinned `main` SHA:

- 2022–2025: `python3 scripts/replay_keeper.py results/calibration/nyisonext16_span --years <y> --out-dir results/calibration/nyisonext17_<y> --set nyiso_fg_split=true`
- 2021: the same from `results/calibration/nyisonext16_2021`.

## 3. Gates (fixed before any solve; every value anchored to the keeper)

- **G-1 leg acceptance.**
  - `git rev-parse HEAD` equals the pin.
  - The leg's `scenario_config` equals the keeper's except (i) `nyiso_fg_split: true` and (ii) keys absent from the keeper at their dataclass default.
  - The leg's network sidecar carries a `Upstate_West>Lower_Hudson` link.
- **G-2 conservation.** Per year, against the keeper's P1 system sidecar:
  - total NYCA demand is equal within 0.1 GWh;
  - Capital_Hudson + Lower_Hudson demand is equal within 0.1 %;
  - Upstate_West, NYC and Long_Island demand are each equal within 0.1 %.
- **G-3 the new structure is live.**
  - `Upstate_West>Capital_Hudson` sits at its forward bound in ≥ 1 % of P1 hours.
  - `Upstate_West>Lower_Hudson` carries positive flow in ≥ 50 % of P1 hours.
  - Both hold every year.
- **G-4 no re-collapse upstate.** Upstate_West P1 hours at ≤ $0 are ≤ 100 in every year (keeper 0).
- **G-5.** C6 PASS and C8 PASS, every year.
- **G-6 no infeasibility pressure.** P1 load-slack energy does not exceed the keeper's by more than 1 GWh in any year.
- **G-7 conduct.** No D-4 failure row keyed (year, mechanism, plant) appears in the arm's composed `legitimacy_diagnostics.json` that is absent from the keeper's, in any year. Rows are keyed by the regex `(\d{4}) (.+?): plant (\S+)` (the NEXT-16 `_d4_fail_keys` pattern).

## 4. Promotion rule (fixed before any solve)

**Promote iff G-1 to G-7 hold in all five years.** This is a structural promotion (rule 1): the arm repairs a zone-membership misalignment (G's load and plants sit in a zone that is priced and scored as F) and carries TOTAL EAST as its two measured legs.

The following are **reported, not gating**, in either direction:

- C1, C3a, C3b, C3c and price MAE;
- zone-month errors;
- the CE-regime Capital − Upstate spread against measured;
- link binding shares.

If any gate fails, the run is registered (rule 15), not promoted, and the owner is asked.

## 5. Prediction (recorded, not a gate)

- The zero-LP pre-check measures the split's Upstate cut (CE posted + non-CE p90, 4,407 MW mean in 2021) as no tighter than the one-link envelope (4,378 MW). **A large 2021 C3a move is not expected.**
- Capital_Hudson (F alone) should price above Lower_Hudson more often when UW → CH binds. Upstate_West separates only when both upstate links bind.
