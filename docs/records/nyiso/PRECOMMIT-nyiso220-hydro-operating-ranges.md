# PRECOMMIT nyiso-220 — the licensed operating range, the instrument that sets it, and the period length it identifies

**Session:** nyiso-220, NYISO `backcast-calibration` lane. **Branch:**
`claude/nyiso-hydro-operating-ranges-4jfj0b`, on `main` at `7486cb9b`. **Date:** 2026-09-08.
**Keeper:** `2026-09-07-nyiso-213-summer-seam` — **to be left untouched.**
**ZERO LP planned.** Nothing to be armed, screened, solved or registered; no `ScenarioConfig` field;
no `src/market_sim/` change; no marker moved; no matrix cell letter changed; no held-out year spent.

**This document is committed and pushed BEFORE any substantive document content is read and before
any number below is measured.** §1 discloses what was already in hand (rule 29 step 0, which
legitimately precedes a PRECOMMIT). §§3–4 are the predictions. §5 is the outcome partition.

---

## 0. Scope discipline, stated before anything else

**There are NO in-sample rubric failures for NYISO.** The keeper reads **CALIBRATED**, grade 7/8,
**zero failing criteria** across 2023–2025, C3c the lone ledgered caveat. The only failing cells in
the NYISO record are on the **2022 validation holdout**, and rule 22 `[R-HOLDOUT]` forbids targeting
them: 2022 **motivates, never gates, and identifies nothing**.

**This session's object is STRUCTURAL and is not a rubric criterion at all** — there is no hydro row
in `fuelRows` and no hydro record in any C-criterion. I am not manufacturing a failure to justify
the work, and no prediction below is a prediction about a price residual.

**No held-out year is spent.** Nothing here reads out-of-training model output, computes a score for
one, or solves/registers anything.

**Adjudicated cells are not re-opened:** `hydro_ror_split` **G**, `hydro_budget_nameplate_aware`
**I**, and the three armed keeper cells (`hydro_dispatch_envelope` **K**, `hydro_min_flow_floor`
**K**, `nyiso_hydro_reserve_eligible` **K**) are all left as they are.

## 1. Step-0 disclosure — what is already in hand, before predictions

**(a) Committed from nyiso-219, re-used and NOT re-derived:** the pondage-duration bound
(72.01 % of scored fleet MW cannot hold one day of its own full output; Robert Moses Niagara
**0.244 h**; St. Lawrence **73.07 h**), the FERC licence index (152 plants, 97.82 % of fleet MW,
111 dockets), the NID intake, HILARRI, ORNL EHA, and the daily-driver closure (flow r 0.243,
climatology r 0.031).

**(b) The route census, re-measured at THIS container today, before predictions.** All four routes
the handoff named were re-tested, plus four the handoff did not:

| route | outcome at this container |
|---|---|
| `www.ferc.gov`, `cms.ferc.gov` | **403** with a browser `User-Agent` — reproduces nyiso-219 |
| `elibrary.ferc.gov` (SPA shell) | **200**, 22,464 bytes — byte-size reproduces nyiso-219's shell exactly |
| `eLibrary/api/search`, `/api/v1/search` | **200 / 22,464** — the SPA catch-all, exactly as nyiso-219 found. Confirmed, not re-discovered |
| pre-pinned Chromium | **not testable here** — the `playwright` Python package is absent from this env and `playwright install` is forbidden. **Reported as untested, not as failed** |
| **`WebFetch` on `www.ferc.gov`** *(route nyiso-219 did not have)* | **403** — does not bypass FERC's edge |
| generic egress control (`example.com`) | **200** — egress is healthy; the 403 is FERC's own edge |
| `ijc.org`, `www.ijc.org/en/loslrb`, `nypa.gov`, `govinfo.gov`, `loc.gov`, `glerl.noaa.gov` | **200** |
| `www.usace.army.mil` | 403 |

**(c) A NEW and more precise FERC negative, measured today.** nyiso-219 concluded eLibrary has "no
public API". That is nearly right but imprecise, and the precise version is worth recording so no
future session re-spends: the SPA's own config at
`elibrary.ferc.gov/eLibrary/assets/config/app-settings.json` (HTTP 200) declares
`"apiUrl": "/eLibraryWebAPI/api/"` — **a real ASP.NET Web API base that returns genuine JSON error
bodies, not the SPA catch-all.** The app's compiled chunks name its endpoints exactly
(`Search/GeneralSearch`, `Search/AdvancedSearch`, `Docket`, `Document`, `File`,
`DocFamily/GetDocFamily`) with full request payloads. **But the search controllers are not
deployed there:** `Search`, `Document` and `DocFamily` all return **404**, while `Docket` returns the
ASP.NET scaffold `["value1","value2"]` for *any* id and `File` returns empty — i.e. stubs, not a
working service. **The API route is therefore a characterized dead end, not an unexplored one.**
*(Also recorded so it is not re-chased: the `"/api/v2/"` string in the main bundle is **Datadog RUM
telemetry** (`ddforward`), not FERC's API — the same class of false positive nyiso-219 hit.)*

I did **not** attempt to defeat FERC's bot protection, per the standing rule that an
organization/edge 403 is reported, not worked around. Reading a site's own published config and
compiled bundle to find its documented endpoints is ordinary use of a public site; the 403 hosts
were left alone.

**(d) What this means for the plan.** FERC document text is **not automatically retrievable from
this container**. The instrument question is therefore not a nicety — it decides whether this
session has a corpus at all, because `ijc.org` **is** reachable where FERC is not.

## 2. The two documents that matter, restated

| plant | MW | % fleet | cum % | docket | NID pondage upper bound |
|---|---:|---:|---:|---|---:|
| Robert Moses Niagara | 2,429.1 | 51.89 | 51.89 | **P-2216** | **0.244 h** |
| Robert Moses St. Lawrence | 912.0 | 19.48 | **71.38** | **P-2000** | 73.07 h |

Both are **international boundary-water** projects. That is the whole reason the instrument question
must be settled before a corpus is chosen.

## 3. PREDICTIONS — sign and magnitude, written before measurement

**P1 (instrument, my preferred reading).** For **both** dominant projects, the quantity that bounds
inter-day energy movement — the water available and the headpond operating band — is set by an
**international instrument** (for P-2216 the 1950 Niagara Treaty and the International Niagara Board
of Control; for P-2000 the IJC Orders of Approval for Lake Ontario–St. Lawrence outflow, as
supplemented by Plan 2014), **not** by a numeric article of the FERC licence, which I predict defers
to or incorporates the international instrument rather than restating a band.
**Falsifier, stated in advance:** if a retrieved FERC licence states a numeric forebay/headpond
elevation band for either project **and** the international instrument does not, **P1 is WRONG** and
FERC is the correct corpus — in which case this session's honest result is (b), a negative, because
§1(c) says I cannot fetch FERC here.

**P2 — THE PREDICTION THAT HURTS MY PREFERRED ANSWER.** I predict the international instruments
specify a **level** band (elevation, metres) and a **flow** regime (cfs/m³s⁻¹), and **NOT a usable
volume** — and that converting a level band into the volume a period length needs requires a
**stage–storage relationship that is not published in the same instrument.** I put
**P(convertible to a per-plant volume for Niagara) < 0.5**, i.e. **more likely than not that my
preferred outcome (a) FAILS for the single largest plant in the fleet**, landing O3/O5 rather than
O1/O2. I am recording this because it is the way this session most plausibly falls short, and I do
not want to be able to discover it only after the fact.

**P3 (magnitude consistency, a two-sided check I cannot win by choosing).** A licensed operating
range is a **band inside** the full reservoir volume, so any period length derived from it must be
**≤ the NID full-volume bound already measured**:
* Niagara (2693): derived length **≤ 0.244 h** on NID's head proxy, **≤ ~0.75 h** on the 3× head
  correction nyiso-219 already flagged as the proxy's error direction;
* St. Lawrence (2694): derived length **≤ 73.07 h**.

**If a retrieved instrument implies a LONGER period than these bounds, then one of the two
measurements is wrong**, and **that contradiction is the finding** — reported as a contradiction. I
do not get to keep the convenient one.

**P4 — THE SELF-FALSIFICATION TEST, aimed at the largest number in the lane.** I predict that
Robert Moses Niagara's inter-day shaping capability is physically carried by the **Lewiston
Pump-Generating Plant** reservoir — a pumped-storage sibling of the same NYPA project — and that
Lewiston is a **separate EIA plant** which the model represents in its **storage** fleet, *outside*
plant 2693's hydro budget row.
* **If TRUE:** the 0.244 h forebay figure is the right pondage for the hydro row, and the charter's
  premise strengthens.
* **If FALSE** — Lewiston's capability is folded into plant 2693, **or** Lewiston is absent from the
  model's storage fleet so its shaping is implicitly being carried by 2693's hydro budget — then
  **2693's effective pondage is materially larger than 0.244 h and the charter's central number is
  overstated.** That would weaken the object at its strongest point, and I would report it as such.

This is checkable now, zero LP, against the committed fleet, and I commit to reporting it in the
direction it comes out.

**P5 (coverage).** I predict whatever is recovered covers **≤ 75 % of fleet MW** — the two dominant
projects plus at most a handful — and that a **fleet-grain per-plant** period length is **NOT**
achievable in this session, the residual ~100 dockets at ~26 % of MW being unreachable per §1(c).
A **material-plant** period length may still be.

## 4. Thresholds, written now, to be reported in the words they are written in

* **T1 — instrument settled.** Settled iff, for each of P-2216 and P-2000, I can name the governing
  instrument for **each of two distinct quantities separately** (diversion/outflow entitlement vs
  headpond operating band) and cite a retrievable document for it. Naming one quantity only is a
  **MISS**, reported as a miss.
* **T2 — range recovered.** Recovered iff a **numeric** operating band is retrieved with its units
  and its datum, from a **citable public document**, for ≥ 50 % of fleet MW. Below 50 % is a MISS.
* **T3 — period length derived.** Derived iff T2's band converts to hours **without any fitted
  scalar and without an unpublished input**. A conversion needing a stage–storage curve I cannot
  cite is a **MISS**, and I will say the band was recovered but the length was not, rather than
  quietly substituting a proxy.

**I will not restate any of T1–T3 after seeing a number.** nyiso-219's P2b/P2c were reported as
misses in the words they were written in; that is the standard here.

## 5. OUTCOME PARTITION — exhaustive, with an explicit instrument-failure branch

| | outcome | this session's deliverable |
|---|---|---|
| **O1** | FERC licence governs the band **and** it is retrievable here | **(a)** ranges + derived lengths |
| **O2** | An international instrument governs **and** yields a usable band or a published categorical accounting period | **(a)** ranges + derived lengths |
| **O3** | Instrument identified, band retrieved, but **not convertible** to a length without an uncitable input (**P2's branch**) | **(b) partial:** instrument SETTLED, length NOT derived — stated as such |
| **O4** | Neither corpus retrievable from this container | **(b) clean negative**, routes recorded |
| **O5** | **INSTRUMENT FAILURE:** documents conflict, or are ambiguous about which instrument binds, or the band is defined on a **river-reach / system** quantity that does not map to the model's **plant** grain | **report the mismatch and assert NO number** |
| **O6** | **MOOT:** P4 comes out FALSE, so the licensed range is not the right operand for the hydro budget row in the first place | **report that the object needs restating** before any range matters |

**A clean negative is a success.** O3–O6 are results, not failures of the session.

## 6. What must NOT happen — named in advance, before any measurement

* **No period length set at the actual's own measured within-month daily sd** (5.7–8.0 % of daily
  mean). That is an **outcome-derived** number; it would close the residual almost exactly, and that
  is precisely why it is forbidden (rule 13 `[R-MEASURED]`).
* **No hydro shape pinned to measured `NG: WAT`** at any grain — reaches r = 1.000 by construction.
  **Tripwire:** any within-month r near ~0.95 is to be checked for exactly this.
* **No period length chosen or SWEPT because it makes a criterion move** — rule 21 `[R-DOF]` case 3
  and rule 1 `[R-STRUCT]`. nyiso-219 neither chose nor swept one; neither will this session.
* **No borrowing of NEISO's `HDP`/`HDR`/`HW` duration taxonomy** — rule 25 `[R-ISO-SCOPE]`. It is an
  existence proof only; NYISO must derive its own or the mechanism does not arm.
* **No stacking on `hydro_dispatch_envelope`** — rule 19 `[R-ONE-MECH]`. The replace-vs-reconcile
  choice is decided at phase 0 on overlap arithmetic (owner Q2), not by preference.
* **No per-plant hourly structure invented.** A static per-plant pondage duration is admissible; an
  hourly claim is not.
* **Rule 14 `[R-ACCURATE]` cuts both ways, stated before any number:** hydro is ~20 % of NYISO
  generation, so re-timing it **will** move C3a/C3b/C3c. **If the faithful representation makes the
  price fit worse, it STAYS**, and the worse fit is a discovered root-cause question. Precedent: the
  2026-07-25 probe made C3a-2023 worse (+18.3 → +22.2 %) and was still recorded as mechanism
  confirmed.
* **Rule 31 `[R-RETAIN]`:** nothing is deleted; the promotion question is surfaced before the session
  ends.

## 7. The finer-grain register trap — pre-declared guard

nyiso-219 hit this **three times in one session** and every instance inflated a figure: an external
register keyed **finer** than the model's plant, summed without collapsing first (NID `NY00678`'s
seven structures; EHA's one row per **powerhouse**; the 78 % vs 84.24 % peaking share). All three
were caught by **cross-checking against an independently computed number**, not by re-reading code.

**Pre-declared guard for this session:** every coverage or magnitude figure I publish will be
cross-checked against a second, independently computed number before it is written down, and the
cross-check will be shown. **P4 is itself an instance of this guard** — it cross-checks the lane's
single largest number (0.244 h) against the model's own fleet representation.

**No eighth owner card is opened.** The seven pending rulings (nyiso-206, -207, -203,
DECISION-CARD-nyiso193 §5/5.1, -208, -214 §6, -215 §6) are untouched.
