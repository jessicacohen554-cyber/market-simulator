# FINDING miso-171 — the reserve-requirement decomposition: the synchronised share is already gated, the supplemental share may not be, and the sub-regional extension is measured inert

**Session miso-171 (2026-08-20).** Executes THE PREREQUISITE of the miso-171
charter (`FINDING-miso170-scarcity-reserve-supply-anatomy-2026-08-19.md` §5):
decompose the `miso_subregional_or_midwest` and `miso_rbdc` requirements into
their SYNCHRONISED (regulating + spinning) and NON-SYNCHRONISED (supplemental)
components from MISO's own published product definitions and measured cleared
series, and only then decide whether the sub-regional gating lever exists.

**NO LP SPENT. Keeper `2026-08-19-miso-170-sitegrain` (`miso170_layup_B2`)
UNCHANGED; nothing armed, no `ScenarioConfig` field added, no run registered**
(the miso-142/153/155/156/157/161/163/164/167 no-LP precedent; rule 15
`[R-DASHBOARD]` not engaged). Instrument:
`scripts/probes/_miso171_reserve_product_decomposition.py` (5 stages,
read-only), record `results/calibration/_miso171_reserve_product_decomposition.json`.
Every number below reproduces from committed artifacts by running that script.

**The verdict, against the charter's three outcomes: MIXED — and the mixed
lever, once measured, is INERT on this keeper.** The synchronised share of the
sub-regional requirement is 58 % in the 2025 scarce hours, so a gateable share
exists in kind; but the extension adds **zero new gated volume** (the
synchronised share is exactly the 1,617 MW the keeper's armed market-wide gate
already covers, re-cut locationally), and its incremental binding surface
measures **3 scarce hours in 2025 and 0 hours in all of 2023 and 2024** — under
the inertness standard this lane itself pre-registered (PREREG-miso167 §3
K-PRE-A), that is a DO-NOT-SOLVE. With it, the DA-foreseen half of the
C3a-2025 miss closes end-to-end (§6).

---

## 1. The decomposition (stage 1–2 of the instrument)

Measured cleared MW by region × product from MISO's real-time ASM
cleared-offers record (`data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet`) —
the SAME parquet, hour key (`_to_model_hour`) and product sets the solve-path
loader (`data.reserve_requirements.load_miso_reserve_requirements`) feeds the
LP families, so this split is exactly the split the families see. Scarce set =
top-47 hours by keeper system load within Jun–Sep (the FINDING-miso167 §1 /
FINDING-miso170 §7 set; the keeper-family means below reproduce the
FINDING-miso170 §2 table to the MW).

**2025, the 47 summer scarcity hours (means, MW):**

| family (requirement basis) | OR total | reg+spin | supp | sync share |
|---|---:|---:|---:|---:|
| `miso_rbdc` (market = N+C+S) | 2,488.1 | 1,616.8 | 871.3 | **0.650** |
| `miso_subregional_or_midwest` (N+C) | 2,073.3 | 1,207.6 | 865.8 | **0.582** |
| `miso_zonal_or_miso_south` (S) | 414.7 | 409.3 | 5.5 | **0.987** |

All years (scarce-47 sync share; annual share in parens): market
2023 0.628 (0.550) / 2024 0.644 (0.569) / 2025 0.650 (0.587); Midwest
2023 0.616 (0.488) / 2024 0.581 (0.504) / 2025 0.582 (0.501); South
2023 0.994 (0.959) / 2024 0.998 (0.959) / 2025 0.987 (0.976).

Identities, verified exact (stage 3): Midwest OR + South OR = market OR with
max |diff| = 0.0 MW in every hour of every year; and each keeper family's
`requirement_mw` equals the measured series it claims to carry to **0.0 MW**
in the scarce set (`miso_rbdc` = market OR, `miso_subregional_or_midwest` =
N+C OR, `miso_rbdc_regspin` = market reg+spin, `miso_zonal_or_miso_south` =
South OR).

**Notable structure in the measurement itself: essentially ALL of MISO's
cleared supplemental reserve is held in the Midwest.** Market supp 871.3 vs
Midwest supp 865.8 MW (2025 scarce hours); the South reservation is ~99 %
synchronised in every year. The Midwest sub-regional family is therefore the
family with the LOWEST synchronised share, not the highest.

## 2. The product-definition basis (every split cited)

Source: **MISO Energy and Operating Reserve Markets Business Practices Manual,
BPM-002-r23, effective SEP-30-2022** (in force entering the 2023–2025
calibration window; obtained as the public docket copy in KY PSC Case No.
2022-00402 — MISO's own BPM library serves only the current revision. Page
numbers are the document's printed "Page N of 327").

* **Regulating Reserve is a synchronised product.** §4.2.1.1.2 (p. 73),
  Real-Time Resource Eligibility: "synchronized Generation Resources;
  synchronized DRRs-Type II; and available External Asynchronous Resources and
  Stored Energy Resources."
* **Spinning Reserve is a synchronised product.** §4.2.1.2.2 (p. 75),
  Real-Time Resource Eligibility: "Synchronized Generation Resources;
  Uncommitted DRRs-Type I with a Contingency Reserve Status of 'online';
  Synchronized DRRs-Type II; and Available External Asynchronous Resources."
  (§4.2.1.2, p. 73, carries the deployment qualifications.)
* **Supplemental Reserve is NOT a synchronised product — offline quick-start
  is expressly eligible.** §4.2.1.3 (p. 75): "Only Resources registered as
  Quick Start will be eligible to clear as off-line Supplemental."
  §4.2.1.3.1 (p. 76, day-ahead) and §4.2.1.3.2 (p. 77, real-time) both list
  "uncommitted Quick-Start Resources (Only for offline Supplemental)"
  alongside "synchronized Generation Resources" — supplemental may be held
  online OR offline. **Gating a supplemental requirement to synchronised
  capacity is therefore a rule-1 [R-STRUCT] breach**, exactly as the charter
  stated.
* **MISO's own construct decomposes reserve requirements into spinning vs
  supplemental components — market-wide and per zone.** §3.6.2.2 (pp. 56–57):
  MISO "posts the MISO BA Spinning Reserve requirement and Supplemental
  Reserve requirement" separately (the worked example: 640 MW spin / 960 MW
  supp), and Exhibit 3-2 (p. 57) tabulates PER-RESERVE-ZONE "Minimum
  Contingency Reserve Requirement / Minimum Spinning Reserve Requirement /
  Minimum Supplemental Reserve Requirement", fn. 5: "Determined by the
  Reserve Zone Requirements Study." The synchronised/non-synchronised split
  of a locational requirement is thus MISO's own published construct, not a
  model invention.
* The measured per-product cleared series (`asm_rt_cleared_mw_<y>`,
  region × {reg, spin, supp}) is the revealed realisation of those
  requirements — the same rule-13 revealed-reservation basis the keeper's
  families already adopt (miso-56/miso-71).

## 3. Half the charter's candidate is ALREADY IMPLEMENTED: `miso_rbdc`'s synchronised component is the armed nested family

The charter's candidate read "extend online-gating to
`miso_subregional_or_midwest` … and possibly to the Reg+Spin component inside
`miso_rbdc`". The second half is **already the keeper**: the nested
`miso_rbdc_regspin` family (armed via `miso_reserve_online_gated` since
miso-169, keeper-carried since miso-170) has a requirement measured-identical
to the market reg+spin series (§1: 0.0 MW difference), draws on the GATED
product columns only, and binds 12 h of 2025 (max $85.87). Because gated
awards count toward `miso_rbdc` too (the nested draw), the LP must already
back the synchronised 65 % of `miso_rbdc` with online capacity; **the family's
ungated margin is exactly its supplemental share** (871 MW in the 2025 scarce
hours). By §2's citations that share is legitimately providable by offline
quick-start capacity — of which the model carries 8.0 GW in the scarce hours
(miso-169 pre-check H_off) against an 871 MW need — so `miso_rbdc`'s zero
marginal dual is **correct in kind, not a defect**. There is no further
admissible gate on `miso_rbdc`.

## 4. The residual lever, sized: locational re-allocation only, and measured inert

What remains gateable is the **locational** synchronised split: nested gated
Reg+Spin legs for Midwest (1,207.6 MW, 2025 scarce mean) and South
(409.3 MW). Two measured facts size it:

**(a) It adds ZERO new gated volume.** Midwest reg+spin + South reg+spin =
market reg+spin exactly (1,207.6 + 409.3 = 1,616.9 ≈ 1,616.8, the loader
identity) — i.e. the charter's "up to ~2 GW of additional gated requirement,
roughly doubling to tripling miso-169's gated base" premise is **false as
measured**: the base does not grow at all. The extension only forces the
already-armed 1,617 MW to sit in the right region.

**(b) Its incremental binding surface is ~3 hours (stage 5).** Replicating
the miso-169 §3 pre-check's own H_on instrument (reserve-eligible plants,
plant-grain online threshold, headroom = cap − mw) at REGIONAL grain on the
committed `miso169_gated_A` unit_hourly (bit-identical to the miso-160-era
keeper P1; the miso-170 lay-up census delta is disclosed in the instrument —
it removes online ST_GAS output, so these counts are a floor but a shallow
one), against the regional reg+spin requirements:

| 2025 | short in scarce-47 | short all year | incremental (regional-short, market-NOT-short) |
|---|---:|---:|---:|
| Midwest leg | 9 | 16 | — |
| South leg | 6 | 14 | — |
| market (the armed gate) | 8 | 13 | — |
| **union of regional beyond market** | — | **8** | **3 scarce / 8 all-year** |

2023: regional shorts 6 (Midwest) / 4 (South), **incremental 0 hours all
year**. 2024: 7 / 6, **incremental 0 hours all year**.

The incremental hours are the only hours the extension can price the scored
benchmark (INDIANA.HUB, a Midwest zone) beyond what the armed market gate
already reaches: where both bind, the locational leg mostly RE-ALLOCATES the
existing shortage dual from all zones onto the Midwest (the hub keeps roughly
what it has; the South loses it). Against the lane's own pre-registered
inertness standard — PREREG-miso167 §3 K-PRE-A kills at H_on ≥ requirement in
≥ 80 % of the scarce hours — the Midwest leg alone measures 80.9 % (38/47, vs
the market gate's 78.7 % that proceeded by one hour), and the incremental
surface measures 93.6 %. **The kill fires. The arm is not solved.** For
scale: the armed market gate's 12 binding hours bought +0.10 pp on C3a-2025;
a 3-scarce-hour incremental surface extrapolates to ~+0.03 pp, against the
2.5 pp C3a-2025 needs. The charter's against-interest gate is passed
trivially — 0 incremental hours in 2023/2024 means the extension could not
have hurt them — but there is nothing material for it to protect.

## 5. What the published ASM record says about the rest (stage 4)

MISO's own RT ASM MCP by product in the 47 summer RT>$200 hours of 2025
(the miso-167 §3 set; market-wide "Miso-Wide" GEN MCPs):

| set | RT reg | RT spin | RT supp | supp share | DA total (same set) |
|---|---:|---:|---:|---:|---:|
| all 47 | 93.14 | 65.69 | 63.54 | **0.286** | 56.72 |
| DA-foreseen (20 h, DA>$150) | 131.56 | 97.94 | 97.94 | 0.299 | 81.13 |
| RT-only (27 h) | 64.68 | 41.81 | 38.06 | 0.263 | 38.64 |

(Hour-key note: on the loader's EST hour key the 47-hour RT total is
$222.37; the FINDING-miso167 §3 figure of $484.87 reproduces exactly at that
instrument's −1 h CST alignment. The PRODUCT SHARES — the object here — are
robust to the alignment: reg+spin 70.7–72.9 %, supp 27.1–29.3 % at every
shift tested.)

Three consequences:

* **~71 % of MISO's published scarce-hour reserve price sits on the
  synchronised products** — the phenomenon the armed gate targets. In the
  DA-foreseen hours MISO's DA ASM cleared reg+spin at $60.63; the armed
  gate's regspin dual in those hours is $25.81 (miso-169 K-5) — right order,
  conservative, consistent with the RHO_CLIP 0.5 floor blunting the gate in
  the conservative direction (the standing nyiso-144 owner escalation,
  untouched here).
* **~29 % sits on supplemental** — a product the model must NOT gate (§2)
  and correctly prices at ~$0 while 8 GW of offline quick-start capability
  is idle. MISO's own supp price separates from $0 through real-time
  deployment risk, failure-to-start exposure and the ORDC — RT phenomena on
  the far side of the miso-163 model-class line. Even in the DA-foreseen
  hours, MISO's DA market priced supp at only $20.50 against an RT
  realisation of $97.94: **79 % of even the "foreseeable" supplemental price
  is RT-only**, unreachable by any deterministic hourly LP with a correct
  supply model.
* The DA ASM record shows MISO's own deterministic forward market priced the
  whole reserve stack at $81 in the DA-foreseen hours — the model's
  DA-comparable ceiling — while its RT market realised $327. The gap between
  those two IS the model-class limit, measured in MISO's own two clearings
  of the same hours.

## 6. The end-to-end closure of C3a-2025's DA-foreseen half

Assembling the pieces, the C3a-2025 summer-scarcity miss is now documented
end to end, each piece with its own measured record:

1. **RT-only hours (27 of 47, 34.8 % of the summer gap)** — model-class
   limit, CLOSED by the miso-163 owner ruling (spikes at 98.7 GW that MISO's
   own DA market priced at $80). Untouched here; re-confirmed by §5's DA/RT
   ASM split.
2. **DA-foreseen synchronised share** — the reachable half's reachable part,
   **ALREADY ARMED** (`miso_reserve_online_gated`, keeper since miso-170):
   the gate prices exactly the hours a deterministic LP may claim (K-5
   textbook: +$10.12 DA-foreseen, $0.00 RT-only) and captured +0.10 pp of
   C3a-2025. Its remaining conservatism is the RHO_CLIP band — the standing
   nyiso-144 OWNER call, not a session's (and family-grain headroom says
   resolving it would not flip the scarce hours: FINDING-miso170 §4).
3. **DA-foreseen supplemental share (~29 % of the published reserve price)**
   — **structurally ungateable** (§2: offline quick-start is tariff-eligible
   to hold it; rule 1 forbids the gate), and mostly RT-priced even within
   the foreseen hours (§5: DA supp $20.50 vs RT supp $97.94). Closed as a
   product-definition consequence, not a model defect.
4. **The locational (sub-regional) synchronised split** — real in kind
   (§2's Exhibit 3-2 construct), adds zero gated volume, and its incremental
   binding surface is 3 scarce hours in 2025 and 0 in 2023/2024 (§4).
   **Measured inert on this keeper by the lane's own pre-registered
   standard; not solved.** If a future MISO fleet thins the Midwest's online
   headroom materially (retirements without replacement), the measurement
   regenerates and the verdict can flip — the instrument is committed.

**Consequence: MISO's C3a-2025 is a documented model-class limit END TO END.**
The DA-foreseen half now has the same adjudicated status as the RT-only half:
what a deterministic hourly LP may structurally claim of it is armed and
captured (+0.10 pp); what remains is either forbidden structure (gating
supplemental), inert structure (the locational split), or the DA→RT gap
MISO's own two market clearings measure at 4× ($81 → $327). The honest
ceiling of miso-167 §5 (~+3.3 pp reachable) is hereby REVISED DOWN for
supply-side reserve levers: the measured capture is +0.10 pp, the measured
residual increment is ~+0.03 pp, and the balance of the "reachable" half sits
in the supplemental product and the RT deepening of synchronised prices —
both on the far side of the structural line. No supply-side reserve lever
that a rule-1-faithful model may arm can close the remaining −12.1 %.

## 7. What this finding does NOT change, and what it hands forward

* Keeper, determinations, caveats, ledgers: unchanged. No cell verdict is
  minted from a solve; the matrix stamp records this adjudication on the
  miso-171 queue entry (evidence-cited, DO-NOT-REDO grounds for the
  sub-regional extension).
* `ordc_scarcity_overlay` (`G`) untouched — reserve DEMAND curve, not this
  lane. Reserve REQUIREMENT raises stay refuted (miso-167 §2c, rule 14). The
  +1.33 GW scarce-hour over-import stays a separate defect (rule 19).
* The RHO_CLIP band stays the nyiso-144 OWNER escalation; this finding adds
  no new claim on it.
* The charter's §4 carry-forward items are taken up next in this session:
  (a) the D-4 plant-grain attribution defect (cross-ISO, scorer-only),
  (b) the 1402 per-year `online_frac` successor (own prereg, own A/B — a
  REAL defect, now MISO's sole C8 blocker), (c) the Ames (1122) p25-level
  basis (own identification, never an exclusion), (d) the two C8 rubric
  design questions (owner decision — raised with measurements, not amended).

## 8. Reproduction

`python3 scripts/probes/_miso171_reserve_product_decomposition.py` — reads
`data/raw/MISO-AS/asm_rt_cleared_mw_<y>.parquet`,
`asm_rtmcp_zonal_2025.parquet`, `asm_damcp_zonal_2025.parquet`,
`data/raw/_validation-source/actual_lmp_hourly_MISO.parquet`, the keeper's
`miso170_layup_B2/hourly/{system,reserve_family}_<y>.parquet`, and
`miso169_gated_A/hourly/unit_hourly_<y>.parquet`; writes
`results/calibration/_miso171_reserve_product_decomposition.json`.
