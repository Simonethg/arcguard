import assert from "node:assert/strict";
import { readFileSync, readdirSync } from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";
import { RULES, RULE_IDS, SOURCE_URLS } from "../content/rules.ts";
import { parsePublicGithubRepo } from "../lib/github-url.ts";
import { sanitizeCliReport } from "../lib/scan-sandbox.ts";
import { validateSolidity } from "../lib/solidity-input.ts";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");

test("public github urls are limited to https github.com owner/repo", () => {
  const repo = parsePublicGithubRepo("https://github.com/Simonethg/scaffold-arc/");
  assert.equal(repo?.label, "Simonethg/scaffold-arc");
  assert.equal(repo?.href, "https://github.com/Simonethg/scaffold-arc");
  assert.equal(
    parsePublicGithubRepo("https://github.com/Simonethg/scaffold-arc/blob/main/README.md")?.label,
    "Simonethg/scaffold-arc",
  );
  assert.equal(parsePublicGithubRepo("http://github.com/Simonethg/scaffold-arc"), null);
  assert.equal(parsePublicGithubRepo("https://user:hunter2@github.com/a/b"), null);
  assert.equal(parsePublicGithubRepo("https://github.com/a/b?ref=main"), null);
  assert.equal(parsePublicGithubRepo("https://gitlab.com/a/b"), null);
  assert.equal(parsePublicGithubRepo("https://github.com/only-owner"), null);
});

test("solidity input rejects empty, huge, and non-source text", () => {
  assert.equal(validateSolidity("   "), "empty");
  assert.equal(validateSolidity("not code"), "not-solidity");
  assert.equal(validateSolidity("contract Foo {}"), "ok");
  assert.equal(validateSolidity("a".repeat(100_001)), "too-large");
});

test("every v0.1 rule has three locales, a docs anchor, and a fix", () => {
  assert.deepEqual(
    RULES.map((rule) => rule.id),
    [...RULE_IDS],
  );
  for (const rule of RULES) {
    for (const locale of ["es", "en", "pt-BR"] as const) {
      const copy = rule.copy[locale];
      assert.ok(copy.problem.length > 40, `${rule.id} ${locale} problem`);
      assert.ok(copy.vulnerableCaption.length > 10);
      assert.ok(copy.fixCaption.length > 10);
      assert.ok(copy.findingSummary.length > 10);
    }
    assert.ok(rule.vulnerable.code.includes("\n") || rule.vulnerable.code.length > 10);
    assert.ok(rule.fix.code.length > 10);
    assert.ok(rule.docs[0].url.startsWith("https://docs.arc.io/"));
    assert.ok(rule.docs[0].url.includes("#"), rule.id);
    if (rule.usdcUnitsApplies) {
      assert.match(rule.fix.code, /UsdcUnits/);
    }
  }
  assert.equal(SOURCE_URLS.length, 3);
});

test("sample report is Arc testnet and only cites documented rules", () => {
  const sample = JSON.parse(
    readFileSync(path.join(root, "fixtures/sample-report.json"), "utf8"),
  ) as {
    network: { chainId: number; rpcUrl: string };
    findings: { ruleId: string; origin: string; docsUrl: string }[];
  };
  assert.equal(sample.network.chainId, 5042002);
  assert.equal(sample.network.rpcUrl, "https://rpc.testnet.arc.io");
  const ids = new Set(RULE_IDS);
  const reference = sample.findings.filter((row) => row.origin === "reference").map((row) => row.ruleId);
  assert.deepEqual(reference, ["ARC-001", "ARC-003"]);
  for (const row of sample.findings) {
    assert.ok(ids.has(row.ruleId as (typeof RULE_IDS)[number]));
    assert.ok(row.docsUrl.startsWith("https://docs.arc.io/"));
  }
});

test("cli json from another chain is discarded", () => {
  assert.equal(
    sanitizeCliReport(
      {
        tool: "arcaudit",
        network: { chainId: 1 },
        findings: [],
      },
      { kind: "file", label: "input.sol" },
    ),
    null,
  );
  const kept = sanitizeCliReport(
    {
      tool: "arcaudit",
      network: { chainId: 5042002 },
      findings: [
        {
          ruleId: "ARC-001",
          path: "/tmp/arcguard-scan-abc/Pay.sol",
          symbol: "pay",
          line: 4,
          origin: "illustrative",
          docsUrl: "javascript:alert(1)",
        },
      ],
    },
    { kind: "file", label: "Pay.sol" },
  );
  assert.equal(kept?.mode, "cli");
  assert.equal(kept?.network.chainId, 5042002);
  assert.equal(kept?.findings[0].path, "Pay.sol");
  assert.ok(kept?.findings[0].docsUrl.startsWith("https://docs.arc.io/"));
});

test("dictionaries share keys and the web tree does not name a mainnet rpc", () => {
  const dictDir = path.join(root, "lib/i18n/dictionaries");
  const es = JSON.parse(readFileSync(path.join(dictDir, "es.json"), "utf8")) as Record<string, string>;
  for (const name of ["en.json", "pt-BR.json"]) {
    const other = JSON.parse(readFileSync(path.join(dictDir, name), "utf8")) as Record<string, string>;
    assert.deepEqual(Object.keys(other).sort(), Object.keys(es).sort(), name);
  }

  const files = walk(root).filter(
    (file) =>
      !file.includes(`${path.sep}node_modules${path.sep}`) &&
      !file.includes(`${path.sep}test${path.sep}`),
  );
  const blob = files
    .filter((file) => /\.(ts|tsx|json|mjs|css|md)$/.test(file))
    .map((file) => readFileSync(file, "utf8"))
    .join("\n");
  const mainnetHost = ["rpc", "mainnet.arc.io"].join(".");
  assert.equal(blob.includes(mainnetHost), false);
  assert.equal(/chainId["']?\s*[:=]\s*5042\b/.test(blob), false);
});

function walk(dir: string): string[] {
  const out: string[] = [];
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.name === "node_modules" || entry.name === ".next") continue;
    if (entry.isDirectory()) out.push(...walk(full));
    else out.push(full);
  }
  return out;
}
