# ArcGuard

Escáner open source (MIT) de trampas específicas de [Arc](https://www.arc.io) al portar contratos y herramientas desde Ethereum. El comando es `arcaudit`.

**ArcGuard no certifica seguridad y no reemplaza una auditoría.** Un reporte vacío, o un escaneo que todavía no corre, no significa que un contrato sea seguro. Este repositorio es solo **Arc testnet**. No incluye configuración de mainnet, claves ni datos personales.

Open-source (MIT) scanner for Arc-specific pitfalls when porting contracts and tooling from Ethereum. The command is `arcaudit`.

**ArcGuard does not certify security and does not replace an audit.** An empty report, or a scan that does not run yet, does not mean a contract is safe. This repository targets **Arc testnet only**. It does not ship mainnet configuration, keys, or personal data.

Slither encuentra bugs de Ethereum. ArcGuard busca los que aparecen al portar a Arc. / Slither finds Ethereum bugs. ArcGuard looks for the ones that show up when porting to Arc.

## Estado de este scaffold / Scaffold status

`pip install -e .` instala el paquete `arcguard`, el comando `arcaudit` y el entry point de plugin de Slither (`slither_analyzer.plugin` → `arcguard.plugin:make_plugin`). `arcaudit --help` responde. `arcaudit scan` sale con código 2 y **no** ejecuta detectores: las listas del plugin están vacías a propósito, para no publicar un chequeo que todavía no existe. La GitHub Action igual ejecuta ese comando. Mientras el CLI no escriba SARIF, la Action aplica reglas de texto para que un pull request con código vulnerable falle. Cuando `arcaudit scan` acepte `--format sarif --output <archivo>`, ese SARIF es el que se sube y las reglas de texto no se usan.

`pip install -e .` installs the `arcguard` package, the `arcaudit` command, and the Slither plugin entry point (`slither_analyzer.plugin` → `arcguard.plugin:make_plugin`). `arcaudit --help` works. `arcaudit scan` exits 2 and does **not** run detectors: the plugin lists are empty on purpose, so the tool does not advertise a check it does not perform yet. The GitHub Action still runs that command. Until the CLI writes SARIF, the Action applies text rules so a pull request with vulnerable code fails. When `arcaudit scan` accepts `--format sarif --output <file>`, that SARIF is what gets uploaded and the text rules are not used.

Referencia de producto y corpus futuro: [scaffold-arc](https://github.com/Simonethg/scaffold-arc).

## Reglas v0.1 / v0.1 rules

Cada regla sale de la documentación pública de Arc. El detalle está en [`docs/rules/`](docs/rules/README.md).

| ID | Slug | Severidad / Severity | Qué busca / What it looks for |
| --- | --- | --- | --- |
| ARC-001 | `msg-value-vs-balanceof-mix` | Alta / High | Comparar, sumar o restar `msg.value` o `address.balance` (18 decimales) contra montos `balanceOf` / `transfer` de USDC ERC-20 (6 decimales) sin escalar. Mixing native value (18 decimals) with ERC-20 USDC amounts (6 decimals) without scaling. |
| ARC-002 | `usdc-decimals-hardcoded` | Alta / High | Suponer 6 decimales en el valor nativo, o 18 en el ERC-20. Assuming 6 decimals for native value, or 18 for the ERC-20. |
| ARC-003 | `native-erc20-dual-asset-pool` | Alta / High | Pools, LTV u oráculos que tratan el USDC nativo y el USDC ERC-20 como dos activos. Pools, LTV, or oracles that treat native USDC and ERC-20 USDC as two assets. |
| ARC-004 | `weth-pattern` | Media / Medium | `WETH.deposit` / `withdraw`, constantes WETH, wrap y unwrap. WETH deposit, withdraw, constants, wrap, and unwrap. |
| ARC-005 | `value-to-zero-address` | Alta / High | Envío de valor a `address(0)`. En Arc ese envío revierte. Sending value to `address(0)`. On Arc that transfer reverts. |
| ARC-006 | `unchecked-native-send` | Media / Medium | `call{value:}`, `transfer` o `send` asumiendo éxito. Un envío nativo puede revertir aunque haya saldo. Native sends assumed to succeed. A native transfer can revert even when the balance is enough. |
| ARC-007 | `selfdestruct-moves-usdc` | Alta / High | `selfdestruct` que mueve el USDC del contrato, o un envío a una cuenta destruida. `selfdestruct` moves the contract's USDC instead of burning it. |
| ARC-008 | `prevrandao-randomness` | Alta / High | `block.prevrandao` o `block.difficulty` usados como aleatoriedad. En Arc ese valor es 0. Using `block.prevrandao` or `block.difficulty` as randomness. On Arc that value is 0. |
| ARC-OFF-1 | `max-fee-below-floor` | Alta / High | En scripts TS/JS o Foundry, `maxFeePerGas` por debajo del piso de 20 Gwei. La transacción se descarta. `maxFeePerGas` below the 20 Gwei floor in TS/JS or Foundry scripts. The transaction is dropped. |

Fuentes / Sources:

- [EVM differences](https://docs.arc.io/arc/references/evm-differences)
- [Porting contracts to Arc](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc)
- [Arc compatibility guide for existing EVM apps](https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps)

El descargo de “no reemplaza una auditoría” sigue el mismo criterio que Arc publica en [Security on Arc](https://www.arc.io/security). / The “does not replace an audit” notice follows the same stance Arc publishes on [Security on Arc](https://www.arc.io/security).

## Instalación / Install

Requiere Python 3.10 o superior. / Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
arcaudit --help
```

Extra opcional para cargar el plugin dentro de Slither (los detectores siguen vacíos en este scaffold): / Optional extra to load the plugin inside Slither (detectors are still empty in this scaffold):

```bash
pip install -e ".[detectors]"
```

Lint y tests locales: / Local lint and tests:

```bash
pip install -e ".[dev]"
ruff check .
ruff format --check .
pytest
```

Antes del primer commit, activá el hook (una vez por clone): / Before the first commit, enable the hook (once per clone):

```bash
git config core.hooksPath scripts/hooks
```

Eso bloquea `.env*` (salvo `.env.example`), claves, keystores, JSON de cuentas de servicio, archivos de más de 50 MB y diffs con material de credenciales. Si `gitleaks` o `trufflehog` están en el `PATH`, el hook también los ejecuta. La config alternativa está en [`.pre-commit-config.yaml`](.pre-commit-config.yaml) (`pre-commit install`).

That blocks `.env*` (except `.env.example`), keys, keystores, service-account JSON, files over 50 MB, and diffs that contain credential material. If `gitleaks` or `trufflehog` is on `PATH`, the hook runs it too. The alternative config is [`.pre-commit-config.yaml`](.pre-commit-config.yaml) (`pre-commit install`).

## GitHub Action

`uses: Simonethg/arcguard@v0` instala este repositorio, corre `arcaudit scan` y sube el SARIF a Code Scanning. En el pull request publica un resumen en español e inglés. El comentario usa una lista (identificador, severidad en palabras, archivo y enlace a la doc), así se puede leer sin depender del color.

`uses: Simonethg/arcguard@v0` installs this repository, runs `arcaudit scan`, and uploads SARIF to Code Scanning. On the pull request it posts a Spanish and English summary. The comment is a list (identifier, severity in words, file, and a link to the docs), so it can be read without relying on color.

La etiqueta `v0` la crea quien publica el release. Los workflows de este repositorio usan `uses: ./` para probar la Action del propio commit antes de que exista esa etiqueta. El mismo manifiesto está en la raíz (para `@v0`) y en [`action/action.yml`](action/action.yml) (para `uses: Simonethg/arcguard/action@v0`).

The `v0` tag is created when the release is published. Workflows in this repository use `uses: ./` so they test the Action from the same commit before that tag exists. The same manifest is at the repository root (for `@v0`) and in [`action/action.yml`](action/action.yml) (for `uses: Simonethg/arcguard/action@v0`).

Permisos mínimos del workflow que llama la Action: `contents: read`. `security-events: write` solo para subir el SARIF. `pull-requests: write` solo si `comment` queda en `true`. En un repositorio privado, `actions: read` permite descargar las actions que esta composite usa. El comentario usa el token del workflow (`github.token`). No hay secretos en el repositorio: un release o un RPC de testnet, si algún día hacen falta, entran solo por GitHub Secrets.

Minimum permissions for a workflow that calls the Action: `contents: read`. `security-events: write` is only for the SARIF upload. `pull-requests: write` is only needed when `comment` stays `true`. On a private repository, `actions: read` lets the runner download the actions this composite uses. The comment uses the workflow token (`github.token`). This repository has no secrets: a release or a testnet RPC, if one is ever required, comes only from GitHub Secrets.

```yaml
name: arcguard
on: [pull_request]
permissions:
  contents: read
  actions: read
  security-events: write
  pull-requests: write
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: Simonethg/arcguard@v0
        with:
          path: .
          fail-on: high
```

Inputs: `path` (default `.`), `fail-on` (`high` por defecto / default `high`), `comment`, `upload-sarif`, `ignore`, `sarif-file`, `sarif-category`, `python-version`, `version`, `token`. El detalle está en [`action/README.md`](action/README.md).

Inputs: `path` (default `.`), `fail-on` (default `high`), `comment`, `upload-sarif`, `ignore`, `sarif-file`, `sarif-category`, `python-version`, `version`, `token`. Details are in [`action/README.md`](action/README.md).

`demo-vulnerable.yml` escanea `action/fixtures/vulnerable` y el check queda en rojo: ese código manda valor a `address(0)`, usa `block.prevrandao`, llama a `selfdestruct` y fija `maxFeePerGas` por debajo de 20 Gwei. `demo-fixed.yml` escanea la versión corregida y tiene que pasar. ArcGuard no certifica seguridad y no reemplaza una auditoría.

`demo-vulnerable.yml` scans `action/fixtures/vulnerable` and the check stays red: that code sends value to `address(0)`, uses `block.prevrandao`, calls `selfdestruct`, and sets `maxFeePerGas` below 20 Gwei. `demo-fixed.yml` scans the corrected fixture and must pass. ArcGuard does not certify security and does not replace an audit.

Fuentes de las reglas / Rule sources:

- [EVM differences](https://docs.arc.io/arc/references/evm-differences)
- [Porting contracts to Arc](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc)
- [Arc compatibility guide for existing EVM apps](https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps)

## Estructura / Layout

```
detectors/     paquete Python arcguard y plugin de Slither
offchain/      reglas sobre TS/JS/Foundry (ARC-OFF-*)
cli/           implementación de arcaudit (arcguard.cli)
action/        GitHub Action composite (SARIF, comentario en el PR / PR comment)
corpus/        contratos vulnerables y corregidos (todavía vacío)
tests/         pytest del scaffold
web/           UI (todavía sin páginas)
docs/rules/    una página por regla, ES/EN
```

## Accesibilidad / Accessibility

Este scaffold no renderiza UI. La web futura tiene que cumplir WCAG 2.1/2.2 AA en 390 px y 1440 px, con el escaneo acotado al componente que cambie. No hay hallazgos de axe-core porque no hay componente que escanear. El comentario de la Action es Markdown con encabezado, lista y enlaces; la severidad está escrita con palabras (high, medium, low, info), no solo con color.

This scaffold does not render a UI. The future web app must meet WCAG 2.1/2.2 AA at 390 px and 1440 px, with scans scoped to the component that changed. There are no axe-core findings because there is no component to scan. The Action comment is Markdown with a heading, a list, and links; severity is written in words (high, medium, low, info), not by color alone.

## Licencia / License

MIT. Copyright (c) 2026 Simoneth Gomez. Ver [LICENSE](LICENSE).
