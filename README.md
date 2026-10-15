# ArcGuard

Escáner open source (MIT) de trampas al portar contratos y herramientas a **Arc**, **Base** y **Celo**. El comando es `arcaudit`. El motor es multichain: cada cadena es un módulo `arcguard.<chain>` con `scan_path(path) -> list[Finding]`.

**ArcGuard no certifica seguridad y no reemplaza una auditoría.** Un reporte vacío no significa que un contrato sea seguro. Las pruebas en vivo se quedan en **testnets públicas**. Este repositorio no incluye configuración de mainnet, claves ni datos personales.

Open-source (MIT) multichain scanner for pitfalls when porting contracts and tooling to **Arc**, **Base**, and **Celo**. The command is `arcaudit`. Each chain is an `arcguard.<chain>` module with `scan_path(path) -> list[Finding]`.

**ArcGuard does not certify security and does not replace an audit.** An empty report does not mean a contract is safe. Live checks stay on **public testnets**. This repository does not ship mainnet configuration, keys, or personal data.

Slither encuentra bugs de Ethereum. ArcGuard busca los que aparecen al portar a Arc, Base o Celo. / Slither finds Ethereum bugs. ArcGuard looks for the ones that show up when porting to Arc, Base, or Celo.

## Motor / Engine

`pip install -e .` instala el paquete `arcguard`, el comando `arcaudit` y el entry point de plugin de Slither (`slither_analyzer.plugin` → `arcguard.plugin:make_plugin`). Con el extra `detectors`, el plugin registra ARC-001..ARC-008.

`arcaudit scan <ruta|URL-de-github> --chain arc|base|celo|all` carga los módulos instalados y normaliza cada hallazgo al mismo `Finding`: `rule_id`, `chain`, `severity`, `file`, `line`, `message`, `doc_url`. Si el extra `detectors` está instalado, un scan que incluye Arc también ejecuta ARC-001..ARC-008.

| Módulo | Cadena | Qué corre hoy |
| --- | --- | --- |
| `arcguard.arc` (`offchain/`) | Arc | ARC-OFF-1: `maxFeePerGas` o `gasPrice` por debajo de 20 Gwei en TS/JS, Foundry o Hardhat. Arc descarta la transacción en silencio. |
| `arcguard.base` | Base | Se llama `scan_path` del paquete Base si está instalado. Ese módulo publica `path` en vez de `file`, severidad en título y sin `chain` ni `doc_url`; el registro lo adapta y no modifica ese paquete. |
| `arcguard.celo` | Celo | La misma firma `scan_path`. Si el paquete no está, `--chain all` deja una nota y `--chain celo` sale con código 2. |

`--format text` (default), `json`, `sarif` (SARIF 2.1.0) o `markdown`. El proceso sale con código 1 si hay un hallazgo de severidad mayor o igual que `--threshold` (`info`, `low`, `medium`, `high`, `critical`; default `low`).

Con el extra `detectors`, el plugin expone ARC-001..ARC-008 y un scan de Arc los ejecuta. Sin ese extra las listas quedan vacías y no se simula un análisis de Solidity.

`pip install -e .` installs the `arcguard` package, the `arcaudit` command, and the Slither plugin entry point (`slither_analyzer.plugin` → `arcguard.plugin:make_plugin`).

`arcaudit scan <path|github-url> --chain arc|base|celo|all` loads installed modules and normalizes every hit to the same `Finding`: `rule_id`, `chain`, `severity`, `file`, `line`, `message`, `doc_url`.

| Module | Chain | What runs today |
| --- | --- | --- |
| `arcguard.arc` (`offchain/`) | Arc | ARC-OFF-1: `maxFeePerGas` or `gasPrice` below 20 Gwei in TS/JS, Foundry, or Hardhat. Arc drops the transaction silently. |
| `arcguard.base` | Base | Calls that package's `scan_path` when it is installed. Its finding uses `path` rather than `file`, title-case severity, and no `chain` or `doc_url`; the registry adapts it and does not modify that package. |
| `arcguard.celo` | Celo | Same `scan_path` signature. If the package is absent, `--chain all` records a note and `--chain celo` exits 2. |

`--format text` (default), `json`, `sarif` (SARIF 2.1.0), or `markdown`. The process exits 1 when a finding's severity is at least `--threshold` (`info`, `low`, `medium`, `high`, `critical`; default `low`).

With the `detectors` extra, the plugin exposes ARC-001..ARC-008 and an Arc scan runs them. Without that extra the lists stay empty and no Solidity analysis is simulated.

Referencia de producto y corpus futuro: [scaffold-arc](https://github.com/Simonethg/scaffold-arc). Fuentes de ARC-OFF-1: [EVM differences](https://docs.arc.io/arc/references/evm-differences), [porting](https://docs.arc.io/arc/tutorials/porting-contracts-to-arc), [compatibility guide](https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps).

## Reglas v0.1 / v0.1 rules

Cada regla sale de la documentación pública de Arc. El detalle está en [`docs/rules/`](docs/rules/README.md).

| ID | Slug | Severidad / Severity | Qué busca / What it looks for |
| --- | --- | --- | --- |
| ARC-001 | `msg-value-vs-balanceof-mix` | Alta / High | Comparar, sumar o restar `msg.value` o `address.balance` (18 decimales) contra montos `balanceOf` / `transfer` de USDC ERC-20 (6 decimales) sin escalar, incluido el call site que pasa `msg.value` real a un helper. Un parámetro llamado `msgValue` mezclado solo con `balanceOf` es Media. Mixing native value (18 decimals) with ERC-20 USDC amounts (6 decimals) without scaling, including a call site that passes real `msg.value` into a helper. A `msgValue` parameter mixed only with `balanceOf` is Medium. |
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

Extra para los detectores Slither ARC-001..ARC-008: / Extra for the Slither detectors ARC-001..ARC-008:

```bash
pip install -e ".[detectors]"
```

Lint y tests locales: / Local lint and tests:

```bash
pip install -e ".[dev,detectors]"
solc-select install 0.8.28
solc-select use 0.8.28
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

## Estructura / Layout

```
detectors/     paquete arcguard: Finding común, registro de cadenas, plugin Slither
offchain/      arcguard.arc (ARC-OFF-1)
cli/           arcaudit scan (arcguard.cli): texto, JSON, SARIF, Markdown
action/        GitHub Action composite (falla cerrado: aún no escanea)
corpus/        contratos vulnerables y corregidos por regla (Arc, Base, Celo)
tests/         pytest, incluida la validación SARIF 2.1.0
web/           UI (todavía sin páginas)
docs/rules/    una página por regla, ES/EN
```

## Accesibilidad / Accessibility

Este scaffold no renderiza UI. La web futura tiene que cumplir WCAG 2.1/2.2 AA en 390 px y 1440 px, con el escaneo acotado al componente que cambie. No hay hallazgos de axe-core porque no hay componente que escanear.

This scaffold does not render a UI. The future web app must meet WCAG 2.1/2.2 AA at 390 px and 1440 px, with scans scoped to the component that changed. There are no axe-core findings because there is no component to scan.

## Licencia / License

MIT. Copyright (c) 2026 Simoneth Gomez. Ver [LICENSE](LICENSE).

## Reglas Celo (heurísticas) / Celo rules (heuristics)

Reglas específicas de Celo sacadas de docs.celo.org, en `detectors/celo/`. Corren con `arcaudit scan --chain celo` o `--chain all` (no son detectores de Slither). / Celo-specific rules sourced from docs.celo.org in `detectors/celo/`, run by `arcaudit scan --chain celo` or `--chain all` (not Slither detectors). Índice / Index: [docs/rules/celo](docs/rules/celo/README.md).

## Reglas Base (heurísticas) / Base rules (heuristics)

Reglas específicas de Base, todas sacadas de docs.base.org. Son heurísticas de texto en `detectors/base/` y corren con `arcaudit scan --chain base` (o `--chain all`). No están en el plugin de Slither. / Base-specific rules sourced from docs.base.org. They are text heuristics in `detectors/base/` and run with `arcaudit scan --chain base` (or `--chain all`). They are not in the Slither plugin.

| ID | Slug | Severidad / Severity |
| --- | --- | --- |
| BASE-001 | [b20-union-weakens-blocklist](docs/rules/BASE-001.md) | Alta / High |
| BASE-002 | [b20-policy-id-unchecked](docs/rules/BASE-002.md) | Media / Medium |
| BASE-003 | [b20-seize-unguarded](docs/rules/BASE-003.md) | Alta / High |
| BASE-004 | [validity-predicate-unsafe](docs/rules/BASE-004.md) | Media / Medium |
| BASE-005 | [block-count-duration](docs/rules/BASE-005.md) | Alta / High |
| BASE-OFF-1 | [flashblocks-pending-dependency](docs/rules/BASE-OFF-1.md) | Media / Medium |
| BASE-OFF-2 | [builder-code-suffix-missing](docs/rules/BASE-OFF-2.md) | Baja / Low |
