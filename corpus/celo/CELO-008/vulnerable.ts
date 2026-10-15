// Corpus CELO-008 (vulnerable). Indexes CELO deposits only via ERC-20 Transfer logs.
import { erc20Abi } from "viem";
const CELO = "0x471EcE3750Da237f93B8E339c536989b8978a438";

export function watchDeposits(client: any, vault: `0x${string}`, onDeposit: (v: bigint) => void) {
  return client.watchContractEvent({
    address: CELO, abi: erc20Abi, eventName: "Transfer", args: { to: vault },
    onLogs: (logs: any[]) => logs.forEach((l) => onDeposit(l.args.value)),
  });
}
