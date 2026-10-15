#!/usr/bin/env bash
# Compile and run in-process Arc tests. Does not start a node and does not
# broadcast. Fork tests stay skipped unless ARC_FORK=true.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"

if ! command -v arc-forge >/dev/null 2>&1; then
  echo "arc-forge is not on PATH. Install Arc Foundry:" >&2
  echo "  https://docs.arc.io/arc/tutorials/install-arc-foundry" >&2
  exit 1
fi

arc-forge build
arc-forge test --network arc -vv
