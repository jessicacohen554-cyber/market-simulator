# SPP Addition Desk — ledger (2026-09)

Canonical live state of the SPP addition program. Plan: `docs/multi-iso/spp-addition-plan-2026-09.md`.
Desk prompt: `docs/handoffs/spp-desk-handoff-2026-09-06.md`. **This ledger wins where the plan or the
handoff diverge on live state.** One `§0` entry per sitting, newest at top; amendments are appended to
the sitting's entry (`am.1`, `am.2`), never rewritten. Errors are recorded against interest in the entry
that finds them (§6).

---

## 0. Sittings (newest first)

### 0o. r#14 — sitting #14: SPP-49 LANDED — both input seams repaired REPO-WIDE at zero LP, the key census exact; ALL SEVEN GATES GREEN; SPP-50 issued (2026-09-08, main HEAD `d1b8d1bf`)

- Pin `d1b8d1bf` (the r#13 desk branch is merged; nothing ahead). One lane graded.
- **SPP-49 LANDED — P19 EXECUTED REPO-WIDE, ZERO LP** (PR #5640, `FINDING-spp-49-2026-09-08.md`).
  - **The open adjudication, decided per seam with its criterion stated** (which is what it was left open
    for): **seam 1 is a REGISTERED GATE** — `f923_gas_price_plausibility_screen`, **default ON**, declared
    at `("2026-09-08", …, "True")` — because a desk can legitimately want its own raw series; **seam 2 is
    a CONSTRUCTION** (`_apply_simple_cycle_hr_floor`, beside the existing `_apply_egrid_boundary_hr_repairs`
    CC ceiling), because a sub-9.0 eGRID rate on a non-CHP simple-cycle plant is not a reading anyone would
    want. The lane took the harder half of each call rather than the convenient one.
  - **THE CENSUS IS THE LANE'S BEST WORK: ex ante = ex post, exactly.** The PRECOMMIT predicted **18 keys
    move, 0 off-target**, with `scenarios.py` untouched; the landed tree moved **the identical set and the
    identical key pairs** (CAISO 2, MISO 1, NEISO 5, NYISO 7, PJM 2, SPP 1 — six of them designated
    keepers), 0 forecast, 0 hindcast, 0 ERCOT. Live confirmation on real payloads: SPP's and NYISO's keeper
    configs take new keys; **ERCOT's is byte-identical to the pre-edit tree**. Seam 2 added two names to
    `constants.py` and moved zero values (`solve_surface_register.py --diff` → "0 moved, 2 added").
  - **SPP-46's attribution reproduced, pre and post, and it is the proof the repair is the right one.**
    Pre-repair the lane reproduces SPP-46 **to the GWh** on every named row (Pioneer +5,013; Harrington
    +6,136; Mustang CC +2,222). Post-repair those rows move **−3,362 / −5,739 / −4,643 GWh** and the
    **CLEAN cohorts stay put** (ST_GAS clean +6 GWh on −6,062). Same rows, same direction, same order —
    at 60–75 % of the pre-registered magnitude, with the reason given (at the reference price these plants
    are still in merit above ~$20/MWh, so the in-merit metric moves less than the cost does). The ST_GAS
    clean −6.1 TWh is untouched by both seams, exactly as SPP-46 said, and stays SPP-46 R-5.
  - **One narrowing, made before any number was cited and disclosed as such:** CHP plants are excluded
    from seam 2. The first rebuild put 81 CAISO CT_CHP rows / 631 MW at 9.9 instead of their 10.3–13.5
    topping-corrected rates — eGRID's cogen rate is STEAM-CREDITED, so a sub-9 value there is the published
    convention, not an impossibility, and the model already owns it (`_correct_chp_steam_credit_hr`,
    `measured_chp_heat_rates`). Clamping first would have pre-empted that chain: **two mechanisms on one
    row, rule 19**. Pioneer and every plant SPP-46 named are non-CHP and unaffected.
  - **Who owes a re-solve, in the lane's own line:** **SPP** (→ SPP-50), **MISO** and **PJM** have keepers
    whose INPUTS moved; **CAISO / NYISO / NEISO** keys move but their keeper inputs are byte-identical or
    the move is ≤ 167 MW / 3.7 MW of clamped CT — owed on the letter of a moved key, inert in substance,
    their desks' cadence; **ERCOT owes nothing** (neither seam reaches its keeper, no ERCOT key moved).
- **GATES at the pin: ALL SEVEN EXIT 0.** `check_gate_a_provenance` is green again — the ERCOT and MISO
  rows red at r#13 were re-keyed by their own desks, so **R-av is DISCHARGED** without this desk acting,
  which is what routing is for.
- **DESK RECORD DUTIES EXECUTED:** plan §5 row + §9 index, `docs/calibration-log/spp.md` **spp-16**
  appended from the FINDING's own `## Log entry` block (renumbered at the desk — the lane proposed
  `spp-13`, already taken by SPP-46; **E-12's collision is now a per-sitting certainty, not a surprise**),
  this ledger, the CHANGELOG. The lane wrote its own matrix row + shard cells (its own files, §8.0 rule 2)
  and touched no shared record.
- **NO P15 CANDIDATE** — nothing was solved. Keeper-3 stands, NOT-YET unchanged.
- **ISSUED: SPP-50** [FABLE] — the batched re-baseline P19b ruled: **ONE** full-span invocation carrying
  SPP-48's wind repair (its parquets regenerated as the lane's first act) AND both SPP-49 seams, with a
  four-leg promotion rule pre-declared, the identity leg on the P0 objective and LP input arrays (never a
  warm-started P1 — E-8), keeper-3's 1.106808 wind identity re-verified, SPP-49 §0.5's attribution deltas
  as an acceptance leg, and the promotion served to the owner as **P15**, never taken by the lane.
- Next sitting: grade SPP-50 and serve its P15; route SPP-49 R-1 (the CLI flag) and R-2 (the third,
  still-unscreened F923 consumer) once the re-baseline is settled; SPP-54b after SPP-50.

### 0n. r#13 — sitting #13: SPP-46 / 47 / 48 ALL LANDED — **the C1-2024 gas split is a measured-INPUT defect, not a mechanism**; the wind LEVEL rule repaired; P16 executed. Card P19 served (2026-09-08, main HEAD `a667073f`)

- Pin `a667073f` (the r#12 desk branch was merged into `main`; branch fast-forwarded, nothing ahead).
- **GRADED BY CONTENT — three of three LANDED, ZERO LP spent across all three.**
  - **SPP-46 LANDED — BOTH R-17 CANDIDATES KILLED AT RULE-29 PHASE 0** (PR #5602,
    `FINDING-spp-46-2026-09-07.md`). (A) the P0-anchored form reaches ≤ 0.25 of the ST_GAS under-run
    against a declared 0.50 bar (0.007 as SPP-44 actually measured it), and the measured-STATE form
    **fails rule 13's forward test** — an observed commitment OUTCOME, the part-load form of the
    observed-generation pin rule 13 forbids by name. (B) reaching the 2024 split needs CT ×2.0 while the
    merit-order lane's derived per-class set moves CT **0.00 TWh**, and ~**100 %** of the CT over-run sits
    on rows whose own inputs are already flagged — so a band that closed the split would paper over the
    input defect (rule 14, refused on the input census and never on the residual).
  - **THE OBJECT, NAMED BY MEASUREMENT — and it is not a mechanism at all.** SPP's C1-2024 gas split is a
    **measured-input plausibility defect on three seams keeper-3 consumes at face value**: (1) EIA-923
    own-month gas prices with **no plausibility screen** — across the SPP states, **91 plant-months ≤ $0.50,
    31 NEGATIVE and 206 ≥ $10 of 5,707** (Elk Station at $0.16–0.41/MMBtu every month of 2024; Mustang CC
    at *negative* prices in seven months); (2) plant-level eGRID heat rates with no prime-mover floor —
    **Pioneer 57881 at 3.43 MMBtu/MWh on simple-cycle GTs**, carrying 763 MW of rows against a 427 MW
    nameplate, worth **+5,013 GWh** of the 2024 CT over-run alone; (3) **Harrington 6193** priced as
    1,018 MW of $1.48 gas steam while CAMPD has all three boilers burning **coal** through 2023–24. The
    **clean** CT cohort — 110 plants, 7,080 MW — reproduces to **−244 GWh**. That is the finding: the
    peaker fleet is fine, and three input seams carry the split.
  - **SPP-47 LANDED — P16 EXECUTED, repo-wide** (PR #5599, `FINDING-spp-47-2026-09-07.md`): **one
    executable line**, zero new parameters, the existing `ref <= 0.0` guard already supplying the
    "fuels EIA-930 reports" restriction. SPP-43 §6's five cells reproduce **to the digit**, and the lane
    found a **SIXTH** — NYISO 2022 oil (1.8437 → 4.8854), which rule 22's *what is held out is the SCORE,
    never the DATA* clause makes **required**, not optional, and which is not a holdout spend (nothing
    solved, scored or registered). Census exhaustive over 7 ISOs × every year; there is no seventh.
    **Every ISO's determination unchanged and the whole scorer report byte-identical** — with the
    mechanism given rather than asserted: `calibration_verdict.py` **never reads
    `calibration_reference.json`** (stdlib-only over committed sidecars and bench parts). No bench part
    went STALE; no desk routed.
  - **SPP-48 LANDED — the LEVEL rule repaired, and SPP-54's C-3 STOP DISSOLVED** (PRs #5592/#5601,
    `FINDING-spp-48-2026-09-07.md`). The defect is now stated exactly: the split is invariant to a COMMON
    rescaling of every zone's shape but **not to a per-zone one**, so the six-largest-plants subsample —
    covering **13.8 % to 100 %** of a zone's capacity depending on the zone — was an **undeclared per-zone
    free parameter multiplying the redistribution** (rules 21 / 24). **R-LEVEL** replaces it with the
    definition it was approximating: every EIA-860 operable wind plant in the zone, at its own coordinates
    and hub height, through the UNCHANGED shear law and power curve. `_SAMPLES_PER_ZONE` is DELETED — **net
    −1 free parameter, nothing added** — the shared rule lives once in `scripts/lib/wind_shape.py` with no
    ISO name, constant or branch (test-enforced, rule 25 intact), and the result is
    **partition-consistent** (`C_A·SHAPE_A + C_B·SHAPE_B ≡ C_C·SHAPE_C`), so re-cutting a boundary can no
    longer move another zone's weight. Rule 13's forward test is answered **more strongly than the rule it
    replaces**. Honest reporting at the gate: **h8509 still reads −75 MW** — the split-INDUCED infeasibility
    is gone, the hour's own margin problem is not, and the lane said so rather than claiming the pocket
    unblocked. The solve-path parquets were **not** regenerated, exactly as chartered.
- **GATES at the pin: six of seven EXIT 0. `check_gate_a_provenance` EXIT 1 — and NEITHER row is SPP's**:
  ERCOT's board row cites the superseded `2026-09-05-ercot248-two-config-keeper` (live:
  `2026-09-08-ercot256-drag-layup-mask`) and MISO's cites `2026-09-07-miso-233-spp-hourly` (live:
  `2026-09-07-miso-243-spp-pairing`). Both are those desks' Q34 standing re-key duty → **R-av**. SPP's own
  row is green and stays green.
- **DESK RECORD DUTIES EXECUTED.** All three lanes obeyed the r#11 collision rules — none touched a shared
  record — so the desk wrote every one: plan §5 rows and §9 index for all three, `docs/calibration-log/spp.md`
  entries **spp-13 / spp-14 / spp-15** appended from each FINDING's own `## Log entry` block, this ledger,
  and the CHANGELOG. **Numbering collision resolved at the desk, per E-12:** SPP-46 and SPP-47 both proposed
  `spp-13`; SPP-47 was renumbered `spp-14` and SPP-48 normalised to `spp-15`.
- **NO P15 CANDIDATE** — SPP-46 recommends none and says why: *issue the repair lane before any further
  gas-split lever.* Keeper-3 stands, NOT-YET unchanged. Eleven consecutive arms now killed or stopped.
- **TWO RE-BASELINES ARE NOW OWED, and the desk is batching them.** SPP-48's repaired builder is on `main`
  while the solve-path parquets are not regenerated — a deliberate, recorded state with **zero behaviour
  change** (the LP reads the parquet). Keeper-3 must be re-solved on the repaired wind input, and SPP-46's
  R-1…R-4 input repairs will move the same keeper's inputs again. Two re-baselines for what can be one LP
  span is waste, so the desk sequences: **input repairs first, then ONE re-baseline covering both.**
  MISO's keeper is owed the same re-baseline on its own side (SPP-48 R-3) → **R-aw**.
- **CARD P19 SERVED AND RULED IN-SITTING (§2): REPO-WIDE, BOTH SEAMS, ONE LANE** → **SPP-49** issued
  [FABLE]. The scope is closed and the construction named (the [0.5, 2.0] band on `N3045<ST>3` ÷ 1.037; the
  9.0 aero floor beside `_egrid_boundary_hr_repairs`' existing CC ceiling; SPP-46 R-7's empty-`state`
  prerequisite); the ONE question left open for the lane is **construction vs registered gate, per seam**,
  with its criterion stated so the answer cannot be chosen for convenience. It is required to record an
  **ex-ante cache-key census before either file is edited** — a seven-ISO marginal-cost change that
  silently re-keys ten keepers is the failure this catches.
- **SEQUENCING RULED (P19b): BATCH.** → **SPP-50 QUEUED**, issued when SPP-49 lands: ONE full-span
  invocation carries SPP-48's wind repair and SPP-49's input repairs together, so the keeper that emerges
  is identified against the final input surface rather than an intermediate nobody would keep. One LP span
  (~7 min by SPP-46's estimate) instead of two.
- Next sitting: grade SPP-49; issue SPP-50 the moment it lands; route the per-ISO re-solve list SPP-49
  produces to each desk; SPP-54b still waits on SPP-50 (its rating is settled by P18, its input is not).

### 0m. r#12 — sitting #12: ALL SIX W5/W6 LANES LANDED (five killed at their own gates, one LP spent); gate (a) GREEN; SPP-46 issued; cards P16 / P17 / P18 served (2026-09-07, main HEAD `6212108f`)

- Pin `6212108f` (2 commits since r#11 by count, but r#11's own merge is one of them — the substantive
  arrivals are the six lanes below, all merged before r#11's desk commit reached `main`). Branch
  fast-forwarded, no divergence, no conflict.
- **GRADED BY CONTENT — six of six LANDED, and exactly ONE LP was spent across all of them** (SPP-60's
  T1-H). Five arms died at a pre-registered gate, four of those at **zero LP**:
  - **SPP-45 LANDED** (PR #5554, `FINDING-spp-45-2026-09-07.md`): the identity re-key the charter named
    **had already landed** at `d26652f3` — a parallel Fable session firing the same Q34 standing duty —
    so the lane **did not redo it** ("re-keying an already-correct row would have asserted a supersession
    that did not happen"). It delivered what was still owed: the **promotion instrument**
    (FINDING-spp-43 ADDENDUM A) in the row's `detail`, the MISO row's `corrected_by` sha, and the two
    record annotations. `check_gate_a_provenance` **EXIT 0** — the desk's one red gate since r#9 is closed.
    No marker claimed, requested or implied (rule 22).
  - **SPP-58 LANDED** (PR #5566, `FINDING-spp-58-2026-09-07.md`): ψ₂ = DC power-flow PTDF/OTDF on a reduced
    network built from public HIFLD line geometry + EIA-860 coordinates — **reads no price, no shadow
    price, no binding hour, no model output**, and is year-invariant by construction. It is **OUTSIDE the
    pre-declared disagreement band on every object**: N↔S T*₂ **11,022 N→S / 13,175 S→N** against ψ₁'s
    3,400 / 4,206; SPS tie **1,600 MW** against SPP-57b's 10,705. `ttc_mw` **untouched** as chartered
    (outside the band ⇒ a card, never an edit). The structural reason is now measured, not asserted: ψ₁
    rests on **Franklin 161/69** (44 % of the corridor's binding hours) and an under-lay set that ψ₂
    **cannot see** — HIFLD's 2023 edition carries nothing below 115 kV — while ψ₂ rests on the 345 kV
    backbone (Cooper–St Joe). **CARD P18.**
  - **SPP-54 LANDED — DESIGN COMPLETE, NO SOLVE** (PR #5567, `FINDING-spp-54-2026-09-07.md`): the
    three-zone SPS / Texas-Panhandle pocket is fully designed, censused and tested on the branch
    (design commit `8d427adc`; ≈ 6.8 GW thermal + 4.65 GW wind against a 3.0–6.4 GW load, thermally
    self-sufficient at its own peak, an overnight exporter), and the **solve path was restored to
    `origin/main`'s bytes before the PR** — so HEAD is still two zones / one 3,400 MW link (verified).
    It **STOPPED pre-solve at h8509** on the R-18 wind reconciliation, which passes both identity legs
    (Σ_z cap·cf = M(t) to 6e-16; no capacity overflow) and fails feasibility in one window hour. The
    cause is measured: the redistribution weights each zone by `cap_z · SHAPE_z(t)`, so a **six-site
    sample's relative mean LEVEL acts as a zonal capacity-factor level** — splitting the old South moves
    the North's annual potential **+1.38 / +1.47 / +1.91 TWh at an identical system total**. **CARD P17**
    (it reaches MISO's `build_miso_wind_shape.py` through the shared `_SAMPLES_PER_ZONE` construction).
  - **SPP-51 LANDED — KILLED AT RULE-29 PHASE 0, NO LP** (PR #5573, `FINDING-spp-51-2026-09-07.md`):
    three adjudications made and pinned by test — (a) a **per-ISO** anchor map in
    `derive_neighbor_hr_by_year.py` (an ISO with no map now fails); (b) the SPP-33 R2 **HH + basis**
    correction (`MISO_West` 10.55, `MISO_South` 9.63, `AECI` 10.23, `ERCOT` 16.78); (c) **ERCOT 835 MW**
    on rule 14 (the measured clip on both EIA-930 and SPP's own meter, corr +1.0000; 820 would refuse
    547 / 128 / 21 recorded hours — ERCOT's own row untouched, rule 25). The screen was never reached:
    the mechanism's **own identity — flow follows spread — fails on the measured record** in every year
    and both runs (sign agreement 0.436–0.501 against a 0.55 bar; corr(spread, import) ≈ 0). The real
    SPP↔MISO flow is scheduled / JOA / loop flow, which is **why MISO's own keeper prices this seam as a
    measured hourly-anchored offset ladder**. Residual-blind: the gate read no C3a/C3b/C3c.
  - **SPP-55 LANDED — KILLED AT ZERO LP** (PR #5565, `FINDING-spp-55-2026-09-07.md`): the object was
    corrected from SPP's own protocols to the published **Contingency Reserve Demand Curve
    ($275 / $550 / $1,100)** and lands **default-off under the shared `energy_reserve_coopt` gate — no
    new field**. Leg (i) of the STOP gate was decided from keeper-3's committed sidecars: reserve-eligible
    thermal headroom falls below the 1,500 MW requirement in **0 / 1 / 0 hours** of 2023 / 2024 / 2025 and
    in **0 of the 4 / 3 / 7 measured hour-long shortage hours** — the family is **INERT on keeper-3's
    dispatch**. And the C3c tail is **not a reserve object**: **1 / 0 / 0** of 42 / 59 / 68 C3c hours carry
    any reserve-short interval, median RT LMP in the shortage hours $32–36. C3c is a **5-minute RT
    price-formation object** — the desk stops routing it to reserve mechanisms.
  - **SPP-60 LANDED** (PR #5564, `FINDING-spp-60-2026-09-07.md`): **SPP's first T1-H is registered** —
    `spp-2021-2025-realized-t1h-spp60`, key `e586d7cae19eab13` (the pre-declared key, matched), verdict
    `spp-t1h` **HOLD / FC-3 FAIL at full magnitude** — the same reading every ISO's bare T1-H has at HEAD.
    The gap table is closed: the 2020-vintage `eia860_generators.parquet` gained its **1,527 SWPP rows**
    with the six existing BAs byte-for-byte preserved (the first launch had died at fleet build),
    `capacity_actuals_spp.csv` **built** (110 retirements / 2.2 GW; 185 additions / 13.9 GW), and SPP's
    **first confirmed-retirement rows** landed (Tolk 1/2, NMPRC 22-00286-UT, deferred to 2029-03 by the
    2026-05-07 IRP approval). Step 5 decided **0 MW in every year and every tech**; step 3 retains every
    non-nuclear thermal class through the admission cap. `GOLDEN_ISOS` untouched.
- **GATES at the pin — ALL SEVEN EXIT 0**, and gate (a) is green for the first time since r#9:
  `audit_keepers --check` 0 · parity 0 (19 runs, 52 bundle dirs, keeper-only retention holds) ·
  **`check_gate_a_provenance` 0 (7 rows)** · bench freshness 0 STALE (SPP 2023/24/25 carry engine drift
  warnings only — reproducing payloads) · goldens OK · refactor-guards OK · mechanism-matrix 0, integrity
  + keeper stamps + §5.x prose + all three ratchets, re-run with `--base bfbb0b6a` for the new-field limb.
- **DESK RECORD DUTIES EXECUTED** (plan §8.0, first sitting under the r#11 rules): the six lanes had all
  been issued **before** the collision fix, so each still wrote its own plan/log/shard rows; the desk
  verified rather than re-wrote them, and supplied the four they left: plan §5 rows SPP-45 / SPP-58 →
  LANDED, plan §9 SPP-45 row, plan §4 r#12 block, and this ledger. Calibration-log entries spp-9 (SPP-58) /
  spp-10 (SPP-55) / spp-11 (SPP-54) / spp-12 (SPP-51) verified present; SPP-45 (records) and SPP-60
  (forecast namespace) owe none. SPP shard verified at keeper-3 with the four new cell verdicts
  (`priced_interchange` / `reference_price_interface` U → **R**; `energy_reserve_coopt` U → **I**;
  `measured_interface_limits` stays **O** with the SPP-54/58 evidence appended). **One shared-record
  repair the desk made itself** (SPP-54 R-25): `docs/codebase-site/data/iso-topologies.json` still carried
  the **48,700 MW placeholder** for the N↔S link seven sittings after SPP-53 landed 3,400 — corrected,
  and it now matches `get_iso_config("SPP")` exactly.
- **NO P15 CANDIDATE — keeper-3 stands, and every one of the five structural arms recommended against
  itself.** That is now **eight consecutive killed arms** on SPP (SPP-57, 57b, 44, the price family, 51,
  55, plus 54 and 58 stopped before a screen). The determination is unmoved: NOT-YET on C1-2024 (gas
  split), C3a-2023, C3b 2023/24, C3c all years.
- **CARDS SERVED (§2): P16** (re-served — the reference hydro/oil vintage repair, five cells in four
  ISOs), **P17** (SPP-54 R-21 — the wind-shape builder's per-zone level rule, which reaches MISO's
  builder), **P18** (SPP-58 R-21/R-22 — the two identifications of the N↔S link, 3,400 vs 11,022, and the
  SPS tie, 1,600 vs 10,705).
- **ISSUED: SPP-46** [FABLE] — the C1-2024 gas split, SPP-44 R-17's two admissible objects, phase-0 first.
  **BLOCKED ON CARDS, not issued: SPP-54b** (the pocket's rating + solve half — it needs P17 *and* P18)
  and any `ttc_mw` question (P18). **SPP-56 stays LAST** (P4), now with its non-inertness instrument
  (`docs/handoffs/spp55/headroom.py`, SPP-55 R-22).
- **am.1 — ALL THREE CARDS RULED IN-SITTING (2026-09-07).** **P16 → REPO-WIDE, one rule, all five cells**
  → **SPP-47** issued [OPUS]. **P17 → SHARED builder repair, each ISO re-derives its own numbers**
  → **SPP-48** issued [OPUS] (re-assigned from FABLE in-sitting: with the construction NAMED by the desk, nothing in the lane is an adjudication), with the landing sequenced by the desk (its repaired parquets are NOT
  merged while SPP-46 solves against keeper-3 — a changed wind input is a LIVE hunk that would invalidate
  SPP-46's rule-29(b) form-4 control mid-flight). **P18 → KEEP 3,400, record ψ₂ as unresolved**: `ttc_mw`
  is not re-keyed, SPP-54b will rate the South↔SPS link at **ψ₂'s 1,600 MW** (the only identification that
  saw it) and state the disagreement at its gate; SPP-58 R-23's missing 69 kV under-lay stays open (R-aq).
- **THREE LANES ISSUED r#12, files disjoint by construction, safe in parallel:** SPP-46 (the gas split —
  the LP lane, and the only one that solves), SPP-47 (the reference vintage rule — zero-LP, scoring side),
  SPP-48 [OPUS] (the wind level rule — zero-LP, builders only, landing held). **SPP-54b stays UNISSUED**: P18
  gives it its rating but P17's repair must land first, and that is gated behind SPP-46.
- Next sitting: grade SPP-46 / 47 / 48; sequence SPP-48's landing and any keeper-3 re-baseline it
  recommends; issue SPP-54b once the wind repair is on `main`.

### 0l. r#11 — desk act: the PR-collision fix (2026-09-07, main HEAD `bfbb0b6a`)

- Pin `bfbb0b6a` (56 commits since r#10, none SPP's; branch fast-forwarded). No lane graded — none of the
  six issued lanes has a branch yet.
- **THE DEFECT (E-10):** the desk's own house style told every lane to "update this plan's §5 row status and
  the ledger pointer in the same PR", and the charters' EXIT lines said "plan §5 row → LANDED". Six-plus
  lanes therefore edited the same two tables, the same log tail, the same CHANGELOG top and the same shard
  stamp — so each merge invalidated every open PR (SPP-57: 4 PRs; SPP-43: 3; SPP-57b merged `main` into
  itself twice to keep one table row; the desk branch itself diverged twice).
- **THE FIX (plan §8.0, handoff §5, standing):** a lane touches NO shared record — its FINDING (with a
  `## Log entry` section) and its own shard cell line are its whole footprint; the DESK moves plan rows,
  appends the log, writes the CHANGELOG line and re-stamps the shard at each refresh; rebase never
  merge-in; one PR per lane, opened when done. A STANDING RULES block is pasted into every lane session.
- P16 still pending. Next sitting: grade whatever launched; execute the desk's new duties for each LANDED lane.

### 0k. r#10 — sitting #10: SPP-44 LANDED (screen KILLED — the gas problem is never-started units); SPP-55 issued; P16 still pending (2026-09-07, main HEAD `32516df6`)

- Pin `32516df6` (8 commits since r#9). The desk branch had diverged (main took SPP-44's plan rows while
  r#9 sat unmerged) → **rebased onto main**, the plan's §5/§9 conflict resolved by keeping BOTH the lane's
  SPP-44 LANDED rows and the desk's r#9 rows; r#9 replayed as `ac7256d5`.
- **GRADED BY CONTENT. SPP-44 LANDED** (`claude/spp-44-gas-commitment-bridge-ljv87g`, PRs #5519/#5535,
  `FINDING-spp-44-2026-09-07.md`): the 2023 screen **KILLED as pre-registered** on legs (i) and (iii) —
  CC window agreement with CAMPD 0.694 against a 0.76 bar (lift +0.034 over the unconditional online
  fraction: no better than chance) and a D-4 unit-conduct FAIL at five laid-up / capacity-only plants
  (CC 201, 3604, 8000, 55178; ST_GAS 3485). The mechanism was built as declared and FIRED (7,091
  unit-hours, 0.414 TWh, D-2 forced share 0.5 %) — but it reaches a TENTH of the 4.2 TWh measured
  committed-state gap, because **a bridge can only refuse to stop a unit the model itself started, and
  SPP's gas problem is units the model never starts** (62 % of CC and 78 % of ST_GAS P0 runs dropped as
  phantom). ST_GAS window agreement 0.968: the steam fleet IS the committed-state object, unreachable from
  P0. Displaced energy was coal, not CT (CT −0.044 TWh, below the noise floor). Field
  `spp_gas_commitment_bridge` LANDED default-off (seven keys unmoved), matrix row + 7 cells, SPP cells
  `gas_commitment_bridge` / `spp_gas_commitment_bridge` U → **R**; both bundles deleted before the PR.
  Also on main: the SPP status part rebuilt after SPP-43 (audit_keepers S1), and the capx director's r#58
  entry recording that the Q59 board row "goes stale within hours on this desk's own gate (a) red" —
  SPP-45 is the repair.
- **GATES at the pin:** audit_keepers 0; parity 0; bench 0; goldens 0; refactor-guards 0; matrix 0 (with
  SPP-44's row); **gate-(a) EXIT 1 (SPP row, SPP-45 issued r#9, not yet launched)**.
- **P16 remains PENDING** (served r#9; the owner's click was accidental and the answer is withdrawn — no
  ruling recorded; the reference vintage is untouched).
- **NO P15 CANDIDATE.** **ISSUED: SPP-55** [FABLE] — the hold lifted because SPP-44's every-shard 28c edit
  is merged: an in-LP reserve demand curve on SPP's published VRL steps ($250/MW spinning, $50,000/MW power
  balance), MISO-RBDC form, requirement from SPP's own rule, footprint from the measured RTBM MCPs (read
  for the gate, never priced on — P4 stands: SPP-56 is still LAST), with the SPP-44 R-17 guard (the curve
  prices scarcity, it does not start plants). **QUEUED, not issued: SPP-46** — SPP-44 R-17's two
  admissible next objects for the gas split (a measured commitment-STATE input on ST_GAS with duty
  membership — the ercot141 / nyiso-146b construction on SPP's own conduct — or a per-class differentiated
  band under the carve-out, pre-registered); issued after SPP-55 lands (28c) unless SPP-55 needs no field.
- Next sitting: grade SPP-45 / 58 / 54 / 51 / 60 / 55 as they launch; P15 for any candidate; SPP-46.

### 0j. r#9 — sitting #9: KEEPER-3 (owner ruling); SPP-57b KILLED; SPP-38 landed; SPP-44 running; two owner-launched lanes recorded; SPP-45 / 58 / 54 / 51 / 60 issued (2026-09-07, main HEAD `7b8f3699`)

- Pin `7b8f3699` (110 commits since r#8; the desk branch merged as PR #5505). Branch fast-forwarded.
- **GRADED BY CONTENT.** **SPP-43 LANDED** (`claude/spp-43-screened-rebaseline-2ro0x8`, PRs #5512/#5521/#5526):
  the re-solve REGISTERED and STOPPED on its own leg (i) — the 2024/2025 P1 objectives are not bit-identical
  to keeper-2's (same P0 objective, same inputs, a different vertex of the same optimal face under the
  cross-year P1 basis seed); legs (ii)–(iv) met; the year-invariant curtailment gross-up identity 1.106808
  now holds in all three years (2023 had read 1.06985 — exactly the h3907 artifact). The owner ruled
  in-session (P14 applied a third time) → **KEEPER-3 `2026-09-07-spp-3-screened-input`**, NOT-YET on the
  same four criteria; keeper-1 and keeper-2 PRUNED; C1/C4-2023 wind scored for the first time;
  `bench/SPP/2023` 288.201 → 284.616 TWh (SPP-41 R-10 discharged). **SPP-38 LANDED** (PR #5522): of the
  fifteen "SPP-era" red tests, FOUR were SPP's (two new campaign configs; assertions extended); eleven were
  three unrelated defects (a stale SCN skip guard ×5, an unbuilt `data/clean` ×3, NYISO marker drift ×2, the
  miso-233 parity-registry debt ×2 — still red, MISO's). **SPP-57b LANDED** (PRs #5513/#5527): the 2025
  screen KILLED as pre-registered — the corridor-only N↔OK link at 3,400 is LIVE 23.5 % and 93 % N→OK (the
  correction worked), but the sps_tie link (rated 10,700, named OK→S) never binds because the residual
  bubble flows the OTHER way in every percentile above the median: **directionally misaligned, not too
  wide** (R-17 → SPP-54 first); unserved rose 89 → 444 MWh through the per-zone wind rebuild (R-18);
  topology not landed. **SPP-44 RUNNING**: PRECOMMIT landed (PR #5519) — CC 0.209 / ST 0.090 plant-basis
  min-load, min-run 15 / 5 h, 45 eligible plants, screen year 2023 by footprint (4,209 GWh, carried by
  ST_GAS: the keeper runs gas steam at zero in 5,914 hours where the real fleet holds ~800 MW at minimum
  load); branch open, no FINDING.
- **TWO OWNER-LAUNCHED LANES, off-desk, recorded (not chartered here):** (1) **SPP PRICE FAMILY** (PRs
  #5533/#5534): phase 0 showed SPP's price surface is LOAD-driven (corr(price, load) +0.78 vs gas +0.27;
  SPP inverts PJM); the uniform `offer_curve_by_group` quadruple was KILLED on its structural leg — it
  moved the level −9 % as predicted and did NOT steepen the stack (1.62 → 1.63 vs ≥ 1.78 required) —
  while taking C3a-2025 +7.2 % → −2.5 % and C3b 0.189 → 0.171. Rejected anyway (rule 1 / carve-out (c)).
  `R` for SPP as a uniform quadruple; a per-class curve is a different, open question; C3c is a separate
  object (spikes at ordinary load, 79–93× gas) → SPP-55; C1-2024 is a `pct_peaking` structural share →
  SPP-44's territory. (2) **capx Q59 BOARD ROW** (PR #5528, the capx director's lane): the §2.1b SPP row
  written from backcast artifacts; **Q59 split SPP's forecast onboarding — the board-row half to capx, the
  T1-H recipe + forecast intake half TO THIS DESK** (supersedes P8's "route W6 to capx" for that half) →
  SPP-60 chartered. The row cites keeper-2, so **gate-(a) is RED on SPP at the pin** → SPP-45.
- **GATES at the pin:** audit_keepers 0; parity 0; bench 0; goldens 0; refactor-guards 0; matrix 0;
  **gate-(a) EXIT 1 (SPP row F-5, ours to re-key — SPP-45)**. Surfaces: only `spp43_screened_B` +
  `2026-09-07-spp-3-screened-input` remain (keeper-only retention holds); shard stamped; log spp-5/spp-6.
- **NO P15 CANDIDATE** (57b and the price arm both killed). **P16 SERVED** (§2): SPP-43 §6's one-rule
  reference-hydro vintage repair reaches five cells in four ISOs (SPP/MISO/NEISO 2025 hydro, NEISO 2025
  oil, NYISO 2023 oil) — a shared-file, cross-ISO benchmark change, so it is the owner's.
- **ISSUED (parallel): SPP-45** [OPUS] board-row re-key + two record annotations; **SPP-58** [FABLE] ψ₂ —
  an identification independent of the hub-spread × shadow-price regression, with a pre-declared
  disagreement band (3,400 stands inside it; outside → card, never an edit); **SPP-54** [FABLE] the SPS
  pocket — design, census and the R-18 wind reconciliation now, link rating after SPP-58, solve after
  that, screen year 2024 (largest sps_tie footprint); **SPP-51** [FABLE] the priced seams with SPP-33's
  R1/R2 and the ERCOT clip adjudication; **SPP-60** [FABLE] the T1-H recipe + forecast intake per Q59.
  **HELD: SPP-55** until SPP-44 lands (both add a `ScenarioConfig` field → the 28c every-shard edit
  collides). Next sitting: grade six; P15 for SPP-44 / SPP-51 / SPP-54 if any reports a candidate.

### 0i. r#8 — sitting #8: W4b ALL LANDED — KEEPER-2; SPP-57 screen KILLED; SPP-43 / SPP-38 / SPP-57b / SPP-44 issued (2026-09-07, main HEAD `b054988c`)

- Pin `b054988c` (123 commits since r#7; the desk branch itself merged as PR #5460). Branch fast-forwarded.
- **GRADED BY CONTENT — five lanes LANDED 2026-09-07.** **SPP-42** (`claude/spp-42-coal-hydro-5y1z3h`,
  PR #5471, ran as Fable; the owner launched it immediately, NOT after SPP-36/41 — it derived the coal
  crosswalk itself): **KEEPER-2 `2026-09-07-spp-2-crosswalk-hydro`**, determination **NOT-YET** at full
  magnitude, promoted under its charter's rule (no load-bearing PASS → FAIL). Movement vs keeper-1:
  C3a-2025 +21.7 % → +7.2 % PASS; C3b-2025 0.283 → 0.189 PASS; unserved 2,007 MWh/6 h → 89 MWh/1 h
  (the survivor is a South shortfall behind the bound corridor — the SPP-57 object); C5a −67 % → −3 %;
  C1-2023 every class in band; C1-2024 the gas split alone (CC −8.6 / CT +9.9 TWh); C3c 24 → 1 h in
  2025. The 2025 screen missed its literal "unserved → 0" leg and the lane proceeded on rule 14 with the
  miss stated (§2.3) — the desk accepts that reading (E-7 below). **SPP-36** (PR #5480): the gate record;
  its artifact converged byte-identically with SPP-42's (rule-23 check). **SPP-41** (PR #5497): ONE seam;
  the SPP-31 two series + one input series move, nothing else across 7 ISOs × 2019–2026; seven keys
  unmoved — but it landed AFTER keeper-2 was solved, so keeper-2's 2023 wind input (+27 GWh) and
  `bench/SPP/2023` (wind 106.634) still carry the slip. **SPP-37** (PR #5474): six leftovers closed.
  **SPP-57** (PRs #5479/#5483/#5493/#5496): the 2025 screen **KILLED as pre-registered** — the union rule
  pooled `oklahoma_internal` into the N↔OK set and rated both links 6,500 / 6,700 MW; neither is live
  (2.5 % / 0 %), the pocket traps nothing, negative hours 6 → 0. Topology NOT landed (solve path restored
  byte-identical to keeper-2's); design, instruments, the measured EIA-861 CSWS split and the T* tables
  landed for the re-issue (commit `f5926636`). The owner asked the lane in-session whether it was a
  candidate; the lane answered NO under P14 (structure regressed).
- **GATES at the pin: ALL SEVEN EXIT 0** (audit_keepers 0 — someone rebuilt ERCOT/PJM status parts;
  parity 0 — every screen bundle deleted before merge; bench 0; goldens 0 with the pre-existing ERCOT/
  NEISO STALE notes; refactor-guards 0; matrix 0). Registration surfaces verified: keeper-2 sidecar +
  payload, `keepers/SPP.json` (`keeper_previous` = spp-1), status, bench ×3, shard stamp, §5.7 header,
  log spp-3/spp-4. Keeper-1 is still registered — rule 15 prunes it at the NEXT registration (SPP-43).
- **NO CARDS.** P15 has no candidate (SPP-57 killed; keeper-2 promoted under a pre-declared rule).
- **ISSUED (all parallel): SPP-43** [OPUS] keeper-2's recipe re-solved through the SPP-41 seam → keeper-3
  candidate, identity check (2024/2025 objectives identical), C1/C4-2023 wind scored for the first time,
  prunes keeper-1/-2, folds N-1/N-2 + the R-15 / plant-6193 zero-LP reports; **SPP-38** [OPUS] the 15
  SPP-era red tests at HEAD in the SPP-20 pattern (never GOLDEN_ISOS / program-status); **SPP-57b**
  [FABLE] R-12 — N↔OK = `n_s_corridor` alone (3,400, live N→OK-dominant 2,065 h in the killed screen's own
  flows), OK↔S = `sps_tie` alone on (p_S − p_OK), `oklahoma_internal` excluded from both, same gate; screen
  control keeper-2 (the seam moves no 2025 series); **SPP-44** [FABLE] the gas split as a P1-native
  commitment bridge (SPP-42 §7's rule-19 enumeration: nothing floors CT today), measured from SPP's CAMPD
  conduct by the NYISO construction, a new ISO-exclusive field with its matrix row (28c).
- Next sitting: grade the four; serve P15 if SPP-57b or SPP-44 reports a candidate; then SPP-51 (Fable),
  SPP-58 (ψ second identification — R-14 makes it load-bearing for every FCITC rating that admits
  Oklahoma-internal elements), SPP-54 (start from SPP-57 R-13's table, not the P1 prose).

### 0h. r#7 — sitting #7: FIRST SPP KEEPER LANDED (NOT-YET, owner direction); SPP-35 landed; SPP-41 unlaunched → v2; W4b repairs + SPP-57 issued (2026-09-07, main HEAD `8a4bfd29`)

- Pin `8a4bfd29` (109 commits since r#6). Branch fast-forwarded.
- **GRADED BY CONTENT.** **SPP-40 LANDED** (`claude/spp-40-first-solve-pvanrx`, PRs #5425 / #5434 /
  #5446 / #5447; `PRECOMMIT-spp-40` pushed at `45d02b0e` before the solve; `FINDING-spp-40-2026-09-07.md`).
  The rule-29(a) 2024 screen was **KILLED as pre-registered** on the direction leg — link live at bound
  1,776 h (20.3 %) but 877 N→S / 899 S→N, a 22-hour tie against a 1.7:1 N→S-dominant market; legs B/C/D
  passed. The owner then ruled in-session (**P14**, §2) and the full span was solved (369 s, 5.25 GB)
  and registered as the **FIRST SPP KEEPER `2026-09-07-spp-1-baseline`**, determination **NOT-YET** at
  full magnitude (C1 FAIL, C3a/C3b/C3c FAIL; C2/C4/C6/C8 PASS). DoD rows 1–5 MET. The tie was
  2024-specific (2023 1,702/275, 2025 1,245/373). Reported not tuned: |S−N| ~$1 vs $12–17; 7–9
  negative hours vs ~1,000; 0.0 % re-curtailment; CT over / CC+ST under; 2025 unserved 2,007 MWh.
  Registration surfaces verified at the pin: `keepers/SPP.json`, `index.json` (7), `status/SPP.js`,
  `bench/SPP/{2023,2024,2025}`, registry + 743 KB payload, `spp40_baseline_B/` + `hourly/`, shard
  stamped (`measured_interface_limits` U → O), log spp-1/spp-2, §5.7 header re-stamped. The lane also
  found and neutralised a **rule-25 breach** (SPP had inherited ERCOT-fitted COAL bands) BEFORE solving.
  **SPP-35 LANDED** (`claude/spp-35-seven-iso-prose-ypsq70`, PR #5440): S-1/S-2/O-4/O-6 closed; six
  leftovers routed (→ SPP-37). **SPP-41 NOT LAUNCHED** — no branch, no FINDING; the seam is untouched
  (`_screen_fuel_spikes` still only in the builder). Re-issued as **v2** (same stem) widened to the
  wind-INPUT path SPP-40 §4 found (the same h3907 slip reaches the delivered wind profile, +27 GWh).
- **GATES at the pin:** parity 0; gate-(a) 0; bench-freshness 0 (29 parts); goldens 0 (three
  pre-existing STALE notes, NEISO/ERCOT, not ours); matrix 0 (one anchor-digit warning, not ours);
  refactor-guards 0 (after `pip install numpy …` — the container had lost its deps; not a repo state);
  `audit_keepers --check` **EXIT 1 — S1 stale `status/ERCOT.js`, `status/PJM.js`** (MISO's cleared;
  PJM's new) — §3 R-s.
- **NO CARDS SERVED. Desk acts within P1 / P7 / P14 as ruled:** (1) SPP-40's R-1 (re-issue with a
  re-cut direction leg) is MOOT — the full span is the keeper and the 29(b) control. (2) The three
  score/input defects SPP-40 named are ZERO-DOF data repairs, so they are chartered as **W4b**:
  **SPP-36** coal supply class (`derive_coal_supply.py --iso SPP`, CLI verified by the desk against
  `--help`), **SPP-37** SPP-35's six leftovers, **SPP-42** the 2025 hydro vintage repair
  (`--hydro-backfill-year 2024`, the CAISO/PJM/MISO/NEISO precedent; matrix row
  `hydro_vintage_input_repair`) folded with ONE full-span re-baseline after SPP-36 + SPP-41, under a
  promotion rule declared in its PRECOMMIT (any ambiguity STOPs → card). (3) **SPP-57** issued in
  full — design now, solve after SPP-42 — with the STOP gate carrying **ex-ante dominance
  thresholds** (E-6). Promotion of any W5 candidate is a card (P15), never the lane's act.
- **Collision check (§4):** the MISO lane promoted `2026-09-07-miso-233-spp-hourly` (MISO's priced SPP
  seam, rule 25 — MISO's own); `git diff 7347933c..8a4bfd29` on `iso_configs.py` / `interchange/` /
  `spp_seam_*` is EMPTY, so no SPP object moved. Its bundle `miso233_sppseam_K` is MISO's.
- ISSUED: SPP-41 v2, SPP-36, SPP-37 (parallel, now); SPP-42 (after 36 + 41); SPP-57 (design now).
  Next sitting: grade all five; serve P15 if SPP-42 STOPs or SPP-57 reports a candidate; then SPP-51
  (Fable) and SPP-58 in ranked order.

### 0g. r#6 — sitting #6: W3 ALL LANDED; SPP-40 owner-launched; C4-2023 blocker relayed; SPP-41 + SPP-35 issued (2026-09-07, main HEAD `7347933c`)

- Pin `7347933c` (branch fast-forwarded from `9bdd0709`; the two newer merges are MISO/PJM lanes, no SPP
  touch). **Owner note: "spp 40 has launched."** No `claude/spp-40*` head is visible on origin at the
  pin, so per the standing line SPP-40 reads **RUNNING (owner-launched), branch unconfirmed**.
- **GRADED BY CONTENT — six lanes LANDED 2026-09-07:** SPP-30 (#5378), SPP-31 (#5389), SPP-32 (#5396 +
  #5399), SPP-33 (#5377), SPP-34 (#5388), SPP-53 (#5374/#5383/#5393). SPP-40's four preconditions
  verified at the pin: `_spp_config` link `ttc_mw = 3400.0` (not the 48,700 placeholder); outages
  `campd-unit-outages-SPP.csv` + siblings; `actual_lmp.json` / `calibration_reference.json` SPP
  blocks; clean zonal shares + wind shape + `meanzero.py` basis rows.
- **GATES at the pin:** parity 0 (16 runs / 49 dirs), gate-(a) 0, bench-freshness 0 (26 parts),
  goldens 0, refactor-guards 0, matrix 0 (7 shards). `audit_keepers --check` **EXIT 1 — S1: stale
  `status/ERCOT.js` and `status/MISO.js`**, neither this desk's (§3 R-k). `keepers/index.json` still
  six; no SPP bundle exists yet, as expected.
- **BLOCKER FOUND FOR SPP-40, relayed as an addendum, not a re-charter.** FINDING-spp-31 §3.3/§5a:
  the P9 `NG:` spike screen closed only inside `calibration_reference.json`; the C4 scoring path
  (`run_calibration_full._eia930_frame_generic` → `e930.parquet` → `bench/`) calls the loader
  unscreened, so SPP 2023's C4 would score wind against +3.5857 TWh (one hour, h3907). → **SPP-41
  chartered (Fable)**: move the screen into `load_eia_hourly_benchmark`, zero-LP two-series proof
  first (SPP 2023 wind, NYISO 2024 `other`), cache-key + bench-freshness consequence audit. SPP-40
  told to report C4-2023 as UNSCORED pending SPP-41; the desk re-renders bench/SPP/2023 afterwards
  (no re-solve — the LP never reads the benchmark).
- **SPP-35 chartered (Opus)**: SPP-34's S-1 (five stale "six ISOs" sentences in CLAUDE.md / spec /
  codebase README / user manual) + S-2 (ISO badge contrast, five of seven fail WCAG AA; the passing
  `.badge--iso-*` pattern already exists) + SPP-20's O-4 / O-6 doc items.
- **W5 reshaped from W3 evidence (no card needed — desk acts within P1/P13 as ruled):** SPP-51 is
  re-labelled **Fable** — SPP-33's R1 (anchor map) and R2 (`HH + gas_basis` heat-rate correction:
  10.09 / 10.23 / 16.78 vs the registered values) and the ERCOT 820-vs-±835 MW clip question are
  adjudications riding the same PR; **SPP-58** added (asymmetric pair 3,400 / 4,206 MW with a second
  ψ identification, after SPP-57); **SPP-59** reserved (SPP-32's R-3/R-4/R-5 consolidations — MISO
  files, held for the MISO lane's consent). SPP-33's R3 (`_HR_GAS_ELASTIC` global key) stays with
  the desk as a W5 card (§3 R-n) — it is forward-only and inert for the keeper.
- **CHARTER DEFECTS FOUND BY THE LANES, corrected here (§6 E-5):** `derive_cc_committed_pct.py` in
  the SPP-30 sequence (ERCOT-only legacy, would have overwritten ERCOT's file); `hubs.py` named as
  the SPP-32 basis home (it is `basis/meanzero.py`); the SPP-30 charter's "zero full-year fallbacks"
  gate was unachievable as written (every ISO carries `eia923_netzero` units) — the lane reported 9,
  itemised, inside the cross-ISO band, and the desk accepts that as the gate's intent.
- ISSUED: SPP-40 ADDENDUM (into the running session), SPP-41, SPP-35. Next sitting: grade all three;
  when SPP-40 lands verify `keepers/SPP.json`, `index.json`, `status/SPP.js`, `bench/SPP`, the shard
  stamp; after SPP-41 re-render + re-score C4-2023; then W5 in ranked order (SPP-57 → SPP-51 → SPP-58 …).

### 0f. r#5 — sitting #5: SPP IS REGISTERED; SPP-14/15/20 landed; P1 ranking applied; P13 ruled; W3 + SPP-53 issued (2026-09-07, main HEAD `96a6c4b3`, 01:35 UTC)

- Pin `96a6c4b3` (137 commits since r#4). Branch fast-forwarded. **Needs-registration line (E-4
  standing): SPP-20 has merged — nothing is gated on registration any more.**
- **GRADED BY CONTENT.** SPP-20 **LANDED** (PR #5329, `claude/spp-20-topology-market-design-1iew99`,
  `FINDING-spp-20-2026-09-06.md`): `SUPPORTED_ISOS` = 7; SPP-North 0.5125 / SPP-South 0.4875; voll 2000;
  PRM 0.16; TAIL 200; `SURFACE_ISOS` = 7; overrides `{}`; six keepers unmoved (0 moved surface rows,
  persisted identity 23/23, MISO keeper `fleet_only` hash-identical); 15 six-tuple tests extended, 3
  documented exclusions. **The N↔S link is a 48,700 MW PLACEHOLDER that cannot bind** (no public
  rating; SPP-20 §5 R-6) → card P13. Eight routed items (§3 R-i…R-p). SPP-14 **LANDED** (PRs #5335,
  #5341; two parallel sessions → an add/add collision on the FINDING, salvaged onto main by the owner's
  lane as `df5e8c3d` / `3cfb73bc`; both reports kept): `portal.spp.org` answered anonymously on
  2026-09-06 (the SPP-12/13 block did not reproduce; UA-independent); rows 5–9 ALL SERVED from SPP's own
  files; per-hub parquet promoted under the cross-check gate (sha256-identical system rebuild); hourly
  \|N−S\| mean/p90: **2024 widest on both legs, both markets** (RT mean 17.23 vs 12.13 / 15.18; p90 41.4
  vs 28.5 / 36.2) → **P7 stands on the hourly measure**; the four-group table served (below); RTBM
  effective limits exist only from 2026-01-28 (§5.4). SPP-15 **LANDED** (PR #5333): 12 back-year CEMS
  parquets, 4 sub-BA files, interchange widened 2019–2025 with the 2023–25 slice byte-identical, gas
  back years; blocked table EMPTY.
- **P1 RANKING APPLIED (desk act under the ruled test, no card).** `oklahoma_internal` 0.603 / 0.681 /
  0.648 of hours at $188 / $229 / $331 mean \|shadow\| ≥ `n_s_corridor` 0.555 / 0.516 / 0.631 at $140 /
  $194 / $227 ≫ `sps_tie` 0.258 / 0.342 / 0.282 at $52 / $70 / $59 (2023 / 2024 / 2025). The SPS tie
  never reaches the N↔S share → **SPP-57 outranks SPP-54**; SPP-54 stays queued behind it.
- **CARD P13 RULED** (§2): SPP-53 pulled from W5 into W3 as SPP-40's fourth precondition — a Fable
  derive lane reconciling the 2026→ corridor-flowgate effective limits into one link TTC under rule
  14's misalignment clause, construction declared in a PRECOMMIT before any limit is read.
- **ISSUED: SPP-30, SPP-31, SPP-32, SPP-33, SPP-34, SPP-53** (six parallel lanes; the W3 charters carry
  "RULINGS APPLIED (r#5)" blocks assigning SPP-20's and SPP-14's routed items: R-2 → SPP-32, R-3/R-4/R-5/
  R-8 → SPP-34, R-7 → SPP-33, the `_validation-source/README.md` row → SPP-31, R-6 → SPP-53).
- Gates at the pin: audit_keepers 0 · parity 0 (15 runs / 48 dirs — the owner's MISO lane pruned) ·
  bench 0 (25 parts) · goldens 0 · refactor-guards 0 (the SPP allowlist entry is gone) · matrix validate
  0 · **`check_gate_a_provenance` EXIT 1, now MISO** (`gate.a_keeper_marker` cites superseded
  `miso-230-ctdrag-seam`) — capx Q34 duty, §3 R-e updated. `keepers/index.json` still six — correct
  until SPP-40 registers.
- Standing note from the SPP-14 collision: **one charter = one session.** A charter pasted into two
  sessions produces two FINDINGs at one path and a salvage merge; the desk asks the owner before
  re-issuing anything that might already be running (§0 rule 3 already says so — restated because it
  cost a salvage).

### 0e. r#4 — sitting #4: SPP-13 and SPP-21 landed, SPP-20 running, P12 ruled, SPP-14 chartered (2026-09-06, main HEAD `5a20cec1`, 23:01 UTC)

- Pin `5a20cec1` (61 commits since r#3; the r#3 desk commit merged as PR #5291). Branch fast-forwarded.
- **GRADED BY CONTENT.** SPP-13 **LANDED** (PR #5314, `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8`,
  `FINDING-spp-13-2026-09-06.md`): the public-data route is **anonymous FTP** (`pubftp.spp.org`, user
  `anonymous`, password = email — no token, no login) and is blocked ONLY by the session egress (port
  21 not relayed; controls `ftp.gnu.org` / `ftp.debian.org` fail identically). Every product's FTP
  folder + file grammar recorded; real product schemas verified from the v35 sample zip (BC 14 columns
  incl. `Real Time Effective Limit`; hourly load by control zone = the EIA-930 sub-BA tokens); gen-mix
  2024-02-15 → 2025-12-16 and monthly peak load LANDED. Row 11 (N↔S rating): **swept, NOT PUBLIC** —
  it lives in the ITP Constraint Assessment NDA/CEII workbook (`SPPSPSTIES`, `SPSNMTIES` tabs), so
  SPP-20's Tier-3 estimate is the ruled path and the RTBM `Real Time Effective Limit` (row 8) is the
  measured substitute for SPP-53. Per-hub spread and four-group tables: NOT OBTAINABLE; P7 stands.
  SPP-21 **LANDED** (PR #5304, `claude/spp-21-matrix-shard-ti2gy3`, `FINDING-spp-21-2026-09-06.md`):
  seventh shard, 305 cells (162 `U` / 47 fc-only `U` / 96 `.`), guard exit 0, 33/33 matrix tests,
  7 columns render; no verdict minted anywhere; the lane also touched the two matrix test files
  (out of its charter region, recorded by the lane as owner-authorized) — noted, not adjudicated.
  SPP-20: no branch/commit → asked; owner: "Running on another branch" → RUNNING; its six target
  files have had ZERO writes since the r#3 pin (a quiet window).
- **CARD P12 RULED** (§2): "Try to find the data somewhere else" → **SPP-14 chartered** (Opus;
  gridstatus.io hosted API, the `gridstatus` package's endpoints, EnergyOnline, spp.org CDN hosts,
  Kaggle/Zenodo mirrors, MMU monthly tables; a rule-14 cross-check gate against the committed
  system-hub parquet before any landed series is used). W3/W4 never wait on it.
- Gates at the pin: ALL 0 — audit_keepers, parity (17 runs / 50 dirs), gate-(a) (re-keyed since r#3),
  bench, goldens, refactor-guards, matrix validate.
- ISSUED: SPP-14. Nothing else newly issuable — W3 waits on SPP-20.

**r#4 am.1** (owner: *"Is that really all that can run"*). Checked rather than asserted: every W3
derive — `derive_campd_unit_outages`, `derive_thermal_tranches`, `derive_actual_lmp`,
`build_calibration_reference`, `curate_zonal_shares`, `build_miso_wind_shape` — calls
`get_iso_config("SPP")`, so W3 is gated by registration itself (SPP-20), not by this desk; SPP-34's
`iso-topologies.json` likewise. Two things need NO registration and were not yet issued:
**SPP-15** (back-year intake 2019–2022 of the SPP-11 products — rule 22 data prep, no marker; the
owner's dispatch is the `--holdout-intake SPP` authorization) and an **SPP-14 addendum** (the three
measured files in SPP's v35 zip: `SL_to_Pnode_to_Zone_with_Area.csv`, `Hub_Definitions.csv`,
`TieFlows_Sep2025.csv`, HTTPS-reachable). Considered and NOT chartered: a NASA-POWER pre-pull for
the wind shape — the builder keeps no raw cache, so it would mean editing the MISO builder for a
network pull that is minutes long; and SPP-34's prose half — it would advertise seven ISOs before
the registration exists. Both issued; recorded against interest that r#4 called W3's gate "SPP-20"
without having measured which scripts impose it (§6 E-4).

### 0d. r#3 — sitting #3: SPP-12 landed, G12 met, P10/P11 ruled, SPP-13 chartered, SPP-20 issued (2026-09-06, main HEAD `992760ec`, 22:20 UTC)

- Pin `992760ec` (54 commits since r#2; the r#2 desk commit merged as PR #5273). Branch fast-forwarded.
- **GRADED BY CONTENT.** SPP-12 **LANDED** (PR #5285, `claude/spp-12-fetch-portal-x9cn-6atxy2`,
  `FINDING-spp-12-2026-09-06.md`). Served: planning PDFs (PRM, VRLs, offer cap, ITP report), the ASOM
  hub-spread series (2024 confirmed the widest year on BOTH published measures → P7 stands), wind
  curtailment as MW, the LTLF (`2025 ITP`, vintage 2025, four peak rows) — **G12 MET**, and the NRC
  addendum (Wolf Creek 2045; **Cooper 2034-01-18, SLR under review — inside the horizon**). Blocked:
  portal rows 5–9 — **not an API move but an `X-SPP-UI-Token` requirement** (discriminating probe: a
  real fsName returns `200 []`, an invented one 404); row 11 (N↔S TTC) **not found** in the ITP
  report. **The SPP-54/57 ranking has no measured input** — the binding-constraint archive is behind
  the token. SPP-12 fixed the four-group spec in `spp-binding-constraints/README.md` before any data
  (rule 1). SPP-21: no branch/commit → asked; owner: "Running on another branch" → RUNNING.
- **TWO CORRECTIONS TO THE PLAN from SPP-12** (recorded §6 E-3): PRM is 16 % East summer (v5.0A),
  the plan's 15 % was PY2023–25; SPP's posted energy offer cap is $1,000 (Order 831 hard ceiling
  $2,000). Both now carried in the SPP-20 charter.
- **CARDS P10, P11 RULED** (§2): voll $2,000 (cost-verified ceiling, both numbers cited); SPP-13
  chartered (FTP public-data route + ITP Manual sweep for the N↔S capability), W2 proceeds in parallel,
  SPP-20 registers the N↔S TTC Tier-3 with the misalignment documented if SPP-13 has not landed.
- **ISSUED: SPP-20** (the pin flip — P1–P11 ruled, G12 met; charter carries r#2 + r#3 "RULINGS
  APPLIED" blocks and the live-writer collision list) and **SPP-13** (new, plan §8).
- Gates at the pin: audit_keepers 0 · parity 0 (16 runs / 49 dirs) · bench 0 · goldens 0 ·
  refactor-guards 0 · matrix validate 0 · **`check_gate_a_provenance` EXIT 1 again, now CAISO**
  (`gate.a_keeper_marker` cites superseded `2026-09-06-caiso-257-b1-ctonly`) — capx Q34 duty,
  ROUTED (§3 R-e updated).
- Matrix files: base last written 21:34 UTC, shards 22:14 UTC (SCN-WS5A-RESOLVE) — continuous; SPP-21
  (running) rebases before its single commit per charter.

### 0c. r#2 — sitting #2: W1 graded, cards P1–P9 ruled, SPP-21 issued (2026-09-06, main HEAD `a6e4b6db`, 21:50 UTC)

- Owner said "Refresh". Pin: `origin/main` `a6e4b6db` (111 commits since r#1's pin, incl. the
  charter's own merge; the D79 solve-surface fingerprint; four keeper promotions — NEISO neiso-105,
  MISO, CAISO, NYISO; the SCN desk's r#16). Branch fast-forwarded to it.
- **GRADED BY CONTENT.** SPP-10 **LANDED** (PR #5254, `claude/spp-10-miso-audit-wowrmp`): the
  814-line audit + doc 00/01 corrections; census 103.3 GW / 828 plants reconciles to SPP's MMU at
  +0.5 % / −2.8 %; registry-values table §5 (22 rows) is what SPP-20 executes. SPP-11 **LANDED**
  (PRs #5239 / #5243 / #5247, `claude/spp-11-fetch-epa-eia-xs70mz`): all four items GOT, blocked
  table EMPTY, 16 CEMS parquets schema-verified, 17 sub-BAs = 0.9995–0.9999 of BA demand, 11 DIBAs.
  SPP-12: no commit, no branch → **asked, not graded LOST**; owner: "It is running on another
  branch" → RUNNING, branch to be recorded when it lands.
- **CARDS P1–P9 SERVED AND RULED** (§2, verbatim). P9 is NEW — raised by the audit §3.4 (three
  defective EIA-930 SWPP hours). The plan §3 ruling column is filled; charters SPP-20 / SPP-31 /
  SPP-40 carry "RULINGS APPLIED" blocks; W5 gains SPP-57 (Oklahoma pocket) ranked against SPP-54.
- **ISSUED: SPP-21** (matrix shard) — the r#1 hold is lifted: the base file's last write was
  21:34 UTC (miso PJM seam ladder), shards 21:37 (nyiso-207); writers are continuous, so the
  charter's "rebase immediately before your single commit" is the protocol, not a hold.
  **ISSUED: SPP-12 ADDENDUM** (paste into the running session): NRC licence intake (routed back by
  SPP-11), the Oklahoma-internal flowgate group, explicit P7 confirmation.
- **STILL BLOCKED: SPP-20** on G12 alone (LTLF edition/vintage — SPP-12's row 13). P1–P9 no longer
  block it. **New atomicity item** recorded in plan §2.3: `config/solve_surface.py::SURFACE_ISOS`
  (D79) must gain SPP in the same commit as `_ISO_BUILDERS`, with `--diff` showing zero moved rows
  for the six ISOs.
- Gates at the pin: `audit_keepers --check` 0 · parity 0 (15 runs / 48 dirs) · bench-freshness 0 ·
  golden-manifest 0 · refactor-guards 0 · matrix (validate mode) 0 with the two pre-existing anchor
  warnings · **`check_gate_a_provenance` EXIT 1** — NEISO's `gate.a_keeper_marker` cites the
  superseded keeper `neiso-99-joint-p1`; the current keeper is `2026-09-06-neiso-105-fossil-offer`.
  That is the capx director's standing Q34 re-key duty, not this desk's → ROUTED (§3 R-e).
- Errors against interest recorded in §6 (two).

### 0b. r#1 — first sitting, W1 issued (2026-09-06, main HEAD `b22b91c3`; charter commit `45055ba0` on `claude/spp-iso-model-plan-pf6ygd`)

- Owner instruction, verbatim: *"Commit the plan and then you turn into the desk and issue wave 1."*
  The charter commit was pushed and blob-verified (plan 808 lines, handoff 177 lines — local and
  origin sha256 MATCH; `git diff HEAD origin/<branch>` empty).
- Gates run at the pin, all exit 0: `audit_keepers --check`, `check_registry_payload_parity`
  (15 runs / 48 bundle dirs), `check_gate_a_provenance` (6 rows), `check_bench_freshness` (24 parts,
  0 stale), `check_golden_manifest`, `ci_refactor_guards`, `check_mechanism_matrix --base origin/main`
  (two PRE-EXISTING anchor warnings on `entry_lookahead_reprice` / `startup_co2_reporting`, not this
  desk's — routed, not repaired).
- **ISSUED: SPP-10, SPP-11, SPP-12** (plan §8 W1, verbatim; stems in §5). Three parallel Opus lanes,
  DATA PROFILE shared, disjoint files. Dispatch is unconfirmed until a branch exists.
- **HELD: SPP-21** (the early-issue option). The matrix base file
  `docs/codebase-site/data/mechanism-matrix.js` was last written by capx D78-R2 at 18:36 UTC, 30 min
  before this pin, and the shards by nyiso-204b at 18:26 — active writers. SPP-21 is issued at
  sitting #2 beside SPP-20 after a fresh collision check (§4 hold recorded).
- Cards: none served (P1–P8 are due at sitting #2 with W1's evidence — ruling O-1).
- Nothing else moved. No src/, scripts/, configs/, tests/ or frontend/ file touched by this desk.

### 0a. r#0 — charter (2026-09-06, main HEAD `b22b91c3`)

- Program chartered by the owner in session `claude/spp-iso-model-plan-pf6ygd`. Three owner answers
  taken at charter and recorded as O-1…O-3 (§2).
- Verified state recorded in the plan §2: SPP is NOT registered (six-ISO pin in five places); SWPP
  EIA-930 hourly + hub LMP actuals 2023–2025 already on disk; CEMS missing for OK NE NM WY; portal.spp.org
  file-browser API moved (listings `[]`, downloads 404 on this date); `spp` token collides with ERCOT's
  `DAMLZHBSPP_*` zips; `docs/multi-iso/00` §0/§3 falsely claim SPP registered.
- Wave graph W1–W6 and charters W1–W4 committed to the plan §8; W5 reserved; W6 routed (P8).
- Gates at charter: not run by this session (docs-only charter; nothing under `src/` touched) —
  recorded UNREAD. The r#1 sitting runs them.
- Nothing dispatched. Dispatch is unconfirmed until a branch exists.

---

## 1. Lane scoreboard

Status vocabulary: CHARTERED · ISSUED · RUNNING · LANDED · KILLED · HELD · ROUTED.

| Lane | Wave | Model | Profile | Status | Branch realised | PR | FINDING |
|---|---|---|---|---|---|---|---|
| SPP-10 audit + doc 00 fix | W1 | Opus | shared | **LANDED 2026-09-06** | `claude/spp-10-miso-audit-wowrmp` (session-assigned; stem was `claude/spp-10-audit-k7wq`) | — | `FINDING-spp-10-2026-09-06.md` → `docs/multi-iso/spp-data-audit.md` |
| SPP-11 EPA CAMPD + EIA fetch | W1 | Opus | shared | **LANDED 2026-09-06** — all four §6 items 1–4 GOT, blocked table EMPTY | `claude/spp-11-fetch-epa-eia-xs70mz` (stem issued `…-m3rd`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-11-2026-09-06.md` |
| SPP-12 portal.spp.org + spp.org fetch | W1 | Opus | shared | **LANDED 2026-09-06** — rows 10–14 + NRC served; rows 5–9 token-blocked; row 11 not found; addendum (A)(B-spec)(C) honoured | `claude/spp-12-fetch-portal-x9cn-6atxy2` | #5285 | `docs/handoffs/FINDING-spp-12-2026-09-06.md` |
| SPP-13 portal FTP route + N↔S TTC (P11) | W2 | Opus | shared | **LANDED 2026-09-06** — FTP route documented (anonymous; egress-blocked on port 21); row 11 NOT PUBLIC (NDA/CEII); gen-mix + monthly peak landed | `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8` | #5314 | `docs/handoffs/FINDING-spp-13-2026-09-06.md` |
| SPP-14 alt HTTPS sources for rows 5–9 (P12) | W2 | Opus | shared | **LANDED 2026-09-06** — rows 5–9 ALL served from SPP's own portal (open anonymously that day); per-hub parquet promoted (gate PASS); four-group table served; addendum (A)(B)(C) landed | `claude/spp-14-alt-sources-w6dp` + `-i49r3m` (two parallel sessions; salvaged `df5e8c3d`, `3cfb73bc`) | #5335, #5341 | `FINDING-spp-14-2026-09-06.md` + `-session-b.md` |
| SPP-15 back-year intake 2019–2022 (rule-22 data prep) | W2∥ | Opus | shared | **LANDED 2026-09-06** — all four items GOT, blocked table EMPTY; producers unmodified; interchange widened with the 2023-2025 slice proven byte-identical (268,177 rows, sha256 `243889469b96…`, before and after); nothing solved/scored/registered and no marker claimed. Four source defects reported and routed, not filled — incl. **`N3045OK3` publishes nothing 2015-2021** (OK gas exists for only 3 of the 7 years 2019-2025) and two impossible `AECI` prints that sign-flip SWPP's 2020 system net | `claude/spp-15-backyears-intake-0cah85` (stem issued `…-q3nf`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-15-2026-09-06.md` |
| SPP-20 register (pin flip) | W2 | Fable | shared→spp | **LANDED 2026-09-06** — SPP registered; six keepers unmoved; N↔S link a 48,700 MW placeholder (→ P13 / SPP-53); 8 routed items assigned r#5 | `claude/spp-20-topology-market-design-1iew99` | #5329 | `docs/handoffs/FINDING-spp-20-2026-09-06.md` |
| SPP-21 matrix shard + §5.7 | W2 | Opus | code | **LANDED 2026-09-06** — seventh shard live (305 cells: 162 `U` / 47 fc-only `U` / 96 `.`), `check_mechanism_matrix.py` exit 0 on 7 shards, 33/33 matrix tests pass, page renders 7 columns. **TWO out-of-region edits, both owner-authorized in session:** (1) 4 six-ISO assertions in `tests/unit/config/test_mechanism_matrix_{shard_migration,keeper_stamp}.py` (the charter budgeted one); (2) a one-line repair to `mechanism-matrix-assemble.js` for a PRE-EXISTING anchor mismatch that had left the rendered page blank since the 2026-08-11 sharding | `claude/spp-21-matrix-shard-ti2gy3` (stem issued `…-r4tq`; branch set by the session's own directive) | — | `docs/handoffs/FINDING-spp-21-2026-09-06.md` |
| SPP-30 outages + tranches | W3 | Opus | spp | **LANDED 2026-09-07** — G4 PASS (OK 1060 / NE 358 windows); 9 itemised full-year fallbacks; `derive_cc_committed_pct` dropped (E-5) | `claude/spp-30-outages-tranches-l2mdug` (stem `claude/spp-30-outages-tranches-b8kt`) | #5378 | `docs/handoffs/FINDING-spp-30-2026-09-07.md` |
| SPP-31 benchmarks | W3 | Opus | spp | **LANDED 2026-09-07** — SPP blocks in every shared JSON, others byte-identical; P9 closed in the builder; **§5a C4-path gap → SPP-41** | `claude/spp-31-benchmarks-calibration-klpemi` (stem `claude/spp-31-benchmarks-n2vw`) | #5389 | `docs/handoffs/FINDING-spp-31-2026-09-07.md` |
| SPP-32 zonal + wind shape + gas hub | W3 | Opus | spp | **LANDED 2026-09-07** — all gates PASS; six keepers unmoved; basis 2022–24 in `meanzero.py`; R-3/4/5 → SPP-59 | `claude/spp-32-zonal-wind-gas-tmuwui` (stem `claude/spp-32-zonal-wind-gas-r7ql`) | #5396, #5399 | `docs/handoffs/FINDING-spp-32-2026-09-07.md` |
| SPP-33 seam derive | W3 | Opus | spp | **LANDED 2026-09-07** — `hr_by_year` for SPP-51; R1/R2 → SPP-51 (Fable), R3 → desk | `claude/spp-33-seam-derive-ezmktp` (stem `claude/spp-33-seam-derive-c4hm`) | #5377 | `docs/handoffs/FINDING-spp-33-2026-09-07.md` |
| SPP-34 site + docs | W3 | Opus | code | **LANDED 2026-09-07** — S-1/S-2 → SPP-35; S-3 evidence job open; S-4 → audit | `claude/spp-34-site-docs-hjykvj` (stem `claude/spp-34-site-docs-t9xe`) | #5388 | `docs/handoffs/FINDING-spp-34-2026-09-07.md` |
| SPP-40 first solve → first keeper | W4 | Fable | spp | **LANDED 2026-09-07 — FIRST SPP KEEPER `2026-09-07-spp-1-baseline`, NOT-YET (P14 owner direction over the pre-registered 2024 screen kill); the 29(b) control for every later SPP lane; R-1…R-8 assigned r#7** | `claude/spp-40-first-solve-pvanrx` | #5425, #5434, #5446, #5447 | `docs/handoffs/FINDING-spp-40-2026-09-07.md` (+ PRECOMMIT) |
| SPP-41 EIA-930 spike screen → loader seam (SPP-31 §5a + SPP-40 §4 wind input) | W4b | Fable | code | **LANDED 2026-09-07** — one seam; two bench + one input series move, seven keys unmoved; landed AFTER keeper-2 → SPP-43 | `claude/spp-41-fuel-spike-seam-oqq8w4` (stem `…-k2mr`) | #5497 | `docs/handoffs/FINDING-spp-41-2026-09-07.md` |
| SPP-35 seven-ISO prose + badge contrast (S-1/S-2, O-4/O-6) | W4∥ | Opus | code | **LANDED 2026-09-07** — all four closed; six leftovers R-1…R-6 → SPP-37 (R-3 routed) | `claude/spp-35-seven-iso-prose-ypsq70` (stem `…-v8jd`) | #5440 | `docs/handoffs/FINDING-spp-35-2026-09-07.md` |
| SPP-36 coal supply class (SPP-40 R-7) | W4b | Opus | spp | **LANDED 2026-09-07** — gate record; artifact byte-identical to SPP-42's (converged); R-9 tranche guard → model desk, R-10 plant 6193 → SPP-43 | `claude/spp-36-coal-supply-67urkl` (stem `…-t3kp`) | #5480 | `docs/handoffs/FINDING-spp-36-2026-09-07.md` |
| SPP-37 SPP-35's six leftovers | W4b | Opus | code | **LANDED 2026-09-07** — all six closed; N-1/N-2 → SPP-43; R-3 routed | `claude/spp-37-leftovers-q7hn-w9r00a` | #5474 | `docs/handoffs/FINDING-spp-37-2026-09-07.md` |
| SPP-42 hydro-2025 repair + re-baseline (+ the coal crosswalk, R-7) | W4b | Fable (ran as; chartered Opus) | spp | **LANDED 2026-09-07 — KEEPER-2 `2026-09-07-spp-2-crosswalk-hydro`, NOT-YET**; C3a/C3b-2025 PASS; unserved 2,007 → 89 MWh; C5a in band; solved BEFORE the SPP-41 seam → SPP-43 | `claude/spp-42-coal-hydro-5y1z3h` (stem `…-w8nd`) | #5471 | `docs/handoffs/FINDING-spp-42-2026-09-07.md` |
| SPP-57 Oklahoma pocket (P1 first lever) | W5 | Fable | spp | **LANDED 2026-09-07 — 2025 SCREEN KILLED** (union-rated links 6,500 / 6,700 inert); topology NOT landed; design + instruments landed (`f5926636`, `spp57/`); R-12 → SPP-57b | `claude/spp-57-oklahoma-pocket-yedapf` (stem `…-m4rt`) | #5479, #5483, #5493, #5496 | `docs/handoffs/FINDING-spp-57-2026-09-07.md` (+ PRECOMMIT) |
| SPP-43 re-baseline on the screened input → keeper-3 | W4c | Opus | spp | **LANDED 2026-09-07 — KEEPER-3 `2026-09-07-spp-3-screened-input`** (registered + STOPPED on leg (i) bit-identity; owner ruled in-session → promoted; keeper-1/-2 pruned; C1/C4-2023 wind scored) | `claude/spp-43-screened-rebaseline-2ro0x8` (stem `…-p2vq`) | #5512, #5521, #5526 | `docs/handoffs/FINDING-spp-43-2026-09-07.md` (+ PRECOMMIT) |
| SPP-38 the 15 SPP-era red tests at HEAD | W4c | Opus | code | **LANDED 2026-09-07** — 4 of 15 were SPP's (2 configs + assertions); 11 were three unrelated defects; 2 red remain (miso-233 parity debt, MISO's) + the CAISO one | `claude/spp-38-test-repairs-lhpzsk` (stem `…-n6wr`) | #5522 | `docs/handoffs/FINDING-spp-38-2026-09-07.md` |
| SPP-57b Oklahoma pocket, constituent sets re-declared (R-12) | W5 | Fable | spp | **LANDED 2026-09-07 — 2025 SCREEN KILLED** (N↔OK 3,400 live 23.5 % / 93 % N→OK; OK↔S 10,700 never — directionally misaligned, R-17 → SPP-54; unserved 89 → 444 MWh, R-18); topology not landed | `claude/spp-57b-oklahoma-pocket-973wcd` (stem `…-h3km`) | #5513, #5527 | `docs/handoffs/FINDING-spp-57b-2026-09-07.md` (+ PRECOMMIT, `spp57b/`) |
| SPP-44 gas split as a P1-native commitment bridge (SPP-42 §7 / R-q) | W5 | Fable | spp | **LANDED 2026-09-07 — 2023 SCREEN KILLED** (CC window agreement 0.694 < 0.76; D-4 FAIL at five laid-up plants; the bridge reaches 0.41 of a 4.2 TWh gap — never-started units); field landed default-off; cells U → R; R-17 → SPP-46 queued | `claude/spp-44-gas-commitment-bridge-ljv87g` (stem `…-r5tc`) | #5519, #5535 | `docs/handoffs/FINDING-spp-44-2026-09-07.md` (+ PRECOMMIT, `spp44/`) |
| SPP-55 VRL-based scarcity (in-LP reserve demand curve) | W5 | Fable | spp | **LANDED 2026-09-07 — KILLED AT ZERO LP** (the SPP Contingency Reserve family lands default-off under the shared `energy_reserve_coopt` gate; the row can bind in 0 / 1 / 0 hours of 2023 / 2024 / 2025 and in 0 of the 4 / 3 / 7 measured hour-long shortage hours, so it is INERT on keeper-3's dispatch; the C3c tail is a 5-minute RT object, 1 / 0 / 0 coincident) | `claude/spp-55-vrl-scarcity-jgqidm` | #5565 | `FINDING-spp-55-2026-09-07.md` |
| SPP PRICE FAMILY (owner-launched, off-desk) | W5∥ | — | spp | **LANDED 2026-09-07 — arm KILLED on its structural leg** (uniform quadruple = level lever, not shape); `R` for SPP; C3c → SPP-55; C1-2024 → SPP-44 | `claude/spp-price-family-calibration-de9ddj` | #5533, #5534 | `docs/handoffs/FINDING-spp-price-family-2026-09-07.md` (+ PRECOMMIT) |
| capx Q59 board row (capx director's lane) | W6 | — | code | **LANDED 2026-09-07** — §2.1b SPP row from backcast artifacts; T1-H half → this desk (SPP-60); row cites keeper-2 → gate-(a) RED → SPP-45 | `claude/spp-forecast-board-row-6nwvmb` | #5528 | `program-status.json` SPP row |
| SPP-45 board-row re-key + records (gate-(a) F-5) | W6 | Opus | code | **LANDED 2026-09-07** — the re-key had already landed at `d26652f3` (a parallel Fable session firing the same Q34 duty); the lane did NOT redo it and delivered what was still owed: the promotion instrument (FINDING-spp-43 ADDENDUM A) in the row's `detail`, the MISO row's `corrected_by` sha, and the two record annotations. `check_gate_a_provenance` EXIT 0 | `claude/spp-45-board-rekey-records-cjc0ji` | #5554 | `FINDING-spp-45-2026-09-07.md` |
| SPP-58 ψ₂ — second independent shift-factor identification | W5 | Fable | spp | **LANDED 2026-09-07** — DC-network PTDF/OTDF (HIFLD + EIA-860); OUTSIDE the 1.92× band on every object (N→S 11,022 vs 3,400; S→N 13,175 vs 4,206; `sps_tie` 1,600 vs 10,705); `ttc_mw` UNTOUCHED, card R-21/R-22 to the desk; Potter width collapsed; double attribution real; SPP-54 input 1,600 MW | `claude/spp-58-second-identification-r2nmcx` (stem `claude/spp-58-psi-second-identification-j6tw`) | — | `docs/handoffs/FINDING-spp-58-2026-09-07.md` |
| SPP-54 SPS pocket — third zone (P1's second lever; SPP-57b R-17) | W5 | Fable | spp | **LANDED 2026-09-07 — DESIGN COMPLETE, NO SOLVE** (design commit `8d427adc`; pocket = NM + 42 SPS Texas counties, `SPS → SPP-SPS`, shares 0.5125 / 0.3616 / 0.1259; link South→SPS-named, rating rule fixed, ψ₂ pending SPP-58, R2 = 10,476; R-18 reconciliation identity 6e-16 but **C-3 STOP at h8509** — the wind-shape builder's six-site level rule, R-21 → desk card; topology NOT on main) | `claude/spp-54-sps-pocket-kx4jvd` (stem `claude/spp-54-sps-pocket-v2kq`) | — | `docs/handoffs/FINDING-spp-54-2026-09-07.md` (+ PRECOMMIT, `spp54/`) |
| SPP-51 priced seams MISO / AECI / ERCOT | W5 | Fable | spp | **LANDED 2026-09-07 — ARM KILLED AT RULE-29 PHASE 0, NO LP SPENT** (three adjudications made: per-ISO anchor map, the HH+basis flat-HR correction, ERCOT 835 MW on rule 14; the mechanism's own identity *flow follows spread* FAILS on both MISO seams in every year — sign agreement 0.436–0.501 vs a 0.55 bar, corr(spread, import) ≈ 0) | `claude/spp-51-priced-seams-hqgei3` | #5573 | `FINDING-spp-51-2026-09-07.md` |
| SPP-60 T1-H recipe + forecast intake (Q59) | W6 | Fable | spp | **LANDED 2026-09-07** — T1-H `spp-2021-2025-realized-t1h-spp60` registered (`spp-t1h`: HOLD, FC-3 FAIL — retire 0.744 vs 1.994 GW, additions 0 vs 13.9 GW; I7 + I12 declared); board legs (b)/(c) filled from the measured result; gap table + intake (capacity_actuals_spp, confirmed-retirements Tolk 1/2, the 2020-vintage generators parquet lacked every SWPP row) | `claude/spp-60-t1h-recipe-hindcast-x67gbz` (stem `claude/spp-60-t1h-recipe-w3pd`) | — | `docs/handoffs/FINDING-spp-60-2026-09-07.md` |
| SPP-53 N↔S TTC derive (P13 — W5 → W3) | W3 | Fable | spp | **LANDED 2026-09-07** — `ttc_mw` 48,700 → **3,400 MW** (FCITC, ex-ante construction); S→N set 4,206 → SPP-58 | `claude/spp-53-ttc-link-limit-67e3yf` (stem `claude/spp-53-ns-ttc-f6dz`) | #5374, #5383, #5393 | `docs/handoffs/FINDING-spp-53-2026-09-07.md` |
| SPP-49 P19 the two shared input seams | W5 | Fable | shared | **LANDED 2026-09-08 — BOTH SEAMS REPAIRED REPO-WIDE, ZERO LP**; seam 1 a registered gate (`f923_gas_price_plausibility_screen`, default ON), seam 2 a construction; ex-ante key census = ex-post exactly (18 / 0 off-target); SPP-46's attribution reproduced to the GWh pre and moved as predicted post, clean cohorts put; CHP excluded from seam 2 (rule 19); SPP / MISO / PJM owe re-solves, ERCOT none | `claude/spp-49-input-seam-repairs-arx1x2` | #5640 | `FINDING-spp-49-2026-09-08.md` |
| SPP-50 the batched re-baseline (wind LEVEL + both seams) | W5 | Fable | spp | **ISSUED r#14** · promotion = P15 | — (stem `claude/spp-50-rebaseline-<4>`) | — | — |
| SPP-46 the C1-2024 gas split (SPP-44 R-17) | W5 | Fable | spp | **LANDED 2026-09-07 — BOTH CANDIDATES KILLED AT PHASE 0, ZERO LP**; the object is a measured-input plausibility defect on three seams (EIA-923 own-month prices / eGRID plant heat rates / Harrington's fuel vintage) plus a self-commitment residual; R-1…R-8 routed | `claude/spp-46-gas-split-object-6i09yn` | #5602 | `FINDING-spp-46-2026-09-07.md` |
| SPP-47 P16 reference incomplete-fuel swap rule | W5 | Opus | shared | **LANDED 2026-09-07** — one executable line, zero new parameters; 5 specified cells to the digit + a SIXTH (NYISO 2022 oil, required by rule 22's data-vs-score clause); every determination and the whole scorer report byte-identical; no bench part STALE | `claude/spp-47-reference-vintage-rule-3k1xx2` | #5599 | `FINDING-spp-47-2026-09-07.md` |
| SPP-48 P17 wind-shape per-zone LEVEL rule | W5 | Fable (ran as; re-assigned Opus in-sitting after launch) | spp | **LANDED 2026-09-07** — R-LEVEL in `scripts/lib/wind_shape.py`; `_SAMPLES_PER_ZONE` deleted (net −1 free parameter); partition consistency proved; SPP-54's C-3 STOP dissolved (h8509 still −75 MW, reported); **both SPP's and MISO's keepers owed a re-baseline**; solve-path parquets deliberately not regenerated | `claude/spp-48-wind-level-rule-dn2l1r` | #5592 / #5601 | `FINDING-spp-48-2026-09-07.md` |
| SPP-46 (QUEUED r#10: SPP-44 R-17's two objects — a measured ST_GAS commitment-STATE input, or a per-class band under the carve-out), 52, 56 (LAST, P4), 59 (reserved r#6) levers | W5 | per plan §8 | spp | RESERVED · blocked on SPP-40 · **P1 ranking APPLIED r#5: SPP-57 (Oklahoma pocket) before SPP-54 (SPS pocket)** | — | — | — |
| SPP-60 forecast entry | W6 | Fable | spp | ROUTED to capx director (P8) | — | — | — |

---

## 2. Owner rulings (verbatim, numbered)

| # | Date | Question | Ruling (verbatim) | Where it binds |
|---|---|---|---|---|
| O-1 | 2026-09-06 | SPP topology for the first backcast: how many zones? | "Let the Phase-0 data audit decide" | plan §3 card P1 (served at sitting #2 with W1 evidence); no default topology in any charter |
| O-2 | 2026-09-06 | Where should the SPP desk sit relative to the existing directors? | "Standalone SPP desk (Recommended)" | this desk; rulings namespace P; collision register §4 |
| O-3 | 2026-09-06 | Data you cannot fetch from a session — how should the plan handle it? | "The plan should include sessions that fetch the data" | plan §6 (every row is a fetch lane first: SPP-11, SPP-12); manual upload only on a documented block |
| P1 | 2026-09-06 r#2 | topology for the W2 registration | "2 zones now; two ranked levers (Recommended)" | SPP-20 registers SPP-North/SPP-South; SPP-54 (SPS pocket) and SPP-57 (Oklahoma pocket) both pre-declared, ranked by SPP-12's per-flowgate binding share + shadow price vs the N↔S corridor |
| P2 | 2026-09-06 r#2 | SPP's MISO seam given MISO prices SPP from its side | "Served schedule first, priced seam default-off (Recommended)" | `_SCALAR_INTERCHANGE_ISOS` += SPP; `NeighborInterface("MISO")` + `("AECI")` default-off; SPP-51 validates |
| P3 | 2026-09-06 r#2 | ERCOT DC ties | ACCEPTED: "ERCOT DC ties as a default-off neighbour, 820 MW" | SPP-20 |
| P4 | 2026-09-06 r#2 | reserves | ACCEPTED: "defer reserve co-optimisation (M2 last)" | SPP-56 last; cells `U` |
| P5 | 2026-09-06 r#2 | scarcity seed | ACCEPTED: "no scarcity/ORDC seed at registration" | `voll=2000`; SPP-55 later; `test_iso_config` checkpoint untouched |
| P6 | 2026-09-06 r#2 | `TAIL_THRESHOLD["SPP"]` | "$200 (Recommended)" | three files, SPP-20; SPP-31 regenerates |
| P7 | 2026-09-06 r#2 | first-solve screen | "Control = none; screen 2024, structural STOP gate only (Recommended)" | SPP-40 PRECOMMIT; SPP-12's hourly per-hub number overrides 2024 if it disagrees |
| P8 | 2026-09-06 r#2 | W6 forecast entry | "Route to the capx director after a keeper exists (Recommended)" | SPP-60 never chartered by this desk |
| P10 | 2026-09-06 r#3 | `voll` after SPP-12's correction (posted cap $1,000; Order 831 hard ceiling $2,000) | "$2,000 — the cost-verified ceiling (Recommended)" | SPP-20 registers 2000.0 with both numbers cited; SPP-55 revisits against the VRLs |
| P11 | 2026-09-06 r#3 | unblocking portal rows 5–9 + the N↔S TTC | "Charter SPP-13 probe lane; W2 proceeds in parallel (Recommended)" | SPP-13 chartered (FTP route, ITP Manual sweep); SPP-20 registers the N↔S TTC Tier-3 with misalignment documented if SPP-13 has not landed; SPP-54/57 ranking waits for the flowgate archive |
| P12 | 2026-09-06 r#4 | rows 5–9 after SPP-13 (anonymous FTP, egress-blocked; row 11 NDA-only) | "Try to find the data somewhere else" | SPP-14 chartered (HTTPS third-party / mirror sweep with a rule-14 cross-check gate); W3/W4 proceed regardless; row 11 stays Tier-3 in SPP-20 |
| P1 (applied) | 2026-09-07 r#5 | the SPP-54 vs SPP-57 ranking under P1's own test | — (desk act; SPP-14 §5.2 measured `oklahoma_internal` ≥ `n_s_corridor` ≫ `sps_tie` in all three years on both legs) | SPP-57 first; SPP-54 does not clear "SPS-tie share ≥ N↔S share" and stays queued |
| P13 | 2026-09-07 r#5 | the N↔S TTC for the first keeper (SPP-20's 48,700 MW placeholder cannot bind) | "Pull SPP-53 into W3 as SPP-40's precondition (Recommended)" | SPP-53 issued (Fable derive, PRECOMMIT-first construction, rule 14 misalignment documented); SPP-40's preconditions now SPP-30/31/32/53 — **EXECUTED 2026-09-07 (SPP-53): 3,400 MW** |
| P14 | 2026-09-07 (given IN the SPP-40 session, recorded r#7) | the 2024 screen killed on a 22-h direction tie — is the baseline a keeper candidate? | "Is this a recommended keeper candidate? If so plz promote. If structural integrity improves but gates regress that may still be a keeper." | the full span was solved and `2026-09-07-spp-1-baseline` promoted as the FIRST SPP KEEPER at NOT-YET; STANDING for W5: a candidate that improves structure may be promoted even if gates regress — but promotion is served as a card (P15…), never a lane's act — **APPLIED r#8 by SPP-42** (promoted under a pre-declared rule with a stated gate miss, rule 14) **and by SPP-57** (the owner re-asked in-session; the lane answered NO — structure regressed, two inert pipes replaced one live one) — **APPLIED a third time r#9 by SPP-43** (owner ruled in-session over the lane's own bit-identity leg (i): structure improved, no gate regressed → keeper-3) |
| Q59 (capx card, 2026-09-07, capx ledger §0bb(a)) | ruled on the capx director's card | SPP forecast onboarding | "SPP onboarding split — the board-row half here, the T1-H recipe half routed to the SPP desk" | SUPERSEDES P8 for the T1-H half: SPP-60 is THIS desk's (chartered r#9); the board row itself stays the capx director's file, edited by this desk only under the Q34 re-key form (SPP-45) and for legs (b)/(c) from measured results (SPP-60) |
| P16 | 2026-09-07 r#9, **RULED r#12** | SPP-43 §6 / SPP-57 R-15: a one-rule, zero-parameter repair of the reference's hydro/oil vintage (use the EIA-930 swap other renewables already get when the EIA-923 vintage is preliminary) reaches FIVE cells in FOUR ISOs (SPP/MISO/NEISO 2025 hydro, NEISO 2025 oil, NYISO 2023 oil) — apply repo-wide, SPP-only, or not at all? | **REPO-WIDE, ONE RULE, ALL FIVE CELLS** (2026-09-07, r#12) | → **SPP-47** issued r#12 [OPUS]: the one-line swap-loop extension, every moved cell diffed over all seven ISOs, and the per-ISO determination delta measured from COMMITTED artifacts (`calibration_verdict.py --run-id`, never a solve). Non-SPP bench parts are reported and routed to their desks, never edited |
| P17 | 2026-09-07 r#12 | SPP-54 R-21: the wind-shape builder weights zones by `cap_z · SHAPE_z(t)`, so a six-site sample's mean LEVEL acts as a zonal capacity-factor level (splitting SPP's South moves the North +1.4/+1.5/+1.9 TWh at an identical system total, and h8509 flips infeasible). It blocks EVERY three-zone SPP solve and the same builder serves MISO — SPP-only, shared, or not now? | **SHARED BUILDER REPAIR; EACH ISO RE-DERIVES ITS OWN NUMBERS (rule 25)** (2026-09-07, r#12) | → **SPP-48** issued r#12 [**OPUS** — re-assigned from FABLE the same sitting, the desk closing the construction choice (whole-fleet capacity-weighted LEVEL, six-site diurnal shape retained, rule 23) rather than leaving it to the lane; `scripts/data/` is Opus territory by the r#20 economy rule]: the repair in both builders, the identity legs on both ISOs, the h8509 verdict, the two-zone keeper-3 delta with a re-baseline recommendation, and the MISO delta routed to MISO's desk. **The solve-path parquets are NOT regenerated** — SPP-46 is solving against keeper-3 in parallel and a changed wind input would invalidate its rule-29(b) control mid-flight; the desk sequences the landing |
| P19 | 2026-09-08 r#13 | SPP-46 R-1/R-2: the C1-2024 gas split is carried by two SHARED input seams — the EIA-923 own-month gas price consumed with no plausibility screen (SPP alone: 91 plant-months ≤ $0.50, 31 negative, 206 ≥ $10 of 5,707) and plant-level eGRID heat rates with no simple-cycle floor (Pioneer 57881 at 3.43). Both are zero-DOF rule-14 repairs on files outside any one ISO — repo-wide, arm-for-SPP-only, SPP-only, or not now? | **REPO-WIDE, BOTH SEAMS, ONE LANE** (2026-09-08, r#13) | → **SPP-49** issued r#13 [FABLE]: scope closed and construction named; the ONE question left open is construction-vs-registered-gate per seam, decided in the PRECOMMIT with its criterion stated. Every ISO owing a re-solve is named in the FINDING so the desk can route it |
| P19b (sequencing) | 2026-09-08 r#13 | Keeper-3 is owed a re-solve for SPP-48's wind repair, and P19's input repairs move the same keeper's inputs again — batch, re-baseline now, or not yet? | **BATCH: REPAIRS FIRST, THEN ONE RE-BASELINE** (2026-09-08, r#13) | → **SPP-50** QUEUED, issued when SPP-49 lands: one full-span invocation carries SPP-48's wind repair AND SPP-49's input repairs, so the keeper that emerges is identified against the final input surface. One LP span instead of two |
| P18 | 2026-09-07 r#12 | SPP-58 R-21/R-22: two independent identifications of SPP's links disagree far outside the declared band — N↔S ψ₁ 3,400/4,206 (REGISTERED) vs ψ₂ 11,022/13,175; SPS tie ψ₁-era 10,705 vs ψ₂ 1,600. ψ₂ is model-blind but cannot see Franklin 161/69, which carries 44 % of the corridor's binding hours (no public 69 kV data exists in this repo's reach) | **KEEP 3,400; RECORD ψ₂ AS UNRESOLVED** (2026-09-07, r#12) | `ttc_mw` is NOT re-keyed — ψ₂ is blind to the element that decides ψ₁'s number, and the corridor is measurably LIVE at 3,400 (SPP-57b: 23.5 % of hours, 93 % N→S). SPP-54b rates the South↔SPS link at **ψ₂'s 1,600 MW**, the only identification that saw it, and states the disagreement at the gate. SPP-58 R-23 (the missing 69 kV under-lay) stays open as R-aq: no lane can close it without new data |
| P9 | 2026-09-06 r#2 | EIA-930 SWPP defective hours (audit §3.4) | "Benchmark-side fix in SPP-31; demand-side routed (Recommended)" | SPP-31 screens `NG:` columns in the benchmark builder; low-side demand screen → audit track (§3 R-f); SPP-40 PRECOMMIT names the hours |

---

## 3. Routed / open, not this desk's to fix

| # | Item | Owner | Why it is here |
|---|---|---|---|
| R-a | W6 forecast-program entry for SPP (T1-F, `program-status.json`, `GOLDEN_ISOS`) | capx director (after card P8) | this desk never writes `frontend/data/forecast/` |
| R-b | `complete` marker for SPP holdout years | owner (rule 22) | manifest row 15 deferred; no out-of-training solve chartered |
| R-c | MISO's own SPP seam constants | MISO calibration lane | rule 25; SPP-20 adds SPP's blocks only |
| R-d | rule-28(c) CI enforcement gap | audit track | inherited consequence: read checker output, not exit code |
| R-e | `check_gate_a_provenance` EXIT 1 at r#2 (NEISO), r#3 (CAISO), r#5 (**MISO**: cites superseded `miso-230-ctdrag-seam`) `gate.a_keeper_marker` cites superseded `2026-09-06-caiso-257-b1-ctonly` | capx director (standing Q34 re-key duty) | seen at this desk's pin; not this desk's file |
| R-h | Row 11 — the N↔S transfer capability / SPS tie ratings exist only in SPP's ITP Constraint Assessment NDA/CEII workbook (`SPPSPSTIES`, `SPSNMTIES`), FINDING-spp-13 §4 | owner (an NDA read is an owner act, never a lane's) | SPP-20 registers Tier-3 with the misalignment documented; SPP-53 uses the RTBM `Real Time Effective Limit` as the measured substitute once row 8 lands |
| R-i | **D79 declared-hash ledger has no new-ISO-row limb** (FINDING-spp-20 §5 R-1): `check_cache_key_registration.py` check 6 treats a by-ISO entry as one string, so appending SPP's row is an "edit" breach and `--declare` refuses already-declared names → SPP's 17 new surface rows are UNDECLARED (they stay out of SPP's own cache key) | capx director (D79 owner) — wanted before SPP-40 registers, so SPP's first bundle's key sees its rows | the six ISOs are unaffected; SPP's key is incomplete until the limb exists |
| R-j | The 2026-01-28→ 14-column daily RTBM BC files are a forward-looking measured limit series (FINDING-spp-14 §5.4) | SPP-53 (now chartered) | its reduced corridor sidecar is SPP-53's deliverable |
| R-g | Cooper Nuclear (801 MW, NE) licence expires **2034-01-18** with its SLR under review; Wolf Creek 2045 with intent only — an SPP forecast assuming both firm through 2050 assumes an outcome the instrument record does not yet support (FINDING-spp-12 §7) | forecast lane / capx director, at W6 | recorded so SPP-60's charter carries it; no backcast consequence |
| R-f | low-side EIA-930 demand dropout screen (`_screen_demand_dropouts` catches only exactly-0.0; SWPP 2025-06-21 05:00 = 1,505 MW and 2024-07-19 00:00 escape) — repo-wide, cache-key risk | audit track (ruling P9) | SPP-40's PRECOMMIT names the hours as known artifacts; no SPP lane adds a screen parameter |

| R-k | `audit_keepers --check` S1: `status/ERCOT.js` and `status/MISO.js` stale against their keeper shards at pin `7347933c` | the ERCOT / MISO promoting lanes (rule 22 D-5(b) re-key duty) or capx | seen at this desk's pin; not this desk's files |
| R-l | CAISO `calibration_reference.json` renewables block predates the 2026-09-05 EIA-860 `vintage_2024` intake (FINDING-spp-31 §4a); three CAISO test files red on `main` (FINDING-spp-32 §8) | CAISO calibration lane | pre-existing, proven at HEAD without SPP code |
| R-m | 63 non-SPP registry rows regenerated by SPP-34's R-3, 35 still `needs-citation` (FINDING-spp-34 S-4) | audit track (rule 5 citations) | not an SPP object |
| R-n | `_HR_GAS_ELASTIC` global name key blocks SPP↔MISO forward elasticity (FINDING-spp-33 R3; PJM owns `"MISO"`) | SPP-DESK — a W5 card, forward-only, inert for the backcast keeper | a keying change in `neighbor_price.py` is mechanism-shaped; not SPP-51's one lever |
| R-o | SPP-30's `derive_cc_committed_pct.py` has no `argparse` and silently ignores `--iso` (would overwrite ERCOT's file) | ERCOT lane / audit — a guard (refuse `--iso ≠ ERCOT`) or deletion (rule 26, superseded by `derive_thermal_tranches`) | not run for SPP; recorded so nobody else does |
| R-p | SPP-35 R-3: `generate_parameter_registry.py` cannot express an `iso_configs` value (the O-6 code half) | registry owner / audit track | not an SPP object |
| R-q | SPP-40 R-6: gas split CT 1.78× / CC 0.85× / ST 0.78× with coal −4…−11 TWh — a commitment-physics question (rule 18) | SPP-DESK — W5 queue entry after SPP-57/51/58; never a band | mechanism-shaped; needs its own lever lane |
| R-r | FINDING-spp-53 §6 O-1/O-2 (asymmetric pair 3,400 / 4,206; identification width 2,645–11,121 MW) — SPP-40 §7.2 shows S→N live at the symmetric rating | SPP-58 (chartered r#6) | **served 2026-09-07**: ψ₂ reads 11,022 / 13,175 — outside the band; the width is real and the card (FINDING-spp-58 R-21) is the desk's |
| R-s | `audit_keepers --check` S1: `status/ERCOT.js`, `status/PJM.js` stale at pin `8a4bfd29` | ERCOT / PJM promoting lanes | not this desk's files |
| R-t | Three pre-existing STALE goldens (NEISO perfb-campd ×2 vs live `neiso-106`; ERCOT perfb-campd-ercot-after, provenance pruned) | NEISO / ERCOT lanes | reported by `check_golden_manifest` at the pin, exit 0 |
| R-u | SPP-42 R-9 / SPP-41 §8: stuck EIA-930 SWPP `Demand` runs (2025: 698 h / 19 runs, longest 155 h from 12-15; 2024: 396 h; 2023: 36 h; the surviving 2025 unserved hour sits inside the December window); SPP-41's co-flag proposal (repair the `NG` total only where an `NG:` cell was flagged) | audit track (ruling P9: demand-side routed) — the desk's adjudication on the co-flag: NOT chartered now, it reaches no criterion; revisit if the completeness ratio is ever gated | `src/` demand-path screen with cache-key risk, repo-wide |
| R-v | SPP-36 R-9: `assembly.py` six-slice econ ramp has no feasibility precondition — a sub-3.0 MW econ block is silently deleted by `MIN_TRANCHE_CAPACITY_MW` (2.40 MW on one SPP plant; ISO-agnostic) | model desk / audit | pre-existing, not SPP's |
| R-w | SPP-41 §7(f): 16 red tests at HEAD — one CAISO (SPP-31 §5e), fifteen SPP-era | SPP-38 (chartered r#8) for the fifteen; CAISO lane for the one | SPP-caused breakage on `main` |
| R-x | SPP-41 §7(b): the record carries NYISO 2024 `other` 3.3197 (screen-before-gap-fill), not SPP-31's projected 3.3486 — DESK RULING r#8: the seam's construction stands; SPP-31 §3.2's number is superseded, not restored | closed | unscored series |
| R-y | SPP-35 R-3 / SPP-37 N-3: the registry generator cannot express an `iso_configs` value; `docs/parameter-citations.md:1744`'s hand-added N↔S row dies on the next generator run | registry owner / audit track | still open |
| R-z | SPP-57 R-13: the residual-South price reads SPS DEARER than the Oklahoma hub on the annual mean in 2024–2025 (+4.74 / +12.07) — SPP-54's design starts from that table, not P1's prose | SPP-54 (queued) | recorded so the charter carries it |
| R-aa | SPP-57 R-14: the hub-pair ψ identification double-attributes intra-Oklahoma elements to whichever link the regression is run for — SPP-58's second identification is load-bearing for every FCITC rating that admits them | SPP-58 (queued; now ranked right after SPP-57b / SPP-51) | **served 2026-09-07**: the double attribution is REAL under ψ₂ (FINDING-spp-58 §5) — the elements sit on both transfer paths; SPP-57b's exclusion stands |
| R-ab | SPP-57 R-15: `calibration_reference.json` SPP 2025 hydro = EIA-923 preliminary 0.02 TWh, so leg (v) reads hydro out of band on every 2025 run carrying keeper-2's repair | SPP-43 (zero-LP report + proposed one-rule repair, not applied) | builder-side vintage question |
| R-ac | SPP-43 R-17: `P1 basis seed: ON` makes a year's P1 depend on earlier years in the same invocation — no single year is independently reproducible from its own bundle; keeper FINDINGs should record every pass's objective | model desk (determinism); desk standing note for every SPP charter (record P0 AND P1 objectives per year) | surfaced by SPP-43's leg (i) |
| R-ad | SPP-43 R-10: plant 6193 Harrington is carried as `gas_st` in every year against EIA-860 vintage_2023's `SUB` (a mid-conversion coal station; 3.178 TWh of 2023 coal in the bench population) | fleet lane | not an SPP-only object (the vintage rule) |
| R-ae | SPP-38 R-1: miso-233 added three `ScenarioConfig` fields with no `forecast_parity_registry.py` row — 2 red in `tests/scoring` at HEAD; the likely disposition is BACKCAST_ONLY (rule-13 adjudication) | MISO desk / miso-233's successor | not a test repair and not SPP's |
| R-af | SPP-38 R-2: the sixteen deleted `full_horizon_summary.json` campaign files (5 regression tests SKIP; whole-tree number 101.967 vs pinned 18.830) | SCN desk | — |
| R-ag | SPP-38 R-4: `collate_scenario_campaign.SYSTEM_LABEL` reads "six-ISO modeled system" and names SPP un-modeled — true as campaign scope (no SPP arm), false as prose | SCN desk / W6 when SPP joins the campaign | — |
| R-ah | SPP-57b R-18: the per-zone wind-shape rebuild lowers the OK+S region's own generation in h8507–h8508 (unserved 89 → 444 MWh at identical demand/pipe/system wind) — a per-zone reconciliation against the EIA-930 SWPP profile is owed before any three-zone solve | SPP-54 (design step C) | **MEASURED by SPP-54 (FINDING §4): the builder's six-site sample MEAN LEVEL is load-bearing in the redistribution (North +1.4–1.9 TWh/yr, 75–85 % from the residual South's own sample); C-3 STOP at h8509 → R-21 desk card (zone level from the whole fleet, zero DOF)** |
| R-ai | Price family §6: `offer_curve_by_group` is `R` for SPP as a UNIFORM quadruple; a per-class differentiated curve is open but "far more freedom, correspondingly easier to fit" — any opener must derive the class differentiation from SPP's own data and pre-register how; the gas-series question (`gas_monthly_actuals` / `gas_daily_shape` unarmed) stays OPEN, untested | SPP-DESK — not chartered; revisit after SPP-44/54/51 report | rule 1 / carve-out (c) |
| R-aj | SPP-44 R-17: the gas-split object is a never-started / merit question, not a bridge question — admissible next objects: (a) the `offer_curve_by_group` band channel under rule 1's carve-out, per-class, declared ex ante, never swept; (b) a measured commitment-STATE input on the ST_GAS fleet (online-hours state floor with MEASURED duty membership, the ercot141 / nyiso-146b construction on SPP's own conduct) | SPP-46 (queued; issued after SPP-55 lands) | a new PRECOMMIT either way |
| R-ak | SPP-44 R-18: five bridge-floored plants read laid-up / capacity-only on their own meter (CC 201, 3604, 8000, 55178; ST_GAS 3485; zero-load share 0.53–0.95) — the membership channel (`derive_campd_bridge_layup_exclusions.py --iso SPP`) is a PREREQUISITE for any future P0-anchored SPP floor | SPP-46 and any later SPP floor lane | — |
| R-al | SPP-44 R-19/R-20: keeper-2's recorded 2023 P0 objective (−97,436,762) vs the flag-free re-solve (−96,274,350) with dispatch agreeing to 25 GWh — which pass the recorded figure belongs to; and the SPP-41 seam's measured 2023 dispatch effect (−25 GWh wind, +21 coal, +7 CC, −7 CT; no criterion row moves) | closed by SPP-43's record (keeper-3 supersedes; R-ac's standing note: record every pass's objective) | — |
| R-am | **SPP-51 R-a: the two-bus priced-seam topology.** A registry-declared second external zone + per-seam host zone, generic and default-empty — the prerequisite for ANY LP test of a priced SPP seam. At HEAD `--priced-interchange` cannot build one | a `model/interchange` lane (mechanism-shaped, not SPP's) |
| R-an | **SPP-51 R-b: the seam form that could pass gate (i)** — a measured hourly-anchored OFFSET ladder from SPP's side (the miso-233 construction mirrored: SPP hub + per-band offsets against the MISO-West / MISO-South anchors, hourly). This, not a spread-clearing seam, is what the measured record admits | SPP-DESK (a later W5/W6 lane, forward-only) |
| R-ao | **SPP-51 R-d: `ERCOT_DC_TIE_ZONE_MAP["SWPP"]` reads 820 MW against the measured 835 clip.** SPP's own block carries 835 (rule 14, misalignment stated); the ERCOT-side row is ERCOT's to adjudicate (rule 25) | ERCOT lane, if it wants it |
| R-ap | **SPP-54 R-24: STOP-gate leg (iii) is written for an EXPORTING pocket.** The SPS pocket imports at its bound, so a screen stopping on (iii) alone would be the gate measuring the wrong sign of the same object. **DESK RULING (r#12), recorded before any re-issue:** leg (iii) is re-stated for SPP-54b as *the link changes what the pocket's own fleet does* (re-curtailment OR a displaced-thermal delta), sign-agnostic, with the dominance threshold declared ex ante (E-6); the leg is not deleted and not widened | SPP-DESK — **RULED**, applies to SPP-54b's charter |
| R-aq | **SPP-58 R-23: a 69 kV under-lay is the one dataset that would let ψ₂ see Franklin** — the constituent carrying 44 % of the corridor's binding hours. No public line dataset in this repo's reach has it (HIFLD 2023 carries nothing below 115 kV in the box), so the two identifications **cannot be compared on the element that decides ψ₁'s number**. Stated on card P18 | SPP-DESK (stated on the card; no lane can close it without new data) |
| R-ar | **SPP-58 R-24: a proper `data/raw/hifld-transmission-lines/` intake** (README / SOURCES / SHA256SUMS / per-page JSON, the `hifld-substations` form) is owed if any later lane reuses SPP-58's reduced network, which currently lives under `docs/handoffs/spp58/` | SPP-DESK (data-intake card, when a lane needs it) |
| R-as | **SPP-55 R-23/R-24: a LIVE reserve family would need two things this design does not carry** — an intermittent-class MSSC limb (the requirement reads 756–1,320 MW against ~1,480 posted in the MSSC unit's refuelling months, because SPP's MSSC then passes to a wind cluster or an SMCE), and `SPP_BA_CR_REQUIREMENT_RATIO` **by year** from the posted RSG record (0.973 → 0.954 → ~0.90–0.97) rather than one scalar. Immaterial while the family is inert | SPP-56 |
| R-at | **SPP-55 R-25: the RTBM-OR cleared-reserve archives** (`operating-reserves` 2023.zip / 2024.zip, ~47 MB each) were read to scratch and NOT landed; if SPP-56 wants them as a measured requirement input (the `miso_measured_reserve_requirements` analogue) that is a data-intake row on SPP-14's documented route | SPP-56 / data intake |
| R-au | **SPP-60 §4: the T1-H's own routed set** — the 2021 wind shape is absent (flat 0.36 fallback; inert for this T1-H, bites any solve-year-weather arm), `demand_growth_vintage` is impossible for SPP (no 2021 / 2023 vintage entry, so *realized* is the only T1-H variant), and two `regenerate_clean.py` curation failures in this container (`lmp` CAISO `KeyError: 'MGHG'`; `emissions-unit-annual` OOM) are **not on the SPP T1-H path** | capx / CAISO / data owners as named in FINDING-spp-60 §4 |
| R-av | **DISCHARGED r#14** (both rows re-keyed by their own desks; gate EXIT 0). ~~`check_gate_a_provenance` EXIT 1 at this desk's r#13 pin, on TWO rows and neither is SPP's**: ERCOT cites the superseded `2026-09-05-ercot248-two-config-keeper` (live `2026-09-08-ercot256-drag-layup-mask`); MISO cites `2026-09-07-miso-233-spp-hourly` (live `2026-09-07-miso-243-spp-pairing`) | ERCOT / MISO promoting lanes (Q34 standing re-key duty) or capx | seen at this desk's pin; not this desk's files (rule 25) |
| R-aw | **SPP-48 R-3: MISO's keeper needs a wind re-baseline** on the repaired per-zone LEVEL rule, measured on MISO's own six zones from MISO's own EIA-860 rows (no SPP number crosses). The repaired builder is already on `main`; MISO's solve-path parquets are not regenerated, so nothing has changed for MISO until its desk acts | MISO calibration desk | the delta is measured and in `FINDING-spp-48-2026-09-07.md`, so MISO's desk acts on a number, not a claim |
| R-ax | **SPP-46 R-4 / R-ad (now doubly evidenced): Harrington 6193's fuel vintage.** Carried as `gas_st` at $1.48 in 2023–24 while CAMPD burns coal on all three boilers (3.54 / 2.51 TWh gross), converting in 2025 — worth +5.8 TWh of "gas" steam in the 2024 model AND 3.44 / 2.23 TWh of coal generation grouped as ST_GAS in the bench | fleet lane (the fuel-switch-date seam is not SPP-only) | SPP's copy of the object is inside card P19's repair lane; the underlying fleet seam is not |
| R-ay | **SPP-46 R-6 / R-7 / R-8**: the 2023 clean-CT +5.0 TWh over-run on the HIGH-gas side of the same seam (answered by R-1's own census on 2023); every SPP fleet row carries an EMPTY `state`, which would void a state-keyed plausibility screen (so R-1 must key its reference on the F923 frame's `state`); and CO CAMPD extracts are absent, J Lamar Stall 56565 has no CAMPD series | the P19 repair lane (R-6, R-7) / any CAMPD-based SPP derive (R-8) | R-7 is a prerequisite, not a footnote — it is the difference between a screen that works and one that silently does nothing |
| R-az | **SPP-49 R-1: the CLI flag `--no-f923-gas-price-plausibility-screen`** is not yet threaded into `run_calibration.py` / `run_calibration_full.py` (nor onto `--replay-bundle`), the D76 pattern. Verified at this desk's pin: neither script exposes a generic `--set`, so **the pre-repair posture is currently unreachable from the CLI** | SPP-DESK (a small lane, after SPP-50 settles) | it is a governance gap, not a solve gap: a registered default-ON gate whose `False` branch no runner can select |
| R-ba | **SPP-49 R-2: the THIRD F923 consumer is still unscreened** — `plant_prices.iso_monthly_gas_prices` / `_iso_monthly_fuel_prices`, the ISO-month volume-weighted series `model/interchange/caiso.py` reads. The same implausible plant-months reach it by a different path | CAISO desk / the interchange lane | the repair is landed at the plant seam only; this is a second seam, not a second version of the same one |
| R-bb | **SPP-49 R-5: a hub-level reference for Permian-connected plants** (Elk 58835, Mustang 56326 / 55065, Jones 3482 in SPP-South; ERCOT West if it ever arms the seam) — the TX state blend is defined on a different boundary than Waha gas, which is rule 14's declared misalignment exception, so the screen's fallback is coarse exactly where SPP's worst rows are | SPP-DESK (a reconciled reference is better than either extreme) | it does not un-do the repair; it would sharpen the fallback |
| R-bc | **SPP-49 R-3 (cache-epoch ledger + scoped `SolveEpoch` for seam 2), R-7 (the F923 monthly-cost frame carries no PA / NJ / DE / CT / RI / ME / VT gas rows, so PJM and NEISO price gas from the pool), R-8 (the MISO high-tail cohort — 27 plants in 2024 whose screened months may be fixed-charge averages rather than real winter delivered costs) and R-9 (a capx surface pin advanced inside this lane's cause block)** | audit track / PJM / NEISO / MISO / capx desks as named in `FINDING-spp-49-2026-09-08.md` §6 | each is another desk's file; SPP-49 named them rather than reaching across |

---

## 4. Collision register (verify at every sitting against the capx and SCN ledgers' top entries)

| Surface | Live writers at charter | SPP lane | Protocol |
|---|---|---|---|
| `config/capacity_market.py` adequacy / entry / storage dicts | capx D75-R landed 17:11 UTC; D76 / D78 / D81 LIVE (capx r#52) | SPP-20 | append SPP as the LAST entry of each dict, rebase last; HOLD if a capx lane holds the same dict mid-PR |
| `config/constants.py` `DEMAND_GROWTH_RATES(+_VINTAGES)`, `DATACENTER_ADDITIONS_MW`, `ELECTRIFICATION_LAYERS`, `VOLUNTARY_BASELINE_ISO_WEIGHT` | SCN desk (load re-derivation, voluntary dict); capx D67 lane (PJM rate) | SPP-20 | append-last; SPP-20 declares the constant families it adds |
| `model/interchange/spec.py` | miso-231 seam ladder landed 21:34 UTC; miso-232 LIVE | SPP-20 (new `"SPP"` blocks only), SPP-51 | region-disjoint; append after the MISO blocks; rebase last |
| `data/renewables.py`, `data/fuel/hubs.py` | any live per-ISO calibration lane | SPP-32 | named regions; G-DRIFT classification of every hunk in the FINDING |
| `frontend/data/backcast/tail/actual_tail.json`, `amplitude/actual_amplitude.json`, `completeness/` | holdout-intake lanes | SPP-31 | regenerate as the LAST commit after rebase; non-SPP diff = ∅ |
| `docs/codebase-site/data/mechanism-matrix.js` + shards | every lane, several times a day | SPP-21 (7th shard), SPP-40 (stamp), every W3+ lane (cell lines) | one commit; last after rebase; 7 shards from SPP-21 on |
| `scripts/ci_refactor_guards.py` allowlist | audit Y-lanes | SPP-20 | delete-only edit; cite Y-21 |
| `frontend/data/backcast/keepers/index.json`, `status/*.js` | keeper promotions | SPP-40 | per-ISO shards are conflict-free; `index.json` is one line, rebase last |
| `frontend/data/forecast/program-status.json`, `ff-verdicts.json`, goldens, `GOLDEN_ISOS` | capx director's sole writer | none until W6 | ROUTE, never charter |
| `results/cache.py`, `ScenarioConfig` fields | capx D77/D79 (cache fingerprint) | none | never touched by any SPP lane through W4 (plan §7 G8) |
| Per-plant solve slots | capx / SCN campaigns, per-ISO calibration lanes | SPP-40, SPP-5x | advisory: confirm no other per-plant solve before the SPP leg (rule 12, ≤ 2 concurrent) |
| r#7 | MISO lane keeper `2026-09-07-miso-233-spp-hourly` (bundle `miso233_sppseam_K`) — MISO's priced SPP seam, rule 25 | VERIFIED no SPP object moved (`iso_configs.py`, `interchange/`, `spp_seam_*` diff empty 7347933c..8a4bfd29); SPP-51 will read MISO's seam constants but never edit them |
| r#8 | SPP-44 adds a `ScenarioConfig` field → a cell line in EVERY ISO shard (rule 28c, the one non-parallel edit) | SPP-44 rebases LAST and re-runs `check_mechanism_matrix`; the capx / SCN / per-ISO lanes writing shards this week are the collision surface — the lane touches one `·` line per foreign shard and nothing else |
| r#8 | SPP-43 (full span) ∥ SPP-57b (screen) ∥ SPP-44 (screen) — three per-plant SPP solves in flight | separate sessions/containers; rule 12's ~2-per-host cap holds per container; each charter asks the desk before solving |
| r#9 | `frontend/data/forecast/program-status.json` — the capx director's file; SPP's row written by Q59's lane, now stale (keeper-3) | SPP-45 edits the SPP row ONLY under the Q34 re-key form; SPP-60 fills legs (b)/(c) from measured results; nothing else in the namespace |
| r#9 | SPP-44 (field + 7-shard cells) ∥ SPP-55 (would add a second field) | SPP-55 HELD until SPP-44 merges — one 28c every-shard edit at a time |
| r#10 | SPP-44's 28c edit MERGED (#5535) → SPP-55 issued; SPP-46 (if it needs a field) waits for SPP-55's merge — one every-shard edit at a time | SPP-55 rebases LAST and re-runs `check_mechanism_matrix` |
| r#9 | SPP-54 solve ∥ SPP-51 solve ∥ SPP-44 screens ∥ SPP-60 hindcast — up to four SPP per-plant solves in flight across containers | each charter asks the desk before solving; rule 12 holds per host |

Holds recorded: **r#1 — SPP-21 held** (LIFTED r#2 — writers on the matrix files are continuous, so the charter's rebase-immediately-before-commit line is the protocol); `mechanism-matrix.js` last written by capx D78-R2 (`8e68a471`, 18:36 UTC) and the shards by nyiso-204b (`330e3cac`, 18:26 UTC) within the hour before the pin. Re-check at sitting #2.

---

## 5. Issuance record

| Sitting | Lane | Stem issued | Branch realised | Charter location | Note |
|---|---|---|---|---|---|
| r#1 | SPP-10 | `claude/spp-10-audit-k7wq` | — | plan §8 W1 · SPP-10 | issued verbatim |
| r#1 | SPP-11 | `claude/spp-11-fetch-epa-eia-m3rd` | — | plan §8 W1 · SPP-11 | issued verbatim |
| r#1 | SPP-12 | `claude/spp-12-fetch-portal-x9cn` | unknown — owner confirms RUNNING r#2 | plan §8 W1 · SPP-12 | issued verbatim |
| r#2 | SPP-12 addendum | (into the running session) | — | plan §8 W1 · SPP-12 ADDENDUM | NRC intake + Oklahoma flowgate group + P7 confirm |
| r#2 | SPP-21 | `claude/spp-21-matrix-shard-r4tq` | unknown — owner confirms RUNNING r#3 | plan §8 W2 · SPP-21 | issued verbatim |
| r#3 | SPP-13 | `claude/spp-13-portal-ftp-ttc-h2vk` | — | plan §8 W2 · SPP-13 | new charter under P11 |
| r#3 | SPP-20 | `claude/spp-20-register-p8nz` | unknown — owner confirms RUNNING r#4 | plan §8 W2 · SPP-20 (+ r#2/r#3 RULINGS APPLIED) | issued verbatim |
| r#3 | SPP-13 | `claude/spp-13-portal-ftp-ttc-h2vk` | `claude/spp-13-portal-ftp-ttc-h2vk-h9c6q8` | plan §8 W2 · SPP-13 | LANDED #5314 |
| r#4 | SPP-14 | `claude/spp-14-alt-sources-w6dp` | — | plan §8 W2 · SPP-14 | new charter under P12 |
| r#4 am.1 | SPP-14 addendum | (into the SPP-14 session) | — | plan §8 · SPP-14 ADDENDUM | three v35-zip measured files |
| r#4 am.1 | SPP-15 | `claude/spp-15-backyears-q3nf` | `claude/spp-15-backyears-intake-0cah85` | plan §8 · SPP-15 | LANDED #5333 |
| r#5 | SPP-30 | `claude/spp-30-outages-tranches-b8kt` | — | plan §8 W3 · SPP-30 (+ r#5 block) | issued |
| r#5 | SPP-31 | `claude/spp-31-benchmarks-n2vw` | — | plan §8 W3 · SPP-31 (+ r#2/r#5 blocks) | issued |
| r#5 | SPP-32 | `claude/spp-32-zonal-wind-gas-r7ql` | — | plan §8 W3 · SPP-32 (+ r#5 block) | issued |
| r#5 | SPP-33 | `claude/spp-33-seam-derive-c4hm` | — | plan §8 W3 · SPP-33 (+ r#5 block) | issued |
| r#5 | SPP-34 | `claude/spp-34-site-docs-t9xe` | — | plan §8 W3 · SPP-34 (+ r#5 block) | issued |
| r#5 | SPP-53 | `claude/spp-53-ns-ttc-f6dz` | — | plan §8 · SPP-53 (new, P13) | issued |
| r#6 | SPP-40 addendum | (into the running SPP-40 session, owner-launched) | — | plan §8 · SPP-40 ADDENDUM | six facts; C4-2023 unquotable until SPP-41 |
| r#6 | SPP-41 | `claude/spp-41-fuel-spike-seam-k2mr` | — | plan §8 · SPP-41 (new) | issued |
| r#6 | SPP-35 | `claude/spp-35-seven-iso-prose-v8jd` | — | plan §8 · SPP-35 (new) | issued |
| r#7 | SPP-41 v2 | `claude/spp-41-fuel-spike-seam-k2mr` | — | plan §8 W4b · SPP-41 v2 | v1 never launched; re-issued whole |
| r#7 | SPP-36 | `claude/spp-36-coal-supply-class-t3kp` | — | plan §8 W4b · SPP-36 | issued |
| r#7 | SPP-37 | `claude/spp-37-leftovers-q7hn` | — | plan §8 W4b · SPP-37 | issued |
| r#7 | SPP-42 | `claude/spp-42-hydro-rebaseline-w8nd` | — | plan §8 W4b · SPP-42 | issued; launch after SPP-36 + SPP-41 land |
| r#7 | SPP-57 | `claude/spp-57-oklahoma-pocket-m4rt` | — | plan §8 W5 · SPP-57 | issued; design now, solve after SPP-42 |
| r#8 | SPP-43 | `claude/spp-43-screened-rebaseline-p2vq` | — | plan §8 W4c · SPP-43 | issued |
| r#8 | SPP-38 | `claude/spp-38-seventh-iso-tests-n6wr` | — | plan §8 W4c · SPP-38 | issued |
| r#8 | SPP-57b | `claude/spp-57b-oklahoma-pocket-sets-h3km` | — | plan §8 W4c · SPP-57b | issued (SPP-57 R-12) |
| r#8 | SPP-44 | `claude/spp-44-gas-commitment-bridge-r5tc` | — | plan §8 W4c · SPP-44 | issued |
| r#9 | SPP-45 | `claude/spp-45-board-rekey-records-c8vm` | — | plan §8 W5-r#9 · SPP-45 | issued |
| r#9 | SPP-58 | `claude/spp-58-second-identification-r2nmcx` (stem `claude/spp-58-psi-second-identification-j6tw`) | — | plan §8 W5-r#9 · SPP-58 | **landed 2026-09-07** — card R-21/R-22 (both identifications side by side) awaits the desk |
| r#9 | SPP-54 | `claude/spp-54-sps-pocket-v2kq` | `claude/spp-54-sps-pocket-kx4jvd` | plan §8 W5-r#9 · SPP-54 | design landed 2026-09-07 (no solve; C-3 STOP → R-21; rating after SPP-58) |
| r#9 | SPP-51 | `claude/spp-51-priced-seams-t4nb` | — | plan §8 W5-r#9 · SPP-51 | issued |
| r#9 | SPP-60 | `claude/spp-60-t1h-recipe-w3pd` | — | plan §8 W5-r#9 · SPP-60 | issued (Q59) |
| r#10 | SPP-55 | `claude/spp-55-vrl-scarcity-d7xm` | — | plan §8 W5-r#9 · SPP-55 | issued (hold lifted) |
| r#12 | SPP-46 | `claude/spp-46-gas-split-object-<suffix>` | — | plan §8 W5-r#12 · SPP-46 | issued (SPP-44 R-17; phase 0 before any LP) |
| r#12 | SPP-47 | `claude/spp-47-reference-vintage-rule-<suffix>` | — | plan §8 W5-r#12 · SPP-47 | issued under owner ruling P16 (repo-wide) |
| r#13 | SPP-49 | `claude/spp-49-input-seam-repairs-<suffix>` | — | plan §8 W5-r#13 · SPP-49 | issued under owner ruling P19 (repo-wide) |
| r#14 | SPP-50 | `claude/spp-50-rebaseline-<suffix>` | — | plan §8 W5-r#14 · SPP-50 | ISSUED (SPP-49 landed); one full-span invocation carries wind + both seams |
| r#12 | SPP-48 | `claude/spp-48-wind-level-rule-<suffix>` | — | plan §8 W5-r#12 · SPP-48 | issued under owner ruling P17 (shared repair; landing held behind SPP-46). **Re-assigned FABLE → OPUS in-sitting** on the owner's question: the desk named the construction, so the lane adjudicates nothing |

---

## 6. Errors against interest

| # | Sitting | Error | Consequence | Correction |
|---|---|---|---|---|
| E-1 | r#0 charter (found r#2) | The plan listed **WY** among SPP's missing CEMS states. No EIA-860 plant with BA `SWPP` is in Wyoming (audit §2.4); the plan also omitted **CO** from the footprint. | SPP-11 fetched four inert `WY_*` parquets on the charter's word (harmless: the loader filters to the ISO's fleet). | Plan §2.1 corrected r#2; `ISO_STATES["SPP"]` in the SPP-20 charter now follows audit row 21 (WY out, CO in). |
| E-4 | r#4 (found r#4 am.1) | The r#4 entry stated "W3 waits on SPP-20" and "nothing else newly issuable" without measuring which scripts impose the gate or listing what needs no registration. The owner asked. | Two issuable lanes (SPP-15, the SPP-14 addendum) were a sitting late. | Measured (`get_iso_config` in every W3 derive) and recorded; from r#5 every sitting's §0 entry carries a "what needs no registration / what does" line until SPP-20 merges. |
| E-3 | r#0/r#2 (found r#3) | The plan carried **PRM 15 %** (manifest row 12) and card P5 cited "$2,000 — FERC 831 offer cap" as if it were SPP's posted cap. SPP-12's transcriptions: the live East BAA Base PRM is **16 %** (v5.0A; 15 % was PY2023–25), and SPP's posted Safety-Net Energy Offer Cap is **$1,000** ($2,000 is the Order 831 hard ceiling). The r#2 addendum also cited audit §6.1 to a lane that read it before SPP-10 had merged. | P5's value survives on a different justification (card P10); the PRM row now carries the live vintage with the history cited. | Plan §3 and the SPP-20 charter corrected r#3; the desk cites only landed files in addenda from now on. |
| E-2 | r#2 | The desk ran `git merge --ff-only origin/main` on its branch while the harness was in plan mode (read-only). | None — a fast-forward with no local commits; nothing lost or rewritten. | Recorded because the mode was explicit; the desk does not repeat state changes under plan mode. |
| E-5 | r#5 charters (found r#6) | Three charter defects the W3 lanes had to catch: (i) SPP-30's sequence named `derive_cc_committed_pct.py --iso SPP` — the script has no `argparse`, is ERCOT-only and would have overwritten ERCOT's committed file; (ii) SPP-32 named `data/fuel/hubs.py` as the basis home — the SPP rows belong in `basis/meanzero.py`; (iii) SPP-30's gate read "ZERO full-year fallbacks" — unachievable, every ISO carries `eia923_netzero` units (MISO 135, PJM 95 …). | None landed wrong: SPP-30 refused the script on a scratch proof and reported 9 itemised fallbacks; SPP-32 wired the right file. The desk had asserted the sequence and the gate from docstrings it had not run. | Plan §5/§8 corrected this sitting; standing note: a charter's RUN line is verified against `--help` output, not a docstring, before issuance. |
| E-6 | r#5/r#6 charters (found r#7) | The SPP-40 STOP gate was chartered as "link binds in the measured direction" with no dominance threshold, so the lane operationalised it as a strict inequality and a 22-hour (0.25 %) tie killed a screen whose every sign-based reading agreed with the market; the owner had to direct the full span (P14). | One extra owner intervention; no wrong number landed — the screen record stands unedited and the keeper is the honest baseline. | Standing rule from r#7: every direction/sign leg in an SPP STOP gate states an ex-ante dominance threshold (e.g. ≥ 55 % of at-bound hours) and a minimum liveness (≥ 5 % of hours); written into SPP-57's charter. |
| E-7 | r#7 (found r#8) | The desk chartered SPP-36 → SPP-42 as a dependency chain ("launch SPP-42 after SPP-36 + SPP-41 land") and told the owner it would hold SPP-42 — but the owner launched it at once; it derived the crosswalk itself and solved BEFORE the SPP-41 seam, so keeper-2 carries the unscreened 2023 wind input and a fourth solve (SPP-43) is now owed. The desk's sequencing was advisory and it did not say so. | One extra ~6-minute solve; two lanes derived one file (benign — byte-identical, and a rule-23 check the desk could not have bought otherwise). | Standing from r#8: every charter states what to do when a precondition is UNMET at launch (proceed on a stated basis, or STOP) instead of assuming the desk's order holds; the owner launches what is issued, so issue only what may run now, and put the rest in the next sitting's queue. |
| E-8 | r#8 (found r#9) | The SPP-43 charter's promotion leg (i) demanded bit-identical 2024/2025 P1 objectives without knowing that P1 is warm-started from a basis seeded across years in one invocation, so a byte-identical LP landed on another vertex of the same optimal face and the lane had to STOP on a self-imposed test stricter than any rubric criterion; an owner intervention was needed to promote. | One in-session card; the lane's record is correct and stands. | Standing from r#9: identity legs are written on the P0 objective + the LP input arrays (what the code guarantees), never on a warm-started P1 objective; every SPP FINDING records every pass's objective per year (R-ac). |
| E-9 | r#8 (found r#9) | The desk chartered SPP-38 as "the 15 SPP-era red tests" from SPP-41 §7f's attribution by test NAME; eleven of the fifteen were three unrelated defects (SCN skip guard, unbuilt `data/clean`, NYISO marker drift, miso-233 parity debt). The charter's exit ("the CAISO failure is the ONLY red") was unreachable from the lane's ownership. | A lane spent on triage the desk could have done from the failure causes; two red remain, MISO's. | Standing from r#9: a test-repair charter is issued only after the desk has read the failure CAUSES (`pytest -x` output), not the names; G19 added to plan §7 (build `data/clean` before gates; cold-start curation failures). |
| E-10 | r#0–r#10 (found r#11) | The desk's house style and every charter's EXIT line made lanes edit the shared tables (plan §5/§9, ledger, log, CHANGELOG, shard stamp) in their own PRs. Parallel lanes then collided on every merge. | Four PRs for SPP-57, three for SPP-43, merge-in commits on lane branches, two desk-branch divergences; hours of owner time re-merging. | Plan §8.0 COLLISION RULES (standing): lanes own only their FINDING + their cell line; the desk writes every shared record from the FINDING at refresh; rebase never merge-in; one PR per lane. |
| E-11 | r#9 charter (found r#12) | The **SPP-45** charter told the lane to re-key a board row the desk had measured RED at its own pin, but carried **no instruction to re-verify the gate at the lane's own pin first**. Between issuance and launch a parallel Fable session fired the same Q34 standing duty at `d26652f3` and the row went green. | None material — the lane supplied the missing discipline itself, re-ran `check_gate_a_provenance` at its own base, refused to manufacture a supersession that did not happen, and spent the session on what was actually still owed. Had it obeyed the charter literally it would have written a false provenance claim into a governance file. | **STANDING (desk rule):** every charter whose deliverable is "repair a red gate" opens with *re-run the gate at YOUR base sha before touching anything; if it is green, do not re-key — report what is still owed and stop*. Added to the STANDING RULES block. |
| E-12 | r#9/r#10 charters (found r#12) | Three lanes running in parallel (**SPP-54, SPP-55, SPP-58**) each minted routed items numbered **R-21 … R-25** inside their own FINDING, because the desk's charters ask for per-FINDING numbering while the ledger's register is lettered. A bare citation "R-21" is now ambiguous across three documents (it means the wind-level rule, the C3c-is-RT finding, or the ψ card, depending). | Citations already written in the four FINDINGs and their log entries are ambiguous on their face; nothing is lost, but a reader must open all three. | Every citation in this ledger from r#12 forward reads **`<lane> R-nn`** (e.g. "SPP-54 R-21"), never a bare `R-nn`; the desk's own register stays lettered (R-a … R-au) so the two namespaces cannot collide. Added to the STANDING RULES block. |
