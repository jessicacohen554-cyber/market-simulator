# FINDING — pjm-142: **the overnight gas commitment bridge is KILLED at the pre-registered no-LP pre-check — the bridgeable pool is 1.36–1.60 GW against a ~3 GW materiality bar, and PJM's diurnal-amplitude lever queue is now EMPTY with zero open successors.** The pre-check (thresholds committed ex ante in `PRECHECK-pjm142-overnight-gas-commitment-bridge-2026-07-30.md`, before any measurement ran) fired on neither branch: forcing the ENTIRE lever-favorable pool moves the overnight clearing point **$0.52 / $0.41 / $0.64/MWh** against the K-A bar of $1.00 — 7.6 / 7.1 / 18.7 % of the +$6.82 / +$5.78 / +$3.40 overnight error — and the marginal rung stays `CC_REGULAR:econ` in the plurality of overnight hours even at full forcing. Matrix item 13's one non-adjudicated successor is adjudicated: `gas_commitment_bridge` PJM `U → R` (pre-check refutation). No mechanism was built, per the charter's own stop rule.

**No LP was solved.** The measurement is the committed pjm-141 census probe's new
**T7** block (`scripts/probes/_pjm141_overnight_tranche.py`, extended per the
charter rather than a new script), run on the keeper `pjm140_rampenv_B`'s own
reconstructed fleet/offers (`fleet_only=True`), its committed `hourly/`
sidecars, and the re-fetched `data/raw/pjm-zonal-lmp/` DA components (verified
**36/36 byte-identical** to the committed manifest — the pjm-141 reproducibility
check reproduced). Machine output:
`results/probes/pjm142_bridge_precheck.json` (gitignored; these numbers are the
record). The T1 census re-printed pjm-141's tranche shares to the third decimal
in all three years — the T7 extension is grafted onto an independently
regression-checked base.

**Nothing is registered on the dashboard and no keeper changes** — no arm was
solved (the pjm-138/139/141 disposition). The keeper stays
`2026-07-30-pjm-140-rampenv`, CALIBRATED, every criterion passing;
`audit_keepers.py --check` shows PJM `[✓]`.

---

## §0 — the verdict in one table

| | 2023 | 2024 | 2025 | pre-registered bar | verdict |
|---|---|---|---|---|---|
| bridge-eligible idle committed pool, tranche basis (GW) | 0.95 | 0.92 | 0.65 | — | |
| pool at the max plausible min-load (0.574 × plant, net of existing floors) (GW) | 1.36 | 1.38 | **1.60** | **F($1) = 2.88 / 3.37 / 2.57** | **pool < bar, ×3** |
| **Δ dual at FULL pool, h01–h04 mean ($/MWh)** | **0.52** | **0.41** | **0.64** | **K-A ≥ $1.00 in ≥2 of 3 yrs** | **FAIL ×3 → KILL** |
| share of the overnight error closed | 7.6 % | 7.1 % | 18.7 % | — | |
| net CC volume shift at full pool (GW) | +0.31 | +0.34 | +0.50 | K-B ≤ 1.0 | (would have passed — kill is K-A alone) |
| marginal rung at full pool, plurality | `CC_REGULAR:econ` 42.5 % | 40.2 % | 36.4 % | — | ownership does NOT shift to `committed` |
| walk baseline vs keeper (in-merit ÷ dispatched thermal) | 0.979 | 1.011 | 0.998 | — | walk valid |
| walk d0 vs keeper lw dual ($) | 27.60 / 27.70 | 26.45 / 26.48 | 36.08 / 36.18 | — | walk valid |

The ex-ante slope prediction from pjm-141's committed T2 quantiles — **2.92 /
3.50 / 2.66 GW per $1/MWh** — is confirmed by the hour-resolved measurement to
within 2–4 % (**2.88 / 3.37 / 2.57**). There is no local merit-curve cliff at
the overnight clearing point for a small forced block to exploit; the PRECHECK
§3 "ex-ante tension" resolved exactly as stated.

## §1 — the pool: why there is so little for a bridge to add

Eligible rows: **70** merchant gas-CC `committed` tranches (rule 18
`[R-PHYSICS]`: `fuel_type == gas_cc`, CHP excluded, min-down ≥ 4 h — resolved
via the heat-rate-keyed `CC_COMMITMENT_PARAMS` table, see §5). At h01–h04,
mean over 1,460 hours/year:

| GW | 2023 | 2024 | 2025 |
|---|---|---|---|
| eligible committed ALREADY IN MERIT | **19.47** | **22.24** | **21.95** |
| already force-floored by `cc_mustrun_per_plant` on the pooled plants | 1.51 | 1.04 | 1.10 |
| idle + day-anchored committed tranche (the pool, net of floors) | **0.95** | **0.92** | **0.65** |
| pooled plants' whole available capacity | 5.00 | 4.21 | 4.70 |
| forced MW at min-load scan 0.30 / 0.45 / 0.574 (net) | 0.00 / 0.74 / 1.36 | 0.22 / 0.86 / 1.38 | 0.31 / 1.02 / 1.60 |

This is pjm-141 T3's "the LP already loads `committed` preferentially",
sharpened to the bridge-eligible margin: of the merchant gas-CC committed
tier, **~20–22 GW is already dispatched in merit overnight** and another
**~1.0–1.5 GW is already held on by the keeper's incumbent CC commitment floor
(`cc_mustrun_per_plant`, 11.5 TWh forced CC_REGULAR in 2024 per the committed
D-2)** — a floor a bridge must reconcile with, never stack on (rule 19
`[R-ONE-MECH]`). What remains for a bridge to add — plants that ran the
flanking day windows but sit off overnight — is **0.65–0.95 GW of committed
tranche**, or at most **1.36–1.60 GW** granting the largest min-load fraction
any ISO has ever measured (0.574, an upper-bound scan only, never a PJM
parameter).

The restart-economics screen says the *story* is real — **94–100 %** of the
pool (capacity-weighted) would hold at min-load rather than re-pay a startup
under the standard restart inequality at every scanned min-load fraction. The
bridge fails not because PJM CCs wouldn't stay on, but because **the model
already keeps nearly all of them on economically**: the commitment behaviour
the bridge would inject is already delivered by the merit order plus the
incumbent floor, and the residual pool is a rounding term against the stack's
~3 GW/$ slope.

## §2 — the walk: what full forcing buys, and who clears afterwards

Static merit-curve walk (lever-favorable: demand, storage, interchange, DA
virtual layer all held fixed; an elastic response would buffer the drop), new
dual at cumulative in-merit MW − F:

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| Δ dual at FULL pool ($/MWh) | **0.52** | **0.41** | **0.64** |
| MW needed for $1.00 (GW) | 2.88 | 3.37 | 2.57 |
| displaced band mix at full pool (CC / CT / ST, GW) | 1.05 / 0.13 / 0.26 | 1.04 / 0.11 / 0.24 | 1.10 / 0.22 / 0.30 |
| net family shift (CC / CT / ST, GW) | +0.31 / −0.13 / −0.26 | +0.34 / −0.11 / −0.24 | +0.50 / −0.22 / −0.30 |
| new marginal rung, share of overnight hours: `econ` / `committed` (CC_REGULAR) | 42.5 / 22.5 % | 40.2 / 23.8 % | 36.4 / 19.9 % |

Two things worth the record:

1. **The displaced band is ~73–78 % CC**, well above the marginal-census 40 %
   share the PRECHECK's K-B arithmetic assumed — so the volume-conservation
   guard was never in danger (+0.31/+0.34/+0.50 GW net CC, inside the 1.0 GW
   bar). The kill is **pure materiality**, not a volume conflict.
2. Even at full forcing, **`CC_REGULAR:econ` keeps plurality marginal
   ownership** (42.5 / 40.2 / 36.4 % of overnight hours vs `committed`'s
   22.5 / 23.8 / 19.9 %). The mechanism's stated aim — shifting marginal
   ownership from `econ` to the cheaper `committed` rung — does not occur even
   in the most favorable static reading.

## §3 — adjudication against the pre-registered kill rule

PRECHECK §3, verbatim thresholds, fixed before any measurement: **K-A** fires
only if Δd(F_pool) ≥ $1.00/MWh in ≥ 2 of 3 years; **K-B** (≤ 1.0 GW net family
shift) evaluated only if K-A passes; the mechanism is built only if both hold.

* K-A: **$0.52 / $0.41 / $0.64** — fails in **all three** years (needed ≥ 2
  passes). The FIRE rule cannot be met.
* K-B: moot; recorded as would-have-passed.
* **VERDICT: KILL.** Per the charter's stop rule: no `ScenarioConfig` field, no
  mechanism code, no arm, no PREREG. `gas_commitment_bridge` PJM `U → R`
  (pre-check refutation on the pre-registered thresholds; cells `KKUUKK →
  KKRUKK`).

## §4 — what this closes: item 13, and the queue is now empty without an asterisk

Matrix §5.3 item 13 named this bridge as "the one non-adjudicated successor"
to PJM's diurnal-amplitude defect, with its ex-ante refutation half-stated
(volume already correct; committed already loaded). The pre-check completes
that refutation with the other half measured: **the idle bridgeable margin is
~1.4 GW against a ~3 GW bar, and forcing all of it neither reaches materiality
nor hands the margin to `committed`.**

PJM's diurnal amplitude deficit is therefore a **DIAGNOSED, UNCLOSED
structural limitation whose lever queue is EMPTY with no open successor** —
pjm-141's terminal state, now without the item-13 asterisk. Every route is
adjudicated: `measured_offer_surface` `R` under both conditioning definitions
(pjm-123/126/127/132), re-binning barred by rule 23, the reserve/scarcity lane
owner-closed (pjm-138), `ramp_envelopes` spent (pjm-140), every daily gas
series barred by the zero within-day σ (pjm-139/141), the seam refuted
(pjm-141 §5.2), and the commitment bridge killed here. This is the NYISO-C3c
terminal state (nyiso-96/97) reached with every exit measured shut. **It fails
no gate**: the keeper is CALIBRATED on every criterion, and the annual level's
pass-by-cancellation (+$6.82/+$5.78/+$3.40 overnight against
−$7.62/−$11.37/−$22.19 at peak) is a disclosed representation boundary of a
monthly-amortized, hour-invariant offer stack under the no-MIP mandate — the
LP-vs-MIP boundary's offer-side face.

## §5 — infrastructure facts discovered, recorded for any future re-open

* **PJM's CAMPD-bin tranches carry no native commitment physics**:
  `min_run_hours = min_down_hours = 0` on every CC row (543/543 in 2024), so
  `model/commitment.py::_commitment_params` returns `None` for them and the
  existing bridge detector machinery would have nothing to gate on. The first
  T7 run returned an empty eligibility set for exactly this reason (visible in
  this branch's commit history); the corrected run resolves rule-18 physics
  the way a port would have to — per-unit fields when set, else the
  heat-rate-keyed `CC_COMMITMENT_PARAMS` row (min-down 4/6/8 h; every gas-CC
  passes the ≥ 4 h gate). Any future PJM commitment mechanism must wire this
  table (or bin-level params) first; that wiring is now known to be necessary
  AND known to be not worth doing for this defect.
* **The incumbent PJM gas commitment mechanism is `cc_mustrun_per_plant`**
  (keeper `run_config.json`; D-2: 11.52 TWh forced CC_REGULAR in 2024, with
  `reliability_floor` 0.01 TWh and `ct_netload_drag` 0.02 TWh the only other
  CC entries). The rule-19 enumeration the charter demanded is discharged: a
  bridge would have been its second mechanism on the same phenomenon, and the
  pool measurement nets out what it already floors (1.0–1.5 GW overnight).
* The walk machinery (T7) validates cleanly against the keeper: in-merit MW
  reproduces dispatched thermal to **0.979 / 1.011 / 0.998** and the curve's
  baseline dual reproduces the load-weighted sidecar dual to **$0.10 / $0.03 /
  $0.10** — the 137.71-GW-style cross-check the handoff required.

## §6 — DO-NOT-REDO (binding on successors)

- **Do not re-charter a PJM gas commitment bridge — in any form (physical
  gap, economic/startup leg, posture, or floor variant) — against the
  overnight cell or the diurnal amplitude.** The cell is `R` on a
  pre-registered pre-check whose favorable-case arithmetic is measured: pool
  1.36–1.60 GW (net of the incumbent `cc_mustrun_per_plant` floor), bar
  2.57–3.37 GW, Δd $0.41–0.64 at full forcing, marginal ownership unmoved.
  Re-opening requires NEW evidence that the pool itself was mismeasured — not
  a different min-load fraction (the 0.574 scan is already the largest any ISO
  has measured) and not a different threshold (the $1.00 bar was committed
  before measurement).
- **Do not read the kill as "PJM CCs don't stay on overnight."** They do —
  94–100 % of the pool passes the restart screen. The model already delivers
  that behaviour through the merit order (19.5–22.2 GW in merit) plus
  `cc_mustrun_per_plant`; the bridge had nothing left to force.
- **Do not quote the first T7 run's `eligible_units: 0`.** It is a field
  artifact (§5), corrected in the same session before adjudication.
- **The amplitude defect's queue is EMPTY — do not manufacture a successor.**
  The terminal state is legitimate under rule 1 `[R-STRUCT]`; the alternative
  is an adder tuned to the residual (rule 13 forbids). New work on PJM price
  formation needs a NEW defect or NEW data, not a re-tread of this one.
- Carried forward unchanged and still binding **in full**: `FINDING-pjm141`
  §6, `FINDING-pjm140` §6, `FINDING-pjm139` §6, `FINDING-pjm138` §6,
  `FINDING-pjm137` §5, `FINDING-pjm136` §5, `FINDING-pjm135` §7,
  `FINDING-pjm134` §5/§8.

## §7 — matrix duties discharged this session (rule 28 duty b)

- `docs/codebase-site/data/mechanism-matrix.js`: `gas_commitment_bridge`
  cells `KKUUKK → KKRUKK` (PJM `U → R`), note + `ev.P` citation added; header
  stamped for pjm-142. No other ISO's cells touched (rule 25).
- `docs/mechanism-testing-matrix.md` §5.3: item 13 CLOSED with the pre-check
  numbers; the section header updated (queue empty, no open successor).
- No dashboard registration — **no run was solved** (rule 15 governs completed
  runs; there is none). No keeper edit — promotion/declaration is owner-only.

## §8 — handover: what is left for PJM, stated but NOT executed here

1. **OWNER DECISION NOW IN ORDER: declare PJM calibration-complete.** The
   keeper (`2026-07-30-pjm-140-rampenv`) is CALIBRATED on every criterion; the
   structural queue is measured empty (this session closed its last item); the
   remaining amplitude limitation is a diagnosed representation boundary that
   fails no gate, disclosed in the record (pjm-141, here). Declaring adds PJM
   to `complete` in `frontend/data/backcast/calibration-complete.json`
   (format: `"PJM": {"declared": ..., "keeper":
   "2026-07-30-pjm-140-rampenv", "by": ...}`), which unlocks the 2022
   validation one-shot under rule 22 (`--holdout-authorized`); the 2022 PJM
   data is already substantially intaken (2026-07-04 intake, 2026-07-22
   re-authorization, 2026-07-24 outage backfill — see the intake_log). The
   NYISO precedent (declared → withdrawn on the phantom-outage re-audit) is
   retired for PJM: its outage windows were byte-verified on the current
   detector at the 2026-07-24 intake.
2. **The owner-lane keeper-shard item carried from pjm-141**: `keepers/PJM.json`
   root cause (15) still names the W6 census as "the next instrument"; it
   should be restated to the flat-stack amplitude diagnosis with its
   now-empty, now-successor-free lever queue (pjm-141 answered the census;
   pjm-142 closed the successor).
3. **Queue item 10 (`winter_citygate_daily`, TETCO-M3) survives on the winter
   LEVEL story ONLY** — a rule-14 accuracy correction to the delivered winter
   basis, barred from the overnight/amplitude cell by the zero within-day σ
   (pjm-139 §6, tightened pjm-141 §4.1). It is an accuracy lane, not a
   calibration-gate lane, and does not block a completeness declaration.
4. Carried from pjm-137, still blocked on a measured sub-zonal load basis: the
   `PJM_Dominion` NoVA/Loudoun split.

## §9 — reproduction

```
PYTHONPATH=. .venv/bin/python scripts/probes/_pjm141_overnight_tranche.py \
    --bundle results/calibration/pjm140_rampenv_B \
    --out results/probes/pjm142_bridge_precheck.json
```

One fleet reconstruction per year (~7 min, ~4 GB, no LP, no swap).
`data/raw/pjm-zonal-lmp/`'s 36 DA parquets are gitignored and re-fetched
(`--feeds da_hrl_lmps`); all 36 verified byte-identical to the committed
manifest and `SHA256SUMS.txt` restored afterwards. `results/probes/` is
gitignored; the numbers above are the record and the probe script is
committed. Kill thresholds: `PRECHECK-pjm142-overnight-gas-commitment-bridge-
2026-07-30.md`, committed at `a2d72e4` before the first measurement ran.
