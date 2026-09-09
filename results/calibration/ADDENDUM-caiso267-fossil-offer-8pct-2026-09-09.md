# ADDENDUM to PRECOMMIT-caiso267 — **OWNER PIVOT**: the corpus lane is closed; the session becomes an authorized offer-curve price-tuning solve, **fossil bands × 0.92, CAISO-scoped**

**Session caiso-267, 2026-09-09.** Branch `claude/busy-volta-u6dlvt`.
**PUSHED BEFORE THE FIRST LP.** Every number below is measured from committed
artifacts with **zero LP**; no solver has been called at the moment this
document is committed.

---

## §A — What the owner ruled, verbatim, and what it replaces

Mid-session, in answer to the PRECOMMIT §3 funding question, the owner ruled:

> *"Stop doing this and pivot to a solve that reduces fossil free curves by 8 %
> across the board because they are overshooting significantly that that will
> ring 2021 in tolerance."*

and, immediately after, two clarifying instructions:

> *"Don't do any more data fetching"*
> *"I don't care what measured says just adjust it 8 % downward"*

Read as written (the two evident typos are "free" → **offer** and "ring" →
**bring**). **Effect on the PRECOMMIT:**

* **§3, §5 (T0–T4) and §6 are WITHDRAWN.** The `PUB_DAM_GRP` thermal read is
  **not** executed. One request was issued before the pivot — the pre-registered
  1-day reachability probe of §3 (2024-04-10) — and it is reported in §B below.
  **No further fetch of any kind occurs in this session.**
* **§1 (DO-NOT-REDO), §4 (the BELLY definition), §7 and §8 (governance) STAND.**
* The session's deliverable changes from a measurement to a **solve**.

**I raised two objections before executing; the owner reaffirmed; they are the
owner's decision and are recorded here rather than re-argued.** Stated once,
at full magnitude, because a reader of this run needs both:

1. **For CAISO the measured surface points the other way.** caiso-266 §7
   measured the CC bands pooled over 2023–2025: `committed` **1.030** against
   an armed 1.000, and `econ_low` / `econ_high` / `peak` measured at **exactly**
   their armed 1.066 / 1.072 / 1.386. A measured-faithful repair therefore moves
   the CAISO belly price **UP**. This run moves it **DOWN**. It is consequently
   **NOT** a rule 14 `[R-ACCURATE]` measured-input repair and is never described
   as one — it is the rules 1 `[R-STRUCT]` / 13 `[R-MEASURED]`
   **authorized price-tuning channel**, declared under §C.
2. **The 8 % is not selected against 2021, and 2021 is not touched.** See §F.

## §B — The one request that was issued (disclosure, PRECOMMIT §3)

The pre-registered reachability probe ran before the pivot arrived:
`GroupZip PUB_DAM_GRP 20240410` → **382,728 B zip in 1.3 s**, one member,
10,988,166 B CSV, **41,616 data rows**, **28 columns** matching
`scripts/lib/dam_public_bids/caiso.py::_RAW_COLS` exactly. **No price and no MW
was read from it**, exactly as pre-registered, and the file was not retained.
Measured cost of the corpus, for whoever picks the G-26 lane up later:
**0.38 MB/day**, ~7.3 s/request at the OASIS AUP throttle, hole rate
**1/1,096 = 0.091 %**. The corpus is reachable; it was simply not funded here.

## §C — The mechanism, and the rule 1 `[R-STRUCT]` carve-out conditions, each answered

**Mechanism.** Multiply **every** `offer_curve_by_group` band multiplier of
**every fossil class** by **0.92**, applied through the operator override
channel (`replay_keeper.py --offer-curve-json`, which resolves at
`pipeline/backcast_config.py:2523` — *after* every per-ISO and measured-surface
merge, so the cut is not silently overwritten). The resolved absolute values are
committed verbatim at `results/calibration/_caiso267_fossil92_offer_curve.json`
and reproduced in §D.

The carve-out is **narrow and conditioned**; every condition binds:

* **(a) the channel is the band multipliers ONLY.** Exactly four bands move per
  class — `committed`, `econ_low`, `econ_high`, `peak`. **UNTOUCHED:** every
  `phys_*` key (measured physics), `econ_low_share` and `pct_peaking` (the
  structural shares), and every non-band key. No adder, offset, haircut, load
  proxy or gas discount exists anywhere in this run.
  **One derived consequence, disclosed:** `CC_REGULAR` and `CT_PEAKER` carry a
  `peak_ladder` — five equal-capacity rungs the `caiso_offer_surface_conditional`
  split writes as *uniform copies of the resolved peak*. That split runs at
  `backcast_config.py:2609`, **after** the override, and **rebuilds the ladder
  from the post-override `peak`**. So the ladder follows the cut automatically,
  the "N equal sub-bands at one MC == one flat band" identity is preserved, and
  **no separate ladder parameter is introduced**. Verified pre-solve: the
  keeper's ladders are `[[0.2, 1.386]×5]` and `[[0.2, 1.154]×5]` — uniform
  copies of `peak` in both classes.
* **(b) ONE config across EVERY scored year.** A single factor, 0.92, one
  override file, one invocation covering `--years 2023 2024 2025`. **No per-year
  value exists and none will be produced.**
* **(c) set EX ANTE, declared BEFORE the solve, NEVER swept.** The factor is the
  owner's, handed down in §A before any solve; this document is committed and
  pushed **before the first LP**. **The factor will not be swept.** If the gates
  do not land where the owner expects, the RESULT reports that at full
  magnitude — it does **not** try 6 % or 10 %. Trying a second factor to make a
  criterion pass is precisely the fitted-mechanism selection condition (c)
  forbids, and it stays forbidden in this session.
* **(d) merit-order adjustment across classes is INTENDED, not a defect.** A
  uniform 0.92 preserves every *relative* band ratio, so the fossil stack's
  internal merit order is unchanged; what moves is fossil against **non-fossil**
  (hydro, imports, storage, renewables), which is the intended effect.
* **(e) declared in the attestation + carried in the DOF ledger.** The bundle's
  `calibration_attestation.json` will carry an `authorized_price_tuning` block
  naming this ruling (C6 FAILS without it), and the DOF ledger gains **one** free
  parameter — `fossil_offer_band_scale = 0.92` — whose identification source is,
  per rule 20 `[R-DOF]`'s cross-reference, **"price residual, authorized channel
  (rules 1/13 amendment 2026-09-05); owner ruling 2026-09-09"** — never a
  measured input. Under that same cross-reference its presence does **not** by
  itself make the residual it closes an open root-cause issue; **every other**
  tuned value still would, and no other one exists here.

**Rule 25 `[R-ISO-SCOPE]`:** the cut is applied as a CLI override on a **CAISO**
invocation. It touches no shared default, no `constants.py` value and no other
ISO's curve. "Across the board" is read as *across every fossil class of this
ISO*, which is what rule 25 permits; it is **not** propagated to ERCOT, PJM,
MISO, NYISO, NEISO or SPP by this session.

**Rule 24 `[R-REGISTRY]`:** the resolved curve is recorded verbatim in the
bundle's `run_config.json` (`scenario_config.offer_curve_by_group`), so the
channel is on-registry and inspectable. No env var, no hardcoded dict.

## §D — The 13 classes and 52 bands that move (measured, pre-solve)

Every fossil group in `offer_curve_by_group`; nothing else exists in it.

| class | committed | econ_low | econ_high | peak |
|---|--:|--:|--:|--:|
| CC_REGULAR | 1.000 → **0.920** | 1.066 → **0.98072** | 1.072 → **0.98624** | 1.386 → **1.27512** |
| CC_INTERMEDIATE | 0.920 → 0.84640 | 0.950 → 0.87400 | 1.080 → 0.99360 | 2.250 → 2.07000 |
| CC_CHP | 1.000 → 0.92000 | 1.066 → 0.98072 | 1.072 → 0.98624 | 1.386 → 1.27512 |
| CT_CHP | 1.100 → 1.01200 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| CT_PEAKER | 0.991 → 0.91172 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| CT_INTERMEDIATE | 1.000 → 0.92000 | 1.000 → 0.92000 | 1.200 → 1.10400 | 3.000 → 2.76000 |
| ST_GAS | 0.810 → 0.74520 | 1.103 → 1.01476 | 1.146 → 1.05432 | 1.154 → 1.06168 |
| ST_GAS_INTERMEDIATE | 1.000 → 0.92000 | 1.000 → 0.92000 | 1.150 → 1.05800 | 2.200 → 2.02400 |
| COAL_LIGNITE | 0.950 → 0.87400 | 1.140 → 1.04880 | 1.150 → 1.05800 | 1.550 → 1.42600 |
| COAL_PRB | 0.950 → 0.87400 | 0.770 → 0.70840 | 1.190 → 1.09480 | 1.480 → 1.36160 |
| COAL_BIT | 0.900 → 0.82800 | 0.950 → 0.87400 | 1.100 → 1.01200 | 1.450 → 1.33400 |
| COAL_WC | 0.850 → 0.78200 | 0.900 → 0.82800 | 1.020 → 0.93840 | 1.200 → 1.10400 |
| COAL | 0.900 → 0.82800 | 0.950 → 0.87400 | 1.100 → 1.01200 | 1.450 → 1.33400 |

**Which of these actually carry CAISO energy** (keeper P1, committed
`class_hourly_<y>` sidecars, TWh): CC_REGULAR 48.40/46.10/40.33 · CC_CHP
8.48/7.53/7.56 · CT_PEAKER 2.04/1.67/0.79 · CT_CHP 1.24/1.23/1.20 · ST_GAS
0.119/0.193/0.022 · COAL 0.090/0.045/0.076. The four `*_INTERMEDIATE` classes
and COAL_LIGNITE/PRB/BIT/WC carry **zero** CAISO energy in all three years
(`cc_intermediate_split` and `ct_intermediate_split` are both `false`); they are
included so the declaration is complete rather than partial, and they are inert.

**Two per-plant bypasses that blunt the cut, disclosed pre-solve:**
`caiso_st_gas_committed_measured` and `caiso_st_gas_peak_measured` are both
armed, and their consumer resolves those bands **per plant** for the
`ST_GAS_PEAKER_PLANTS` members, bypassing `offer_curve_by_group` entirely
(that bypass is the defect caiso-239 repaired). So the ST_GAS `committed` and
`peak` cuts reach only the non-bypassed ST_GAS units. ST_GAS is 0.02–0.19 TWh —
0.04 % of fossil energy — so this is a completeness note, not a material one.

## §E — Rule 29 `[R-SCREEN]`: the screen year, and why it is not the residual's

**Zero-LP step 0 (done, above and here).** Offer-array delta computed from the
committed `class_band_hourly_<y>` sidecars: each band's P1 energy × its own
Δmc, where Δmc = 0.08 × HR_mult × base_HR × (gas + 0.057 t/MMBtu × CARB). Base
heat rates are the committed measured surface's own (CC 7.442, CT 10.862, ST_GAS
11.847); gas 2.54/2.19/3.52 $/MMBtu and CARB 33.03/35.23/28.06 $/t are the run's
own recorded values.

| year | fossil TWh | **$ of offer re-pricing** | mean Δmc on fossil MWh | C3a residual |
|---|--:|--:|--:|--:|
| **2023** | **60.280** | **$171.5 M** | **$2.845/MWh** | +4.37 % |
| 2024 | 56.726 | $153.4 M | $2.704/MWh | **+8.89 %** |
| 2025 | 49.908 | $163.0 M | $3.266/MWh | +8.25 % |

**SCREEN YEAR = 2023**, fixed here before the screen runs. It is the largest
footprint on **both** available measures — the $ of offer re-pricing (the
mechanism's own quantity) *and* raw fossil energy — so the choice does not turn
on which measure is preferred. **It is simultaneously the year with the
SMALLEST residual**, which is the check that matters: rule 29 forbids choosing
by the residual, and a residual-driven choice would have picked 2024.

**Pre-solve prediction, so the screen has something to falsify.** Mean Δmc on
2023 fossil energy is **$2.845/MWh**. Model C3a 2023 is +4.37 % on a $54.17
actual, i.e. **+$2.37/MWh**. So λ should fall by an amount of order $2–3/MWh in
gas-marginal hours, and fossil energy should *rise* modestly as fossil displaces
imports/hydro at the margin. A move an order of magnitude away from that, or in
the wrong direction, means the mechanism is not doing what its own arithmetic
says.

**The screen gate is STRUCTURAL and STOP-ONLY. It may kill the arm; it may
never promote it, and it is NOT gated on the target residual** (a screen that
read "did C3a improve" would be exactly the selection rule 1(c) forbids, one
year at a time). Fixed here:

* **G-IDENT** — the arm differs from the control by the offer curve and
  **nothing else**: demand, renewables, hydro, imports, outages and fleet
  capacity byte-identical. Any other moved input **STOPS** the session.
* **G-FOOT** — the dispatch response is confined to the rows the mechanism
  claims: fossil classes and the prices they set. Non-fossil *capacity* and
  *availability* unchanged (their dispatch may of course move — that is the
  mechanism working through the merit order).
* **G-DIR** — |Δλ| in 2023 lands in **[$0.5, $8.0]/MWh** and is **negative**
  (a cut cannot raise the annual mean price). Outside that band the pre-solve
  arithmetic and the LP disagree and the session STOPS to find out why.
* **G-NOFLIP** — no **non-target load-bearing** criterion flips PASS → FAIL
  (C1, C2, C3b, C4, C6, C8). C3a is the target and is exempt in both
  directions. **C3c is exempt** — rubric v3.6, already the keeper's single
  ledgered caveat.

**Only if all four hold** does the full span run, as ONE
`--years 2023 2024 2025` invocation and ONE bundle (rule 16 `[R-ALLYEARS]`).
The screen bundle is a **throwaway diagnostic probe** — never registered, never
a keeper, never quoted as a keeper number, and 2023 is re-solved inside the full
bundle.

**G-CTRL: form 4 is NOT claimed, and a one-year control IS spent.** Rule 29(b)
makes the keeper's committed bundle the default control, valid only when a
**G-DRIFT** audit classifies every changed hunk on the backcast solve path as
INERT. Measured: `git diff bdfb3095..HEAD` (the keeper's own merge commit, its
recorded `git.sha e162147b` and `basis_sha` both being unreachable after the
branch merged) over `src/market_sim`, `scripts/run_calibration*.py`,
`scripts/lib`, `data/raw/_validation-source`, `data/raw/reference` touches
**94 files, +46,838 / −26,486 lines**, including `results/cache.py` (+342),
`model/interchange/spec.py` (+691), `model/reserves/spec.py` (+272),
`data/fleet/floors.py` (+269), `runner.py` (+137) and `backcast_config.py`
(+143). **A credible hunk-by-hunk INERT classification of that is not
achievable in this session, so I do not assert one.** Rule 29(b) provides for
exactly this case — a LIVE hunk earns a control solve "for the years the screen
needs" — so the control is replayed **on 2023 only**, at HEAD, from the
keeper's own `meta.json`, concurrently with the arm (rule 12: separate
invocations, 2 concurrent). This makes the A/B an **exact single-delta at one
code basis**, and the control-vs-committed-keeper difference additionally
*measures* the drift instead of asserting it.

## §F — 2021: reported, never fitted to, and **not touched**

The owner's stated motivation is that the cut "will bring 2021 in tolerance".
**No part of this session is identified against 2021, and 2021 is not solved,
scored or registered.** Three independent reasons, all measured:

1. **Rule 22 `[R-HOLDOUT]` — 2021 is validation tier.** It may only ever be a
   **re-test** of a config identified on 2023–2025. This config is identified on
   nothing at all: 0.92 is an ex-ante constant. Selecting it *because* it moves
   2021 would be per-criterion selection against a holdout year, which rule 1(c)
   forbids, so the value is fixed here and **will not be swept** whatever 2021
   would say.
2. **2021 is not scoreable today.** The committed hourly actual-LMP reference
   `data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet` carries years
   **{2022, 2023, 2024, 2025, 2026}** — there is **no 2021 row** — and
   `frontend/data/backcast/bench/CAISO/` holds **2022–2025** only. There is
   nothing to score a 2021 solve against.
3. **The two standing blockers are unchanged** (caiso-266 §11 #4): a **60-day
   RTM gap** 2021-08-02..09-30 in the source, and a `CAISO_PARTIAL_YEARS`
   amendment (currently `frozenset({2026})`) that **CAISO cannot grant itself**.

If the owner wants the 2021 rung, it needs its own session: the RTM gap
re-fetched, the actual-LMP reference extended, a bench part built, and the
`CAISO_PARTIAL_YEARS` amendment ruled on. **That is a separate decision and this
session does not pre-empt it.**

## §G — Exposures declared BEFORE the solve

So that no post-hoc reading of the result can be presented as a prediction:

* **C3a may cross zero.** The keeper is +4.37/+8.89/+8.25 %; mean Δmc is
  $2.85/$2.70/$3.27 against gaps of $2.37/$3.08/$2.84. **A cut of this size is
  the same order as the whole residual in every year**, so C3a landing
  *negative* in 2023 (where the gap is smallest and the cut largest) is a live
  outcome, not a surprise. It will be reported at full magnitude either way.
* **C4-2025 is on a knife edge.** Gas NRMSE 0.287/0.260/**0.298** against a
  ≤ 0.300 tolerance. This mechanism changes gas dispatch directly. **C4-2025 is
  the single most likely G-NOFLIP failure** and it is named here, in advance.
* **C3c-2023** (price tail / scarcity) is the keeper's ledgered caveat and stays
  ledgerable under rubric v3.6; it is exempt from G-NOFLIP.
* **C1** (12/12 free, 8/8) is a class-volume criterion and fossil volume moves
  by construction; a C1 cell flip is a real possibility and is gated.
* **The determination may get worse.** If it does, that is the result, reported
  as such. The keeper is not replaced by a worse run.

## §H — Governance carried from the PRECOMMIT

* **Rule 15 `[R-DASHBOARD]`** — the full-span bundle is registered whatever it
  says, keeper or rejection. The **screen** bundle and the **control** bundle are
  never registered (rule 29(2)/(c)) and are `.gitignore`d so they cannot reach
  `main` or turn the parity gate red.
* **Rule 31 `[R-RETAIN]`** — **nothing solved is deleted.** Gitignore discharges
  the delete-before-merge duty; `rm` does not. The promotion question is put to
  the owner **explicitly** before the session ends, together with the statement
  that the bundles live on local disk and do not survive container reclamation.
* **Rule 28 `[R-MECH-MATRIX]`** — `offer_curve_by_group` is an existing matrix
  row; its CAISO cell takes this session's evidence and, if the run is promoted,
  the keeper/gates re-stamp. No new `ScenarioConfig` field is created, so duty
  (c) does not fire.
* **Rule 27 `[R-PUSH]`** — no source file ≥ 300 lines is rewritten. The only
  code touched is a `.gitignore` line.
* **The caiso-265 §4 `rt_lw` retrofit stays INERT** — no 2022 year is solved
  here, so the bench part is not rewritten.

**Next number: caiso-268.**
