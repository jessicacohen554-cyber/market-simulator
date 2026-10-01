# PRECOMMIT — SPP-52a: a uniform −7 % fossil offer-curve level, through the rule-1 authorized channel

**Lane** SPP-52a · **Model** Opus 5 (`claude-opus-5`) · **Date** 2026-09-09 ·
**Branch** `claude/spp-51c-curtailment-allocation-izd5x2` · **Base** `5b354406` ·
**Data profile** `spp` · **Control** SPP keeper 4 `2026-09-09-spp-51c-oversupply-curtailment`
(`results/calibration/spp51c_oversupply`, committed, on the REPAIRED clock).

**Pushed BEFORE the solve is launched**, because rule 1 `[R-STRUCT]` condition (c) requires the
value to be declared ex ante. Nothing in §3 has been computed.

---

## 1. The instruction, and why it is admissible

Owner instruction, verbatim: *"first just tune the offer curve down by 7% across all fossil and
launch an LP that runs that"*.

This is the **rule 1 `[R-STRUCT]` / rule 13 `[R-MEASURED]` authorized price-tuning channel** (owner
amendment 2026-09-05). Every condition is met and each is stated rather than assumed:

- **(a) the channel is the four `offer_curve_by_group` bands ONLY.** The arm sets
  `committed / econ_low / econ_high / peak = 0.93` and touches **no** `phys_*`, **no**
  `econ_low_share`, **no** `pct_peaking`, and adds no adder, offset, haircut or proxy.
- **(b) ONE config across EVERY scored year.** A single scalar 0.93, all three years. No per-year
  value.
- **(c) set ex ante, declared here before the solve, and NEVER swept.** The value is the owner's own
  number. This lane does not try 0.95 or 0.90 and keep the one that makes a criterion pass; **if the
  declared 0.93 overshoots or undershoots, that is the result, and I will report it as such rather
  than re-running at a different value to land a gate.**
- **(d) merit-order adjustment across classes is an INTENDED effect**, not a defect.
- **(e)** the run declares the channel in its attestation's `authorized_price_tuning` block (C6
  FAILS without it) and carries 0.93 as a **free parameter in the DOF ledger** (rule 21
  `[R-DOF]`), identification *"price residual, authorized channel (rules 1/13 amendment
  2026-09-05)"* — **not** a measured source. The ledger therefore goes **3 entries / 1 residual →
  4 entries / 2 residual**, and that cost is the point of the ledger.

**Rule 25 `[R-ISO-SCOPE]`:** passed per-run via `--offer-curve-json`, so no generic fallback moves
off 1.0 and no other ISO is touched.

## 2. The cell is `R` for SPP, and what the new evidence is

`offer_curve_by_group` is adjudicated **`R`** for SPP by the price-family lane
(`FINDING-spp-price-family-2026-09-07.md`), which killed a uniform quadruple on its pre-registered
**G-2 steepening** gate: measured arm/control price ratio 0.9070–0.9151 across the entire load
range, a 0.81 pp spread — *"the surface moved DOWN; it did not ROTATE"*. Rule 28(a) forbids
re-testing an `R` cell **without new evidence**. The new evidence is twofold and it is about what
the residual now IS, not about what the lever does:

1. **The residual has changed character.** That lane faced a residual it diagnosed as a *shape/tail*
   defect, and a level lever aimed at a shape defect is the wrong instrument — which is what G-2
   caught. On keeper 4 the remaining C3a failure is a **marginal LEVEL miss in ONE year**
   (2025 +10.28 % against a ±10 % band; 2023 +7.80 % and 2024 +5.64 % already pass). **A level lever
   is the apt instrument for a level miss.**
2. **The basis is different.** Every price-family number was computed against the **GMT-indexed**
   actual; SPP-51c repaired that sidecar, and `rt_lw` moved +0.70/+0.92/+0.64 \$/MWh. The `R` was
   reached on a basis that no longer exists.

**What is NOT claimed:** that G-2 would now pass. A uniform quadruple is still a level lever and
still will not rotate the stack. This arm is **not** offered as a shape repair and its result must
not be read as overturning the price-family lane's mechanism finding.

## 3. PRE-REGISTERED PREDICTIONS — sign and magnitude, none computed

- **P-1 (direction + magnitude).** The load-weighted mean model price falls by **5.0–8.0 %** in every
  year. Mechanism: in a fossil-marginal hour the clearing price scales with the marginal unit's
  multiplier, so a flat 0.93 on all four bands should move the level ≈ −7 % less whatever share of
  hours is set by wind / hydro / nuclear, which do not scale.
- **P-2 (the target).** C3a lands **inside ±10 % in all three years**: roughly **+0.3 / −1.7 /
  +2.6 %** from 7.80 / 5.64 / 10.28.
- **P-3.** C3b monthly NRMSE **improves** in all three years (the model is too dear, so a level cut
  moves monthly means toward the actual), and 2025 drops **below 0.20**.
- **P-4 (AGAINST INTEREST — this hurts my preferred reading).** **I predict this does NOT change the
  determination.** It stays **NOT-YET**, because C1 still fails on the 2024 ST_GAS row (the
  Harrington fuel-vintage object, SPP-46 R-4, which no offer multiplier reaches) and C3c still fails
  in all three years — two failing criteria, so the C3c standing rule cannot fire. **A passing C3a
  is not a calibrated ISO and I will not present it as one.**
- **P-5 (AGAINST INTEREST).** **C3c gets WORSE or stays pinned at zero.** The model already prints
  0 / 4 / 2 hours above \$200 against 42 / 59 / 68; making the whole fossil stack 7 % cheaper can
  only lower the top of the surface. Reported at full magnitude; under rule 1 a worsened C3c is not
  grounds to abandon an authorized, declared level lever, and it is also not grounds to dress this
  arm up as structural.
- **P-6.** Class energy moves are **small** — summed |class error| changes by **< 1.5 TWh** in each
  year — because a uniform multiplier preserves the between-class merit order (the price-family lane
  measured CT_PEAKER −0.247 TWh on a steeper quadruple than this one).

**A threshold that misses is reported in the words above.** If P-1 lands at 9 %, the band was
"5.0–8.0 %" and it **missed**, and the arm **overshot** — which on P-2's arithmetic would push 2024
through −10 % and turn a PASS into a FAIL in the other direction. I will say that plainly rather
than re-cutting the band or re-running at 0.95.

## 4. The arm, exactly

One invocation, full span, years sequential (rules 12 / 16):

```
uv run python scripts/run_calibration_full.py --iso SPP --year 2023 2024 2025 \
    --out-dir results/calibration/_spp52a_fossil93 \
    --hydro-backfill-year 2024 --hydro-eia930-monthly \
    --vre-curtailment-oversupply-allocation \
    --offer-curve-json '{"CC_REGULAR":{...0.93...}, ... }'
```

Keeper 4's recipe **plus only the offer-curve JSON**. The ten classes carrying a registered base
curve that SPP dispatches: `CC_REGULAR, CC_CHP, CT_CHP, CT_PEAKER, ST_GAS, COAL, COAL_BIT,
COAL_LIGNITE, COAL_PRB, COAL_WC` — all at 1.0 today, all to 0.93 on the four bands.

**Two exclusions, both deliberate and both inherited from the price-family lane's measured
experience.** `ST_CHP` has **no registered base curve** in SPP's resolved `offer_curve_by_group`
(verified: the resolved dict has 13 keys and `ST_CHP` is not among them), so including it creates an
entry with no `econ_low_share` and the launch dies with `KeyError: 'econ_low_share'` — that is how
the price-family lane's first launch failed. The three `*_INTERMEDIATE` curves carry a separately
identified ERCOT-lineage shape and all three splits (`cc_/ct_/st_gas_intermediate_split`) are
`False` in SPP's recipe, so they are **provably unreachable** and are left untouched.

## 5. Rule postures

- **Rule 29 `[R-SCREEN]`.** The owner asked for the full LP directly, so no screen is run and none is
  claimed. Recorded honestly: this spends the full span without a one-year screen, on an owner
  instruction, and the pre-solve arithmetic in §3 is the phase-0 substitute.
- **Rule 29(b).** Control = keeper 4's **committed** bundle, which is on the repaired clock and was
  solved at `86e45462`; form 4 holds with no control solve.
- **Rule 31 `[R-RETAIN]`.** `results/calibration/_spp52a_*` is gitignored at the moment of writing
  and **never `rm`'d**; the promotion question is asked in-session while the bundle is alive.
- **Rule 15.** Registered in the session it finishes, keeper or rejected.
- **Rule 28.** `offer_curve_by_group` is SPP's cell to move; the §2 evidence is appended either way
  and the cell moves only if this arm is adjudicated.
- **Out of scope:** the R-2 thermal-commitment floor (next lane), R-3 the zonal spread, C3c / SPP-55,
  the 2024 ST_GAS Harrington row. **No owner card opened.**
