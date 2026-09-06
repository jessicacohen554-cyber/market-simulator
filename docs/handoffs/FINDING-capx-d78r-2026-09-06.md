# FINDING — capx D78-R: the sector gate is an EXACT candidate-set partition across the whole 2021–2025 window — every control-only row is sector-1 in all five years, the arm-only set is EMPTY, the 2022 auction is byte-identical, and composition and LOYO both hold; but the PRE-REGISTERED W4 band and the W5 purity gate FIRED, so the pre-stated recommendation is HOLD-and-route, not ARM

**Lane:** capx D78-R (director r#48, pack §D78-R; D78 §8 item 2 is this lane's spec).
Pre-registration `PRECOMMIT-capx-d78r-full-window-2026-09-06.md`, **pushed at `fa8a857d` before any
LP**, with **ADDENDUM 1** (the band on the first control), **ADDENDUM 2** (the LIVE-hunk re-audit
and the W0 restatement) and **ADDENDUM 3** (the band on the rebased control) each pushed **before
the solve they govern**. Instrument `docs/handoffs/d78r/window_compare.py`, committed at
`41b46142` **before the first LP**.
**Branch:** `claude/capx-d78r-full-window-s35hos`, off `origin/main` `acbb5350`, **rebased mid-lane
onto `c3988c73`** (§1).
**Date:** 2026-09-06. **Model:** Opus. **DATA PROFILE:** `pjm`.

**NOTHING ARMS. NO MECHANISM CODE WAS WRITTEN.** No new field, no default flip, no `_pjm_config`
override, no parameter value, no keeper, no marker. `retirement_sector_gate` stays default-off and
un-overridden for PJM. The arm is registered SUFFIXED as **`pjm-t1h-d78r-sectorgate`**; the bare
`pjm-t1h` key is untouched; the control bundle is **deleted before merge** (rule 29(c)).

---

## 0. Verdict (one paragraph)

**The mechanism is exactly what D53 says it is, now demonstrated over the full window rather than
one screen year — and the lane still does not recommend arming it, because two of its own
pre-registered gates fired.** Across **all five years** the arm's failing pool is the control's
**minus rows that are 100 % sector-1 and nothing else** (2022: 26 rows / 1,993.188 MW; 2023: 3 /
127.566; 2024: 6 / 3,158.006), the **arm-only set is EMPTY in every year**, every shared row's MW
is identical to the decimal, **zero** sector-1 rows reach any decision ledger in any year, and
**zero** arm-only decided or executed rows are unexplained (W1, W2, W3 — all PASS). The 2022
auction, on identical fleets, is **byte-identical** between the legs: 1,399 offers, 158,103.444 MW
offered, 23,331.628 price-takers, 90.411052 $/MW-day, position 1.042601, all 1,399 stack rows
identical. The window decided total falls **2,120.754 MW**, which is **exactly** the control's
sector-1 decided MW (1,993.188 + 127.566) — the cleanest candidate-set identity this lane could
have measured, and it landed on **9,394.156 MW, to the digit the point value ADDENDUM 3 wrote down
before the arm existed**. Composition holds: window `economic` release precision **RISES**
0.122 → 0.146 with every released row at a non-sector-1 plant, and LOYO loses no fold the control
holds. **But W4 FAILED** — 9,394.156 sits **below** the pre-registered band's lower edge
(10,511.510), because I derived that edge from the cap's *granularity* (±Σ`g_y` = 1,003.4 MW) when
the mechanism's own arithmetic bounds the downside by the *sector-1 decided MW it removes*
(2,120.754 MW); A3.3 even wrote the correct point value and then mis-stated it as "inside the
band". **And W5 FAILED** — 2021/2022 exact and 2023 fleet-delta hold to the digit, but in 2024 and
2025 the offers of 679 / 619 units present in *both* stacks differ, because the E&AS margin in the
net-ACR offer reads the prior year's prices and those diverge once the fleets do. Both firings are
diagnosed below as **defects in my own gate construction, not in the mechanism** — and **rule 29's
discipline is that a fired STOP gate is honored however right the diagnosis** (the D62/D78
precedent). Limb (a) purity is therefore FAIL, and §6's pre-stated rule returns **HOLD-and-route**.
`retire.total_gw` moving FAIL → PASS (18.058 → 15.937 GW against 15.062 actual) is reported at full
magnitude and is **explicitly not a criterion in either direction** (rule 14).

---

## 1. What was solved — and the mid-lane rebase that cost one control leg

| leg | code (HEAD guard) | recipe | key (declared → realized) | wall |
|---|---|---|---|---|
| control-P **(discarded)** | `41b46142` | bare `pjm-t1h` | `15a723ba3b6dc856` → match | 22.0 min |
| **control-P** | `cbf98979` | bare `pjm-t1h` | **`a9c66d8ea25acb9d`** → **match** | **19.1 min** |
| **repaired arm** | `99245361` | `--retirement-sector-gate` | **`bb6a60239d69508b`** → **match** | **21.2 min** |

All: `run_capacity_hindcast.py --iso PJM --start-year 2021 --end-year 2025 --vintage 2020
--fuel-variant realized --entry-screen-diagnostics`, through the committed
`docs/handoffs/d78/run_full.sh`. Solve years **{2021, 2023, 2024, 2025}**, **2022 bridged** and
never scored; the holdout freeze asserted ACTIVE on every leg; no out-of-training year solved,
scored or registered (rule 22). PJM solo, sequential, years sequential (rule 12). **HEAD guard held
on every leg.** `data/clean` was absent at session start and was rebuilt in full
(`regenerate_clean.py`, **56/56 datatypes, 0 failures, exit 0**) before any leg.

**The two graded legs share one solve-code state.** Their guard shas differ only by the ADDENDUM 3
docs commit: `git diff cbf98979 99245361 -- src/market_sim scripts/` is **empty**.

**The rebase (PRECOMMIT §1, STOP 9).** Main moved `acbb5350` → `c3988c73` (21 commits) while the
first control-P was solving. The re-audit (ADDENDUM 2, written **before** anything was re-solved)
found **three LIVE hunks**: **capx D67-ARM** (owner ruling Q52 — `capacity_adequacy_requirement_published_by_iso: {"PJM": True}` in `_pjm_config`, changing the adequacy-requirement operand and hence
the R-NEW admission-cap budget) and **capx D81** in `retirements.py` + `evolve.py` (the pending
dated plants and this-year retrofits move onto **`exit_exempt_unit_ids`** — this lane's own seam).
Everything else INERT: SCN-CAP's mass-cap schedule (`mass_cap_enabled` False), ruling S9's
comment-only carbon-knot relabel (this recipe runs `carbon_price 0.0`), D65-B-R's retrofit ledger
record (CCS inert below 2028), miso-225, CAISO inputs. So control-P was **re-solved on the rebased
HEAD before the arm ran**, and its first 22.0 min of LP was discarded, not graded. That was the
right call on the merits as well as the letter: D67-ARM changes the very budget W4 bands, and D81
lands on this lane's own seam — grading against a control that predated both would have recommended
arming a mechanism whose interaction with PJM's shipped posture had never been measured.

*(Main moved again, `c3988c73` → `23bbacd7`, as the arm was launched. Per §1 a rebase never happens
**during** a leg; that delta is unaudited by this lane and is stated as a limitation in §7.)*

---

## 2. W0′ — the drift from D78 is FULLY ATTRIBUTED to the two named LIVE hunks (ADDENDUM 2.3)

W0's known-answer form was **void at this HEAD by construction**, and A2.3 said so and replaced it
**before the re-solve**: every difference from D78's measured 2022 screen must be attributable to a
named A2.1 LIVE hunk, and an unattributable one is a STOP. The attribution closes **exactly**:

| 2022 quantity | D78 (at `9fcdf19c`) | **control-P (at `cbf98979`)** | attributed to |
|---|---:|---:|---|
| `census_mw` | 181,435.072 | **181,435.072** | — **identical** |
| `offered_mw` | 150,857.184 | **158,103.444** | **D81** (+7,246.260) |
| `price_takers_mw` | 30,577.888 | **23,331.628** | **D81** (−7,246.260) |
| `offered + price_takers` | 181,435.072 | **181,435.072** | **conserved to the MW** |
| `n_offers` | 1,370 | **1,399** | D81 (+29 dated units now offering) |
| `requirement_mw` | 146,816.46 | **163,268.9** | **D67-ARM** (the published operand) |
| failing pool | 677 / 29,727.898 | 129 / 10,686.443 | D67-ARM (the requirement sets the cap) |
| price $/MW-day | 67.760162 | 90.411052 | D67-ARM + D81 jointly |

**The offer-side drift conserves to the MW**: D81 moved **7,246.260 MW** out of the `Q_0`
price-taker residual and into the sell-offer stack, with the census unchanged — precisely D81's
stated mechanism (a pending dated plant must offer at its net-ACR cap instead of landing at $0).
The requirement move is D67-ARM's published operand, exactly as its `_pjm_config` comment records.
**No unattributable difference exists. W0′ PASS**, and the residual known-answer content W0 was
carrying is discharged.

---

## 3. The identities — W1, W2, W3, W5, arm vs control-P at one code state

### 3.1 W1 — the candidate identity, ALL FIVE YEARS (**PASS**)

| year | form | control-only rows / MW | sectors | arm-only | shared | shared MW identical | unexplained |
|---|---|---:|---|---:|---:|:--:|---:|
| 2021 | exact | 0 / 0 | — | **0** | 0 | ✓ | 0 |
| 2022 | exact | **26 / 1,993.188** | **sector 1 ×26 — nothing else** | **0** | 103 | ✓ | 0 |
| 2023 | fleet-delta | **3 / 127.566** | **sector 1 ×3** | **0** | 20 | ✓ | 0 |
| 2024 | fleet-delta | **6 / 3,158.006** | **sector 1 ×6** | **0** | 0 | ✓ | 0 |
| 2025 | fleet-delta | 0 / 0 | — | **0** | 0 | ✓ | 0 |

**Every control-only row, in every year, is sector-1. The arm-only set is EMPTY in every year.
Zero merchant rows change state anywhere in the window.** This is D78 G3 generalized from one
screen year to five, and it holds without exception.

### 3.2 W2 — the decided-cohort composition (**PASS**)

Zero sector-1 rows in `decided`, `entry_capped`, `floor_retained`, `throughput_deferred`, any
`pipeline_events` row, and `retirements` with `reason == "economic"` — **in all five years**. Zero
unknown-sector pipeline rows in all five years.

### 3.3 W3 — the decided-cohort provenance (**PASS**)

Zero arm-only decided rows and zero arm-only executed rows in every year, so there is nothing to
explain: **nothing entered the arm's candidate universe that was not in the control's.** (With the
cap not binding in 2022–2023 there is no capped pool to re-fill from — §4.)

### 3.4 W5 — purity (**FAIL**, on 2024–2025 only; 2021–2023 exact)

| year | form | footprint | clearing scalars | shared-stack offers / `A_g` | verdict |
|---|---|:--:|:--:|---|:--:|
| 2021 | exact | identical | identical | — | **PASS** |
| **2022** | exact | identical | **identical** | **all 1,399 rows identical** | **PASS** |
| 2023 | fleet-delta | identical | requirement identical; census/offers differ by the exit delta (+12 offers) | **offer diff 0, `A_g` diff 0, cleared-flag diff 0** | **PASS** |
| 2024 | fleet-delta | identical | requirement identical | **offer diff 679**, `A_g` diff 0, cleared-flag diff 5 | **FAIL** |
| 2025 | fleet-delta | identical | requirement identical | **offer diff 619**, `A_g` diff 0, cleared-flag diff 0 | **FAIL** |

**The 2022 identity is the strong one and it is exact**: on identical fleets the gate changes
nothing about the auction — 1,399 offers, 158,103.444 / 23,331.628 MW, 90.411052 $/MW-day, position
1.042601, requirement 163,268.9, and every one of the 1,399 stack rows identical in unit, fuel,
offer (≤1e-9), `A_g` (≤1e-6) and cleared flag. The D78 seam repair holds at the new HEAD.

**Why 2024–2025 fail, diagnosed rather than excused.** `A_g` is identical everywhere and no fuel
changes; what differs is the **offer value** of units present in both stacks. The net-ACR offer is
`max(0, going-forward cost − E&AS margin) / (A_g × 365)`, and the **E&AS margin reads the prior
year's prices** through `prior_results`. Once the arm retires less in 2022, the 2023 prices differ,
so the 2024 offers differ, and so on. That is a **second-order propagation of the fleet delta**,
one year removed, not a second seam — and it is unavoidable for *any* mechanism that changes *any*
exit. **My §3.1 pre-registration nonetheless said "every unit present in both years' stacks carries
an identical offer and `A_g`" with no carve-out for that propagation, so W5 fails as written.**
D78 only ever graded one year past the identical-fleet year, where it does hold exactly (2023 here:
offer diff 0), so this failure mode had never been reachable before.

---

## 4. W4 fired — and the band's lower edge is MY construction error

| quantity | control-P | **arm** | Δ |
|---|---:|---:|---:|
| window **decided** MW | 11,514.910 | **9,394.156** | **−2,120.754 (−18.42 %)** |
| control's sector-1 **decided** MW (2022 1,993.188 + 2023 127.566) | **2,120.754** | — | — |
| **W4 band (ADDENDUM 3.2, pre-registered)** | **[10,511.510 , 12,518.310]** | 9,394.156 | **BELOW the lower edge** |

**The arm's window decided total fell by EXACTLY the control's sector-1 decided MW, to the
milli-MW.** That is the strongest possible confirmation of a candidate-set partition: the removed
candidates simply do not retire, and **nothing re-fills**, because under D67-ARM's published
requirement the admission cap **no longer binds in 2022 or 2023** (`capped_mw` = 0 in both) — the
regime change ADDENDUM 3.3 recorded before the arm existed. The number even matches A3.3's
pre-declared point value **9,394.156 MW to the digit**.

**The gate fired anyway, and the fault is mine.** I built W4's bracket symmetrically as ±Σ`g_y`,
the *granularity of one whole-unit admission at the budget boundary* (Σ`g_y` = 1,003.400 MW, from
2024 alone). That granularity is the right bound on the **upside** — the re-fill's overshoot — but
the **downside** of a candidate-set gate is bounded by the **sector-1 decided MW it removes**
(2,120.754 MW), which is larger. A correct W4 would have read
`[Σdecided_ctl − Σ(sector-1 decided_ctl), Σdecided_ctl + Σg_y]` = **[9,394.156 , 12,518.310]**, and
the arm would have landed **exactly on its lower edge**. **A3.3 item 1 computed 9,394.156 and then
asserted it "sits inside A3.2's band near its lower edge" — that arithmetic claim was simply
wrong** (9,394.156 < 10,511.510), and it is corrected here at full magnitude rather than quietly.

**This is the mirror image of G6, and it is honored the same way.** G6 gated a quantity the
mechanism does not control; W4 gated the right quantity with a mis-derived edge. Rule 29's
discipline does not distinguish: **a fired pre-registered STOP is honored, and a lane does not
promote past its own pre-registration however right the diagnosis** (D78 §0, the D62 precedent).
The corrected bracket is offered to the director as the successor's pre-registration, **not** as a
re-read of this one.

---

## 5. Reported at full magnitude, never gated (PRECOMMIT §3.2, rule 14)

| quantity | control-P | **arm** | note |
|---|---:|---:|---|
| **FC-3 `retire.total_gw`** (actual 15.062) | 18.058 · err 0.199 · **FAIL** | **15.937 · err 0.058 · PASS** | **NOT a criterion in either direction** |
| `unit_recall_gt300` | 0.650 (13/20) · FAIL | **0.550 (11/20)** · FAIL | falls, as §4 item 6 pre-declared (a matched large sector-1 exit is no longer reachable) |
| `plant_recall_frac` | 0.700 (14) | 0.700 (14) | unmoved |
| `false_retire` | 8.065 GW · 0.447 · FAIL | 7.166 GW · 0.450 · FAIL | |
| window `economic` release **precision** | 0.122 | **0.146** | **RISES** — limb (c) |
| window `all` release precision | 0.421 | 0.476 | |
| window **executed** economic MW | 11,514.910 | **9,394.156** | −2,120.754 |
| executed 2022 / 2023 / 2024 | 9,464.455 / 828.467 / 1,221.988 | 8,693.255 / 700.901 / **0** | per-year, REPORTED not gated |
| window retirements, all channels | 17,034.468 | 14,913.714 | |

**The rule-14 line, restated after the fact exactly as it was stated before.** `retire.total_gw`
crossing from FAIL to PASS is a **consequence** of removing candidates from a control that
over-retires (D58 PREDECL §3 P5 established that PJM's control over-retires), reported because it
moved; it is **not evidence for the mechanism**, it is not a criterion, and a worse band would not
have been evidence against it. Recall falling is reported the same way.

---

## 6. The flip condition, graded (PRECOMMIT §6)

| limb | condition | reading |
|---|---|---|
| **(a) purity** | W5 holds on the full window | **FAIL** — 2021–2023 exact/fleet-delta PASS; 2024–2025 shared-stack offers differ through the E&AS margin (§3.4) |
| **(b) fidelity** | W1 + W2 + W3 | **MET** — the pool falls by exactly the sector-1 rows in every year, zero sector-1 rows in any decision ledger, zero unexplained rows |
| **(c) composition** | window `economic` precision ≥ control's, every row non-sector-1 | **MET** — 0.122 → **0.146**, and W2 gives every row non-sector-1 |
| **(d) LOYO** | no fold lost that the control holds | **MET** — folds computed on both legs (`--flip-gate-extras`); control holds **no** recall-PASS fold (2023/24/25 all FAIL) and the arm holds none either, so none is lost; `tr10a`/`tr10b` PASS on all three folds in both legs. **Non-discriminating on recall, and said so.** |

**§6's pre-stated rule:** *"Recommend HOLD-and-route if (a) fails."*

# **RECOMMENDATION: HOLD-and-route.** NOT ARM.

Held on limb (a) and on the fired W4 — **not** on the mechanism, whose fidelity (b), composition
(c) and LOYO (d) limbs are all MET and whose partition identity is exact in all five years. What
must be resolved before an arming recommendation is possible:

1. **Restate W5's fleet-delta form to admit the E&AS propagation** — a successor pre-registers
   "shared-stack `A_g`, fuel and cleared-flag identical; offers identical in the first divergent
   year, and thereafter differing **only** through the prior year's price vector" — with the
   propagation *tested* (e.g. that the offer delta is zero for units whose E&AS operand is zero)
   rather than assumed. This lane measured `A_g` diff 0 and fuel diff 0 everywhere, which is the
   part that would signal a real second seam; the offer channel needs its own identity.
2. **Restate W4's lower edge** as `Σdecided_ctl − Σ(sector-1 decided_ctl)` (§4). On this lane's own
   measurement the arm lands exactly on it.
3. **Re-solve on a HEAD that includes D81 and D67-ARM and is not itself superseded** — both landed
   *during* this lane, and main moved once more as the arm launched (§7).

---

## 7. Governance attestation, limitations, retention

**Rule 1 `[R-STRUCT]`:** the mechanism is PJM's must-offer rule and an ownership attribute; every
gate graded is an identity or a control-derived bracket, none a residual; the two firing gates are
honored on structure, and the one metric that improved (`retire.total_gw`) is explicitly excluded
from the determination. **Rule 12:** PJM solo, legs sequential, years sequential. **Rules 13/14:**
the sign line was stated before the solve on a quantity the mechanism controls; every number is
reported at full magnitude, misses and my own arithmetic error included. **Rule 19:** no mechanism
stacked; the D78 seam is used as merged. **Rule 21:** zero DOF — this lane wrote no code and set no
parameter. **Rule 22:** forecast-mode hindcast; solve years {2021, 2023, 2024, 2025}, 2022 bridged;
freeze asserted active on every leg; nothing outside training solved, scored or registered.
**Rules 24/25:** no tunable added or changed; PJM's cell only, on PJM's own evidence; MISO's `K`
untouched. **Rule 27:** no `src/` file touched; docs and the instrument edited locally and pushed as
exact on-disk bytes. **Rule 28(b):** PJM's shard only; no new row (no field). **Rule 29:** G-DRIFT
before any LP and re-audited before the re-solve; the pre-declaration and both band addenda pushed
before the solves they govern; STOP-only structural gates; a fired gate is honored; the control
bundle deleted before merge.

**Stated limitations.**
1. **Main moved again during the arm** (`c3988c73` → `23bbacd7`). §1 forbids rebasing *during* a
   leg, so that delta is **unaudited by this lane**. The A/B remains internally valid — both legs
   at one solve-code state — but the recommendation is stated **as of `c3988c73`**.
2. **W0's known-answer form was void** at this HEAD and was restated as W0′ before the re-solve
   (§2). The restatement was pre-registered, not retrofitted.
3. **Limb (d) is non-discriminating on recall** — the control holds no recall-PASS fold, so "loses
   no fold" is satisfied trivially on that leg; `tr10a`/`tr10b` do discriminate and pass in both.
4. **RSS not captured** (`/usr/bin/time` absent on this box), as in D78; wall is inside the D57
   envelope on every solve year.
5. **An instrument key repair** (`price` → `price_usd_per_mw_day` / `cleared_position`) was found
   and fixed **before** the arm was solved and is disclosed in ADDENDUM 1.4; no gate, threshold or
   pass condition was changed by it. A second repair — an absent LOYO block reading as a vacuous
   pass — was fixed after the grade and is disclosed in §6(d); it did not change the verdict
   (limb (a) already failed), and the folds were then genuinely computed.

**Retention (rule 29(c)).** `results/hindcast/pjm-2021-2025-realized-t1h-d78-control-P` is
**deleted before merge**; the arm keeps only its slim registered files
(`meta.json`, `run_config.json`, `forecast_verdict.json`) exactly as every registered PJM T1-H run
does. Every number this lane will ever cite is in this document, the PRECOMMIT with its three
addenda, and `docs/handoffs/d78r/{window_compare,control_band}.json`.

**Board lock.** D65-B-R landed on main (`26504ab6`) during this lane. This lane nonetheless commits
**only** the registry sidecar and its `VERDICT_MAP` entry and **holds the `ff-verdicts.json` /
`program-status.json` snapshot row**, as PRECOMMIT §8 said it would either way — the board is not
this lane's to write.

---

## 8. Matrix (rule 28) and registration

- PJM's `retirement_sector_gate` cell stays **`O`** (open) with this finding's evidence — the
  partition is proven exact over the full window, and the lane's own gates refuse promotion.
  `docs/codebase-site/data/mechanism-matrix/PJM.js` only; no other shard, no new row.
- The arm registers SUFFIXED: `pjm-2021-2025-realized-t1h-d78-sectorgate` → **`pjm-t1h-d78r-sectorgate`**.

## 9. Reproduction

```
uv run python docs/handoffs/d78/keys_probe.py
bash docs/handoffs/d78/run_full.sh control-P
bash docs/handoffs/d78/run_full.sh arm --retirement-sector-gate
uv run python scripts/score_capacity_hindcast.py --bundle <dir>
uv run python scripts/score_capacity_hindcast.py --bundle <dir> --flip-gate-extras
uv run python docs/handoffs/d78r/window_compare.py --ctl <ctl> --arm <arm>
```
