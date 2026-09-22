# PRECOMMIT — hydro-5: hydro dispatch physics, SPP + NEISO + MISO (2026-09-22)

**Lane:** hydro-5 · **ISOs:** SPP, NEISO, MISO · **Mode:** backcast · **LP spent before this doc:** zero.

Successor to `docs/RESULT-hydro-1-2026-09-22.md` §D (the cross-ISO census). Every number below
is measured with no solve — `scripts/probes/_hydro5_phase0.py`, output committed as
`results/calibration/_hydro5_phase0.json` — from each keeper's own committed `hourly/` sidecars,
EIA-930 `NG: WAT`, EIA-923/860 and the committed ORNL-EHA / HILARRI sources. Shards launch
**after** this doc is pushed and its SHA pinned (rule 32(c)(1)).

| ISO | control keeper (rule 29(b) form 4) | bundle(s) | years |
|---|---|---|---|
| SPP | `2026-09-22-spp-71-ensemble-syncfloor` (+ rung stamped to it) | `spp71_ensemble_rung`, `spp71_ensemble_span` | 2019–2025 (7) |
| NEISO | `2026-09-19-neiso112-mer-year-isolated` | `neiso112_mer_span` | 2020–2025 (6) |
| MISO | `2026-09-20-miso-264-anchor-vintage` | `miso264_anchor_span` | 2020–2025 (6) |

All three keepers were solved year-isolated (rule 36), so a per-year arm is like-for-like. **SPP's
keeper changed during this lane's phase 0** (SPP-71 promoted keeper 15 at `107be503`, same hydro
posture — every `hydro_*` field off); every SPP number here is re-measured on the new keeper.

---

## 1. The defect, measured on the keepers (zero LP)

`h<1 MW` = hours the P1 hydro class sits below 1 MW. `top-dec` = share of each month's hydro
energy in that month's top-10 % load hours (flat fleet = 0.10). `daily CV` = mean over months of
SD(daily energy) ÷ mean(daily energy) — the within-month banking statistic. Measured columns are
EIA-930 `NG: WAT`; **in parentheses where that series folds pumped storage** and is therefore
not a like-for-like reference for a conventional-only class.

| ISO-year | keeper TWh | h<1 MW | p05 | p50 | p95 | top-dec | daily CV | meas. p05 | meas. top-dec | meas. daily CV |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| SPP 2019 | 15.323 | 1,191 | 0 | 2044 | 3103 | 0.149 | 0.457 | 681 | 0.112 | 0.078 |
| SPP 2020 | 11.612 | 2,126 | 0 | 854 | 3102 | 0.172 | 0.524 | 493 | 0.130 | 0.071 |
| SPP 2021 | 9.778 | 2,873 | 0 | 478 | 3102 | 0.160 | 0.683 | 412 | 0.132 | 0.093 |
| SPP 2022 | 8.207 | **3,209** | 0 | 452 | 3102 | **0.212** | **0.718** | 302 | 0.132 | 0.099 |
| SPP 2023 | 8.344 | 2,682 | 0 | 452 | 2965 | 0.171 | 0.682 | 304 | 0.129 | 0.096 |
| SPP 2024 | 8.967 | 2,014 | 0 | 492 | 2956 | 0.171 | 0.671 | 281 | 0.123 | 0.160 |
| SPP 2025 | 8.818 | 2,221 | 0 | 492 | 2969 | 0.153 | 0.707 | 293 | 0.130 | 0.114 |
| NEISO 2020 | 6.582 | 1,882 | 0 | 707 | 1883 | **0.303** | 0.757 | (208) | (0.162) | (0.168) |
| NEISO 2021 | 6.225 | 1,293 | 0 | 438 | 1908 | 0.252 | 0.742 | (290) | (0.163) | (0.186) |
| NEISO 2022 | 6.478 | 1,766 | 0 | 587 | 1877 | 0.262 | 0.833 | (293) | (0.174) | (0.173) |
| NEISO 2023 | 8.517 | 0 | 58 | 1009 | 1836 | 0.165 | 0.484 | (554) | (0.157) | (0.127) |
| NEISO 2024 | 6.673 | 451 | 0 | 671 | 1803 | 0.210 | 0.645 | (253) | (0.167) | (0.158) |
| NEISO 2025 | 5.106 | **1,908** | 0 | 254 | 1790 | 0.288 | **0.866** | 187 | 0.120 | 0.167 |
| MISO 2020 | 11.120 | 62 | 60 | 1236 | 2378 | 0.175 | 0.413 | (695) | (0.151) | (0.112) |
| MISO 2021 | 10.139 | 480 | 0 | 1044 | 2420 | 0.194 | 0.517 | (540) | (0.159) | (0.144) |
| MISO 2022 | 9.244 | **565** | 0 | 891 | 2411 | 0.191 | 0.530 | (483) | (0.171) | (0.167) |
| MISO 2023 | 8.775 | 295 | 5 | 813 | 2369 | 0.200 | 0.492 | (425) | (0.163) | (0.139) |
| MISO 2024 | 9.029 | 188 | 4 | 902 | 2332 | 0.197 | 0.525 | (371) | (0.164) | (0.142) |
| MISO 2025 | 9.064 | 252 | 4 | 905 | 2322 | 0.197 | 0.534 | (481) | (0.153) | (0.120) |

Two readings. **SPP is the worst case on banking**: its p95 sits at the whole fleet's nameplate
(3,102–3,103 of 3,103.5 MW in 2019–2022; within 4 % of 3,078 MW after) — bang-bang — and its daily CV is 5–10× the measured fleet's, whose day-to-day energy is
nearly constant (Corps Missouri-mainstem release schedules). **NEISO and MISO bank less but still
park at zero** — and the folded references cannot score them below the p05 level, so for those
two the admissible evidence is the model's own zero-hours and the physics of the RoR class.

---

## 2. Rule 25 — the classifier review, on each BA's own labelled subset

`scripts/data/curate_hydro_plant_modes.py --iso SPP NEISO MISO`, printed validation line and the
confusion matrix behind it (completion rules 2–5 applied to plants that DO carry an EHA label):

| BA | validation line | label RoR → completion shapeable | label shapeable → completion RoR | completion-"RoR" precision (MW) |
|---|---|---:|---:|---:|
| SPP (SWPP) | 12/16 plants, **92.3 %** of labelled MW | 214.9 MW / 3 | 8.4 MW / 1 | 89.6 % |
| NEISO (ISNE) | 77/125 plants, **66.1 %** | 317.9 MW / 37 | 68.0 MW / 11 | 81.8 % |
| MISO | 65/135 plants, **62.5 %** | 586.3 MW / 62 | 54.5 MW / 8 | 84.3 % |

**Verdict: admitted, and the reason is the direction of the error, not the aggregate.** NEISO and
MISO score below CAISO's 84 % because the completion calls many small labelled-RoR plants
*shapeable* (an inventoried reservoir behind a diversion or navigation dam). That error is
one-sided and **conservative** — the flat treatment is *under*-applied. The opposite error, the one
that would force a real peaker flat, is 54.5–68.0 MW per ISO. Most of each RoR class is decided by
the EHA label itself, not the completion (2023 budget shares of the RoR class: SPP 1.05 of 1.18 TWh,
NEISO 3.18 of 4.11, MISO 3.28 of 5.20).

Spot-check of the largest completion-decided plants against their hydrology, which is what the
label would say: MISO Keokuk (Mississippi L&D 19), Dam 2 and Whillock (Arkansas River navigation
dams), Edison Sault and St Marys Falls (St Marys River) → RoR, correct; Toledo Bend, Blakely
Mountain → shapeable, correct. NEISO Hadley Falls, Charles E Monty, Smith → RoR, correct;
Comerford, S C Moore (Fifteen Mile Falls storage) → shapeable, correct. SPP Ellis (Arkansas River)
→ RoR, Keystone → shapeable, correct. One visible miss, in the conservative direction: MISO
Smithland (Ohio River L&D, 75.9 MW) → shapeable.

**The Corps rule (rule 3) does not transfer, and correctly so.** Its pattern `CESP|USACE|Corps`
fires only on Sacramento-District dams. SPP/MISO's Corps plants (Keystone, Blakely Mountain,
Degray, the Missouri mainstem) are SWPA/WAPA-marketed **peaking** projects, so leaving them to the
EHA label is right; widening the pattern would force real peakers flat. Nothing is changed.

**Falsification test (nyiso-111's) where the measured series is clean.** A fleet cannot swing
more than its shapeable MW, and the RoR class alone can never deliver less than its flat base:

| | shapeable MW | measured mean-diurnal swing | RoR flat base vs measured monthly p01 |
|---|---:|---:|---|
| SPP 2019–2025 | 2,758–2,785 | 559–969 MW | base ≤ p01 in all 84 months (p01 ≥ 1.60 × base) |
| NEISO 2025 | 1,118 | 221 MW (p95 daily range 456) | base ≤ p01 in 11/12 months; **June: base 384 MW vs p01 360 MW** |

NEISO June 2025 is a small, real tension — the measured fleet dipped 24 MW (6 %) below what the
RoR class alone would produce in 1 % of June hours — and is recorded as such: some New England
"RoR" plants carry daily pondage. It is one month of one clean year and does not reverse the
review. **MISO has no clean hourly series** (`EIA930_PS_FOLDED_INTO_WAT`), so neither test can be
run there; the review rests on the labelled-subset confusion above.

`DEFAULT_ISOS` gains SPP, NEISO and MISO **in this commit**, with the review recorded at the
constant. The partitions' content hashes (sha256 of the sorted `plant_id,shapeable` CSV, 16 hex)
are pinned for the shards: SPP `f7fc0b2a2beb0411`, NEISO `02c3f7710de08661`,
MISO `dc2a9d4be30a0727`.

---

## 3. Which lever, per ISO — not a free choice

| ISO | arm | why |
|---|---|---|
| SPP | **F** `hydro_min_flow_floor` | `NG: WAT` admissible (below) |
| SPP | **R** `hydro_ror_split` | classifier reviewed (§2) |
| NEISO | **R** `hydro_ror_split` | year-invariant; the floor would read PS-folded `NG: WAT` in 2020–2024 |
| MISO | **R** `hydro_ror_split` | `NG: WAT` folds PS every year; floor and envelope barred (rule 14) |

**SPP arms F and R are separate arms, never stacked** (rule 19). Not tested: NEISO floor on 2025
alone (a config that is live in one year of six is not a keeper posture this lane can recommend),
`hydro_dispatch_envelope` anywhere, and `hydro_pondage_bound` anywhere (refuted in NYISO,
`RESULT-hydro-1` §C).

**SPP `NG: WAT` admissibility, measured rather than assumed.** SPP was not among the BAs the
`EIA930_PS_FOLDED_INTO_WAT` citation screened, and SWPP files **no** `NG: PS` column while
operating Salina (GRDA, EIA 2982, 259.2 MW PS, endogenous storage in the model). The constant's
three signatures (`scripts/probes/_miso109_hydro_level_audit.py --iso SPP`): (a) no `NG: PS` —
**present**; (b) `NG: WAT` above the 3,103.5 MW conventional nameplate — **0 hours in every year
2019–2025** (max 2,061–2,776 MW); (c) negative hours — **0**. 930 − 923 `HY` gap +4.6 / +2.5 /
+1.4 / +0.3 / **−0.7** / +3.1 % (2019–2024), with 2023 within ±40 GWh in every month. A fold
cannot be excluded outright, so its reach is bounded instead: Salina's gross discharge is at most
259 MW, and a daily-cycling pumped-storage unit discharges at peaks and pumps in the fleet's
lowest hours — the hours the floor's **Q95 level** reads. The floor's level is therefore the
admissible measured object even if a small fold exists. Disclosed, not assumed away.

---

## 4. What each arm does, predicted before any solve

| ISO-year | RoR plants | RoR MW | RoR share of energy | RoR flat base MW (month min–max) | F level MW | F forced share of budget |
|---|---:|---:|---:|---:|---:|---:|
| SPP 2019 | 8 | 320 | 0.094 | 73–222 | 406–1986 | 0.706 |
| SPP 2020 | 8 | 320 | 0.121 | 98–188 | 310–1019 | 0.516 |
| SPP 2021 | 8 | 320 | 0.129 | 82–187 | 212–589 | 0.418 |
| SPP 2022 | 8 | 320 | 0.134 | 84–162 | 189–580 | 0.387 |
| SPP 2023 | 8 | 320 | 0.141 | 92–178 | 169–808 | 0.477 |
| SPP 2024 | 8 | 320 | 0.140 | 97–191 | 211–866 | 0.461 |
| SPP 2025 | 8 | 320 | 0.141 | 107–214 | 235–662 | 0.394 |
| NEISO 2020 | 113 | 795 | 0.492 | 78–619 | — | — |
| NEISO 2021 | 112 | 793 | 0.518 | 188–548 | — | — |
| NEISO 2022 | 112 | 793 | 0.497 | 123–668 | — | — |
| NEISO 2023 | 112 | 793 | 0.479 | 373–561 | — | — |
| NEISO 2024 | 109 | 782 | 0.473 | 146–540 | — | — |
| NEISO 2025 | 109 | 782 | 0.474 | 92–516 | — | — |
| MISO 2020 | 100 | 1,246 | 0.553 | 597–859 | — | — |
| MISO 2021 | 100 | 1,247 | 0.575 | 523–813 | — | — |
| MISO 2022 | 101 | 1,253 | 0.590 | 438–781 | — | — |
| MISO 2023 | 100 | 1,251 | 0.592 | 343–784 | — | — |
| MISO 2024 | 98 | 1,239 | 0.592 | 328–772 | — | — |
| MISO 2025 | 98 | 1,239 | 0.588 | 331–766 | — | — |

**The SPP asymmetry, stated now.** SPP's RoR class is 320 MW and 9–14 % of the energy; its bulk
is the Missouri-mainstem and SWPA reservoir fleet, which EHA labels `Peaking`. Arm R can end the
zero-hours (its base never falls below 73 MW) but **cannot reach the mainstem banking** that
drives SPP's daily CV. Arm F forces 39–71 % of each year's water as a month-constant base and is
the arm that reaches it. **If both pass G1–G3, SPP's recommendation is F**, on that coverage
argument, decided here and not by the scored criteria.

**G2 — the nameplate clip is not a G2 mechanism, and the probe proves it.** The RoR loader clips a
flat level above nameplate, and logs it (NEISO 7–54 plant-months, MISO 4–50). But the budget row
is `≤` and the control's hourly cap is the same nameplate, so that energy is **undeliverable in
the control too**. Decomposing each keeper's own shortfall against its budget: it is entirely
this infeasible excess everywhere except **MISO 2020** (0.136 TWh = **1.22 %** of the keeper of
*economic* spill — water the control could turbine and did not) and SPP 2025 / 2021 / 2019
(0.061 / 0.011 / 0.009 %). So the
prediction is a move inside the 0.1 % bar in 18 of 19 ISO-years, and a possible **upward** move up to ~1.2 % in MISO
2020 if the spilled water is RoR-class water the arm now turbines. *(This also bears on
`RESULT-hydro-1` §2's attribution of NYISO 2022's −0.12 % to the clip — the clip cannot remove
energy the control delivers. NYISO arms the dispatch envelope, which is a more likely route. Not
this lane's ISO; noted for the NYISO G2 lane.)*

---

## 5. Gates, declared before the solves

Decided on structure (rule 1). A failing gate does not by itself kill an arm and a passing one
does not by itself promote it. **If the faithful representation makes the fit worse, it stays.**

**G1 — LIVENESS.** R: the loader logs `RoR split — N/M plants flat` with N equal to §4's count
and the arm's hourly hydro never below §4's monthly flat base minus 1 MW. F: the loader logs
`hydro min-flow floor on N units` with a level range equal to §4's, and the arm's hourly hydro
never below the month's floor level minus 1 MW. *An inert arm is reported inert, not refuted.*

**G2 — THE INVARIANT.** |Δ annual hydro TWh| < 0.1 % of the keeper, and no month moves by more
than 0.1 % of that month's keeper energy. The **one pre-declared exception** is an *upward* MISO
2020 move no larger than its 1.22 % economic-spill bound (§4). A downward breach anywhere, or any
breach outside that exception, is a defect in the code path, not a finding.

**G3 — THE TARGETED STATISTICS MOVE THE RIGHT WAY, IN EVERY YEAR.** Hours below 1 MW → **0**
(predicted exactly 0 for every arm: every base/level is ≥ 73 MW). Top-decile share falls toward
0.10 — and toward the measured value where admissible (SPP 0.112–0.132; NEISO 2025 0.120). Daily
CV falls toward the measured (SPP 0.07–0.16; NEISO 2025 0.167). Reported per year, arm vs keeper
vs measured.

**G4 — NO SILENT BREAKAGE.** C1, C2, C3a, C3b re-scored on every year against the keeper with
`scripts/screen_collateral_gate.py` (same scorer, committed bench held fixed), C3c/C4/C8 reported.
Every move reported at full magnitude. A PASS→FAIL flip is **reported, not a kill** (rule 1), and
opens a root-cause question if it happens.

**Promotion.** This lane **recommends**; the owner rules (rule 31). A recommendation needs G1, G2
and G3 in every year of the ISO's span; G4 is reported beside it. Nothing is deleted before the
owner rules.

---

## 6. Control and G-DRIFT (rule 29(b))

*(Filled below before any shard launches — see §6.1.)*

---

## 7. Shard plan — one shard per (arm, year), rule 36; every shard pushes its full bundle, rule 34(a)

| arm | ISO | years | shards | out-dir / branch stem |
|---|---|---|---:|---|
| F `hydro_min_flow_floor` | SPP | 2019–2025 | 7 | `hydro5_spp_floor_<Y>` / `claude/hydro5-spp-floor-<Y>` |
| R `hydro_ror_split` | SPP | 2019–2025 | 7 | `hydro5_spp_ror_<Y>` / `claude/hydro5-spp-ror-<Y>` |
| R `hydro_ror_split` | NEISO | 2020–2025 | 6 | `hydro5_neiso_ror_<Y>` / `claude/hydro5-neiso-ror-<Y>` |
| R `hydro_ror_split` | MISO | 2020–2025 | 6 | `hydro5_miso_ror_<Y>` / `claude/hydro5-miso-ror-<Y>` |

**26 shards. No year deliberately omitted** — each ISO's registered year set is exactly its
keeper's (plus, for SPP, the 2019–2022 rung stamped to it).

Each shard runs, after `curate_hydro_plant_modes.py --iso <ISO>` for an R arm:

```
python scripts/replay_keeper.py results/calibration/<keeper bundle> --years <Y> \
  --set <flag>=true --out-dir results/calibration/<out-dir> \
  --note "hydro-5: <flag> on the <ISO> keeper, <Y> (rule 36 single-year)"
```

then `scripts/probes/_hydro5_shard_check.py`, which **must pass** before a push: the arm's recorded
`scenario_config` differs from the keeper's by exactly `<flag>: false → true` (fields added since
the keeper allowed only at their default), and an R arm's classifier hash equals §2's.

Retrievability (rule 34(e)): each shard commits its bundle **including `dispatch/<Y>_P1.parquet`**
and the `results/calibration/_shared/<ISO>/` captures its `meta.json` references, to its own
branch, by `.gitignore` negation and plain `git add`. The parent fetches, verifies
(`git ls-tree` > 0 files), composes per ISO-arm, and lands anything that must survive on `main`
before this lane's PR merges (rule 33(f)).
