# BASE-OFF-1 `flashblocks-pending-dependency`

**Severidad / Severity:** Media / Medium

**Estado / Status:** heurística de texto en `detectors/base/`; corre con `arcaudit scan --chain base` (no está en el plugin de Slither). / text heuristic in `detectors/base/`; runs with `arcaudit scan --chain base` (not in the Slither plugin).

## Español

Denim reemplaza Flashblocks por bloques canónicos de 200 ms. Las suscripciones `newFlashblocks`, `pendingLogs` y `newFlashblockTransactions`, y las lecturas con el tag `"pending"`, dejan de dar estado preconfirmado. La doc dice que no tienen equivalente directo.

**Qué marca:** en TS/JS, esas suscripciones y `blockTag: "pending"` o argumentos `"pending"`.

**Dirección del arreglo:** migrar a `newHeads`, `logs` y lecturas canónicas siguiendo la tabla de la guía de migración, y probar en Vibenet.

## English

Denim replaces Flashblocks with canonical 200 ms blocks. `newFlashblocks`, `pendingLogs`, and `newFlashblockTransactions` subscriptions, and reads with the `"pending"` tag, no longer return preconfirmed state. The docs say they have no direct equivalent.

**What it flags:** those subscriptions in TS/JS, plus `blockTag: "pending"` or `"pending"` arguments.

**Fix direction:** migrate to `newHeads`, `logs`, and canonical reads following the migration table, and test on Vibenet.

## Fuentes / Sources

- [Migrate From Flashblocks](https://docs.base.org/upgrades/denim/migrate-from-flashblocks)
- [200ms Native Blocks](https://docs.base.org/upgrades/denim/200ms-blocks)
