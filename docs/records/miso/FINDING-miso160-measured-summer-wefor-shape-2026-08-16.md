# FINDING — miso-160: the measured seasonal forced-outage shape replaces the 0.30 heuristic — **KEEPER**, promoted by the session's own pre-registered rule; C3b comes off its knife edge in all three years; C3a-2025 improves and still fails

**Session** miso-160 · **ISO** MISO · **Date** 2026-08-16 ·
**Keeper** `2026-08-16-miso-160-wefor-shape` (bundle `miso160_wefor_B`),
promoted from `2026-08-15-miso-159-cod-vintage`.

**PREREG** `results/calibration/PREREG-miso160-summer-wefor-measured-share-2026-08-16.md`,
pushed at **`a96702b`**, blob **`57d2b8b1`**, **verified byte-identical against
the FETCHED remote ref BEFORE the construction was built, the derive statistic
was computed, or any solve was launched** (rule 27 `[R-PUSH]`).

**Rule 22 `[R-HOLDOUT]`:** 2023 / 2024 / 2025 only, both arms, one
`--year 2023 2024 2025` invocation each, years sequential (rules 12 / 16).
MISO holds neither `complete` nor `final`; the holdout spend freeze is
untouched.

---

## 1. Provenance — the owner decision that unblocked the lever (rule 28(a))

The miso-159 queue named exactly one un-adjudicated lever bearing on the 2025
cushion: `SUMMER_WEFOR_SHARE = 0.30`, **gated on the owner's data-provenance
decision** (miso-157 §11 item 2: which measured record adjudicates a
forced-outage seasonal shape — the question miso-157's B-DISAGREE kill gate
could not answer for itself). **The owner took the decision this session**,
recorded in `docs/handoffs/miso-outage-grain-data-ask-2026-07.md` §9:

- **MISO's published MOM outage record is the admissible seasonal-shape
  source** — ticket-based (clears the standing ask's §2A, the criterion whose
  text already rejects "CAMPD … and every derivative"), cause-separated
  (§2E), daily and year-specific (§2C), MISO-footprint (§2D), and internally
  coherent (its `Planned` bucket moves out of summer, 0.56–0.66, agreeing
  with the model's separately-measured `MAINTENANCE_MONTHLY_SHAPE`, while its
  unplanned buckets run above annual as heat-correlated physics predicts).
- **CAMPD is inadmissible for outage measurement**: output-derived (§2A),
  documented phantom-outage bias whose class gradient miso-157 §5 measured,
  and **zero `CT_PEAKER` windows** — no measurement at all of the class that
  sets MISO's summer peak price.
- **§2a is amended to fleet grain for this one deliverable**: replacing a
  fleet-uniform scalar invents no unit/class attribution, so the miso-85/87
  closures are untouched; §2B/§2F stand for every other use of the ask.

## 2. The mechanism and the derived value

`ScenarioConfig.summer_wefor_share_override` (default `None` = byte-inert;
registered in `_CACHE_KEY_OPTIONAL_FIELDS` + the pinned-defaults ledger in
the same commit — default cache key verified unmoved vs HEAD, armed key
distinct). When armed it replaces the module constant in the seasonal WEFOR
split at both availability-builder sites and the `results/scarcity.py`
variance mirror; the mechanism itself is unchanged (rule 19 `[R-ONE-MECH]`):
summer gets `share × WEFOR`, the shoulder absorbs the displaced outage
energy, winter keeps flat WEFOR, per-unit annual mean conserved for ANY
share — including share > 1, the measured sign.

**The derived value (rule 23, basis fixed in the PREREG before computation):**
`R* = 1.0599` — the unweighted mean over 2023/2024/2025 of
[Jun–Sep mean offline MW ÷ annual mean offline MW], region `"MISO"`, causes
`Derated+Forced+Unplanned` (the GADS EFOR-family basis the WEFOR table
carries, which includes equivalent derated hours), through the production
loader `miso_outage_mw_series`. Per-year **1.1039 / 0.9671 / 1.1086** —
**V1 reproduces miso-157's published comparators to ≤0.0004** (bar ±0.01).
Pooled value inside P-1's [1.04, 1.08]; S-DERIVE silent. Companions
(per-bucket, per-region, Jun+Jul) are in the committed record. **The measured
sign REVERSES the heuristic: summer unplanned-outage rates sit 6 % ABOVE
annual where the 0.30 put them 70 % below.** No sweep, no alternative basis
tried.

**Population on this keeper:** all six non-coal thermal classes at full
statistical WEFOR (`wefor_residual = None`; `cc_nameplate_summer_derate`
off; coal exempt under `coal_drop_pof`; floor CTs and coal sync tranches
keep their bypasses) — exactly the population the 0.30 reached.

## 3. Validity gates — all PASS, one trigger fired on the instrument itself

| gate | result |
|---|---|
| **V1** — derive reproduces miso-157 | **PASS 3/3** (≤0.0004 vs ±0.01) |
| **V2** — control reproduces the committed keeper | **PASS, STRONGEST FORM: BIT-IDENTICAL.** 0 of 70,080 differing P1 zone-hour price cells in EVERY year; demand-weighted LMP 32.8306 / 30.5432 / 39.4959 equal to the keeper's committed sidecars to the 4th decimal. No K0-class drift — and the new field's off path is proven byte-inert at the FULL-SOLVE grain |
| **V3** — fleet identity, both arms | **PASS 3/3** (`n_gen` 2929/2923/2923; 6 carry zones) |
| **V4a** — winter invariance | **PASS 3/3, EXACTLY 0.0** for every unit in every winter hour |
| **V4b** — per-unit annual-mean conservation (rebuilt composition) | **PASS 3/3** (max 1.3e−17 vs 1e−9 bar); final-array residue ≤0.12 GW/yr (multiplicative overlay interaction, reported not gated) |
| **V5 / S-CACHE** — off-arm byte-inertness + cache keys | **PASS** (default key `603c2498bf71d21d` unmoved vs HEAD; armed key distinct; flip-guard suite green) |

**S-CONSERVE FIRED ONCE, AND THE DEFECT WAS THE INSTRUMENT'S OWN** — the
probe's first month masks used the real 2024 leap calendar against the
model's fixed non-leap clock (240 mis-labelled hours fired V4a for 2024).
Per the PREREG's stop-debug-disclose clause the probe was rebuilt on the
production `_hour_to_month_index` (the T-8 discipline it should have used
from the start), re-run, and **`R*` was unchanged at 1.0599** (2024's ratio
moved in the 5th decimal). The same defect class as miso-157's S-V1:
disclosed, not papered over.

## 4. The A/B, at full magnitude (arm − control)

**Reach (P-2, production arrays):** Jun–Sep thermal capability
**−3.46 / −3.59 / −3.67 GW** (2025 by class: CT_PEAKER **−1.541**, ST_GAS
−0.951, CC_REGULAR −0.943, CHP classes −0.23); top-200 Jun–Sep demand hours
−3.62 / −3.72 / −3.69 GW. CT_PEAKER landed on P-2's centre (1.55). Winter
untouched exactly; annual mean conserved.

**Prices (direction disclosed in the PREREG before the solve; none of it
claimed as calibration skill):** demand-weighted **+3.83 / +4.18 / +3.98 %
Jun–Sep**, **+0.68 / +0.68 / +0.69 % annual** (+0.22/+0.21/+0.27 $/MWh) —
UP in all three years, summer-concentrated, with the shoulder returning the
conserved outage energy as the mechanism requires.

**P-3's magnitude bands MISSED HIGH, reported at full size:** 2025 annual
registered +2.5 to +9 %, measured +0.69 %. The reach was exactly as
predicted; the price response per removed GW is far below the miso-159
episode that anchored the band, for two structural reasons: this removal is
summer-only into a cushion that is deep (~6.3 GW within $20/MWh of the 2025
clearing price, miso-153 D-1), and it RETURNS capability to the shoulder
where miso-159's vintage repair removed capability in all hours.

**The gates (registered runs, `calibration_verdict.py`):**

| criterion | control | arm |
|---|---|---|
| C3a mean LMP | −0.1 / −5.4 / **−13.1 % (2025 FAIL)** | +0.6 / −4.8 / **−12.5 % (2025 FAIL)** — improves **+0.60 pp** |
| C3b NRMSE | 0.080 / 0.113 / **0.200 (knife-edge)** | **0.079 / 0.109 / 0.181** — improves ALL years, 2025 off the knife edge |
| C3c >$200 h (ledgered) | 0 / 5 / 1 vs 30/37/88 | **3 / 6 / 4** — toward the actuals |
| C1 / C2 / C4 / C6 / C8 | all PASS (C1 16/16, free 12/12) | all PASS (C8 ST_GAS grounded share **falls** 47.4→46.2 % in 2025) |
| **Determination** | NOT-YET on C3a-2025 alone | **NOT-YET on C3a-2025 alone** |

S-2023 silent (2023 lift +0.68 % < +6 %; C3a-2023 +0.6 % < +5.0 %). S-TAIL
silent (4 h < 20). C3a-2025 is reported at full magnitude and **still
fails**; nothing here is offered as progress toward the tail half of the
miso-156 identity object.

## 5. Decision — PROMOTED per PREREG §7(a), no escalation

All three pre-registered conditions met: (1) **no criterion-year PASS→FAIL
flip** anywhere; (2) **C3a-2025 improved +0.60 pp ≥ 0.5**; (3) V1–V5 PASS
with S-2023 silent. Keeper → `2026-08-16-miso-160-wefor-shape`, on rules 1
`[R-STRUCT]` / 14 `[R-ACCURATE]`: a measured, owner-adjudicated input
replaces a self-declared uncited heuristic whose sign ran against the
physics, on the price-setting availability path. The favorable residual
direction was disclosed before the solve and is not the ground of adoption.
Both runs registered (rule 15); matrix cell `O → K` with the queue and
prose-header re-stamps in the same session (rule 28); the keeper shard and
`status/MISO.js` rebuilt and re-audited.

**A PREREG bookkeeping miss, disclosed:** §2 said the DOF ledger's residual
count falls 2 → 1, echoing the standing description of the share as "in the
DOF ledger under identification `residual`". The committed ledger carries no
separate entry for the share — it was an open rule-20 root-cause item in the
governance prose. The honest form of the improvement: ledger 30 → 31 entries
/ 2 residual (the new entry is `derived-measured`), and **the standing open
root-cause item on `SUMMER_WEFOR_SHARE` is RETIRED for MISO**.

## 6. Where this leaves the lane

1. **The blocker is still C3a-2025, now −12.5 % vs ±10 %.** The miso-156
   decomposition stands, with its availability channel now adjudicated and
   armed: the summer cushion has been shrunk by the full measured seasonal
   shape (~3.7 GW) and the miss narrowed only 0.6 pp — consistent with
   miso-156's own reading that the annual residue is bounded by the
   **C3c-adjacent above-cost/tail half** (18–47 % basis-sensitive, §4.2).
   Any further cushion lever needs a NEW measured identification with its
   own charter; rule 20 forbids closing the remainder with a tuned value,
   and the C3c ledger governs the tail half.
2. **The mechanism is exportable under rule 25**: each lane derives its own
   share from its own admissible ticket-based record (PJM holds a candidate
   in `data/raw/pjm-outages`); no value transfers; cells `U`.
3. **Session infrastructure, disclosed:** this container's git transport has
   no credentials (the miso-159 situation). Every text artifact traveled to
   the branch via the API path with per-blob byte verification; the
   implementation traveled as the verified three-piece patch under
   `.claude-transfer/miso160/` (reassembly sha256 `e0679f23…`); the binary
   artifacts (run payloads `runs/*.js`, bundle `hourly/*.parquet`, changed
   `bench/*.json.gz`) are manifested there with hashes for a follow-on git
   session — **the dashboard registration is not fully delivered until that
   push lands.**

---

**Artifacts.** Probe `scripts/probes/_miso160_wefor_shape_instrument.py`;
record `results/calibration/_miso160_wefor_shape_instrument.json`; unit tests
`tests/unit/config/test_miso160_summer_wefor_override.py` (4/4);
attestations `scripts/gen_miso160_attestation.py` (control 30/2, arm 31/2);
runs `2026-08-16-miso-160-control` (bundle `miso160_wefor_A`) /
`2026-08-16-miso-160-wefor-shape` (bundle `miso160_wefor_B`). PREREG
`a96702b`, blob `57d2b8b1`.
