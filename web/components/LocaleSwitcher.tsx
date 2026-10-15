"use client";

import { LOCALES, LOCALE_META, type Locale } from "@/lib/i18n/locales";
import { useI18n } from "@/lib/i18n/I18nProvider";

export function LocaleSwitcher() {
  const { locale, setLocale, t } = useI18n();

  return (
    <div
      className="locale-switcher"
      role="group"
      aria-labelledby="locale-label"
      data-testid="locale-switcher"
    >
      <span id="locale-label" className="visually-hidden">
        {t("locale.group")}
      </span>
      {LOCALES.map((code: Locale) => {
        const meta = LOCALE_META[code];
        const selected = locale === code;
        return (
          <button
            key={code}
            type="button"
            className="locale-flag"
            aria-pressed={selected}
            data-testid={`locale-${code}`}
            onClick={() => setLocale(code)}
          >
            <span aria-hidden="true">{meta.flag}</span>
            <span>{meta.label}</span>
          </button>
        );
      })}
    </div>
  );
}
