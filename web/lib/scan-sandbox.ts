/**
 * Run `arcaudit scan` in a temp directory and drop the directory afterwards.
 *
 * The child process does not inherit the parent environment, so credentials
 * from the host are not forwarded. User Solidity is written to a mode 0600
 * file and deleted in `finally`. It is not returned in the API response.
 *
 * The child is `arcaudit scan <target> --format json`. When that JSON
 * contains findings, those rows are the report. The bundled example is
 * used only when the CLI is missing, times out, or returns no findings.
 * The example is not a scan of the pasted input.
 *
 * Sources for the rules this report describes:
 * - https://docs.arc.io/arc/references/evm-differences
 * - https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
 * - https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
 */

import { spawn } from "node:child_process";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { isRuleId, ruleById } from "../content/rules";
import { exampleForTarget } from "./sample-report";
import { sanitizeSolName } from "./solidity-input";
import type { CliNote, Finding, ScanApiSuccess, ScanReport } from "./types";

const OUTPUT_CAP = 200_000;
const TIMEOUT_MS = 8_000;

type CliResult = {
  available: boolean;
  exitCode: number | null;
  stdout: string;
  stderr: string;
  timedOut: boolean;
};

function cliBin(): string {
  const raw = process.env.ARCGUARD_ARCAUDIT;
  if (raw && /^[A-Za-z0-9_./:-]+$/.test(raw) && !raw.startsWith("-")) return raw;
  return "arcaudit";
}

function childEnv(): NodeJS.ProcessEnv {
  // Only these fields are forwarded. Host credentials stay in the parent.
  const env: NodeJS.ProcessEnv = {
    PATH: process.env.PATH ?? "/usr/bin:/bin",
    LANG: "C.UTF-8",
    HOME: process.env.HOME ?? tmpdir(),
    NODE_ENV: process.env.NODE_ENV,
  };
  return env;
}

function invokeArcaudit(target: string): Promise<CliResult> {
  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let settled = false;
    let timedOut = false;
    const child = spawn(cliBin(), ["scan", target, "--format", "json"], {
      cwd: path.dirname(target),
      env: childEnv(),
      stdio: ["ignore", "pipe", "pipe"],
    });

    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, TIMEOUT_MS);

    const finish = (result: CliResult) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve(result);
    };

    child.stdout?.on("data", (buf: Buffer) => {
      if (stdout.length < OUTPUT_CAP) stdout += buf.toString("utf8");
    });
    child.stderr?.on("data", (buf: Buffer) => {
      if (stderr.length < OUTPUT_CAP) stderr += buf.toString("utf8");
    });
    child.on("error", (err: NodeJS.ErrnoException) => {
      finish({
        available: err.code !== "ENOENT",
        exitCode: null,
        stdout,
        stderr,
        timedOut,
      });
    });
    child.on("close", (code) => {
      finish({ available: true, exitCode: code, stdout, stderr, timedOut });
    });
  });
}

function noteFor(result: CliResult, parsed: boolean): CliNote {
  if (!result.available) return "missing";
  if (result.timedOut) return "timeout";
  if (parsed) return "ok";
  if (/not implemented/i.test(result.stderr)) return "not-implemented";
  return "not-json";
}

function cleanPath(value: string): string {
  const base = value.split(/[/\\]/).pop() ?? "input";
  if (!/^[A-Za-z0-9._-]{1,80}$/.test(base)) return "input";
  return base;
}

const ARC_TESTNET = {
  name: "Arc Testnet" as const,
  chainId: 5042002 as const,
  rpcUrl: "https://rpc.testnet.arc.io" as const,
};

function lineOf(value: unknown): number {
  if (typeof value === "number" && Number.isFinite(value)) return Math.max(1, Math.floor(value));
  return 1;
}

function versionOf(value: unknown): string {
  if (typeof value === "string" && /^[0-9]+\.[0-9]+\.[0-9]+$/.test(value)) return value;
  return "0.1.0";
}

/**
 * Map one `arcaudit scan --format json` finding (`rule_id`, `file`, `line`).
 * Unknown rule ids are skipped. The docs link is the rule page, not the CLI string.
 */
function findingFromCliJson(row: Record<string, unknown>): Finding | null {
  const ruleId = typeof row.rule_id === "string" ? row.rule_id : "";
  if (!isRuleId(ruleId)) return null;
  const rule = ruleById(ruleId);
  if (!rule) return null;
  const file = typeof row.file === "string" ? cleanPath(row.file) : "input";
  const line = lineOf(row.line);
  return {
    ruleId: rule.id,
    path: file,
    symbol: `${file}:${line}`.slice(0, 120),
    line,
    origin: "illustrative",
    docsUrl: rule.docs[0].url,
  };
}

function reportFromRealCli(
  record: Record<string, unknown>,
  target: ScanReport["target"],
): ScanReport | null {
  if (!Array.isArray(record.findings)) return null;
  const findings: Finding[] = [];
  for (const item of record.findings) {
    if (!item || typeof item !== "object") continue;
    const mapped = findingFromCliJson(item as Record<string, unknown>);
    if (mapped) findings.push(mapped);
  }
  return {
    tool: "arcaudit",
    version: versionOf(record.version),
    mode: "cli",
    network: ARC_TESTNET,
    target,
    findings,
  };
}

/**
 * Accept either the real CLI JSON (`tool: "arcguard"`, `rule_id`) or the
 * older report shape (`tool: "arcaudit"`, Arc testnet `chainId`, `ruleId`).
 * Documentation links are replaced with the canonical rule URLs.
 */
export function sanitizeCliReport(
  value: unknown,
  target: ScanReport["target"],
): ScanReport | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  if (record.tool === "arcguard") return reportFromRealCli(record, target);
  if (record.tool !== "arcaudit") return null;
  const network = record.network as Record<string, unknown> | undefined;
  if (!network || network.chainId !== ARC_TESTNET.chainId) return null;
  if (!Array.isArray(record.findings)) return null;

  const findings: Finding[] = [];
  for (const item of record.findings) {
    if (!item || typeof item !== "object") return null;
    const row = item as Record<string, unknown>;
    if (typeof row.ruleId !== "string" || !isRuleId(row.ruleId)) return null;
    const rule = ruleById(row.ruleId);
    if (!rule) return null;
    findings.push({
      ruleId: rule.id,
      path: typeof row.path === "string" ? cleanPath(row.path) : "input",
      symbol: typeof row.symbol === "string" ? row.symbol.slice(0, 120) : "",
      line: lineOf(row.line),
      origin: row.origin === "reference" ? "reference" : "illustrative",
      docsUrl: rule.docs[0].url,
    });
  }

  return {
    tool: "arcaudit",
    version: versionOf(record.version),
    mode: "cli",
    network: ARC_TESTNET,
    target,
    findings,
  };
}

function parseJson(stdout: string): unknown | null {
  const trimmed = stdout.trim();
  if (!trimmed.startsWith("{")) return null;
  try {
    return JSON.parse(trimmed) as unknown;
  } catch {
    return null;
  }
}

export async function runSandboxedScan(input: {
  kind: "github" | "file";
  label: string;
  source?: string;
  filename?: string;
}): Promise<ScanApiSuccess> {
  const target = { kind: input.kind, label: input.label };
  const dir = await mkdtemp(path.join(tmpdir(), "arcguard-scan-"));
  try {
    let scanTarget = dir;
    if (input.kind === "file" && input.source) {
      const filePath = path.join(dir, sanitizeSolName(input.filename));
      await writeFile(filePath, input.source, { encoding: "utf8", mode: 0o600 });
      scanTarget = filePath;
    }
    const cli = await invokeArcaudit(scanTarget);
    const parsed = sanitizeCliReport(parseJson(cli.stdout), target);
    // A real JSON report replaces the fixture only when it has findings.
    // An empty scan, or a CLI that did not speak JSON, keeps the example.
    if (parsed && parsed.findings.length > 0 && cli.available && !cli.timedOut) {
      return {
        mode: "cli",
        cli: {
          attempted: true,
          available: true,
          exitCode: cli.exitCode,
          parsedJson: true,
          note: "ok",
        },
        report: parsed,
      };
    }
    return {
      mode: "example",
      cli: {
        attempted: true,
        available: cli.available,
        exitCode: cli.exitCode,
        parsedJson: false,
        note: noteFor(cli, false),
      },
      report: exampleForTarget(input.kind, input.label),
    };
  } finally {
    await rm(dir, { recursive: true, force: true });
  }
}
