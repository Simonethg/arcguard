/**
 * Sandboxed scan endpoint.
 *
 * Calls `arcaudit scan <target> --format json` when the CLI is installed.
 * Findings in that JSON are the report. The bundled example is returned
 * only when the CLI is missing or the JSON has no findings. The example
 * is labeled as an example. It is not a verdict on the input.
 *
 * Arc testnet only (chain 5042002). No analytics and no third-party calls.
 *
 * - https://docs.arc.io/arc/references/evm-differences
 * - https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
 * - https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
 */

import { NextResponse } from "next/server";
import { parsePublicGithubRepo } from "@/lib/github-url";
import { runSandboxedScan } from "@/lib/scan-sandbox";
import { MAX_SOURCE_CHARS, validateSolidity } from "@/lib/solidity-input";
import type { ScanErrorCode } from "@/lib/types";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function fail(error: ScanErrorCode, status: number) {
  return NextResponse.json({ error }, { status });
}

export async function POST(request: Request) {
  const length = Number(request.headers.get("content-length") ?? "0");
  if (Number.isFinite(length) && length > MAX_SOURCE_CHARS + 2_000) {
    return fail("too-large", 413);
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return fail("invalid-json", 400);
  }
  if (!body || typeof body !== "object") return fail("invalid-json", 400);

  const record = body as Record<string, unknown>;
  const kind = record.kind;
  const githubUrl = typeof record.githubUrl === "string" ? record.githubUrl : "";
  const source = typeof record.source === "string" ? record.source : "";
  const filename = typeof record.filename === "string" ? record.filename : undefined;

  if (kind !== "github" && kind !== "file") return fail("empty", 400);
  if (kind === "github" && source.trim()) return fail("both", 400);
  if (kind === "file" && githubUrl.trim()) return fail("both", 400);

  if (kind === "github") {
    const repo = parsePublicGithubRepo(githubUrl);
    if (!repo) return fail("invalid-github-url", 400);
    const result = await runSandboxedScan({ kind: "github", label: repo.label });
    return NextResponse.json(result);
  }

  const issue = validateSolidity(source);
  if (issue !== "ok") return fail(issue, 400);
  const safeName = filename && filename.length <= 80 ? filename : "input.sol";
  const result = await runSandboxedScan({
    kind: "file",
    label: safeName.split(/[/\\]/).pop() || "input.sol",
    source,
    filename: safeName,
  });
  return NextResponse.json(result);
}
