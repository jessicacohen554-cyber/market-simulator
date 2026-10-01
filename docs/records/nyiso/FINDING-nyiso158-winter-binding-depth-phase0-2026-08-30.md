# FINDING nyiso-158 — post-seam phase-0: the winter binding-depth differential is the measured Transco TTC step, no measured driver reaches the sharpened re-open bar, C3b-2025 is wholly the two faces, and the CE-utilisation overshoot is not an envelope-identification defect

**Session:** nyiso-158, 2026-08-30. **NO SOLVE** — every number below is read or
recomputed from committed artifacts (the keeper bundle
`results/calibration/nyiso157_pararm_B` + its control, the committed run
payloads, the P-32 raw/clean intake, `constants.NYISO_INTERFACE_TTC_BY_MONTH`)
and the deterministic input-side attribution module. Freeze ACTIVE; no year
outside {2023, 2024, 2025} touched; zero fitted scalars; nothing armed,
disarmed, rescaled or scoped. Machine-readable measurement record:
`results/calibration/_nyiso158_winter_phase0.json`.

**Keeper under diagnosis:** `2026-08-30-nyiso-157-par-attribution`
(NOT-YET on {C3a, C3b, C3c} by the 2026-08-30 owner ruling).

One construction note against the handoff: the slim bundles carry **no
`network_*` sidecar** — the committed-format binding signal is the
EXECNOTE-nyiso157 §5 primary, the `system_<yr>.parquet` zonal-dual spread
`price(Capital_Hudson) − price(Upstate_West) > $0.50`, and that is what every
model-side binding number here uses.

---

## §1 — Task 1: why Feb-2023 binds ~98 % and the object months 13–42 %

### §1.1 The differential, exactly

Keeper (arm) cutset binding by month (spread > $0.50; fraction of month
hours), vs the measured Central East interface (MIS P-32
`CENTRAL EAST - VC`, hourly `flow_mw / positive_limit_mw`; complete sample,
100 % valid limits all three years):

| month | model bind frac | measured bind95 | measured bind90 | measured mean util | applied TTC (MW) | measured p50 RT limit |
|---|---|---|---|---|---|---|
| Jan-2023 | **1.000** | 0.220 | 0.680 | 0.910 | 1,950 | 1,920 |
| Feb-2023 | **0.963** | 0.146 | 0.717 | 0.904 | 1,875 | 1,780 |
| Dec-2024 | 0.132 | 0.065 | 0.223 | 0.791 | 3,075 | 3,065 |
| Jan-2025 | 0.419 | 0.269 | 0.507 | 0.884 | 3,175 | 3,205 |
| Feb-2025 | 0.183 | 0.077 | 0.256 | 0.802 | 3,075 | 3,015 |

(The shard's "18–31 %" re-open prose reconciles exactly: Jan+Feb windows,
262/1,416 h = 18.5 % in 2024 and 435/1,416 h = 30.7 % in 2025.)

### §1.2 The component ledger — the differential is the measured TTC step

Monthly-mean west-side ledger (committed sidecars + recomputed attribution
input; MW): the **west base surplus**
(nuclear + hydro + wind + attributed-UW-envelope − UW demand) is **nearly
constant across every winter month of all three years, ~3.0–3.6 GW**. What
moved is the denominator. Deltas of each component, object month minus
Feb-2023, signed toward binding:

| vs Feb-2023 | ΔTTC (against) | ΔUW envelope | Δnuclear | Δhydro | Δwind | −ΔUW demand | Δ(surplus−TTC) |
|---|---|---|---|---|---|---|---|
| Dec-2024 | **+1,200** | +232 | +2 | −92 | +148 | −220 | **−1,130** |
| Jan-2025 | **+1,300** | +667 | −11 | −293 | +371 | −554 | **−1,120** |
| Feb-2025 | **+1,200** | +471 | −18 | −564 | +189 | −370 | **−1,492** |

The applied CE TTC is itself a measured input (calendar-month mean DAM
postings, `NYISO_INTERFACE_TTC_BY_MONTH`): 1,875–1,950 MW in Jan/Feb-2023 →
3,050–3,175 MW in the object months — **the NY Transco AC upgrade, in service
Dec-2023, +1,200–1,300 MW**. That single measured step is 80–107 % of the
headroom change on its own; measured 2025 hydro decline (−290 to −560 MW,
EIA-930-pinned) and UW demand growth (+220 to −554) deepen it; the deeper
2025 UW envelope and wind offset only part.

### §1.3 The measured interface does not do Feb-2023-like depth either — in any month

The re-open bar sharpened at nyiso-157 reads *"binding the cutset in the
OBJECT months at Feb-2023-like depth (~98 % of winter hours)"*. Measured
against NYISO's own posted interface conduct, **that regime does not exist in
reality**:

* Real Feb-2023: the interface sat at ≥ 95 % of its posted limit **14.6 %**
  of hours (≥ 98 %: 0.9 %; ≥ 90 %: 71.7 %; mean util 0.904). The model's
  96–100 % binding at the 1,875 MW pre-Transco pipe is **LP bang-bang
  saturation**, an overshoot of a hovering-at-0.9 real regime — the same
  overshoot the CE-utilisation report line carries (model 0.975 vs measured
  0.807 annual, §3).
* Real object months: bind95 6.5 % (Dec-24) / 26.9 % (Jan-25) / 7.7 %
  (Feb-25). The model's 13.2 / 41.9 / 18.3 % sits **inside the measured
  bind95–bind90 bracket** in all three — the keeper's binding *frequency* in
  the object months is roughly faithful. What Feb-2023 has is not more truth
  but a smaller denominator.

### §1.4 The driver search — none produces it

Every admissible measured driver checked, each moving the wrong way or an
order too small (full rows in the JSON, `t1_driver_search`):

1. **Measured CE limits** (the one driver that would mechanically raise
   binding): RT limit medians in the object months (2,965–3,205) sit at/above
   the applied DAM monthly means, p10 RT limits 2,900–2,995 ≥ applied —
   adopting them binds **less**. BLOCKER-C stands closed and is not
   re-opened; this is the same direction it recorded.
2. **Attributed UW envelope**: already the measured p90; the measured seam
   itself declined (UW attributed realized mean 1,128 → 741 MW annual,
   2023 → 2025 — the HQ/Ontario import collapse is real). PREREG-nyiso126
   §8-3 honoured: no rescale, no scoping.
3. **Upstate supply**: hydro measured-pinned and down (Feb −564 MW); nuclear
   flat; wind +189 MW (Feb) against a +1,200 MW step.
4. **UW demand**: measured-load-driven and up (+370 MW Feb).
5. **Reality itself** (§1.3): the object-month regime is partial binding.

**Verdict: NONE.** The sharpened re-open condition's first leg
("Feb-2023-like depth in the object months") is **unreachable by any
admissible measured driver, and describes a model-overshoot regime rather
than a real one**. The dose-response in the companion record confirms the
mechanism reading: iroquois W-K3a recovery tracks the keeper's binding
fraction almost monotonically (13 % → 0.07–0.14; 18 % → 0.14–0.16;
42 % → 0.41–0.51; 96–100 % → 0.54–1.65). With the first leg closed on
measurement, the sharpened condition reduces to its second leg: **the Leg-2
in-city commitment identification (INTAKE-SPEC-nyiso156 §2, owner-executable)
is the only identified route to the winter face.** `nyiso_iroquois_winter_spread`
stays R; nothing here re-tests it.

### §1.5 What the real premium is made of instead (adjacent evidence, honestly bounded)

Feb-2024 is the only winter month with both hourly zonal RT LMPs and P-32 on
disk. There, ~**96 % of the real CH−UW premium mass forms OUTSIDE bind95
hours** (bind95 1.4 %, in-bind $6.02/h vs out-bind $2.25/h). The LP's spread
is 100 % inside binding hours by construction (equal duals otherwise). The
object months are not measurable on-disk (RTM coverage: 2023 Jun+Dec, 2024
Feb–Jun+Sep, 2025 Aug), but the arithmetic bound is stated in the JSON: for
the real Feb-2025 $27.1 monthly spread to live entirely in its 52 bind95
hours would need a $352/h average across them — implausible; Jan-2025's
$137/h is plausible. At least Feb-2025 therefore carries a substantial
non-binding-hour premium component that **no cutset-binding mechanism of any
depth can produce** — consistent with, and sharpening, the Leg-2 routing.

---

## §2 — Task 2: C3b-2025 is wholly the two-face object

Scorer-exact reproduction (payload `pMon`·`dMon` vs bench `rt_lw_mon`): arm
**0.2034**, control **0.1973** — both to the recorded digit.

| month | actual | arm model | err | share of squared error |
|---|---|---|---|---|
| Jan | 111.20 | 87.42 | −23.8 | 27.3 % |
| Feb | 99.40 | 76.34 | −23.1 | 25.7 % |
| Jun | 78.42 | 51.28 | −27.1 | 35.6 % |
| Jul | 79.63 | 65.38 | −14.3 | 9.8 % |
| other 8 months | — | — | |err| ≤ 3.4 | **1.6 % combined** |

The four face months carry **98.4 %** (arm; control 97.9 %) of the squared
error. Counterfactual month-replacement: winter face closed → **0.1394**;
summer face closed → **0.1503**; both → 0.0255. **Either adjudicated face
alone returns C3b-2025 under the 0.20 bar** — exactly the nyiso-156 C3a
structure. The arm's knife-edge crossing (0.1973 → 0.2034) is the same two
faces deepening ~$1–2/month each; no new month enters.

**Verdict: C3b-2025 has no third component and needs no lever of its own —
it closes with the faces.** (Construction note: recomputing model months from
the raw `system_*` duals gives 0.227/0.221 — the payload months include the
registered scarcity-overlay layer the scorer scores; the payload is the
scored object and is what this section uses.)

---

## §3 — Task 3: the CE-utilisation overshoot is not an identification defect in the attributed envelope

The measured object reproduces exactly: median hourly `flow/limit` over the
complete P-32 sample = **0.807 / 0.616 / 0.591** (2023/2024/2025). Audit of
the measured construction found **no defect**: sample complete (zero
invalid-limit hours in all three years — no availability-window conditioning
in the measured medians); PAR availability windows (P-33) verified (K7
reproduces the nyiso-127 shares to 4dp, year-shares stable 0.068–0.070 NYC);
the p90 × (month × hour-of-day)-bin envelope tracks the realized p90
faithfully, with winter export-hour distortion ~0 (Dec 5–10 %, correctly
reducing the cap). The caps exceeding realized *means* by 1.5–1.9× is what a
p90 capability bound over a supply distribution is, not an error. **Nothing
is rescaled or scoped (PREREG-nyiso126 §8-3).**

The overshoot decomposes as:

* **Denominator artifact, small:** the model's util is read against the
  applied monthly-mean DAM TTC, the measured against hourly RT limits.
  At identical denominators the measured medians read 0.753/0.608/0.581 —
  the artifact is 0.053/0.008/0.009 of a 0.147–0.193 gap.
* **Numerator, the object:** the LP moves **+355 / +439 / +577 MW** more
  across CE at the median than the measured interface. Sources, in
  mechanism order:
  1. **LP pinning with zero operating margin** — reality holds CE below its
     limit in essentially every hour (bind98 ≤ 1.5 % in every month of all
     three years) while the LP saturates the cap whenever east marginal cost
     exceeds west (annual spread-hours 86 %/20 %/34 %). Same model-class
     family as the ledgered C3c: an LP carries no conduct/security margin.
  2. **Placement freedom under the pinned total** —
     `nyiso_import_reconciliation` pins the monthly seam total to EIA-930;
     placement across border links is LP-free within the p90 caps, so
     hub-priced west import fills UW toward cap in expensive-east hours
     where reality delivered mean depth.
  3. **Missing east-side commitment** — every real in-city/downstate
     AORR-committed MW absent from the model is replaced by an import across
     CE: **the BLOCKER-B / Leg-2 object seen from the flow side.**

**Verdict: the envelope construction stands as measured; the overshoot is
model-class conduct (1, 2) plus the Leg-2 identification gap (3). No
mechanism change is proposed from this residual, per §8-3 and rule 13.**

---

## §4 — What this closes, what it routes, what it does not touch

* **CLOSED ON MEASUREMENT:** the search for a measured driver that would
  bind the cutset at Feb-2023-like depth in the object months (§1.4). The
  iroquois re-open condition's first leg is unreachable; the cell stays
  **R** untested, with this finding appended to its evidence.
* **ROUTED:** the winter face of C3a-2025/C3b-2025 rests on **Leg 2** (the
  owner-executable MyNYISO as-enforced AORR intake, INTAKE-SPEC-nyiso156
  §2) — now supported from three independent committed measurements: the
  companion dose-response, the non-binding-hour premium mass (§1.5), and
  the CE flow-side import substitution (§3.3).
* **CONFIRMED:** C3b-2025 is not a third object (§2); it needs no lever and
  closes with the faces. The summer face stays the ledgered C3c limitation.
* **NOT TOUCHED:** BLOCKER-C (Tier-3 TTC re-grounding) stays closed — §1.4's
  limit check reproduces its direction and re-opens nothing. No holdout
  year, no hydro-pair re-tune, no scarcity parameter, no share rescale.
  `nyiso_seam_deliverability_envelope` stays armed-but-shadowed (rule 19).
  The determination stays NOT-YET as the owner wrote it; nothing here is a
  promotion or a re-verdict.

**Rule 13 note on the one number that could tempt a lever:** the applied
monthly-mean DAM TTC vs the measured hourly RT limit series is a
data-alignment question in principle (rule 14), but §1.4-1 measures its
direction — hourly limits would *loosen* the object months — so the accurate
input is already the tighter one and BLOCKER-C's misalignment clause stands
unchanged.
