"use client";

import Link from "next/link";
import { RULES } from "@/content/rules";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function RulesScreen() {
  const { t, locale } = useI18n();

  return (
    <section data-testid="rules-index">
      <h1>{t("rules.title")}</h1>
      <p className="lede">{t("rules.lede")}</p>
      <ul className="rule-grid section-gap">
        {RULES.map((rule) => (
          <li key={rule.id}>
            <Link className="rule-card" href={`/rules/${rule.id}`} data-testid={`rule-link-${rule.id}`}>
              <span>
                <h2>
                  {rule.id} · {rule.copy[locale].name}
                </h2>
                <p className="hint">{rule.slug}</p>
              </span>
              <span className={`badge ${rule.severity}`}>
                <span className="visually-hidden">{t("severity.group")} </span>
                {t(rule.severity === "high" ? "severity.high" : "severity.medium")}
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
