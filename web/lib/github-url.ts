/**
 * Accept only public https://github.com/owner/repo URLs.
 * Userinfo, query strings, and other hosts are rejected so a pasted
 * credential cannot be stored or fetched.
 */

export type PublicRepo = {
  href: string;
  label: string;
};

const SEGMENT = /^[A-Za-z0-9_.-]+$/;

export function parsePublicGithubRepo(raw: string): PublicRepo | null {
  const input = raw.trim();
  if (input.length === 0 || input.length > 300) return null;
  if (input.includes("@") || input.includes("\\") || /\s/.test(input)) return null;

  let url: URL;
  try {
    url = new URL(input);
  } catch {
    return null;
  }

  if (url.protocol !== "https:") return null;
  if (url.username || url.password) return null;
  if (url.port) return null;
  if (url.search || url.hash) return null;

  const host = url.hostname.toLowerCase();
  if (host !== "github.com" && host !== "www.github.com") return null;

  const parts = url.pathname.split("/").filter(Boolean);
  if (parts.length < 2) return null;

  const owner = parts[0];
  let repo = parts[1];
  if (repo.endsWith(".git")) repo = repo.slice(0, -4);
  if (!SEGMENT.test(owner) || !SEGMENT.test(repo) || repo.length === 0) return null;
  if (parts.slice(2).some((part) => part === "." || part === "..")) return null;

  return {
    href: `https://github.com/${owner}/${repo}`,
    label: `${owner}/${repo}`,
  };
}
