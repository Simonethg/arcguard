/**
 * Report shape shared by the example fixture, the scan API, and the UI.
 *
 * Network is Arc testnet only:
 * https://docs.arc.io/arc/references/evm-differences
 */

import type { RuleId } from "../content/rules";

export type FindingOrigin = "reference" | "illustrative";

export type Finding = {
  ruleId: RuleId;
  path: string;
  symbol: string;
  line: number;
  origin: FindingOrigin;
  docsUrl: string;
};

export type ScanReport = {
  tool: "arcaudit";
  version: string;
  mode: "example" | "cli";
  network: {
    name: "Arc Testnet";
    chainId: 5042002;
    rpcUrl: "https://rpc.testnet.arc.io";
  };
  target: {
    kind: "example" | "github" | "file";
    label: string;
  };
  findings: Finding[];
};

export type CliNote = "missing" | "not-implemented" | "not-json" | "timeout" | "ok";

export type ScanApiSuccess = {
  mode: "example" | "cli";
  cli: {
    attempted: boolean;
    available: boolean;
    exitCode: number | null;
    parsedJson: boolean;
    note: CliNote;
  };
  report: ScanReport;
};

export type ScanErrorCode =
  | "invalid-json"
  | "empty"
  | "both"
  | "invalid-github-url"
  | "too-large"
  | "not-solidity";

export type ScanApiError = {
  error: ScanErrorCode;
};
