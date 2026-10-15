# BASE-005 `block-count-duration`

**Severidad / Severity:** Alta / High

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

Denim pasa Base de un bloque cada 2 s a cinco bloques por segundo (200 ms). `block.number` avanza 10 veces más rápido, mientras `block.timestamp` sigue en segundos. Timelocks, cooldowns, deadlines y rate limits medidos en bloques duran una décima parte de lo previsto. En contratos inmutables no se pueden reajustar después de la activación.

**Qué marca:** aritmética o comparaciones con `block.number` del tipo `block.number + N`, `x - block.number` o `block.number >= start + N`.

**Dirección del arreglo:** medir duraciones con `block.timestamp`. Si hace falta, usar el predeploy BaseTime para resolución en milisegundos.

## English

Denim moves Base from one block every 2 s to five blocks per second (200 ms). `block.number` advances 10x faster while `block.timestamp` still moves in seconds. Timelocks, cooldowns, deadlines, and rate limits counted in blocks last one tenth of the intended time. Immutable contracts cannot be retuned after activation.

**What it flags:** `block.number` arithmetic or comparisons such as `block.number + N`, `x - block.number`, or `block.number >= start + N`.

**Fix direction:** measure durations with `block.timestamp`. Use the BaseTime predeploy for millisecond resolution if needed.

## Fuentes / Sources

- [200ms Native Blocks — Block-Number-Based Contract Logic](https://docs.base.org/upgrades/denim/200ms-blocks)
- [Upgrades — Denim schedule](https://docs.base.org/upgrades/overview)
