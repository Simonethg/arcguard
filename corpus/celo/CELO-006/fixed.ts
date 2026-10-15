// Corpus CELO-006 (fixed). Detects MiniPay and verifies the fee currency actually used.
const USDC_FEE_ADAPTER = "0x2F25deB3848C207fc8E0c34035B3Ba7fC157602B";

export async function pay(to: string, data: string) {
  const provider = window.ethereum;
  const [from] = await provider.request({ method: "eth_requestAccounts" });
  const params: Record<string, string> = { from, to, data };
  if (provider.isMiniPay) params.feeCurrency = USDC_FEE_ADAPTER;
  const hash = await provider.request({ method: "eth_sendTransaction", params: [params] });
  const tx = await provider.request({ method: "eth_getTransactionByHash", params: [hash] });
  return { hash, paidIn: tx?.feeCurrency ?? "CELO" };
}
