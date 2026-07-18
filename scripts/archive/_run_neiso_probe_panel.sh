#!/usr/bin/env bash
# Re-run the NEISO single-knob offer-curve probe panel on current main.
# Each probe is the P12 keeper config + one +-0.05 band delta, year 2024,
# commitment on. Bundles land in the canonical results/calibration/<name> dirs
# the Jacobian REGISTRY (scripts/data/derive_offer_curve_jacobian.py) expects.
#
# Concurrency is capped (NEISO 8760h commitment LP is several GB each); pass the
# cap as $1 (default 2). Each job logs to /tmp/<name>.log.
set -u
cd "$(dirname "$0")/.."
source .venv/bin/activate

CAP="${1:-2}"
RUN="python scripts/run_calibration_full.py --iso NEISO --year 2024 --commitment"
OUT="results/calibration"

# name -> offer-curve-delta JSON
names=(
  neiso_probe_cc_regular_committed_plus
  neiso_probe_cc_regular_committed_minus
  neiso_probe_cc_regular_econ_high_plus
  neiso_probe_cc_regular_econ_high_minus
  neiso_probe_ct_peaker_committed_plus
  neiso_probe_ct_peaker_committed_minus
  neiso_probe_st_gas_committed_minus
  neiso_probe_st_gas_peak_minus
  neiso_probe_cc_chp_committed_minus
  neiso_probe_ct_chp_committed_minus
)
deltas=(
  '{"CC_REGULAR":{"committed":0.05}}'
  '{"CC_REGULAR":{"committed":-0.05}}'
  '{"CC_REGULAR":{"econ_high":0.05}}'
  '{"CC_REGULAR":{"econ_high":-0.05}}'
  '{"CT_PEAKER":{"committed":0.05}}'
  '{"CT_PEAKER":{"committed":-0.05}}'
  '{"ST_GAS":{"committed":-0.05}}'
  '{"ST_GAS":{"peak":-0.05}}'
  '{"CC_CHP":{"committed":-0.05}}'
  '{"CT_CHP":{"committed":-0.05}}'
)

for i in "${!names[@]}"; do
  # throttle: wait until running job count drops below CAP
  while [ "$(jobs -rp | wc -l)" -ge "$CAP" ]; do wait -n; done
  n="${names[$i]}"; d="${deltas[$i]}"
  echo "launching $n  delta=$d"
  $RUN --offer-curve-delta-json "$d" --out-dir "$OUT/$n" \
       --note "probe panel re-run on current main (branch neiso-backcast-jacobian)" \
       > "/tmp/$n.log" 2>&1 &
done
wait
echo "ALL NEISO PROBES DONE"
