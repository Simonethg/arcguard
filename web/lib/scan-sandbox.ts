/**
 * Run `arcaudit scan` in a temp directory and drop the directory afterwards.
 *
 * The child process does not inherit the parent environment, so credentials
 * from the host are not forwarded. User Solidity is written to a mode 0600
 * file and deleted in `finally`. It is not returned in the API response.
 *
 * If the CLI is missing, exits without JSON, or is still the scaffold that
 * refuses to scan, the bundled example report is returned and labeled as
 * an example. That is not a scan of the pasted input.
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
    const child = spawn(cliBin(), ["scan", target], {
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

/**
 * Accept CLI JSON only when it is an Arc testnet arcaudit report.
 * Documentation links are replaced with the canonical rule URLs.
 */
export function sanitizeCliReport(
  value: unknown,
  target: ScanReport["target"],
): ScanReport | null {
  if (!value || typeof value !== "object") return null;
  const record = value as Record<string, unknown>;
  if (record.tool !== "arcaudit") return null;
  const network = record.network as Record<string, unknown> | undefined;
  if (!network || network.chainId !== 5042002) return null;
  if (!Array.isArray(record.findings)) return null;

  const findings: Finding[] = [];
  for (const item of record.findings) {
    if (!item || typeof item !== "object") return null;
    const row = item as Record<string, unknown>;
    if (typeof row.ruleId !== "string" || !isRuleId(row.ruleId)) return null;
    const rule = ruleById(row.ruleId);
    if (!rule) return null;
    const line =
      typeof row.line === "number" && Number.isFinite(row.line)
        ? Math.max(1, Math.floor(row.line))
        : 1;
    findings.push({
      ruleId: rule.id,
      path: typeof row.path === "string" ? cleanPath(row.path) : "input",
      symbol: typeof row.symbol === "string" ? row.symbol.slice(0, 120) : "",
      line,
      origin: row.origin === "reference" ? "reference" : "illustrative",
      docsUrl: rule.docs[0].url,
    });
  }

  return {
    tool: "arcaudit",
    version: "0.1.0",
    mode: "cli",
    network: {
      name: "Arc Testnet",
      chainId: 5042002,
      rpcUrl: "https://rpc.testnet.arc.io",
    },
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
    if (parsed && cli.available && !cli.timedOut) {
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
