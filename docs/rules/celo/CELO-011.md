# CELO-011 `removed-precompiles`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-011/` (vulnerable + fixed)

## Español

En la migración a L2 se eliminaron todos los precompiles de Celo salvo el de transfer (`0xfd`). Las llamadas a los otros fallan o devuelven vacío.

**Qué marca:** `address(0xff - n)` con n ≠ 2, direcciones `0x…00e0`–`0x…00fc` o funciones de `UsingPrecompiles` (`fractionMulExp`, `getEpochSize`, `numberValidatorsInSet`, ...).

**Dirección del arreglo:** quitar la dependencia o leer el dato de contratos/config.

## English

The L2 migration removed every Celo precompile except transfer (`0xfd`). Calls to the others fail or return empty.

**What it flags:** `address(0xff - n)` with n ≠ 2, addresses `0x…00e0`–`0x…00fc`, or `UsingPrecompiles` helpers.

**Fix direction:** drop the dependency or read the value from contracts/config.

## Fuentes / Sources

- [Celo L1 → L2 changes — precompiles](https://docs.celo.org/learn/celo-l1)
