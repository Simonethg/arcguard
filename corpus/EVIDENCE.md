# Evidencia de transacciones fallidas

Solo Arc testnet.

| Campo | Valor |
|---|---|
| Chain id | `5042002` |
| RPC | `https://rpc.testnet.arc.io` |
| Explorador | `https://testnet.arcscan.app` |
| USDC ERC-20 | `0x3600000000000000000000000000000000000000` (6 decimales) |
| Piso de `maxFeePerGas` | 20 gwei. Por debajo, el mempool descarta la tx sin recibo. |

No hay clave en este repositorio. `scripts/run-testnet-evidence.sh` la lee de `ARC_TESTNET_PRIVATE_KEY` (entorno o secreto de CI) y se niega a correr contra cualquier chain id distinto de `5042002`. No imprime la variable. Si no está definida, no envía nada.

## Cómo reproducir

```bash
cp .env.example .env
# Poner la clave de testnet en .env o exportarla. No la commitees.
bash scripts/run-testnet-evidence.sh
```

El script manda 1 wei nativo, con `--gas-price 20gwei`, a:

1. `address(0)` — ARC-005. En Arc revierte con `Zero address not allowed` y el recibo queda con status 0.
2. `0x70997970C51812dc3A010C7d01b50e0d17dc79C8` — dirección blocklisted publicada en la doc de direcciones de Arc. Una transferencia de valor hacia ella revierte en testnet. En `arc-anvil --network arc` local esa dirección no está blocklisted: el mismo envío allí se mina con status 1. No uses el anvil local como prueba de blocklist.

La salida queda en `evidence/last-run.txt` (gitignored). De ahí se copia solo el hash y el status.

## Cómo registrar el hash

1. Confirmá que el status es fallido (`0x0`) y que el chain id de la RPC era `5042002`.
2. Abrí `https://testnet.arcscan.app/tx/<hash>`.
3. Reemplazá el placeholder de la tabla. No pegues la clave, ni el JSON completo del recibo, ni un volcado que incluya inputs de firma.

Un fork de solo lectura (`bash scripts/run-testnet-fork.sh`) también muestra el revert de `address(0)`, `decimals() == 6` y `PREVRANDAO == 0`, pero no produce un hash en el explorador. El hash solo sale de la transacción enviada.

## Hashes

Sin credenciales en este entorno no se envió ninguna transacción a testnet. Los placeholders quedan vacíos a propósito.

| Regla | Qué falló | Status | Tx hash | Explorador |
|---|---|---|---|---|
| ARC-005 | Valor nativo distinto de cero a `address(0)`. Motivo esperado: `Zero address not allowed`. | pendiente | `<sin-clave>` | `https://testnet.arcscan.app/tx/<sin-clave>` |
| ARC-006 | Valor nativo a la dirección blocklisted de testnet documentada por Arc. | pendiente | `<sin-clave>` | `https://testnet.arcscan.app/tx/<sin-clave>` |

## Qué sí se observó sin clave

Estas comprobaciones no son hashes de testnet:

- Lectura pública de testnet: chain id `5042002`, `decimals()` de USDC igual a 6, base fee del último bloque en el piso de 20 gwei.
- `arc-forge test --network arc`: el envío con valor a `address(0)` revierte con `Zero address not allowed`; el envío de valor 0 a `address(0)` no revierte; `block.prevrandao` y `block.difficulty` son 0; `SELFDESTRUCT` hacia sí mismo con saldo revierte; `SELFDESTRUCT` hacia `address(0)` con saldo revierte con `Zero address not allowed`; un envío con valor, en la misma transacción, a una cuenta recién destruida devuelve falso con `Cannot increase the balance of selfdestructed account`.
- `arc-anvil --network arc` reporta `"network": "arc"`, chain id `31337` (no es testnet) y base fee de 20 gwei. El predeploy de USDC responde `decimals() == 6`.
