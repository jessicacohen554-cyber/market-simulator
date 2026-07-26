# FINDING — pjm-127: the conditioning-artifact verdict CONFIRMS in all three years (2026-07-26)

**Verdict: ARTIFACT in 2023, 2024 and 2025 independently, and on the pooled
three-year corpus with the fidelity hard-guard. The pjm-126 result is settled
for the full training window.** The measured mid-curve surface's tightest-bin
inversion is a property of the within-year conditioning, not of PJM's offers,
in every year the surface covers. Lane 2 stays open; the re-derive decision
memo (`docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`,
pre-registered before these results) goes to the owner.

pjm-126 measured 2025 only and its §5 scope limit owed this check: "the
multi-year check is owed before this is treated as settled for all three."
This session ran the identical probe (same pre-registered criteria, committed
`9409f7f`; same season map; one NA-safety fix, `af95a7e`) on the freshly
fetched 2023 and 2024 corpora, then once on the pooled 2023–2025 corpus
without `--skip-fidelity`.

---

## 1. The measurement

Inversion gap = `median(bin2) − median(bin3)` on each segment's diagnostic
share band; **positive = the tightest bin is cheaper** (the inversion is
present). Arm A is the frozen within-year conditioning, arm B within-season,
arm C the frozen conditioning on the all-four-bins population.

| year | segment | A_frozen | B_season | flag | C_fixedpop | flag |
|---|---|---|---|---|---|---|
| 2023 | CT_FAST | +3.000 | **−3.000** | **FLIP** | +3.000 | HOLDS |
| 2023 | CC_LIKE | +0.200 | **−0.300** | **FLIP** | +0.200 | HOLDS |
| 2023 | LONG_RUN | +0.250 | **−0.300** | **FLIP** | +0.250 | HOLDS |
| 2024 | CT_FAST | +5.100 | **+1.150** | **NARROW (77%)** | +5.100 | HOLDS |
| 2024 | CC_LIKE | +0.400 | **−0.300** | **FLIP** | +0.400 | HOLDS |
| 2024 | LONG_RUN | +0.050 | +0.250 | HOLDS | +0.050 | HOLDS |
| 2025 | CT_FAST | +10.000 | **−0.850** | **FLIP** | +10.000 | HOLDS |
| 2025 | CC_LIKE | +0.350 | **−0.200** | **FLIP** | +0.350 | HOLDS |
| 2025 | LONG_RUN | +0.100 | +0.250 | HOLDS | +0.100 | HOLDS |

Per-year verdicts on the pre-registered 2-of-3 criterion: **2023 ARTIFACT
(3/3 segments), 2024 ARTIFACT (2/3), 2025 ARTIFACT (2/3)**. The 2025 rows
are pjm-126's committed run, which this session **re-ran on the freshly
fetched corpus and reproduced with an identical gap table** (all nine rows,
same 8.5e-13 fidelity deviation;
`pjm126_conditioning_precheck_2025_rerun.json`) — the re-download and the
NA-safety patch change nothing. Pooled three-year run: see §3.

**Fidelity guard, full strength, every run.** Worst arm-A deviation vs the
committed `pjm_offer_midcurve_condbinned.json` ladders: **7.9e-13 (2023),
9.2e-13 (2024), 8.5e-13 (2025)** — the probe measures the frozen surface
exactly; `--skip-fidelity` was never used.

## 2. The mechanism holds — and is *stronger* in the confirmation years

The pjm-126 mechanism is segregation: PJM is summer-peaking, so winter's own
tight hours never reach the annual top-3% of net load, leaving the tightest
bin a summer-only sample while winter's expensive CT offers inflate the
middle bins. The confirmation years are more extreme than 2025, not less
(within-year bins × season, EIA-930 net load, hours):

| year | bin3 winter | bin3 summer | bin3 shoulder | bins 1–2 winter |
|---|---|---|---|---|
| 2023 | **3** | 260 | 0 | 441 |
| 2024 | **1** | 262 | 0 | 494 |
| 2025 | **34** | 229 | 0 | 726 |

In 2024 exactly **one winter hour all year** ranks in the annual top-3%. A
conditioner under which winter scarcity is unrepresentable by construction
cannot be measuring tightness state; the 2025 finding was not a weather
fluke of one year.

Two honest wrinkles, stated rather than smoothed:

* **2024's CT_FAST narrows (77%) instead of flipping.** 2024's summer was
  the tightest of the three (the bin3 sample is still 99.6% summer), and its
  within-season bin3 keeps a residual +1.15 gap on a base of ~26 — a 4%
  effect vs arm A's 21%. The pre-registered NARROW ≥ 50% branch exists for
  exactly this case, and CC_LIKE — the segment the keeper actually arms —
  flips outright in all three years.
* **LONG_RUN is noise-level everywhere.** Its arm-A gaps are +0.05 to +0.25
  on bases of ~8–10 (0.5–2.5%), flipping in 2023 and holding in 2024/2025
  with |gap| ≤ 0.30 throughout. As pjm-126 put it: an order of magnitude
  below the two segments that carry the effect, in either direction.

## 3. The pooled three-year run (the hard-guard run)

One pass over the full 36-month corpus, per-year within-year vs within-season
ranking, gaps evaluated on the year-pooled histograms, `--skip-fidelity` NOT
passed — the guard ran at full strength and passed (worst arm-A deviation
**9.2e-13** at CT_FAST/2024/bin0/s0.99, tol 0.05; segmentation 1,064 CT_FAST /
883 CC_LIKE / 216 LONG_RUN units).
`results/calibration/pjm127_conditioning_precheck_3yr.json`:

| segment | A_frozen | B_season | flag | C_fixedpop |
|---|---|---|---|---|
| CT_FAST | +5.850 | **−0.600** | **FLIP** | +5.850 (HOLDS) |
| CC_LIKE | +0.200 | **−0.300** | **FLIP** | +0.200 (HOLDS) |
| LONG_RUN | +0.250 | **−0.050** | **FLIP** | +0.250 (HOLDS) |

**Pooled verdict: ARTIFACT, 3/3 segments FLIP** — on the corpus the frozen
surface was actually derived from, every physics segment's tightest-bin
inversion reverses sign under within-season ranking. The pooled result is
stronger than any single year because the year-pooled middle bins accumulate
three winters of expensive offers while the pooled bin3 stays ~97% summer
(§2), so the segregation arithmetic compounds.

## 4. Consequences

Unchanged from pjm-126, now standing on the full training window:

* **pjm-123 §3's generalization stays narrowed** to "the surface as
  conditioned in the 2026-07 vintage" — in all three years, not just 2025.
* **The measured surface stays a live candidate dispersion lever**, aimed at
  the residual pjm-125 left standing (the dispersion compression pjm-121's
  promotion caveat records as untouched). Lane 2 stays open; frontier
  remains premature.
* **Nothing here re-derives anything.** Rule 20 binds; the owner decision
  memo — pre-registered on this branch *before* these confirmations landed
  (`cee35d5`) — is the vehicle. Its §4 A/B expectations and refutation
  signature were in git before any 2023/2024 number was seen.

## 5. Guardrail review

* **Rule 20** — no surface written, no derive re-run; diagnostic JSONs only.
  The one probe edit (`af95a7e`) is an NA-safety fix for the 2023 fall-back
  day's NaT row, committed before the 2023 run; it reproduces arm A's
  drop-at-merge behaviour and touches no definitional content.
* **Rule 1 / rule 13** — no residual entered any verdict; offers only,
  clearing prices untouched.
* **Rule 22** — 2023/2024/2025 only; no out-of-training year touched.
* **Pre-registration** — criteria unchanged from pjm-126's committed
  docstring; the owner memo's forward-looking criteria were committed
  (`cee35d5`) while the probes were still running.
* **Scope limit** — the commitment-status half of the Lane 2 hypothesis
  remains untested. Arm C stays effectively vacuous in every year — 731 of
  737 units (2023), 712 of 715 (2024), 711 of 711 (2025) and 2,154 of 2,163
  pooled offer in all four bins, so arm C reproduces arm A's gap table to
  three decimals in every row. Testing commitment status needs the DA *awards* side, which
  the offer corpus does not carry — that is pjm-128, not this probe.

## 6. Reproduction

```
python scripts/data/fetch_pjm_energy_offers.py --years 2023 2024 2025   # ~6.5 h, ~430 MB
for y in 2023 2024 2025; do
  python scripts/probes/pjm126_midcurve_conditioning_precheck.py --years $y \
      --json-out results/calibration/pjm126_conditioning_precheck_$y.json
done
python scripts/probes/pjm126_midcurve_conditioning_precheck.py --years 2023 2024 2025 \
    --json-out results/calibration/pjm127_conditioning_precheck_3yr.json
```

The §2 composition table needs no offer corpus — EIA-930 net load plus the
month→season map.

## Pointers

* The 2025 finding this confirms: `docs/FINDING-pjm126-midcurve-conditioning-artifact-2026-07.md`.
* The decision this feeds: `docs/handoffs/pjm-midcurve-reconditioning-memo-2026-07.md`.
* Charter and ledger: `docs/handoffs/pjm-frontier-path-2026-07.md` §3.
* The untested half: pjm-128 (DA awards / commitment status), handoff §3.
