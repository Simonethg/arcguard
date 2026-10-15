"use client";

import type { ReactNode } from "react";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function ExternalLink({
  href,
  children,
  testId,
}: {
  href: string;
  children: ReactNode;
  testId?: string;
}) {
  const { t } = useI18n();
  return (
    <a
      className="action-link"
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      data-testid={testId}
    >
      {children}
      <span className="visually-hidden"> ({t("report.newTab")})</span>
    </a>
  );
}
