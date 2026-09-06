# ADDENDUM — pjm-166 independently corroborated, and two hypotheses foreclosed

Session: BC-TOUCHPOINT-2022-PJM, 2026-09-06 (branch `claude/bc-touchpoint-2022-iso-vp92q8`).
Parent: `results/calibration/FINDING-pjm166-c1-object-phase0-2026-09-06.md` (landed, `ac7ceab0`).
Keeper `2026-08-15-pjm-162-inputclock`; touchpoint `2026-09-05-pjm-2022-2021-touchpoints`.

**No solve, no config change, no mechanism armed. Nothing tuned to 2021 or 2022.**

This lane opened to run rule 22's touchpoint loop for PJM and found step 2 already complete:
pjm-166 landed the same day. This addendum records only what that finding does not already
carry. **It opens no lever and re-opens no cell.**

## 1. Independent corroboration (arrived at before reading pjm-166)

Working from the committed sidecars alone, this session reached pjm-166 §0's object by a
different route — a share-basis decomposition of C1 rather than an additive fossil-surplus one —
and reproduced its net-cleared-virtual series **exactly**: `+7.40 / +6.48 / −0.89` in-sample,
`−6.14 / −9.91` held out. It also independently reproduced the layer's rule-13 anchor by clearing
the measured 2023 `hrl_da_incs_decs` curve at PJM's actual hourly DA prices over all 8,707
covered hours: **−0.52 TWh** net demand, against pjm-158's −0.755 and pjm-105's −0.68.

Two sessions on independent paths, plus a third reproduction of the anchor, land on the same
object and the same magnitudes. That is corroboration for the owner-escalated architecture
question (pjm-158 → pjm-166 §7.2), and it is **not** a second vote to pull the lever: the cell
stays `K`, adjudicated, inside the closed price-formation frontier.

## 2. Two hypotheses foreclosed, so they are not re-tried

**(a) The 2020 demand-feed defect does NOT extend to 2021/2022.** pjm-166 rules out demand on
*level* (±2.2 TWh). The natural follow-on worry is *shape*, since `ASSESSMENT-neiso-pjm-
validation-touchpoints-2026-09-05.md` §3.2 measured PJM 2020's feed as defective on shape — a
181,841 MW peak above PJM's all-time 165.5 GW record, at 11:00. From the committed
`system_<y>.parquet`:

| year | annual TWh | peak MW | peak timestamp |
|---|---|---|---|
| 2021 | 796.2 | 149,590 | 08-24 16h |
| 2022 | 810.2 | 148,528 | 07-20 16h |
| 2023 | 784.8 | 147,605 | 07-27 16h |
| 2024 | 812.7 | 153,121 | 07-15 16h |
| 2025 | 843.2 | 160,560 | 06-23 16h |

Summer-afternoon peaks, plausible magnitudes, below the record, same shape as the training
years, matching PJM's published peaks. The 2020 blocker is 2020's alone.

**(b) The touchpoint did NOT run on partial virtual-bid data.** The corpus README's default
regeneration range is `2023-2025` — exactly the training window — so thin 2021/2022 coverage is
a reasonable suspicion. It is foreclosed at the code: `virtual_bids.py:223-232` enumerates the
year's twelve monthly parquets and raises `FileNotFoundError` naming the missing months. The
touchpoint solved, so all twelve months existed for both held-out years. Coverage is complete
and the sign flip is genuine endogenous clearing, not a data gap.

## 3. Operational note — the corpus recovery route is verified live

`data/raw/pjm-da-virtuals/` is gitignored (DataMiner2 redistribution restriction) and its payload
was stripped by the 2026-08-16 history rewrite, which CLAUDE.md flags as having killed some
corpora's pin-based recovery. Its README's documented re-fetch route was exercised in full this
session — `python3 scripts/data/fetch_pjm_da_virtuals.py --years 2023 --feeds hrl_da_incs_decs`
returned all twelve 2023 months cleanly. For this corpus the stated recovery is **working as of
2026-09-06**. Nothing fetched is committed.

## 4. Loop status and duties

* **PJM touchpoint loop: step 2 complete, step 3 BLOCKED** on the owner ruling for the escalated
  architecture question (the LP carries one price series gated as RT, while the virtual curve
  needs a DA price). No step-3 work is available to a calibration lane until that returns, so
  this session correctly solved nothing.
* **Rule 30(a) fold** — already correct: the touchpoint's `holdout.keeper` is
  `2026-08-15-pjm-162-inputclock`, the current designated keeper. Not dangling, no re-stamp owed.
* **Rule 30(b) status ladder** — already present and per-year in `status/PJM.js`. Not rebuilt.
* **Rule 30(c)** — the two NOT-YET rungs do **not** downgrade PJM. Its determination is the
  train-tier verdict, `CALIBRATED`, untouched.
* **Rule 28** — no mechanism was tested, so no PJM cell verdict changes.

## 5. Routed, not fixed — NEISO (not this lane)

`check_mechanism_matrix.py` warns that `docs/codebase-site/data/mechanism-matrix/NEISO.js` and
the `docs/mechanism-testing-matrix.md` NEISO §5 prose header both still stamp
`2026-08-17-neiso-99-joint-p1` while `keepers/NEISO.json` reads
`2026-09-06-neiso-105-fossil-offer`. Confirmed still open at HEAD `013826a4`. That is the
neiso-105 promoting session's rule-28 duty and belongs to the NEISO lane; this PJM lane leaves
it untouched. Two NEISO touchpoint runs (`2026-09-05-neiso-2022-touchpoint-k99`,
`2026-09-05-neiso-2020-2021-touchpoints`) also still carry `holdout.keeper` stamps naming the
superseded neiso-99 — dangling under the rule 30(a) amendment, so they render as separate cards
rather than folding. Also NEISO's to resolve.
