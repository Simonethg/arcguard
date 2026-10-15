// Corpus CELO-013 (fixed). CIP-64 (type 123) for fee abstraction.
const USDC_FEE_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function pay(wallet: any, to: `0x${string}`) {
  return wallet.sendTransaction({ type: "cip64", to, feeCurrency: USDC_FEE_ADAPTER });
}
