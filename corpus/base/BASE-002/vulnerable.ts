// Corpus BASE-002 (vulnerable). Binds a policy ID received from config without checking it exists.
// docs.base.org: a never-created INTERSECT ID returns true for everyone (behaves like ALWAYS_ALLOW).
import { b20Abi } from "./abi";

export async function bindTransferPolicy(wallet: any, token: `0x${string}`, scope: `0x${string}`, policyId: bigint) {
  return wallet.writeContract({ address: token, abi: b20Abi, functionName: "updatePolicy", args: [scope, policyId] });
}
