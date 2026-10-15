// Corpus BASE-OFF-1 (fixed): canonical heads and latest state (docs.base.org, Migrate From Flashblocks).
export async function watch(ws: any, client: any, addr: `0x${string}`) {
  await ws.send({ method: "eth_subscribe", params: ["newHeads"] });
  return client.getBalance({ address: addr, blockTag: "latest" });
}
