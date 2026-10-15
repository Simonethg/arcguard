"use client";

import Link from "next/link";
import { useEffect, useRef } from "react";
import { ruleById, USDC_UNITS_URL } from "@/content/rules";
import { CodeBlock } from "@/components/CodeBlock";
import { ExternalLink } from "@/components/ExternalLink";
import { useI18n, type MessageKey } from "@/lib/i18n/I18nProvider";
import type { CliNote, Finding, ScanReport } from "@/lib/types";

const CLI_NOTE: Record<CliNote, MessageKey> = {
  missing: "report.note.missing",
  "not-implemented": "report.note.not-implemented",
  "not-json": "report.note.not-json",
  timeout: "report.note.timeout",
  ok: "report.note.ok",
};

type Banner = "static" | "api";

export function ReportView({
  report,
  banner,
  cliNote,
  headingLevel = "h1",
  autoFocusHeading = false,
}: {
  report: ScanReport;
  banner: Banner;
  cliNote?: CliNote;
  headingLevel?: "h1" | "h2";
  autoFocusHeading?: boolean;
}) {
  const { t, locale } = useI18n();
  const headingRef = useRef<HTMLHeadingElement>(null);
  const Heading = headingLevel;

  useEffect(() => {
    if (autoFocusHeading) headingRef.current?.focus();
  }, [autoFocusHeading, report.target.label, report.mode]);

  const high = report.findings.filter((finding) => ruleById(finding.ruleId)?.severity === "high").length;
  const medium = report.findings.length - high;
  const reference = report.findings.filter((finding) => finding.origin === "reference");
  const illustrative = report.findings.filter((finding) => finding.origin === "illustrative");
  const referenceRepo = report.target.label.toLowerCase().includes("simonethg/scaffold-arc");

  const bannerText =
    report.mode === "cli"
      ? t("report.cliBanner")
      : banner === "static"
        ? t("report.staticBanner")
        : t("report.apiExampleBanner");

  return (
    <section className="panel" data-testid="report-view" aria-labelledby="report-title">
      <Heading id="report-title" tabIndex={-1} ref={headingRef}>
        {t("report.title")}
      </Heading>
      <p className="banner" data-testid="example-banner" role="note">
        {bannerText}
        {cliNote ? ` ${t(CLI_NOTE[cliNote])}` : ""}
        {referenceRepo && report.mode === "example" ? ` ${t("report.referenceMatch")}` : ""}
      </p>
      <p className="summary-line" data-testid="report-summary">
        {t("report.counts", {
          total: String(report.findings.length),
          high: String(high),
          medium: String(medium),
        })}
      </p>
      <dl className="facts">
        <dt>{t("report.target")}</dt>
        <dd data-testid="report-target">{report.target.label}</dd>
        <dt>{t("report.network")}</dt>
        <dd>{report.network.name}</dd>
        <dt>{t("report.chain")}</dt>
        <dd>{report.network.chainId}</dd>
        <dt>{t("report.mode")}</dt>
        <dd>{report.mode === "cli" ? t("report.mode.cli") : t("report.mode.example")}</dd>
      </dl>

      {report.findings.length === 0 ? <p>{t("report.empty")}</p> : null}

      <FindingGroup
        heading={t("report.referenceHeading")}
        note={t("report.referenceNote")}
        findings={reference}
        locale={locale}
        headingLevel={headingLevel === "h1" ? "h2" : "h3"}
      />
      <FindingGroup
        heading={t("report.illustrativeHeading")}
        note={t("report.illustrativeNote")}
        findings={illustrative}
        locale={locale}
        headingLevel={headingLevel === "h1" ? "h2" : "h3"}
      />

      <details className="report-json">
        <summary>{t("report.json")}</summary>
        <CodeBlock code={JSON.stringify(report, null, 2)} labelledBy="report-title" />
      </details>
    </section>
  );
}

function FindingGroup({
  heading,
  note,
  findings,
  locale,
  headingLevel,
}: {
  heading: string;
  note: string;
  findings: Finding[];
  locale: "es" | "en" | "pt-BR";
  headingLevel: "h2" | "h3";
}) {
  const { t } = useI18n();
  if (findings.length === 0) return null;
  const Heading = headingLevel;

  return (
    <div className="section-gap">
      <Heading>{heading}</Heading>
      <p className="hint">{note}</p>
      <ul className="finding-list">
        {findings.map((finding) => {
          const rule = ruleById(finding.ruleId);
          if (!rule) return null;
          const copy = rule.copy[locale];
          return (
            <li
              key={`${finding.ruleId}-${finding.symbol}`}
              className="finding"
              data-testid="finding"
              data-rule={finding.ruleId}
            >
              <div className="finding-top">
                <strong>{finding.ruleId}</strong>
                <span className={`badge ${rule.severity}`}>
                  <span className="visually-hidden">{t("severity.group")} </span>
                  {t(rule.severity === "high" ? "severity.high" : "severity.medium")}
                </span>
                <span className="badge origin">
                  {finding.origin === "reference"
                    ? t("report.origin.reference")
                    : t("report.origin.illustrative")}
                </span>
              </div>
              <p>{copy.findingSummary}</p>
              <p className="hint">{copy.findingDetail}</p>
              <p className="meta">
                {finding.path}
                {finding.symbol ? ` · ${finding.symbol}` : ""} · {t("report.line")} {finding.line}
              </p>
              <div className="action-row">
                <ExternalLink href={finding.docsUrl} testId={`docs-${finding.ruleId}`}>
                  {t("report.docLink")}
                </ExternalLink>
                <Link className="action-link" href={`/rules/${finding.ruleId}`}>
                  {t("report.ruleLink")}
                </Link>
                {rule.usdcUnitsApplies ? (
                  <ExternalLink href={USDC_UNITS_URL} testId={`usdc-${finding.ruleId}`}>
                    {t("report.usdcUnits")}
                  </ExternalLink>
                ) : (
                  <span data-testid={`usdc-na-${finding.ruleId}`}>{t("report.usdcUnitsNa")}</span>
                )}
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
