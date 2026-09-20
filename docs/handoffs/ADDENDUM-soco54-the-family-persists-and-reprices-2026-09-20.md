# ADDENDUM 3 to PRECOMMIT-soco-54 — CORRECTION to ADDENDUM 2 §1: the constant-multiplier family persists in ALL THREE YEARS. What moves is the CONTRACT MULTIPLIER, on machines whose physics does not change.

**Written BEFORE any arm leg landed** (pinned PRECOMMIT SHA
`d85e0c47567b0ae8258a99920d512fd3fe8fe1df`; `git ls-remote origin 'refs/heads/claude/soco54-*'`
returned **0** branches at the moment of this commit).

## 1. THE CORRECTION

`ADDENDUM-soco54-the-effect-is-concentrated-in-2023` §1 stated:

> *"PRECOMMIT §4's seven-plant constant-multiplier family is a **2023** measurement and this
> addendum does not claim it holds in the later years."*

**That is wrong, and the error was mine: I auto-selected the reference plant per year as the
cheapest reporter, and in 2024 that picked plant 47, which is not a family member.** Re-measured
against a **FIXED** reference (54538 Hartwell) in all three years, the family is present and
tight in every one:

| plant | 2023 ratio (CV) | 2024 ratio (CV) | 2025 ratio (CV) |
|---|---|---|---|
| 54538 Hartwell | 1.0000 (0.00000) | 1.0000 (0.00000) | 1.0000 (0.00000) |
| 55141 Hawk Road | 1.0730 (0.00008) | 1.1147 (0.00005) | 0.7188 (0.00005) |
| 55244 Doyle | 1.1349 (0.00045) | 1.1382 (0.00054) | 0.7142 (0.00012) |
| 7813 Sewell Creek | 1.4382 (0.00030) | 1.1498 (0.00024) | 0.7748 (0.00005) |
| 7829 Smarr | 1.4441 (0.00081) | 1.2287 (0.00033) | 0.7657 (0.00006) |
| 7916 Talbot County | 1.4905 (0.00016) | 1.4771 (0.00008) | 0.9024 (0.00003) |
| **728 Yates** | **1.8279** (0.00009) | **1.1669** (0.00013) | **0.7959** (0.00009) |
| 55128 Walton County | absent | 0.9853 (0.00018) | 0.6023 (0.00005) |

**Every cell is a constant multiple to CV ≤ 0.00081 over 10–12 months.** Eight plants, three
years, one shape.

## 2. WHY THE CORRECTION STRENGTHENS THE LANE'S CLAIM RATHER THAN WEAKENING IT

The family does not dissolve. **The multipliers REPRICE.**

- **Yates (728) goes 1.8279 → 1.1669 → 0.7959 against Hartwell.** The same boiler, at the same
  site, on the same pipeline, moves from paying **83 % more** than a Georgia peaker to paying
  **20 % less**, in two years.
- **Sewell Creek goes 1.4382 → 1.1498 → 0.7748**; **Smarr 1.4441 → 1.2287 → 0.7657**.
- Hartwell, the reference, goes from the cheapest member of the family in 2023 to the DEAREST in
  2025.

**No physical property of these machines changed by 2.3× in two years.** Their heat rates are the
same measured values `measured_ct_heat_rates` / `measured_st_heat_rates` derive from their own
CAMPD record; their location, their pipeline and their fuel are unchanged. **What changed is the
contract.**

**This is the lane's whole structural claim, measured rather than argued.** A merit order built on
these prints is ordered by *negotiated contract terms that reprice on a commercial calendar*, not
by the cost of producing the next MWh. The C1 defect it produces is not stable either — it is
large in 2023, when Yates's multiplier was 1.83, and small in 2024, when it was 1.17. **The
residual tracks the contract, which is exactly what a mis-based cost input looks like and exactly
what a physical cost input does not.**

## 3. WHAT ADDENDUM 2 GOT RIGHT AND KEEPS

Addendum 2's substantive content stands and is not withdrawn:

- **The arm's Δmc table for all three years** (its §1) was measured against the model's own
  rebuilt `mc_base` and is unaffected by the reference-selection error. 2023 remains the clean
  case; 2024 is weaker; 2025 is mixed, with Hartwell going **cheaper** by $12.66.
- **§2's naming of the uncomfortable coincidence stands in full**, and this correction does not
  soften it: the arm still bites hardest in SOCO's only failing C1 year, the three answers to it
  (nothing selected, nothing swept, reported ex ante) are unchanged, and §3's statement that rule
  1 `[R-STRUCT]` decides on the basis argument rather than on 2023's residual is unchanged.

What §2 of THIS addendum adds is that the basis argument is no longer only an argument: the
year-over-year repricing of a plant-constant multiplier, on eight plants at CV ≤ 0.0008, is a
**measurement** that the print is a contract term.

## 4. ROUTED

**This is a CROSS-ISO observation and is reported, never taken** (rules 25 `[R-ISO-SCOPE]` /
28(d)). Five other keepers arm `gas_plant_monthly_fuel_pricing`. Whether their footprints carry
constant-multiplier formula families of their own is a question for **their** lanes, on **their**
receipts; this lane measured SOCO's and fills no other ISO's cell. The one-line test is in
`scripts/probes/_soco54_phase0.py`'s idiom: pivot `load_monthly_fuel_costs()` to
`plant_id × month`, divide by a fixed reference row, and report the ratio CV.
