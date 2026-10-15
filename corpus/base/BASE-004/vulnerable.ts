// Corpus BASE-004 (vulnerable). Waits for an "empty" slot as if that proved the target is safe to call.
export const predicates = [
  {
    type: "storage",
    params: { address: "0x2222222222222222222222222222222222222222", slot: "0x0", op: "=", value: "0x0" },
  },
];
