// Corpus CELO-001 (fixed). USDC/USDT/USA₮ use 6 decimals on Celo (USDm uses 18).
import { parseUnits } from "viem";
const USDC = "0xcebA9300f2b948710d2653dD7B07f33A8B32118C";
const USDC_DECIMALS = 6;

export function usdcAmount(human: string) {
  return { token: USDC, amount: parseUnits(human, USDC_DECIMALS) };
}
