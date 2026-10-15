/** Bounds for a pasted or uploaded Solidity file. Not executed. */

export const MAX_SOURCE_CHARS = 100_000;

export type SolidityIssue = "empty" | "too-large" | "not-solidity";

export function validateSolidity(source: string): SolidityIssue | "ok" {
  if (source.length > MAX_SOURCE_CHARS) return "too-large";
  if (source.includes("\0")) return "not-solidity";
  const trimmed = source.trim();
  if (!trimmed) return "empty";
  if (!/pragma\s+solidity|\bcontract\s+|\blibrary\s+|\binterface\s+/.test(trimmed)) {
    return "not-solidity";
  }
  return "ok";
}

export function sanitizeSolName(name: string | undefined): string {
  const base = (name ?? "input.sol").split(/[/\\]/).pop() ?? "input.sol";
  if (!/^[A-Za-z0-9._-]{1,80}\.sol$/.test(base)) return "input.sol";
  return base;
}
