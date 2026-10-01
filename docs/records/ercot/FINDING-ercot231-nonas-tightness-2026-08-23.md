# FINDING — ercot-231: the NON-AS ENERGY/TIGHTNESS sweep — five factors carried to verdicts, the tie-zone attribution crosses the C3a adoption bar, and the keeper lineage's measured-GTC arm is discovered silently dead (and repaired gates-clean)

**Session:** ercot-231 — a two-container record. The hub session (branch
`claude/ercot-energy-tightness-channel-vm4w8k`) executed Phase 0, the N1a
build+solve and the GTC discovery, and died mid-close with four commits
unmerged; the continuation session (branch
`claude/2023-ercot-config-assessment-ouhsua`, this file) recovered those
commits, independently replicated the control identity, solved the combined
probe, and wrote this record.
**Charter:** `docs/PRECOMMIT-ercot231-nonas-tightness-2026-08-23.md`
(blob `526401e`, pushed + blob-verified before any measurement).
**Keeper at pin (untouched):** `2026-08-20-ercot223-arm-eventrelease`
(NOT-YET; C3a-2023 −39.7 %, C3b-2023 0.729, C3c 74 h of RT 181; 2024/2025
clean; miss split 67 caught / 114 missed / 7 phantom).
**Predecessors:** `FINDING-ercot227-factor-sweep-2026-08-22.md` (AS side
closed), `FINDING-ercot230-adaptive-fixed-point-2026-08-23.md` (conduct
fixed point).

## 0. Where the hub stopped, and what this completion added

The hub committed the precommit, the N1a build (`ercot_tie_zonal_interchange`
+ matrix row + all-shard cells), the Phase-0 JSON, and the five
documentation-verdict probe JSONs to main (PR #4227). Its last four commits —
the solved N1a probe JSON, the N1a gates JSON, the combined-candidate
attestation generator, and the combo-bundle gitignore — were stranded on its
branch and are merged forward by this session unrewritten. Two mid-flight
defects the hub found and fixed are part of the record:

- **The demand-threading defect (commit `0b72358`, the caiso-80/nyiso-87
  class):** the backcast orchestrator loads demand once and threads it into
  `run_year`, so a `--set`-armed `ercot_tie_zonal_interchange` probe solved
  on the RAW load-share spread while `run_config.json` recorded the armed
  value — silently inert and misreported. Caught because the first N1a arm
  came back demand-identical to control; fixed prb-overrides-first in both
  loaders. Every solved result below post-dates the fix.
- **The G-REPRO tool dtype defect (commit `7608ee0`):** fixed before any
  identity claim was recorded.

This session re-validated the environment end-to-end at the pins
(python 3.11.15, highspy 1.15.1, numpy 2.4.6, scipy 1.17.1, pandas 3.0.5,
pyarrow 25.0.1): the official scorer reproduces the keeper's registered
digits exactly (`--validate-keeper` OK, all three years) before any probe was
scored.

## 1. THE FACTOR TABLE — verdicts

| factor | object | verdict | record |
|---|---|---|---|
| **N1a** | DC-tie interchange placed at the tie-host zones (measured EIA-930 per-neighbor split) | **SOLVED — mechanically REJECTED-AS-ARMED on G-SPUR alone; every other §5.5 criterion clears, C3a +1.6 pp; KEEPER-CANDIDATE escalated to the owner** (§3) | `ercot231_probe_n1a.json` + `ercot231_n1a_gates.json` |
| **GTC** *(discovered, not chartered)* | the recipe's own `ercot_gtc_limits_measured=True`, data-starved across the keeper lineage | **measured-GTC restoration is gates-clean as its own single delta and moves 4 missed hours λ-carried — the rule-14 repair** (§2) | `ercot231_gtc_gates.json` |
| **N1b** | priced/elastic DC ties | NO-WINDOW + DATA-ABSENT (miss set is all-import, p50 64.8 % of capability; no neighbor price series) | `ercot231_probe_n1b.json` |
| **N2/N2a/N2b** | outage/derate residual beyond armed channels | ALREADY-CARRIED + DATA-ABSENT (battery, attempt log) + REFUTED-BY-OWN-MEASUREMENT (CHP) | `ercot231_probe_n2.json` |
| **N3** | renewable delivery basis (+504 MW wedge) | DOCUMENTATION — wedge real (p50 +396 MW, 0.962-correlated with measured curtailment) but unrepresentable: 14 of 17 2023 GTCs are intra-zone pockets; topology stays CLOSED | `ercot231_probe_n3.json` |
| **N4** | demand-side residuals | MEASURED-FAITHFUL (0 interpolated hours; two-publication wedge at comparator noise, mixed sign) | `ercot231_probe_n4.json` |
| **N5** | uncarried supply classes | ALL CLASSES CARRIED / BELOW-MATERIALITY | `ercot231_probe_n5.json` |
| **Combined** | keeper recipe + N1a + GTC restoration, 2023-only W-2 probe | §5 | `ercot231_probe_combined.json` + `ercot231_combined_gates.json` |

Phase-0 measurements for every factor: `ercot231_phase0.json`. All probe
bundles stayed local and gitignored (W-2); the committed JSONs, this FINDING
and the matrix stamps are the record.

## 2. THE GTC-LINEAGE DISCOVERY — the ERCOT-76 provenance defect, resurfaced on the current keeper and this time solved

**The keeper lineage (ercot-215 → 221 → 223) solved on the static-TTC
fallback despite `ercot_gtc_limits_measured=True` in its own meta and
run_config.** `data/gtc.py::load_gtc_hourly` returns `None` when the
`data/clean/gtc-limits` partition is absent — gitignored and therefore absent
in every fresh container unless the session runs
`scripts/data/curate_gtc_limits.py` first. No session since the July window
did, so the armed flag has been a silently-starved no-op across the current
lineage. This is not a new class: **ERCOT-76 (2026-07-17) surfaced exactly
this defect** ("the keeper's armed flag is data-starved in every fresh
container"), recorded owner options (regenerate at solve time, or record the
effective state), and neither option was taken. The ercot-231 hub tripped
over it in the opposite direction: its first "control" replay ran WITH a
freshly curated partition and failed identity against the keeper by 427 hours
> $1 (max $157.7).

**Proof, replicated in both containers:** G-REPRO numeric identity against
the keeper's committed sidecars is achieved exactly and only WITHOUT the
partition. This session's static-TTC control replay reproduces every numeric
column of every 2023 hourly sidecar to **max|Δ| = 0.0** and the official
scorer prints the keeper digits (−39.7 % / 0.729 / 74 h) — the keeper's
effective 2023 network is the static ratings, measured twice independently.

**The measured-GTC solve as its own single delta** (`ercot231_ctl_gtc`,
gate-paneled vs the keeper in `ercot231_gtc_gates.json`): **all six gates
PASS** including G-SPUR 11↔11 (identical hour sets), official model mean
38.81 → 38.82 (+$0.01), C3c 74 → 75, miss split unchanged 67/114/7, and **4
improved missed hours, λ-carried (share 1.0059), max +$6.49** — the first
factor in the whole 226/227/230/231 program to move any missed hour at all.
Curation is deterministic from committed raw archives
(`data/raw/iso-specific-transmission/*SCEDBTCNP686*`, 2023: 13,452
(gtc, hour) rows across 17 GTCs; 3 mapped onto reduced-topology links —
NE_LOB, PNHNDL, WESTEX — 14 correctly ignored as intra-zone pockets).

**Adjudication.** Rule 14 `[R-ACCURATE]`: the measured limit exists, is
armed by the recipe's own config, and its restoration is gates-clean — the
static fallback was an accident of container state, not a modelling choice.
The matrix ERCOT cell `measured_interface_limits: K ("ercot GTC keeper")` had
drifted from the artifacts beneath it (the current keeper provably never
solved on the measured caps); re-stamped this session with the discovery.
The repair is carried in the combined candidate (§5) rather than self-adopted
(§6). A durable fix for the trap itself (fail-loud when the flag is armed and
the partition is absent, or curation as a standing solve-time step) is put to
the owner in §6 — ERCOT-76's options, still open, now with a solved A/B
attached.

## 3. N1a — the tie-zone interchange attribution: adoption-bar C3a movement, one gate over

**Mechanism** (built default-off, zero fitted scalars): the netted DC-tie
interchange leaves the load-share spread and lands on the tie-host zones —
SWPP flow → Northeast (600/820) + North (220/820), CEN flow → South
(`constants.ERCOT_DC_TIE_ZONE_MAP`, published tie ratings; measured
per-neighbor flows from `data/raw/eia-930-interchange/`). Column sums
conserve the netted total every hour, so the system energy balance is
unchanged by construction — only placement moves. Phase-0 grounding: **all
114 keeper-2023 missed hours were net imports** (p50 −814 MW = 64.8 % of the
1,256 MW capability, zero export hours), SWPP pinned at its tie limit; the
netting identity closes to ≤ 1 MW at the miss set.

**The A/B** (control = static-TTC keeper replay; arm = control + the one
`--set`, post-threading-fix):

| measurement | control | N1a arm |
|---|---|---|
| official C3a-2023 | −39.7 % (38.81) | **−38.1 % (39.84) — +1.6 pp, clears the 1.5 bar** |
| official C3b NRMSE | 0.729 | **0.696 — improves** |
| official C3c model tail | 74 h | 93 h (vs RT 181) |
| miss split (caught/missed/phantom) | 67/114/7 | **80/101/11** |
| `d_price_at_miss` | — | **p50 +$8.28, max +$49.83** |
| window concentration | — | 0.9742 |
| calm fortnight | +15.44 % | +16.29 % (bar ≤ +2 pp: PASS) |
| channel λ-share at improved misses | — | 1.0017 (λ-carried; G-SHORTFALL subset holds) |
| G-CAP / G-SHED / G-BAT / G-D2 / G-SHORTFALL | — | **all PASS** |
| **G-SPUR banded** | 11 | **21 vs bar 14 — FAIL** |

The G-SPUR detail: 10 new spurious mid-band hours, all Aug-5–Sep-26
in-season, lidless s_top = 0 (none above $500) — the arm's tightened
placement over-fires the $200 band in shoulder-summer hours reality kept
below it, the exact failure mode the gate exists to price.

**Mechanical verdict: REJECTED-AS-ARMED on G-SPUR alone** — recorded
unrewritten, the flag stays default-off. Every other §5.5 criterion clears,
which makes this the precommit's own named borderline case (§5.8: "borderline
mechanical verdicts escalate, never self-adjudicate"), and its shape is the
ercot-188/213/215/221 pattern (one regressing gate, everything else toward
actual, zero fitted scalars, measured physical placement) under which the
owner's standing structural standard has promoted four times. **KEEPER-
CANDIDATE, escalated to the owner in §6 — not self-adopted, nothing
registered.**

## 4. N1b / N2 / N3 / N4 / N5 — the documentation verdicts

All five terminate at Phase 0 with their §5.4 kill preconditions fired,
each with exactly one committed probe JSON (§1 table). The one measurement
worth restating: N3's +504 MW renewable wedge is real, 0.962-correlated with
ERCOT's own measured curtailment (HSL − gen), and **unrepresentable** — the
curtailment is spread across 14-of-17 GTCs that are intra-zone pockets in the
7-zone reduction, an actual-generation UB pin is the rule-13 forbidden form,
and closing the whole wedge is worth ~$0.6–0.8/MWh at the measured
1.6 $/MWh/GW slope. The West/Panhandle topology split stays CLOSED. N5's
closure context reproduces the ercot-216 anatomy on this keeper's miss set:
the model's extra supply (renewables +396, coal +414, battery +189, hydro
+79 MW) is the counterparty of its gas shortness (−1,207 MW); none of it is
missing-supply tightness.

## 5. THE COMBINED 2023 PROBE — keeper recipe + N1a + the GTC restoration

Solved by this session (2023-only, W-2; bundle `ercot231_combo2023`, local +
gitignored): the static-TTC control recipe + the single
`--set ercot_tie_zonal_interchange=true`, with the `gtc-limits` partition
curated so the recipe's own `ercot_gtc_limits_measured=True` engages. Both
deltas verified live in the solve log (tie-zone applied, −98 MW avg; NE_LOB /
PNHNDL / WESTEX applied hourly over their 3,640 / 1,312 / 1,881 active hours,
14 unmapped constraints ignored).

| measurement | control | combined arm |
|---|---|---|
| official C3a-2023 | −39.7 % (38.81) | **−38.0 % (39.85) — +1.7 pp, clears the 1.5 bar** |
| official C3b NRMSE | 0.729 | **0.696** |
| official C3c model tail | 74 h | 93 h (vs RT 181) |
| miss split | 67/114/7 | **80/101/11** |
| `d_price_at_miss` | — | **p50 +$8.24, max +$54.31, 82 improved miss hours** |
| window concentration / calm fortnight | — / +15.44 % | 0.9677 / +16.28 % (Δ +0.84 pp, bar ≤ +2: PASS) |
| channel λ-share at improved misses | — | 1.0017 (λ-carried) |
| adaptive conduct path | 7 spike days, floor cal 22/118/16 h ≥$1k | **identical** (7 days, same floors) |
| G-CAP / G-SHED / G-BAT / G-D2 / G-SHORTFALL | — | **all PASS** |
| **G-SPUR banded** | 11 | **21 vs bar 14 — FAIL, the identical 21-hour set of the tie-only arm** |

**The composition is measured additive.** Tie-only 39.84 / GTC-only +$0.01 /
combined 39.85 on the official mean; the combined spur set is bitwise the
tie arm's (the GTC piece is invisible at the gate grain), and the GTC
restoration's contribution shows only where its own single delta already
did — at the top of the book (`d_price_at_miss` max +$49.83 → +$54.31,
improved miss hours 80 → 82). No interaction term, no cross-amplification —
two independent measured surfaces, each carrying exactly its own effect.

**Mechanical verdict: REJECTED-AS-ARMED on G-SPUR alone** — the same single
gate, the same hours, the same in-season/no-top character as N1a (§3).
Record: `ercot231_probe_combined.json` + `ercot231_combined_gates.json`.

## 6. PROGRAM DISPOSITION — everything to the owner, nothing self-adjudicated

Under §5.5/§5.8 strictly read, **no factor cleared adoption in full** (N1a's
G-SPUR), so the else-branch governs: keeper untouched, nothing registered,
flags default-off, and the handback puts the open questions to the owner:

1. **N1a promotion** under the standing structural standard, over the G-SPUR
   mechanical kill (§3) — the ercot-221 shape, with the mechanical verdict
   standing unrewritten either way.
2. **The GTC restoration** as the rule-14 repair (§2): gates-clean, moves 4
   missed hours, and makes the recipe's recorded config true. Also ERCOT-76's
   still-open trap fix: fail-loud on armed-but-starved, or curation as a
   standing solve-time step.
3. **If either is taken:** the combined 3-year path (`ercot231_tiegtc_full`)
   runs under the full keeper workflow — §5.7's explicit-2024/2025-scoring
   branch (both drivers are live in all years), the X-2 keeper-file prose
   rewrite, and the C3c OPEN-RESIDUAL-LANE re-wording, whose generator is
   already committed (`scripts/gen_ercot231_attestation.py`) and discharges
   only at promotion.
4. **If neither:** the §0 termination protocol — Door D restore (rest until
   the 2026 SOM RTC+B-era anchors, ~mid-2027) vs the seasonal end-of-season
   term card, the only un-adjudicated named successor of the adaptive family.

**AMENDMENT — THE OWNER'S ANSWER (2026-08-23, in the hub session, verbatim):**
*"Try 3 year but you can do a 1 year keeper on ERCOT 2023 because it is a
fundamentally different market design than 2024 and 2025… that's the whole
point of this exercise rule 16 be damned."* Effect: options 1+2 are TAKEN
TOGETHER — the combined 3-year path (option 3) is GO — and **rule 16
[R-ALLYEARS] is owner-waived for ERCOT 2023 specifically**, pre-authorizing
a 2023-only keeper registration if the 3-year run degrades 2024/2025
retention, on the regime ground the record itself carries (2023 is the
pre-reform ECRS / no-release design; the armed regime machinery is
date-gated for exactly this reason). Decision rule fixed before the 3-year
result was seen: **2024/2025 official C3a/C3b remain PASS → promote the
3-year bundle (standard rule-16 form); either year degrades past its band →
register and promote the 2023-only bundle under the waiver, with the
2024/2025 results reported at full magnitude alongside and the waiver
recorded verbatim in the attestation, the keeper note and the log.** The
termination protocol (option 4) is moot in its measured-empty form.

**EXECUTED (2026-08-24).** The 3-year invocation surfaced one more silent
inert on its first run — 2024 is a leap year and the by-neighbor slice
(8,784 hour-ending rows) refused attribution, falling back to the spread —
fixed by Feb-29 excision on the hour-beginning clock (hermetic test added)
and the full 3-year re-solved with the attribution live in all three years
(2023 −98 / 2024 +14 / 2025 −34 MW avg). Final bundle
(`ercot231_tiegtc_full`): **2023 −38.0 % / 0.696 / 93** (keeper
−39.7/0.729/74), **2024 +0.4 % / 0.130 / 22** and **2025 −7.7 % / 0.099 /
1** — retention PASS in both guard years, so the STANDARD 3-year branch
fired and **the rule-16 waiver was left unused**. Gates: G-SPUR-only
regression (the pre-authorized posture; 21 in-season, s_top 0); G-D2
verified PASS against the 3-year keeper comparator (24 = 24 rows — the
1-year-control comparison's 2024/2025 rows are an artifact, listed and
dismissed); 2024 spur 11 = baseline, shed {3067} = baseline; 2025 spur
1 = baseline, shed ∅. Registered as
**`2026-08-24-231-tie-zone-measured`** (determination NOT-YET on
{C3a-2023, C3b-2023}, C3c-2023 a clean PASS at 93/181 = 0.51× — the tie-zone/GTC hours carried
2023 over the band's lower edge, the first ERCOT keeper on which the 2023
tail criterion passes — with the caveat now ledgered ×2 (2024 22/53,
2025 1/31) and the OPEN-RESIDUAL-LANE re-wording discharged in the
attestation (the spent 2023 entry dropped per the generator's own
band-met clause; caught by the keeper auditor, which repaired the shard
note and status page)) and
**PROMOTED TO KEEPER**, with the keeper shard's X-2 note rewritten to this
keeper's magnitudes (discharging the prose debt carried since ercot-223),
the status page rebuilt, and the matrix keeper/gates/cell stamps landed.
**Replay-reproduction rule, now keeper-binding: replays of THIS keeper
require the `gtc-limits` clean partition; replays of ercot-223 and earlier
require its absence.**

What is different from every prior handback in this program: the sweep did
**not** terminate MEASURED-EMPTY. The pre-registered §1 arithmetic said a
quantity factor could not reach the bar without multi-GW magnitude; N1a
cleared it anyway by **placement** — the miss-set hours are all-import with
the flow spread across zones by load share, and putting the measured MW where
the ties physically sit moves the binding zones' λ at exactly the missed
hours (97.4 % window-concentrated, λ-carried). The 2023 summer residual's
remaining depth is still the conduct object (ercot-230's closed circle), but
its reachable margin from measured physical inputs was not zero.

## 7. COMPLETENESS — the §4 enumeration is discharged

With N1–N5 at verdicts, every term of the LP's 2023 input surface is now
armed-measured, enumerated, or cited-closed: demand (N4), interchange inside
demand (N1), thermal availability (N2), renewable bounds + network limits
(N3; measured GTC restored §2), storage (conduct/AS families closed),
absent classes (N5); the AS/reserve side closed by 226/227, the conduct/offer
side by 221/222/223/230. **The 2023 tightness surface has no admissible
un-swept input face left.** What remains on the year is the conduct depth
(7 vs 23 event days — the map's own fixed point) and the §6 owner calls.

## 8. THE 2022 DUAL-CONFIG STANDING PROTOCOL (record only — NOT executed)

Unchanged from PRECOMMIT-ercot226 §7 / FINDING-ercot227 §9: ERCOT holds no
`complete` marker, so 2022 is untouched (rule 22). When authorized, 2022 runs
the frozen keeper recipe under the pre-ECRS design (RegUp/RRS/NonSpin only;
ECRS launched 2023-06-10) against the same measured-overlay discipline. Both
of this program's candidate repairs regenerate for 2022 from the same
measured products (EIA-930 flows; NP6-86 archives, whose 2020–2022 partitions
the curation already writes).

## 9. Session hygiene

- Solves in-session and sequential (rule 12): static control, then the
  combined arm, one at a time; 6 GB swapfile preemptive, `MALLOC_ARENA_MAX=2`;
  no OOM, no retries.
- Years ⊂ {2023} solved, W-2 probes only (rule 22); ERCOT-only shards and
  curves (rule 25); no dashboard registration, no keeper/status/bench
  contact.
- The hub's four stranded commits merged forward unrewritten (fast-forward;
  its branch tip already contained origin/main). Every pushed ≥300-line file
  blob-verified (rule 27); `check_mechanism_matrix.py` exit 0 on every push.
- No CI solves, no new workflows.
