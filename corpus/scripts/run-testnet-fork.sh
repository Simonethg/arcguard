#!/usr/bin/env bash
# Simulate the corpus against Arc testnet state. Read-only fork: no key, no broadcast.
# Refuses every chain id other than 5042002.
set -euo pipefail
cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

RPC="${ARC_TESTNET_RPC_URL:-https://rpc.testnet.arc.io}"
chain=$(arc-cast chain-id --rpc-url "$RPC")
if [ "$chain" != "5042002" ]; then
  echo "Refusing: RPC chain id is $chain, not Arc testnet 5042002." >&2
  exit 1
fi

ARC_FORK=true arc-forge test --network arc --fork-url "$RPC" --match-path 'test/fork/*' -vv
