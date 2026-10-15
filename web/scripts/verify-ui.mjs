/**
 * Exercise the scan flow and run axe-core on the changed components only.
 * Viewports: 390x844 (mobile) and 1440x900 (desktop).
 * Critical and serious violations fail the process. Moderate and minor are printed.
 */
import { spawn } from "node:child_process";
import { fileURLToPath } from "node:url";
import path from "node:path";
import AxeBuilder from "@axe-core/playwright";
import { chromium } from "playwright";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const port = Number(process.env.PORT ?? "3456");
const base = process.env.BASE_URL ?? `http://127.0.0.1:${port}`;
const ownServer = !process.env.BASE_URL;

const viewports = [
  { name: "desktop", width: 1440, height: 900 },
  { name: "mobile", width: 390, height: 844 },
];

const scopes = [
  { path: "/report", selector: '[data-testid="report-view"]' },
  { path: "/", selector: '[data-testid="scan-form"]' },
  { path: "/", selector: '[data-testid="locale-switcher"]' },
  { path: "/rules/ARC-001", selector: '[data-testid="rule-article"]' },
];

async function waitForHttp() {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    try {
      const response = await fetch(base);
      if (response.status < 500) return;
    } catch {
      // Server is still booting.
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
  }
  throw new Error("server did not start");
}

async function axeInclude(page, selector) {
  return new AxeBuilder({ page }).include(selector).analyze();
}

const blocking = [];
const observations = [];

let server;
if (ownServer) {
  server = spawn("npx", ["next", "start", "-H", "127.0.0.1", "-p", String(port)], {
    cwd: root,
    env: { ...process.env, NEXT_TELEMETRY_DISABLED: "1" },
    stdio: ["ignore", "pipe", "pipe"],
  });
  await waitForHttp();
}

const browser = await chromium.launch({ headless: true });
const context = await browser.newContext();
await context.addInitScript(() => {
  localStorage.setItem("arcguard-locale", "es");
});
const page = await context.newPage();

try {
  for (const viewport of viewports) {
    await page.setViewportSize({ width: viewport.width, height: viewport.height });
    for (const scope of scopes) {
      await page.goto(`${base}${scope.path}`, { waitUntil: "networkidle" });
      await page.locator(scope.selector).waitFor();
      const result = await axeInclude(page, scope.selector);
      for (const violation of result.violations) {
        const row = {
          viewport: viewport.name,
          path: scope.path,
          selector: scope.selector,
          id: violation.id,
          impact: violation.impact,
          help: violation.help,
          nodes: violation.nodes.length,
        };
        if (violation.impact === "critical" || violation.impact === "serious") blocking.push(row);
        else observations.push(row);
      }
    }
  }

  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/report`, { waitUntil: "networkidle" });
  await page.getByTestId("report-view").waitFor();
  const reportText = await page.getByTestId("report-view").innerText();
  if (!reportText.includes("ARC-001")) throw new Error("example report is missing ARC-001");
  if (!reportText.includes("NaiveEthereumPort")) throw new Error("example report is missing NaiveEthereumPort");
  const docHref = await page.getByTestId("docs-ARC-001").getAttribute("href");
  if (!docHref?.includes("https://docs.arc.io/arc/references/evm-differences#value-transfer-rules")) {
    throw new Error(`unexpected docs href ${docHref}`);
  }

  await page.getByTestId("locale-en").click();
  await page.getByText("This is the bundled example report.").waitFor();
  if ((await page.locator("html").getAttribute("lang")) !== "en") {
    throw new Error("html lang did not switch to en");
  }
  await page.getByTestId("locale-pt-BR").click();
  await page.getByText("Este é o relatório de exemplo empacotado.").waitFor();
  await page.getByTestId("locale-es").click();

  await page.goto(`${base}/`, { waitUntil: "networkidle" });
  await page.getByTestId("github-url").fill("https://github.com/Simonethg/scaffold-arc");
  await page.getByTestId("scan-submit").click();
  await page.getByTestId("report-view").waitFor();
  const homeReport = await page.getByTestId("report-view").innerText();
  if (!homeReport.includes("ARC-001")) throw new Error("submitted report is missing ARC-001");
  if (!homeReport.includes("Simonethg/scaffold-arc")) throw new Error("target label missing");
  if (!homeReport.includes("ejemplo")) throw new Error("submitted report is not labeled as an example");
  await page.screenshot({ path: "/tmp/arcguard-ui/submit-desktop.png", fullPage: true });

  const githubScan = await fetch(`${base}/api/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      kind: "github",
      githubUrl: "https://github.com/Simonethg/scaffold-arc",
    }),
  });
  const githubPayload = await githubScan.json();
  if (githubPayload.mode !== "example") throw new Error("github scan was not the example report");
  if (githubPayload.report?.network?.chainId !== 5042002) throw new Error("github scan left testnet");
  if (!githubPayload.cli?.attempted) throw new Error("sandbox did not attempt the CLI");

  const fileScan = await fetch(`${base}/api/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({
      kind: "file",
      filename: "Pay.sol",
      source: "pragma solidity ^0.8.24;\ncontract Pay { function f() external payable {} }\n",
    }),
  });
  const filePayload = await fileScan.json();
  if (filePayload.mode !== "example" || filePayload.report?.target?.label !== "Pay.sol") {
    throw new Error("file scan did not return the labeled example");
  }

  const rejected = await fetch(`${base}/api/scan`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ kind: "github", githubUrl: "https://user:hunter2@github.com/a/b" }),
  });
  if (rejected.status !== 400) throw new Error("credential URL was accepted");

  await page.goto(`${base}/rules/ARC-001`, { waitUntil: "networkidle" });
  const article = await page.getByTestId("rule-article").innerText();
  if (!article.includes("UsdcUnits")) throw new Error("rule page is missing UsdcUnits");
  const ruleDoc = await page.getByTestId("rule-doc-0").getAttribute("href");
  if (!ruleDoc?.includes("#value-transfer-rules")) throw new Error(`rule doc href ${ruleDoc}`);

  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto(`${base}/`, { waitUntil: "networkidle" });
  await page.getByTestId("scan-form").waitFor();
  const box = await page.getByTestId("scan-submit").boundingBox();
  if (!box || box.width < 44 || box.height < 44) {
    throw new Error(`submit target is smaller than 44px: ${JSON.stringify(box)}`);
  }

  await page.screenshot({ path: "/tmp/arcguard-ui/home-mobile.png", fullPage: true });
  await page.setViewportSize({ width: 1440, height: 900 });
  await page.goto(`${base}/report`, { waitUntil: "networkidle" });
  await page.screenshot({ path: "/tmp/arcguard-ui/report-desktop.png", fullPage: true });
  await page.goto(`${base}/rules/ARC-001`, { waitUntil: "networkidle" });
  await page.screenshot({ path: "/tmp/arcguard-ui/rule-desktop.png", fullPage: true });
} finally {
  await browser.close();
  if (server) server.kill("SIGTERM");
}

const summary = { blocking, observations };
console.log(JSON.stringify(summary, null, 2));
if (blocking.length > 0) {
  process.exitCode = 1;
}
