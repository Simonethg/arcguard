"use client";

import Link from "next/link";
import { ScanForm } from "@/components/ScanForm";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function HomeScreen() {
  const { t } = useI18n();

  return (
    <>
      <section className="hero">
        <h1>{t("hero.title")}</h1>
        <p>{t("hero.lede")}</p>
        <p className="disclaimer" data-testid="disclaimer">
          {t("hero.disclaimer")}
        </p>
        <p>
          <Link className="action-link" href="/report" data-testid="example-report-link">
            {t("nav.report")}
          </Link>
        </p>
      </section>
      <ScanForm />
    </>
  );
}
