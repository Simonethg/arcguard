// Corpus CELO-003 (fixed). Transfers use the token address.
import { erc20Abi } from "viem";
const USDC_TOKEN = "0xcebA9300f2b948710d2653dD7B07f33A8B32118C";

export async function send(wallet: any, to: `0x${string}`, amount: bigint) {
  return wallet.writeContract({ address: USDC_TOKEN, abi: erc20Abi, functionName: "transfer", args: [to, amount] });
}
