// Corpus BASE-004 (fixed): the predicate only gates inclusion on a known, verified slot;
// the critical check lives in the called contract (docs.base.org, Predicates and Safety).
export const predicates = [
  {
    type: "storage",
    params: { address: "0x2222222222222222222222222222222222222222", slot: "0x7", mask: "0xff", op: "=", value: "0x2a" },
  },
];
