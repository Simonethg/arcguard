"use client";

import { SOURCE_URLS } from "@/content/rules";
import { ExternalLink } from "@/components/ExternalLink";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function SiteFooter() {
  const { t } = useI18n();

  return (
    <footer className="site-footer">
      <p data-testid="footer-disclaimer">{t("footer.disclaimer")}</p>
      <p>{t("footer.testnet")}</p>
      <p>
        <ExternalLink href="https://www.arc.io/security">Security on Arc</ExternalLink>
      </p>
      <p>{t("footer.sources")}</p>
      <ul className="source-list">
        {SOURCE_URLS.map((url) => (
          <li key={url}>
            <ExternalLink href={url}>{url}</ExternalLink>
          </li>
        ))}
      </ul>
      <p>{t("footer.license")}</p>
    </footer>
  );
}
