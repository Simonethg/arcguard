// Corpus CELO-003 (vulnerable). Transfers USDC through the adapter address (only valid as feeCurrency).
import { erc20Abi } from "viem";
const USDC_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function send(wallet: any, to: `0x${string}`, amount: bigint) {
  return wallet.writeContract({ address: USDC_ADAPTER, abi: erc20Abi, functionName: "transfer", args: [to, amount] });
}
