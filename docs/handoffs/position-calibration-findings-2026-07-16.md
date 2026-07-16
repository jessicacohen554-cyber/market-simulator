# Position calibration — curve-ON probe hindcasts, PJM + MISO (RC-1A, 2026-07-16)

**Charter.** F-6 of the flip-gate lane
(`docs/handoffs/forecast-retirement-calibration-plan-2026-07.md` §2.2/§2.3 —
the measurement that breaks the position↔payment circularity, and the ⛔ gate
input for RC-2B). A/B capacity hindcasts, PJM and MISO, 2021→2025 realized
fuel, EIA-860 2020 vintage, 2022 bridged-never-solved (rule 22): the committed
fixed-mode configs reproduced at HEAD (BEFORE) vs `--capacity-market-clearing`
probe legs (`capacity_market_clearing_by_iso={iso: True}`, scalar and every
default untouched). Scored raw + IS-2020 (RC-0B §c.5), Pass-2 position
restatements, and I5/I13 on every leg. Registered on the forecast-validation
dashboard only. **Nothing here tunes anything; every landed change is a cited
structural completion, byte-identical at defaults (rules 1/13/24).**

Dependency state at run time (verified on `origin/main`, 2026-07-16):

- RC-1B plumbing (per-ISO gate, vintage resolver, probe flag) on main; the
  IS-2020 scorer (RC-1E) on main; the D4 hindcast information gate on main and
  **verified live** (as-of-2020: zero in-window confirmed exits, zero reversal
  suppressions for PJM/MISO — Byron/Dresden still announced-retire, exactly the
  committed bundles' accidental-but-correct behavior, now pinned by code).
- **D1 (RC-0B) is PENDING** — no owner adoption commit exists;
  `retirement_years_coal` ran at HEAD's value **1** (below its measured ≥3
  floor, RC-0B §a.4). This re-baselines nothing here but is material to the
  wave-size findings below (§4).
- **RC-1C LANDED MID-SESSION** (PR #2326, merged after this session's first
  solves): the branch was rebased onto it and the MISO probe leg **re-solved
  on the seasonal RBDC grain** (per the charter's rebase-to-seasonal clause).
  The registered MISO probe is the seasonal leg; the earlier annual-grain
  solve of the same leg is quoted in §2 as a labeled grain-sensitivity
  diagnostic (not registered). RC-1C's NYISO curve-ineligibility gate and its
  own vintage helpers were reconciled with this session's threading (§0-1
  composes: the threaded MISO year resolves the PY2025-26 vintage carrying
  `seasonal_rbdc`, so the screens price the four-season sum).

## 0. What had to be fixed before the probe could run (structural, cited, default-byte-identical)

The probe flag as landed by RC-1B was a **silent no-op end-to-end**, and the
per-delivery-year anchors were **flat (shapeless) exactly in the probe's
window**. Three completions were landed, each its own commit; none changes any
default path (gate-off byte-identity is test-asserted):

1. **Seam threading (`capacity.py`/`storage.py`/`runner.py`).** The runner
   gated `curve_reserve_position` on the *scalar* `capacity_market_clearing`
   only, so the by-ISO probe arm never computed a position; and the three
   screens' price calls passed neither `iso` nor `year` into
   `MarketDesign.capacity_price_per_firm_mw_yr`, so the by-ISO gate fell
   through to the (off) scalar and the vintage anchor never resolved. Now the
   runner resolves `resolve_capacity_market_clearing(config, iso)` and all
   three screens thread `iso`/`year` (consulted only inside the curve branch).
   `tests/test_capacity_demand_curve.py::TestScreenSeamThreading`.
2. **PJM pre-CIFP vintage curve shapes from published rows only.** The RC-1B
   vintage table carried `demand_curve=()` for PJM 2021/22–2025/26 (flat
   anchors 83.5–117.4 $/kW-yr) — under the gate the probe would have paid a
   position-INDEPENDENT price *higher* than fixed mode in every hindcast year,
   reverting the mechanism it exists to test. The five RPM BRA Planning Period
   Parameters workbooks were intaken (committed under
   `data/raw/capacity-market/demand-curve/pjm/`), adding the published RTO
   Reliability Requirement, FRR-adjusted requirement, and EE-Addback rows.
   Finding: **VRR point UCAP levels ÷ (RelReq adjusted for FRR + EE Addback)
   reproduce PJM's own Manual-18 pct-of-requirement fractions to ≤0.1 % in
   every vintage** (2025/26: 0.98912/1.01583/1.06726 vs the committed M18 rows
   0.989/1.016/1.068), and the point prices are the filings' explicit
   1.5×/0.75×/0 × net-CONE construction (2025/26's own published 451.61/171.61
   $/MW-day). The five vintages now carry these published shapes — zero
   guessed formulas, zero fitted values (rule 13); reconciliation
   test-asserted against the datatype rows.
3. **Pass-2 restatement of HEAD-produced bundles.**
   `validate_capacity_prices.py` gains `--pass2-run ISO=RUN` (+ MISO's
   committed hindcast joins `HINDCAST_RUNS`) and `--pass2-adopted-basis`: a
   HEAD (post-N-5) ledger already records `accredited_firm_capacity_mw` in
   `reserve_margin`, so the legacy restatement double-derates it (~25 GW low
   on PJM); the flag reads the native adopted-basis firm back directly. The
   Pass-2 model-price column now prices each calendar year on its own curve
   vintage (`resolve_demand_curve_vintage`) — what the screens actually see.

LOYO note (rule 22): these changes alter **no keeper and no default path**
(byte-identical with the gate off — the entire backcast surface and the
production forecast path are untouched); they activate only under the probe
flag. No keeper verdict can flip, so there is no LOYO-scorable mechanism
change here; the probe legs themselves span all three train years.

**BEFORE-leg fidelity at HEAD.** MISO BEFORE reproduces the committed
2026-07-14 bundle event-for-event (all five years). PJM BEFORE reproduces the
committed p2c bundles except one 2,000 MW `gas_ct` entry in 2023 that no
longer clears — the N-5 payment-basis effect (CT pays on its 0.60 ELCC class
rating post-R4), i.e. the §1.5 interaction the plan said to measure, not a
regression. Headline retirement metrics are identical (PJM −63 %, 4.106 GW;
MISO −95 %, 0.784 GW).

## 1. PJM — the coupled system works, then overshoots (T-R1)

| leg | coal econ exits (GW, cum) | thermal exits (GW, cum) | recall >300 MW | false-retire raw / IS-2020 (GW) | wind / solar / gas_cc / storage adds (GW) | gas_ct adds (GW) |
|---|--:|--:|--:|--:|---|--:|
| BEFORE (HEAD) | 0.0 | 4.106 | 0 % (0/17) | 4.097 / 0.0 | 6.0 / 0.0 / 12.0 / 0.0 | 0.0 |
| curve-ON probe | **9.913** | 14.02 | **76 % (13/17)** | 7.125 / 3.028 | 6.0 / 0.0 / 8.0 / 0.0 | 8.428 (2.0 entry + 6.428 backstop) |
| actual | 6.885 | 11.121 | — | — | 1.619 / 13.066 / 8.525 / 0.283 | 0.447 |

Mechanism trace (evolution ledgers + Pass 2, adopted basis):

| cal yr | BEFORE pos | probe pos | year's own curve pays (probe) | auction cleared | probe events |
|---|--:|--:|--:|--:|---|
| 2022 (bridge) | — | prices 2021 pos 1.097 on 2021/22 curve (zero-cross 1.0741) → $0 | — | — | **3.48 GW coal economic exits** (first fossil economic exit in any capacity-market hindcast) + Byron/Dresden 4.10 GW announced (unchanged) |
| 2023 | 1.113 | 1.078 | $0 (past 2023/24 zero-cross 1.0655) | 12.5 $/kW-yr | 4 GW CC + 2 GW CT entry return |
| 2024 | 1.099 | **1.006** | 112 $/kW-yr | 10.6 | second coal wave **6.43 GW** |
| 2025 | 1.017 | **0.977** | 164.8 (cap plateau) | 98.5 | adequacy backstop builds **6.43 GW CT** (firm short of the FPR requirement) |

- The $0-at-long-position → GFC-uncovered → exits-resume → position-shortens →
  price-rises loop **closes end-to-end** — the §2.2 measurement this probe
  exists to take. Coal goes 0 → 9.9 GW (actual 6.9); recall 0 → 76 %;
  plant-exact recall 0 → 35 %; the gas_cc additions band flips to PASS (−6 %).
- **But the loop is underdamped**: the 2024 second wave (coal threshold = 1
  loss-year, D1 pending) pushes the position *through* the priced region in
  one step (1.078 → 1.006), and the 2025 backstop over-corrects with 6.4 GW of
  CT (the I12 de-firm→overshoot signature of plan §1.5). 2024 pays 112 $/kW-yr
  in a year the real auction cleared 10.6; 2025 lands at 0.977 vs the
  auction's 1.007 (miss 0.030, band ±0.028) *from the short side*.
- I5 (no retire-reenter) and I13 (no cobweb) **PASS on both legs** — the §2.2
  mass-wave risk gate holds at this window length; the overshoot is visible in
  the position trace, not (yet) as a sawtooth.

## 2. MISO — same physics, on the RC-1C seasonal RBDC grain (T-R2)

The registered MISO probe prices the screens on MISO's own **four-season RBDC
revenue sum** (RC-1C, landed mid-session; the leg was re-solved on it). The
PY2025-26 parameter set still serves every hindcast year hold-first (a single
seasonal vintage — the pre-RBDC vertical-curve era remains unrepresented, the
honest remainder of prereq 4a).

| leg | coal econ exits (GW, cum) | thermal exits (GW, cum) | recall >300 MW | false-retire raw / IS-2020 (GW) | wind / solar / gas_cc / gas_ct / storage adds (GW) | 2025 CO2 err |
|---|--:|--:|--:|--:|---|--:|
| BEFORE (HEAD = committed) | 0.0 | 0.784 | 0 % (0/17) | 0.0 / 0.0 | 12.0 / 6.0 / 9.0 / 0.0 / 0.0 | +14 % |
| curve-ON probe (SEASONAL) | **11.809** | **12.593 (−17 %)** | **76 % (13/17)** | **0.874 / 0.874 (PASS)** | 12.0 / **12.0** / 0.0 / 0.01 / 0.0 | **+5 %** |
| actual | 10.934 | 15.227 | — | — | 7.2 / 18.649 / 3.867 / 1.379 / 0.744 | — |

| cal yr | BEFORE pos | probe pos | seasonal RBDC pays (probe) | cleared (summer PRA) | probe events |
|---|--:|--:|--:|--:|---|
| 2022 (bridge) | — | prices 2021 pos 1.134 → $0 | — | — | **8.05 GW coal economic** + Palisades 0.77 announced |
| 2023 | 1.128 | 1.038 | $0 | 3.6 $/kW-yr | +6 GW solar (2nd tranche) |
| 2024 | 1.147 | **1.010** | $0 | 10.9 | second coal wave **3.76 GW** (vs 6.91 on the annual grain) |
| 2025 | 1.175 | 1.035 | 24.5 | **243.3 (at cap)** | backstop 0.01 GW CT (vs 0.64 annual) |

- The BLK-9 cliff breaks exactly as predicted: MISO coal (fixed-mode ratio
  1.26, the closest cliff) posts loss years the moment the long position
  zeroes the payment. The program's largest single capacity miss (coal 0 vs
  10.9 GW) closes to **+8 %** with recall 76 % and **false-retire 0.874 GW —
  band PASS in BOTH raw and IS-2020**.
- Thermal total lands at −17 % (residual = the non-coal fossil classes the
  screens still miss: gas_ct 2.4 / gas_cc 0.5 / oil 0.5 GW, all −100 % — their
  fixed-mode ratios were far above the cliff, so the curve alone does not
  reach them in-window at their 2–3-year thresholds). 2025 CO2 collapses
  **+14 % → +5 %** (T-R2c — the fleet error was most of the CO2 error).
- gas_cc additions fall +133 % → −100 % (0 GW, now 3.9 GW under actual — the
  responsive price relieves the entry over-fire and then some); solar rises
  6 → 12 GW (−68 % → −36 %, Δ-share −8.3 pp) purely through the price channel.
  The backstop fires only 0.01 GW (vs PJM's 6.4 — MISO's position never goes
  short). **Wind does NOT fall** (12 GW both legs): wind entry never sees the
  curve — VRE earns zero capacity revenue in the entry screen (BLK-7, §1.4
  term c) and the build sits at the queue-cap chunk (term e). That half of
  T-R2(b) fails and is routed, not tuned.
- The 2025 shortage still under-pays (24.5 vs 243 at cap — position 1.035 on
  the seasonal curve): with the instrument now seasonal, the residual is
  cleanly the **fleet path** (the model's 2025 position is long because the
  probe's exits, at +8 %, still leave more firm capacity than the real
  market's — plus the real 2025/26 auction's demand-side changes the
  hold-first single vintage cannot carry).
- **Grain sensitivity (annual-RBDC diagnostic solve of the same leg — labeled,
  not registered):** on the annual stand-in the same probe over-retired
  (coal 14.97 GW, +37 %; false-retire 4.03 GW FAIL; 2024 second wave 6.91 GW;
  backstop 0.64 GW) and over-paid 2024 (71 $/kW-yr vs 10.9 cleared). The
  seasonal grain's flatter shoulder-season revenue near 1.0 damps the second
  wave — the instrument's own grain materially changes the coupled dynamics,
  which is precisely why prereq 4a existed. PJM's overshoot (§1) is the same
  phenomenon still undamped by D1.

## 3. T-R scorecard (pre-registered bands, graded as written — never widened)

| ID | criterion (pre-registered) | measured | verdict |
|---|---|---|---|
| T-R1a | PJM coal `economic` recall > 0; cumulative coal exits ∈ [2, 14] GW (actual 6.9) | 9.913 GW, recall 76 % | **PASS** |
| T-R1b | PJM cumulative thermal exits ≤ 2× actual 11.1 = 22.2 GW | 14.02 GW | **PASS** |
| T-R1c | zero economic nuclear exits | 0 MW economic nuclear (both ISOs, every leg) | **PASS** |
| T-R1d | 2025-step restated position moves ≥ half the distance from 1.06 toward 1.007 | 1.017 (HEAD BEFORE, adopted basis) → **0.977**: through 1.007 and 0.030 past it — far more than half the distance, from either baseline (1.057 committed-restated or 1.017 HEAD-native) | **PASS, with overshoot** (see T-R4) |
| T-R1e | additions bands not degraded vs BEFORE — solar/wind/gas_cc/storage each no further from actual | solar 0→0, wind 6.0→6.0, gas_cc 12→8 (+41 %→−6 %), storage 0→0 | **PASS** (gas_ct — not in the enumerated set — degrades 0→8.43 GW: the backstop over-fire, → BLK-10) |
| T-R2a | MISO coal recall > 0; cumulative ∈ [3, 22] GW (actual 10.9) | **11.809 GW (+8 %)**, recall 76 %, false-retire 0.874 GW PASS (raw + IS-2020) | **PASS** |
| T-R2b | MISO gas_cc AND wind additions fall vs +133 %/+67 % | gas_cc +133 %→−100 % ✓ (falls, to 3.9 GW under); wind 12 GW→12 GW ✗ (+67 % unchanged) | **FAIL (wind half)** — mechanism §4.3 |
| T-R2c | MISO 2025 CO2 error sign moves from +14 % toward 0 (report-only) | +14 % → **+5 %** | **PASS** (report-only) |
| T-R4 | PJM 2025 position within ±0.028 of 1.007; long years (2021/23/24) OUT of the priced region | 2025: 0.977 → |Δ| = 0.030 (**miss by 0.002, from the short side**); 2021: 1.097 OUT ✓; 2023: 1.078 OUT ✓ ($0 on its own vintage; also past the 2026/27-shape zero-cross); 2024: **1.006 IN the priced region** (era curve pays 112 $/kW-yr; real market cleared 10.6) | **FAIL** — mechanism §4.1 |
| T-R5-inv | I5 (no retire-reenter) + I13 (no sawtooth) PASS on EVERY leg | PASS on all four legs (I3/I7/I9/I12 flags are pre-existing on the committed sidecars: PJM 2021 base-year ledger artifact, MISO storage ε-degeneracy, and the I12 band being stale against N-5-basis reserve margins) | **PASS** |
| T-R7 | nuclear guard, every probe leg | economic-channel nuclear = 0 everywhere; announced-channel: Byron/Dresden 4.097 GW → IS-2020 `reversal_exposure` (raw false-retire), Palisades 0.768 GW → correct recall (±1 yr) — both exactly as RC-0B §c.5 pre-registered | **PASS** |

Raw vs IS-2020, side by side (RC-0B §c.5 — quoting only one is scoring abuse):

| leg | false-retire raw (GW) | false-retire IS-2020 (GW) | reversal exposure (GW) |
|---|--:|--:|--:|
| PJM BEFORE | 4.097 | 0.0 | 4.097 |
| PJM probe | 7.125 | 3.028 | 4.097 |
| MISO BEFORE | 0.0 | 0.0 | 0.0 |
| MISO probe (seasonal) | **0.874 (PASS)** | **0.874 (PASS)** | 0.0 |

PJM's probe IS-2020 false-retire (3.0 GW) is entirely the coal overshoot
(+44 %) — **PJM's gate item 4 "strictly improves false-retire" clause stays
OPEN**. MISO's seasonal probe holds false-retire to 0.874 GW (7 % of model,
band PASS) — its item 4 blocker is only the raw-vs-BEFORE strictness
(0 → 0.874 GW is technically a degradation against a leg that retired
nothing at all; against any non-degenerate baseline it is a pass-quality
number).

## 4. Mechanism hypotheses for every FAIL (module-named), and routing

1. **Coal-wave overshoot (PJM false-retire raw 7.1/IS 3.0 GW; T-R4
   2024-in-region; T-R1d/T-R4 2025 short-side miss; on MISO the seasonal
   grain damps it to 0.874 GW — the annual-grain diagnostic showed 4.0).**
   `model/capacity.py::apply_economic_retirements` retires the entire
   loss-cohort the year its counter hits `retirement_years_coal = 1` — a value
   RC-0B §a.4 graded **MIS-IDENTIFIED (below its measured ≥ 2–3-year
   announced-to-deactivation floor)** — and no deactivation-queue rate damps
   the wave (`staged_oversupply_thinning` default-off; rule 19 says the
   threshold and the queue are one phenomenon, D1's exact subject). Both
   waves (2022, 2024) are 1.7–2.2× the largest real single-year exit, so the
   position steps over the priced region instead of walking down the curve.
   **Routing: D1 Option B (coal = 3, the data-identified value — RC-0B §d) is
   the named, owner-pending fix; per rules 1/13 it is NOT adopted here and
   its adoption must cite only the §a.3 lag table, never these residuals. A
   D1-adopted probe re-run is the first action item for RC-2B's evidence
   base.** The probe *quantifies* what D1 re-baselines: both BEFORE legs are
   D1-invariant (they retire no coal at any threshold), so only the probe
   legs re-run.
2. **PJM backstop over-fire (gas_ct +1784 %, 6.43 GW `gas_ct_adequacy_2025`).**
   The reserve-margin backstop's need-sizing
   (`model/capacity.py` adequacy step 6) rebuilds the full one-pass deficit in
   a single year against the same requirement whose breach the undamped wave
   just caused — the §1.5 de-firm→overshoot signature, now measured in a
   capacity-market ISO. **Filed as the plan-§2.4 new gap-register row BLK-10**
   (the one new ID this lane creates), with this leg as evidence. Note the
   two failures are coupled: damping the wave (D1) shrinks the deficit the
   backstop over-corrects, so BLK-10 must be re-measured after D1 lands
   before any backstop-sizing work is chartered.
3. **MISO wind non-response (T-R2b wind half).** The entry screen credits VRE
   zero capacity revenue (`apply_economic_new_entry` prices only thermal
   candidates through `capacity_revenue_per_mw_yr`; BLK-7), so the curve
   cannot move wind either way, and the 4 GW/yr queue-cap chunk
   (`QUEUE_CAP_PER_TECH_GW`) keeps it pinned. **Routing: RC-0C's §1.4 terms
   (c) and (e) — no change here.**
4. **Solar still short (PJM 0 GW; MISO −36 %).** BLK-8, owned by RC-0C. New
   evidence from this probe: MISO solar rose 6 → 12 GW purely from the price
   channel (post-exit tighter prices), supporting §1.4 term (a) sensitivity;
   PJM solar stayed at 0 — term (a) alone is insufficient there.
5. **MISO 2025 shortage under-priced (24.5 vs 243 at cap) even at seasonal
   grain.** With the instrument seasonal (RC-1C), the residual is the fleet
   path — the probe's +8 % coal exits still leave the 2025 position at 1.035
   (long side of the curve) where the real market was short — plus the
   hold-first single PY2025-26 vintage cannot carry the real auction's own
   demand-side moves. Fleet-side remainder routes with §4.1/§4.2; the
   vintage-history half is the remaining RC-0A/RC-1C intake gap (pre-RBDC
   era).
6. **Pre-existing scorer/invariant artifacts (not this probe's):** the PJM
   2021 base-year ledger writes a placeholder reserve margin (I3/I7 flags,
   identical on the committed sidecars); I12's [13.8 %, 28.7 %] band predates
   the N-5 basis and now flags every adopted-basis margin; MISO I9 storage
   ε-degeneracy is on the committed sidecar byte-for-byte. Worth a small
   scorer-lane cleanup ticket; none blocks this measurement.

## 5. §2.1 flip-gate item scorecard (the RC-2B input)

| # | Gate item | PJM | MISO |
|---|---|---|---|
| 1 | Basis (published accreditation) | **PASS** (N-5 R1–R4, closed) | **PASS** (keep-and-verify per plan; EFORd pairing consistent) |
| 2 | Instrument (per-delivery-year published curve) | **PASS — strengthened this session**: 2021/22–2025/26 vintages now carry published shapes (workbook-reconciled ≤ 0.1 %); 2026/27 P-2A-validated | **PASS-leaning-OPEN** — seasonal RBDC grain landed (RC-1C) and the probe priced on it; the residual instrument gap is the single hold-first PY2025-26 vintage (pre-RBDC era unrepresented — RC-0A intake item 3) |
| 3 | Position (in priced region when the market priced, out when it didn't) | **OPEN** — measured: BEFORE 1.017–1.113 (never in region, pays $0 incl. the 2025/26 shortage) → probe 0.977–1.078 (converges through the region; 2024 in-region a year early; 2025 0.030 short of the 1.007 target vs the ±0.028 band). Blocker: §4.1 wave damping (D1) + BLK-10 backstop | **OPEN** — BEFORE 1.128–1.175 (never priced) → seasonal probe 1.010–1.038: long years stay out of the priced region ✓, but the 2025 shortage year also stays out (pays 24.5 vs 243 at cap) — the position path is one-sided. Blockers: D1 re-probe + the fleet-path residual (§4.5) |
| 4 | Skill (recall & false-retire strictly improve; additions not degraded) | **OPEN** — recall 0 → 76 % ✓, enumerated additions bands not degraded ✓ (gas_cc improves to PASS), but false-retire degrades 4.1 → 7.1 raw / 0 → 3.0 IS-2020 (coal overshoot) and the backstop CT is a new miss | **OPEN-leaning-PASS** — recall 0 → 76 % ✓, coal +8 % ✓, false-retire 0.874 GW band-PASS (raw + IS-2020) ✓, CO2 +5 % ✓, solar improves −68 %→−36 % ✓, gas_cc falls to −100 % (3.9 GW under — over-corrected); wind unchanged; the only strict degradation is 0 → 0.874 GW against a nothing-retires baseline |
| 5 | Plumbing (per-ISO gate) | **PASS — end-to-end verified this session** (the RC-1B seam existed but was runner/screen-inert; completed + tested; probe ran on `capacity_market_clearing_by_iso={'PJM': True}` with the scalar off and no cross-ISO leak) | **PASS** (same seam, `{'MISO': True}`, composed with RC-1C's seasonal branch + eligibility gate) |

**Bottom line for RC-2B:** the circularity is broken and the coupled system
is qualitatively right — exits resume at $0, the position walks into the
priced region, entry and CO2 respond in the right direction, and on MISO's
seasonal grain the retirement record is close to pass-quality (coal +8 %,
false-retire 0.874 GW PASS). The flip stays gated on position/skill (items
3–4) in both ISOs, with ONE shared dominant blocker: the undamped exit waves
(`retirement_years_coal = 1`, mis-identified per RC-0B) and, on PJM, the
coupled backstop over-fire (BLK-10). The identified, owner-pending D1
Option B is the single change most likely to move items 3–4 to PASS; it must
be adopted on its identification (RC-0B §a.3), never on these residuals, and
re-probed (probe legs only — the BEFORE legs are D1-invariant). The MISO
annual-vs-seasonal sensitivity (§2) is direct evidence that instrument grain
shapes the coupled dynamics — the same reason PJM's D1 re-probe should run on
the era-correct vintage shapes landed here.

## 6. Artifacts

- Runs (forecast-validation dashboard, `docs/codebase-site/forecast-validation.html`):
  `pjm-2021-2025-realized-cmc-before` / `pjm-2021-2025-realized-cmc-probe` /
  `miso-2021-2025-realized-cmc-before` / `miso-2021-2025-realized-cmc-probe`
  (sidecars under `frontend/data/hindcast/`; bundles under `results/hindcast/`).
  **Nothing touches the backcast dashboard.**
- Reports: `docs/hindcast-reports/{pjm,miso}-2021-2025-realized-cmc-{before,probe}-2026-07-16.md`
  (each carries its raw + IS-2020 tables and its A/B context note).
- Pass-2 restatements: `scripts/validate_capacity_prices.py --pass2-run
  <ISO>=<bundle> --pass2-adopted-basis` (per-delivery-year vintage pricing);
  committed-bundle defaults unchanged.
- Code/intake commits (each default-byte-identical, test-asserted): seam
  threading + per-ISO runner gate; PJM planning-parameter workbook intake +
  published vintage shapes; Pass-2 override/adopted-basis machinery.
- Gap register: **BLK-10** filed (backstop/additions overshoot);
  BLK-8/BLK-9 rows gain probe evidence (BLK-9's mechanism is now
  demonstrated-resolvable by the CR chain: fossil exit is no longer
  arithmetically impossible under the curve).

*Produced 2026-07-16 (RC-1A). Four hindcast legs solved (2021/2023/2024/2025
each; 2022 bridged, never solved — rule 22); no holdout year touched; no
backcast artifact touched; no default changed; every landed change cited and
byte-identical with the gate off. ⛔ gate input for RC-2B.*
