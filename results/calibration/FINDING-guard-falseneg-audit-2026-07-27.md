# FINDING — merit-order guard FALSE-NEGATIVE audit: no CONFIRMED cell; four SUSPECT on tight-hour placement alone, the population test is clean everywhere, and the smoking-gun statistic is mostly a window-length effect

**Lane:** cross-ISO (governance), owner-raised 2026-07-27. Audits the
owner-adopted merit-order guard
(`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §3a/§8) for
FALSE NEGATIVES: a unit that breaks during a stretch when it is ALSO out of
merit is indistinguishable from economic layup on the guard's discriminator
and gets erased — if material, the corrected envelope under-counts outages in
tight hours, prices come out too low and the scarcity tail too thin
(directionally, PJM's post-guard C3a-2025 −10.6 % / C3c 0.39×/0.47×).
**This lane audits the guard; it does not change it** (rule 23
`[R-FROZEN-DERIVE]`): no extract re-derived, no `outage_detect.py` edit, no
solve, nothing registered (rule 15 — correct for a no-solve session), no
holdout year (rule 22), no keeper/frontier state touched.

**Probe:** `scripts/probes/guard_falseneg_audit.py`, pre-registered at commit
`2b1bc6b` (verdict rules, constants, placebo construction in the docstring)
BEFORE the first run; post-hoc placement-null diagnostic added at `1b63004`
AFTER the pre-registered results existed, labelled post-hoc at the site and
never a verdict input (pjm-131 §4 / pjm-132 §4 precedent). Output:
`results/calibration/guard_falseneg_audit_2026-07.json` (pre-registered
fields verified byte-identical across both runs). Committed inputs only: the
guard-on extracts, their `campd-unit-outages-layup[-<ISO>].csv` companions,
the five charter-§4 published anchors, and measured EIA-930 net load.

## §0 — verdicts (pre-registered rules; unmet-means-dead)

| ISO | D2 population test | D3 tightness placement | **verdict** |
|---|---|---|---|
| ERCOT | clean 0/3 | fires 2/3 | **SUSPECT** |
| CAISO | clean 0/3 | fires 3/3 | **SUSPECT** |
| MISO | clean 0/3 | clean 0/3 | **CLEAN** |
| NEISO | clean 0/3 (two-population instrument) | fires 2/3 | **SUSPECT** |
| NYISO | no published anchor | fires 1/3 (recorded) | **UNVERIFIABLE** |
| PJM | clean 0/3 | fires 3/3, largest margins | **SUSPECT** |

**No ISO reaches CONFIRMED** (CONFIRMED required both discriminators to fire
in ≥2 of 3 years). The owner's specific mechanism — mechanically-broken
windows being erased wholesale as layup — is **unsupported at the population
grain in all five anchored ISOs**, including the highest-stakes PJM cell. What
survives is narrower (§4–§6).

## §1 — D1: what the guard drops (descriptive)

Dropped share of baseline (kept + dropped) outage GW-days, per year
2023/2024/2025, and the 3-year seasonal split of dropped GW-days:

| ISO | dropped share | seasonal split DJF/MAM/JJA/SON (%) | top dropped classes |
|---|---|---|---|
| ERCOT | 31.8 / 23.0 / 21.2 % | 42 / 24 / 13 / 22 | ST_GAS, CC_REGULAR, COAL |
| CAISO¹ | 17.9 / 8.1 / 6.9 % | 27 / 31 / 23 / 19 | ST_GAS, CC_REGULAR, CC_CHP |
| MISO | 11.5 / 10.8 / 11.0 % | 41 / 21 / 11 / 27 | ST_GAS, COAL, CC_REGULAR |
| NEISO | 10.5 / 17.9 / 25.3 % | 36 / 32 / 11 / 21 | CC_REGULAR, CC_CHP |
| NYISO | 26.9 / 22.7 / 22.8 % | 25 / 35 / 20 / 20 | ST_GAS, CC_REGULAR |
| PJM | 13.3 / 8.9 / 12.5 % | 28 / 27 / 20 / 25 | ST_GAS, COAL/CC_REGULAR |

¹ All CAISO figures in this finding are on the reviewed-crosswalk
active-plant scope (34 plants, 1,691 of 5,138 windows) — the population on
which CAISO's anchor is interpretable at all; one consistent population for
all three measurements.

Everywhere the drops are winter/shoulder-heavy and summer-light —
layup-consistent. PJM's drops are the most season-uniform in the fleet, which
foreshadows its D3 result.

## §2 — D2: the dropped windows do NOT look like the mechanical population

Monthly correlation of the DROPPED windows' daily-MW series against each
ISO's published outage instrument, per year (rule and placebo pre-registered;
placebo = same in-year GW-days dropped at random, 30 draws):

| ISO | r(dropped, published OUTAGES) | placebo p50 / p95 | r(kept, OUTAGES) context |
|---|---|---|---|
| ERCOT² | +0.07 / −0.20 / −0.30 | ~+0.6–0.8 / +0.72–0.90 | +0.79 / +0.81 / +0.92 |
| CAISO³ | +0.55 / +0.57 / −0.14 | +0.59–0.72 / +0.87–0.89 | +0.78 / +0.77 / +0.85 |
| MISO | +0.10 / +0.33 / −0.39 | +0.63–0.66 / +0.86–0.90 | +0.88 / +0.80 / +0.95 |
| NEISO⁴ | −0.26 / +0.01 / +0.24 | (two-population rule) | +0.71 / +0.61 / +0.78 |
| PJM | +0.36 / −0.07 / +0.14 | +0.72–0.81 / +0.85–0.92 | +0.90 / +0.91 / +0.95 |

² ERCOT anchor caveat (charter §4): DAM offered capacity conflates mechanical
unavailability with not-offered, so it carries some layup itself and a D2
fire would have been over-called. It did not fire.
³ CAISO anchor caveat: CNOG's non-operational bucket can itself include
long-term economic states; active-plant scope mitigates, not eliminates.
⁴ NEISO ran the full two-population rule: r vs published UNCOMMITTED =
+0.77 / +0.71 / +0.67, so the dropped windows track the published *layup*
population and anti-track the published *outage* population — and the port
check reproduced the charter §3a D1 reference values **exactly** (all six
numbers within rounding).

In **all 15 anchored ISO-years** the dropped series sits at or below the
placebo p50 against the published mechanical series — a random same-size drop
would track published outages far better than the guard's actual drop does.
At the seasonal/population grain the guard is removing the layup population,
not the mechanical one. Secondary result, worth keeping: the guard-KEPT
extracts track their published instruments at r +0.61…+0.95 in every anchored
ISO-year — the charter's NEISO positive control generalizes to all five
anchored ISOs at no solve cost.

## §3 — D3: the pre-registered smoking gun fires in 10 of 15 anchored cells…

MW-weighted share of window-hours in the year's TIGHTEST net-load quartile
(EIA-930 Demand − wind − solar, within-year percentile; placebo = same
in-year GW-days dropped at random, 30 draws, p95):

| ISO | dropped share by year | kept share | placebo p95 | fires |
|---|---|---|---|---|
| ERCOT | 0.106 / 0.175 / 0.203 | 0.082 / 0.121 / 0.150 | 0.113 / 0.143 / 0.184 | 2/3 |
| CAISO | 0.208 / 0.197 / 0.242 | 0.168 / 0.142 / 0.196 | 0.190 / 0.179 / 0.221 | 3/3 |
| MISO | 0.150 / 0.168 / 0.179 | 0.163 / 0.154 / 0.170 | 0.187 / 0.177 / 0.203 | 0/3 |
| NEISO | 0.248 / 0.202 / 0.224 | 0.203 / 0.201 / 0.173 | 0.245 / 0.240 / 0.218 | 2/3 |
| NYISO | 0.216 / 0.179 / 0.163 | 0.189 / 0.186 / 0.178 | 0.213 / 0.205 / 0.204 | 1/3 |
| PJM | **0.222 / 0.218 / 0.196** | 0.123–0.163 | 0.191 / 0.173 / 0.153 | **3/3** |

The capacity the guard returns to the envelope sits on tight hours at close
to the *unconditional* quartile rate (0.25) rather than the well-below-uniform
rate pure cheap-hour layup predicts — except in MISO, whose dropped set
behaves exactly as layup should (below placebo in all three years; MISO is
the CLEAN reference cell). Scale of the returned tight-hour capacity
(dropped GW-days × 24 × tight share ÷ ≈2,190 tight hours):

* **PJM ≈ 5.0 / 2.8 / 3.4 GW** average per tight hour in 2023/2024/2025 —
  the C3c-relevant magnitude, on the ISO whose post-guard misses are exactly
  a thin scarcity tail;
* ERCOT ≈ 2.0–2.6 GW; MISO ≈ 2.2–2.4 GW; NYISO ≈ 1.6–2.8 GW;
  NEISO ≈ 0.7–1.1 GW; CAISO ≈ 0.3–0.7 GW (scoped).

## §4 — …but the post-hoc placement null attributes most of D3 to window LENGTH

The pre-registered D3 placebo matches GW-days but not window length, and a
long window's tight share regresses toward 0.25 mechanically. The post-hoc
diagnostic (commit `1b63004`, labelled at the site, never a verdict input)
re-places the same windows — same in-year span lengths, same MW — uniformly
at random within the year:

* **KEPT windows sit below the placement-null p5 in all 18 ISO-year cells**:
  mechanical/maintenance windows are strongly *timed away* from tight periods
  (planned outages avoid peaks), typically 0.08–0.11 below the null median.
* **DROPPED windows sit marginally below the null p5 (11 cells) or inside the
  band (5 cells — CAISO 2023/2025, NEISO 2023/2025, NYISO 2023)**, typically
  only 0.02–0.04 below the null median. PJM's dropped set: 0.222 vs p5
  0.226, 0.218 vs 0.221, 0.196 vs 0.213 — just below the band's floor.

So the D3 exceedance over the pre-registered placebo is **mostly a length
composition effect**: dropping long windows per se returns more tight-hour
capacity per GW-day than the short, deliberately shoulder-timed maintenance
windows that dominate the baseline. Controlled for length, the dropped set is
*weakly* tight-avoiding — not tight-seeking. What the null cannot decide is
whether "weakly tight-avoiding" is simply what layup timing looks like (fuel
economics operate at week/month grain and cannot dodge individual tight days
the way scheduled maintenance does) or whether a sub-population of genuinely
broken-while-uneconomic windows is diluting a strongly tight-avoiding layup
signal. No committed instrument measures hour-grain mechanical capability,
which is exactly why the four D3-only cells stay SUSPECT rather than
resolving to CLEAN or CONFIRMED.

## §5 — synthesis

1. **The strong form of the false-negative hypothesis is refuted.** In every
   anchored ISO the dropped population anti-tracks the published mechanical
   series and (where the instrument separates the populations) tracks the
   published layup series — with the charter's own NEISO control reproduced
   exactly. The guard is selecting the population it was designed to select.
2. **The surviving exposure is hour-grain, not window-grain.** The guard's
   window-level veto (OOM share ≥ 0.90) erases windows that contain up to
   10 % in-merit hours, and those windows sit on tight hours at near-uniform
   rates because they are long. The units demonstrably did not run through
   those tight hours (that is why a detector window exists at all); whether
   they *could have* is unmeasured. The returned capacity concentrated there
   is material — ~3–5 GW per average tight hour in PJM.
3. **MISO is the clean reference**: its dropped set is below placebo on both
   discriminators in every year — the guard's intended signature.
4. **NYISO remains the instrument gap**: 22–27 % of its baseline GW-days are
   dropped (second-highest in the fleet) with no published series to check
   either discriminator's population against. D3 recorded 1/3 (clean) for
   when an anchor lands.

## §6 — what this means for PJM and FINDING-pjm132 §5

**PJM did not confirm.** Under the pre-registered bar, PJM's re-tune does
**not** acquire a named root cause from this lane: D2 is clean 3/3 — the
windows PJM's guard dropped are, at the population grain, layup, not erased
breakage. The frontier assessment of `FINDING-pjm132-withinseason-refuted-2026-07.md`
§5 therefore **stands unchanged**: PJM is NOT frontier, the blocker remains
the keeper-on-corrected-data question (an owner call), and this audit neither
re-opens the mechanism ledger nor adds to it.

What this lane *does* hand the PJM conversation is a quantified, previously
unmeasured property of the corrected envelope: the guard returns ~2.8–5.0 GW
of average capacity to PJM's tightest net-load quartile, its dropped set is
the most season-uniform and least tight-avoiding in the fleet (D3 3/3 with
the largest margins), and the direction matches the C3a/C3c misses that
opened this lane. That is a **SUSPECT-grade lead on the already-open
G-20b/G-22 reserve-tightness root cause** (pjm-129's framing), not a
confirmed cause — and closing it needs an instrument this program does not
currently hold (hour-grain mechanical capability, §7).

## §7 — recommendation (evidence for a memo; no fix is written here)

A fix memo is **not yet warranted on this evidence alone** — no cell
confirmed, and the D3 signal is mostly length composition. What is warranted:

1. **NYISO anchor intake** (owner authorization, per-ISO per-window intake
   clause of rule 22): NYISO drops the second-largest share of its envelope
   with zero verification capability. Any published NYISO outage/availability
   series (e.g. NYISO outage schedule reports) converts UNVERIFIABLE into a
   measurable cell for both this audit and the charter's §4 protocol.
2. **If the owner wants the hour-grain exposure closed**, the memo to write
   is a *within-window tight-hour treatment* question (does a vetoed window's
   in-merit tail — ≤10 % of hours under `OOM_FRAC = 0.90`, concentrated in
   tight hours — stay erased with the window, or does the envelope keep the
   unit out through it?). That memo must confront charter §3a D2's explicit
   "not shortened" decision and its rationale ("no evidence of a
   genuinely-down core"), the fact that the unit measurably did NOT run
   through those hours, and neiso-68's finding that seam-population units
   were in merit on essentially every seam day yet stayed down — i.e. the
   evidence cuts both ways, and rule 19 `[R-ONE-MECH]` bars stacking a new
   mechanism on the guard's lane without replacing it. Owner sign-off, its
   own charter, LOYO within 2023–2025 (rule 22) — not this lane's work.
3. **No guard parameter moves on this finding** (rule 23), and the four
   SUSPECT verdicts must not be quoted as CONFIRMED anywhere downstream.

## §8 — rule compliance

* **Rules 1/13/26:** the published outage MW is the only target anywhere in
  the probe; no LMP, no price residual, no tuning.
* **Rule 22 `[R-HOLDOUT]`:** 2023–2025 only; the probe hard-refuses other
  years; freeze untouched.
* **Rule 15 `[R-DASHBOARD]`:** no solve ⇒ nothing to register (pjm-124…131
  precedent).
* **Rule 23 `[R-FROZEN-DERIVE]`:** `outage_detect.py` and every extract
  untouched; guard parameters unread except as citations.
* **Rule 25 `[R-ISO-SCOPE]`:** per-ISO measurements only; no cross-ISO
  parameter exists in the probe.
* **Pre-registration:** verdict rules committed at `2b1bc6b` before any run;
  the two post-registration code changes are (a) a mechanical
  `DatetimeIndex.notna()` fix and (b) the post-hoc placement null, both
  disclosed at the site and in this finding; pre-registered outputs verified
  identical across runs.
* **Rule 27 `[R-PUSH]`:** files edited locally, exact on-disk bytes pushed,
  blob-verified after push.

## Reproduction

```
uv sync
PYTHONPATH=. .venv/bin/python scripts/probes/guard_falseneg_audit.py \
    --posthoc-placement \
    --json results/calibration/guard_falseneg_audit_2026-07.json
```

No `data/clean/` regeneration is required (net load reads raw EIA-930).
