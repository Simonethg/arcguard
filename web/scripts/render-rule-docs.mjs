/**
 * Write docs/rules from web/content/rules.ts so the GitHub pages and the UI
 * stay on the same copy.
 *
 * The previous stub pages (problem plus a short fix direction, es/en only,
 * links to the doc root) are replaced because each rule needs the problem,
 * a vulnerable example, the fix, pt-BR, and the exact docs.arc.io section.
 */
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { RULES, SOURCE_URLS, USDC_UNITS_URL } from "../content/rules.ts";

const docsDir = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../../docs/rules");

const severity = {
  high: { es: "Alta", en: "High", "pt-BR": "Alta" },
  medium: { es: "Media", en: "Medium", "pt-BR": "Média" },
};

const status = {
  es: "Implementada. ARC-001..ARC-008 corren con slither --detect arc-... y en arcaudit scan --chain arc. ARC-OFF-1 corre con arcaudit scan (offchain/).",
  en: "Implemented. ARC-001..ARC-008 run with slither --detect arc-... and arcaudit scan --chain arc. ARC-OFF-1 runs with arcaudit scan (offchain/).",
  "pt-BR": "Implementada. ARC-001..ARC-008 rodam com slither --detect arc-... e com arcaudit scan --chain arc. ARC-OFF-1 roda com arcaudit scan (offchain/).",
};

function fence(language, code) {
  return "```" + language + "\n" + code + "\n```";
}

function page(rule) {
  const chunks = [
    `# ${rule.id} \`${rule.slug}\``,
    "",
    "<!-- Replaced the es/en stub (problem and fix direction only, no example, no pt-BR, no section anchor). Source of copy: web/content/rules.ts -->",
    "",
    `**Severidad / Severity / Severidade:** ${severity[rule.severity].es} / ${severity[rule.severity].en} / ${severity[rule.severity]["pt-BR"]}`,
    "",
    `**Estado / Status:** ${status.es} / ${status.en} / ${status["pt-BR"]}`,
    "",
    "Fuentes de la regla / Rule sources:",
    "",
    ...SOURCE_URLS.map((url) => `- ${url}`),
    "",
  ];

  for (const locale of ["es", "en", "pt-BR"]) {
    const copy = rule.copy[locale];
    const heading = locale === "es" ? "Español" : locale === "en" ? "English" : "Português (Brasil)";
    chunks.push(`## ${heading}`, "");
    chunks.push(`### Problema / Problem / Problema`, "");
    chunks.push(copy.problem, "");
    chunks.push("### Ejemplo vulnerable / Vulnerable example / Exemplo vulnerável", "");
    chunks.push(copy.vulnerableCaption, "");
    chunks.push(fence(rule.vulnerable.language, rule.vulnerable.code), "");
    chunks.push("### Arreglo / Fix / Correção", "");
    chunks.push(copy.fixCaption, "");
    chunks.push(fence(rule.fix.language, rule.fix.code), "");
    if (rule.usdcUnitsApplies) {
      chunks.push(`UsdcUnits: ${USDC_UNITS_URL}`, "");
    } else {
      chunks.push(
        locale === "es"
          ? "UsdcUnits no aplica a esta regla."
          : locale === "en"
            ? "UsdcUnits does not apply to this rule."
            : "UsdcUnits não se aplica a esta regra.",
        "",
      );
    }
    chunks.push("### Documentación / Documentation / Documentação", "");
    for (const doc of rule.docs) {
      chunks.push(`- [${doc.label[locale]}](${doc.url})`);
    }
    chunks.push("");
  }

  return chunks.join("\n");
}

function indexPage() {
  const rows = RULES.map(
    (rule) =>
      `| ${rule.id} | [\`${rule.slug}\`](${rule.id}.md) | ${severity[rule.severity].es} / ${severity[rule.severity].en} / ${severity[rule.severity]["pt-BR"]} |`,
  );
  return [
    "# Reglas ArcGuard / ArcGuard rules / Regras ArcGuard",
    "",
    "Estas páginas reemplazan los stubs es/en del scaffold. Cada regla tiene el problema, un ejemplo vulnerable, el arreglo (UsdcUnits de scaffold-arc cuando aplica) y el enlace a la sección de docs.arc.io, en español, inglés y portugués de Brasil.",
    "",
    "These pages replace the scaffold es/en stubs. Each rule has the problem, a vulnerable example, the fix (scaffold-arc UsdcUnits when it applies), and the docs.arc.io section link, in Spanish, English, and Brazilian Portuguese.",
    "",
    "Estas páginas substituem os stubs es/en do scaffold. Cada regra tem o problema, um exemplo vulnerável, a correção (UsdcUnits do scaffold-arc quando se aplica) e o link da seção em docs.arc.io, em espanhol, inglês e português do Brasil.",
    "",
    "ArcGuard no certifica seguridad y no reemplaza una auditoría. Solo Arc testnet (chain 5042002). ARC-001..ARC-008 corren con `slither --detect arc-...` y, con el extra `detectors`, también en `arcaudit scan --chain arc`. ARC-OFF-1 corre en `offchain/` sin Slither.",
    "",
    "ArcGuard does not certify security and does not replace an audit. Arc testnet only (chain 5042002). ARC-001..ARC-008 run with `slither --detect arc-...` and, with the `detectors` extra, inside `arcaudit scan --chain arc`. ARC-OFF-1 runs in `offchain/` without Slither.",
    "",
    "O ArcGuard não certifica segurança e não substitui uma auditoria. Somente Arc testnet (chain 5042002). ARC-001..ARC-008 rodam com `slither --detect arc-...` e, com o extra `detectors`, também em `arcaudit scan --chain arc`. ARC-OFF-1 roda em `offchain/` sem Slither.",
    "",
    "## Fuentes / Sources / Fontes",
    "",
    ...SOURCE_URLS.map((url) => `- ${url}`),
    "",
    "## Índice / Index / Índice",
    "",
    "| ID | Página / Page / Página | Severidad / Severity / Severidade |",
    "| --- | --- | --- |",
    ...rows,
    "",
  ].join("\n");
}

await mkdir(docsDir, { recursive: true });
await writeFile(path.join(docsDir, "README.md"), indexPage(), "utf8");
for (const rule of RULES) {
  await writeFile(path.join(docsDir, `${rule.id}.md`), page(rule), "utf8");
}
