# CELO-010 `block-time-assumption`

**Severidad / Severity:** Media / Medium

**Estado / Status:** heurística de texto en `detectors/celo/` (corre con `arcaudit scan --chain celo|all`; no es detector de Slither). / text heuristic in `detectors/celo/` (runs with `arcaudit scan --chain celo|all`; not a Slither detector).

**Corpus:** `corpus/celo/CELO-010/` (vulnerable + fixed)

## Español

Celo L1 tenía bloques de 5 s; Ethereum, de 12 s. Celo L2 produce bloques de **1 s**. Timelocks, vesting o rate limits medidos en bloques con esas constantes corren 5 a 12 veces más rápido.

**Qué marca:** constantes de tiempo de bloque = 5 o 12 (`BLOCK_TIME`, `SECONDS_PER_BLOCK`, ...) o bloques por día/año típicos de 5 s/12 s (17280, 7200, 6307200, 2628000, ...).

**Dirección del arreglo:** usar `block.timestamp` o recalcular con 1 s.

## English

Celo L1 had 5 s blocks and Ethereum has 12 s. Celo L2 produces **1 s** blocks. Block-count timelocks, vesting or rate limits built on those constants run 5-12x faster.

**What it flags:** block-time constants equal to 5 or 12 or blocks-per-day/year typical of 5 s/12 s (17280, 7200, 6307200, 2628000, ...).

**Fix direction:** use `block.timestamp` or recompute for 1 s.

## Fuentes / Sources

- [Celo L1 → L2 changes — block time](https://docs.celo.org/learn/celo-l1)
