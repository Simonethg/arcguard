"use client";

import { useId, useState, type ChangeEvent, type FormEvent } from "react";
import { ReportView } from "@/components/ReportView";
import { useI18n } from "@/lib/i18n/I18nProvider";
import { MAX_SOURCE_CHARS, validateSolidity } from "@/lib/solidity-input";
import type { ScanApiError, ScanApiSuccess, ScanErrorCode } from "@/lib/types";

const ERROR_KEYS: Record<ScanErrorCode, "scan.error.invalid-json" | "scan.error.empty" | "scan.error.both" | "scan.error.invalid-github-url" | "scan.error.too-large" | "scan.error.not-solidity"> = {
  "invalid-json": "scan.error.invalid-json",
  empty: "scan.error.empty",
  both: "scan.error.both",
  "invalid-github-url": "scan.error.invalid-github-url",
  "too-large": "scan.error.too-large",
  "not-solidity": "scan.error.not-solidity",
};

export function ScanForm() {
  const { t } = useI18n();
  const githubHintId = useId();
  const pasteHintId = useId();
  const statusId = useId();
  const [githubUrl, setGithubUrl] = useState("");
  const [filename, setFilename] = useState("input.sol");
  const [source, setSource] = useState("");
  const [pending, setPending] = useState(false);
  const [error, setError] = useState<ScanErrorCode | "network" | null>(null);
  const [result, setResult] = useState<ScanApiSuccess | null>(null);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setResult(null);

    const url = githubUrl.trim();
    const body = source.trim();
    if (url && body) {
      setError("both");
      return;
    }
    if (!url && !body) {
      setError("empty");
      return;
    }
    if (body) {
      const issue = validateSolidity(source);
      if (issue !== "ok") {
        setError(issue);
        return;
      }
    }

    setPending(true);
    try {
      const response = await fetch("/api/scan", {
        method: "POST",
        headers: { "content-type": "application/json" },
        body: JSON.stringify(
          url
            ? { kind: "github", githubUrl: url }
            : { kind: "file", filename, source },
        ),
      });
      const payload = (await response.json()) as ScanApiSuccess | ScanApiError;
      if (!response.ok || "error" in payload) {
        const code = "error" in payload ? payload.error : "invalid-json";
        setError(code);
        return;
      }
      setResult(payload);
    } catch {
      setError("network");
    } finally {
      setPending(false);
    }
  }

  async function onFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) return;
    if (file.size > MAX_SOURCE_CHARS) {
      setError("too-large");
      return;
    }
    const text = await file.text();
    setFilename(file.name);
    setSource(text);
    setError(null);
  }

  const errorText =
    error === "network"
      ? t("scan.error.network")
      : error
        ? t(ERROR_KEYS[error])
        : "";

  return (
    <>
      <form
        className="panel"
        data-testid="scan-form"
        aria-labelledby="scan-title"
        aria-describedby={githubHintId}
        aria-busy={pending}
        onSubmit={onSubmit}
      >
        <h2 id="scan-title" className="visually-hidden">
          {t("nav.scan")}
        </h2>
        <div className="field">
          <label htmlFor="github-url">{t("scan.githubLabel")}</label>
          <input
            id="github-url"
            name="githubUrl"
            type="url"
            inputMode="url"
            autoComplete="off"
            spellCheck={false}
            maxLength={300}
            value={githubUrl}
            aria-describedby={githubHintId}
            aria-invalid={error === "invalid-github-url" || error === "both" || error === "empty"}
            data-testid="github-url"
            onChange={(event) => setGithubUrl(event.target.value)}
          />
          <p id={githubHintId} className="hint">
            {t("scan.githubHint")}
          </p>
        </div>
        <p className="or-rule">{t("scan.or")}</p>
        <div className="field">
          <label htmlFor="sol-file">{t("scan.fileLabel")}</label>
          <input
            id="sol-file"
            name="solFile"
            type="file"
            accept=".sol,text/plain"
            data-testid="sol-file"
            onChange={onFile}
          />
        </div>
        <div className="field">
          <label htmlFor="sol-source">{t("scan.pasteLabel")}</label>
          <textarea
            id="sol-source"
            name="source"
            spellCheck={false}
            maxLength={MAX_SOURCE_CHARS}
            value={source}
            aria-describedby={pasteHintId}
            aria-invalid={error === "not-solidity" || error === "too-large" || error === "both"}
            data-testid="sol-source"
            onChange={(event) => setSource(event.target.value)}
          />
          <p id={pasteHintId} className="hint">
            {t("scan.pasteHint")} {t("scan.help")}
          </p>
        </div>
        <div className="actions">
          <button type="submit" data-testid="scan-submit" disabled={pending}>
            {pending ? t("scan.pending") : t("scan.submit")}
          </button>
        </div>
        <p
          id={statusId}
          className={errorText ? "status error" : "status"}
          role="status"
          aria-live="polite"
          tabIndex={-1}
          data-testid="scan-status"
        >
          {errorText}
        </p>
      </form>
      {result ? (
        <ReportView
          report={result.report}
          banner="api"
          cliNote={result.cli.note}
          headingLevel="h2"
          autoFocusHeading
        />
      ) : null}
    </>
  );
}
