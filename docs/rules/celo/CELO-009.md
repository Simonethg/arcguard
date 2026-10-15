# CELO-009 `msgvalue-plus-erc20-double-count`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-009/` (vulnerable + fixed)

## Español

Por la dualidad del token, `address(x).balance` y `GoldToken.balanceOf(x)` devuelven el **mismo** saldo. Sumarlos duplica los activos (precio de shares, colateral).

**Qué marca:** una expresión Solidity que suma `.balance` y `balanceOf(...)`.

**Dirección del arreglo:** contar CELO una sola vez.

## English

Because of token duality, `address(x).balance` and `GoldToken.balanceOf(x)` return the **same** balance. Adding them doubles assets (share price, collateral).

**What it flags:** a Solidity expression that adds `.balance` and `balanceOf(...)`.

**Fix direction:** count CELO once.

## Fuentes / Sources

- [CELO token — token duality](https://docs.celo.org/learn/protocol/celo-token)
- [Migrate from Ethereum](https://docs.celo.org/build/tools/overview/migrate/from-ethereum)
