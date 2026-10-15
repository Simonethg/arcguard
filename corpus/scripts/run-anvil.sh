#!/usr/bin/env bash
# Start arc-anvil --network arc if needed, then fork it with arc-forge.
# Local anvil uses chain id 31337. It is not Arc testnet.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"

RPC="${ARC_ANVIL_RPC_URL:-http://127.0.0.1:8545}"
port="${RPC##*:}"
port="${port%%/*}"

if ! command -v arc-anvil >/dev/null 2>&1 || ! command -v arc-forge >/dev/null 2>&1; then
  echo "arc-anvil and arc-forge must be on PATH." >&2
  echo "https://docs.arc.io/arc/tutorials/install-arc-foundry" >&2
  exit 1
fi

started=0
if ! arc-cast chain-id --rpc-url "$RPC" >/dev/null 2>&1; then
  arc-anvil --network arc --port "$port" >"${TMPDIR:-/tmp}/arcguard-anvil.log" 2>&1 &
  echo $! >"${TMPDIR:-/tmp}/arcguard-anvil.pid"
  started=1
  for _ in 1 2 3 4 5 6 7 8 9 10; do
    if arc-cast chain-id --rpc-url "$RPC" >/dev/null 2>&1; then
      break
    fi
    sleep 0.3
  done
fi

cleanup() {
  if [ "$started" -eq 1 ] && [ -f "${TMPDIR:-/tmp}/arcguard-anvil.pid" ]; then
    kill "$(cat "${TMPDIR:-/tmp}/arcguard-anvil.pid")" >/dev/null 2>&1 || true
    rm -f "${TMPDIR:-/tmp}/arcguard-anvil.pid"
  fi
}
trap cleanup EXIT

network=$(arc-cast rpc anvil_nodeInfo --rpc-url "$RPC" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("network"))')
if [ "$network" != "arc" ]; then
  echo "Refusing: node at $RPC reports network=$network, expected arc." >&2
  exit 1
fi

ARC_FORK=true arc-forge test --network arc --fork-url "$RPC" --match-path 'test/fork/*' -vv
