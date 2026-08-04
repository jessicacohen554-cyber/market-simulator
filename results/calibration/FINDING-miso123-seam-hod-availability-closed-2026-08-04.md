# FINDING miso-123 — the MISO seam's availability channel is ALREADY hour-of-day-shaped (r ≈ +0.95); the named successor is closed on measurement, and with it every remaining class of seam-shape mechanism

Session miso-123, 2026-08-04, branch `claude/miso-seam-band-availability-tb6atf`,
off `origin/main` at `05d291d7`. **NO LP SOLVED.** Pre-registration
`results/calibration/PREREG-miso123-seam-hod-band-availability-2026-08-04.md`,
written and committed **before** the probe was written. Probe
`scripts/probes/_miso123_seam_hod_availability.py`; transcript
`results/calibration/PROBE-miso123-seam-hod-availability-2026-08-04.txt`.

**Keeper UNCHANGED** — `2026-08-04-miso-122b-scope-gate`
(`results/calibration/miso122_scopegate_B`), determination `NOT-YET`, sole FAIL
C7 `COAL_PRB` diurnal shape, ledgered caveats {C3a, C3c}. Rule 15
`[R-DASHBOARD]`: no run was produced, so there is nothing to register — the
miso-103 / 104 / 105 / 114 discipline of refusing on measurement rather than
spending a solve.

---

## 0. Verdict

The lever chartered from `docs/mechanism-testing-matrix.md` §5.4 item **0c** —
miso-114's *"one admissible successor … hour-of-day-resolved band availability
at the `(month × hour-of-day)` grain"* — **rests on a premise that is already
satisfied, and the mechanism class it belongs to is bounded out of the job.**

1. **The availability channel is not hour-invariant and never was.** The armed
   p90 deliverability envelope tracks the measured hour-of-day flow profile at
   **r = +0.95 / +0.99 / +0.96** on the PJM seam and **+0.81 … +1.00** on all
   four, in every year — while the model's own cleared flow tracks it at
   **−0.64 / −0.75 / −0.85** on that same seam. Availability already points the
   right way; the LP's flow points the wrong way. The defect is **entirely on
   the price side**, exactly where miso-114 located it and exactly where
   miso-114 also refuted the fix.
2. **The candidate fails its own pre-registered bars.** Held-price hour-of-day
   correlation moves **+0.058 / +0.031 / +0.005** against a pre-registered
   **≥ +0.20 in ≥ 2 of 3 years** (K3), while annual seam energy falls from
   1.012 / 1.010 / 0.902 to **0.868 / 0.812 / 0.718** against a pre-registered
   **[0.85, 1.15]** (K6). It buys a rounding-error of shape by deleting an
   eighth to a quarter of the seam.
3. **The bound generalises past the candidate to the WHOLE ceiling class.** Even
   the *forbidden* construction — cleared = `min(model, measured)` hour by hour,
   an outcome pin rule 13 `[R-MEASURED]` prohibits and which is computed here
   only as an unattainable upper bound — reaches hour-of-day correlation
   **+0.241 / −0.289 / +0.305**, clearing +0.20 in **one** of three years, at
   energy ratios **0.775 / 0.624 / 0.460**. *No availability ceiling whatsoever
   can do this job*, because a ceiling can only **cut**, and the model's
   overnight seam is **short**, not long.

**Disposition, per the pre-registration's own §5.2:** Phase 0 refuses,
**no LP is spent**, and §5.4 item 0c is **CLOSED on measurement.**

---

## 1. Q0 — the reconstruction is the model's seam, and it independently reproduces miso-114

Everything downstream is conditional on this, so it is reported first. The probe
rebuilds each seam's bands offline from the model's own objects
(`INTERFACE_NEIGHBORS["MISO"]` + `MISO_MANITOBA_SEAM_SPEC` → 8 equal-width bands;
`measured_seam_import_envelope` → the p90 cap; the merit-cap waterfall of
`inject_miso_seam_flow_limit` → availability; `MISO_SEAM_LADDER_BY_YEAR` → the
rungs) and clears them against the keeper's **own solved P1 duals** at the
external zones the keeper's `miso_south_seam_split` actually hosts them in.

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| corr(reconstruction, keeper solved `import` class) | **+0.994** | **+0.995** | **+0.993** |
| hour-of-day-profile corr, reconstruction vs keeper | **+1.000** | **+1.000** | **+1.000** |
| mean MW, reconstruction vs keeper | 4,381 vs 4,419 | 2,661 vs 2,686 | 1,952 vs 1,971 |
| bias | −38 MW | −25 MW | −19 MW |

The residual bias is the border-link TTCs and the zonal network the accounting
omits; it is ≤ 1 % and it does not touch any conclusion below, all of which are
*differences* computed inside the same accounting.

**Independent confirmation of the defect itself.** The hour-of-day correlation
measured here on the **miso-122b** keeper is **+0.094 / −0.455 / −0.023**;
miso-114 measured **+0.097 / −0.453 / −0.030** on the **miso-109b** keeper, with
a different construction. Two keepers, two constructions, the same answer — the
seam's hour-of-day defect is stable and real, and it is not an artifact of
either bundle.

---

## 2. Q1 — THE result: availability is already hour-of-day-**shaped**, not merely hour-of-day-resolved

The armed envelope is a per-`(month × hour-of-day)` p90 of the measured directed
BA-to-BA flow, so it is hod-resolved *by construction*. The question that
matters is whether its **shape is right**. Correlating each channel's own
24-point hour-of-day profile against the **measured** flow's:

| seam | armed p90 cap 2023 / 24 / 25 | model cleared 2023 / 24 / 25 |
|---|---:|---:|
| **PJM** (the large seam) | **+0.952 / +0.987 / +0.955** | **−0.638 / −0.753 / −0.852** |
| SPP | +0.904 / +0.973 / +0.948 | −0.755 / −0.529 / −0.311 |
| South | +0.814 / +0.837 / +0.844 | n/a¹ / +0.700 / +0.377 |
| Manitoba | +0.996 / +0.992 / +0.986 | +0.929 / +0.898 / +0.818 |

¹ the South seam clears identically 0 MW in 2023, so its model profile is flat
and has no shape to correlate; reported rather than suppressed.

Night/peak ratios say the same thing in level terms — on PJM in 2024 the cap
runs **1.25** night-over-peak and the measured flow **1.41** (same direction,
mildly understated), while the model runs **0.86** (inverted).

**So the successor's premise is already satisfied.** miso-114 attributed the
mis-shape to the hour-**invariant** `MISO_SEAM_LADDER_BY_YEAR` price ladder, and
that attribution is confirmed here from the other side: the one channel that is
*not* hour-invariant is already carrying nearly the whole measured shape, and
the LP still ends up anti-correlated with reality because the **price** decides
which bands clear. "Hour-of-day-resolved band availability" cannot be the fix
for a defect the availability channel does not have.

---

## 3. Q2 — the envelope is not the marginal constraint overnight (the miso-121 statistic)

Per miso-121's standing lesson — **binding is not marginality; the predictive
ex-ante statistic is the marginal share of binding hours** — the probe separates
*the ceiling is reached* from *the ceiling is what stops the next MW* (a band in
the money at the solved dual whose availability the envelope has zeroed):

| seam | | binding all / night / peak | **MARGINAL** all / night / peak |
|---|---|---|---|
| PJM | 2023 | 13.8 / 3.3 / 35.1 % | 3.8 / **0.6** / 12.0 % |
| PJM | 2024 | 25.4 / 8.6 / 50.8 % | 10.9 / **2.4** / 28.6 % |
| PJM | 2025 | 12.2 / 5.3 / 28.3 % | 4.4 / **1.4** / 11.6 % |

Overnight — the window that carries the defect — the envelope is the marginal
constraint in **0.6 / 2.4 / 1.4 %** of hours. It is essentially never what stops
MISO importing at night. **Price is.** At peak it *does* bind marginally
(12.0 / 28.6 / 11.6 %), which is precisely why the candidate can cut the peak
limb and only the peak limb (§5).

---

## 4. Q3 / Q5 — the candidate fails K3 and K6 on its own pre-registered numbers

Candidate **C1** (per-band per-`(month × hod)` cell survival availability: band
*k*'s availability in a cell = the measured fraction of that cell's hours whose
directed flow exceeded band *k*'s lower depth edge; same source, same grain,
same 8-band grid, **zero free parameters, zero thresholds**, a strict ceiling),
held-price:

| | 2023 | 2024 | 2025 | bar |
|---|---:|---:|---:|---|
| hour-of-day corr, current → candidate | +0.094 → **+0.152** | −0.455 → **−0.424** | −0.023 → **−0.018** | |
| **Δ hod corr** | **+0.058** | **+0.031** | **+0.005** | **K3: ≥ +0.20 in ≥ 2 of 3 → FAIL (0 of 3)** |
| annual seam energy ratio | 1.012 → **0.868** | 1.010 → **0.812** | 0.902 → **0.718** | **K6: [0.85, 1.15] → FAIL (2024, 2025)** |
| PJM seam energy Δ | −4.439 TWh | −3.536 TWh | −3.007 TWh | |

The shape gain is an order of magnitude short of the bar, and it is paid for by
deleting 13 / 19 / 28 % of the seam's annual energy. That trade is the exact
failure mode K6 was written in advance to catch: **shape bought by deleting
volume is not a fidelity gain.**

### 4.1 KILL-13 did NOT fire — and the pre-registration predicted it would

Recorded as a wrong prediction rather than re-narrated. §4 of the
pre-registration stated *"C1 is **expected to FAIL** KILL-13(a) — its band sum is
a Riemann sum of the cell survival function and therefore approximates the cell
**mean** flow, removing exactly the headroom the p90 envelope exists to
preserve. This is written down before measuring it."*

Measured, it does not:

| limb | bar | PJM 2023 / 24 / 25 |
|---|---|---|
| (a) candidate ceiling within 5 % of the cell **mean** | majority of cells | **11.8 / 0.4 / 0.0 %** |
| (b) ceiling binds | > 70 % of hours | **3.9 / 12.3 / 3.7 %** |

The reason is the band grid's coarseness: at PJM the width is 7,300/8 =
**912.5 MW**, so an 8-rung survival sum is far too crude a Riemann sum to land on
the cell mean, and the candidate ceiling stays above it (5,079 / 4,131 / 3,651 MW
against measured means of 4,674 / 3,689 / 3,199 MW). **C1 is therefore a
legitimate capability envelope under rule 13, not an outcome pin** — it is
refused on rules 1 / 14 effectiveness (K3, K6), not on admissibility. The
distinction matters: the lane should not carry forward a belief that this
construction is forbidden. It is *allowed* and it *does not work*.

---

## 5. Q6 — why no ceiling can do this job, and the bound over the whole class

A ceiling can only **reduce** cleared flow. The signed mis-shape says the model
is **short overnight** and **long at peak**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| night mis-shape (model − measured) | **−1,116 MW** | **−972 MW** | **−1,009 MW** |
| candidate moves night by | −265 MW | −226 MW | −226 MW |
| | *further short — **away from reality** in all three years* | | |
| peak mis-shape | **+1,312 MW** | **+1,139 MW** | **+711 MW** |
| candidate moves peak by | −1,038 MW | −898 MW | −740 MW |
| | *toward reality* | | |

So the candidate fixes the peak limb almost exactly and makes the night limb
worse, and the two nearly cancel in the correlation — which is the arithmetic
behind the +0.058 / +0.031 / +0.005 of §4.

**The bound over every ceiling, not just this one.** Set cleared =
`min(model, measured)` hour by hour: cut wherever the model is long, cut nothing
where it is short. That is the best any availability ceiling could possibly
achieve at held prices — and it is a **forbidden outcome pin** under rule 13,
computed here purely as an unattainable upper bound and **never armed**:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| hod corr under the forbidden pin | **+0.241** | **−0.289** | **+0.305** |
| improvement over current | +0.147 | +0.166 | +0.328 |
| annual energy ratio | **0.775** | **0.624** | **0.460** |

Even with the rulebook suspended, the ceiling class clears the +0.20 bar in
**one** of three years, and does so while deleting **22 / 38 / 54 %** of the
seam's energy. **The class is bounded out of the job.** This is the finding's
most transferable result: it forecloses not one construction but every
availability-ceiling construction, so no future MISO session need re-derive a
different envelope statistic to find out.

---

## 6. What this closes — all three mechanism classes are now spent

The seam's hour-of-day shape admits exactly three classes of mechanism, and
after this session none is available:

| class | mechanism | status |
|---|---|---|
| **Price** — reprice the bands hour by hour | `miso_pjm_lmp_import_pricing` | **REFUTED ex ante** (miso-114 §4, on MISO's own measured data: actual MISO−PJM_WEST spread ±$1–2 overnight, night-minus-peak −1.07 / +2.16 / +3.15 $/MWh, corr(spread, actual net import) +0.289 / +0.240 / +0.286, MISO importing 4,591 MW at h2 on a +$1.0/MWh spread) |
| **Ceiling** — shape *when* a band may clear | hour-of-day-resolved band availability (this session) | **CLOSED on measurement** — premise already satisfied (§2), whole class bounded out (§5) |
| **Floor** — force the scheduled base | `miso_firm_import_floor` | **REJECTED as an outcome pin** (rule 13); miso-114 §4 stated this finding does not re-license it, and nothing here does either |

The defect itself remains **real and unfixed**, and is reported as such rather
than declared solved: the MISO seam reproduces annual net-interchange energy to
1.017 / 1.016 / 0.908 with an hour-of-day correlation of +0.094 / −0.455 /
−0.023. What has changed is that it now has a **measured attribution** (the
price ladder, not the availability channel) and a **measured bound** on the one
class that was thought to be admissible.

**Nothing here is claimed about C7 `COAL_PRB`, C3a or C3c.** The
pre-registration §1.1 fixed this as a rule 1 `[R-STRUCT]` structural-fidelity
item sized in advance at 4–7 % of the residual, and no result above is quoted as
progress on any scored criterion. The model's overnight seam short measured here
(−1,116 / −972 / −1,009 MW) is consistent with, and a component of, miso-114
§2.3's overnight import hole (1,743 / 1,547 / 1,484 MW) — reported for
continuity, not as a new lane.

### 6.1 What would legitimately re-open it

Not a different envelope statistic and not a percentile — §5 bounds those, and
`miso_seam_flow_percentile` is an already-registered knob whose sweep against a
residual is exactly what rule 23 `[R-FROZEN-DERIVE]` forbids. Re-opening needs a
genuinely new object: a **scheduling representation** of the firm/JOA transfer
base that can *raise* overnight flow with an identification that is not the
measured net interchange itself. miso-114 named that gap; this session bounds
what can be done without it.

---

## 7. Rule duties

* **Rule 1 `[R-STRUCT]`** — chartered as structural fidelity in advance and
  refused on structural grounds (the mechanism cannot reproduce the market's
  hour-to-hour behaviour), not on the residual. The residual was never consulted.
* **Rule 13 `[R-MEASURED]`** — KILL-13 measured and **not** fired; the wrong
  pre-registered prediction is recorded in §4.1. The forbidden outcome pin in §5
  is a diagnostic bound only and is not armed, not registered and not proposed.
* **Rule 15 `[R-DASHBOARD]`** — no run produced; nothing to register.
* **Rule 16 `[R-ALLYEARS]`** — all three training years measured together; no
  single-year claim is made.
* **Rule 19 `[R-ONE-MECH]`** — nothing armed, nothing stacked.
* **Rule 22 `[R-HOLDOUT]`** — 2023 / 2024 / 2025 only. MISO holds no
  `calibration-complete` marker and no out-of-training year was solved, scored
  **or read**.
* **Rule 23 `[R-FROZEN-DERIVE]`** — no derive re-run, no percentile swept; §6.1
  states why a sweep is not the successor.
* **Rule 25 `[R-ISO-SCOPE]`** — MISO only. NYISO's `import_shape_lever` `G` was
  confronted in the pre-registration as an **argument** and MISO's cell is minted
  from **MISO's own measurement**, never transferred. No cell outside MISO is
  stamped, and the cross-ISO CHP handoffs miso-122 opened (NYISO 2493 East River,
  NEISO 1595 Kendall) were not touched from this session — they remain those
  lanes' work.
* **Rule 28 `[R-MECH-MATRIX]`** — duty (b) discharged in this session:
  `import_shape_lever` MISO `·` → **`G`** (closed-no-mechanism, measured), and
  `seam_flow_envelopes` MISO **stays `K`** with its evidence re-stamped by §2's
  measurement of the armed envelope's hour-of-day fidelity. No new
  `ScenarioConfig` field was added, so duty (c) does not arise.

**Contamination declared:** the session read miso-114's finding, miso-122's
finding and the matrix `import_shape_lever` / `seam_flow_envelopes` rows before
measuring, so it was **not** blind to the hour-of-day-correlation result or to
NYISO's refusal. Immaterial to §§1–5, which rest on the committed EIA-930
directed-flow series, the keeper's own solved duals and the model's own seam
construction — and §1 independently reproduces miso-114's headline on a
different keeper.

* Next number: **miso-124.**

---

## 8. Pre-existing `origin/main` breakage — reported, not fixed, and NOT this branch's

This branch adds one probe, one pre-registration, this finding, and matrix/doc
stamps; it touches **nothing under `src/market_sim/`**. The failures below were
carried into this session's brief from miso-122's verification on a clean
`origin/main` worktree and are re-reported unchanged so they are not lost:

* **Cache-key pin drift.** Default `ScenarioConfig` cache key
  **`973a0acdef818e91`** vs the pinned `603c2498bf71d21d` — and it has moved
  since the earlier bisect (`0e9fce2fb55b889f` → `973a0acdef818e91`), so a
  further field has landed on the original culprit. Fails three tests in
  `tests/regression/test_persisted_identity.py` plus
  `test_cc_committed_offer_margin`, `test_ramp_envelope_basis`'s
  `test_default_cache_key_is_byte_stable` and
  `test_forecast_xyear_warmstart_flag::test_default_cache_key_unmoved`.
  Registering the culprit field versus advancing the pin belongs to the owning
  lane.
* **`tests/unit/data/test_outages.py::NuclearUnitAvailabilityTest::test_unknown_iso_degrades_to_empty`**
  asserts NEISO is an unknown ISO; NEISO nuclear outage data has since been
  intaken and three units now resolve. Stale test, different cause, also not
  this branch's.
