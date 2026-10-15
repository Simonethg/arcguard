// Corpus BASE-OFF-1 (vulnerable). Relies on Flashblocks preconfirmations and the "pending" tag.
export async function watch(ws: any, client: any, addr: `0x${string}`) {
  await ws.send({ method: "eth_subscribe", params: ["newFlashblocks"] });
  return client.getBalance({ address: addr, blockTag: "pending" });
}
