#!/usr/bin/env bash
# Verify the LCE portfolio tool is truly standalone: copy scope2-lce-portfolio/
# to a directory OUTSIDE the parent market-simulator repo, build a fresh venv
# from requirements.txt only, and drive it end-to-end with zero parent-repo
# access -- pytest, the synthetic sample sweep, a real-ISO CLI run against the
# committed bundled data (CF profiles, BAU LMP, fossil-avg CO2 rate,
# generated-on-demand reference load), and a launcher smoke test.
#
# Usage (from anywhere):
#   scope2-lce-portfolio/scripts/verify_standalone.sh
#
# Fails loudly (set -e, explicit assertions) on the first broken step. Never
# writes into the parent repo -- everything happens inside a fresh copy under
# a temp directory outside this checkout.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
VERIFY_ISO="${VERIFY_ISO:-ERCOT}"

WORK_DIR="$(mktemp -d /tmp/lce-standalone-verify.XXXXXX)"
COPY_DIR="$WORK_DIR/scope2-lce-portfolio"

cleanup() {
  local rc=$?
  if [ -n "${SERVER_PID:-}" ] && kill -0 "$SERVER_PID" 2>/dev/null; then
    kill "$SERVER_PID" 2>/dev/null || true
    wait "$SERVER_PID" 2>/dev/null || true
  fi
  rm -rf "$WORK_DIR"
  if [ "$rc" -ne 0 ]; then
    echo "FAIL: verify_standalone.sh exited $rc" >&2
  fi
}
trap cleanup EXIT

echo "== copying $TOOL_ROOT -> $COPY_DIR (outside the parent repo) =="
mkdir -p "$COPY_DIR"
# Real profile/lmp/emissions data lives in the working tree regardless of
# .gitignore state, so a plain recursive copy (not "git archive") carries it.
cp -R "$TOOL_ROOT"/. "$COPY_DIR"/
rm -rf "$COPY_DIR/.venv-verify" "$COPY_DIR/data/outputs" "$COPY_DIR/launcher/saved_configs.json" "$COPY_DIR/launcher/last_used.json"

cd "$COPY_DIR"

echo "== grep guard: no real 'import market_sim' statement anywhere in the copy =="
# Anchored to actual import statements (start of line, optional indent) so
# docstring/comment mentions of "import market_sim" (e.g. explaining what the
# tool avoids) don't trip a false positive.
if grep -rIn --include='*.py' -E '^[[:space:]]*(import market_sim|from market_sim)' . ; then
  echo "FAIL: found a market_sim import in the standalone copy" >&2
  exit 1
fi
echo "OK: no market_sim import"

echo "== building a fresh venv (PARENT_ROOT unreachable from here) =="
python3 -m venv .venv-verify
# shellcheck disable=SC1091
source .venv-verify/bin/activate
python -m pip install --quiet --upgrade pip
# pytest + pyyaml are test-time only (pyproject.toml [project.optional-
# dependencies].dev) -- pyyaml itself is a runtime-optional dependency
# (PortfolioConfig.from_file's YAML path) but the test suite exercises it
# directly, so it needs to be present for `pytest -q` to be meaningful.
python -m pip install --quiet -r requirements.txt pytest pyyaml

echo "== pytest -q =="
python -m pytest -q

echo "== examples/run_sample_sweep.py =="
python examples/run_sample_sweep.py

echo "== real-ISO CLI run on bundled data only ($VERIFY_ISO) =="
LMP_FILE="data/bundled/lmp/${VERIFY_ISO}_2024_bau_lmp.csv"
EMISSIONS_FILE="data/emissions/${VERIFY_ISO}_2024_fossil_avg_co2_rate.parquet"
if [ ! -f "$LMP_FILE" ]; then
  echo "FAIL: no bundled LMP for $VERIFY_ISO at $LMP_FILE" >&2
  exit 1
fi
python scripts/make_reference_load.py
EMISSIONS_ARGS=()
if [ -f "$EMISSIONS_FILE" ]; then
  EMISSIONS_ARGS=(--emissions "$EMISSIONS_FILE")
else
  echo "note: no fossil-avg CO2 rate file for $VERIFY_ISO -- running without it (optional input)"
fi
# profile_shape_year pins the CF-profile vintage to the committed 2024
# bundle and (per PortfolioConfig docstring) turns a missing file into a
# hard error instead of a silent synthetic-shape fallback -- the CLI has no
# flag for this field, only --config, so a tiny config file sets it.
PROFILE_CONFIG="$WORK_DIR/verify_profile_config.json"
printf '{"profile_shape_year": 2024}\n' > "$PROFILE_CONFIG"
RUN_ID="verify_standalone_${VERIFY_ISO,,}"
python run_portfolio.py \
  --config "$PROFILE_CONFIG" \
  --load data/reference/reference_load_100mw.csv \
  --lmp "$LMP_FILE" \
  "${EMISSIONS_ARGS[@]}" \
  --iso "$VERIFY_ISO" \
  --deltas 10 20 \
  --results --run-id "$RUN_ID"

METADATA_FILE="results/${RUN_ID}/${VERIFY_ISO}_run_metadata.json"
if grep -q '"source": *"synthetic"' "$METADATA_FILE" 2>/dev/null; then
  echo "FAIL: $METADATA_FILE shows a synthetic CF-profile fallback -- the real bundled profile was not used" >&2
  exit 1
fi
echo "OK: $METADATA_FILE confirms a real (non-synthetic) CF profile was used"

REPORT_HTML="results/${RUN_ID}/report.html"
if [ ! -s "$REPORT_HTML" ]; then
  echo "FAIL: $REPORT_HTML missing or empty after the real-ISO CLI run" >&2
  exit 1
fi
echo "OK: $REPORT_HTML written ($(wc -c < "$REPORT_HTML") bytes)"

echo "== launcher smoke test (--no-open --port 0) =="
LAUNCHER_LOG="$WORK_DIR/launcher.log"
PYTHONPATH="$COPY_DIR/src" PYTHONUNBUFFERED=1 python -m lce_portfolio.launcher \
  --no-open --port 0 \
  --results "$WORK_DIR/launcher_results" \
  --state-dir "$WORK_DIR/launcher_state" \
  --inputs-dir "$WORK_DIR" \
  > "$LAUNCHER_LOG" 2>&1 &
SERVER_PID=$!

PORT=""
for _ in $(seq 1 150); do
  if ! kill -0 "$SERVER_PID" 2>/dev/null; then
    echo "FAIL: launcher process exited before serving; log:" >&2
    cat "$LAUNCHER_LOG" >&2
    exit 1
  fi
  PORT="$(sed -nE 's#.*http://127\.0\.0\.1:([0-9]+)/.*#\1#p' "$LAUNCHER_LOG" 2>/dev/null | head -1 || true)"
  if [ -n "$PORT" ]; then
    break
  fi
  sleep 0.1
done
if [ -z "$PORT" ]; then
  echo "FAIL: launcher never reported a serving URL; log:" >&2
  cat "$LAUNCHER_LOG" >&2
  exit 1
fi

STATUS="$(curl -s -o /dev/null -w '%{http_code}' "http://127.0.0.1:${PORT}/")"
if [ "$STATUS" != "200" ]; then
  echo "FAIL: launcher / returned HTTP $STATUS" >&2
  exit 1
fi
echo "OK: launcher served / with HTTP 200 on port $PORT"

kill "$SERVER_PID"
wait "$SERVER_PID" 2>/dev/null || true
SERVER_PID=""

echo "== ALL CHECKS PASSED =="
