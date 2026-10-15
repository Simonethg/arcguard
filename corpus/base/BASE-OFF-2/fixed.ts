// Corpus BASE-OFF-2 (fixed): suffix from ox/erc8021 (docs.base.org, Builder Codes for App Developers).
import { createWalletClient, http } from "viem";
import { base } from "viem/chains";
import { Attribution } from "ox/erc8021";

const DATA_SUFFIX = Attribution.toDataSuffix({ codes: ["YOUR-BUILDER-CODE"] });
const wallet = createWalletClient({ chain: base, transport: http(), dataSuffix: DATA_SUFFIX });
export const pay = (account: any, to: `0x${string}`, value: bigint) => wallet.sendTransaction({ account, to, value });
