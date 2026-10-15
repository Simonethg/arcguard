// Corpus CELO-002 (fixed). feeCurrency uses the USDC adapter from FeeCurrencyDirectory.
const USDC_FEE_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function pay(wallet: any, to: `0x${string}`, data: `0x${string}`) {
  return wallet.sendTransaction({ to, data, feeCurrency: USDC_FEE_ADAPTER });
}
