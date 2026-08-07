# miso-140 — MISO bench comparator refresh, verified; every MISO C3a re-verified

**Session:** miso-140, 2026-08-07, branch `claude/miso-bench-refresh-c3a-e2zuk7`.
**Scope:** §5.4 MISO lever queue **item 1** (owner-selected 2026-08-06).
**Outcome:** item 1 **DISCHARGED**. Keeper unchanged, determination unchanged,
nothing registered, no cell verdict minted.

* **PREREG** `results/calibration/PREREG-miso140-bench-lw-refresh-2026-08-07.md` (pushed `483091b3`, before any adjudicating statistic)
* **FINDING** `results/calibration/FINDING-miso140-bench-lw-refresh-verified-2026-08-07.md`
* **Probe / record** `scripts/probes/_miso140_bench_lw_verify.py` · `results/calibration/_miso140_bench_lw_verify.json`

---

## 1. What the next session inherits

| | state at end of miso-140 |
|---|---|
| MISO keeper | `2026-08-05-miso-132b-cc-committed` (bundle `results/calibration/miso132_ccmin_B`) — **UNCHANGED** |
| determination | **NOT-YET** — unchanged; sole FAIL **C3a `price_mean`**; ledger 1 of 1 on C3c |
| C3a (RT, gated) | 2023 **−0.4 % PASS** · 2024 **−6.0 % PASS** · 2025 **−14.1 % FAIL** |
| C3a (DA, diagnostic) | 2023 −4.4 % · 2024 −8.4 % · 2025 −15.8 % |
| comparator (`rt_lw` / `da_lw`) | 2023 **32.85 / 34.23** · 2024 **32.30 / 33.14** · 2025 **45.46 / 46.35** |
| holdout tier | MISO holds **no** marker in `calibration-complete.json` — **2023–2025 only** |
| open queue | **item 2 is the queue head** (flat summer capacity haircut vs net-summer `pmax`) |

**The bench is now correct and does not need touching again.** Both verification
gates passed 78/78 cells; the stale-demand-vintage defect miso-137 §5 opened is
closed and independently confirmed.

## 2. What actually happened (read this before re-deriving anything)

The mechanical refresh **was already performed by a cross-ISO session ~45 min
before this one opened** — pjm-160 B5 re-derived `*_lw` in
`data/raw/_validation-source/actual_lmp.json` for all six ISOs (`1d63141c`) and
propagated MISO's into the three bench parts (`056eb164`). The PREREG disclosed
this in advance and re-pointed the session from *doing* the refresh to
**adjudicating whether it is right**, which nobody had checked.

* **G-1 (reproducibility) PASS, 0/78 mismatches.** `_lw_fields` recomputed at
  HEAD reproduces the committed reference exactly; unrounded 2025 RT =
  **45.4555**, matching miso-137's recompute to the fourth decimal.
* **G-2 (faithfulness + confinement) PASS, 0/78 mismatches.** Of the
  **19 / 22 / 20** bench leaves that moved (of 8178 / 8109 / 8074), **100 % are
  `avgLMP.*_lw` / `*_lw_mon` — zero non-`*_lw` leaves.** The pjm-160 PJM-side
  nameplate-union bench regen (`f6e88aa3`) did **not** reach MISO.
* **G-3 (C3a) PASS as pre-registered.** `calibration_verdict.py --run-id …`,
  committed artifacts, **no re-solve**, all three years in one invocation
  (rule 16). Scored twice — at HEAD, and with the bench reverted in place to
  `056eb164^` — to isolate the comparator's own effect.

**Determination: `NOT-YET` → `NOT-YET`, and ZERO criterion-status flips across
all eight criteria** (checked record-by-record, not at the headline). PREREG §2
branch 2 applies; the escalation path (second invocation +
`calibration-keeper-auditor --iso MISO`) was **not triggered** and not run, and
no keeper text moved.

**Direction, stated because it was pre-registered:** the refresh makes 2025
(−13.97 → −14.09 %) and 2024 (−5.90 → −5.98 %) **worse** and only 2023 better.
**It is not progress against the −14 % C3a gap and must not be cited as such.**

## 3. Provenance of the comparator (so nobody re-derives it blind)

* **Deriver** `scripts/data/derive_actual_lmp.py::_lw_fields` → `lw_retrofit`
  (CLI `--lw-retrofit`), non-ERCOT branch; statistic `_lw_stats` (NaN-aware,
  `w > 0` masked, `round(·, 2)`, fixed non-leap month-start table).
* **Prices** `data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`
  (Indiana Hub system reference) — **last touched `f434590d`, unchanged by the
  refresh.** The refresh moved *weights*, not prices; miso-137's diagnosis holds.
* **Weights** `eia_loader.load_demand("MISO", year, get_iso_config("MISO"))`
  summed over zones — `(6, 8760)` over MISO-West/Plains/Illinois/Indiana/East/South,
  **640.993 / 644.633 / 663.810 TWh** for 2023 / 2024 / 2025.
* **Where the scorer reads it** `calibration_verdict.score_price_mean` →
  bench part `bench.avgLMP.{rt_lw,da_lw}` (rubric v2.4 like-for-like basis).

To re-verify at any later HEAD: `uv run python scripts/probes/_miso140_bench_lw_verify.py`
(reads committed artifacts only; solves nothing).

## 4. Two things carried forward, deliberately not repaired

1. **Registry sidecars store no scored value** — `id / label / date / shorthand /
   definition / years / iso / file / bundle` only. Scoring is derived from the
   bench at render/deploy time, so **every MISO run re-scores off the refreshed
   comparator automatically**; there is no per-run repair to do. The one built
   artifact that does store scored numbers, `frontend/data/backcast/status/MISO.js`,
   was already regenerated by pjm-160 (`2026-08-07 05:53`) and matches this
   session's independent re-verification exactly — no rebuild needed.
2. **One stale prose site, inert and pre-existing.** The keeper bundle's
   `calibration_attestation.json` → `.exceptions[5].reason` (the C3a `price_mean`
   ledger) still quotes `$45.39`. Left alone because it is **not scored** (that
   ledger entry is inadmissible under rubric v3.1 — the run's basis reads
   *"undocumented out-of-tolerance (FAIL) criteria: price_mean"*), because PREREG
   §2.4 bars a keeper-text move on a hygiene refresh, and because it was
   **already** stale on two further numbers beforehand (model `$38.66` vs the
   keeper's `$39.05`; *"2023 (−2.2 %) and 2024 (−8.0 %)"* vs the actual
   −0.4 % / −6.0 %). **Owner: the next MISO keeper promotion**, which regenerates
   the attestation anyway.

## 5. Next — queue item 2, and what stays closed

**QUEUE HEAD: item 2 — the flat summer capacity haircut vs the net-summer `pmax`
basis** (rule 14 `[R-ACCURATE]`), its own session, full text at
`docs/mechanism-testing-matrix.md` §5.4. Untouched here by design (rule 19). In
short: MISO's merchant gas classes carry a flat `SUMMER_CLASS_DERATE`
(CC 0.10 / CT 0.125, `fuel_trajectories.py`) applied Jun–Sep **on top of** a
`pmax` that is already the EIA-860 net-summer rating (`eia860.py:998`). A
double-count is the **live hypothesis, not the premise** — establish first what
the flat derate was identified against. **No C3a claim may be attached to it:**
miso-139 §7 already measured the capability family at 30–39× too small to move
the summer-afternoon marginal unit.

**Stays closed / not a lane:** the anchor-convention successor (OPEN OWNER
DECISION, not queued — do not open it); `temp_derate_mean_anchored`
(REFUSED-AT-G0 at miso-139, needs new evidence); C7 COAL_PRB (deprioritized by
owner order).

**Still the standing target** (owner directive 2026-08-06): the 2024/2025
mean-LMP level miss. The best current characterisation of it is miso-137 —
**a compressed price distribution**, over-priced below ~$40 and under-priced
above it, monotone in the actual price level with no break, and compressed on
the clock the same way (summer h00–05 high, summer h12–17 low). A **level**
lever cannot fix it. Nothing in miso-140 changes that picture; the comparator
correction is 0.14 % of level and adverse.

## 6. Environment note

The web container starts with project deps absent (`ModuleNotFoundError:
market_sim` / `pydantic`); `uv sync` installs them and everything above runs
under `uv run python`. The four pre-existing `main`-red checks (Fast test tier,
FR-22 forecast parity, Rule-22 quarantine gates, Forecast-invariant audit) are
all **other ISOs'** artifacts and were not touched from this lane.
