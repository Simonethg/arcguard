# ArcGuard web

Next.js (App Router) UI for ArcGuard. Paste a public GitHub repository URL or a `.sol` file and read the report. Arc testnet only (chain `5042002`, `https://rpc.testnet.arc.io`).

ArcGuard does not certify security and does not replace an audit.

Interfaz Next.js para ArcGuard. Pegá la URL de un repositorio público de GitHub o un archivo `.sol` y leé el reporte. Solo Arc testnet (chain `5042002`). ArcGuard no certifica seguridad y no reemplaza una auditoría.

## Run

```bash
cd web
npm install
npm test
npm run build
npm start
```

Open `/` to submit a target, `/report` for the bundled example, and `/rules` for ARC-001..008 and ARC-OFF-1.

`POST /api/scan` runs `arcaudit scan` in a temp directory and deletes that directory afterwards. The child process does not inherit the parent environment. The scaffold CLI does not emit JSON yet, so the API returns `fixtures/sample-report.json` and the page labels it as an example. That example is not a scan of the pasted input.

There is no analytics and no third-party key.

## Languages

Español, English, and Português (Brasil). The switcher is `data-testid="locale-switcher"`. The choice is stored under `arcguard-locale`.

## Rules

`npm run docs:rules` rewrites `docs/rules/` from `content/rules.ts`.

The scaffold stubs in `docs/rules/` (problem and a short fix direction, Spanish and English only, links to the doc root) were replaced. Each page now has the problem, a vulnerable example, the fix (`UsdcUnits` from [scaffold-arc](https://github.com/Simonethg/scaffold-arc/blob/main/packages/foundry/src/UsdcUnits.sol) when it applies), and the exact `docs.arc.io` section, in es / en / pt-BR.

Los stubs del scaffold en `docs/rules/` se reemplazaron por ese contenido.

## Sources

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps

## Accessibility

`npm run test:axe` starts `next start` and runs axe-core against the changed components only (`scan-form`, `locale-switcher`, `report-view`, `rule-article`) at 390px and 1440px. Run `npm run build` first. Critical and serious violations fail the script. Selectors are `data-testid` first.
