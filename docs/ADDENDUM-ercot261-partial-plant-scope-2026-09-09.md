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

> **UPDATED 2026-09-09 after the rebase onto `main`.** The whole-plant half of
> Card B is WITHDRAWN — superseded by `7934e92c`, which widened the window to
> 2019 globally with a multi-vintage reader (see PRECOMMIT Addendum 2). Sections
> 1-2 and 4-5 below stand as measured; §3's delivery mechanism changed from a new
> gated `ScenarioConfig` field to a **one-line repair of the whole/partial window
> mirror that `7934e92c` left broken** (`_PARTIAL_EXIT_WINDOW_START` 2023 -> 2019).
> The Decker Creek finding is UNAFFECTED and is now the whole of Card B's
> surviving substance: main's widened parquet still carries **zero** ERCOT 2022
> rows, so the 405 MW ST is still missing without the partial-plant channel.

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

**RE-MEASURED 2026-09-09 after the rebase**, at the 2019 window the mirror repair
restores (the numbers in §1–§3 were measured against a 2021 window and are
superseded here). Units the partial-plant carry adds to ERCOT, by retirement year:

| retirement year | units | MW | largest |
|---|---|---|---|
| 2019 | 6 | 9.2 | — |
| **2020** | 1 | **320.0** | **Decker Creek 1** (gas ST, ret 2020-10) |
| 2021 | 3 | 26.0 | Sam Rayburn 1 & 2 (10.5 MW CTs) |
| **2022** | 1 | **404.0** | **Decker Creek 2** (gas ST, ret 2022-03) |
| 2023 | 1 | 59.2 | Freeport Energy G-37 |
| 2024 | 1 | 70.0 | C R Wing Cogen GEN3 |
| **total** | **13** | **888.4** | |

Measured directly: ERCOT's within-window retiree set goes **38 units / 1,721.2 MW
→ 51 units / 2,609.6 MW**, a **+888.4 MW** delta.

**This is materially larger than the pre-rebase estimate (+406 MW into 2022), and
the reason is the window itself.** Restoring the mirror to 2019 surfaces
**Decker Creek unit 1** — a *second* 320 MW gas ST that retired 2020-10 and was
hidden by BOTH the old 2023 partial window and the whole-plant filter. The two
Decker units together are **724 MW**, and each is timed out by its own
`planned_retirement_*` through `cod_ramp.effective_cod`, so unit 1 is online
through Oct-2020 and unit 2 through Mar-2022 while the plant's four 51.5 MW CTs
keep running throughout.

Per-year dispatch reach after COD masking: 2021 sees Decker **2** only (unit 1
already retired), i.e. **+404 MW plus 26 MW of CTs**; 2022 sees Decker 2 through
March; 2023 and 2024 gain 59.2 and 70.0 MW respectively. The 2023/2024 rows
remain the one place this touches the training years — now **59–70 MW**, about
**0.1 %** of peak, still consistent with the PRECOMMIT's P6.

**P8 is REVISED and the revision is stated rather than buried**: the pre-rebase
claim that Card B is "immaterial to 2021" was measured at 9.8 MW. At the restored
window ERCOT's 2021 fleet gains **~430 MW**, which is **not** immaterial. Card B
is still included because it is correct (rule 14 `[R-ACCURATE]`) and not because
it moves a residual — but it can no longer be pre-registered as inert, and any
2021 movement must now be attributed between Card A and Card B rather than
assigned to Card A by default.

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
