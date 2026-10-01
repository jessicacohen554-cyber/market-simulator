# FINDING — nyiso-95: the TSA downstate transfer derate is NOT identifiable from published data (ex-ante, no solve)

**Date:** 2026-07-28 · **Lane:** NYISO C3c (sole determination blocker) ·
**Charter:** queue item 1b, `docs/mechanism-testing-matrix.md` §5.5 ·
**Keeper (unchanged):** `2026-07-28-nyiso-92-hydro-envelope`
(bundle `results/calibration/nyiso92_hydro_envfloor`, DETERMINATION NOT-YET)

**Verdict: `tsa_transfer_derate` → NYISO `G` (governance-refused), ex ante, NO SOLVE
SPENT.** The charter's STEP-1 branch point is hit — but through a different door than
the charter anticipated. The **event set is fine**: it is published, exact, already
in-repo, and *already wired into the keeper*. What cannot be identified is the
**derate magnitude**. Every route to a MW number is either a fitted scalar
(rule 21 `[R-DOF]`), a measured *outcome* fed back as an input (rule 13
`[R-MEASURED]`), or a quantity defined on a boundary our reduced network does not
carry (rule 14 `[R-ACCURATE]` misalignment clause).

No solve was spent, no run registered — same disposition and same precedent as
nyiso-93 (INERT ex-ante) and nyiso-94 (REFUSED ex-ante).

---

## 1. Two charter premises are factually wrong — both in the model's favour

The §5.5 queue entry for item 1b carried two caveats. Both are incorrect, and
correcting them is half this finding's value.

> "Caveats: needs a TSA-history intake that does not exist in-repo"

**A TSA history has existed in-repo since 2026-07-10.**

| | |
|---|---|
| **Source** | NYISO MIS **P-35 Real-Time Events**, `mis.nyiso.com/public/csv/RealTimeEvents/` |
| **Fetcher** | `scripts/fetch_nyiso_operating_events.py` (hard-capped at 2026-06-30) |
| **Raw** | `data/raw/NYISO-AS/requirements/realtime-events/NYISO_realtime_events_<year>.csv` |
| **Clean** | `nyiso-operating-events` datatype, `event_type = thunderstorm_alert` |
| **Vintage** | intaken **2026-07-10** under session-logged owner authorization; coverage **2018-01 → 2026-06** |
| **Authorization** | `docs/out-of-sample-results-2026-07.md` §1.2 (rule 22 out-of-training clause) |

The feed carries the alert state directly and unambiguously — three message
forms, no inference:

```
03/13/2023 20:00:00   **System now operating in thunderstorm alert.**
03/14/2023 00:00:00   Start of day thunderstorm alert state is ACTIVE
03/14/2023 18:25:00   **System no longer operating in thunderstorm alert.**
```

> "The model has no TSA representation"

**The model already represents TSA's one *published, quantified* consequence.**
NYISO's Locational Reserve Requirements posting specifies that a TSA **zeroes**
the NYC 10T/30T and SENY 30T locational reserve requirements. That rule is
hand-transcribed in-repo as the `tsa_reduced_to_zero` column of
`data/raw/NYISO-AS/requirements/nyiso_locational_reserve_requirements.csv`, and
it is **live in production**:

```
scripts/data/derive_nyiso_reserve_requirements_hourly.py::build_tsa_windows   (line 120)
  → pairs the P-35 thunderstorm_alert start/end transitions into windows
  → derive_year() applies  series *= (1 - tsa_fraction)  where tsa_reduced_to_zero  (line 325)
  → NYISO_reserve_requirements_<year>.csv
  → ScenarioConfig.nyiso_dynamic_reserve_requirements
```

and `nyiso_dynamic_reserve_requirements = True` **on the nyiso-92 keeper**
(verified in `results/calibration/nyiso92_hydro_envfloor/run_config.json`).

So TSA is not an unmodelled phenomenon. Its published half is armed. The
*transfer-derate* half is what is missing — and §2–§4 are why it stays missing.

### 1.1 The reconstructed event set corroborates the IMM independently

Windows reconstructed from the raw feed (probe pairing, consistent with the
production `build_tsa_windows` logic):

| year | spans | TSA-active hours | % of year | share in h13–21 | share May–Sep |
|---|---|---|---|---|---|
| 2023 | 32 | 187 | 2.1 % | 61 % | 75 % |
| 2024 | 30 | 272 | 3.1 % | 55 % | 90 % |
| 2025 | 18 | 477 | 5.4 % | 42 % | 97 % |

The SOM says TSA events concentrate in "the afternoon hours from 13 to 21 during
the months of May through September" (2025 SOM p.50). The independently
reconstructed set agrees. **The event set is not the problem.** We hold something
strictly better than the IMM's own instrument: the IMM built a weather classifier
because the *day-ahead* market cannot see the future; a backcast has the realized
events.

---

## 2. The derate is NOT in NYISO's published interface limits — measured, well-powered, null

The charter asked for the magnitude "from NYISO's published interface limits
rather than the SOM's '1-2 GW' prose." That measurement was made, on the
**MIS P-32 Interface Limits and Flows** posting
(`data/raw/NYISO/interface-flows/NYISO_interface_flows_hourly_<year>.csv.gz`,
hourly `positive_limit_mw` / `negative_limit_mw` / `flow_mw`, 18 interfaces).

**Identification.** A raw TSA-vs-non-TSA mean is confounded: TSA fires on
summer-peak afternoons, when NYISO posts its *highest* limits anyway. (Indeed the
naive comparison shows UPNY CONED **+447 / +191 / +347 MW** *higher* during TSA
hours.) The clean test is the discontinuity at the declaration instant, which
holds day, season and load regime fixed: `limit[h+1] − limit[h−1]`, pooled over
all 83 non-carryover TSA starts in 2023–2025.

| interface | n | Δ posted limit | events with \|Δ\| > 100 MW |
|---|---|---|---|
| **SPR/DUN-SOUTH** | 83 | **+0.0 MW** | **0 %** |
| **TOTAL EAST** | 83 | **+0.0 MW** | **0 %** |
| **UPNY CONED** | 83 | **−23.9 MW** | 10 % |
| CENTRAL EAST - VC | 83 | −5.9 MW | 17 % |
| MOSES SOUTH | 83 | −1.8 MW | 1 % |
| *(all 18 interfaces)* | 83 | *no interface exceeds \|32\| MW* | ≤ 17 % |

Per-year on UPNY CONED — the ConEd-facing interface — the mean Δ is
**−40.9 / −19.5 / −4.5 MW**, the **median is exactly 0.0 in all three years**, and
only 19 % / 17 % / 10 % of events move it down at all.

**The null is not a power failure.** The same posting demonstrably moves by
GW-scale amounts when something real happens:

| UPNY CONED `positive_limit_mw` | 2023 | 2024 | 2025 |
|---|---|---|---|
| distinct posted values in the year | 138 | 142 | 137 |
| std of hour-over-hour change | 83.0 MW | 76.0 MW | 82.9 MW |
| **max \|1-hour change\|** | **1,565 MW** | **835 MW** | **910 MW** |
| full-year range | 2,945 MW | 2,646 MW | 2,440 MW |

A 1–2 GW step is well within what this feed resolves, on this interface, in
these years. It is not there at the TSA instant. **The derate magnitude is not
published in the limits feed.**

---

## 3. The SOM's "1–2 GW" is not an interface rating — and the real constraint is off our boundary

Reading the source the charter cites (2025 SOM §D, pp. 49–51; in-repo at
`data/raw/NYISO/NYISO-2025-SOM-Report__5-19-2026-final.pdf`) resolves why:

> "These events, known as Thunderstorm Alerts (TSAs), routinely reduce
> upstate-to-downstate transfer capability by approximately 1 to 2 GW **relative
> to day-ahead scheduled levels**" — 2025 SOM p.50

The quantity is defined **against the DA schedule**, not against a physical
interface rating. It is also a range, not a value.

And the constraint itself is a **line-level multi-contingency**, not an interface
derate (2025 SOM §V.C.2, "TSA-related Congestion Residuals in July 2025", p.80):

> "during Thunderstorm Alert (TSA) conditions, the system must be operated more
> conservatively, requiring certain facilities to be **secured against multiple
> contingencies** in the real-time market."
>
> "six transmission lines carry the majority of flows from Zone G to Zones H and
> I. **Line #1, the Lovett-Buchanan 345 kV line, is the limiting facility** for
> this TSA constraint. Lines #2, #3, and #4, the two Pleasant Valley-Wood St.-
> Millwood 345 kV lines and one Pleasant Valley-Wood St.-Pleasantville 345 kV
> line, are **contingent elements**. Lines #5 and #6 … **are not part of the TSA
> constraint itself but are key components of the UPNY-Con Ed interface.**"

Three consequences, each independently fatal to a link-TTC derate:

1. **The IMM explicitly separates the TSA cutset from the UPNY-Con Ed interface.**
   Derating our `Capital_Hudson → Lower_Hudson` link (the model's UPNY-SENY
   proxy, TTC 5,150 MW) would be derating the wrong object.
2. **It is one of six parallel paths our five-zone network collapses into one
   link.** This is verbatim rule 14 `[R-ACCURATE]`'s named misalignment
   exception: *"a single GTC that is one of several parallel paths our reduced
   network collapses into one link."* Rule 14 prefers a **reconciled** version of
   real data over a guess — but reconciling "Lovett-Buchanan limit under
   contingency CE40" into "MW off the G→H/I link" requires the line's rating, its
   OTDF for the G→H/I transfer under CE40, and the base-case loading. **NYISO
   publishes none of the three at that grain, and none is in-repo.**
3. **Even the IMM has no published magnitude.** Its forecast model (Appendix
   III.J, pp. A-71–A-73) is a logistic regression on six ERA5 weather variables
   (CAPE, K-Index, Lifted Index, RH-500, V-500, VV-850), trained on 2023–2024,
   AUC > 0.93 on 2025. It predicts **P(TSA occurrence)** — a binary — and the
   congestion cost is then measured *ex post* from realized shadow prices. There
   is no published magnitude model anywhere to adopt.

---

## 4. The one real measured signal — and why it is a validation target, never an input

TSA does produce a measured, statistically strong **flow** response. Difference-
in-differences at the declaration instant (`flow[h+1] − flow[h−1]`, net of the
same 2-hour drift at the same hour-of-day and month on TSA-free days):

| interface | 2023 | 2024 | 2025 |
|---|---|---|---|
| **UPNY CONED** | −57 MW (z −0.65) | **−412 MW (z −5.81)** | **−326 MW (z −3.87)** |
| **SPR/DUN-SOUTH** | −36 MW (z −0.57) | **−330 MW (z −5.25)** | **−279 MW (z −4.40)** |
| TOTAL EAST | −80 MW (z −0.92) | −205 MW (z −1.99) | −235 MW (z −1.95) |
| CENTRAL EAST - VC *(placebo)* | −27 MW (z −0.82) | −25 MW (z −0.56) | −143 MW (z −2.42) |

The effect is localized on the ConEd-facing interfaces and largely absent on the
upstate placebo — the signature is right. But two things follow, and both point
away from the lever:

**(a) It cannot be used as an input.** Realized flow is a market *outcome* that
already embeds the dispatch response. Rule 13 `[R-MEASURED]` forbids exactly this
— feeding a measured outcome back to force the backcast, the same class as
pinning a unit to its observed CEMS generation. It is a legitimate **validation
target** for any future TSA mechanism, and it is recorded here for that purpose.

**(b) It reframes the "1–2 GW".** The realized physical reduction is **~280–410
MW** on the ConEd-facing interfaces in 2024–25, and statistically
indistinguishable from zero in 2023 — roughly **a quarter of the low end** of the
IMM's stated range. Read together with the SOM's own wording ("relative to
day-ahead scheduled levels"), the 1–2 GW is predominantly the **DA-vs-RT schedule
gap**, not a physical capability cut.

That has a structural consequence the charter anticipated in principle:

> *charter:* "Note this is an RT-side mechanism scored on a DA-expressible C3c:
> argue it on the RT side, do not smuggle it in as a DA constraint."

The model has **no DA/RT split at all** — P1 is a single clearing (CLAUDE.md
"Dispatch & Commitment"). There is no "day-ahead scheduled level" in our
formulation for a derate to be measured *relative to*. So the mechanism **as the
IMM defines it is not expressible in our formulation**, independently of the
magnitude problem. Arguing it "on the RT side" is not available either: our P1 is
the only side there is.

---

## 5. Why this stops here (rule 1 `[R-STRUCT]`, not the residual)

Enumerating every route to a MW number, and what each one violates:

| candidate magnitude | source | disposition |
|---|---|---|
| posted P-32 limit change at TSA onset | measured | **null** (§2) — 0.0 MW on the two ConEd interfaces, well-powered |
| a point inside the IMM's "1–2 GW" | 2025 SOM prose | **rule 21 `[R-DOF]`** — a range is not a value; picking a point and evaluating it on C3c *is* the fitted scalar. Also rule 5 `[R-NO-MAGIC]`: no primary-source citation for any specific value |
| observed flow reduction (−280…−410 MW) | measured | **rule 13 `[R-MEASURED]`** — a realized market outcome, not a capability; no forward analogue |
| N-1-1 share of the link TTC (e.g. TTC ÷ 6 lines) | constructed | **rule 5 + rule 21** — "six lines carry the majority" is prose, the lines are not equal-rated, and 1/6-vs-1/5-vs-largest-element is a modelling choice that would inevitably be selected on C3c. Compounded by the link's own TTC being Tier-3 seeded (`iso_configs.py`: *"Tier 3 (calibration) — verify against NYISO operating-limit postings"*) |
| Lovett-Buchanan rating × OTDF under CE40 | **the correct reconciliation** | **not published**, not in-repo (§3) |

A mechanism whose sole free parameter must be fitted **cannot carry a DOF ledger
entry** (rule 21). Rule 1 `[R-STRUCT]` is explicit that one must "never reach the
right number through a mechanism that isn't real (a fitted adder, a load proxy, a
haircut tuned to the residual)" — and C3c is precisely the residual a TSA derate
would be tuned against. Spending a three-year LP solve to select that scalar is
the thing the charter's branch point exists to prevent.

**The keeper is unchanged.** No config field was added, so rule 28(c) does not
bind; the matrix row is added under 28(b) as the adjudicating session.

---

## 6. What would re-open this (new evidence required)

Any ONE of the following makes this identifiable, and only these:

1. **NYISO publishes the TSA constraint limits themselves** — the as-enforced
   RT constraint set (limiting facility, contingency, MW limit) at hourly or
   5-minute grain. This is a NYISO Market Operations data request, the same
   channel already logged as open item **B1** in
   `data/raw/NYISO-AS/requirements/README.md` ("continuous as-enforced
   requirement series as scheduled into RTD/RTC").
2. **Line ratings + OTDFs for the Zone G→H/I 345 kV group** under the named TSA
   contingencies (CE40 and siblings), enabling the rule-14 *reconciliation* of a
   line-level limit onto the collapsed link.
3. **A DA/RT split in the LP.** If the model ever clears DA and RT separately,
   the IMM's "1–2 GW relative to day-ahead scheduled levels" becomes a directly
   expressible quantity. This is a formulation change far beyond a lever, and is
   noted only to mark where the number would become meaningful.

**Do NOT re-open by:** deriving the derate from the observed LBMP, the observed
flow, the DA–RT price spread, or the C3c residual; or by adopting a point value
from the IMM's prose range. Those are the refused paths, and they are refused on
governance, not on fit.

## 7. Standing notes carried forward

- NYISO has **no measured sub-5-day availability channel** (nyiso-93) — do not
  attribute a short-duration NYISO tightness miss to fleet availability.
- NYISO's DA market is systematically **shallower** than RT (DA book ~0.85 GW
  below RT load; IMM: DA net scheduled load ≈96 % of actual peak, 2025 SOM p.47).
  Any future NYISO DA-side lever starts from **under**-scheduling, not PJM's
  over-scheduling premise. §4 above is the same fact seen from the congestion
  side.
- C3c remains **roof-blocked**, not tightness-blocked (nyiso-94): all five
  mainland zones share one max dual (149.9 / 194.5 / 255.1), 0 h > $258, zero
  load-shed slack in all three years, and every model > $300 hour is Long Island.
  §2's null means TSA was never going to reach that roof either — it is not a
  tightness lever the model was missing.

## 8. Reproduction

Probe scripts (session scratch, not committed — they read only committed raw
data and the committed curation module):

- event-set reconstruction + naive TSA-vs-non-TSA limit comparison
- declaration-instant event study over all 18 interfaces × 3 columns
- limit-feed power characterisation
- difference-in-differences flow response with the CENTRAL EAST placebo

All four import `build_events_frame` from
`scripts/data/curate_nyiso_reserve_requirements.py` (the production parser — no
re-implementation of the timestamp/pairing logic) and read
`data/raw/NYISO/interface-flows/*.csv.gz` directly.
