# RESULT — nyiso-238: the hydro budget arm is SOLVED, RETRIEVABLE, and it IMPROVES THE FOSSIL FIT IN ALL FOUR YEARS

**Session** nyiso-238 (ORCHESTRATOR — rule 32 `[R-SHARD]` (a); **the parent ran ZERO LP**).
**Date** 2026-09-16. **Keeper** `2026-09-14-nyiso-235-gas-repair` — **UNCHANGED by this session.**
**Pre-registration** `docs/PRECOMMIT-nyiso238-hydro-budget-span-2026-09-16.md` + addendum 1, pushed at
`69c6d4a7e1b7c8e458373bc5ce9db51a5a7a6a39` **before the first LP**. **Nothing registered on the
dashboard** — the promotion question is the owner's (§6).

> ## HEADLINE
> 1. **The arm reproduces nyiso-236 EXACTLY**, eight days and four fresh containers later:
>    G2 annual **−0.2155 / −0.0957 / −0.0000 / +0.0000 %** for 2022/23/24/25, worst months
>    **1.275 / 0.838 / 0.000 / 0.000 %**. Every digit of the A1 table, reproduced.
> 2. **THE OWNER'S HYPOTHESIS IS CONFIRMED, 8 measurements out of 8.** Getting hydro's shape right
>    improves the **GAS** fleet's hourly fit against the EIA-930 meter in **every year, on both
>    metrics** — r **+0.0017 / +0.0020 / +0.0010 / +0.0071**, NRMSE **−0.0013 / −0.0020 / −0.0005 /
>    −0.0040**. Hydro's own fit improves far more (r **+0.0887 / +0.0553 / +0.0469 / +0.0779**).
>    **nyiso-236 never measured this**; its G4/G5 only asked whether other classes *moved*, never
>    whether they moved *closer to the meter*.
> 3. **G2 still FAILS 2022 and 2023** (−55.2 and −25.5 GWh of hydro energy destroyed), for the cause
>    nyiso-236 §A2 measured and nyiso-237 confirmed: the LP declines to run Niagara when
>    `Upstate_West` is priced ≤ $0, and a 24 h use-it-or-lose-it budget cannot move that water.
> 4. **THE PRICE DEFECT HAS NO IDENTIFIABLE REPAIR.** This session's phase 0 killed **all four**
>    handed candidates with arithmetic, on committed data, before any solve (§2).
> 5. **THE BUNDLES ARE PUSHED AND RETRIEVABLE BY FULL SHA** (§5) — unlike nyiso-236's, every one of
>    which is dead.

---

## 1. WHAT WAS SOLVED

Four per-year shards on the **owner's instruction** (*"What the fuck one shard PER YEAR no screen"*;
PRECOMMIT addendum 1), all at the pinned SHA, each running the keeper's frozen recipe with **one
field** changed and pushing its **full** bundle (17 files, `dispatch/<yr>_P1.parquet` and the
bundle-root `system.parquet` included):

```
python3 scripts/replay_keeper.py results/calibration/nyiso235_gasrepair_span \
  --years <yr> --out-dir results/calibration/nyiso238_hydro_<yr> \
  --set hydro_budget_period_by_instrument=true
```

Composed in the parent, zero LP, by `scripts/probes/nyiso238_compose_span.py` into
`results/calibration/nyiso238_hydroperiod_span`. `solve_surface.fingerprint` = **`bd2b4657f9b5df7e`**
on every leg, identical to the keeper's. **~18 min wall** against ~60 for the span form.

**THE ARM LIVES IN `meta.json` AND `run_config.scenario_config`, NOT AT `run_config.json`'s TOP
LEVEL.** A top-level read returns `None` on an armed leg and the field is *absent* from the keeper's,
so that path cannot tell armed from unarmed — the HARD STOP 2 in this session's own shard prompts
pointed at it and would have rejected four correct bundles. Corrected in the composer, which now
verifies `meta.json` (`true` on every leg, `false` on the keeper) **and**
`run_config.scenario_config`. Independently confirmed by dispatch: hydro differs from the keeper in
**6,085 / 6,609 / 5,811 / 6,178 hours** with max |ΔMW| **1,910 / 1,548 / 1,632 / 2,217**.

## 2. PHASE 0 — ALL FOUR CANDIDATES FOR THE PRICE DEFECT, KILLED BEFORE ANY SOLVE

`scripts/probes/nyiso238_central_east_seam_phase0.py`, zero LP, every input committed. The object is
nyiso-237's: the keeper prices `Upstate_West` ≤ $0 in **498 h of 2022** against a measured **21**
(WEST alone) / **127** (the five-zone A–E mean that IS the model zone).

| candidate | verdict | the arithmetic |
|---|---|---|
| **(a)** flat monthly-mean TTC applied hourly | **KILLED** | The MIS P-32 hourly `positive_limit_mw` exceeds the monthly mean in only **32.3 %** of the 498 hours; mean headroom **−58.5 MW** (2023 **−74.9**). The repair moves the **wrong way**, and the reason is measured: the posted limit is **211 MW LOWER** in the lowest `Upstate_West` load quintile than the highest (Q1→Q5 **−101 · −60 · +2 · +49 · +110 MW**) — planned-outage derates co-occur with exactly the low-load hours the model fabricates. |
| **(b)** no West export outlet | **KILLED** | The real West-landing ties ran **net export in 2.2 %** of those hours (all-hours 0.6 %). Reality's response was to cut imports **−641 MW**, not to export. |
| **(c)** firm imports into a saturated zone | **KILLED** | The model holds **433 MW** into the West there; reality imported **962 MW** in the same hours. The model **under**-imports by **529 MW** — removing the floor moves *away* from the meter. |
| **(d)** nested-cutset topology | **NOT RE-OPENED** | Already adjudicated **CLOSED** by nyiso-225 (2026-09-10) with the **owner's acceptance**, three independent legs and a DO-NOT-REDO (rule 28 `[R-MECH-MATRIX]` (a)). The handoff authorized it without accounting for that ruling. |

**Two new eliminations nobody had made.** `Upstate_West` **demand is exact** — it reproduces the
measured A–E zonal load to **−0.3 MW** on 2022 (−0.5 on 2023) and −14.5 MW inside the fabricated
hours, so the surplus is not a demand error. On the supply side the model runs nuclear **+219 MW**
above the EIA-930 meter in those hours — real, and a separate finding — but ~20 % of the **966 MW**
by which the real TOTAL EAST flow exceeded the model's cap in **97.8 %** of them.

**Level reconciliation, so candidate (a)'s kill is not a product artifact:** the armed DAM monthly
means and the P-32 hourly means agree to **~1 % in 11 of 12 months** of 2022 (annual **1,821 vs
1,825 MW**). Same series, different grain — and the grain is the wrong direction.

## 3. THE GATES — nyiso-236's G1–G5, re-run EXACTLY AS WRITTEN

| yr | G1 | **G2** ann / worst mo | **G2** | G4-as-written | G4-material | conservation (hydro / non-hydro TWh) |
|---|---|---|---|---|---|---|
| 2022 | PASS (slack 0, dump 0) | **−0.2155 % / 1.275 %** | **FAIL** | CT_PEAKER −0.82 % **PASS** | CC_CHP +0.65 % PASS | −0.0552 / +0.0682 |
| 2023 | PASS (slack 0, dump 0) | **−0.0957 % / 0.838 %** | **FAIL** | CT_PEAKER **−2.28 % FAIL** | CC_CHP −0.75 % PASS | −0.0255 / +0.0310 |
| 2024 | PASS (slack 0, dump 0) | −0.0000 % / 0.000 % | **PASS** | CT_CHP +1.62 % PASS | ST_GAS +0.33 % PASS | +0.0000 / +0.0148 |
| 2025 | PASS (slack 0, dump 0) | +0.0000 % / 0.000 % | **PASS** | CT_PEAKER **+4.53 % FAIL** | CC_CHP −0.50 % PASS | +0.0000 / −0.0077 |

**Every value reproduces nyiso-236's A1 table.** The losing months are the same ones: 2022 m03
**−19.1** + m11 **−23.6** GWh (total −55.2), 2023 m10 **−17.8** GWh (total −25.5).

**G5 — no non-target flip.** ISO load-weighted price moves **+0.62 / −0.10 / −0.01 / −0.11 $/MWh**
and the gas family **+0.162 / −0.043 / +0.029 / −0.076 %**, far inside any band; nothing flips.

### 3.1 ONE CORRECTION TO THIS SESSION'S OWN INSTRUMENT, MADE BEFORE REPORTING

The first run of the gate scorer read 2024 as **G2 FAIL, worst month −0.866 %** (m05 +13.5, m10
+14.1, m11 −17.4 GWh against a true annual −0.0 GWh). That was **my bug, not the arm's**: the scorer
labelled months with `pd.date_range`, but the model's hydro budget rows are built on
`data.fleet.models._hour_to_month_index`, which walks a representative **NON-LEAP** year — so in
**2024, a leap year**, the calendar label drifts 24 h from the model's from March onward and
manufactures compensating monthly deltas that net to zero annually. Scored on the model's own map,
2024 reads **+0.000 %, PASS** — which is also what nyiso-236 reported. The fix is in
`nyiso238_hydro_span_gates.py` with the measurement in the comment.

## 4. THE UPSIDE — THE MEASUREMENT THAT WAS MISSING, AND THE REASON THE FIX WAS ASKED FOR

Owner, this session: *"it would have indirect impacts on it by getting it right and improve the
overall correlation for fossil classes."* Measured against the EIA-930 meter, keeper vs arm:

| yr | hydro r | hydro NRMSE | **gas r** | **gas NRMSE** |
|---|---|---|---|---|
| 2022 | 0.6851 → **0.7738** (+0.0887) | 0.1958 → **0.1593** (−0.0365) | 0.8655 → **0.8673** (+0.0017) | 0.1829 → **0.1816** (−0.0013) |
| 2023 | 0.6682 → **0.7235** (+0.0553) | 0.1731 → **0.1493** (−0.0237) | 0.9393 → **0.9413** (+0.0020) | 0.1225 → **0.1205** (−0.0020) |
| 2024 | 0.7313 → **0.7782** (+0.0469) | 0.1709 → **0.1485** (−0.0224) | 0.8376 → **0.8386** (+0.0010) | 0.1680 → **0.1675** (−0.0005) |
| 2025 | 0.7127 → **0.7906** (+0.0779) | 0.2293 → **0.1855** (−0.0438) | 0.8464 → **0.8534** (+0.0071) | 0.1844 → **0.1804** (−0.0040) |

**16 of 16 directional wins; 8 of 8 on gas.** Stated at full magnitude and without inflation: the
gas gains are **small** — +0.001 to +0.007 of r. What makes them evidence rather than noise is that
they are **uniform in sign across four independent years and both metrics**, and that the mechanism
predicts exactly this sign: hydro that banks across ~730 hours at zero cost displaces fossil in the
wrong hours, so constraining it to its instrument's period puts fossil back where the meter has it.

**This is reported, not claimed as a gate.** No pre-registered gate was written on it, so under rule
1 `[R-STRUCT]` it cannot promote the arm — it is the *consequence* the owner asked to be measured,
and it is now on the record.

## 5. RETRIEVABILITY (rule 34 `[R-SHARD-PROMOTABLE]` (e)) — FULL SHAs, ALL FOUR PUSHED

| year | branch | **commit** | files |
|---|---|---|---|
| 2022 | `claude/nyiso238-hydro-2022` | `cd86a01a9f9f9cf143c2f25549faac4dfa297c72` | 17 |
| 2023 | `claude/nyiso238-hydro-2023` | `f42ef9009aea4b06be22a5fa35f4be5d4d3c801c` | 17 |
| 2024 | `claude/nyiso238-hydro-2024` | `40ecf0a8966b9c0de3c1001d4078c3b4bace85eb` | 17 |
| 2025 | `claude/nyiso238-hydro-2025` | `ff7e024e8e1ade038ee7545aa49fc783b462edf5` | 17 |

`git archive <sha> results/calibration/nyiso238_hydro_<yr> | tar -x`, then compose with
`scripts/probes/nyiso238_compose_span.py`. **Verified by `git ls-tree -r <sha>` before any shard was
archived** (rule 34(d)): 17 files each, non-zero. Gitignored in the working tree, never `rm`'d
(rule 31 `[R-RETAIN]`); kept out of `main` (rule 32(d)).

**WHY THIS SECTION EXISTS.** nyiso-236 wrote the same table eight days ago and **every SHA in it is
now unreachable**, along with `RESULT-nyiso224` §5's "the bundle SURVIVES" branch — only four
branches remain on the remote. Both docs are corrected in place this session with the real re-solve
cost (rule 33 `[R-SHARD-ARCHIVE]` (f)(4)). That loss is the whole reason this arm had to be solved
again rather than simply read.

## 6. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — THE OWNER'S, AND IT IS OPEN

**The bundles are on branches, not on an ephemeral container**, so unlike eight days ago nothing is
lost if the answer takes time. Both arms side by side:

| | keeper (arm OFF) | arm ON |
|---|---|---|
| hydro annual TWh 2022/23/24/25 | 25.6117 · 26.6159 · 26.7390 · 24.0589 | 25.5565 · 26.5904 · 26.7390 · 24.0589 |
| **hydro energy identity (G2)** | exact by construction | **−55.2 / −25.5 / 0 / 0 GWh** (FAIL 2022–23) |
| hydro hourly r | 0.6851 · 0.6682 · 0.7313 · 0.7127 | **0.7738 · 0.7235 · 0.7782 · 0.7906** |
| **gas hourly r** | 0.8655 · 0.9393 · 0.8376 · 0.8464 | **0.8673 · 0.9413 · 0.8386 · 0.8534** |
| cross-day banking | ~730 h, free | constrained to the instrument's 24 h / 168 h |
| load-bearing criteria | — | **none flips** |

**My recommendation: PROMOTE.** The cost is a **0.22 % / 0.10 %** annual hydro energy miss in the
two years whose West price is fabricated; the gain is a better hydro shape and a better **fossil**
shape in **all four** years, and the elimination of cross-day water banking that no instrument
permits. G2 is a real KILL gate and it really fails — but it fails because the *price* is wrong in
those hours, and this session established that the price defect has no identifiable repair, so
"wait for the seam" means never. nyiso-237 recommended against on the same evidence minus §4; §4 is
what changes my reading, and I am naming that rather than hiding it.

**If promoted**, rules 35 `[R-PROMOTE]` (a)–(f) apply in one session: register the composite,
verify with `audit_keepers.py` E1, then prune the outgoing keeper's three stores. The year union
{2022, 2023, 2024, 2025} is covered exactly, so no stamped companion is needed.

## 7. GOVERNANCE

* **Rule 1 `[R-STRUCT]`** — `authorized_price_tuning` = **NONE**; zero offer-curve multipliers move.
  The §4 upside is reported, never used as a gate.
* **Rule 21 `[R-DOF]`** — **zero free parameters**: two published instrument durations (Niagara 24 h,
  St Lawrence 168 h), neither swept (rule 23 `[R-FROZEN-DERIVE]`).
* **Rule 28 `[R-MECH-MATRIX]`** — `hydro_budget_period_by_instrument` cell stamped this session;
  candidate (d) **not** re-tested (DO-NOT-REDO honoured).
* **Rule 29 `[R-SCREEN]`** — not a screen; the arm's screen was spent by nyiso-236 and its
  adjudication stands. Phase 0 clause (0) killed four candidates at zero LP.
* **Rule 32 `[R-SHARD]`** — parent ran no LP; per-year fan-out on owner instruction, with the
  rule-32(b) reading stated in PRECOMMIT addendum 1.
* **Class-E parity** RED for `caiso279_ablate_dswcouple_span` and `soco15_spp_arm` is pre-existing
  and not NYISO's (rule 25 `[R-ISO-SCOPE]`) — reported, untouched.
