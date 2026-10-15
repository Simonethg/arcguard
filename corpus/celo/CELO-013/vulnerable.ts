// Corpus CELO-013 (vulnerable). Legacy tx with feeCurrency (deprecated on Celo L2).
const USDC_FEE_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function pay(wallet: any, to: `0x${string}`) {
  return wallet.sendTransaction({ type: "legacy", to, gasPrice: 1n, feeCurrency: USDC_FEE_ADAPTER });
}
