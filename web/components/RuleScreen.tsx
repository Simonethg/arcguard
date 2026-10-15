"use client";

import Link from "next/link";
import { ruleById, USDC_UNITS_URL, type RuleId } from "@/content/rules";
import { CodeBlock } from "@/components/CodeBlock";
import { ExternalLink } from "@/components/ExternalLink";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function RuleScreen({ id }: { id: RuleId }) {
  const { t, locale } = useI18n();
  const rule = ruleById(id);
  if (!rule) return null;
  const copy = rule.copy[locale];
  const problemId = `${rule.id}-problem`;
  const vulnId = `${rule.id}-vuln`;
  const fixId = `${rule.id}-fix`;

  return (
    <article data-testid="rule-article" aria-labelledby="rule-title">
      <p>
        <Link className="action-link" href="/rules">
          {t("rule.back")}
        </Link>
      </p>
      <h1 id="rule-title">
        {rule.id} <span className="muted">{rule.slug}</span>
      </h1>
      <p>
        <span className={`badge ${rule.severity}`}>
          <span className="visually-hidden">{t("severity.group")} </span>
          {t(rule.severity === "high" ? "severity.high" : "severity.medium")}
        </span>
      </p>
      <p className="lede">{copy.name}</p>
      <p data-testid="rule-status">{t("rule.status")}</p>

      <section className="section-gap" aria-labelledby={problemId}>
        <h2 id={problemId}>{t("rule.problem")}</h2>
        <p>{copy.problem}</p>
      </section>

      <section className="section-gap" aria-labelledby={vulnId}>
        <h2 id={vulnId}>{t("rule.vulnerable")}</h2>
        <p>{copy.vulnerableCaption}</p>
        <CodeBlock code={rule.vulnerable.code} labelledBy={vulnId} />
      </section>

      <section className="section-gap" aria-labelledby={fixId}>
        <h2 id={fixId}>{t("rule.fix")}</h2>
        <p>{copy.fixCaption}</p>
        <CodeBlock code={rule.fix.code} labelledBy={fixId} />
        {rule.usdcUnitsApplies ? (
          <p>
            <ExternalLink href={USDC_UNITS_URL} testId="usdc-units-link">
              {t("rule.usdcUnits")}
            </ExternalLink>
          </p>
        ) : (
          <p data-testid="usdc-units-na">{t("rule.usdcUnitsNa")}</p>
        )}
      </section>

      <section className="section-gap" aria-labelledby="rule-docs">
        <h2 id="rule-docs">{t("rule.docs")}</h2>
        <ul className="source-list">
          {rule.docs.map((doc, index) => (
            <li key={doc.url}>
              <ExternalLink href={doc.url} testId={`rule-doc-${index}`}>
                {doc.label[locale]}
              </ExternalLink>
            </li>
          ))}
        </ul>
      </section>
    </article>
  );
}
