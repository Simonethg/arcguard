#!/usr/bin/env bash
# Submit failing native transfers on Arc testnet and print the receipt hashes.
# The deployer key is read from ARC_TESTNET_PRIVATE_KEY only. This script
# never prints that variable. It refuses any chain id other than 5042002.
set -euo pipefail
case $- in
  *x*)
    echo "Refusing to run with xtrace." >&2
    exit 1
    ;;
esac

cd "$(dirname "$0")/.."
export PATH="${HOME}/.local/bin:${PATH}"

if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  . ./.env
  set +a
fi

RPC="${ARC_TESTNET_RPC_URL:-https://rpc.testnet.arc.io}"

if [ -z "${ARC_TESTNET_PRIVATE_KEY:-}" ]; then
  echo "ARC_TESTNET_PRIVATE_KEY is unset. No testnet transaction was sent."
  echo "Record hashes in corpus/EVIDENCE.md after a funded testnet run."
  echo "Explorer: https://testnet.arcscan.app"
  exit 0
fi

chain=$(arc-cast chain-id --rpc-url "$RPC")
if [ "$chain" != "5042002" ]; then
  echo "Refusing: RPC chain id is $chain, not Arc testnet 5042002." >&2
  exit 1
fi

mkdir -p evidence

send_failing() {
  local to="$1"
  local label="$2"
  local out
  # status 0 is the expected result. cast still exits 0 and prints the receipt.
  out=$(arc-cast send \
    --json \
    --rpc-url "$RPC" \
    --private-key "$ARC_TESTNET_PRIVATE_KEY" \
    --gas-price 20gwei \
    --gas-limit 100000 \
    --timeout 60 \
    --value 1wei \
    "$to") || { printf "%s\tno receipt (rejected by RPC or dropped)\n" "$label"; return 0; }
  python3 -c '
import json, sys
label, raw = sys.argv[1], sys.argv[2]
receipt = json.loads(raw)
status = receipt.get("status")
tx = receipt.get("transactionHash", "")
reason = receipt.get("revertReason") or ""
reason = reason.split(", data:", 1)[0]
failed = status in ("0x0", "0", 0, False)
print(f"{label}\tstatus={status}\tfailed={str(failed).lower()}\ttx={tx}\treason={reason}")
print(f"explorer\thttps://testnet.arcscan.app/tx/{tx}")
if not failed:
    sys.exit(2)
' "$label" "$out"
}

{
  echo "# local evidence dump — do not commit (this directory is gitignored)"
  send_failing 0x0000000000000000000000000000000000000000 "ARC-005 value to zero address"
  send_failing 0x70997970C51812dc3A010C7d01b50e0d17dc79C8 "ARC-006 blocklisted recipient"
} | tee evidence/last-run.txt
