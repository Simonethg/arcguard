# CELO-008 `celo-native-erc20-duality`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-008/` (vulnerable + fixed)

## Español

CELO es a la vez moneda nativa y ERC-20 (GoldToken, `0x471E…a438`): es un único saldo. Un indexer que solo sigue eventos `Transfer` se pierde los movimientos por `value` nativo, que no emiten ese evento.

**Qué marca:** código off-chain que referencia el token CELO y escucha eventos `Transfer` sin seguir también transferencias nativas (`getBalance`, `tx.value`, traces).

**Dirección del arreglo:** seguir también las transferencias nativas o conciliar contra `getBalance`.

## English

CELO is both the native currency and an ERC-20 (GoldToken, `0x471E…a438`): one balance. An indexer that only follows `Transfer` events misses native `value` transfers, which do not emit it.

**What it flags:** off-chain code that references the CELO token and listens to `Transfer` events without also tracking native transfers (`getBalance`, `tx.value`, traces).

**Fix direction:** also track native transfers or reconcile against `getBalance`.

## Fuentes / Sources

- [CELO token — token duality](https://docs.celo.org/learn/protocol/celo-token)
- [Migrate from Ethereum — differences](https://docs.celo.org/build/tools/overview/migrate/from-ethereum)
