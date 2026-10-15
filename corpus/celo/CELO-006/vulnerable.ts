// Corpus CELO-006 (vulnerable). Assumes the injected wallet honors feeCurrency.
const USDC_FEE_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function pay(to: string, data: string) {
  const [from] = await window.ethereum.request({ method: "eth_requestAccounts" });
  // UI says "you pay the network fee in USDC"
  return window.ethereum.request({ method: "eth_sendTransaction", params: [{ from, to, data, feeCurrency: USDC_FEE_ADAPTER }] });
}
