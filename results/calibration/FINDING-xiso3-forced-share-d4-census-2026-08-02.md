# xiso-3 — cross-ISO forced-share / D-4 window census on all six current keepers

**Session:** xiso-3 (cross-ISO calibration, Arm A). **Date:** 2026-08-02.
**LP spent: ZERO.** No solve, no scoring of new output, no registration, no bundle.
**Probe:** `scripts/probes/_xiso3_forced_share_d4_census.py`
**Transcript:** `results/calibration/PROBE-xiso3-forced-share-d4-census-2026-08-02.txt`

This is the first time rule 20 `[R-FORCED-BUDGET]`'s full conditional-pass logic has
been censused **across all six keepers at once** on the committed
`legitimacy_diagnostics.json` artifacts, through the **production scorer itself**
(`scripts/calibration_verdict.py::score_forced_share` and its `_d4_provenance` /
`_d1_shape` / `_class_load_share` helpers — the probe re-implements nothing).

---

## 0. Headline

**All six current keepers PASS C8. Zero FAILs, zero exceptions-ledger flips, zero
D-4 window drift against the HEAD registry.** Reported against interest: full
compliance IS the deliverable; the census's informational yield is a 20-row latent
D-4 coverage map (§5) for classes the gate does not currently reach.

| ISO | keeper | C8 | fails | grounded | ledgered | latent | drift | census verdict |
|---|---|---|---|---|---|---|---|---|
| ERCOT | 2026-08-01-ercot149-gas-event-cap | PASS | 0 | 0 | 0 | 3 | 0 | **PASS** |
| CAISO | 2026-07-31-caiso153-reid-b | PASS | 0 | 0 | 0 | 4 | 0 | **PASS** |
| PJM | 2026-07-31-pjm-143b-hy-level | PASS | 0 | **4** | 0 | 4 | 0 | **GROUNDED-PASS** |
| MISO | 2026-07-31-miso-109b-hy-level | PASS | 0 | **3** | 0 | 6 | 0 | **GROUNDED-PASS** |
| NYISO | 2026-08-01-nyiso109-zonal-margin-anchor | PASS | 0 | 0 | 0 | 0 | 0 | **PASS** |
| NEISO | 2026-07-31-neiso-72-hy-window | PASS | 0 | 0 | 0 | 3 | 0 | **PASS** |

* **PJM and MISO pass through rule 20's conditional path** (7 grounded-above-budget
  class-years total, §4) — every binding mechanism carries a declared window with
  **0.0 % off-window binding**, and every escalated class clears D-1 (worst
  `profile_r` 0.897, worst `cv_ratio` 0.697). Per the rule these are **CLEAN
  PASSES surfaced as report notes, never caveats**.
* **No keeper's C8 depends on the exceptions ledger** (raw `score_forced_share`
  == post-ledger records everywhere).
* **No committed D-4 row drifts from the HEAD `D4_WINDOWS` registry** — no bundle
  predates a window change; no re-generation is owed anywhere.

---

## 1. Admissibility, stated up front

This is an **audit, not a mechanism**. Rule 20's C8 gate is **scorer-only by
construction** ("scored entirely from the committed `legitimacy_diagnostics.json`
… no re-solve, no bundle regen"), so the census costs zero LP and touches no
solve path. Every input is a committed byte: the six keeper bundles'
`legitimacy_diagnostics.json`, their registry sidecars / run payloads / bench
parts, and the HEAD scorer sources. The probe **asserts** every scored year is
inside the 2023–2025 training window; no holdout year is read, and the **holdout
spend freeze stays ACTIVE and untouched**. Nothing was armed, no `ScenarioConfig`
field changed, no keeper changed, nothing registered (rule 15's zero-LP
disposition — the neiso-71/73/74 + xiso-1 + xiso-2 precedent).

Verdicts are **strictly per ISO** (rule 25 `[R-ISO-SCOPE]`): PJM's grounded
CT_PEAKER pass says nothing about any other ISO's CT fleet, and the latent gaps
are per-ISO facts, not a transferable defect class.

Reported against interest throughout: a fully-compliant table is stated as
prominently as a breach would have been, and the places where the *label*
over-hedges (§4a) or the materiality line does real work (§3 notes) are said
plainly.

---

## 2. Method

For each ISO the probe reads the keeper id live from
`frontend/data/backcast/keepers/<ISO>.json`, loads the committed artifacts via
`calibration_verdict.load_artifacts`, and:

1. runs the **production verdict** (`determine_from_artifacts`, rubric v2.9) and
   extracts the C8 criterion status + grounded-above-budget notes;
2. re-runs `score_forced_share` per year (pre-ledger) and diffs against the
   verdict's post-ledger records — any status flip would mean an attestation
   exceptions-ledger entry touched C8;
3. prints the year × class census: D-2 forced share vs cap, the rubric's **live**
   materiality (`_class_load_share`, max(model, actual)/load), the artifact's
   baked flags, and the production status;
4. for every over-budget material class, prints the escalation detail behind the
   record: the binding merchant mechanism set, each mechanism's committed D-4
   row(s) + off-window share **and** its HEAD `D4_WINDOWS` entry, and the D-1
   `profile_r` / `cv_ratio`;
5. sweeps **latent** D-4 coverage (material classes *below* their caps) and
   checks **window drift** (every committed D-4 row vs the HEAD registry).

Two denominator vocabularies coexist by design and are both reported: the D-2
forced share uses the artifact's **plant-group dispatch** denominator (e.g. MISO
2023 ST_GAS 8.31 / 25.15 TWh = 33.1 %), while **materiality** uses the
**scored-class** energy from payload/bench (max(12.94, 13.94) / 641.0 TWh =
2.2 %). Each is internally consistent in its own role; mixing them is how a
hand-recount goes wrong — which is one reason the census is a probe, not a
spreadsheet.

---

## 3. Per-ISO census (material classes; caps 30 % merchant / 15 % CT_PEAKER)

Worst material class-year per ISO, by proximity to its cap:

| ISO | closest material class-year | forced % | cap | margin | outcome |
|---|---|---|---|---|---|
| ERCOT | 2025 ST_GAS | 20.1 % | 30 % | −9.9 pp | PASS on volume |
| CAISO | 2025 CC_REGULAR | 9.6 % | 30 % | −20.4 pp | PASS on volume |
| PJM | 2025 CT_PEAKER | 15.8 % | 15 % | **+0.8 pp** | **grounded pass** |
| MISO | 2025 ST_GAS | 45.5 % | 30 % | **+15.5 pp** | **grounded pass** |
| NYISO | 2024 ST_GAS | 27.5 % | 30 % | −2.5 pp | PASS on volume |
| NEISO | 2024 CC_REGULAR | 0.8 % | 30 % | −29.2 pp | PASS on volume |

Notes, per ISO (full tables in the transcript):

* **ERCOT** — material classes ST_GAS (17.8/14.8/20.1 %), COAL (6.9/8.6/3.4 %),
  CC_REGULAR (≤2.1 %) all within cap. CT_PEAKER is **immaterial** (1.5–1.7 % of
  load) in all three years — its 2023 forced share of 10.7 % is reported, never
  gated.
* **CAISO** — the only binding non-exempt mechanism in the entire keeper is
  `ra_mustoffer_bridge` (CC_REGULAR 6.8/7.7/9.6 %, CT_PEAKER ≤0.5 %); everything
  else forcing dispatch is exempt structural must-run (`chp_steam`,
  `hydro_min_flow`, `nuclear_mustrun`).
* **PJM** — CT_PEAKER (2.8–3.4 % of load) rides 0.2–0.8 pp **above** its 15 %
  cap all three years and grounds cleanly (§4). ST_GAS crosses the materiality
  line only in 2025 (2.0 % of load) and grounds at 40.0 %; its 2023/2024 forced
  shares (52.2/48.7 %) are immaterial-skipped (1.4/1.6 % of load) — **the 2 %
  materiality line does real work here**, and that is the rubric working as
  specified (owner amendment 2026-07-06), not a census gap.
* **MISO** — ST_GAS is material by 0.2–0.7 pp (2.2/2.7/2.3 % of load) and above
  cap all three years (33.1/34.4/45.5 %); grounds cleanly (§4). COAL — 27–32 %
  of load, the fleet rule 20 most exists for — is forced **0.2–0.4 %**.
* **NYISO** — ST_GAS 22.5/27.5/23.0 % (material at 7.4–10.6 % of load) is the
  closest sub-cap class among all six ISOs; CC_REGULAR ≤5.3 %. No escalation.
* **NEISO** — every over-cap forced share sits on an **immaterial** class (COAL
  0.2–0.3 % of load at 32.5 % forced in 2023; CT_PEAKER 0.5–1.6 % of load at
  19.9 % in 2023): reported, never gated. The material CC_REGULAR (53.9–54.5 %
  of load) is forced ≤0.8 %.

---

## 4. The grounded-above-budget escalations (PJM ×4, MISO ×3)

Every escalation clears **both** legs. D-4 rows are mechanism-level (a `floor`
label with no class filter totals the mechanism across classes) — floored TWh
below is the mechanism-wide total, off-window share is what the gate reads.

| ISO / class-year | forced | mechanisms (committed window = HEAD) | off-window | D-1 profile_r | D-1 cv_ratio |
|---|---|---|---|---|---|
| PJM 2023 CT_PEAKER | 15.2 % (3.30/21.72 TWh) | ct_netload_drag h15-21 (2.19 TWh); st_netload_drag h0-23 (6.06 TWh) | 0.0 % / 0.0 % | 0.930 | 0.697 |
| PJM 2024 CT_PEAKER | 15.4 % (3.47/22.49 TWh) | ct_netload_drag h15-21 (2.60 TWh); st_netload_drag h0-23 (5.66 TWh) | 0.0 % / 0.0 % | 0.963 | 1.044 |
| PJM 2025 CT_PEAKER | 15.8 % (4.76/30.12 TWh) | ct_netload_drag h15-21 (3.19 TWh); st_netload_drag h0-23 (7.75 TWh) | 0.0 % / 0.0 % | 0.975 | 0.812 |
| PJM 2025 ST_GAS | 40.0 % (6.12/15.30 TWh) | st_netload_drag h0-23 (7.75 TWh) | 0.0 % | 0.897 | 2.244 |
| MISO 2023 ST_GAS | 33.1 % (8.31/25.15 TWh) | reliability_floor × ST_GAS h0-23 (0.24 TWh); st_gas_mustrun_per_plant h0-23 (8.07 TWh) | 0.0 % / 0.0 % | 0.954 | 1.565 |
| MISO 2024 ST_GAS | 34.4 % (8.67/25.20 TWh) | reliability_floor × ST_GAS h0-23 (0.26 TWh); st_gas_mustrun_per_plant h0-23 (8.41 TWh) | 0.0 % / 0.0 % | 0.960 | 1.278 |
| MISO 2025 ST_GAS | 45.5 % (10.72/23.55 TWh) | reliability_floor × ST_GAS h0-23 (0.28 TWh); st_gas_mustrun_per_plant h0-23 (10.44 TWh) | 0.0 % / 0.0 % | 0.974 | 1.503 |

Two artifact-vintage observations, neither a defect:

* **(a) The baked `lower_bound` label over-hedges.** Every PJM/MISO (and
  ERCOT/CAISO/NYISO) D-2 summary row carries `lower_bound: true` — the
  legacy-P2-era note that rebuilt floors "exclude the P1-dependent RA bridge".
  But the committed D-2 **rows themselves attribute forcing to the P1-native
  seam bridges** where armed (CAISO `ra_mustoffer_bridge` 3.32–3.41 TWh/yr,
  ERCOT `gas_commitment_bridge`, NYISO `nyiso_gas_commitment_bridge`), which the
  `run_year(fleet_only=True)` recompute path cannot reconstruct (the G-06
  comment in `scripts/legitimacy_diagnostics.py` says exactly this). The
  artifacts were therefore generated from the solve's own persisted floors, and
  the quoted shares are solve-exact for the scored P1 run; the label is
  conservative vintage text, not a real under-count. For PJM/MISO it is vacuous
  twice over — neither ISO arms any seam bridge.
* **(b) Baked D-2 verdicts say `FAIL` for the seven escalated rows; the HEAD
  scorer re-scores them into grounded passes.** This is the rubric-v2.2 design
  (the scorer ignores embedded verdicts and applies HEAD gates + escalation to
  the measured shares), not drift — the same mechanism that lets gate changes
  re-grade keepers without bundle regeneration.

---

## 5. The latent D-4 coverage map (informational — nothing here is gated today)

For material classes **below** their caps, the census checked whether each
binding non-exempt mechanism would survive `_d4_provenance` if the class ever
escalated. 20 class-year rows across 4 ISOs would not, collapsing to **five
(ISO, mechanism, class) facts**:

| ISO | mechanism | class(es) | forced today vs cap | committed D-4 row | HEAD `D4_WINDOWS` |
|---|---|---|---|---|---|
| CAISO | `ra_mustoffer_bridge` | CC_REGULAR (2023–25), CT_PEAKER (2024) | 6.8–9.6 % vs 30 %; 0.5 % vs 15 % | none | **none — no entry for `MECH_RA_MUSTOFFER` at all** |
| ERCOT | `reliability_floor` | CC_REGULAR (2023–25) | 0.8–2.1 % vs 30 % | none | none for CC (entries exist only for CT_PEAKER / CT_CHP / ST_GAS) |
| PJM | `reliability_floor` | COAL (2023–25), CC_REGULAR (2025) | 0.1–0.3 %; 2.9 % vs 30 % | none | none for COAL / CC |
| MISO | `reliability_floor` | COAL (2023–25), CC_REGULAR (2023–25) | 0.2–0.4 %; ≤0.1 % vs 30 % | none | none for COAL / CC |
| NEISO | `reliability_floor` | CC_REGULAR (2023–25) | 0.4–0.8 % vs 30 % | none | none for CC |

What this means, precisely:

* **Nothing is wrong today.** Rule 20's provenance leg is only consulted for a
  class **above** its cap; every class above is fully windowed. These rows are
  the map of where a *future* escalation would FAIL C8 for a missing
  declaration (correctly, per rule 12/17 — "a mechanism with no declared window
  fails").
* **Headroom is large everywhere**: the closest latent class to its cap is
  CAISO CC_REGULAR at 9.6 % vs 30 %. No keeper is one re-tune away from
  tripping an undeclared-window FAIL.
* **The CAISO row is the qualitatively distinct one**: `ra_mustoffer_bridge`
  (`MECH_RA_MUSTOFFER`) is the **only mechanism binding a material class in any
  keeper with no `D4_WINDOWS` entry of any kind** — the reliability_floor gaps
  are class-coverage gaps of an existing entry family. If a D-4 row is ever
  wanted for it, the natural declaration is the one the other commitment
  bridges carry (all-hours by driver — the RA must-offer obligation is not a
  clock-hour rule; same shape as `MECH_GAS_COMMITMENT_BRIDGE` /
  `MECH_NYISO_GAS_COMMITMENT_BRIDGE`), plus a regenerated CAISO bundle so the
  row exists (rule 20's regeneration clause).
* **No entry was added this session.** A `D4_WINDOWS` entry is a rule-17
  declaration — driver, window, forward story, per ISO, with cited evidence —
  and a census is not the session to mint five of them. Filed here as the
  standing map; each future declaration cites its own driver evidence.

NYISO is fully covered: both bridge classes and `reliability_floor × ST_GAS`
carry committed rows matching HEAD.

---

## 6. Context: full determinations at HEAD (not census news)

The census ran the whole rubric to place C8 in context. At HEAD (v2.9): PJM
scores **CALIBRATED**; CAISO / NYISO / NEISO **CALIBRATED-WITH-CAVEATS**; ERCOT
and MISO **NOT-YET** — ERCOT on the C3 price family + C7 (its 2023 level
residual, the known §5.1 frontier), MISO on C7 alone (the known §5.4 COAL_PRB
diurnal-shape target, its sole failing criterion). **C8 is not among any ISO's
failing criteria**, and none of the above moved this session — the matrix's
per-ISO headers already record these open gates.

---

## 7. What this licenses, and what it does not

**Licenses:**
* Quoting, with this citation, that every current keeper is rule-20 compliant at
  HEAD — PJM and MISO via the grounded path with the §4 evidence.
* Using §5 as the standing pre-flight map: any session whose change could push a
  listed class over its cap knows in advance which declaration it must first
  earn (and that the bundle must be regenerated to carry the new D-4 row).
* Re-running the census at any time via the probe (~1 min, reads keeper shards
  live, zero LP).

**Does not license:**
* Adding `D4_WINDOWS` entries without per-ISO driver evidence (rule 17), or
  treating the latent gaps as defects — they are declarations not yet required.
* Transferring any grounded verdict or window across ISOs (rule 25).
* Reading PJM/MISO's grounded passes as license to force more — the escalation
  grounds *observed* mechanism windows and class shape, per year, per ISO, and
  re-runs on every keeper change.

---

## 8. Changes made this session

* `scripts/probes/_xiso3_forced_share_d4_census.py` — the census probe (new).
* `results/calibration/PROBE-xiso3-forced-share-d4-census-2026-08-02.txt` — the
  frozen transcript (new).
* This FINDING doc (new).
* Mechanism matrix: new audit row `forced_share_d4_census` (cells per §0) +
  §5.7 entry in `docs/mechanism-testing-matrix.md`; governance log appended.
* **No code change, no `ScenarioConfig` change, no keeper change, nothing
  registered on the dashboard** (zero-LP disposition, rule 15).
