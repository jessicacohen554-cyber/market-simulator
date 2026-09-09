# PRECOMMIT — ercot-265: the corroboration filter discards BOTH measurements

**Session:** ercot-265, 2026-09-09. Branch `claude/ercot-uri-february-fuel-baynmi`.
**Keeper:** `2026-09-09-ercot261-corroborated-gas-level` (bundle
`results/calibration/ercot261_five_year_keeper`). **Nothing solved at the time of writing.**
Pushed BEFORE the arm is solved (rule 29 `[R-SCREEN]`).

---

## 1. The defect

`ercot_ep_gas_basis_corroborated` admits a month's own measured basis only where a SECOND
independent measurement agrees within `ERCOT_GAS_CORROBORATION_TOL_USD_MMBTU = 1.00`. When they
disagree it currently does this:

```python
out[~admissible] = float(basis[admissible].mean())
```

**It discards BOTH measurements** and prices the held-out month at the year's other months'
central value. A month in which ERCOT's generators demonstrably paid an extraordinary price is
therefore priced at an ordinary one.

It fires in **exactly one year of 2019–2025**: 2021, months 2 and 12. February 2021 is Winter
Storm Uri and carries **94.8 % of that year's C3b SSE**, the ISO's only remaining rubric failure.

## 2. The repair — rule 14 `[R-ACCURATE]`, and it is not a residual

Between the two disagreeing measurements, prefer the better-grounded one:

| | Feb-2021 |
|---|---|
| EIA N3045TX3 survey | **$59.73/MMBtu** — a monthly **cost/volume RATIO**, which `.basis.ercot`'s own docstring records as unreliable when a month's within-month distribution is extreme |
| **EIA-923 Schedule-5 receipts** | **$45.96/MMBtu — what the plants ACTUALLY PAID**, quantity-weighted, **36 plants, 28.4 million MMBtu — the year's LARGEST burn month** |

So a held-out month takes the corroborator's own basis (receipts − the same monthly hub).
New field `ercot_ep_gas_basis_receipts_fallback`, default **off**, a **sub-gate inside** the
corroboration flag (rule 19 `[R-ONE-MECH]` — same filter, same rows, same months; only the
fallback VALUE changes). **ZERO free parameters** (rule 21 `[R-DOF]`): the tolerance, the
admissibility test and the fail-closed incompleteness discipline are untouched, and the
substitute comes from a series already committed and already read by this filter.

## 3. Phase 0 — measured, zero LP, BEFORE any solve

**Basis arrays** (`ercot_electric_power_gas_basis_monthly`):

| year | keeper | ARM | note |
|---|---|---|---|
| **2021 m02** | +0.390 | **+40.611** | receipts $45.96 − hub |
| **2021 m12** | +0.390 | **+1.589** | |
| 2022 / 2023 / 2024 / 2025 | — | **BYTE-IDENTICAL** | no month is held out, so the filter is inert |

**The 2023–2025 TRAIN TIER is byte-identical by construction and by measurement.** Only the
validation-tier year 2021 moves. Every other ISO and every forecast is untouched (ERCOT-only
flag, default off).

**Delivered February-2021 gas** (base × `gas_daily_shape` + the flat monthly level − scalar):

| | Feb mean | **cheapest Feb day** | peak day |
|---|---:|---:|---:|
| keeper | $11.09 | $6.23 | $48.79 |
| **ARM** | **$51.31** | **$46.45** | **$89.01** |
| ercot-254 (solved, REJECTED) | $65.08 | $60.22 | $102.77 |

## 4. THE PRE-SOLVE GATE IS AMBIGUOUS, AND THAT IS WHY THIS SOLVES

The mechanism that killed ercot-254 is **breadth**: a MONTHLY level lands on all 672 February
hours while the real Uri spike lasted ~5 days, so the calm days pay a price they never paid and
C3c blows out (234 → 688 h against 258 actual). The arm carries the same construction at **74.7 %
of the level**. Whether that clears the C3c threshold is **not decidable by argument**:

- at the repo's identified marginal heat rate **HR 7.36**, the cheapest February day prices at
  **$342/MWh** — above the $200 C3c threshold, so all 672 hours would count and the arm dies;
- at the model's **own measured calm-February price/gas ratio ≈ 4.0** (keeper calm-day price
  $21–36/MWh on $5.34–7.55 gas — the marginal unit at low load is not the marginal CC), the
  same day prices at **$186/MWh**, below the threshold, and the arm survives.

Both readings are defensible from committed artifacts. **The LP decides which marginal unit
actually sets the calm-February price.** That is a legitimate spend and it is one year.

## 5. PRE-REGISTERED GATES — STOP gates, structural, none on the target residual

The screen **may kill the arm and may never promote it** (rule 29).

- **G-1 (identity, ALREADY PASSED zero-LP):** 2022–2025 basis arrays byte-identical to the
  keeper's. ✅ measured above.
- **G-2 (the arm does what its arithmetic says):** February-2021 delivered gas mean lands at
  **$51.31 ± 0.5/MMBtu**. A materially different value is a wiring defect, not a result.
- **G-3 — THE KILL GATE, pre-registered now:** **C3c-2021 hours > $200/MWh must be ≤ 400.**
  Keeper = 223 h, actual = 214 h, ercot-254 = 688 h. Above 400 the arm has reproduced
  ercot-254's breadth failure and **is dead on the spot**, whatever it did to C3b. This is a
  structural breadth measure, NOT the target criterion.
- **G-4 (no forcing):** slack and dump stay exactly 0.0 in 2021, as on the keeper.
- **G-5 (no load-bearing flip):** C1, C2, C4, C6 do not flip PASS → FAIL on 2021.

**Sealed predictions, scored in the RESULT whatever they do:**
- **P1** C3c-2021 lands **between 223 and 688 h**. I expect it ABOVE 400 and therefore expect
  **G-3 to KILL this arm** — the breadth defect is untouched by a level repair, and I am saying
  so before the solve rather than after.
- **P2** C3b-2021 improves from 0.559 but does **not** reach the 0.20 gate.
- **P3** C3a-2021 moves UP from −6.7 % (more expensive February gas), possibly out of band.
- **P4** even if every gate cleared, this is **not automatically a keeper** — the owner decides
  (rule 31 `[R-RETAIN]`), and a level repair that leaves the breadth defect in place is a
  partial fix by construction.

## 6. G-DRIFT (rule 29(b))

G-CTRL **form 4**: the keeper's COMMITTED 2021 numbers are the control and **no control solve is
spent**. This is stronger than usual here — **ercot-264 solved all five years at HEAD and the
keeper reproduced to the cent** (2021 $154.42 → $154.43; February $1,422.13 exact), so HEAD drift
on ERCOT's backcast path is measured at zero. The only solve-path change since is this session's
own field, which is default-off and byte-identical off.

## 7. Governance

Rule 32 `[R-SHARD]`: the parent solves nothing; ONE shard, ONE year (2021), pinned to this
PRECOMMIT's full 40-char SHA, own out-dir and branch, reporting NUMBERS and pushing no bundle.
Rule 22: 2021 is **validation tier** and ERCOT holds the `complete` marker, so the shard passes
`--holdout-authorized`; 2019 and H1-2026 are frozen and untouched. Rule 16 `[R-ALLYEARS]`: this
is a throwaway diagnostic screen, **never registered**; a keeper would need the full span.
Rule 31 `[R-RETAIN]`: bundle gitignored, never `rm`'d, promotion question to the owner before
the session ends. Rule 28: the ERCOT matrix shard is stamped in this session whatever the result.
