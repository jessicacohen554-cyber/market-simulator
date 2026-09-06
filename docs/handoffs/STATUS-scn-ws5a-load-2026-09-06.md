# STATUS — SCN-WS5A-LOAD (live campaign state)

Standing answer to the recurring check-in questions, so they do not have to be
re-derived from scrollback. Updated as ISOs land.

## Is this a keeper candidate? Should it be promoted?

**No — and this is a category fact, not a judgement on the results.**

"Keeper" is a **backcast calibration** concept: CLAUDE.md rule 1 `[R-STRUCT]`, rule 15
`[R-DASHBOARD]`, the C1–C8 determination rubric, `frontend/data/backcast/keepers/<ISO>.json`.

This lane is a **forecast scenario campaign**: `ScenarioConfig.mode="forecast"`, T1-F
2026–2030, registered with `--kind scenario` into the **forecast** namespace under campaign
`scn-campaign-load-2026-09-06` (forecast plan §7.5). It therefore has:

- no C1–C8 gates, so no "structural integrity improved but gates regressed" trade to weigh;
- no keeper shard, no determination, nothing that *can* be promoted;
- an explicit charter prohibition on touching `frontend/data/*` beyond its own registration
  sidecars, `program-status.json`, `ff-verdicts.json`, or any other ISO's files.

Promoting anything from here would be a governance breach, not a close call.

## Is there backcast calibration work blocked on a merge?

**No.** This session runs no backcast calibration, is not blocked, and has no unpushed or
untracked state.

**Checked at HEAD (`scripts/calibration_verdict.py`, committed artifacts only, no solve):
all six ISOs' designated keepers score `CALIBRATED`.**

| ISO | keeper | determination |
|---|---|---|
| ERCOT | `2026-09-05-ercot248-two-config-keeper` | CALIBRATED |
| CAISO | `2026-09-05-caiso-252-b1-notrim` | CALIBRATED |
| PJM | `2026-08-15-pjm-162-inputclock` | CALIBRATED |
| MISO | `2026-09-05-miso-220-nonsteam-lift` | CALIBRATED |
| NYISO | `2026-09-06-nyiso-196-extract-basis` | CALIBRATED |
| NEISO | `2026-08-17-neiso-99-joint-p1` | CALIBRATED |

So **there is no rubric-failure keeper to tune.** CAISO's only `FAIL` is **C5a CO2 vs eGRID**
(−11.5 %, 2023), which rubric v2.9 demoted to **REPORTED-ONLY** — it carries no status, no
caveat budget and no reason line. Every other ISO's sole blemish is the ledgered **C3c**,
non-downgrading since rubric v3.3.

**What IS open is governance, not tuning.** `calibration-complete.json` reads
`complete = {ERCOT, NEISO, PJM}`, `withdrawn = {CAISO, NYISO}`, MISO never granted, and
`final` is empty with the locked-test tier frozen. Three ISOs hold CALIBRATED keepers while
sitting outside `complete`, which blocks their 2020–2022 validation ladder — and only an
explicit owner declaration clears that. No session can tune its way in.

The handoff prompt for the highest-value remaining calibration work — the **rule-22 touchpoint
loop** on the three ISOs that *are* authorized — was delivered in-session; its shape is
`BC-TOUCHPOINT-2022-<ISO>`, one ISO per invocation, `<ISO> ∈ {ERCOT, NEISO, PJM}`.

## Campaign state

- **Frozen pin** `1cc45bb2`; every leg verified a descendant with **zero** solve-path diff
  and `git.dirty=False` (PRECOMMIT ADDENDUM §5).
- **16 legs** planned: ERCOT/CAISO/MISO/NYISO 3 each, PJM/NEISO 2 each (phase 0 measured the
  DC axis degenerate in PJM and NEISO).
- **Complete:** ERCOT, NEISO, NYISO — solved, registered, delta-reported, FINDING written.
- **Running / queued:** PJM, then MISO, then CAISO (each alone, rule 12).
- Backcast byte-identity untouched; DOF ledger carries **zero** free parameters.

---

## Routed defect — `collate_scenario_campaign.py` differences sums over DIFFERENT ISO sets

Found while pre-flighting the sanctioned collation tool against the three completed ISOs,
**before** it reached this lane's synthesis. Not fixed here: `scripts/collate_scenario_campaign.py`
is SCN-WS0's file and this lane's charter says consume, never modify.

**The defect.** The `six-ISO modeled system` scope in `campaign_delta_table.csv` computes
`emissions_mt_delta` as *(sum over the case's ISOs)* − *(sum over the reference case's ISOs)*,
without restricting both to a common set. When a case has incomplete ISO coverage the two sums
span different systems and the delta is meaningless.

**Measured, on the three ISOs complete at the time:**

| system-scope `LOAD-HI-ORGANIC`, 2030 | Mt |
|---|---|
| reported `emissions_mt_delta` | **+5.4620** |
| correct delta on the common {ERCOT, NYISO} set | **+18.8300** |
| error | **−13.368**, exactly NEISO's REF 2030 level |

`LOAD-HI-ORGANIC` summed 2 ISOs (ERCOT, NYISO — NEISO has no ORGANIC leg because phase 0
measured its DC axis degenerate) while `REF` summed 3. The understatement is **71 %**.

**This is structural, not a partial-results transient.** At full completion `REF` and `LOAD-HI`
will cover **6** ISOs while `LOAD-HI-ORGANIC` covers **4** — PJM and NEISO ship
`LOAD-HI == LOAD-HI-ORGANIC` byte-for-byte, so their ORGANIC arm is correctly never solved
(SCN-WS4b §3, reproduced by this lane's phase 0). So any campaign with a legitimately
degenerate arm hits this.

**Mitigations.** The tool *does* emit `isos` and `isos_missing` per case, so the coverage is
disclosed and the defect is detectable — it is a wrong number beside honest metadata, not a
silent one. This lane's synthesis will compute every cross-ISO delta on the **common ISO set**
and will not quote the system-scope ORGANIC row.

**Suggested repair (for whoever owns the file):** restrict both operands to
`isos(case) ∩ isos(reference_case)` before summing, and label the row with that intersection;
or emit the row as `null` with the coverage mismatch named, rather than a computable-looking
number. Either is preferable to a delta a reader cannot tell is malformed.

---

## CORRECTION — my CCS mechanism claim is FALSIFIED by PJM, and the S5 finding is WIDER

**What I claimed** (NEISO FINDING §2.2, and repeated in the NYISO FINDING): the CCS retrofit
screen is armed by a **state carbon program**, so `gas_cc_ccs` would appear in NEISO / NYISO /
CAISO and **not** in ERCOT / PJM / MISO. Registered as a falsifiable prediction; ERCOT, NEISO
and NYISO all confirmed it, and I reported it as "3/3 confirming".

**PJM falsifies it.** PJM carries **no** state carbon program and still shows
**909.8 MW of `gas_cc_ccs` in 2029 and 2030** (0 MW in 2026–2028).

**Why the claim was wrong.** `model/capacity_evolution/ccs.py` values the retrofit as *"the
incremental uplift over the best unabated state, with the certificate and §45Q … as bid
offsets"*. **§45Q is a federal credit and is independent of any carbon price**, so the screen
can clear on 45Q alone. A carbon price is a *magnitude* driver, not the arming condition. I
over-read capx D50's "at carbon 0 the repair closes the screen" as meaning the screen cannot
open at carbon 0 at all; D50's ERCOT evidence is one ISO's result, not a general condition.

**The corrected picture, as measured:**

| ISO | state carbon program | `gas_cc_ccs` | first year |
|---|---|---|---|
| NEISO | RGGI | **8,833 MW** | 2028 |
| NYISO | RGGI | **6,475 MW** | 2028 |
| PJM | **none** | **909.8 MW** | **2029** |
| ERCOT | none | **0** | — |
| MISO / CAISO | none / CARB | *pending* | — |

So: a carbon program makes the retrofit **large and early**; §45Q alone makes it **small and
late**; and ERCOT shows zero, so 45Q alone is not sufficient everywhere either. *Hypothesis,
not a claim, for whoever owns the screen:* ERCOT's REF is in extreme shortage (load-weighted
price $4,438/MWh at 2030), so an unabated CC already earns enormous margin and the
**incremental** uplift from retrofitting — which costs capex and heat rate — may be negative
there. Untested by this lane.

**Why this matters more, not less.** It **widens** the S5 finding. Contamination from the
SCN-WS2b emission-rate defect is **not confined to the three state-carbon ISOs**; any ISO
whose 45Q economics clear can carry mis-rated `gas_cc_ccs`. The magnitude in PJM is small
relative to its ~470 Mt (unlike NEISO's 41.9 % or NYISO's 25.3 %), but the *scope* claim in
those two FINDINGs was too narrow and is corrected here rather than left standing.

---

## URGENT ROUTE — card D-10's re-solve scope is too narrow by ~2×, measured

SCN-DESK r#10 scopes card **D-10** as *"re-pin once, re-solve the five contaminated legs plus
CAISO, keep ERCOT/PJM/MISO under G-DRIFT"*. That scope rests on this lane's **own earlier,
too-narrow claim** that only the state-carbon ISOs carry `gas_cc_ccs` — a claim PJM falsified
and this lane corrected above. The corrected scope is measured, not argued:

| ISO | legs | `gas_cc_ccs` @2030 (REF → HI) | status |
|---|---|---|---|
| NEISO | 2 | 8,832.9 → 8,802.6 MW | **contaminated** |
| NYISO | 3 | 6,474.6 → 6,620.6 MW | **contaminated** |
| PJM | 2 | **909.8 → 1,512.8 MW** | **contaminated** — not in D-10's list |
| MISO | 2 of 3 solved | **334.5 → 484.1 MW** | **contaminated** — not in D-10's list |
| ERCOT | 3 | 0 | **clean — the only exempt ISO** |
| CAISO | 3 (pending) | expected present (CARB) | expected contaminated |

**So the re-solve set is 13 of 16 legs, not 6.** ERCOT alone is exempt, and "keep ERCOT/PJM/MISO
under G-DRIFT" is right for ERCOT and wrong for PJM and MISO. The magnitudes differ enormously —
NEISO's contamination is 41.9 % of its 2030 level, PJM's ~0.42 % — so a judgement that PJM's and
MISO's levels are *tolerably* stale is entirely reasonable; what is not available is the claim
that they are *unaffected*. That is the desk's call to make with the right number in front of it.

**A second, practical blocker D-10 must plan for.** r#10 records that D77 *"moves no cache key,
so every pre-fix bundle reaching 2028 with a retrofit is silently stale at its own key."* A naive
re-solve of these legs will therefore **hit the existing cache and return the pre-fix numbers**.
Whoever executes D-10 needs an explicit cache invalidation (or a redirected cache dir) as part of
the recipe, or the re-solve will silently reproduce exactly what it was meant to replace.

**What this lane is doing about it, and what it is not.** It is **not** re-solving: D-10 is the
desk's card, the campaign is frozen at `1cc45bb2` by its own PRECOMMIT, and re-pinning mid-campaign
would put legs at two bases — the defect the freeze exists to prevent. It **is** finishing the
campaign at the frozen pin and stating, per ISO, exactly which numbers the D77 seam contaminates
and by how much, so D-10 can be scoped from measurements instead of from this lane's first,
narrower guess.
