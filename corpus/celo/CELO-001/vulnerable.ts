// Corpus CELO-001 (vulnerable). USDC on Celo has 6 decimals; 18 sends 10^12 times the amount.
import { parseUnits } from "viem";
const USDC = "0xcebA9300f2b948710d2653dD7B07f33A8B32118C";

export function usdcAmount(human: string) {
  return { token: USDC, amount: parseUnits(human, 18) };
}
