# ADDENDUM 1 — capx D78-R2: the W4′ band and the control's pre-arm bars

**Pushed after control-P solved and BEFORE the arm is launched** (PRECOMMIT §4,
D74 §9 item 3's procedure). Every number here is read off the control leg alone.
The band's *definition* was fixed in the PRECOMMIT and is not re-derived; only its
two numeric edges are filled in.

## 1. The leg

| | |
|---|---|
| bundle | `results/hindcast/pjm-2021-2025-realized-t1h-d78r2-control-P` |
| key declared → realized | `a9c66d8ea25acb9d` → **match** |
| HEAD guard | `65e12b21…` held across the leg |
| solved / bridged | solved **{2021, 2023, 2024, 2025}**, **2022 bridged** |
| wall | 19:20:30 → 19:41:33 UTC ≈ **21.1 min** |
| `data/clean` | rebuilt in full before the leg: **56/56 datatypes, 0 failures**, 60 dirs |

## 2. The W4′ band — PRE-REGISTERED, computed on the control alone

| quantity | MW |
|---|---:|
| `Σ_y decided_mw(control)` | **11,514.910** |
| `Σ_y sector1_decided_mw(control)` (2022 1,993.188 + 2023 127.566) | **2,120.754** |
| `Σ_y g_y` (2024 alone; the cap binds only there, `capped_mw` 3,158.006) | **1,003.400** |
| **band lower edge = POINT VALUE (exact partition)** | **9,394.156** |
| **band upper edge** | **12,518.310** |

`[9,394.156 , 12,518.310]`. The lower edge is the exact-partition prediction: an
arm that removes exactly the sector-1 candidates and re-fills nothing lands **on**
it. **The arm will be reported by its distance from that point value, not merely
by band membership.**

The admission cap binds in **2024 only** (`capped_mw` = 0 in 2021/2022/2023/2025),
so there is no capped pool to re-fill from in the two years that carry the
sector-1 decided MW — the D67-ARM regime D78-R recorded, reproduced here
independently.

For reference, D78-R's symmetric bracket was `[10,511.510 , 12,518.310]`; its
lower edge is the construction error its §4 records, and it is superseded, not
re-read.

## 3. The control's PRE-ARM bars for flip-condition limbs (c) and (d)

Read before the arm is scored, exactly as PRECOMMIT §7 requires.

| limb | control's bar |
|---|---|
| **(c) composition** | window `economic` release precision **0.122** (11,514.910 MW released, 1,400.330 at real exit plants). The arm must not fall below it. (`all` precision 0.421 for context.) |
| **(d) LOYO** | folds computed (`--flip-gate-extras`). Recall band **FAIL on all three folds** (−2023 8/12, −2024 11/19, −2025 13/19), so the control holds **no recall-PASS fold** and limb (d) is **non-discriminating on recall** — stated now, before the arm, not after. `tr10a`/`tr10b` **PASS on all three folds** and do discriminate. BLK-10 fired 0.0 GW. |

## 4. Reported, never gated (rule 14) — the control's side of the sign line

| quantity | control |
|---|---|
| `retire.total_gw` | 18.058 vs actual 15.062 · err 0.199 · **FAIL** |
| `unit_recall_gt300` | 0.650 (13/20) · **FAIL**; `plant_recall_frac` 0.700 (14) |
| `false_retire` | 8.065 GW · 0.447 of model · **FAIL** |

## 5. An unplanned cross-check that strengthens ADDENDUM A

This control was solved at `b22b91c3`; D78-R's control-P was solved at `cbf98979`,
before main's D67-ARM / D81 / D74 / D75-R / D79. **Every aggregate above matches
D78-R §4–§5 to the digit**: window decided 11,514.910, sector-1 decided 2,120.754,
`Σg_y` 1,003.400, `total_gw` 18.058 / err 0.199, recall 0.650 (13/20),
`plant_recall_frac` 0.700, `false_retire` 8.065 GW / 0.447, `economic` precision
0.122, `all` precision 0.421.

That is an **empirical confirmation of ADDENDUM A's all-INERT verdict**, obtained
from a different direction than the code audit and the key probe: the recipe's
whole measured surface is unmoved across 45 commits of `main`. It is recorded as a
cross-check, and it is **not** used as a control — both graded legs are this lane's
own, at one HEAD, per the PRECOMMIT.
