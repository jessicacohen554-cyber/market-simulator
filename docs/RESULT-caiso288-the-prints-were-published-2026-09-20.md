# RESULT caiso-288 — the 2022 C3a miss was a SCRAPER BUG: EIA published the Dec-22..30 citygate prints and `re.search` threw them away

**Lane:** CAISO calibration · **Date:** 2026-09-20 · **KEEPER PROMOTED** to
`2026-09-20-caiso-288-citygate-recovery` (bundle `caiso288_gasfix_span`) under the owner ruling
of this date (*"If so plz promote"*). Charter:
`docs/PRECOMMIT-caiso288-citygate-catchup-tables-2026-09-20.md`, pushed at
`35adf93cfcde5020f484b0a1057c5ad9a9115434` **before any shard was launched**. Every gate,
band and named outcome below was fixed there.

---

## 0. The answer in one paragraph

CAISO's only load-bearing failure was **C3a-2022, +11.3 % against RT**. It is not a belly
object (the belly carries 3.6 % of it), not a mechanism, and not a tuning problem. **Nine days
— Dec 23–31 2022 — carry 47.1 % of the entire annual gap**, and on those days the model burned
gas at **$54.05/MMBtu**: the forward-fill of the 2022-12-21 print of $53.59, the year's maximum,
struck at the peak of the western gas crisis. EIA had published the days in between all along —
**32.16 / 36.93 / 26.78 / 20.86 / 15.00 / 15.31** — on the extra live tables its catch-up page
carries after the weeks it skips, and `fetch_caiso_citygate_daily.parse_spot_table` took
`re.search`, the **first table only**, and discarded them. Restoring 85 published prints takes
**C3a-2022 from +11.344 % FAIL to +6.852 % PASS** and the 2022 rung from **NOT-YET to
CALIBRATED with zero caveats**. The same defect was found and repaired in the sibling NYISO
fetcher at nyiso-234b six days earlier; this is the CAISO half of it.

## 1. What was wrong, established on the source and never on the residual

`archivenew_ngwu/2022/12_29/` and `2023/01_05/` both return **HTTP 404** — EIA issues no Weekly
Update over Thanksgiving or Christmas/New Year. The `2023-01-12` catch-up page carries **three**
live "Spot Prices" tables, of which two were being thrown away:

| table | flow week | Cal. Comp. Avg ($/MMBtu) |
|---|---|---|
| 1st | Jan 5 – Jan 11 | 16.55 / 17.09 / 18.42 / 18.76 / 17.63 — *was in the CSV* |
| 2nd | Dec 29 – Jan 4 | **15.00 / 15.31 / Holiday / 23.66 / 18.37** |
| 3rd | **Dec 22 – Dec 28** | **32.16 / 36.93 / Holiday / 26.78 / 20.86** |

This is a **rule 14 `[R-ACCURATE]` / rule 23 `[R-FROZEN-DERIVE]` re-derivation cited to a
SOURCE-COVERAGE DEFECT.** The defect was *found* by decomposing the residual in space and time;
it is *adjudicated* on the source, and §4 pre-registered that the repair stays in whichever way
the gates move.

## 2. The repair

`parse_spot_table` now reads **every** live table (`re.finditer`), window 24 k → 60 k, each row
tagged with its week. **New guard G-DUP:** EIA itself re-served **2024's** Thanksgiving table
verbatim under **2025** dates on the `2025-12-04` page; a value vector that exactly reproduces
another week's is not a measurement and the two cannot be told apart from this source, so
**both are refused** — 10 rows, the deliberately conservative choice, declared rather than
discovered.

`caiso_citygate_daily.csv`: **1,806 → 1,891 rows**. **Zero** `ScenarioConfig` fields, constants,
thresholds, derive re-runs or offer-curve multipliers; **no** `authorized_price_tuning` block;
DOF ledger unchanged at **9/6**. Rule 25 `[R-ISO-SCOPE]`: `parse_spot_table` is imported by
exactly one other module, which builds a CAISO series — **no other ISO's input moves.**

## 3. Every gate, as pre-registered

* **G-SRC** ✓ — the prints exist and are read from EIA's own table; nothing invented or interpolated.
* **G-FETCH** ✓ — all **244** weekly pages of 2021–2026 re-read, **0** fetch failures, all
  **1,156** committed prints in range reproduced **byte-for-byte**, **0 dropped, 85 added**.
  `git diff --stat` independently reads *85 insertions, zero modifications*.
* **G-DUP** ✓ — exactly the 2 predicted weeks refused, nothing else.
* **G-FOOT** ✓ — 648 / 624 / 792 / 672 hours move in 2022 / 23 / 24 / 25, and nowhere else.
* **G-CTRL** ✓ (form 1, paired controls at one HEAD) — **and it returned more than it was asked.**
  The control is **bit-identical** to the superseded keeper on 2022 (94.074407, **0 price cells
  differ**) and within **0.004 %** on 2023–2025. **HEAD drift is nil**, so the 2,062-line
  solve-path diff since `92b8e4db` is entirely inert. Stated against this lane's own choice:
  rule 29 `[R-SCREEN]` (b) form 4 **would have been valid**, and the four control shards bought
  certainty a zero-LP G-DRIFT audit would have bought free.
* **G-DIR** ✓ — fired, as charted. See §5.

## 4. The result

| year | control | treatment | Δ $/MWh | C3a control → treatment |
|---|--:|--:|--:|---|
| **2022** | 94.0744 | **90.2789** | **−3.7955** | **+11.344 % FAIL → +6.852 % PASS** |
| 2023 | 55.8937 | 56.2261 | +0.3324 | +3.182 % → +3.796 % (PASS) |
| 2024 | 37.5471 | 37.2006 | −0.3465 | +8.361 % → +7.361 % (PASS) |
| 2025 | 37.0663 | 36.9754 | −0.0909 | +7.688 % → +7.424 % (PASS) |

**The band was pre-registered at zero LP before the solve: +11.344 % (no movement) to +6.861 %
(full pass-through). The arm landed at 100.2 % of the upper limb.** The outcome was predicted,
not discovered.

**The mechanism is visible in December**: model **291.72 → 242.50 $/MWh** against an **actual RT
of 242.65** — within **$0.15/MWh**, on data never fitted to price. Dec 23–31 falls 400.25 →
223.64 (actual 184.21).

**Determination:** keeper **CALIBRATED** on 2023–2025 with the single ledgered C3c — unchanged
from the superseded keeper. **The 2022 rung goes NOT-YET → CALIBRATED with zero caveats**
(C3c passes there too). `audit_keepers --iso CAISO` **PASS 0/0**.

## 5. Reported against the arm

**2023 gets worse** (+0.3324 $/MWh) and **November 2022 gets worse** (86.22 → 89.16 against an
actual 83.42), because the recovered Jan-2023 and Nov-2022 prints are **higher** than the
back-fill they replace. That is the pre-registered **G-DIR** gate firing for the pre-registered
reason, and it is the signature of a measured input rather than a fitted one: a tuned value
would not move the residual the wrong way in two places. A test constant moves the same way —
Jan-2023 delivered **$16.58 → $17.33** — updated in place with that provenance.

**A capability lost, stated rather than buried:** the superseded keeper carried
`p0_commitment_*`, `p0_dispatch_*` and `p0_prices_*` sidecars (caiso-287's instrumentation).
This span does **not** — the shards were not given those flags. A successor that needs to
interrogate P0 commitment state must re-solve with `--persist-p0-dispatch`, or the next keeper
should carry them.

## 6. A second caiso-288 lane found the same defect, and the two remedies are now SCORED

`claude/caiso-288-c3a-tuning-2jo6s1` (merged to main as **PR #6371**) reached the identical
diagnosis independently and remedied it with a new gated mechanism,
`ScenarioConfig.caiso_citygate_blackout_bridge`, which **estimates** the interior from measured
Henry Hub basis. Its premise is that those days are unobserved. **They were published** — so the
estimator became scorable for the first time. `scripts/probes/caiso288_blackout_estimator_scoreboard.py`
→ `_caiso288_blackout_scoreboard.json`, over all **14** recoverable blackouts / **85** days:

| construction | MAE $/MMBtu | bias | implied CC marginal-cost bias |
|---|--:|--:|--:|
| constant-extension (pre-repair) | 3.354 | +2.820 | +$21.0/MWh |
| HH-basis bridge | 1.513 | +1.269 | +$9.4/MWh |
| **recovered prints** | **0** | **0** | **$0** |

On Dec-2022: staircase MAE **29.96**, bridge **11.87**, recovered **0**. The bridge is a real
improvement (~60 % of the error) but keeps a systematic **high** bias exactly where the residual
lives, and **loses to the naive staircase in 4 of the 14 gaps**.

**They are complementary in a fixed order — RECOVER FIRST, BRIDGE THE REMAINDER.** Its field is
default-off and this keeper does not arm it, so both now sit on main without interaction. Two
consequences for whoever takes it up: a bridge armed over the **unrepaired** series bridges 85
days that are not gaps, and the sibling's 33,216-day holdout validation was measured on that
series and needs re-running on the repaired one.

## 7. Provenance and cost

Eight shards (2 arms × 4 years), one year per container (rule 36 `[R-YEAR-ISOLATION]`), all
pinned to `35adf93c`; **the parent spent ZERO LP** (rule 32 `[R-SHARD]` (a)) — the
decomposition, footprint, band, composition, scoring and differencing are arithmetic over
committed artifacts. Every shard pushed its **full** bundle including `dispatch/<year>_P1.parquet`
(rule 34 `[R-SHARD-PROMOTABLE]` (a)), and that is what made the promotion cost zero re-solves:
when `prune_iso_runs.py` deleted the freshly-registered 2022 rung (its sidecar was newer than
the citation-protected outgoing pair), it was **restored from the shard branch
`aac324c4b211dd33e028e3a0bd1ba50e2e44d7f7` at zero LP.** All 8 shards archived (rule 33).

**Recovery pins, by immutable SHA** (rule 33 `[R-SHARD-ARCHIVE]` (d)) —
`git checkout <sha> -- results/calibration/caiso288_<arm>_<year>`:

| arm | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| gasfix | `aac324c4b211dd33e028e3a0bd1ba50e2e44d7f7` | `8c19a3ae…` | `9bf1e0ba…` | `887bb239…` |
| ctrl | `cd8cc79c…` | `c03bb89a…` | `78fec265…` | `4b4ea69c…` |

**Prune (rule 35 `[R-PROMOTE]`):** the year union **{2022, 2023, 2024, 2025}** was enumerated
**before** any delete (35(b)); the incoming keeper covers all four (35(c)); promote → verify
(`audit_keepers` PASS) → **then** delete (35(e)); the superseded
`2026-09-19-caiso-287-mer-keeper` and its 2022 rung removed via `--force-uncite`, the intended
route (35(d)), with the historical `rekeyed_2026_09_19` citation retained as audit trail.

## 8. Open, and NOT touched

* **`results/calibration/caiso279_ablate_dswcouple_span` is still a CAISO parity RED on main**
  (34 committed files). caiso-286 asked and got no ruling; caiso-287 did not touch it; neither
  did this session. **It needs an owner ruling.**
* The `caiso_ra_bridge_startup_aware` drop-rate admissibility question (caiso-287 §5) stays with
  the owner. Nothing here arms or disarms it.
* The 2022 C3a residual is now **+6.85 %**, inside the band but not zero; and phase 0's finding
  that the model sits **+2.10 % against DA** while **74 % of the original 2022 miss was the
  DA−RT spread** is reported as context, never as a proposal. The DA re-point stays withdrawn.
