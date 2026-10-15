# Corpus ArcGuard (ARC-001 … ARC-008)

Contratos vulnerables y corregidos para las trampas de portar código Ethereum a Arc, más tests de Arc Foundry que reproducen las fallas de ejecución.

Arc es una L1 de Circle. El gas nativo es USDC: la vista nativa usa 18 decimales y la interfaz ERC-20 (`0x3600000000000000000000000000000000000000`) usa 6. Son el mismo saldo. Este directorio solo apunta a **Arc testnet** (chain id `5042002`, `https://rpc.testnet.arc.io`) y a `arc-anvil --network arc`. No hay RPC de mainnet, ni deploys, ni transacciones de mainnet.

## Fuentes

- https://docs.arc.io/arc/references/evm-differences
- https://docs.arc.io/arc/tutorials/porting-contracts-to-arc
- https://www.arc.io/blog/arc-compatibility-guide-for-existing-evm-apps
- Fix de referencia, portado en `src/lib/UsdcUnits.sol`: https://github.com/Simonethg/scaffold-arc (`packages/foundry/src/UsdcUnits.sol`, MIT)
- Caso vulnerable de referencia, portado en `src/vulnerable/NaiveEthereumPort.sol`: https://github.com/Simonethg/scaffold-arc (`packages/foundry/src/examples/NaiveEthereumPort.sol`, MIT)

El mapa regla → archivo está en [CASES.md](CASES.md). Cómo registrar hashes de transacciones fallidas está en [EVIDENCE.md](EVIDENCE.md).

## Qué escanear

| Directorio | Rol |
|---|---|
| `src/vulnerable/` | Debe marcarse. Incluye el port de `NaiveEthereumPort`. |
| `src/fixed/` | Contrapartes corregidas. No deberían marcarse. |
| `src/lib/UsdcUnits.sol` | Fix recomendado. No debería marcarse. |
| `test/`, `lib/forge-std/` | Arnés. Fuera del corpus de reglas. |

## Requisitos

Arc Foundry (`arc-forge`, `arc-cast`, `arc-anvil`), no el Foundry upstream. Guía: https://docs.arc.io/arc/tutorials/install-arc-foundry

`foundry.toml` fija `network = "arc"` y `evm_version = "osaka"`. Un `forge test` de upstream no reproduce el revert a `address(0)` ni `PREVRANDAO = 0`.

## Tests locales (sin clave)

```bash
# 1. Compilar y correr la suite in-process bajo las reglas de Arc.
bash scripts/run-local.sh

# 2. arc-anvil --network arc (chain id 31337) y fork con arc-forge.
bash scripts/run-anvil.sh

# 3. Fork de solo lectura contra Arc testnet. No firma ni envía nada.
bash scripts/run-testnet-fork.sh
```

Equivalente manual:

```bash
arc-forge build
arc-forge test --network arc -vv

arc-anvil --network arc
ARC_FORK=true arc-forge test --network arc \
  --fork-url http://127.0.0.1:8545 \
  --match-path 'test/fork/*' -vv
```

Los tests de `test/fork/` se saltan si `ARC_FORK` no está en `true`, así `arc-forge test` pasa sin nodo. Si el fork no es chain id `31337` (anvil local) ni `5042002` (testnet), el `setUp` revierte.

## Testnet con transacción real

Hace falta una clave de testnet fondeada en https://faucet.circle.com. Se lee solo de `ARC_TESTNET_PRIVATE_KEY` (entorno o secreto de CI). El archivo de ejemplo está vacío:

```bash
cp .env.example .env
# completar ARC_TESTNET_PRIVATE_KEY fuera del repo
bash scripts/run-testnet-evidence.sh
```

El script corta si el chain id no es `5042002`, no imprime la clave y, si la variable no existe, sale 0 sin enviar nada. El recibo queda en `evidence/last-run.txt`, directorio ignorado por git. Copiá el hash a [EVIDENCE.md](EVIDENCE.md).

## Si este entorno no tiene Arc Foundry

Sin `arc-forge` / `arc-anvil` la suite no se puede ejecutar: el Foundry upstream no implementa las reglas de Arc. Instalá los binarios desde las releases de https://github.com/circlefin/arc-foundry y volvé a correr los scripts de arriba.
