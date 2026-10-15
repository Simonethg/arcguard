"use client";

import Link from "next/link";
import { LocaleSwitcher } from "@/components/LocaleSwitcher";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function SiteHeader() {
  const { t } = useI18n();

  return (
    <header className="site-header">
      <Link className="brand-mark" href="/" data-testid="brand-home">
        ArcGuard
      </Link>
      <div className="header-tools">
        <nav aria-label="ArcGuard">
          <ul className="nav-list">
            <li>
              <Link href="/" data-testid="nav-scan">
                {t("nav.scan")}
              </Link>
            </li>
            <li>
              <Link href="/report" data-testid="nav-report">
                {t("nav.report")}
              </Link>
            </li>
            <li>
              <Link href="/rules" data-testid="nav-rules">
                {t("nav.rules")}
              </Link>
            </li>
          </ul>
        </nav>
        <LocaleSwitcher />
      </div>
    </header>
  );
}
