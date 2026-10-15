// Corpus CELO-002 (vulnerable). feeCurrency set to the USDC token instead of its adapter.
const USDC_TOKEN = "0xcebA9300f2b948710d2653dD7B07f33A8B32118C";

export async function pay(wallet: any, to: `0x${string}`, data: `0x${string}`) {
  return wallet.sendTransaction({ to, data, feeCurrency: USDC_TOKEN });
}
