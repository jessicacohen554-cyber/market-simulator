# FINDING — miso-140: the MISO comparator refresh REPRODUCES EXACTLY and is CONFINED to `*_lw`; every MISO C3a re-verified; the determination does NOT change

**Session:** miso-140, 2026-08-07, branch `claude/miso-bench-refresh-c3a-e2zuk7`.
Queue item 1 of the §5.4 MISO lever queue (owner-selected 2026-08-06).
**NO LP, no solve, no arm, no field, no parameter, no run registered, no cell
verdict minted. Keeper UNCHANGED** at `2026-08-05-miso-132b-cc-committed`
(bundle `results/calibration/miso132_ccmin_B`).

**PREREG** `results/calibration/PREREG-miso140-bench-lw-refresh-2026-08-07.md`,
pushed at **`483091b3`** BEFORE any adjudicating statistic, carrying the
expected per-year deltas, the weight provenance written out in advance, and the
pre-committed decision rule for whether the determination may change.

**THIS IS BENCH HYGIENE, NOT A LEVER.** It cannot close the −14 % C3a gap and is
not reported as progress against it — and in fact it moves the blocker year the
*wrong* way (§3). No price lever was chartered or folded in (rule 19).

---

## 1. The headline

The chartered object — miso-137 §5's finding that the committed MISO `*_lw`
actual scalars recompute to **45.4555 vs the committed 45.39** — **had already
been repaired by a cross-ISO session ~45 minutes before this session opened**,
and the PREREG disclosed that in advance rather than discovering it later:

| commit | time (UTC) | what it did |
|---|---|---|
| `1d63141c` | 2026-08-07 ~06:0x | pjm-160 B5: re-derived `*_lw` in `data/raw/_validation-source/actual_lmp.json`, **all six ISOs** |
| `056eb164` | 2026-08-07 06:14:59 | pjm-160 B5: propagated MISO's into the three bench parts + regenerated `status/MISO.js` |

So the session re-pointed from *performing* the refresh to **adjudicating
whether it is right** — which nobody had checked. A comparator that is merely
*newer* is not a comparator that is *correct*, and mine would have been the
third vintage if I had rewritten it on my own numbers (PREREG S1).

**Both verification gates PASS, 78/78 cells each, exactly as pre-registered.**

---

## 2. G-1 and G-2 — the refresh is reproducible, faithful, and confined

**G-1 — does the refreshed reference reproduce?** This is the miso-137 G-0(i)
test re-run against the **new** values. `derive_actual_lmp._lw_fields("MISO", y)`
recomputed at HEAD vs the committed `actual_lmp.json`:

| cells compared | mismatches | verdict |
|---|---:|---|
| 78 (2 bases × 3 years annual = 6; + 2 × 3 × 12 monthly = 72) | **0** | **PASS** |

| year | `rt_lw` fresh / committed | `da_lw` fresh / committed | unrounded `rt_lw` |
|---:|---|---|---:|
| 2023 | 32.85 / **32.85** | 34.23 / **34.23** | 32.8470 |
| 2024 | 32.30 / **32.30** | 33.14 / **33.14** | 32.3006 |
| 2025 | 45.46 / **45.46** | 46.35 / **46.35** | **45.4555** |

The unrounded 2025 RT lands on **45.4555**, matching miso-137's published
recompute to the fourth decimal and hitting the PREREG's pre-declared
`45.4555 ± 0.0005` band. The stale-vintage defect is **closed**.

**G-2 — is the propagation faithful, and CONFINED?** Every `*_lw` cell in the
committed bench parts equals the reference (78/78, 0 mismatches). And of the
leaves that moved in `056eb164`:

| year | leaves total | leaves moved | **moved and NOT `*_lw`** |
|---:|---:|---:|---:|
| 2023 | 8,178 | 19 | **0** |
| 2024 | 8,109 | 22 | **0** |
| 2025 | 8,074 | 20 | **0** |

**100 % of the movement is `avgLMP.*_lw` / `*_lw_mon`.** The PREREG's S3
blast-radius stop rule did not fire: the pjm-160 PJM-side bench regeneration on
a *corrected nameplate union* (`f6e88aa3`) did **not** reach MISO, and no
`classFull` / `e930` / `co2` / `plants` leaf moved under a comparator mandate.

**Provenance of the new weights**, read from source at HEAD and written into the
PREREG §0c *before* verification:

* **Deriver** `scripts/data/derive_actual_lmp.py::_lw_fields` → `lw_retrofit`
  (CLI `--lw-retrofit`), non-ERCOT branch; statistic `_lw_stats` — NaN-aware,
  `w > 0` masked, `round(·, 2)`, fixed non-leap month-start hour table.
* **Prices** `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`
  (Indiana Hub system reference). **Last touched `f434590d` — unchanged by the
  refresh.** The refresh moved *weights*, not prices, confirming miso-137's
  diagnosis that this was never a price-series defect.
* **Weights** `eia_loader.load_demand("MISO", year, get_iso_config("MISO"))`
  summed over zones — verified at HEAD to return `(6, 8760)` over MISO-West /
  Plains / Illinois / Indiana / East / South, totalling **640.993 / 644.633 /
  663.810 TWh** for 2023 / 2024 / 2025.
* Committed `src_lw`: *"system hub hourly series load-weighted by measured
  system demand (eia_loader.load_demand)"*.

---

## 3. G-3 — every MISO C3a re-verified, and the direction of the correction

`scripts/calibration_verdict.py --run-id 2026-08-05-miso-132b-cc-committed`,
**committed artifacts only, NO RE-SOLVE**, all three years in one invocation
(rule 16 `[R-ALLYEARS]` — never a single-year re-score). Scored twice: once at
HEAD, and once with the bench reverted in place to `056eb164^` to isolate the
comparator's own effect. Model scalars are identical in both — only the actual
moved.

| year | basis | model | actual PRE | actual POST | C3a PRE | C3a POST | status |
|---:|---|---:|---:|---:|---:|---:|---|
| 2023 | RT (gated) | 32.72 | 32.87 | **32.85** | −0.5 % | **−0.4 %** | PASS → PASS |
| 2024 | RT (gated) | 30.37 | 32.27 | **32.30** | −5.9 % | **−6.0 %** | PASS → PASS |
| 2025 | RT (gated) | 39.05 | 45.39 | **45.46** | −14.0 % | **−14.1 %** | **FAIL → FAIL** |
| 2023 | DA (diag) | 32.72 | 34.24 | 34.23 | −4.4 % | −4.4 % | SKIPPED |
| 2024 | DA (diag) | 30.37 | 33.13 | 33.14 | −8.3 % | **−8.4 %** | SKIPPED |
| 2025 | DA (diag) | 39.05 | 46.29 | **46.35** | −15.6 % | **−15.8 %** | SKIPPED |

**THE DETERMINATION DOES NOT CHANGE.** `NOT-YET` → `NOT-YET`; sole FAIL **C3a
`price_mean`**; caveat ledger identical (1 of 1, spent on C3c); and **ZERO
criterion-status flips across all eight criteria** (C1 fuelmix, C2 sysvol, C3a
price_mean, C3b price_shape, C3c price_tail, C4 dispatch_corr, C6 governance,
C8 forced_share), checked record-by-record rather than at the headline.
PREREG §2 branch 2 therefore applies as written; §2.3's escalation path (second
independent invocation, `calibration-keeper-auditor --iso MISO`) is **not
triggered** and was not run, and no keeper text moved.

**The correction is ADVERSE on the blocker year, and that is stated because it
was pre-registered.** 2025 goes −13.97 % → −14.09 % and 2024 −5.90 % → −5.98 %;
only 2023 improves (−0.46 % → −0.40 %). A hygiene fix that makes the target
*further away* cannot be spun as progress, and this one is structurally
incapable of it.

---

## 4. Two things carried, neither repaired here

**(i) Registry sidecars store NO scored value — so nothing is stranded.** The
charter's concern that the refresh "moves the comparator for EVERY MISO run" is
real but self-healing: a MISO registry sidecar carries only
`id / label / date / shorthand / definition / years / iso / file / bundle`, with
zero occurrences of any C3a scalar or percentage. Scoring is **derived at
render/deploy time from the bench**, never stored per run. Every MISO run
therefore re-scores off the refreshed comparator automatically; no per-run
repair exists, and none is needed. The one *built* artifact that does store the
scored numbers — `frontend/data/backcast/status/MISO.js` — was already
regenerated by pjm-160 (stamp `2026-08-07 05:53`) and **matches this session's
independent re-verification exactly** (−0.4 / −6.0 / −14.1 RT; −4.4 / −8.4 /
−15.8 DA; NOT-YET), so no rebuild is required either.

**(ii) One stale prose site, inert and pre-existing.** The keeper bundle's
`calibration_attestation.json` → `.exceptions[5].reason` — the **C3a
`price_mean` ledger entry** — still quotes the old `$45.39`. It is not repaired,
for three reasons: it is **not scored** (under rubric v3.1 that ledger entry is
inadmissible at all, and this session's own run confirms the basis reads
*"undocumented out-of-tolerance (FAIL) criteria: price_mean"*); PREREG §2.4 bars
a keeper-text move on a hygiene refresh; and it was **already** stale on two
further numbers before the refresh touched it — model `$38.66` against the
keeper's `$39.05`, and *"2023 (−2.2 %) and 2024 (−8.0 %)"* against the actual
−0.4 % / −6.0 % (the same drift miso-139 §0 corrected). Its repair belongs to
the next MISO keeper promotion, which regenerates the attestation anyway.

---

## 5. Rule duties

**Rule 15 `[R-DASHBOARD]`** — no LP solved, so there is **no run to register**
(the miso-131…137 precedent). Keeper unchanged; nothing new registered.
**Rule 16 `[R-ALLYEARS]`** — all three years re-verified in one invocation; no
single-year re-score.
**Rule 19 `[R-ONE-MECH]`** — no mechanism proposed, armed or tested; no price
lever chartered or folded in; queue item 2 untouched.
**Rule 22 `[R-HOLDOUT]`** — MISO holds **no** marker in
`calibration-complete.json`. 2023/2024/2025 only; no out-of-training year read,
solved, scored or registered.
**Rules 13/21/24** — nothing sized on any residual, no parameter derived, no
tuning channel created. The comparator is a **measured input recomputed from
unchanged measured sources**, and it moves the target *away* from the model.
**Rule 25 `[R-ISO-SCOPE]`** — MISO artifacts only. The five other ISOs' `*_lw`
also moved in `1d63141c`; adjudicating them is not a MISO lane's business.
**Rule 28(b) `[R-MECH-MATRIX]`** — **NO cell verdict minted**: no mechanism was
tested, probed or armed. The only matrix edit is the §5.4 queue stamp retiring
item 1 and promoting item 2 to the queue head.
**Owner directives** — no C7 work; `temp_derate_mean_anchored` not re-opened;
the anchor-convention successor not opened.

---

## 6. The generalisable lesson — A REPAIR IS NOT A VERIFICATION

The queue item was written as *"refresh the bench"*, and the refresh arrived
from another lane before the session started. The tempting readings were both
wrong: "already done, nothing to do", or "do it again my way". The first accepts
a number nobody checked; the second would have minted a **third** vintage of the
same scalar and destroyed the ability to tell which was right. What discharges
the item is neither — it is **re-running the failing test against the new
values, and separately proving the fix touched nothing else**. The confinement
half was the one with real risk: the same cross-ISO session that fixed the
comparator had, on another ISO, regenerated bench parts on a corrected nameplate
union, and a comparator mandate is no licence to import that. *When someone else
lands your fix, your job is not to redo it and not to trust it — it is to run
the test that failed, and to bound the blast radius.*

Family: miso-133 *measure the slack, on one basis* → miso-135 *the right
quantity at the wrong grain is the wrong source* → miso-136 *an absence claim is
a measurement, not a premise* → miso-137 *a threshold is a hypothesis, not a
definition* → **miso-140 *a repair is not a verification***.

---

**Probe** `scripts/probes/_miso140_bench_lw_verify.py` ·
**Record** `results/calibration/_miso140_bench_lw_verify.json` ·
**PREREG** `results/calibration/PREREG-miso140-bench-lw-refresh-2026-08-07.md` ·
**Handoff** `docs/handoffs/miso-140-bench-refresh-2026-08-07.md`.
