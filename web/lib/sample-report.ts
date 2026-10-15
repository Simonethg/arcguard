/**
 * Bundled example report used when `arcaudit scan` is not implemented.
 * Findings for NaiveEthereumPort are reference cases. The other rows are
 * illustrative snippets, not a live scan of scaffold-arc.
 *
 * Sources:
 * - https://docs.arc.io/arc/references/evm-differences
 * - https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
 * - https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
 */

import { isRuleId, ruleById } from "../content/rules";
import sample from "../fixtures/sample-report.json" with { type: "json" };
import type { Finding, ScanReport } from "./types";

function isFinding(value: unknown): value is Finding {
  if (!value || typeof value !== "object") return false;
  const row = value as Record<string, unknown>;
  return (
    typeof row.ruleId === "string" &&
    isRuleId(row.ruleId) &&
    typeof row.path === "string" &&
    typeof row.symbol === "string" &&
    typeof row.line === "number" &&
    (row.origin === "reference" || row.origin === "illustrative") &&
    typeof row.docsUrl === "string" &&
    row.docsUrl.startsWith("https://docs.arc.io/")
  );
}

export function loadExampleReport(): ScanReport {
  const raw = sample as unknown;
  if (!raw || typeof raw !== "object") {
    throw new Error("sample report is not an object");
  }
  const record = raw as Record<string, unknown>;
  const network = record.network as Record<string, unknown> | undefined;
  const target = record.target as Record<string, unknown> | undefined;
  if (record.tool !== "arcaudit" || record.mode !== "example") {
    throw new Error("sample report mode is not example");
  }
  if (!network || network.chainId !== 5042002 || network.name !== "Arc Testnet") {
    throw new Error("sample report is not Arc testnet");
  }
  if (network.rpcUrl !== "https://rpc.testnet.arc.io") {
    throw new Error("sample report rpc is not Arc testnet");
  }
  if (!target || typeof target.label !== "string" || target.kind !== "example") {
    throw new Error("sample report target is missing");
  }
  if (!Array.isArray(record.findings) || !record.findings.every(isFinding)) {
    throw new Error("sample report findings are invalid");
  }
  return structuredClone(sample) as ScanReport;
}

export function exampleForTarget(
  kind: ScanReport["target"]["kind"],
  label: string,
): ScanReport {
  const report = loadExampleReport();
  report.target = { kind, label };
  report.mode = "example";
  return report;
}

export const EXAMPLE_REPORT: ScanReport = loadExampleReport();

/** Canonical docs URL from the rule page, never a URL supplied by the CLI. */
export function canonicalDocsUrl(ruleId: string): string | undefined {
  return ruleById(ruleId)?.docs[0]?.url;
}
