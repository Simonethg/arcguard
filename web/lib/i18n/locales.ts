/**
 * Locale set matches the ArcGuard web task: es, en, pt-BR.
 * Flag treatment and storage follow scaffold-arc, with a product-specific key.
 * https://github.com/Simonethg/scaffold-arc
 */

export const LOCALES = ["es", "en", "pt-BR"] as const;

export type Locale = (typeof LOCALES)[number];

export const DEFAULT_LOCALE: Locale = "es";

export const LOCALE_STORAGE_KEY = "arcguard-locale";

export const LOCALE_META: Record<
  Locale,
  { flag: string; label: string; htmlLang: string }
> = {
  es: { flag: "🇦🇷", label: "Español", htmlLang: "es" },
  en: { flag: "🇬🇧", label: "English", htmlLang: "en" },
  "pt-BR": { flag: "🇧🇷", label: "Português", htmlLang: "pt-BR" },
};

export function isLocale(value: string | null | undefined): value is Locale {
  return !!value && (LOCALES as readonly string[]).includes(value);
}

/** Prefer es / pt-BR from the browser, otherwise English. */
export function detectBrowserLocale(): Locale {
  if (typeof navigator === "undefined") return DEFAULT_LOCALE;
  const candidates = [navigator.language, ...(navigator.languages ?? [])].filter(Boolean);
  for (const raw of candidates) {
    const lower = raw.toLowerCase();
    if (lower.startsWith("es")) return "es";
    if (lower.startsWith("pt")) return "pt-BR";
    if (lower.startsWith("en")) return "en";
  }
  return DEFAULT_LOCALE;
}
