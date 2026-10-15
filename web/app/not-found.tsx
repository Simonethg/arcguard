"use client";

import Link from "next/link";
import { useI18n } from "@/lib/i18n/I18nProvider";

export default function NotFound() {
  const { t } = useI18n();
  return (
    <section data-testid="not-found">
      <h1>{t("notFound.title")}</h1>
      <p>{t("notFound.body")}</p>
      <p>
        <Link className="action-link" href="/">
          {t("notFound.home")}
        </Link>
      </p>
    </section>
  );
}
