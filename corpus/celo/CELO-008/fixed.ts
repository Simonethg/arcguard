// Corpus CELO-008 (fixed). Reconciles against the single CELO balance (native == ERC-20 view).
const CELO = "0x471EcE3750Da237f93B8E339c536989b8978a438";

export async function vaultCelo(client: any, vault: `0x${string}`) {
  // One balance: native getBalance equals GoldToken.balanceOf. Never add them.
  return { token: CELO, amount: await client.getBalance({ address: vault }) };
}
