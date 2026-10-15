// Corpus BASE-OFF-2 (vulnerable). Writes on Base without the ERC-8021 Builder Code suffix.
import { createWalletClient, http } from "viem";
import { base } from "viem/chains";

const wallet = createWalletClient({ chain: base, transport: http() });
export const pay = (account: any, to: `0x${string}`, value: bigint) => wallet.sendTransaction({ account, to, value });
