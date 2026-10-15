// Corpus BASE-002 (fixed): verify the ID with policyExists() before binding it.
import { b20Abi, registryAbi } from "./abi";

export async function bindTransferPolicy(pub: any, wallet: any, registry: `0x${string}`, token: `0x${string}`, scope: `0x${string}`, policyId: bigint) {
  const exists = await pub.readContract({ address: registry, abi: registryAbi, functionName: "policyExists", args: [policyId] });
  if (!exists) throw new Error(`policy ${policyId} does not exist`);
  return wallet.writeContract({ address: token, abi: b20Abi, functionName: "updatePolicy", args: [scope, policyId] });
}
