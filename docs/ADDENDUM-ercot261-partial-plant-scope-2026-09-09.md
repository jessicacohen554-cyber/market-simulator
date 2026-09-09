# ADDENDUM to PRECOMMIT-ercot261 — Card B needs the PARTIAL-plant channel, and here is its footprint, declared before the solve

> Written **before any LP is spent**, as an addendum to
> `docs/PRECOMMIT-ercot261-gas-level-retirements-2026-09-09.md` §3.

## 1. What the whole-plant channel actually recovers for ERCOT: 9.8 MW

The parquet was appended back to 2021 (append-only; every pre-existing row
preserved byte-for-byte, verified). Measured on the committed sheet, filtered to
`balancing_authority_code == ERCO`:

| retirement year | units | MW | whole-plant | partial-plant |
|---|---|---|---|---|
| 2021 | 10 | 37.2 | **9.8** | 27.4 |
| 2022 | 2 | 406.0 | **0.0** | 406.0 |

**The whole-plant channel recovers 7 landfill-gas units totalling 9.8 MW.** It
recovers **none** of 2022.

*(The handoff quoted 35.8 MW / 510.2 MW from the FINDING. That count is on
`state == TX`; the model maps fleets by balancing authority, and on `ERCO` the
figures are the ones above. Neither number changes the conclusion.)*

## 2. Why — and it is the guard working, not a bug

**Decker Creek (plant 3548)** is 98 % of ERCOT's affected capacity: a **405 MW
gas ST retired 2022**. Its plant still carries **four 51.5 MW CTs (GT1–GT4, all
`OP`)** in the operable snapshot, so `build_within_window_retirees` drops it by
design — the COD map is **plant**-keyed, so injecting a surviving plant's retired
unit would hold the whole plant online and **double-count** capacity. That is
precisely the guard `tests/unit/data/test_retiree_window_append.py` pins, and it
is correct.

The unit-grain channel that *can* carry it already exists:
`partial_plant_exit_carry` (miso-190), whose rows carry their own actual
retirement in `planned_retirement_*`, which `cod_ramp.effective_cod` prefers over
the plant-collapsed date — so the ST ages out in 2022 while its four CTs keep
running.

## 3. The scope decision

**Card B arms `partial_plant_exit_carry` for ERCOT**, and
`_PARTIAL_EXIT_WINDOW_START` now reads the same
`paths.active_retiree_window_start()` the whole-plant filter reads.

Reasons: (a) Card B's stated purpose is that *"a unit that ran in 2021 and
retired in 2021–2022 is missing from the fleet entirely, biasing capacity SHORT
and price HIGH"* — Decker Creek **is** that unit, and delivering Card B while
omitting 98 % of its own capacity would deliver the headline and not the
substance; (b) it is the **same channel's membership**, not a second mechanism
stacked on the same phenomenon — the miso-190 docstring calls it "the gated
complement of `build_within_window_retirees`' whole-plant filter" with "zero
overlap by construction" (rule 19 `[R-ONE-MECH]`); (c) splitting the two windows
would carry a plant's whole-plant exits back to 2021 while stranding its
unit-grain exits at 2023, which is incoherent.

**Rule 25 `[R-ISO-SCOPE]` is respected**: `partial_plant_exit_carry` carries
**zero fitted scalars** — it is a membership rule on published EIA-860 rows — so
nothing is transferred from MISO. ERCOT's matrix cell records it as newly
exercised here, and no other ISO's cell is filled by this verdict.

## 4. The footprint this adds, declared ex ante

| year | added by the partial channel | units |
|---|---|---|
| 2021 | **+27.4 MW** | Sam Rayburn 1 & 2 (11.2 MW CTs), TAMU Central Utility STG04 (5.0 MW CC) |
| 2022 | **+406.0 MW** | **Decker Creek 2 (405.0 MW gas ST)**, OCI Alamo battery (1.0 MW) |
| 2023 | **+75.0 MW** | Freeport Energy G-37 (gas CT, retired 2023) |
| 2024 | **+75.0 MW** | C R Wing Cogen GEN3 (gas CC, retired 2024) |
| 2025 | 0 | — |

**This is the one place Card B reaches the training years.** 75 MW on a ~70 GW
system is **0.1 %**, which is consistent with the PRECOMMIT's P6 (2023–2025 move
near-zero) — but it is **not** byte-identical, and it is declared here rather
than discovered afterwards. G-1's $0.40/MMBtu gas gate and G-4's no-flip gate
both still bind on those years.

Predicted effect, registered: 2022 is the year Card B can actually move (405 MW
of gas ST re-entering a year the model prices high); 2021 remains immaterial at
27.4 MW ≈ 0.04 % of peak, exactly as the handoff said. **Card B is included
because it is correct (rule 14 `[R-ACCURATE]`), not because it moves a residual**
— and P8 stands: if 2021 moves materially on Card B, that is a surprise to
report, not a success to claim.

## 5. Prior art honoured

Phase 0's construction-C result — that reshaping the monthly February basis by
the measured Henry Hub daily curve leaves the calm days carrying ~$30/MMBtu they
never paid — **independently reproduces `FINDING-ercot258`**, which had already
closed that successor on the same arithmetic (its estimate ~$28–30/MMBtu; measured
here at **$31.26**). This session did not re-open an adjudicated cell: it derived
the same bar from the fuel side and then took a different route (corroboration
hold-out) that ercot-258 did not consider. The DO-NOT-REDO discipline of rule 28
`[R-MECH-MATRIX]` is satisfied, and ercot-258's `O` verdict on
`ercot_ep_gas_basis_monthly` stands unamended.
