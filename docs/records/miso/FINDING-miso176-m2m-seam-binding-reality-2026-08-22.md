# FINDING miso-176 — the M2M/CMP record NAMES the binder in about half the scarce hours: seam-class congestion management co-moves with MISO stress, restriction-consistent, with MISO OVER its own entitlement — and every zero-DOF encoding is refused (`m2m_seam_entitlement_cap` minted `G`)

**Session miso-176 (2026-08-22).** Executes miso-174 §7 item 3: the M2M/CMP
seam-class data intake and the binding-reality measurement behind the
scarce-hour seam response. **NO LP SPENT. Keeper `2026-08-22-miso-175-hourkey`
UNCHANGED; no ScenarioConfig field added; no run registered** (rule 15 not
engaged; the miso-142…174 no-LP precedent). Determination unchanged:
**NOT-YET on C3a-2025 alone**, C3c the single ledgered caveat.

Deliverables landed on this branch:

| piece | artifact |
|---|---|
| intake (schema/fetch/curate/tests/README/dictionary) | `miso-m2m-flowgates` datatype, commit `9d4681c` |
| prereg (kills fixed BEFORE gated quantities) | `PREREG-miso176-m2m-seam-class-adjudication-2026-08-22.md`, commit `75b8488` |
| instrument + record | `scripts/probes/_miso176_m2m_seam_binding.py` → `_miso176_m2m_seam_binding.json` |

## 0. The verdict

**`m2m_seam_entitlement_cap` at MISO: minted `G` (governance-refused), by the
pre-registered verdict mapping** (PREREG §8, row 3): the measured outcome is
**A-2 CO-MOVES (3/3 years) + A-3 RESTRICTION-CONSISTENT (2/3)** — the
phenomenon is real and the record names it — **and no construction survives
K-1/K-2**: any encoding conditioned on the measured binding state, shadow
prices or market flows is answer-class (rule 13, the charter's fixed line),
and any seam-MW bound derived from the input-class FFEs is branch-grain data
placed on a seam-aggregate link with no published distribution factors — the
standing M1/miso-77 §5.2 apportionment refusal. The evidence transfers to
owner item 5(i), the coincident-peak seam-response envelope ruling (§5).

## 1. The intake

MISO's public annual `M2M_Settlement_srw_YYYY.csv` (the miso-77 §2a
seam-class series, same no-auth channel as bc_HIST) is now a curated
datatype: hourly per-flowgate rows for both M2M seams (PJM, SWPP) carrying
both parties' RT shadow prices, market flows, Firm Flow Entitlements and
settlement credits — 124,821 / 162,394 / 181,989 rows, 309/385/401
flowgates, every hour of every year covered by some flowgates. Mirrors are
gitignored with sha256 README rows (bc_HIST precedent); the clean partitions
regenerate via `fetch_miso_m2m_flowgates.py` + `curate_miso_m2m_flowgates.py`.
The rule-13 line is fixed in the schema header: FFE columns input-class in
kind; shadow/flow/credit columns ANSWER-class, validation only.

## 2. V-KEY — the clock was verified, not assumed

The source stamps are hour-ending 1..24 on fixed EST (HE 24 posted
"24:00:00"; full 24-label days all year — no DST seam). The measured leg:
`2025_rt_bc_HIST` carries a `Flowgate NERCID` column, so the settlement
record joins MISO's own RT binding record **on ID, no token matching**.
Across 8 joined flowgates (each ≥ 300 M2M binding hours, ≥ 100 shared),
correlating the hourly M2M `miso_shadow` series against the bc_HIST
hourly-mean |SP| under key shifts −3..+3: **shift 0 wins at pooled
r = 0.9934** — the two publications are the same clock and, to hourly
integration, the same physical quantity. **V-KEY PASS**; V-SETS reproduces
n = 11/14/47 exactly; the pre-registered ±1 h robustness re-run leaves every
A-2 conclusion standing at shifts −1/0/+1.

## 3. The measurement

**A-1/A-2 — binding co-moves with MISO's scarce hours, all three years.**
PJM-seam coordination is present in 91/100/98 % of the scarce hours and
BINDING in 36/57/49 % of them. Binding intensity vs the seam's own summer
baseline:

| year | mean binding flowgates/h, scarce vs summer | R_cnt | mean Σ-shadow $/h, scarce vs summer | R_ssp |
|---|---|---:|---|---:|
| 2023 | 0.55 vs 0.30 | **1.81** | 258 vs 68 | **3.82** |
| 2024 | 0.79 vs 0.69 | 1.15 | 476 vs 90 | **5.31** |
| 2025 | 1.06 vs 0.46 | **2.32** | 692 vs 121 | **5.74** |

The pre-registered CO-MOVES condition (R_cnt ≥ 1.5 OR R_ssp ≥ 2.0 in ≥ 2 of
3 years) is met **3/3**; the shadow-price basis says the binding that does
occur at MISO's stress is 4–6× harder than ordinary summer binding.

**A-3 — restriction-consistent, on the pre-registered directional split.**
Measured PJM-seam net import (EIA-930 DIBA, the keeper's −1 h key) over
summer hours: top-quartile-binding hours vs zero-binding hours:

| year | top-binding import | zero-binding import | split | pre-reg line (≤ −0.3 GW) |
|---|---:|---:|---:|---|
| 2023 | +5.68 GW | +5.74 GW | −0.06 | miss |
| 2024 | +3.56 GW | +4.14 GW | **−0.58** | clears |
| 2025 | +3.50 GW | +4.72 GW | **−1.22** | clears |

2/3 clears → **RESTRICTION-CONSISTENT** (the INCONSISTENT line — at/above
in ≥ 2 of 3 — is nowhere near firing; r(import, binding) is negative in all
three years: −0.125/−0.216/−0.295 on counts).

**A-4 — when the seam class binds at stress, MISO is OVER its firm
entitlement.** On the scarce-hour binding rows, MISO's market flow exceeds
its FFE on **67 / 82 / 80 %** of rows (top-47-load set: 79/84/76 %; ordinary
summer: 53–68 %). The JOA's congestion-management obligation in exactly
those hours is to push MISO's use back TOWARD its entitlement — measured
M2M physics that restricts MISO's seam utilisation when MISO is tight,
with the counterparty also over on 50–82 % of rows (a genuinely short
constraint, not a one-sided allocation artifact).

**A-5 — the binder, by name.** The scarce-hour binding census (verbatim in
the record) is concentrated: 6/8/13 distinct flowgates. 2025 is dominated by
`CherryValley_SilverLake 345 flo Byron` (PJM-monitored, 15 of 47 scarce
hours, p50 shadow $699) and `Burr_Oak_Plymouth 138 flo Burr_Oak_Hip`
(MISO-monitored, 10 h, p50 $1,304) — border-region facilities of the
MISO–ComEd/northern-Indiana seam, at shadow prices ($500–1,500) that are
hard congestion, not noise.

## 4. The honest half: it is a PARTIAL explanation

Post-registration exploratory context (record `stage6_exploratory_postreg`,
added after the gates resolved and labelled so): within the scarce hours,
measured PJM-seam net import in the BINDING subset vs the NON-binding
subset vs the summer mean:

| year | binding subset | non-binding subset | summer mean |
|---|---:|---:|---:|
| 2023 | 5.20 (n=4) | 4.71 (n=7) | 5.66 |
| 2024 | 3.37 (n=8) | 3.55 (n=6) | 3.99 |
| 2025 | **2.93** (n=23) | 3.92 (n=24) | 4.46 |

In 2025 the pull-back concentrates hard in the binding hours (−1.54 GW below
summer mean when binding vs −0.54 when not). But the non-binding scarce
hours sit below the summer mean in ALL three years too: the M2M record
names the binder for roughly half the scarce hours and leaves a residual
pull-back — TLR-class events on non-M2M paths, PJM-internal congestion
deeper in its footprint, scheduling conservatism — unnamed. The miso-174 §3
coincident-stress object is therefore **partly measured congestion
management and partly still conduct**, and no claim beyond that is made.

## 5. What this hands to owner item 5(i)

The coincident-peak seam-response envelope (an envelope conditioned on the
NEIGHBOUR's own load — miso-174 §7 item 2, the owner admissibility call this
session raises and does not decide) inherits material evidence: the seam's
negative response to MISO stress is now measured to coincide, in about half
the hours and hardest in 2025, with **real, hard, named JOA congestion
management in which MISO sits over its firm entitlement**. That is exactly
the physics a coincident-stress-conditioned envelope would encode — market
design responding to coincident regional stress — and it is NOT a
residual-fit artifact. The admissibility line (forward driver vs pinned to
the residual) remains the owner's to draw; this measurement sharpens what
the envelope would be encoding.

## 6. Reported against interest

* **2023's directional split is −0.06 GW — essentially zero.** The
  restriction-consistency verdict rests on 2024/2025; 2023 (n=4 binding
  scarce hours) contributes co-movement (R_cnt 1.81, R_ssp 3.82) but no
  measurable import suppression in the quartile split.
* **2024's count-basis ratio is flat (R_cnt 1.15, below even the 1.2
  refuted-leg line);** only the shadow-price basis (5.31) carries 2024's
  CO-MOVES. Binding was not much more FREQUENT at 2024's stress — it was
  much HARDER.
* **Binding covers only ~half the scarce hours** (36/57/49 %), and the
  non-binding half still pulls back (§4). Anyone quoting this finding as
  "M2M congestion explains the over-import" is over-reading it.
* **The 2024 EIA-930 internal inconsistency** (DIBA↔BALANCE TI r = 0.8286;
  miso-174 §5) attaches to every 2024 measured-flow number here (A-3,
  stage 6). The A-2/A-4 legs are EIA-930-free.
* **V-VINTAGE drift**: the per-seam model-side context numbers read from
  `miso169_gated_A`'s `unit_hourly` drift vs the CURRENT keeper by
  −0.046/−0.069/−0.157 GW in the scarce sets (disclosed in the record); no
  gate consumes them.
* **One winter boundary hour per year** is uncovered by the EST→CST
  partition mapping (disclosed in the record; all scored sets are summer).
* **SWPP seam**: binds MORE in absolute terms in scarce hours
  (1.45/1.07/1.87 flowgates/h) and its SSP basis also co-moves
  (2.05/2.05/3.05). Measured and reported; no verdict is minted for any
  SWPP-facing mechanism, and the SWPP seam's own gap flips sign by year
  (miso-174 §1).

## 7. Standing OWNER items, restated not decided (charter item 5)

Carried forward from miso-171/172/173/174/175; this session raises them and
decides none:

1. **The coincident-peak seam-response envelope admissibility ruling**
   (miso-174 §7 item 2 verbatim) — now the named successor for the seam
   lane, holding this session's evidence (§5). An envelope conditioned on
   the neighbour's own load is a forward driver in kind but correlates with
   MISO scarcity by coincident peak; where "conditioned on an exogenous
   forward driver" ends and "pinned to the residual" begins is an OWNER
   call. Nothing was built.
2. **The C8 provenance-materiality floor** — the rubric hole is unrepaired
   (C8's provenance leg has no materiality floor; the miso-173 mask cleared
   the plant-990 instance only as a side effect).
3. **The committed-vs-regenerated diagnostics exposure** (MISO and PJM,
   measured) — unchanged in kind; nothing here touches diagnostics.
4. **`RHO_CLIP` 0.5 vs the measured MISO rho 0.1764** (nyiso-144) — still
   the standing escalation; no new claim.
5. **MISO's determination posture** — C3a-2025 is the SOLE failing
   criterion, documented end to end as a model-class limit (miso-163 ruling
   + FINDING-miso171 §6), on a keeper with ZERO D-4 conduct failures, C6
   attested, C8 PASS all years, C3c the single ledgered caveat. Whether
   `NOT-YET` should be adjudicated to a declaration is an OWNER question —
   riper again: the seam lane's last named data gap (miso-174 §7 item 3) is
   now measured and adjudicated, and the largest remaining seam question is
   an owner ruling, not a session's work.

## 8. The honest ceiling, restated after the result

**C3a-2025 stays CLOSED end to end as a model-class limit** (miso-163;
FINDING-miso171 §6). The over-import this lane addresses is worth
≤ +3.3/+7.7/+3.9 $/MWh at the model's own slope even at its inadmissible
upper bound (miso-174 §5) — nothing in this finding is claimed against
C3a-2025, and no number here may be quoted as scarcity progress.

## 9. Governance

Rule 22: 2023–2025 only; MISO holds neither `complete` nor `final`; spend
freeze untouched; no marker re-key owed. Rule 28(b): `m2m_seam_entitlement_cap`
minted as a new base row with a cell line in every shard in this PR
(MISO `G` with this evidence; PJM `U` — its side of the same JOA record is
PJM's lane's call, rule 25; the other four `.`). Rule 15 not engaged — no
solve. DO-NOT-REDO honoured throughout (nothing re-opens
`measured_interface_limits`, `import_shape_lever`, the C3a lane, the
congestion cells, the copper-plate reading, or the hour-key convention).
The SOUTH under-export (miso-174 §7 item 4) remains the next unchartered
seam component; this session's alternative branch was not needed (the
intake was not blocked).

## 10. Reproduction

```
python3 scripts/data/fetch_miso_m2m_flowgates.py          # mirrors (gitignored)
python3 scripts/data/curate_miso_m2m_flowgates.py         # clean partitions
python3 scripts/data/fetch_miso_bc_hist.py --years 2025 --markets rt   # V-KEY comparator
python3 scripts/probes/_miso176_m2m_seam_binding.py       # gates + record
```

Reads `results/calibration/miso175_hourkey/hourly/{system,class_hourly}_<y>.parquet`,
`miso169_gated_A/hourly/unit_hourly_<y>.parquet`,
`data/clean/miso-m2m-flowgates/MISO/*.parquet`,
`data/raw/transfer-constraint-binding/MISO/2025_rt_bc_HIST.csv.gz`,
`data/raw/eia-930-interchange/MISO interchange hourly.parquet`,
`data/raw/MISO_region.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`.
